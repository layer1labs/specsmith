# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Session initialization -- detect project, load governance, offer onboarding (REQ-225).

When Kairos opens or ``specsmith run`` starts, this module provides the
intelligence to:
  1. Detect if the current directory is a specsmith-governed project
  2. If not: offer to import/scaffold it
  3. If yes but outdated: offer to migrate
  4. Load the full governance context for the session

The ``SessionContext`` returned by ``init_session()`` is the single
object that the runner, serve, and Kairos all consume to understand
the current project state.

Context lifecycle (Issue #335):
  - init_session() now runs initialization hooks (directory setup, isolation check, context warm)
  - shutdown_session() persists state, clears locks, cleans temp artifacts
  - clear_session_context() provides aggressive cleanup for fresh starts
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)


@dataclass
class SessionContext:
    """Complete governance context for a session.

    Includes context lifecycle fields for:
      - Continuity: tracking previous session state
      - Isolation: detecting stale/leaked session data
      - Cleanup: managing session resources
    """

    project_dir: str = ""
    project_name: str = ""
    is_governed: bool = False
    needs_import: bool = False
    needs_migration: bool = False
    spec_version: str = ""
    installed_version: str = ""
    governance_version: str = ""

    # Governance state
    phase: str = "inception"
    phase_label: str = "Inception"
    phase_emoji: str = "\U0001f331"
    phase_readiness_pct: int = 0
    health_score: int = 0  # 0-100
    health_issues: list[str] = field(default_factory=list)

    # Requirements & compliance
    total_requirements: int = 0
    covered_requirements: int = 0
    total_tests: int = 0
    compliance_score: int = 0  # 0-100

    # Provider state
    active_profile: str = "unrestricted"
    provider_count: int = 0
    reachable_providers: int = 0

    # Session metadata
    session_id: str = ""
    started_at: str = ""

    # Context lifecycle fields (internal)
    _prev_session_id: str = ""  # Previous session ID for continuity
    _prev_phase: str = ""  # Previous phase for transition tracking
    _history_turns: int = 0  # Number of history turns loaded

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_dir": self.project_dir,
            "project_name": self.project_name,
            "is_governed": self.is_governed,
            "needs_import": self.needs_import,
            "needs_migration": self.needs_migration,
            "spec_version": self.spec_version,
            "installed_version": self.installed_version,
            "governance_version": self.governance_version,
            "phase": self.phase,
            "phase_label": self.phase_label,
            "phase_emoji": self.phase_emoji,
            "phase_readiness_pct": self.phase_readiness_pct,
            "health_score": self.health_score,
            "health_issues": self.health_issues,
            "total_requirements": self.total_requirements,
            "covered_requirements": self.covered_requirements,
            "total_tests": self.total_tests,
            "compliance_score": self.compliance_score,
            "active_profile": self.active_profile,
            "provider_count": self.provider_count,
            "reachable_providers": self.reachable_providers,
            "session_id": self.session_id,
            "started_at": self.started_at,
            # Context lifecycle metadata
            "_prev_session_id": self._prev_session_id,
            "_prev_phase": self._prev_phase,
            "_history_turns": self._history_turns,
        }


