# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Rebuildable two-tier ESDB test harness (REQ-365, REQ-366).

Builds specsmith into a fresh, isolated virtual environment from scratch and
validates BOTH Epistemic State Database backends end-to-end:

  * Free tier        SQLite backend (built-in, MIT; no license, no chronomemory)
  * Commercial tier  ChronoStore backend (chronomemory + valid Ed25519 license)

This mirrors the CI "esdb-backends" job (.github/workflows/ci.yml) but runs
locally and cross-platform, so contributors can prove both tiers work before
pushing to git / PyPI. The commercial tier is skipped automatically when the
chronomemory source or a license is unavailable, keeping the free SQLite tier
the zero-config default for this OSS project.

Non-destructive: every backend dogfood command ("esdb status" / "esdb migrate")
runs against an isolated COPY of .specsmith/, never the live tracked stores, so
your working tree is never mutated. (This matters because "esdb status"
auto-promotes SQLite records into ChronoStore in non-interactive mode.)

Usage (from the repo root):
    py scripts/dev/test_esdb_backends.py                  # both tiers, ESDB set
    py scripts/dev/test_esdb_backends.py --full           # whole suite per tier
    py scripts/dev/test_esdb_backends.py --free-only      # SQLite tier only
    py scripts/dev/test_esdb_backends.py --chrono-only    # ChronoStore tier only
    py scripts/dev/test_esdb_backends.py --keep-venv      # keep the temp venv
    py scripts/dev/test_esdb_backends.py --chronomemory-src ../chronomemory

On Windows, prefer the wrapper so Unicode renders correctly:
    .\\scripts\\dev\\test-esdb-backends.ps1 --full

Exit code is non-zero if any executed tier fails. A skipped commercial tier
(missing chronomemory/license) does NOT fail the run unless --chrono-only was
requested.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(os.path.realpath(__file__))
DEFAULT_REPO_ROOT = SCRIPT.parents[2]

# Env flags applied to every child process. Mirrors the CI esdb-backends job.
ENV_FLAGS = {
    "SPECSMITH_ALLOW_NON_PIPX": "1",
    "SPECSMITH_NO_AUTO_UPDATE": "1",
    "SPECSMITH_PYPI_CHECKED": "1",
    "PYTHONUTF8": "1",
    "PYTHONIOENCODING": "utf-8",
}

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"

# Extra ESDB-adjacent test files that are not matched by the test_esdb*.py glob.
EXTRA_ESDB_TESTS = (
    "tests/test_sqlite_parity.py",
    "tests/test_trace_vault_esdb.py",
    "tests/test_deprecation_registry.py",
)


def log(msg: str = "") -> None:
    print(msg, flush=True)


def section(title: str) -> None:
    log("")
    log("=" * 72)
    log(title)
    log("=" * 72)


def base_env(overrides: dict[str, str | None] | None = None) -> dict[str, str]:
    """Build a child-process environment.

    Always drops PYTHONPATH (so a leaked ``...\\src`` from the parent shell can
    never shadow the installed wheel) and applies the shared ENV_FLAGS. Values
    in *overrides* set or, when None, unset a variable.
    """
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.update(ENV_FLAGS)
    if overrides:
        for key, value in overrides.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
    return env


def run(
    cmd: list[str],
    *,
    cwd: Path,
    env_overrides: dict[str, str | None] | None = None,
    stream: bool = False,
    stderr_inherit: bool = False,
    timeout: int | None = None,
) -> tuple[int, str, str]:
    """Run *cmd* and return ``(returncode, stdout, stderr)``.

    - *stream*: output streams live to the console; returned stdout/stderr empty.
    - *stderr_inherit*: capture stdout (for JSON) but let stderr stream live so
      long-running progress (e.g. ChronoStore promotion) stays visible.
    - otherwise both streams are captured.

    stdin is always DEVNULL so a child that probes for a TTY (e.g. ChronoStore's
    SQLite->ChronoStore promotion prompt) never blocks on input(). On timeout the
    return code is 124.
    """
    env = base_env(env_overrides)
    common: dict[str, object] = {
        "cwd": str(cwd),
        "env": env,
        "check": False,
        "stdin": subprocess.DEVNULL,
    }
    try:
        if stream:
            proc = subprocess.run(cmd, timeout=timeout, **common)
            return proc.returncode, "", ""
        if stderr_inherit:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                **common,
            )
            return proc.returncode, proc.stdout or "", ""
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            **common,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout}s"


