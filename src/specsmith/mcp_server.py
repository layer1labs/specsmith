# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""specsmith MCP Server — native governance tool server (REQ-363).

Implements the Model Context Protocol (MCP) over stdio (JSON-RPC 2.0).
Any MCP client (Warp/Oz, Cursor, Claude Code) can add specsmith as a
tool server to call governance commands as structured tool calls.

Start with:
    specsmith mcp serve [--project-dir .]

Warp MCP config (Settings → Agents → MCP servers):
    {
      "specsmith-governance": {
        "command": "specsmith",
        "args": ["mcp", "serve"]
      }
    }

Tools exposed
-------------
governance_audit        Run governance audit; returns health + check results.
governance_checkpoint   Emit GOVERNANCE ANCHOR JSON (phase, health, counts).
governance_preflight    Preflight a change intent; returns decision + work_item_id.
governance_phase        Current AEE phase, readiness %, and failing checks.
governance_req_list     List all requirements (id, title, status, covered).
governance_trace_seal   Seal a milestone/decision in the cryptographic trace vault.

Protocol
--------
MCP pin: 2024-11-05 (current stable).
Transport: stdio (newline-delimited JSON-RPC 2.0).
No external dependencies — stdlib only + existing specsmith modules.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# MCP protocol constants
# ---------------------------------------------------------------------------

MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "specsmith-governance"
SERVER_VERSION = "0.13.0"

# ---------------------------------------------------------------------------
# Multi-project state — populated by run_server() at startup
# ---------------------------------------------------------------------------

# Default project dir used when a tool call omits ``project_dir``.
_DEFAULT_PROJECT_DIR: str = "."

# All registered project directories (absolute paths), default first.
_REGISTERED_PROJECTS: list[str] = []

# Registry mutations may come from multiple MCP clients in one process or from
# separate CLI processes.  A process-local re-entrant lock prevents same-process
# read/modify/write races; the adjacent lock file serializes cooperating
# processes on Windows, Linux, and macOS without platform-specific APIs.
_REGISTRY_THREAD_LOCK = threading.RLock()
_REGISTRY_LOCK_TIMEOUT_SECONDS = 5.0
_REGISTRY_LOCK_POLL_SECONDS = 0.05
_REGISTRY_STALE_LOCK_SECONDS = 60.0
_REGISTRY_IO_RETRY_ATTEMPTS = 6
_REGISTRY_IO_RETRY_SECONDS = 0.025


def _retry_registry_permission_error(operation: Callable[[], None]) -> None:
    """Retry a short registry filesystem operation after transient denial.

    Windows virus scanners and file indexers can briefly retain a handle after
    it is closed, causing ``os.replace`` or ``Path.unlink`` to raise WinError 5
    or 32.  A bounded retry keeps registry mutations atomic without hiding a
    persistent permissions problem.
    """
    for attempt in range(_REGISTRY_IO_RETRY_ATTEMPTS):
        try:
            operation()
            return
        except PermissionError:
            if attempt + 1 >= _REGISTRY_IO_RETRY_ATTEMPTS:
                raise
            time.sleep(_REGISTRY_IO_RETRY_SECONDS)


# ---------------------------------------------------------------------------
# Persistent project registry  (~/.specsmith/mcp-projects.json)
# ---------------------------------------------------------------------------

# Patterns that identify a path as transient/temporary.
# These match the *last path component* (the project directory itself),
# not arbitrary substrings in parent directories.
_TEMP_SUFFIXES = (
    "/pytest",
    "\\pytest",
    "/pytest-",
    "\\pytest-",
    "/tmp",
    "\\tmp",
    "/temp",
    "\\temp",
    "/__pycache__",
    "\\__pycache__",
    "/.vite/",
    "/.svelte-kit/",
    "/.next/",
    "/node_modules/.cache/",
    "/.tox/",
    "/.nox/",
    "/.eggs/",
    "/.dist-info/",
)

# Specsmith project markers that indicate a valid project root.
_PROJECT_MARKERS = (
    ".specsmith",
    "AGENTS.md",
    "ARCHITECTURE.md",
    "docs/SPECSMITH.yml",
    "docs/REQUIREMENTS.md",
)


def _registry_file() -> Path:
    """Return the path to the user-level MCP project registry file.

    Respects ``SPECSMITH_HOME`` if set; otherwise uses
    ``~/.specsmith/mcp-projects.json``.
    """
    base = os.environ.get("SPECSMITH_HOME", "").strip()
    home = Path(base) if base else Path.home() / ".specsmith"
    return home / "mcp-projects.json"


def _registry_lock_file() -> Path:
    """Return the cooperative cross-process lock path for the registry."""
    registry = _registry_file()
    return registry.with_name(f".{registry.name}.lock")


