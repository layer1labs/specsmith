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


def _older_version(version: str) -> str:
    """Return a semantic version strictly older than ``version``.

    Decrements the least-significant non-zero component so the result is always
    a valid forward-upgrade target regardless of which release ``__version__``
    resolves to at runtime. Hardcoding a constant breaks whenever ``__version__``
    resolves to an equal-or-older release and the backward-migration guard
    (REQ-370) then refuses the upgrade.
    """
    import re

    match = re.match(r"(\d+)\.(\d+)(?:\.(\d+))?", version or "")
    if not match:
        return "0.0.0"
    major, minor, patch = (int(part) if part is not None else 0 for part in match.groups())
    if patch > 0:
        patch -= 1
    elif minor > 0:
        minor -= 1
    elif major > 0:
        major -= 1
    return f"{major}.{minor}.{patch}"


class TestCLIVersion:
    def test_version_flag(self) -> None:
        from specsmith import __version__

        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "specsmith" in result.output
        assert __version__ in result.output


class TestCLIHelp:
    def test_preflight_help_does_not_migrate_or_write_project_files(
        self, tmp_path, monkeypatch
    ) -> None:
        """TEST-475: help must not mutate a project that needs migration."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "SPECSMITH.yml").write_text(
            "name: temp-specsmith-repro\ntype: cli-python\nspec_version: 0.22.0\n",
            encoding="utf-8",
        )
        (tmp_path / "LEDGER.md").write_text("# Ledger\n", encoding="utf-8")
        before = {
            path.relative_to(tmp_path): path.read_bytes()
            for path in tmp_path.rglob("*")
            if path.is_file()
        }

        monkeypatch.chdir(tmp_path)
        result = CliRunner().invoke(
            main,
            ["preflight", "--help"],
            env={"SPECSMITH_NO_UPDATE_CHECK": "1"},
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.output
        assert "Usage: " in result.output
        assert "Auto-migrating" not in result.output
        after = {
            path.relative_to(tmp_path): path.read_bytes()
            for path in tmp_path.rglob("*")
            if path.is_file()
        }
        assert after == before


class TestCheckpointAnchor:
    def test_checkpoint_anchor_is_ascii_and_fixed_width(self, tmp_path: Path) -> None:
        """TEST-479: anchor rows must render safely in proportional-font clients."""
        result = CliRunner().invoke(
            main,
            ["checkpoint", "--project-dir", str(tmp_path)],
            env={"SPECSMITH_NO_AUTO_UPDATE": "1"},
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.output
        lines = result.output.splitlines()
        top = next(index for index, line in enumerate(lines) if line.startswith("+---"))
        bottom = next(
            index for index, line in enumerate(lines[top + 1 :], top + 1) if line.startswith("+---")
        )
        anchor = lines[top : bottom + 1]

        assert all(line.isascii() for line in anchor)
        assert all(len(line) == len(anchor[0]) for line in anchor)
        assert anchor[0] == anchor[-1]
        assert all(line.startswith("|") and line.endswith("|") for line in anchor[1:-1])
        assert "Health  : " in "\n".join(anchor)


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
        from specsmith import __version__

        target = _scaffold_governed(tmp_path)
        # Backdate spec_version so there is an actual upgrade to perform.
        # Derive it dynamically from __version__ so the value is always strictly
        # older than the upgrade target; otherwise the backward-migration guard
        # (REQ-370) refuses the upgrade whenever __version__ resolves to an
        # equal-or-older release than the previously hardcoded constant.
        scaffold_yml = target / "scaffold.yml"
        with open(scaffold_yml) as fh:
            data = yaml.safe_load(fh)
        data["spec_version"] = _older_version(__version__)
        with open(scaffold_yml, "w") as fh:
            yaml.dump(data, fh, default_flow_style=False)
        runner = CliRunner()
        result = runner.invoke(
            main, ["upgrade", "--project-dir", str(target), "--spec-version", __version__]
        )
        assert result.exit_code == 0
        assert "Upgraded" in result.output
        # Verify scaffold.yml spec_version was updated to the target version
        with open(target / "scaffold.yml") as fh:
            data = yaml.safe_load(fh)
        assert data["spec_version"] == __version__


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
