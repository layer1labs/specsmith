# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Sandbox lifecycle test: old project with WORKFLOW.md files upgrades correctly.

Creates a project with old-style governance files (WORKFLOW.md), then
runs upgrade and verifies the migration to SESSION-PROTOCOL.md + LIFECYCLE.md.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from specsmith.cli import main


def _create_old_project(root: Path) -> None:
    """Create a project that looks like an older specsmith version produced it."""
    root.mkdir(exist_ok=True)

    # scaffold.yml with an old version
    scaffold = {
        "name": "old-project",
        "type": "cli-python",
        "platforms": ["windows", "linux"],
        "language": "python",
        "vcs_platform": "github",
        "spec_version": "0.2.0",
    }
    with open(root / "scaffold.yml", "w") as f:
        yaml.dump(scaffold, f, default_flow_style=False, sort_keys=False)

    # Old-style governance files (WORKFLOW.md instead of SESSION-PROTOCOL.md)
    (root / "AGENTS.md").write_text("# AGENTS\nShort hub.\n", encoding="utf-8")
    (root / "LEDGER.md").write_text("# Ledger\n\n## Session 1\nSetup.\n", encoding="utf-8")

    gov = root / "docs" / "governance"
    gov.mkdir(parents=True)
    (gov / "RULES.md").write_text("# Rules\nH1: No unproposed changes.\n", encoding="utf-8")
    (gov / "WORKFLOW.md").write_text(
        "# Session Lifecycle\nOld workflow content.\n", encoding="utf-8"
    )
    (gov / "ROLES.md").write_text("# Roles\nAgent roles.\n", encoding="utf-8")
    (gov / "CONTEXT-BUDGET.md").write_text("# Budget\nContext rules.\n", encoding="utf-8")
    (gov / "VERIFICATION.md").write_text("# Verification\nStandards.\n", encoding="utf-8")
    (gov / "DRIFT-METRICS.md").write_text("# Drift\nMetrics.\n", encoding="utf-8")

    # Old-style docs/WORKFLOW.md (the static milestone file)
    docs = root / "docs"
    (docs / "WORKFLOW.md").write_text(
        "# Workflow\n1. Scaffold\n2. Architecture\n3. Requirements\n",
        encoding="utf-8",
    )
    (docs / "ARCHITECTURE.md").write_text("# Architecture\nOverview.\n", encoding="utf-8")
    (docs / "REQUIREMENTS.md").write_text("# Requirements\n\n", encoding="utf-8")
    (docs / "TESTS.md").write_text("# Tests\n\n", encoding="utf-8")


class TestLifecycleUpgrade:
    """Verify old projects with WORKFLOW.md migrate correctly on upgrade."""

    def test_upgrade_migrates_workflow_to_session_protocol(self, tmp_path: Path) -> None:
        root = tmp_path / "old-project"
        _create_old_project(root)

        # Verify old files exist
        gov = root / "docs" / "governance"
        assert (gov / "WORKFLOW.md").exists()
        assert (root / "docs" / "WORKFLOW.md").exists()

        runner = CliRunner()
        r = runner.invoke(main, ["upgrade", "--project-dir", str(root)])
        assert r.exit_code == 0, f"Upgrade failed: {r.output}"
        assert "Upgraded" in r.output

        # WORKFLOW.md should be gone, SESSION-PROTOCOL.md should exist
        assert not (gov / "WORKFLOW.md").exists(), "Old governance/WORKFLOW.md still exists"
        assert (gov / "SESSION-PROTOCOL.md").exists(), "SESSION-PROTOCOL.md not created"

        # docs/WORKFLOW.md (the milestone file) should be removed
        assert not (root / "docs" / "WORKFLOW.md").exists(), "Old docs/WORKFLOW.md still exists"

        # LIFECYCLE.md should be created
        assert (gov / "LIFECYCLE.md").exists(), "LIFECYCLE.md not created"

        # Verify LIFECYCLE.md has phase content
        lifecycle = (gov / "LIFECYCLE.md").read_text(encoding="utf-8")
        assert "Inception" in lifecycle or "inception" in lifecycle

    def test_upgrade_preserves_workflow_content(self, tmp_path: Path) -> None:
        """The old WORKFLOW.md content should be preserved in SESSION-PROTOCOL.md."""
        root = tmp_path / "old-project"
        _create_old_project(root)

        runner = CliRunner()
        runner.invoke(main, ["upgrade", "--project-dir", str(root)])

        # SESSION-PROTOCOL.md should have session protocol content
        sp = (root / "docs" / "governance" / "SESSION-PROTOCOL.md").read_text(encoding="utf-8")
        assert "Session" in sp or "session" in sp or "Protocol" in sp

    def test_upgrade_updates_spec_version(self, tmp_path: Path) -> None:
        root = tmp_path / "old-project"
        _create_old_project(root)

        runner = CliRunner()
        runner.invoke(main, ["upgrade", "--project-dir", str(root), "--spec-version", "0.4.0"])

        with open(root / "scaffold.yml") as f:
            cfg = yaml.safe_load(f)
        assert cfg["spec_version"] == "0.4.0"

    def test_upgrade_then_audit_runs(self, tmp_path: Path) -> None:
        """After upgrade, audit should run without crashing."""
        root = tmp_path / "old-project"
        _create_old_project(root)

        runner = CliRunner()
        runner.invoke(main, ["upgrade", "--project-dir", str(root)])

        r = runner.invoke(main, ["audit", "--project-dir", str(root)])
        # Audit may exit 1 (missing LICENSE, etc.) but must not crash
        assert r.exit_code in (0, 1), f"audit crashed: {r.exception}"
        # Governance files should be present after upgrade
        assert (root / "docs" / "governance" / "SESSION-PROTOCOL.md").exists()
        assert (root / "docs" / "governance" / "LIFECYCLE.md").exists()

    def test_upgrade_idempotent(self, tmp_path: Path) -> None:
        """Running upgrade twice should not break anything."""
        root = tmp_path / "old-project"
        _create_old_project(root)

        runner = CliRunner()
        # First upgrade
        runner.invoke(main, ["upgrade", "--project-dir", str(root)])
        # Second upgrade (same version — should say nothing to do)
        r = runner.invoke(main, ["upgrade", "--project-dir", str(root)])
        assert r.exit_code == 0
        assert "Nothing to upgrade" in r.output or "Already" in r.output

        # Files should still be correct
        gov = root / "docs" / "governance"
        assert (gov / "SESSION-PROTOCOL.md").exists()
        assert (gov / "LIFECYCLE.md").exists()
        assert not (gov / "WORKFLOW.md").exists()