@contextmanager
def _registry_mutation_lock(timeout: float = _REGISTRY_LOCK_TIMEOUT_SECONDS) -> Iterator[None]:
    """Serialize a complete registry mutation across threads and processes.

    ``O_CREAT | O_EXCL`` is portable to the supported platforms.  A stale lock
    can only be reclaimed after a generous interval, preventing a crashed
    process from permanently disabling a user's registry while avoiding removal
    of an active short-lived mutation.
    """
    lock_path = _registry_lock_file()
    deadline = time.monotonic() + timeout
    with _REGISTRY_THREAD_LOCK:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor: int | None = None
        while descriptor is None:
            try:
                descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
            except FileExistsError:
                try:
                    age = time.time() - lock_path.stat().st_mtime
                    if age > _REGISTRY_STALE_LOCK_SECONDS:
                        lock_path.unlink(missing_ok=True)
                        continue
                except OSError:
                    # Another process may have released or replaced the lock.
                    continue
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"Timed out waiting for MCP registry lock: {lock_path}"
                    ) from None
                time.sleep(_REGISTRY_LOCK_POLL_SECONDS)
        try:
            yield
        finally:
            os.close(descriptor)
            with suppress(FileNotFoundError):
                _retry_registry_permission_error(lock_path.unlink)


def _is_temp_path(path: str) -> bool:
    """Return True if *path* looks like a temporary or transient directory.

    Checks the *last path component* (the project directory name itself)
    against known temp prefixes.  Also checks the immediate parent directory
    for pytest-specific patterns (e.g. ``pytest-of-user``, ``pytest123``).
    This catches paths like ``pytest-of-user/pytest123/test0`` without
    false-positives on the pytest temp directory that pytest creates for
    the test run itself (e.g. ``pytest-1031/test_func/proj``).
    """
    p = Path(path)
    parts = p.parts
    explicit_home = os.environ.get("SPECSMITH_HOME", "").strip()
    if explicit_home:
        with suppress(OSError, ValueError):
            parts = p.resolve().relative_to(Path(explicit_home).resolve()).parts

    for index, component in enumerate(parts):
        lowered = component.lower()
        if (
            lowered in {"pytest", ".pytest_tmp"}
            or lowered.startswith(("pytest-", "pytest-of-", "pytest_of_"))
            or (lowered.startswith("pytest") and lowered[6:].isdigit())
        ):
            return True
        if lowered in {"tmp", "temp"} and (not explicit_home or index == len(parts) - 1):
            return True
        if lowered in {"__pycache__", ".vite", ".svelte-kit", ".next", ".tox", ".nox"}:
            return True

    name = p.name.lower() if p.name else path.lower()
    path_lower = path.lower()
    for suffix in _TEMP_SUFFIXES:
        if suffix.endswith("/"):
            # Match parent directory patterns like /__pycache__/
            if suffix[1:] in path_lower:
                return True
        else:
            pattern = suffix[1:].lower()
            # Match the last component: pytest-*, tmp, temp, etc.
            if name == pattern or name.startswith(pattern + "-"):
                return True
            # Also check the immediate parent directory for pytest patterns.
            # This catches paths like pytest-of-user/pytest123/test0 where
            # the parent (pytest123) is a pytest temp directory.
            if pattern.startswith("pytest") and len(p.parts) >= 2:
                parent = p.parts[-2].lower()
                if parent == pattern or parent.startswith(pattern + "-"):
                    return True
                # Also match pytest-* and pytestNNN patterns in parent.
                if pattern == "pytest":
                    if parent.startswith("pytest-"):
                        return True
                    if parent.startswith("pytest") and len(parent) > 6:
                        return True
    return False


def _is_valid_project(path: Path) -> bool:
    """Return True if *path* looks like a Specsmith project root.

    A path is considered valid if it is a directory and contains at least
    one recognized project marker file/directory.
    """
    if not path.is_dir():
        return False
    # Always accept if it has the specsmith marker.
    return any((path / marker).exists() for marker in _PROJECT_MARKERS)


def _canonicalize_path(path: str) -> str:
    """Canonicalize a path for deduplication.

    - Resolves symlinks and normalizes separators.
    - On Windows, normalizes drive letter case and backslashes.
    """
    p = Path(path).resolve()
    result = str(p)
    # Windows: normalize drive letter to uppercase.
    if result and result[1:2] == ":":
        result = result[0].upper() + result[1:]
    return result


def _paths_equivalent(left: str, right: str) -> bool:
    """Return whether two path spellings identify the same filesystem entry.

    Canonical string equality handles missing and ordinary paths.  ``samefile``
    additionally handles case variants on case-insensitive filesystems without
    conflating distinct entries on case-sensitive filesystems.
    """
    if left == right:
        return True
    try:
        return Path(left).samefile(right)
    except OSError:
        return False


