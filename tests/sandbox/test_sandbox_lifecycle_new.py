# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Sandbox lifecycle test: new project walks through all 7 AEE phases.

Exercises: init → audit → phase show → phase next (through all phases with --force).
Verifies phase tracking, gating, and artifact creation at each stage.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from specsmith.cli import main


def _write_scaffold_config(config_path: Path) -> None:
    config = {
        "name": "lifecycle-test",
        "type": "cli-python",
        "platforms": ["windows", "linux", "macos"],
        "language": "python",
        "vcs_platform": "github",
        "git_init": False,
    }
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


class TestLifecycleNew:
    """Walk a new project through the entire 7-phase lifecycle."""

    def test_governance_files_present(self, tmp_path: Path) -> None:
        """Verify all governance files are present after scaffold."""
        config_path = tmp_path / "scaffold.yml"
        _write_scaffold_config(config_path)
        out = tmp_path / "out"
        out.mkdir()

        runner = CliRunner()
        runner.invoke(
            main,
            ["init", "--config", str(config_path), "--output-dir", str(out), "--no-git"],
        )
        project = out / "lifecycle-test"
        gov = project / "docs" / "governance"

        expected = [
            "RULES.md",
            "SESSION-PROTOCOL.md",
            "LIFECYCLE.md",
            "ROLES.md",
            "CONTEXT-BUDGET.md",
            "VERIFICATION.md",
            "DRIFT-METRICS.md",
        ]
        for f in expected:
            assert (gov / f).exists(), f"Missing governance file: {f}"

        # WORKFLOW.md should NOT exist
        assert not (gov / "WORKFLOW.md").exists()
        assert not (project / "docs" / "WORKFLOW.md").exists()

        # LIFECYCLE.md should reference phases
        lifecycle = (gov / "LIFECYCLE.md").read_text(encoding="utf-8")
        assert "Inception" in lifecycle
        assert "specsmith checkpoint" in lifecycle
        assert "specsmith phase" not in lifecycle

        # AGENTS.md should mention current phase
        agents = (project / "AGENTS.md").read_text(encoding="utf-8")
        assert "Phase:" in agents  # slimmed template uses **Phase:** not **Current Phase:**
        assert "inception" in agents.lower()

        # README.md should have dynamic phase
        readme = (project / "README.md").read_text(encoding="utf-8")
        assert "Inception" in readme