def _find_scaffold(root: Path) -> Path | None:
    """Find the scaffold config file in a project directory."""
    candidates = [
        root / "docs" / "SPECSMITH.yml",
        root / "docs" / "specsmith.yml",
        root / "scaffold.yml",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def _is_yaml_first_mode(root: Path) -> bool:
    """Return True when the project is in YAML-first governance mode (REQ-380)."""
    marker = root / ".specsmith" / "governance-mode"
    if marker.is_file():
        return marker.read_text(encoding="utf-8").strip() == "yaml"
    return False


def _count_requirements(root: Path) -> tuple[int, int]:
    """Count total requirements and covered (with tests) requirements."""
    if _is_yaml_first_mode(root):
        import contextlib
        import json

        req_json = root / ".specsmith" / "requirements.json"
        test_json = root / ".specsmith" / "testcases.json"
        if not req_json.is_file():
            return 0, 0
        with contextlib.suppress(Exception):
            reqs = json.loads(req_json.read_text(encoding="utf-8"))
            req_ids = {r["id"] for r in reqs if "id" in r}
            covered: set[str] = set()
            if test_json.is_file():
                tests = json.loads(test_json.read_text(encoding="utf-8"))
                linked_req_ids = {t.get("requirement_id", "") for t in tests}
                covered = req_ids & linked_req_ids
            return len(req_ids), len(covered)
        return 0, 0

    req_path = root / "docs" / "REQUIREMENTS.md"
    if not req_path.is_file():
        req_path = root / "REQUIREMENTS.md"
    if not req_path.is_file():
        return 0, 0

    import re

    text = req_path.read_text(encoding="utf-8", errors="replace")
    req_ids = set(re.findall(r"REQ-\d+", text))

    test_path = root / "docs" / "TESTS.md"
    if not test_path.is_file():
        test_path = root / "TESTS.md"
    covered_md: set[str] = set()
    if test_path.is_file():
        test_text = test_path.read_text(encoding="utf-8", errors="replace")
        for req_id in req_ids:
            if req_id in test_text:
                covered_md.add(req_id)

    return len(req_ids), len(covered_md)


def _count_tests(root: Path) -> int:
    """Count total test specifications."""
    if _is_yaml_first_mode(root):
        import contextlib
        import json

        test_json = root / ".specsmith" / "testcases.json"
        if not test_json.is_file():
            return 0
        with contextlib.suppress(Exception):
            tests = json.loads(test_json.read_text(encoding="utf-8"))
            return len(tests)
        return 0

    import re

    test_path = root / "docs" / "TESTS.md"
    if not test_path.is_file():
        test_path = root / "TESTS.md"
    if not test_path.is_file():
        return 0
    text = test_path.read_text(encoding="utf-8", errors="replace")
    return len(set(re.findall(r"TEST-\d+", text)))


def _get_health_score(root: Path) -> tuple[int, list[str]]:
    """Quick governance health check (0-100 score + issues)."""
    issues: list[str] = []
    checks_passed = 0
    total_checks = 6

    if _find_scaffold(root):
        checks_passed += 1
    else:
        issues.append("No scaffold.yml or docs/SPECSMITH.yml found")

    if (root / "AGENTS.md").is_file():
        checks_passed += 1
    else:
        issues.append("AGENTS.md missing")

    ledger = root / "docs" / "LEDGER.md"
    if not ledger.is_file():
        ledger = root / "LEDGER.md"
    if ledger.is_file():
        checks_passed += 1
    else:
        issues.append("LEDGER.md missing")

    req_path = root / "docs" / "REQUIREMENTS.md"
    if not req_path.is_file():
        req_path = root / "REQUIREMENTS.md"
    if req_path.is_file():
        checks_passed += 1
    else:
        issues.append("REQUIREMENTS.md missing")

    test_path = root / "docs" / "TESTS.md"
    if not test_path.is_file():
        test_path = root / "TESTS.md"
    if test_path.is_file():
        checks_passed += 1
    else:
        issues.append("TESTS.md missing")

    if (root / ".specsmith").is_dir():
        checks_passed += 1
    else:
        issues.append(".specsmith/ directory missing")

    return int(checks_passed / total_checks * 100), issues


def init_session(project_dir: str | Path = ".", *, force_new: bool = False) -> SessionContext:
    """Initialize a session context for the given project directory.

    This is the primary entry point consumed by ``specsmith run``,
    ``specsmith serve``, and the Kairos governance client.

    Args:
        project_dir: Path to the project root.
        force_new: If True, skip loading previous session state and start fresh.

    Returns:
        A fully-initialized SessionContext with hooks for initialization,
        cleanup, and isolation verification.
    """
    import uuid

    root = Path(project_dir).resolve()

    ctx = SessionContext(
        project_dir=str(root),
        project_name=root.name,
        session_id=f"SS-{uuid.uuid4().hex[:8].upper()}",
        started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )

    # Installed version (package version)
    try:
        from specsmith import __version__
        ctx.installed_version = __version__
    except Exception:  # noqa: BLE001
        ctx.installed_version = "unknown"

    # Governance version (schema version for project config)
    try:
        from specsmith import GOVERNANCE_VERSION
        ctx.governance_version = GOVERNANCE_VERSION
    except Exception:  # noqa: BLE001
        ctx.governance_version = "unknown"

    # Check if project is governed
    scaffold = _find_scaffold(root)
    if scaffold is None:
        ctx.is_governed = False
        ctx.needs_import = True
        _ensure_session_dirs(root)
        isolation_issues = _check_session_isolation(root, ctx.session_id)
        if isolation_issues:
            ctx.health_issues.extend(isolation_issues)
        return ctx

    ctx.is_governed = True

    # Load scaffold config
    try:
        import yaml
        raw = yaml.safe_load(scaffold.read_text(encoding="utf-8")) or {}
        ctx.spec_version = str(raw.get("spec_version", ""))
        if ctx.spec_version and ctx.governance_version and ctx.spec_version != ctx.governance_version:
            ctx.needs_migration = True
    except Exception:  # noqa: BLE001
        pass

    # Phase
    try:
        from specsmith.phase import PHASE_MAP, phase_progress_pct, read_phase
        phase_key = read_phase(root)
        phase = PHASE_MAP.get(phase_key)
        if phase:
            ctx.phase = phase_key
            ctx.phase_label = phase.label
            ctx.phase_emoji = phase.emoji
            ctx.phase_readiness_pct = phase_progress_pct(phase, root)
    except Exception:  # noqa: BLE001
        pass

    # Health
    ctx.health_score, ctx.health_issues = _get_health_score(root)

    # Requirements & compliance
    total_reqs, covered_reqs = _count_requirements(root)
    ctx.total_requirements = total_reqs
    ctx.covered_requirements = covered_reqs
    ctx.total_tests = _count_tests(root)
    ctx.compliance_score = int(covered_reqs / total_reqs * 100) if total_reqs > 0 else 0

    # Provider state
    try:
        from specsmith.agent.provider_registry import ProviderRegistry
        reg = ProviderRegistry.load()
        ctx.provider_count = len(reg.providers)
        ctx.reachable_providers = len([p for p in reg.providers if p.status == "reachable"])
    except Exception:  # noqa: BLE001
        pass

    # Active profile
    try:
        from specsmith.agent.execution_profiles import ExecutionProfileStore
        store = ExecutionProfileStore.load()
        ctx.active_profile = store.default().id
    except Exception:  # noqa: BLE001
        pass

    # -- Context initialization hooks (Issue #335) ---------------------------

    # Hook 1: Ensure session directory structure exists (isolation)
    _ensure_session_dirs(root)

    # Hook 2: Validate session isolation -- detect stale/leaked state
    isolation_issues = _check_session_isolation(root, ctx.session_id)
    if isolation_issues:
        ctx.health_issues.extend(isolation_issues)
        ctx.health_score = max(0, ctx.health_score - len(isolation_issues) * 5)

    # Hook 3: Load previous session state for continuity (unless force_new)
    if not force_new:
        _warm_context_cache(root, ctx)

    return ctx


# ---------------------------------------------------------------------------
# Context lifecycle helpers (Issue #335)
# ---------------------------------------------------------------------------


def _ensure_session_dirs(root: Path) -> None:
    """Ensure session isolation directories exist."""
    sessions_dir = root / ".specsmith" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)


