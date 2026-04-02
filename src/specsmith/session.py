# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Session management — start/end checklists."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SessionCheck:
    """Single check in the session checklist."""

    name: str
    status: str  # "ok", "warn", "action"
    message: str


@dataclass
class SessionReport:
    """Session-end checklist report."""

    checks: list[SessionCheck] = field(default_factory=list)

    @property
    def action_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "action")

    @property
    def warn_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "warn")


def run_session_end(root: Path) -> SessionReport:
    """Run session-end checklist."""
    from specsmith.vcs_commands import (
        get_current_branch,
        has_uncommitted_changes,
        has_unpushed_commits,
    )

    report = SessionReport()

    # Uncommitted changes
    if has_uncommitted_changes(root):
        report.checks.append(
            SessionCheck(
                name="uncommitted",
                status="action",
                message="Uncommitted changes — run: specsmith commit",
            )
        )
    else:
        report.checks.append(
            SessionCheck(name="uncommitted", status="ok", message="Working tree clean")
        )

    # Unpushed commits
    if has_unpushed_commits(root):
        report.checks.append(
            SessionCheck(
                name="unpushed",
                status="action",
                message="Unpushed commits — run: specsmith push",
            )
        )
    else:
        report.checks.append(
            SessionCheck(name="unpushed", status="ok", message="All commits pushed")
        )

    # Branch check
    branch = get_current_branch(root)
    if branch in ("main", "master"):
        report.checks.append(
            SessionCheck(
                name="branch",
                status="warn",
                message=f"On {branch} — switch to a feature branch for next session",
            )
        )
    elif branch:
        report.checks.append(
            SessionCheck(name="branch", status="ok", message=f"On branch: {branch}")
        )

    # Ledger TODOs
    ledger_path = root / "LEDGER.md"
    if ledger_path.exists():
        content = ledger_path.read_text(encoding="utf-8")
        open_todos = sum(1 for line in content.splitlines() if "- [ ]" in line)
        if open_todos > 0:
            report.checks.append(
                SessionCheck(
                    name="todos",
                    status="warn",
                    message=f"{open_todos} open TODO(s) in ledger",
                )
            )
        else:
            report.checks.append(SessionCheck(name="todos", status="ok", message="No open TODOs"))

    # Audit status
    try:
        from specsmith.auditor import run_audit

        audit = run_audit(root)
        if audit.healthy:
            report.checks.append(
                SessionCheck(
                    name="audit",
                    status="ok",
                    message=f"Audit healthy ({audit.passed} checks passed)",
                )
            )
        else:
            report.checks.append(
                SessionCheck(
                    name="audit",
                    status="warn",
                    message=f"Audit: {audit.failed} issue(s) found",
                )
            )
    except Exception:  # noqa: BLE001
        report.checks.append(
            SessionCheck(name="audit", status="warn", message="Could not run audit")
        )

    # Credit spend summary for this session
    try:
        from specsmith.credits import get_summary

        cs = get_summary(root)
        if cs.entry_count > 0:
            report.checks.append(
                SessionCheck(
                    name="credits",
                    status="ok",
                    message=(
                        f"Credits: ${cs.total_cost_usd:.4f} total, "
                        f"{cs.session_count} session(s)"
                    ),
                )
            )
            for alert in cs.alerts:
                report.checks.append(
                    SessionCheck(name="credit-alert", status="warn", message=alert)
                )
    except Exception:  # noqa: BLE001
        pass  # Credits not configured — skip silently

    return report
