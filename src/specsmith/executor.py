# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Executor — cross-platform process execution with PID tracking and abort.

Provides governed command execution with:
- PID file tracking in .specsmith/pids/
- Configurable timeout enforcement
- Cross-platform abort (Windows taskkill / POSIX SIGTERM+SIGKILL)
- Process listing for agent visibility
- Deterministic shell resolution (REQ-313)
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class ShellResolverResult:
    """Structured result from the cross-platform shell resolver (REQ-313)."""

    executable: str  # resolved path to the shell executable
    shell_family: str  # "pwsh", "powershell", "cmd", "bash", "sh", or "unknown"
    argv_prefix: list[str]  # argv prefix for subprocess.Popen
    source: str  # provenance: explicit/config/env/platform/none
    detected_version: str = ""  # e.g. "7.4.0" or ""
    diagnostic: str = ""  # actionable message if source == "none"


# Cached resolver result (module-level singleton for performance)
_resolver_cache: ShellResolverResult | None = None


def _resolve_shell(
    executable: str | None = None, *, config_shell: str | None = None
) -> ShellResolverResult:
    """Resolve the best available shell for cross-platform execution (REQ-313).

    Resolution order:
    1. Explicit override (passed as *executable*)
    2. SPECSMITH_SHELL environment variable
    3. Platform-specific preferred shells:
       - Windows: pwsh.exe → powershell.exe → cmd.exe
       - POSIX: bash → sh
    4. Fail with actionable diagnostic if no supported shell exists.

    Returns a structured ShellResolverResult with provenance.
    """
    global _resolver_cache

    # Return cached result if no override requested
    if executable is None and _resolver_cache is not None:
        return _resolver_cache

    # 1. Explicit override
    if executable is not None:
        resolved = shutil.which(executable)
        if resolved:
            version = _detect_shell_version(resolved)
            family = _classify_shell(executable)
            result = ShellResolverResult(
                executable=resolved,
                shell_family=family,
                argv_prefix=[resolved],
                source="explicit",
                detected_version=version,
            )
            return result
        result = ShellResolverResult(
            executable=executable,
            shell_family=_classify_shell(executable),
            argv_prefix=[executable],
            source="explicit",
            diagnostic=f"Specified shell '{executable}' not found in PATH",
        )
        return result

    # 2. Resolved project configuration
    if config_shell:
        resolved = shutil.which(config_shell)
        if resolved:
            return ShellResolverResult(
                executable=resolved,
                shell_family=_classify_shell(config_shell),
                argv_prefix=_shell_prefix(resolved, _classify_shell(config_shell)),
                source="config",
                detected_version=_detect_shell_version(resolved),
            )
        return ShellResolverResult(
            executable=config_shell,
            shell_family=_classify_shell(config_shell),
            argv_prefix=[config_shell],
            source="config",
            diagnostic=f"Configured shell '{config_shell}' not found in PATH",
        )

    # 3. SPECSMITH_SHELL environment override
    env_shell = os.environ.get("SPECSMITH_SHELL")
    if env_shell:
        resolved = shutil.which(env_shell)
        if resolved:
            version = _detect_shell_version(resolved)
            family = _classify_shell(env_shell)
            result = ShellResolverResult(
                executable=resolved,
                shell_family=family,
                argv_prefix=[resolved],
                source="env",
                detected_version=version,
            )
            _resolver_cache = result
            return result
        # Env set but not found — return diagnostic with source="env"
        result = ShellResolverResult(
            executable=env_shell,
            shell_family=_classify_shell(env_shell),
            argv_prefix=[env_shell],
            source="env",
            diagnostic=f"SPECSMITH_SHELL shell '{env_shell}' not found in PATH",
        )
        _resolver_cache = result
        return result

    # 3. Platform-specific resolution
    if sys.platform == "win32":
        result = _resolve_windows_shell()
    else:
        result = _resolve_posix_shell()
    _resolver_cache = result
    return result


def _classify_shell(name: str) -> str:
    """Classify a shell name into a family string."""
    base = Path(name).stem.lower()
    if base in ("pwsh",):
        return "pwsh"
    if base in ("powershell", "ps"):
        return "powershell"
    if base in ("cmd", "cmd.exe"):
        return "cmd"
    if base in ("bash",):
        return "bash"
    if base in ("sh",):
        return "sh"
    return "unknown"


def _shell_prefix(executable: str, family: str) -> list[str]:
    if family in {"pwsh", "powershell"}:
        return [executable, "-NoProfile", "-NonInteractive", "-Command"]
    if family == "cmd":
        return [executable, "/c"]
    return [executable, "-c"]


def _detect_shell_version(executable: str) -> str:
    """Detect the version of a shell executable."""
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout:
            # Extract version from first line
            first_line = result.stdout.strip().split("\n")[0]
            # Try to extract version number
            import re

            match = re.search(r"(\d+\.\d+\.\d+)", first_line)
            if match:
                return match.group(1)
            return first_line[:80]
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        pass
    return ""


