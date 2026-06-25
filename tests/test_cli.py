# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
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
        # Backdate spec_version so there is an actual upgrade to perform.
        # Without this the scaffold is already at __version__ and the
        # command would return "Already at spec version" instead.
        scaffold_yml = target / "scaffold.yml"
        with open(scaffold_yml) as fh:
            data = yaml.safe_load(fh)
        data["spec_version"] = "0.11.6"
        with open(scaffold_yml, "w") as fh:
            yaml.dump(data, fh, default_flow_style=False)
        runner = CliRunner()
        result = runner.invoke(
            main, ["upgrade", "--project-dir", str(target), "--spec-version", "0.17.1"]
        )
        assert result.exit_code == 0
        assert "Upgraded" in result.output
        # Verify scaffold.yml spec_version was updated to the target version
        with open(target / "scaffold.yml") as fh:
            data = yaml.safe_load(fh)
        assert data["spec_version"] == "0.16.5"


class TestCLICreditsLimits:
    def test_set_and_list_limits_profile(self, tmp_path: Path) -> None:
        runner = CliRunner()

        set_result = runner.invoke(
            main,
            [
                "credits",
                "limits",
                "set",
                "--project-dir",
                str(tmp_path),
                "--provider",
                "openai",
                "--model",
                "gpt-5.4",
                "--rpm",
                "60",
                "--tpm",
                "500000",
                "--target",
                "0.7",
                "--concurrency",
                "4",
            ],
        )
        assert set_result.exit_code == 0
        assert "Saved openai/gpt-5.4" in set_result.output

        list_result = runner.invoke(
            main,
            ["credits", "limits", "list", "--project-dir", str(tmp_path)],
        )
        assert list_result.exit_code == 0
        assert "openai/gpt-5.4" in list_result.output
        assert "RPM=60 TPM=500000" in list_result.output
