# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for the project importer detection engine."""

from __future__ import annotations

from pathlib import Path

from specsmith.config import ProjectType
from specsmith.importer import (
    detect_project,
    generate_import_config,
    generate_overlay,
)


def _make_python_project(tmp_path: Path) -> Path:
    """Create a minimal Python project for import testing."""
    root = tmp_path / "my-py-project"
    root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nname = "my-py-project"\n')
    src = root / "src" / "my_py_project"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("")
    (src / "cli.py").write_text("import click\n")
    (root / "tests").mkdir()
    (root / "tests" / "test_cli.py").write_text("def test_it(): pass\n")
    (root / "conftest.py").write_text("")
    return root


def _make_rust_project(tmp_path: Path) -> Path:
    """Create a minimal Rust project."""
    root = tmp_path / "my-rust-cli"
    root.mkdir()
    (root / "Cargo.toml").write_text('[package]\nname = "my-rust-cli"\n')
    (root / "src").mkdir()
    (root / "src" / "main.rs").write_text("fn main() {}\n")
    return root


def _make_js_project(tmp_path: Path) -> Path:
    """Create a minimal JS project."""
    root = tmp_path / "my-web-app"
    root.mkdir()
    (root / "package.json").write_text('{"name": "my-web-app", "dependencies": {"react": "^18"}}\n')
    src = root / "src"
    src.mkdir()
    (src / "index.tsx").write_text("export default function App() {}\n")
    (src / "components").mkdir()
    (src / "components" / "Header.tsx").write_text("")
    return root


class TestDetectProject:
    def test_detect_python(self, tmp_path: Path) -> None:
        root = _make_python_project(tmp_path)
        result = detect_project(root)

        assert result.primary_language == "python"
        assert result.build_system == "pyproject"
        assert result.test_framework == "pytest"
        assert result.inferred_type == ProjectType.CLI_PYTHON
        assert "my_py_project" in result.modules
        assert result.file_count > 0

    def test_detect_rust(self, tmp_path: Path) -> None:
        root = _make_rust_project(tmp_path)
        result = detect_project(root)

        assert result.primary_language == "rust"
        assert result.build_system == "cargo"
        assert result.inferred_type == ProjectType.CLI_RUST
        assert "main" in result.modules

    def test_detect_js_web(self, tmp_path: Path) -> None:
        root = _make_js_project(tmp_path)
        result = detect_project(root)

        assert result.primary_language in ("tsx", "typescript", "javascript", "jsx")
        assert result.build_system == "npm"
        assert result.inferred_type == ProjectType.WEB_FRONTEND

    def test_detect_entry_points(self, tmp_path: Path) -> None:
        root = _make_python_project(tmp_path)
        result = detect_project(root)
        assert any("cli.py" in ep for ep in result.entry_points)

    def test_detect_test_files(self, tmp_path: Path) -> None:
        root = _make_python_project(tmp_path)
        result = detect_project(root)
        assert any("test_cli" in tf for tf in result.test_files)

    def test_detect_ci_github(self, tmp_path: Path) -> None:
        root = _make_python_project(tmp_path)
        wf = root / ".github" / "workflows"
        wf.mkdir(parents=True)
        (wf / "ci.yml").write_text("name: CI\n")
        result = detect_project(root)
        assert result.existing_ci == "github"

    def test_detect_governance(self, tmp_path: Path) -> None:
        root = _make_python_project(tmp_path)
        (root / "AGENTS.md").write_text("# Agent governance\n")
        result = detect_project(root)
        assert "AGENTS.md" in result.existing_governance

    def test_empty_dir(self, tmp_path: Path) -> None:
        root = tmp_path / "empty"
        root.mkdir()
        result = detect_project(root)
        assert result.file_count == 0
        assert result.inferred_type == ProjectType.CLI_PYTHON  # safe default


class TestGenerateImportConfig:
    def test_config_from_python(self, tmp_path: Path) -> None:
        root = _make_python_project(tmp_path)
        result = detect_project(root)
        config = generate_import_config(result)

        assert config.name == "my-py-project"
        assert config.type == ProjectType.CLI_PYTHON
        assert config.language == "python"
        assert config.detected_build_system == "pyproject"
        assert config.detected_test_framework == "pytest"
        assert config.git_init is False

    def test_config_from_rust(self, tmp_path: Path) -> None:
        root = _make_rust_project(tmp_path)
        result = detect_project(root)
        config = generate_import_config(result)

        assert config.type == ProjectType.CLI_RUST
        assert config.language == "rust"


class TestGenerateOverlay:
    def test_overlay_creates_files(self, tmp_path: Path) -> None:
        root = _make_python_project(tmp_path)
        result = detect_project(root)
        created = generate_overlay(result, root)

        created_names = [p.name for p in created]
        assert "AGENTS.md" in created_names
        assert "LEDGER.md" in created_names
        assert "REQUIREMENTS.md" in created_names
        assert "TESTS.md" in created_names
        assert "ARCHITECTURE.md" in created_names

    def test_overlay_skip_existing(self, tmp_path: Path) -> None:
        root = _make_python_project(tmp_path)
        (root / "AGENTS.md").write_text("existing\n")
        result = detect_project(root)
        created = generate_overlay(result, root)

        # AGENTS.md should NOT be in created (exists, no force)
        assert not any(p.name == "AGENTS.md" for p in created)
        # Content should be preserved
        assert (root / "AGENTS.md").read_text() == "existing\n"

    def test_overlay_force_overwrites(self, tmp_path: Path) -> None:
        root = _make_python_project(tmp_path)
        (root / "AGENTS.md").write_text("existing\n")
        result = detect_project(root)
        created = generate_overlay(result, root, force=True)

        assert any(p.name == "AGENTS.md" for p in created)
        assert "existing" not in (root / "AGENTS.md").read_text()

    def test_overlay_reqs_contain_modules(self, tmp_path: Path) -> None:
        root = _make_python_project(tmp_path)
        result = detect_project(root)
        generate_overlay(result, root)

        reqs = (root / "docs" / "REQUIREMENTS.md").read_text()
        assert "REQ-MY_PY_PROJECT-001" in reqs

    def test_overlay_architecture_has_lang(self, tmp_path: Path) -> None:
        root = _make_python_project(tmp_path)
        result = detect_project(root)
        generate_overlay(result, root)

        arch = (root / "docs" / "ARCHITECTURE.md").read_text()
        assert "python" in arch