def _resolve_windows_shell() -> ShellResolverResult:
    """Resolve shell on Windows: pwsh.exe → powershell.exe → cmd.exe."""
    # Try PowerShell 7 (pwsh.exe) first
    pwsh = shutil.which("pwsh.exe") or shutil.which("pwsh")
    if pwsh:
        version = _detect_shell_version(pwsh)
        return ShellResolverResult(
            executable=pwsh,
            shell_family="pwsh",
            argv_prefix=[pwsh, "-NoProfile", "-NonInteractive", "-Command"],
            source="windows-preferred",
            detected_version=version,
        )

    # Try Windows PowerShell (powershell.exe)
    ps = shutil.which("powershell.exe") or shutil.which("powershell")
    if ps:
        version = _detect_shell_version(ps)
        return ShellResolverResult(
            executable=ps,
            shell_family="powershell",
            argv_prefix=[ps, "-NoProfile", "-NonInteractive", "-Command"],
            source="windows-fallback",
            detected_version=version,
        )

    cmd = shutil.which("cmd.exe") or shutil.which("cmd")
    if cmd:
        return ShellResolverResult(
            executable=cmd,
            shell_family="cmd",
            argv_prefix=[cmd, "/c"],
            source="windows-fallback",
        )
    return ShellResolverResult(
        executable="",
        shell_family="none",
        argv_prefix=[],
        source="none",
        diagnostic="No supported Windows shell found; install PowerShell 7 or repair cmd.exe",
    )


def _resolve_posix_shell() -> ShellResolverResult:
    """Resolve shell on POSIX: bash → sh."""
    # Try bash first
    bash = shutil.which("bash")
    if bash:
        version = _detect_shell_version(bash)
        return ShellResolverResult(
            executable=bash,
            shell_family="bash",
            argv_prefix=[bash, "-c"],
            source="posix-default",
            detected_version=version,
        )

    # Fallback to sh
    sh = shutil.which("sh")
    if sh:
        version = _detect_shell_version(sh)
        return ShellResolverResult(
            executable=sh,
            shell_family="sh",
            argv_prefix=[sh, "-c"],
            source="posix-default",
            detected_version=version,
        )

    # No shell found
    return ShellResolverResult(
        executable="",
        shell_family="none",
        argv_prefix=[],
        source="none",
        diagnostic=(
            "No supported shell found. Install bash or sh. Set SPECSMITH_SHELL to override."
        ),
    )


@dataclass
class TrackedProcess:
    """Metadata for a tracked process."""

    pid: int
    command: str
    started: str  # ISO timestamp
    timeout: int  # seconds
    pid_file: str = ""

    @property
    def started_dt(self) -> datetime:
        return datetime.fromisoformat(self.started)

    @property
    def elapsed(self) -> float:
        return (datetime.now(tz=timezone.utc) - self.started_dt).total_seconds()

    @property
    def is_expired(self) -> bool:
        return self.elapsed > self.timeout


@dataclass
class ExecResult:
    """Result of a tracked execution."""

    command: str
    exit_code: int
    pid: int
    duration: float
    timed_out: bool = False
    aborted: bool = False
    stdout_file: str = ""
    stderr_file: str = ""
    shell_family: str = ""  # REQ-313: shell family used (pwsh, bash, cmd, etc.)
    shell_path: str = ""  # REQ-313: resolved shell executable path


def _pids_dir(root: Path) -> Path:
    d = root / ".specsmith" / "pids"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _logs_dir(root: Path) -> Path:
    d = root / ".specsmith" / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_pid_file(root: Path, proc: TrackedProcess) -> Path:
    """Write PID tracking file. Returns path to PID file."""
    pid_file = _pids_dir(root) / f"{proc.pid}.json"
    proc.pid_file = str(pid_file)
    pid_file.write_text(json.dumps(asdict(proc), indent=2), encoding="utf-8")
    return pid_file


def _remove_pid_file(root: Path, pid: int) -> None:
    """Remove PID tracking file."""
    pid_file = _pids_dir(root) / f"{pid}.json"
    if pid_file.exists():
        pid_file.unlink()


def _is_process_alive(pid: int) -> bool:
    """Check if a process is still running (cross-platform)."""
    try:
        if sys.platform == "win32":
            # Windows: use tasklist to check
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return str(pid) in result.stdout
        # POSIX: signal 0 checks existence without killing
        os.kill(pid, 0)
        return True
    except (OSError, subprocess.TimeoutExpired):
        return False