def _load_registry_raw() -> tuple[list[Any], dict[str, Any] | None]:
    """Load the registry file, returning (projects_list, full_data_or_None).

    Returns an empty list and None when the file is missing or malformed.
    """
    try:
        data = json.loads(_registry_file().read_text(encoding="utf-8"))
        if isinstance(data, dict):
            projects = data.get("projects", [])
            if isinstance(projects, list):
                return projects, data
        return [], None
    except Exception:  # noqa: BLE001
        return [], None


def _save_registry(projects: list[str]) -> None:
    """Atomically persist *projects* to the registry file.

    Uses a write-to-temp-then-rename pattern so an interrupted write
    preserves the prior valid registry.
    """
    reg = _registry_file()
    reg.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"projects": projects}, indent=2, ensure_ascii=False)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{reg.stem}.", suffix=".tmp", dir=reg.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as temporary:
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
        _retry_registry_permission_error(lambda: os.replace(temporary_name, reg))
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def _repair_registry_entries(projects: list[Any]) -> tuple[list[str], bool]:
    """Return safe registry strings and whether persisted data needs repair."""
    repaired: list[str] = []
    seen: set[str] = set()
    changed = False
    for project in projects:
        if not isinstance(project, str) or not project.strip() or _is_temp_path(project):
            changed = True
            continue
        if project in seen:
            changed = True
            continue
        seen.add(project)
        repaired.append(project)
    return repaired, changed


def read_registry() -> list[str]:
    """Return all absolute project paths from the registry.

    Returns an empty list when the registry file is missing or malformed.
    Invalid entries (empty strings, non-strings) are silently skipped.
    Paths are canonicalized and deduplicated.
    """
    projects, _ = _load_registry_raw()
    projects, changed = _repair_registry_entries(projects)
    if changed:
        with _registry_mutation_lock():
            latest, _ = _load_registry_raw()
            projects, latest_changed = _repair_registry_entries(latest)
            if latest_changed:
                _save_registry(projects)

    canonical: list[str] = []
    for p in projects:
        if not isinstance(p, str) or not p:
            continue
        c = _canonicalize_path(p)
        if not any(_paths_equivalent(c, existing) for existing in canonical):
            canonical.append(c)
    return canonical


def write_registry(paths: list[str]) -> None:
    """Persist *paths* to the registry file atomically."""
    with _registry_mutation_lock():
        _save_registry(paths)


def register_project(path: str = ".", *, allow_uninitialized: bool = False) -> bool:
    """Add *path* to the registry. Returns True if it was newly added.

    Parameters
    ----------
    path:
        Project directory to register.
    allow_uninitialized:
        When False (default), the path must exist and contain at least one
        Specsmith project marker (``.specsmith/``, ``AGENTS.md``, etc.).
        When True, any existing directory is accepted.

    The registry is validated, canonicalized, deduplicated, and written
    atomically.  Temporary/transient paths (pytest temp dirs, deleted
    worktrees) are rejected.
    """
    abs_path = Path(path).resolve()
    canonical = _canonicalize_path(str(abs_path))

    # Reject temp/transient paths.
    if _is_temp_path(canonical):
        return False

    # Validate the path.
    if not allow_uninitialized and not _is_valid_project(abs_path):
        return False

    with _registry_mutation_lock():
        projects, _ = _load_registry_raw()
        # Deduplicate using canonical form.
        filtered: list[str] = []
        for p in projects:
            if not isinstance(p, str) or _is_temp_path(p):
                continue
            c = _canonicalize_path(p)
            if not any(_paths_equivalent(c, existing) for existing in filtered):
                filtered.append(c)

        if any(_paths_equivalent(canonical, existing) for existing in filtered):
            return False  # Already registered.

        # Prepend so the new project becomes the default.
        filtered.insert(0, canonical)
        _save_registry(filtered)
        return True


def unregister_project(path: str = ".") -> bool:
    """Remove *path* from the registry. Returns True if it was present."""
    canonical = _canonicalize_path(path)
    with _registry_mutation_lock():
        projects, _ = _load_registry_raw()
        new_projects = [
            p
            for p in projects
            if isinstance(p, str)
            and not _is_temp_path(p)
            and not _paths_equivalent(_canonicalize_path(p), canonical)
        ]
        if len(new_projects) == len(projects):
            return False  # Not found.
        _save_registry(new_projects)
        return True


def prune_registry(*, dry_run: bool = False, stale_threshold_days: int = 30) -> dict[str, Any]:
    """Prune stale, inaccessible, or temporary entries from the registry.

    Parameters
    ----------
    dry_run:
        When True, report what *would* be removed without mutating the file.
    stale_threshold_days:
        Entries whose paths no longer exist are considered stale.  Only
        entries that have been stale for more than *stale_threshold_days*
        are removed (currently all missing entries are treated as stale).

    Returns
    -------
    A dict with keys ``removed``, ``preserved``, ``stale``, ``inaccessible``.
    """
    if dry_run:
        projects, _ = _load_registry_raw()
        return _prune_registry_projects(projects, dry_run=True)

    with _registry_mutation_lock():
        projects, _ = _load_registry_raw()
        return _prune_registry_projects(projects, dry_run=False)


