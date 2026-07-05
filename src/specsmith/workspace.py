# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Workspace — multi-project governance management.

A workspace governs multiple specsmith projects with shared org-level defaults.
workspace.yml at the workspace root defines the project set.

Resolves GitHub issue #17.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class WorkspaceProject:
    """A project within a workspace."""

    path: str
    name: str = ""
    overrides: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkspaceConfig:
    """Workspace configuration parsed from workspace.yml."""

    name: str = ""
    description: str = ""
    projects: list[WorkspaceProject] = field(default_factory=list)
    defaults: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkspaceAuditResult:
    """Audit result for a single project in the workspace."""

    path: str
    name: str
    healthy: bool
    passed: int
    failed: int
    fixable: int
    issues: list[str] = field(default_factory=list)
    error: str = ""


_WORKSPACE_FILE = "workspace.yml"


def load_workspace(root: Path) -> WorkspaceConfig:
    """Load workspace.yml from the given directory."""
    ws_path = root / _WORKSPACE_FILE
    if not ws_path.exists():
        raise FileNotFoundError(f"No workspace.yml found at {root}")

    with open(ws_path) as f:
        raw = yaml.safe_load(f) or {}

    projects = []
    for p in raw.get("projects", []):
        if isinstance(p, str):
            projects.append(WorkspaceProject(path=p))
        elif isinstance(p, dict):
            projects.append(
                WorkspaceProject(
                    path=p.get("path", ""),
                    name=p.get("name", ""),
                    overrides=p.get("overrides", {}),
                ),
            )

    return WorkspaceConfig(
        name=raw.get("name", root.name),
        description=raw.get("description", ""),
        projects=projects,
        defaults=raw.get("defaults", {}),
    )


def init_workspace(root: Path, name: str, project_paths: list[str]) -> Path:
    """Create a workspace.yml at the given root."""
    ws_path = root / _WORKSPACE_FILE
    config = {
        "name": name,
        "description": f"Multi-project workspace for {name}",
        "projects": [{"path": p} for p in project_paths],
        "defaults": {
            "vcs_platform": "github",
            "branching_strategy": "gitflow",
            "required_approvals": 1,
        },
    }
    ws_path.write_text(
        yaml.dump(config, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    return ws_path


def audit_workspace(root: Path) -> list[WorkspaceAuditResult]:
    """Run audit on all projects in the workspace."""
    config = load_workspace(root)
    results = []

    for project in config.projects:
        proj_root = (root / project.path).resolve()
        name = project.name or proj_root.name

        if not proj_root.exists():
            results.append(
                WorkspaceAuditResult(
                    path=project.path,
                    name=name,
                    healthy=False,
                    passed=0,
                    failed=1,
                    fixable=0,
                    error=f"Directory not found: {proj_root}",
                ),
            )
            continue

        try:
            from specsmith.auditor import run_audit

            report = run_audit(proj_root)
            issues = [r.message for r in report.results if not r.passed]
            results.append(
                WorkspaceAuditResult(
                    path=project.path,
                    name=name,
                    healthy=report.healthy,
                    passed=report.passed,
                    failed=report.failed,
                    fixable=report.fixable,
                    issues=issues[:5],  # Show up to 5 issues
                ),
            )
        except Exception as e:  # noqa: BLE001
            results.append(
                WorkspaceAuditResult(
                    path=project.path,
                    name=name,
                    healthy=False,
                    passed=0,
                    failed=1,
                    fixable=0,
                    error=str(e),
                ),
            )

    return results


def export_workspace(root: Path) -> str:
    """Generate combined compliance report for all workspace projects."""
    config = load_workspace(root)
    audit_results = audit_workspace(root)

    lines = [
        f"# Workspace Compliance Report — {config.name}",
        "",
        f"**Projects**: {len(config.projects)}",
        f"**Healthy**: {sum(1 for r in audit_results if r.healthy)} / {len(audit_results)}",
        "",
    ]

    for result in audit_results:
        status = "✓" if result.healthy else "✗"
        lines.append(f"## {status} {result.name} (`{result.path}`)")
        if result.error:
            lines.append(f"\n_Error: {result.error}_\n")
            continue
        lines.append(
            f"\n- Passed: {result.passed} | Failed: {result.failed} | Fixable: {result.fixable}",
        )
        if result.issues:
            lines.append("\n**Issues:**")
            for issue in result.issues:
                lines.append(f"- {issue}")
        lines.append("")

        # Try to add per-project export
        proj_root = (root / result.path).resolve()
        try:
            from specsmith.exporter import run_export

            proj_report = run_export(proj_root)
            # Include first 500 chars of project export
            summary_lines = proj_report.splitlines()[:20]
            lines.extend(["<details><summary>Full report</summary>", ""])
            lines.extend(summary_lines)
            lines.extend(["", "</details>", ""])
        except Exception:  # noqa: BLE001
            pass

    return "\n".join(lines)
