# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""CLI tests using Click CliRunner."""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from specsmith.cli import main
from specsmith.config import ProjectConfig, ProjectType
from specsmith.scaffolder import scaffold_project


@staticmethod
def _scaffold_governed(tmp_path: Path) -> Path:
    """Create a minimal governed project for CLI testing."""
    from specsmith.config import Platform, ProjectConfig

    cfg = ProjectConfig(
        name="test-cli-project",
        type=ProjectType.CLI_PYTHON,
        platforms=[Platform.LINUX],
        language="python",
        git_init=False,
        vcs_platform="",
    )
    target = tmp_path / cfg.name
    scaffold_project(cfg, target)
    config_out = target / "scaffold.yml"
    with open(config_out, "w") as fh:
        yaml.dump(cfg.model_dump(mode="json"), fh, default_flow_style=False)
    return target


class TestCLIVersion:
    def test_version_flag(self) -> None:
        from specsmith import __version__

        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "specsmith" in result.output
        assert __version__ in result.output


class TestCLIInit:
    def test_init_from_config(self, tmp_path: Path) -> None:
        config = {
            "name": "test-init",
            "type": "cli-python",
            "platforms": ["linux"],
            "language": "python",
            "git_init": False,
            "vcs_platform": "",
        }
        config_path = tmp_path / "scaffold.yml"
        with open(config_path, "w") as fh:
            yaml.dump(config, fh)

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["init", "--config", str(config_path), "--output-dir", str(tmp_path), "--no-git"],
        )
        assert result.exit_code == 0
        assert "Done" in result.output
        assert (tmp_path / "test-init" / "AGENTS.md").exists()


class TestCLIAudit:
    def test_audit_healthy_project(self, tmp_path: Path) -> None:
        target = _scaffold_governed(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["audit", "--project-dir", str(target)])
        assert result.exit_code == 0
        assert "Healthy" in result.output


class TestCLIValidate:
    def test_validate_valid_project(self, tmp_path: Path) -> None:
        target = _scaffold_governed(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["validate", "--project-dir", str(target)])
        assert result.exit_code == 0
        assert "Valid" in result.output


class TestCLICompress:
    def test_compress_small_ledger(self, tmp_path: Path) -> None:
        target = _scaffold_governed(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["compress", "--project-dir", str(target)])
        assert result.exit_code == 0
        assert "No compression needed" in result.output


class TestCLIUpgrade:
    def test_upgrade_already_current(self, tmp_path: Path) -> None:
        target = _scaffold_governed(tmp_path)
        config = ProjectConfig(
            name="test-cli-project", type=ProjectType.CLI_PYTHON, language="python"
        )
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["upgrade", "--project-dir", str(target), "--spec-version", config.spec_version],
        )
        assert result.exit_code == 0
        assert "Already at spec version" in result.output

    def test_upgrade_to_new_version(self, tmp_path: Path) -> None:
        target = _scaffold_governed(tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            main, ["upgrade", "--project-dir", str(target), "--spec-version", "0.2.0"]
        )
        assert result.exit_code == 0
        assert "Upgraded" in result.output
        # Verify scaffold.yml was updated
        with open(target / "scaffold.yml") as fh:
            data = yaml.safe_load(fh)
        assert data["spec_version"] == "0.2.0"
