"""Tests for VCS platform integrations."""

from __future__ import annotations

from pathlib import Path

import pytest

from specsmith.config import Platform, ProjectConfig, ProjectType
from specsmith.vcs import get_platform, list_platforms
from specsmith.vcs.base import CommandResult
from specsmith.vcs.bitbucket import BitbucketPlatform
from specsmith.vcs.github import GitHubPlatform
from specsmith.vcs.gitlab import GitLabPlatform


@pytest.fixture
def python_config() -> ProjectConfig:
    return ProjectConfig(
        name="test-project",
        type=ProjectType.CLI_PYTHON,
        platforms=[Platform.LINUX],
        language="python",
        git_init=False,
    )


@pytest.fixture
def fpga_config() -> ProjectConfig:
    return ProjectConfig(
        name="test-fpga",
        type=ProjectType.FPGA_RTL,
        platforms=[Platform.LINUX],
        language="vhdl",
        git_init=False,
    )


class TestPlatformRegistry:
    def test_list_platforms(self) -> None:
        platforms = list_platforms()
        assert "github" in platforms
        assert "gitlab" in platforms
        assert "bitbucket" in platforms

    def test_get_platform(self) -> None:
        gh = get_platform("github")
        assert isinstance(gh, GitHubPlatform)

    def test_get_unknown_platform(self) -> None:
        with pytest.raises(ValueError, match="Unknown VCS platform"):
            get_platform("nonexistent")


class TestGitHubPlatform:
    def test_generates_ci(self, python_config: ProjectConfig, tmp_path: Path) -> None:
        gh = GitHubPlatform()
        files = gh.generate_ci_config(python_config, tmp_path)
        assert len(files) == 1
        assert files[0].name == "ci.yml"
        content = files[0].read_text(encoding="utf-8")
        assert "ruff" in content
        assert "mypy" in content
        assert "pytest" in content
        assert "pip-audit" in content

    def test_generates_dependabot(self, python_config: ProjectConfig, tmp_path: Path) -> None:
        gh = GitHubPlatform()
        files = gh.generate_dependency_config(python_config, tmp_path)
        assert len(files) == 1
        content = files[0].read_text(encoding="utf-8")
        assert "pip" in content
        assert "github-actions" in content

    def test_generate_all(self, python_config: ProjectConfig, tmp_path: Path) -> None:
        gh = GitHubPlatform()
        files = gh.generate_all(python_config, tmp_path)
        names = {f.name for f in files}
        assert "ci.yml" in names
        assert "dependabot.yml" in names

    def test_fpga_ci_has_placeholder(self, fpga_config: ProjectConfig, tmp_path: Path) -> None:
        gh = GitHubPlatform()
        files = gh.generate_ci_config(fpga_config, tmp_path)
        content = files[0].read_text(encoding="utf-8")
        assert "FPGA" in content

    def test_cli_name(self) -> None:
        assert GitHubPlatform().cli_name == "gh"

    def test_command_result_on_missing_cli(self) -> None:
        gh = GitHubPlatform()
        # Use a command that would fail if gh is not configured for this repo
        result = gh.run_command(["--version"])
        assert isinstance(result, CommandResult)


class TestGitLabPlatform:
    def test_generates_ci(self, python_config: ProjectConfig, tmp_path: Path) -> None:
        gl = GitLabPlatform()
        files = gl.generate_ci_config(python_config, tmp_path)
        assert len(files) == 1
        assert files[0].name == ".gitlab-ci.yml"
        content = files[0].read_text(encoding="utf-8")
        assert "stages:" in content
        assert "ruff" in content
        assert "pip-audit" in content

    def test_generates_renovate(self, python_config: ProjectConfig, tmp_path: Path) -> None:
        gl = GitLabPlatform()
        files = gl.generate_dependency_config(python_config, tmp_path)
        assert len(files) == 1
        assert files[0].name == "renovate.json"

    def test_cli_name(self) -> None:
        assert GitLabPlatform().cli_name == "glab"


class TestBitbucketPlatform:
    def test_generates_pipelines(self, python_config: ProjectConfig, tmp_path: Path) -> None:
        bb = BitbucketPlatform()
        files = bb.generate_ci_config(python_config, tmp_path)
        assert len(files) == 1
        assert files[0].name == "bitbucket-pipelines.yml"
        content = files[0].read_text(encoding="utf-8")
        assert "pipelines:" in content
        assert "ruff" in content

    def test_generates_renovate(self, python_config: ProjectConfig, tmp_path: Path) -> None:
        bb = BitbucketPlatform()
        files = bb.generate_dependency_config(python_config, tmp_path)
        assert len(files) == 1
        assert files[0].name == "renovate.json"

    def test_cli_name(self) -> None:
        assert BitbucketPlatform().cli_name == "bb"

    def test_alerts_message(self) -> None:
        bb = BitbucketPlatform()
        result = bb.list_alerts()
        assert result.success
        assert "Renovate" in result.output
