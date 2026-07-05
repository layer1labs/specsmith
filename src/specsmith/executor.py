# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Executor — cross-platform process execution with PID tracking and abort.

Provides governed command execution with:
- PID file tracking in .specsmith/pids/
- Configurable timeout enforcement
- Cross-platform abort (Windows taskkill / POSIX SIGTERM+SIGKILL)
- Process listing for agent visibility
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


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
    command: str,
    *,
    timeout: int = 120,
    capture: bool = True,
) -> ExecResult:
    """Execute a command with PID tracking and timeout enforcement.

    - Writes PID file to .specsmith/pids/<pid>.json
    - Enforces timeout via subprocess.Popen + polling
    - Logs stdout/stderr to .specsmith/logs/
    - Cleans up PID file on completion
    - Cross-platform: works on Windows, Linux, macOS
    """
    started = datetime.now(tz=timezone.utc).isoformat()
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")

    stdout_path = _logs_dir(root) / f"exec_{ts}.stdout"
    stderr_path = _logs_dir(root) / f"exec_{ts}.stderr"

    # Determine shell
    if sys.platform == "win32":
        shell_args: list[str] = ["cmd", "/c", command]
    else:
        shell_args = ["bash", "-c", command]

    stdout_fh = open(stdout_path, "w", encoding="utf-8") if capture else None  # noqa: SIM115
    stderr_fh = open(stderr_path, "w", encoding="utf-8") if capture else None  # noqa: SIM115

    try:
        proc = subprocess.Popen(  # noqa: S603
            shell_args,
            stdout=stdout_fh or subprocess.PIPE,
            stderr=stderr_fh or subprocess.PIPE,
            cwd=str(root),
        )

        tracked = TrackedProcess(
            pid=proc.pid,
            command=command,
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
            command=command,
            exit_code=124 if timed_out else exit_code,
            pid=proc.pid,
            duration=duration,
            timed_out=timed_out,
            stdout_file=str(stdout_path) if capture else "",
            stderr_file=str(stderr_path) if capture else "",
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