def _check_session_isolation(root: Path, current_session_id: str) -> list[str]:
    """Check for stale or leaked session state.

    Returns a list of isolation issues found. Each issue is a human-readable
    string that will be added to SessionContext.health_issues.
    """
    issues: list[str] = []
    specsmith_dir = root / ".specsmith"

    # Check for stale session-state.json
    state_path = specsmith_dir / "session-state.json"
    if state_path.is_file():
        try:
            import json
            existing = json.loads(state_path.read_text(encoding="utf-8"))
            existing_id = existing.get("session_id", "")
            if existing_id and existing_id != current_session_id:
                issues.append(
                    f"Stale session state detected (previous: {existing_id}, "
                    f"current: {current_session_id}) -- new session started"
                )
        except Exception:  # noqa: BLE001
            pass

    # Check for orphaned session directories with lock files
    sessions_dir = specsmith_dir / "sessions"
    if sessions_dir.is_dir():
        for sd in sessions_dir.iterdir():
            if sd.is_dir():
                lock_file = sd / ".lock"
                if lock_file.is_file():
                    issues.append(
                        f"Crashed session detected: {sd.name} (lock file present)"
                    )

    return issues


def _warm_context_cache(root: Path, ctx: SessionContext) -> None:
    """Warm the context cache by loading previous session state."""
    try:
        from specsmith.session_store import load_session
        prev_ctx, history = load_session(root)
        if prev_ctx:
            ctx._prev_session_id = prev_ctx.get("session_id", "")
            ctx._prev_phase = prev_ctx.get("phase", "")
            ctx._history_turns = len(history)
            _log.info(
                "Context warmed: prev_session=%s, history_turns=%d",
                ctx._prev_session_id,
                ctx._history_turns,
            )
        else:
            _log.info("Context warmed: no previous session state found")
    except Exception:  # noqa: BLE001
        _log.debug("Context warm failed (best-effort): %s", exc_info=True)
        ctx._prev_session_id = ""
        ctx._prev_phase = ""
        ctx._history_turns = 0