def _prune_registry_projects(projects: list[Any], *, dry_run: bool) -> dict[str, Any]:
    """Analyze registry entries while the caller owns a mutation lock if needed."""
    removed: list[str] = []
    preserved: list[str] = []
    stale: list[str] = []
    inaccessible: list[str] = []

    canonical_projects: list[str] = []
    seen: set[str] = set()

    for p in projects:
        if not isinstance(p, str) or _is_temp_path(p):
            removed.append(str(p))
            continue
        c = _canonicalize_path(p)
        if c in seen:
            continue  # Skip duplicates.
        seen.add(c)

        proj_path = Path(c)
        if not proj_path.exists():
            stale.append(c)
            removed.append(c)
            continue

        if not proj_path.is_dir():
            stale.append(c)
            removed.append(c)
            continue

        # Path exists and is a directory — preserve it.
        canonical_projects.append(c)
        preserved.append(c)

    result = {
        "removed": removed,
        "preserved": preserved,
        "stale": stale,
        "inaccessible": inaccessible,
    }

    if not dry_run and removed:
        _save_registry(canonical_projects)

    return result


def build_warp_mcp_config() -> dict[str, Any]:
    """Build the Warp MCP server config snippet for the governance server.

    Shared by ``specsmith mcp install-warp`` and the ``warp`` integration
    adapter (REQ-444) so both emit an identical, registry-aware config.

    Executable detection (in priority order):
      1. ``specsmith`` / ``specsmith.exe`` on PATH — covers pipx shims and
         system installs.
      2. ``python -m specsmith`` via the current interpreter — reliable
         fallback for editable dev installs and venvs where the console-script
         wrapper is absent or resolves incorrectly (e.g. some Windows pipx setups).

    The env vars keep the server starting cleanly when Warp launches it directly:
    ``SPECSMITH_ALLOW_NON_PIPX`` prevents the pipx-enforcement gate from exiting
    before the MCP handshake; ``SPECSMITH_NO_AUTO_UPDATE`` / ``SPECSMITH_PYPI_CHECKED``
    suppress startup network calls so the server responds immediately.
    """
    import shutil

    server_env = {
        "SPECSMITH_ALLOW_NON_PIPX": "1",
        "SPECSMITH_NO_AUTO_UPDATE": "1",
        "SPECSMITH_PYPI_CHECKED": "1",
    }
    specsmith_exe = shutil.which("specsmith") or shutil.which("specsmith.exe")
    if specsmith_exe:
        cmd = specsmith_exe
        args: list[str] = ["mcp", "serve"]
    else:
        cmd = sys.executable
        args = ["-m", "specsmith", "mcp", "serve"]
    return {
        "specsmith-governance": {
            "command": cmd,
            "args": args,
            "env": server_env,
        },
    }