def extract_json(text: str) -> dict | None:
    """Parse a JSON object from *text*, tolerating leading/trailing noise."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return None
    return None


def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _on_rm_error(func, path, _exc):
    """Clear the read-only bit and retry (Windows leaves locked/RO files).

    Matches the shutil.rmtree onerror signature ``(func, path, exc_info)``.
    """
    with contextlib.suppress(OSError):
        os.chmod(path, stat.S_IWRITE)
        func(path)


def rmtree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, onerror=_on_rm_error)


def find_chronomemory_src(repo_root: Path, explicit: str | None) -> Path | None:
    """Locate a pip-installable chronomemory source (must contain pyproject.toml)."""
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    env_src = os.environ.get("SPECSMITH_CHRONOMEMORY_SRC", "").strip()
    if env_src:
        candidates.append(Path(env_src))
    candidates.append(repo_root / "crates" / "chronomemory")
    candidates.append(repo_root.parent / "chronomemory")
    for cand in candidates:
        if (cand / "pyproject.toml").is_file():
            return Path(os.path.realpath(str(cand)))
    return None


def find_license(explicit: str | None) -> Path | None:
    if explicit:
        path = Path(explicit).expanduser()
    else:
        env_key = os.environ.get("SPECSMITH_ESDB_KEY", "").strip()
        path = Path(env_key).expanduser() if env_key else Path.home() / ".specsmith" / "esdb.key"
    return path if path.is_file() else None


def _resolve_python(cmd: list[str]) -> str | None:
    """Return ``sys.executable`` reported by *cmd*, or None if it does not run."""
    try:
        proc = subprocess.run(
            [*cmd, "-c", "import sys; print(sys.executable)"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    path = proc.stdout.strip()
    if proc.returncode == 0 and path and os.path.isfile(path):
        return path
    return None


def select_base_python(explicit: str | None) -> str:
    """Pick the interpreter used to build the venv.

    specsmith is tested on Python 3.10-3.13 (CI matrix + trove classifiers);
    newer interpreters such as 3.14 are not yet a supported target. When the
    launcher default (e.g. the Windows ``py`` launcher) resolves to an
    interpreter outside that range, fall back to a supported one so the harness
    exercises specsmith on a CI-aligned Python. Override with ``--python``.
    """
    if explicit:
        return explicit
    if (3, 10) <= sys.version_info[:2] <= (3, 13):
        return sys.executable
    if os.name == "nt":
        candidates = [["py", "-3.13"], ["py", "-3.12"], ["py", "-3.11"], ["py", "-3.10"]]
    else:
        candidates = [["python3.13"], ["python3.12"], ["python3.11"], ["python3.10"]]
    for cand in candidates:
        resolved = _resolve_python(cand)
        if resolved:
            return resolved
    return sys.executable


class Harness:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.repo_root = Path(os.path.realpath(args.repo_root))
        base = Path(args.venv).parent if args.venv else Path(tempfile.gettempdir())
        self.base_dir = base / "specsmith-esdb-harness"
        self.venv_dir = Path(args.venv) if args.venv else self.base_dir / "venv"
        self.work_dir = self.base_dir / "work"
        self.dist_dir = self.base_dir / "dist"
        self.results: list[tuple[str, str, str, str]] = []  # tier, name, status, detail
        self.wheel: Path | None = None
        self.base_installed = False

    # -- result tracking ---------------------------------------------------
    def record(self, tier: str, name: str, status: str, detail: str = "") -> bool:
        self.results.append((tier, name, status, detail))
        marker = {PASS: "[PASS]", FAIL: "[FAIL]", SKIP: "[SKIP]"}[status]
        suffix = f" - {detail}" if detail else ""
        log(f"{marker} {tier}: {name}{suffix}")
        return status != FAIL

    def fail_output(self, name: str, rc: int, out: str, err: str) -> None:
        log(f"  ! {name} exited {rc}")
        tail = (out + err).strip().splitlines()
        for line in tail[-40:]:
            log(f"  | {line}")

    # -- venv interpreter helpers -----------------------------------------
    @property
    def py(self) -> str:
        return str(venv_python(self.venv_dir))

    def pytest_args(self) -> list[str]:
        if self.args.full:
            targets = ["tests"]
        else:
            globbed = sorted(p.as_posix() for p in self.repo_root.glob("tests/test_esdb*.py"))
            extras = [t for t in EXTRA_ESDB_TESTS if (self.repo_root / t).is_file()]
            # Use repo-relative paths (pytest runs with cwd=repo_root).
            targets = [Path(g).relative_to(self.repo_root).as_posix() for g in globbed] + extras
        args = ["-p", "no:cacheprovider", "--tb=short"]
        args.append("-v" if self.args.verbose else "-q")
        if not self.args.editable:
            # Clear pyproject's `pythonpath = ["src"]` so imports resolve to the
            # installed wheel, not the working-tree source.
            args += ["-o", "pythonpath="]
        return args + targets

    # -- phases ------------------------------------------------------------
    def build_venv(self) -> bool:
        section("Build isolated virtual environment")
        rmtree(self.venv_dir)
        rmtree(self.work_dir)
        rmtree(self.dist_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        python = select_base_python(self.args.python)
        log(f"  python: {python}")
        log(f"  venv:   {self.venv_dir}")
        rc, out, err = run(
            [python, "-m", "venv", str(self.venv_dir)],
            cwd=self.repo_root,
            timeout=self.args.timeout,
        )
        if rc != 0:
            self.fail_output("venv create", rc, out, err)
            return self.record("setup", "create venv", FAIL)
        rc, out, err = run(
            [self.py, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel", "-q"],
            cwd=self.repo_root,
            stream=self.args.verbose,
            timeout=self.args.timeout,
        )
        if rc != 0:
            self.fail_output("pip upgrade", rc, out, err)
            return self.record("setup", "upgrade pip", FAIL)
        return self.record("setup", "create venv", PASS, str(self.venv_dir))

    def build_wheel(self) -> bool:
        if self.args.editable:
            return self.record("setup", "build wheel", SKIP, "editable mode")
        section("Build wheel (packaging validation)")
        rmtree(self.dist_dir)
        self.dist_dir.mkdir(parents=True, exist_ok=True)
        rc, out, err = run(
            [self.py, "-m", "pip", "wheel", ".", "--no-deps", "-w", str(self.dist_dir), "-q"],
            cwd=self.repo_root,
            stream=self.args.verbose,
            timeout=self.args.timeout,
        )
        if rc != 0:
            self.fail_output("pip wheel", rc, out, err)
            return self.record("setup", "build wheel", FAIL)
        wheels = sorted(self.dist_dir.glob("specsmith-*.whl"))
        if not wheels:
            return self.record("setup", "build wheel", FAIL, "no wheel produced")
        self.wheel = wheels[-1]
        return self.record("setup", "build wheel", PASS, self.wheel.name)

    def install_base(self, tier: str) -> bool:
        if self.args.editable:
            spec = ".[dev]"
            cmd = [self.py, "-m", "pip", "install", "-e", spec, "-q"]
        else:
            assert self.wheel is not None
            spec = f"{self.wheel}[dev]"
            cmd = [self.py, "-m", "pip", "install", spec, "-q"]
        rc, out, err = run(
            cmd, cwd=self.repo_root, stream=self.args.verbose, timeout=self.args.timeout
        )
        if rc != 0:
            self.fail_output("pip install", rc, out, err)
            return self.record(tier, "install specsmith[dev]", FAIL)
        self.base_installed = True
        return self.record(tier, "install specsmith[dev]", PASS, spec)

    def scratch_project(self, name: str) -> Path:
        """Return a fresh scratch project dir containing a COPY of .specsmith/."""
        dest = self.work_dir / name
        rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)
        src = self.repo_root / ".specsmith"
        if src.is_dir():
            shutil.copytree(src, dest / ".specsmith")
        return dest

    def esdb_status(
        self, tier: str, scratch: Path, overrides: dict[str, str | None]
    ) -> dict | None:
        rc, out, err = run(
            [self.py, "-m", "specsmith", "esdb", "status", "--project-dir", str(scratch), "--json"],
            cwd=self.repo_root,
            env_overrides=overrides,
            stderr_inherit=True,
            timeout=self.args.timeout,
        )
        data = extract_json(out)
        if rc != 0 or data is None:
            self.fail_output("esdb status", rc, out, err)
            return None
        return data

    def free_tier(self) -> bool:
        section("Free tier - SQLite backend (no chronomemory, no license)")
        if not self.install_base("free"):
            return False
        scratch = self.scratch_project("free")
        data = self.esdb_status("free", scratch, {"SPECSMITH_ESDB_BACKEND": "sqlite"})
        if data is None:
            return self.record("free", "esdb status backend", FAIL)
        backend = data.get("backend")
        ok = backend == "sqlite"
        self.record(
            "free",
            "esdb status backend",
            PASS if ok else FAIL,
            f"backend={backend}, records={data.get('record_count')}",
        )
        section("Free tier - pytest")
        rc, _, _ = run(
            [self.py, "-m", "pytest", *self.pytest_args()],
            cwd=self.repo_root,
            env_overrides={"SPECSMITH_ESDB_BACKEND": "sqlite"},
            stream=True,
        )
        self.record("free", "pytest", PASS if rc == 0 else FAIL, f"exit {rc}")
        return ok and rc == 0

    def commercial_tier(self) -> bool:
        section("Commercial tier - ChronoStore backend (chronomemory + license)")
        chrono_src = find_chronomemory_src(self.repo_root, self.args.chronomemory_src)
        license_path = find_license(self.args.license_key)
        required = self.args.chrono_only
        if chrono_src is None and not self.args.allow_pypi_chrono:
            status = FAIL if required else SKIP
            self.record(
                "commercial",
                "chronomemory source",
                status,
                "no local source (set --chronomemory-src or --allow-pypi-chrono)",
            )
            return not required
        if license_path is None:
            status = FAIL if required else SKIP
            self.record(
                "commercial",
                "license file",
                status,
                "no license (set --license-key or ~/.specsmith/esdb.key)",
            )
            return not required

        if not self.base_installed and not self.install_base("commercial"):
            return False

        if chrono_src is not None:
            cmd = [self.py, "-m", "pip", "install", str(chrono_src), "-q"]
            src_label = str(chrono_src)
        else:
            cmd = [self.py, "-m", "pip", "install", "chronomemory>=0.2.7", "-q"]
            src_label = "PyPI chronomemory>=0.2.7"
        rc, out, err = run(
            cmd, cwd=self.repo_root, stream=self.args.verbose, timeout=self.args.timeout
        )
        if rc != 0:
            self.fail_output("pip install chronomemory", rc, out, err)
            return self.record("commercial", "install chronomemory", FAIL)
        self.record("commercial", "install chronomemory", PASS, src_label)

        lic_overrides = {"SPECSMITH_ESDB_KEY": str(license_path), "SPECSMITH_ESDB_BACKEND": None}
        verify = (
            "import os, sys;"
            "from specsmith.esdb._license import verify_license_file as v;"
            "s = v(os.environ['SPECSMITH_ESDB_KEY']);"
            "print(s.customer or '', s.expires_at or '');"
            "sys.exit(0 if s.valid else 1)"
        )
        rc, out, err = run(
            [self.py, "-c", verify],
            cwd=self.repo_root,
            env_overrides=lic_overrides,
            timeout=self.args.timeout,
        )
        if rc != 0:
            self.fail_output("license verify", rc, out, err)
            return self.record("commercial", "license valid", FAIL)
        self.record("commercial", "license valid", PASS, out.strip() or str(license_path))

        scratch = self.scratch_project("chrono")
        rc, out, err = run(
            [
                self.py,
                "-m",
                "specsmith",
                "esdb",
                "migrate",
                "--project-dir",
                str(scratch),
                "--json",
            ],
            cwd=self.repo_root,
            env_overrides=lic_overrides,
            timeout=self.args.timeout,
        )
        migrate = extract_json(out)
        migrate_ok = rc == 0 and bool(migrate and migrate.get("ok"))
        if not migrate_ok:
            self.fail_output("esdb migrate", rc, out, err)
        self.record("commercial", "esdb migrate", PASS if migrate_ok else FAIL)

        log(
            "  Opening ChronoStore and promoting copied .specsmith records "
            "(first run can take ~30-60s)..."
        )
        data = self.esdb_status("commercial", scratch, lic_overrides)
        if data is None:
            self.record("commercial", "esdb status backend", FAIL)
            status_ok = False
        else:
            backend = data.get("backend")
            active = bool(data.get("license", {}).get("active"))
            status_ok = backend == "chronomemory" and active
            self.record(
                "commercial",
                "esdb status backend",
                PASS if status_ok else FAIL,
                f"backend={backend}, license_active={active}, records={data.get('record_count')}",
            )

        section("Commercial tier - pytest")
        rc, _, _ = run(
            [self.py, "-m", "pytest", *self.pytest_args()],
            cwd=self.repo_root,
            env_overrides={"SPECSMITH_ESDB_KEY": str(license_path)},
            stream=True,
        )
        self.record("commercial", "pytest", PASS if rc == 0 else FAIL, f"exit {rc}")
        return migrate_ok and status_ok and rc == 0

    # -- orchestration -----------------------------------------------------
    def run_all(self) -> int:
        try:
            if not self.build_venv():
                return self.finish()
            if not self.build_wheel():
                return self.finish()
            if not self.args.chrono_only:
                self.free_tier()
            if not self.args.free_only:
                self.commercial_tier()
        finally:
            if not self.args.keep_venv:
                rmtree(self.base_dir)
                rmtree(self.venv_dir)
            else:
                log(f"\nKept venv: {self.venv_dir}")
        return self.finish()

    def finish(self) -> int:
        section("Summary")
        for tier, name, status, detail in self.results:
            marker = {PASS: "[PASS]", FAIL: "[FAIL]", SKIP: "[SKIP]"}[status]
            suffix = f" - {detail}" if detail else ""
            log(f"  {marker} {tier}: {name}{suffix}")
        failed = [r for r in self.results if r[2] == FAIL]
        overall = FAIL if failed else PASS
        log("")
        log(f"Overall: {overall}")
        return 1 if failed else 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuildable two-tier (SQLite + ChronoStore) ESDB test harness.",
    )
    parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    parser.add_argument("--free-only", action="store_true", help="Run only the SQLite tier.")
    parser.add_argument(
        "--chrono-only",
        action="store_true",
        help="Run only the ChronoStore tier (fails if chronomemory/license missing).",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run the entire pytest suite per tier instead of the ESDB-focused set.",
    )
    parser.add_argument(
        "--editable",
        action="store_true",
        help="Use `pip install -e .` (CI-style) instead of building+installing a wheel.",
    )
    parser.add_argument("--chronomemory-src", default=None, help="Path to chronomemory source.")
    parser.add_argument("--license-key", default=None, help="Path to the ESDB license key file.")
    parser.add_argument(
        "--allow-pypi-chrono",
        action="store_true",
        help="Allow installing chronomemory from PyPI when no local source is found.",
    )
    parser.add_argument("--venv", default=None, help="Explicit venv path (default: temp dir).")
    parser.add_argument("--keep-venv", action="store_true", help="Do not delete the temp venv.")
    parser.add_argument("--python", default=None, help="Base interpreter for the venv.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Per-command timeout (seconds) for captured steps (default: 900).",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Stream all subprocess output."
    )
    args = parser.parse_args(argv)
    if args.free_only and args.chrono_only:
        parser.error("--free-only and --chrono-only are mutually exclusive")
    return args


def main(argv: list[str] | None = None) -> int:
    for stream_obj in (sys.stdout, sys.stderr):
        if hasattr(stream_obj, "reconfigure"):
            stream_obj.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    return Harness(args).run_all()


if __name__ == "__main__":
    raise SystemExit(main())
