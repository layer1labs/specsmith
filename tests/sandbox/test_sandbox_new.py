# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
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
        "integrations": ["agents-md", "warp", "claude-code"],
    }
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


class TestSandboxNew:
    """Full init workflow: config → scaffold → audit → validate → compress → upgrade → diff."""

    def test_full_scaffold_workflow(self, tmp_path: Path) -> None:
        """End-to-end scaffold of a new Python CLI project from config."""
        config_path = tmp_path / "scaffold.yml"
        _write_scaffold_config(config_path)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        runner = CliRunner()

        # ---- Step 1: Init from config ----
        result = runner.invoke(
            main,
            [
                "init",
                "--config",
                str(config_path),
                "--output-dir",
                str(output_dir),
                "--no-git",
            ],
        )
        assert result.exit_code == 0, f"Init failed: {result.output}"
        assert "Done" in result.output

        project = output_dir / "forge-cli"
        assert project.exists()

        # ---- Step 2: Governance files ----
        assert (project / "AGENTS.md").exists()
        assert (project / "LEDGER.md").exists()
        assert (project / "README.md").exists()
        assert (project / ".gitignore").exists()
        assert (project / ".gitattributes").exists()

        # Modular governance
        gov = project / "docs" / "governance"
        for f in [
            "rules.md",
            "workflow.md",
            "roles.md",
            "context-budget.md",
            "verification.md",
            "drift-metrics.md",
        ]:
            assert (gov / f).exists(), f"Missing governance file: {f}"

        # Project docs
        assert (project / "docs" / "architecture.md").exists()
        assert (project / "docs" / "workflow.md").exists()
        assert (project / "docs" / "REQUIREMENTS.md").exists()
        assert (project / "docs" / "TEST_SPEC.md").exists()

        # ---- Step 3: Project structure ----
        assert (project / "pyproject.toml").exists()
        assert (project / "src" / "forge_cli" / "__init__.py").exists()
        assert (project / "src" / "forge_cli" / "cli.py").exists()
        assert (project / "tests" / ".gitkeep").exists()

        # Scripts
        assert (project / "scripts" / "setup.cmd").exists()
        assert (project / "scripts" / "setup.sh").exists()
        assert (project / "scripts" / "exec.cmd").exists()
        assert (project / "scripts" / "exec.sh").exists()

        # ---- Step 4: CI config (tool-aware) ----
        ci_path = project / ".github" / "workflows" / "ci.yml"
        assert ci_path.exists()
        ci = ci_path.read_text(encoding="utf-8")
        assert "ruff" in ci
        assert "mypy" in ci
        assert "pytest" in ci
        assert "pip-audit" in ci
        assert "setup-python" in ci

        # ---- Step 5: Dependabot ----
        dep_path = project / ".github" / "dependabot.yml"
        assert dep_path.exists()
        dep = dep_path.read_text(encoding="utf-8")
        assert "pip" in dep
        assert "github-actions" in dep

        # ---- Step 6: Agent integration files ----
        assert (project / ".warp" / "skills" / "SKILL.md").exists()
        assert (project / "CLAUDE.md").exists()

        # ---- Step 7: scaffold.yml saved ----
        saved = project / "scaffold.yml"
        assert saved.exists()
        with open(saved) as f:
            cfg = yaml.safe_load(f)
        assert cfg["name"] == "forge-cli"
        assert cfg["type"] == "cli-python"
        assert cfg["vcs_platform"] == "github"

        # ---- Step 8: verification.md has tools ----
        verification = (gov / "verification.md").read_text(encoding="utf-8")
        assert "ruff" in verification
        assert "mypy" in verification
        assert "pytest" in verification

        # ---- Step 9: AGENTS.md has type-specific rules ----
        agents = (project / "AGENTS.md").read_text(encoding="utf-8")
        assert "CLI" in agents or "cli" in agents.lower()

        # ---- Step 10: Audit passes ----
        audit_result = runner.invoke(main, ["audit", "--project-dir", str(project)])
        assert audit_result.exit_code == 0, f"Audit failed: {audit_result.output}"
        assert "Healthy" in audit_result.output

        # ---- Step 11: Validate passes ----
        validate_result = runner.invoke(main, ["validate", "--project-dir", str(project)])
        assert validate_result.exit_code == 0, f"Validate failed: {validate_result.output}"
        assert "Valid" in validate_result.output

        # ---- Step 12: Compress (no-op on fresh project) ----
        compress_result = runner.invoke(main, ["compress", "--project-dir", str(project)])
        assert compress_result.exit_code == 0
        assert "No compression needed" in compress_result.output

        # ---- Step 13: Upgrade to new version ----
        upgrade_result = runner.invoke(
            main, ["upgrade", "--project-dir", str(project), "--spec-version", "0.3.0"]
        )
        assert upgrade_result.exit_code == 0, f"Upgrade failed: {upgrade_result.output}"
        assert "Upgraded" in upgrade_result.output
        with open(saved) as f:
            upgraded_cfg = yaml.safe_load(f)
        assert upgraded_cfg["spec_version"] == "0.3.0"

        # ---- Step 14: Diff (may show differences after upgrade) ----
        diff_result = runner.invoke(main, ["diff", "--project-dir", str(project)])
        assert diff_result.exit_code == 0

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
            "docs/governance/rules.md",
            "docs/governance/verification.md",
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