_TOOLS: list[dict[str, Any]] = [
    {
        "name": "governance_project_list",
        "description": (
            "List all project directories registered in this MCP server instance. "
            "Use the returned paths as the `project_dir` argument for other tools "
            "when working with multiple simultaneous projects."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "governance_audit",
        "description": (
            "Run the specsmith governance audit. Returns health status and a list of "
            "all check results (passed/failed/suppressed). Required before phase advance."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {
                    "type": "string",
                    "description": "Absolute or relative path to the project root. Defaults to '.'.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "governance_checkpoint",
        "description": (
            "Emit the GOVERNANCE ANCHOR — a compact JSON snapshot of the current "
            "governance state (phase, health, REQ/TEST counts, ESDB chain, work items). "
            "Include this verbatim in any context summary. Run every 8-10 turns."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {
                    "type": "string",
                    "description": "Absolute or relative path to the project root. Defaults to '.'.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "governance_preflight",
        "description": (
            "Run a governance preflight check for a proposed change. "
            "Returns decision ('accepted' / 'needs_clarification' / 'rejected'), "
            "work_item_id, and instruction. "
            "Never make a code change without an accepted preflight."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "description": "One sentence describing the change you intend to make.",
                },
                "project_dir": {
                    "type": "string",
                    "description": "Absolute or relative path to the project root. Defaults to '.'.",
                },
            },
            "required": ["intent"],
        },
    },
    {
        "name": "governance_phase",
        "description": (
            "Return the current AEE phase, readiness percentage, and any failing "
            "phase-readiness checks. The 7 phases are: inception → architecture → "
            "requirements → test_spec → implementation → verification → release."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {
                    "type": "string",
                    "description": "Absolute or relative path to the project root. Defaults to '.'.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "governance_req_list",
        "description": (
            "List all requirements in the project. Returns id, title, status, "
            "and whether the requirement has test coverage."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {
                    "type": "string",
                    "description": "Absolute or relative path to the project root. Defaults to '.'.",
                },
                "status_filter": {
                    "type": "string",
                    "description": "Filter by status: 'planned', 'implemented', 'partial', 'deprecated'. Omit for all.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "governance_trace_seal",
        "description": (
            "Seal a milestone, decision, or audit gate in the cryptographic trace vault. "
            "Creates a tamper-evident SealRecord chained to all prior seals. "
            "Required to advance the Release phase to 100%."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "seal_type": {
                    "type": "string",
                    "enum": [
                        "decision",
                        "milestone",
                        "audit-gate",
                        "logic-knot",
                        "stress-test",
                        "epistemic",
                    ],
                    "description": "Type of seal to create.",
                },
                "description": {
                    "type": "string",
                    "description": "Human-readable description of what is being sealed.",
                },
                "project_dir": {
                    "type": "string",
                    "description": "Absolute or relative path to the project root. Defaults to '.'.",
                },
                "author": {
                    "type": "string",
                    "description": "Author of this seal (default: 'specsmith-mcp').",
                },
            },
            "required": ["seal_type", "description"],
        },
    },
    {
        "name": "governance_context_transition",
        "description": (
            "Return Specsmith's authoritative context action and exact replacement "
            "packet digest. Zoo must not invoke native summarization in governed mode."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "telemetry": {"type": "object"},
                "task": {"type": "object"},
                "work_item_id": {"type": "string"},
                "invariants": {"type": "object"},
                "records": {"type": "array", "items": {"type": "object"}},
                "governed": {"type": "boolean", "default": True},
            },
            "required": ["telemetry", "task"],
        },
    },
    {
        "name": "governance_context_verify",
        "description": "Verify that Zoo applied the exact Specsmith context packet digest.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expected_digest": {"type": "string"},
                "applied_digest": {"type": "string"},
            },
            "required": ["expected_digest", "applied_digest"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool handler implementations
# ---------------------------------------------------------------------------


def _resolve_root(args: dict[str, Any]) -> Path:
    """Resolve project_dir from args, falling back to the server default.

    If ``project_dir`` is not in *args* (or is empty), we use
    ``_DEFAULT_PROJECT_DIR`` so callers don't have to repeat the path on
    every tool call when only one project is active.
    """
    raw = args.get("project_dir") or _DEFAULT_PROJECT_DIR
    return Path(str(raw)).resolve()


def _handle_governance_project_list(args: dict[str, Any]) -> dict[str, Any]:  # noqa: ARG001
    """Return the list of projects registered in this server instance."""
    return {
        "default_project": _DEFAULT_PROJECT_DIR,
        "projects": _REGISTERED_PROJECTS,
        "count": len(_REGISTERED_PROJECTS),
    }


def _handle_governance_audit(args: dict[str, Any]) -> dict[str, Any]:
    """Run the governance audit and return structured results."""
    root = _resolve_root(args)
    try:
        from specsmith.auditor import run_audit

        report = run_audit(root)
        return {
            "healthy": report.healthy,
            "passed": report.passed,
            "failed": report.failed,
            "fixable": report.fixable,
            "suppressed": report.suppressed_count,
            "checks": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "suppressed": r.suppressed,
                    "message": r.message,
                    "fixable": r.fixable,
                }
                for r in report.results
            ],
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "healthy": False, "passed": 0, "failed": -1, "checks": []}


def _handle_governance_checkpoint(args: dict[str, Any]) -> dict[str, Any]:
    """Emit a compact governance anchor JSON."""
    root = _resolve_root(args)
    import re

    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Project name
    project_name = root.name
    try:
        import yaml as _yaml

        from specsmith.paths import find_scaffold

        sp = find_scaffold(root)
        if sp:
            raw = _yaml.safe_load(sp.read_text(encoding="utf-8")) or {}
            project_name = str(raw.get("name", root.name))
    except Exception:  # noqa: BLE001
        pass

    # Phase
    phase_key, phase_label, phase_emoji, phase_pct = "unknown", "Unknown", "", 0
    failing_phase_checks: list[str] = []
    try:
        from specsmith.phase import (  # noqa: PLC0415
            PHASE_MAP,
            evaluate_phase,
            phase_progress_pct,
            read_phase,
        )

        phase_key = read_phase(root)
        phase = PHASE_MAP.get(phase_key)
        if phase:
            phase_label = phase.label
            phase_emoji = phase.emoji
            phase_pct = phase_progress_pct(phase, root)
            _, failing_phase_checks = evaluate_phase(phase, root)
    except Exception:  # noqa: BLE001
        pass

    # Audit health
    health_ok, audit_failed = True, 0
    try:
        from specsmith.auditor import run_audit

        report = run_audit(root)
        health_ok = report.healthy
        audit_failed = report.failed
    except Exception:  # noqa: BLE001
        pass

    # REQ / TEST counts
    req_count, test_count = 0, 0
    try:
        rp = root / ".specsmith" / "requirements.json"
        tp = root / ".specsmith" / "testcases.json"
        if rp.exists():
            req_count = len(json.loads(rp.read_text(encoding="utf-8")))
        if tp.exists():
            test_count = len(json.loads(tp.read_text(encoding="utf-8")))
    except Exception:  # noqa: BLE001
        pass

    # ESDB
    esdb_ok, esdb_records = True, 0
    try:
        from chronomemory import ChronoStore

        wal = root / ".chronomemory" / "events.wal"
        if wal.exists():
            with ChronoStore(root) as store:
                esdb_ok = store.chain_valid()
                esdb_records = store.record_count()
    except Exception:  # noqa: BLE001
        pass

    # Recent work items
    recent_wis: list[str] = []
    try:
        for cand in ["docs/LEDGER.md", "LEDGER.md"]:
            lp = root / cand
            if lp.exists():
                text = lp.read_text(encoding="utf-8", errors="ignore")
                wis = re.findall(r"\bWI-[A-F0-9]{8}\b", text)
                seen: set[str] = set()
                for wi in reversed(wis):
                    if wi not in seen:
                        seen.add(wi)
                        recent_wis.insert(0, wi)
                    if len(seen) >= 3:
                        break
                break
    except Exception:  # noqa: BLE001
        pass

    return {
        "anchor": f"SPECSMITH-ANCHOR-{ts}",
        "ts": ts,
        "project": project_name,
        "phase": phase_key,
        "phase_label": f"{phase_emoji} {phase_label}",
        "phase_pct": phase_pct,
        "phase_failing_checks": failing_phase_checks,
        "health": "clean" if health_ok else f"{audit_failed} issues",
        "audit_failed": audit_failed,
        "req_count": req_count,
        "test_count": test_count,
        "esdb_records": esdb_records,
        "esdb_chain_valid": esdb_ok,
        "recent_work_items": recent_wis,
    }


def _handle_governance_preflight(args: dict[str, Any]) -> dict[str, Any]:
    """Run a governance preflight check for the given intent."""
    intent = str(args.get("intent", "")).strip()
    if not intent:
        return {"decision": "rejected", "instruction": "intent is required", "work_item_id": ""}

    root = _resolve_root(args)
    try:
        from specsmith.governance_logic import run_preflight

        result = run_preflight(intent, project_dir=root)
        return dict(result)
    except Exception as exc:  # noqa: BLE001
        # Fallback: subprocess the CLI so preflight always works even if import path differs
        import subprocess

        try:
            proc = subprocess.run(
                [sys.executable, "-m", "specsmith", "preflight", intent, "--json"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(root),
            )
            parsed: dict[str, Any] = json.loads(proc.stdout)
            return parsed
        except Exception as exc2:  # noqa: BLE001
            return {
                "decision": "needs_clarification",
                "instruction": f"preflight unavailable: {exc}; fallback failed: {exc2}",
                "work_item_id": "",
            }


def _handle_governance_context_transition(args: dict[str, Any]) -> dict[str, Any]:
    from specsmith.context_control import (
        ContextAction,
        ContextRecord,
        ContextTelemetry,
        SemanticCheckpoint,
        TaskEnvelope,
        ZooContextController,
        cleanup_context,
        decide_context_action,
    )

    telemetry = ContextTelemetry(**dict(args.get("telemetry") or {}))
    task = TaskEnvelope(**dict(args.get("task") or {}))
    decision = decide_context_action(telemetry, task)
    packet = None
    health = None
    if decision.action is not ContextAction.CONTINUE and args.get("invariants"):
        checkpoint = SemanticCheckpoint.create(
            str(args.get("work_item_id") or "unscoped"), dict(args["invariants"])
        )
        records = [ContextRecord(**record) for record in args.get("records") or []]
        packet, health = cleanup_context(
            checkpoint,
            records,
            token_budget=max(0, telemetry.remaining_work_capacity),
        )
    directive = ZooContextController().directive(
        decision,
        governed=bool(args.get("governed", True)),
        packet=packet,
        health=health,
    )
    return {
        "decision": decision.to_dict(),
        "directive": {
            "action": directive.action,
            "packet_digest": directive.packet_digest,
            "resume_allowed": directive.resume_allowed,
            "native_summary_allowed": directive.native_summary_allowed,
            "degraded": directive.degraded,
            "reason": directive.reason,
        },
        "packet": (
            {
                "checkpoint_id": packet.checkpoint_id,
                "work_item_id": packet.work_item_id,
                "invariants": packet.invariants,
                "records": packet.records,
                "digest": packet.digest,
            }
            if packet
            else None
        ),
    }


def _handle_governance_context_verify(args: dict[str, Any]) -> dict[str, Any]:
    expected = str(args.get("expected_digest") or "")
    applied = str(args.get("applied_digest") or "")
    verified = bool(expected and expected == applied)
    return {
        "verified": verified,
        "resume_allowed": verified,
        "status": "healthy" if verified else "blocked_degraded",
    }


def _handle_governance_phase(args: dict[str, Any]) -> dict[str, Any]:
    """Return the current AEE phase and readiness info."""
    root = _resolve_root(args)
    try:
        from specsmith.phase import PHASE_MAP, phase_progress_pct, read_phase

        phase_key = read_phase(root)
        phase = PHASE_MAP.get(phase_key)
        if not phase:
            return {"phase": phase_key, "label": "Unknown", "pct": 0, "failing_checks": []}

        pct = phase_progress_pct(phase, root)
        # Get failing checks via evaluate_phase
        failing: list[str] = []
        try:
            from specsmith.phase import evaluate_phase

            _, failing = evaluate_phase(phase, root)
        except Exception:  # noqa: BLE001
            pass

        return {
            "phase": phase_key,
            "label": f"{phase.emoji} {phase.label}",
            "pct": pct,
            "description": phase.description,
            "failing_checks": failing,
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "phase": "unknown", "pct": 0, "failing_checks": []}


def _handle_governance_req_list(args: dict[str, Any]) -> dict[str, Any]:
    """List requirements from the project.

    In YAML-mode the requirements are read directly from ``docs/requirements/*.yml``
    so that callers always see the current YAML source without needing a prior
    ``specsmith sync`` (fixes GH #201 — stale JSON cache false positive).
    In legacy Markdown mode the JSON machine-state cache is used as before.
    """
    root = _resolve_root(args)
    status_filter = str(args.get("status_filter", "")).strip().lower() or None

    try:
        from specsmith.governance_yaml import (
            is_yaml_mode,
            load_yaml_requirements,
            load_yaml_tests,
        )

        if is_yaml_mode(root):
            # ── YAML-mode: read canonical source directly (REQ-364) ──────────
            yaml_reqs = load_yaml_requirements(root)
            yaml_tests = load_yaml_tests(root)

            covered: set[str] = {
                str(t.get("requirement_id", "")) for t in yaml_tests if t.get("requirement_id")
            }

            reqs: list[dict[str, Any]] = []
            for r in yaml_reqs:
                rid = str(r.get("id", ""))
                status = str(r.get("status", "")).lower()
                if status_filter and status != status_filter:
                    continue
                reqs.append(
                    {
                        "id": rid,
                        "title": str(r.get("title", r.get("description", ""))),
                        "status": status,
                        "covered": rid in covered,
                    },
                )
        else:
            # ── Legacy Markdown mode: use JSON cache ──────────────────────────
            req_path = root / ".specsmith" / "requirements.json"
            test_path = root / ".specsmith" / "testcases.json"

            if not req_path.exists():
                return {
                    "error": (
                        "requirements.json not found — run `specsmith sync` to "
                        "generate the JSON cache from your governance sources"
                    ),
                    "reqs": [],
                }

            reqs_raw: list[dict[str, Any]] = json.loads(req_path.read_text(encoding="utf-8"))

            covered_json: set[str] = set()
            if test_path.exists():
                tests_raw: list[dict[str, Any]] = json.loads(test_path.read_text(encoding="utf-8"))
                for t in tests_raw:
                    covers = t.get("covers", t.get("req_id", t.get("requirement_id", "")))
                    if covers:
                        covered_json.add(str(covers))

            reqs = []
            covered = covered_json
            for r in reqs_raw:
                rid = str(r.get("id", ""))
                status = str(r.get("status", "")).lower()
                if status_filter and status != status_filter:
                    continue
                reqs.append(
                    {
                        "id": rid,
                        "title": str(r.get("title", r.get("description", ""))),
                        "status": status,
                        "covered": rid in covered,
                    },
                )

        return {
            "total": len(reqs),
            "covered": sum(1 for r in reqs if r["covered"]),
            "reqs": reqs,
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "reqs": []}


def _handle_governance_trace_seal(args: dict[str, Any]) -> dict[str, Any]:
    """Create a cryptographic trace vault seal."""
    seal_type = str(args.get("seal_type", "milestone")).strip()
    description = str(args.get("description", "")).strip()
    author = str(args.get("author", "specsmith-mcp")).strip()
    root = _resolve_root(args)

    if not description:
        return {"error": "description is required", "sealed": False}

    try:
        from specsmith.trace import TraceVault

        vault = TraceVault(root)
        record = vault.seal(seal_type=seal_type, description=description, author=author)
        return {
            "sealed": True,
            "seal_id": record.seal_id,
            "seal_type": record.seal_type,
            "description": record.description,
            "timestamp": record.timestamp,
            "entry_hash": record.entry_hash,
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "sealed": False}


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

_HANDLERS = {
    "governance_project_list": _handle_governance_project_list,
    "governance_audit": _handle_governance_audit,
    "governance_checkpoint": _handle_governance_checkpoint,
    "governance_preflight": _handle_governance_preflight,
    "governance_phase": _handle_governance_phase,
    "governance_req_list": _handle_governance_req_list,
    "governance_trace_seal": _handle_governance_trace_seal,
    "governance_context_transition": _handle_governance_context_transition,
    "governance_context_verify": _handle_governance_context_verify,
}


# ---------------------------------------------------------------------------
# MCP JSON-RPC 2.0 server loop
# ---------------------------------------------------------------------------


def _send(payload: dict[str, Any]) -> None:
    """Write one JSON-RPC message to stdout."""
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _error_response(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _ok_response(req_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _text_block(text: str) -> list[dict[str, str]]:
    return [{"type": "text", "text": text}]


def _handle_request(msg: dict[str, Any]) -> dict[str, Any] | None:
    """Process one JSON-RPC request and return a response dict (or None for notifications)."""
    method = str(msg.get("method", ""))
    req_id = msg.get("id")
    params = msg.get("params") or {}

    # Notifications have no id — send no response
    if req_id is None and method.startswith("notifications/"):
        return None

    if method == "initialize":
        return _ok_response(
            req_id,
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )

    if method == "tools/list":
        return _ok_response(req_id, {"tools": _TOOLS})

    if method == "tools/call":
        tool_name = str(params.get("name", ""))
        tool_args: dict[str, Any] = params.get("arguments") or {}

        handler = _HANDLERS.get(tool_name)
        if handler is None:
            return _ok_response(
                req_id,
                {
                    "isError": True,
                    "content": _text_block(f"Unknown tool: {tool_name}"),
                },
            )
        try:
            result = handler(tool_args)
            content_text = json.dumps(result, indent=2, ensure_ascii=False)
            return _ok_response(
                req_id,
                {"isError": False, "content": _text_block(content_text)},
            )
        except Exception as exc:  # noqa: BLE001
            return _ok_response(
                req_id,
                {"isError": True, "content": _text_block(f"Tool error: {exc}")},
            )

    if method == "ping":
        return _ok_response(req_id, {})

    if req_id is not None:
        return _error_response(req_id, -32601, f"Method not found: {method}")
    return None


def run_server(
    project_dir: str | None = None,
    extra_project_dirs: list[str] | None = None,
) -> None:
    """Start the MCP stdio server. Blocks until stdin closes.

    Reads newline-delimited JSON-RPC 2.0 messages from stdin and
    writes responses to stdout. Stderr is used for diagnostic messages.

    Project discovery order (highest priority first):

    1. ``project_dir`` — if provided, becomes the *default* project (first
       slot).  Any tool call that omits ``project_dir`` will target this.
    2. **Registry** — all paths in ``~/.specsmith/mcp-projects.json`` are
       merged in.  Run ``specsmith mcp register`` in a project once to add it.
    3. ``extra_project_dirs`` — additional paths appended after the registry.
    4. **Fallback** — if nothing resolves, the current working directory is
       used (useful for development/testing).

    All paths are resolved to absolute form; duplicates are silently dropped.
    The server never calls ``os.chdir()``.
    """
    global _DEFAULT_PROJECT_DIR, _REGISTERED_PROJECTS

    all_dirs: list[str] = []
    seen: set[str] = set()

    def _add(p: str) -> None:
        abs_p = str(Path(p).resolve())
        if abs_p not in seen:
            seen.add(abs_p)
            all_dirs.append(abs_p)

    # 1. Explicit primary project (becomes the default)
    if project_dir is not None:
        _add(project_dir)

    # 2. Persistent registry
    for p in read_registry():
        _add(p)

    # 3. Additional explicit dirs
    for p in extra_project_dirs or []:
        _add(p)

    # 4. CWD fallback when nothing is registered
    if not all_dirs:
        _add(".")

    _DEFAULT_PROJECT_DIR = all_dirs[0]
    _REGISTERED_PROJECTS = all_dirs

    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            msg = json.loads(raw_line)
        except ValueError as exc:
            _send(_error_response(None, -32700, f"Parse error: {exc}"))
            continue

        if not isinstance(msg, dict):
            _send(_error_response(None, -32600, "Invalid request"))
            continue

        try:
            response = _handle_request(msg)
        except Exception as exc:  # noqa: BLE001
            _send(_error_response(msg.get("id"), -32603, f"Internal error: {exc}"))
            continue

        if response is not None:
            _send(response)


__all__ = [
    "SERVER_NAME",
    "SERVER_VERSION",
    "_HANDLERS",
    "_TOOLS",
    "read_registry",
    "register_project",
    "run_server",
    "unregister_project",
    "write_registry",
]
