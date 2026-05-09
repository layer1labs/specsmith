# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Session initialization — detect project, load governance, offer onboarding (REQ-225).

When Kairos opens or ``specsmith run`` starts, this module provides the
intelligence to:
  1. Detect if the current directory is a specsmith-governed project
  2. If not: offer to import/scaffold it
  3. If yes but outdated: offer to migrate
  4. Load the full governance context for the session

The ``SessionContext`` returned by ``init_session()`` is the single
object that the runner, serve, and Kairos all consume to understand
the current project state.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)


@dataclass
class SessionContext:
    """Complete governance context for a session."""

    project_dir: str = ""
    project_name: str = ""
    is_governed: bool = False
    needs_import: bool = False
    needs_migration: bool = False
    spec_version: str = ""
    installed_version: str = ""

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_dir": self.project_dir,
            "project_name": self.project_name,
            "is_governed": self.is_governed,
            "needs_import": self.needs_import,
            "needs_migration": self.needs_migration,
            "spec_version": self.spec_version,
            "installed_version": self.installed_version,
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


def _count_requirements(root: Path) -> tuple[int, int]:
    """Count total requirements and covered (with tests) requirements."""
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
    covered = set()
    if test_path.is_file():
        test_text = test_path.read_text(encoding="utf-8", errors="replace")
        # A requirement is "covered" if its ID appears in TESTS.md
        for req_id in req_ids:
            if req_id in test_text:
                covered.add(req_id)

    return len(req_ids), len(covered)


def _count_tests(root: Path) -> int:
    """Count total test specifications."""
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

    # Check key files exist
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


def init_session(project_dir: str | Path = ".") -> SessionContext:
    """Initialize a session context for the given project directory.

    This is the primary entry point consumed by ``specsmith run``,
    ``specsmith serve``, and the Kairos governance client.
    """
    import uuid

    root = Path(project_dir).resolve()

    ctx = SessionContext(
        project_dir=str(root),
        project_name=root.name,
        session_id=f"SS-{uuid.uuid4().hex[:8].upper()}",
        started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )

    # Installed version
    try:
        from specsmith import __version__

        ctx.installed_version = __version__
    except Exception:  # noqa: BLE001
        ctx.installed_version = "unknown"

    # Check if project is governed
    scaffold = _find_scaffold(root)
    if scaffold is None:
        ctx.is_governed = False
        ctx.needs_import = True
        return ctx

    ctx.is_governed = True

    # Load scaffold config
    try:
        import yaml

        raw = yaml.safe_load(scaffold.read_text(encoding="utf-8")) or {}
        ctx.spec_version = str(raw.get("spec_version", ""))
        if ctx.spec_version and ctx.installed_version and ctx.spec_version != ctx.installed_version:
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

    return ctx