def _kill_process(pid: int, *, graceful_timeout: float = 5.0) -> bool:
    """Kill a process cross-platform. Returns True if killed.

    Strategy:
    - POSIX: SIGTERM → wait → SIGKILL
    - Windows: taskkill → taskkill /F
    """
    if not _is_process_alive(pid):
        return True  # Already dead

    try:
        if sys.platform == "win32":
            # Graceful first
            subprocess.run(
                ["taskkill", "/PID", str(pid)],
                capture_output=True,
                timeout=graceful_timeout,
            )
            time.sleep(min(graceful_timeout, 2.0))
            if not _is_process_alive(pid):
                return True
            # Force kill
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid), "/T"],
                capture_output=True,
                timeout=5,
            )
        else:
            # SIGTERM first
            os.kill(pid, signal.SIGTERM)
            deadline = time.monotonic() + graceful_timeout
            while time.monotonic() < deadline:
                if not _is_process_alive(pid):
                    return True
                time.sleep(0.2)
            # SIGKILL
            os.kill(pid, signal.SIGKILL)
    except (OSError, subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass

    time.sleep(0.5)
    return not _is_process_alive(pid)


def run_tracked(
    root: Path,
    command: str | Sequence[str],
    *,
    timeout: int = 120,
    capture: bool = True,
    shell: str | None = None,
) -> ExecResult:
    """Execute a command with PID tracking and timeout enforcement.

    - Writes PID file to .specsmith/pids/<pid>.json
    - Enforces timeout via subprocess.Popen + polling
    - Logs stdout/stderr to .specsmith/logs/
    - Cleans up PID file on completion
    - Cross-platform: works on Windows, Linux, macOS
    - Uses deterministic shell resolver (REQ-313)

    Args:
        root: Project root path.
        command: Command string to execute.
        timeout: Timeout in seconds.
        capture: Whether to capture stdout/stderr to log files.
        shell: Optional explicit shell override (e.g. "pwsh", "bash").
    """
    started = datetime.now(tz=timezone.utc).isoformat()
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")

    stdout_path = _logs_dir(root) / f"exec_{ts}.stdout"
    stderr_path = _logs_dir(root) / f"exec_{ts}.stderr"

    if isinstance(command, str):
        config_shell = None
        if shell is None:
            from specsmith.config_resolver import resolve_config

            resolved_config = resolve_config(root)
            config_shell = (resolved_config.values.get("execution") or {}).get("shell")
        resolver_result = _resolve_shell(executable=shell, config_shell=config_shell)
        if resolver_result.diagnostic:
            raise RuntimeError(resolver_result.diagnostic)
        process_args = resolver_result.argv_prefix + [command]
        command_display = command
    else:
        if not command:
            raise ValueError("direct argv command must not be empty")
        process_args = [str(part) for part in command]
        command_display = " ".join(process_args)
        resolver_result = ShellResolverResult(
            executable=process_args[0],
            shell_family="direct",
            argv_prefix=[],
            source="argv",
        )

    stdout_fh = open(stdout_path, "w", encoding="utf-8") if capture else None  # noqa: SIM115
    stderr_fh = open(stderr_path, "w", encoding="utf-8") if capture else None  # noqa: SIM115

    try:
        proc = subprocess.Popen(  # noqa: S603
            process_args,
            stdout=stdout_fh or subprocess.PIPE,
            stderr=stderr_fh or subprocess.PIPE,
            cwd=str(root),
        )

        tracked = TrackedProcess(
            pid=proc.pid,
            command=command_display,
            started=started,
            timeout=timeout,
        )
        pid_file = _write_pid_file(root, tracked)

        start = time.monotonic()
        timed_out = False

        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_process(proc.pid)
            proc.wait(timeout=5)  # Reap zombie

        duration = time.monotonic() - start
        exit_code = proc.returncode if proc.returncode is not None else -1

        # Clean up PID file
        if pid_file.exists():
            pid_file.unlink()

        return ExecResult(
            command=command_display,
            exit_code=124 if timed_out else exit_code,
            pid=proc.pid,
            duration=duration,
            timed_out=timed_out,
            stdout_file=str(stdout_path) if capture else "",
            stderr_file=str(stderr_path) if capture else "",
            shell_family=resolver_result.shell_family,
            shell_path=resolver_result.executable,
        )

    finally:
        if stdout_fh:
            stdout_fh.close()
        if stderr_fh:
            stderr_fh.close()


def list_processes(root: Path) -> list[TrackedProcess]:
    """List all tracked processes. Prunes stale PID files for dead processes."""
    pids_dir = _pids_dir(root)
    result: list[TrackedProcess] = []

    for pid_file in pids_dir.glob("*.json"):
        try:
            data = json.loads(pid_file.read_text(encoding="utf-8"))
            tp = TrackedProcess(**data)
            if _is_process_alive(tp.pid):
                result.append(tp)
            else:
                # Stale PID file — process already exited
                pid_file.unlink()
        except (json.JSONDecodeError, TypeError, OSError):
            pid_file.unlink(missing_ok=True)

    return result


def abort_process(root: Path, pid: int) -> bool:
    """Abort a specific tracked process by PID. Returns True if killed."""
    killed = _kill_process(pid)
    _remove_pid_file(root, pid)
    return killed


def abort_all(root: Path) -> list[int]:
    """Abort all tracked processes. Returns list of killed PIDs."""
    killed: list[int] = []
    for tp in list_processes(root):
        if _kill_process(tp.pid):
            killed.append(tp.pid)
        _remove_pid_file(root, tp.pid)
    return killed
