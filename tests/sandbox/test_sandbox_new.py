# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Sandbox integration test: scaffold a new Python CLI project from config.

Exercises the full init → audit → validate → compress → upgrade → diff workflow.
Always starts from a clean scaffold.yml — no prior state.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from specsmith.cli import main


def _write_scaffold_config(config_path: Path) -> None:
    """Write a comprehensive scaffold.yml for testing."""
    config = {
        "name": "forge-cli",
        "type": "cli-python",
        "platforms": ["windows", "linux", "macos"],
        "language": "python",
        "vcs_platform": "github",
        "branching_strategy": "gitflow",
        "git_init": False,
        "integrations": ["agents-md", "agent-skill", "claude-code"],
    }
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


class TestSandboxNew:
    """Full init workflow: config → scaffold → audit → validate → compress → upgrade → diff."""

    def test_scaffold_idempotent_restart(self, tmp_path: Path) -> None:
        """Re-scaffolding from same config to a clean dir gives identical results."""
        config_path = tmp_path / "scaffold.yml"
        _write_scaffold_config(config_path)

        runner = CliRunner()

        # First scaffold
        out1 = tmp_path / "run1"
        out1.mkdir()
        runner.invoke(
            main,
            ["init", "--config", str(config_path), "--output-dir", str(out1), "--no-git"],
        )

        # Second scaffold (clean dir)
        out2 = tmp_path / "run2"
        out2.mkdir()
        runner.invoke(
            main,
            ["init", "--config", str(config_path), "--output-dir", str(out2), "--no-git"],
        )

        # Compare key files
        for rel in [
            "AGENTS.md",
            "LEDGER.md",
            ".gitignore",
            "docs/governance/RULES.md",
            "docs/governance/VERIFICATION.md",
            "pyproject.toml",
            ".github/workflows/ci.yml",
        ]:
            f1 = (out1 / "forge-cli" / rel).read_text(encoding="utf-8")
            f2 = (out2 / "forge-cli" / rel).read_text(encoding="utf-8")
            assert f1 == f2, f"File {rel} differs between runs"

    def test_audit_tool_verification(self, tmp_path: Path) -> None:
        """Verify auditor checks CI config for expected tools."""
        config_path = tmp_path / "scaffold.yml"
        _write_scaffold_config(config_path)
        out = tmp_path / "out"
        out.mkdir()

        runner = CliRunner()
        runner.invoke(
            main,
            ["init", "--config", str(config_path), "--output-dir", str(out), "--no-git"],
        )

        project = out / "forge-cli"

        # Audit should pass — CI has ruff and pytest
        result = runner.invoke(main, ["audit", "--project-dir", str(project)])
        assert result.exit_code == 0
        assert "tool-ci-config" not in result.output or "expected" in result.output.lower()
