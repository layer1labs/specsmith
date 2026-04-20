# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Change reports — structured artifacts from improvement runs.

Every improvement run produces a ChangeReport stored as JSON at
``.specsmith/agent-reports/<task_id>.json``.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ChangeReport:
    """Structured output from an improvement run."""

    task_id: str = ""
    task_description: str = ""
    project_dir: str = "."
    status: str = "pending"  # pending, accepted, rejected, failed, unclear
    verdict: str = ""  # ACCEPT, REJECT, UNCLEAR
    plan: str = ""
    build_output: str = ""
    verify_output: str = ""
    files_changed: list[str] = field(default_factory=list)
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    summary: str = ""
    follow_up_tasks: list[str] = field(default_factory=list)
    created: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        """Convert to a JSON-serializable dict (excludes verbose fields)."""
        d = asdict(self)
        # Truncate verbose fields for the summary view
        for key in ("plan", "build_output", "verify_output"):
            if len(d.get(key, "")) > 500:
                d[key] = d[key][:500] + "...(truncated)"
        return d


def save_report(report: ChangeReport) -> Path:
    """Save a change report to ``.specsmith/agent-reports/``."""
    root = Path(report.project_dir).resolve()
    reports_dir = root / ".specsmith" / "agent-reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"{report.task_id}.json"
    path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def list_reports(project_dir: str = ".") -> list[ChangeReport]:
    """List all change reports, newest first."""
    reports_dir = Path(project_dir).resolve() / ".specsmith" / "agent-reports"
    if not reports_dir.exists():
        return []
    reports: list[ChangeReport] = []
    for path in sorted(reports_dir.glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            reports.append(ChangeReport(**{
                k: v for k, v in data.items()
                if k in ChangeReport.__dataclass_fields__
            }))
        except Exception:  # noqa: BLE001
            pass
    return reports