def shutdown_session(root: Path, ctx: SessionContext | None = None) -> dict[str, Any]:
    """Run context cleanup/shutdown hooks for the current session.

    This function performs:
      1. Persist final session state
      2. Clean up lock files and temporary artifacts
      3. Close any open session resources
      4. Write a session-end event to the canonical event log

    Args:
        root: Project root path.
        ctx: Optional SessionContext to persist. If None, loads from disk.

    Returns:
        A summary dict with cleanup results.
    """
    result = {
        "session_id": ctx.session_id if ctx else "",
        "persisted": False,
        "locks_cleared": 0,
        "artifacts_cleaned": 0,
        "errors": [],
    }

    try:
        from specsmith.session_store import save_session

        if ctx is not None:
            ctx_dict = ctx.to_dict()
            history: list[dict[str, Any]] = []
            try:
                from specsmith.session_store import load_session
                _, history = load_session(root)
            except Exception:  # noqa: BLE001
                pass
            save_session(root, ctx_dict, history)
            result["persisted"] = True
    except Exception as exc:  # noqa: BLE001
        result["errors"].append(f"persist: {exc}")

    # Clean up lock files
    sessions_dir = root / ".specsmith" / "sessions"
    if sessions_dir.is_dir():
        for sd in sessions_dir.iterdir():
            if sd.is_dir():
                lock_file = sd / ".lock"
                if lock_file.is_file():
                    try:
                        lock_file.unlink()
                        result["locks_cleared"] += 1
                    except Exception as exc:  # noqa: BLE001
                        result["errors"].append(f"lock cleanup: {sd.name}: {exc}")

    # Clean up temp files (*.tmp)
    specsmith_dir = root / ".specsmith"
    if specsmith_dir.is_dir():
        for tmp in specsmith_dir.rglob("*.tmp"):
            try:
                tmp.unlink()
                result["artifacts_cleaned"] += 1
            except Exception as exc:  # noqa: BLE001
                result["errors"].append(f"temp cleanup: {tmp.name}: {exc}")

    return result


def clear_session_context(root: Path) -> dict[str, Any]:
    """Clear all session context state for a fresh start.

    This is the most aggressive cleanup -- it removes:
      - session-state.json
      - conversation-history.jsonl
      - All session directories under .specsmith/sessions/
      - Lock files and temp artifacts
    """
    result: dict[str, Any] = {
        "files_removed": [],
        "dirs_removed": [],
        "errors": [],
    }

    specsmith_dir = root / ".specsmith"

    # Remove session-state.json
    state_path = specsmith_dir / "session-state.json"
    if state_path.is_file():
        try:
            state_path.unlink()
            result["files_removed"].append("session-state.json")
        except Exception as exc:  # noqa: BLE001
            result["errors"].append(f"remove session-state.json: {exc}")

    # Remove conversation-history.jsonl
    hist_path = specsmith_dir / "conversation-history.jsonl"
    if hist_path.is_file():
        try:
            hist_path.unlink()
            result["files_removed"].append("conversation-history.jsonl")
        except Exception as exc:  # noqa: BLE001
            result["errors"].append(f"remove conversation-history.jsonl: {exc}")

    # Remove all session directories
    sessions_dir = specsmith_dir / "sessions"
    if sessions_dir.is_dir():
        for sd in sessions_dir.iterdir():
            if sd.is_dir():
                try:
                    import shutil
                    shutil.rmtree(sd)
                    result["dirs_removed"].append(sd.name)
                except Exception as exc:  # noqa: BLE001
                    result["errors"].append(f"remove session dir {sd.name}: {exc}")

    return result


__all__ = [
    "SessionContext",
    "init_session",
    "shutdown_session",
    "clear_session_context",
]