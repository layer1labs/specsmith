"""Regression coverage for the governed branching-workflow selection."""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from specsmith.cli import main
from specsmith.config import ProjectConfig
from specsmith.vcs_commands import GitResult, create_branch, create_pr


def test_project_config_defaults_to_single_branch() -> None:
    assert ProjectConfig(name="workflow-test").branching_strategy == "single-branch"


def test_single_branch_refuses_branch_creation(tmp_path: Path) -> None:
    result = create_branch(tmp_path, "new-feature")

    assert not result.success
    assert "Branch creation is disabled" in result.message


def test_gitflow_branch_creation_remains_available(tmp_path: Path, monkeypatch) -> None:
    captured: list[str] = []

    def fake_run_git(root: Path, args: list[str]) -> GitResult:
        captured.extend(args)
        return GitResult(success=True, message="created")

    monkeypatch.setattr("specsmith.vcs_commands._run_git", fake_run_git)

    result = create_branch(tmp_path, "feature/workflow", strategy="gitflow")

    assert result.success
    assert captured == ["checkout", "-b", "feature/workflow", "develop"]


def test_single_branch_refuses_pull_request(tmp_path: Path) -> None:
    (tmp_path / "scaffold.yml").write_text(
        "branching_strategy: single-branch\n",
        encoding="utf-8",
    )

    result = create_pr(tmp_path)

    assert not result.success
    assert "Pull requests are disabled" in result.message


def test_branch_workflow_command_enables_gitflow(tmp_path: Path) -> None:
    (tmp_path / "scaffold.yml").write_text(
        "name: workflow-test\nbranching_strategy: single-branch\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        ["branch", "workflow", "gitflow", "--project-dir", str(tmp_path)],
    )

    assert result.exit_code == 0, result.output
    config = yaml.safe_load((tmp_path / "scaffold.yml").read_text(encoding="utf-8"))
    assert config["branching_strategy"] == "gitflow"


def test_branch_workflow_command_reports_current_strategy(tmp_path: Path) -> None:
    (tmp_path / "scaffold.yml").write_text(
        "branching_strategy: single-branch\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        ["branch", "workflow", "--project-dir", str(tmp_path)],
    )

    assert result.exit_code == 0, result.output
    assert "Branch workflow: single-branch" in result.output
