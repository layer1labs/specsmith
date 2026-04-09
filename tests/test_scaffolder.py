# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Integration tests for specsmith scaffolder."""

from __future__ import annotations

from pathlib import Path

import pytest

from specsmith.config import Platform, ProjectConfig, ProjectType
from specsmith.scaffolder import scaffold_project


@pytest.fixture
def tmp_target(tmp_path: Path) -> Path:
    """Return a temporary target directory for scaffold output."""
    return tmp_path / "test-project"


def _make_config(
    project_type: ProjectType = ProjectType.CLI_PYTHON,
    **overrides: object,
) -> ProjectConfig:
    defaults: dict[str, object] = {
        "name": "test-project",
        "type": project_type,
        "platforms": [Platform.WINDOWS, Platform.LINUX],
        "language": "python",
        "description": "Test scaffold",
        "git_init": False,
    }
    defaults.update(overrides)
    return ProjectConfig(**defaults)  # type: ignore[arg-type]


class TestScaffoldCLIPython:
    """Tests for CLI Python project type."""

    def test_creates_expected_files(self, tmp_target: Path) -> None:
        cfg = _make_config(ProjectType.CLI_PYTHON)
        files = scaffold_project(cfg, tmp_target)
        rel_names = {str(f.relative_to(tmp_target)) for f in files}

        # Governance files
        assert "AGENTS.md" in rel_names
        assert "LEDGER.md" in rel_names
        assert "README.md" in rel_names

        # Modular governance
        for gov in (
            "RULES.md",
            "SESSION-PROTOCOL.md",
            "LIFECYCLE.md",
            "ROLES.md",
            "CONTEXT-BUDGET.md",
            "VERIFICATION.md",
            "DRIFT-METRICS.md",
        ):
            assert f"docs\\governance\\{gov}" in rel_names or f"docs/governance/{gov}" in rel_names

        # Scripts
        assert any("exec.cmd" in n for n in rel_names)
        assert any("exec.sh" in n for n in rel_names)

        # Python source
        assert any("__init__.py" in n for n in rel_names)
        assert any("cli.py" in n for n in rel_names)

    def test_pyproject_toml_generated(self, tmp_target: Path) -> None:
        cfg = _make_config(ProjectType.CLI_PYTHON)
        scaffold_project(cfg, tmp_target)
        pyproject = tmp_target / "pyproject.toml"
        assert pyproject.exists()
        content = pyproject.read_text(encoding="utf-8")
        assert "test-project" in content or "test_project" in content

    def test_gitkeep_in_empty_dirs(self, tmp_target: Path) -> None:
        cfg = _make_config(ProjectType.CLI_PYTHON)
        files = scaffold_project(cfg, tmp_target)
        gitkeep_files = [f for f in files if f.name == ".gitkeep"]
        assert len(gitkeep_files) >= 2  # tests/ + commands/ + utils/

    def test_file_count(self, tmp_target: Path) -> None:
        cfg = _make_config(ProjectType.CLI_PYTHON)
        files = scaffold_project(cfg, tmp_target)
        assert len(files) >= 25  # baseline for cli-python type


class TestScaffoldFPGA:
    """Tests for FPGA/RTL project type."""

    def test_no_pyproject(self, tmp_target: Path) -> None:
        cfg = _make_config(ProjectType.FPGA_RTL)
        scaffold_project(cfg, tmp_target)
        assert not (tmp_target / "pyproject.toml").exists()

    def test_governance_files_present(self, tmp_target: Path) -> None:
        cfg = _make_config(ProjectType.FPGA_RTL)
        files = scaffold_project(cfg, tmp_target)
        rel_names = {f.name for f in files}
        assert "AGENTS.md" in rel_names
        assert "LEDGER.md" in rel_names
        assert "RULES.md" in rel_names


class TestScaffoldLibrary:
    """Tests for library Python project type."""

    def test_creates_pyproject_no_cli(self, tmp_target: Path) -> None:
        cfg = _make_config(ProjectType.LIBRARY_PYTHON)
        files = scaffold_project(cfg, tmp_target)
        rel_names = {str(f.relative_to(tmp_target)) for f in files}

        # Has pyproject.toml
        assert "pyproject.toml" in rel_names
        # No cli.py
        assert not any("cli.py" in n for n in rel_names)


class TestScaffoldOptions:
    """Tests for scaffold configuration options."""

    def test_exec_shims_disabled(self, tmp_target: Path) -> None:
        cfg = _make_config(exec_shims=False)
        files = scaffold_project(cfg, tmp_target)
        rel_names = {f.name for f in files}
        assert "exec.cmd" not in rel_names
        assert "exec.sh" not in rel_names

    def test_all_files_have_content(self, tmp_target: Path) -> None:
        cfg = _make_config()
        files = scaffold_project(cfg, tmp_target)
        for f in files:
            if f.name != ".gitkeep":
                assert f.stat().st_size > 0, f"{f} is empty"

    def test_package_name_sanitized(self) -> None:
        cfg = _make_config(name="my-cool-project")
        assert cfg.package_name == "my_cool_project"
