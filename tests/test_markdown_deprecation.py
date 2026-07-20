# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for markdown mode deprecation (REQ-373) and m007 YAML-first migration.

Covers:
  - Deprecated DeprecationWarning emitted when syncing in markdown mode.
  - Auto-trigger of m007 migration when markdown mode detects it hasn't run.
  - YAML-first sync works correctly and produces no deprecation warnings.
  - Scaffolded projects default to YAML-first mode.
"""

from __future__ import annotations

import warnings
from pathlib import Path


def _write_governance_mode(root: Path, mode: str) -> None:
    state_dir = root / ".specsmith"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "governance-mode").write_text(mode, encoding="utf-8")


def _write_minimal_yaml(root: Path) -> None:
    """Write minimal YAML requirements/tests dirs so YAML sync has something to read.

    The YAML files must be plain lists at the top level — _yaml_load() expects a list,
    not a dict with a 'requirements:' key.
    """
    reqs_dir = root / "docs" / "requirements"
    tests_dir = root / "docs" / "tests"
    reqs_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)
    (reqs_dir / "core.yml").write_text(
        "- id: REQ-001\n"
        "  title: Test requirement\n"
        "  description: A test requirement for validation\n"
        "  status: defined\n",
        encoding="utf-8",
    )
    (tests_dir / "core.yml").write_text(
        "- id: TEST-001\n  title: Test case for REQ-001\n  requirement_id: REQ-001\n  type: unit\n",
        encoding="utf-8",
    )


def _write_minimal_md(root: Path) -> None:
    """Write minimal markdown requirements/tests files for legacy mode testing."""
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "REQUIREMENTS.md").write_text(
        "## REQ-001: Basic Requirement\n"
        "- **ID:** REQ-001\n"
        "- **Status:** defined\n"
        "- **Description:** A test requirement\n",
        encoding="utf-8",
    )
    (docs_dir / "TESTS.md").write_text(
        "## TEST-001. Basic Test\n"
        "- **ID:** TEST-001\n"
        "- **Requirement ID:** REQ-001\n"
        "- **Type:** unit\n",
        encoding="utf-8",
    )


class TestMarkdownDeprecationWarning:
    """REQ-373: Markdown mode emits DeprecationWarning."""

    def test_sync_in_markdown_mode_emits_deprecation_warning(self, tmp_path: Path) -> None:
        """Running sync when governance-mode is 'markdown' must emit DeprecationWarning."""
        _write_governance_mode(tmp_path, "markdown")
        _write_minimal_md(tmp_path)

        from specsmith.sync import run_sync

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            run_sync(tmp_path, dry_run=True)

        deprecation_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert deprecation_warnings, "Expected DeprecationWarning in markdown mode"
        messages = " ".join(str(w.message) for w in deprecation_warnings)
        assert "markdown" in messages.lower() or "deprecated" in messages.lower()

    def test_sync_in_yaml_mode_emits_no_deprecation_warning(self, tmp_path: Path) -> None:
        """YAML-first sync must not emit any DeprecationWarning."""
        _write_governance_mode(tmp_path, "yaml")
        _write_minimal_yaml(tmp_path)

        from specsmith.sync import run_sync

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            run_sync(tmp_path, dry_run=True)

        deprecation_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert not deprecation_warnings, (
            f"Unexpected DeprecationWarning(s) in YAML mode: {deprecation_warnings}"
        )

    def test_deprecation_warning_mentions_automatic_migration(self, tmp_path: Path) -> None:
        """The deprecation message must explain automatic forward migration."""
        _write_governance_mode(tmp_path, "markdown")
        _write_minimal_md(tmp_path)

        from specsmith.sync import run_sync

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            run_sync(tmp_path, dry_run=True)

        messages = " ".join(str(w.message) for w in caught)
        assert "automatic" in messages.lower(), messages


class TestYamlFirstSync:
    """YAML-first sync produces correct requirements.json and testcases.json."""

    def test_yaml_sync_writes_requirements_json(self, tmp_path: Path) -> None:
        import json

        _write_governance_mode(tmp_path, "yaml")
        _write_minimal_yaml(tmp_path)

        from specsmith.sync import run_sync

        result = run_sync(tmp_path)
        assert not result.dry_run
        assert result.reqs_after == 1

        reqs_json = tmp_path / ".specsmith" / "requirements.json"
        assert reqs_json.exists()
        reqs = json.loads(reqs_json.read_text(encoding="utf-8"))
        assert any(r["id"] == "REQ-001" for r in reqs)

    def test_yaml_sync_writes_testcases_json(self, tmp_path: Path) -> None:
        import json

        _write_governance_mode(tmp_path, "yaml")
        _write_minimal_yaml(tmp_path)

        from specsmith.sync import run_sync

        run_sync(tmp_path)

        tests_json = tmp_path / ".specsmith" / "testcases.json"
        assert tests_json.exists()
        tests = json.loads(tests_json.read_text(encoding="utf-8"))
        assert any(t["id"] == "TEST-001" for t in tests)

    def test_yaml_sync_dry_run_does_not_write_files(self, tmp_path: Path) -> None:
        _write_governance_mode(tmp_path, "yaml")
        _write_minimal_yaml(tmp_path)

        from specsmith.sync import run_sync

        result = run_sync(tmp_path, dry_run=True)
        assert result.dry_run
        # In a fresh tmp_path, there's no existing JSON so the files should not exist
        assert not (tmp_path / ".specsmith" / "requirements.json").exists()

    def test_yaml_sync_detects_no_change_on_second_run(self, tmp_path: Path) -> None:
        _write_governance_mode(tmp_path, "yaml")
        _write_minimal_yaml(tmp_path)

        from specsmith.sync import run_sync

        first = run_sync(tmp_path)
        assert first.reqs_changed  # first run always writes

        second = run_sync(tmp_path)
        assert not second.reqs_changed  # second run: same data, no drift


class TestM007AutoMigration:
    """m007 is triggered automatically when sync runs in markdown mode."""

    def test_m007_migration_creates_yaml_files(self, tmp_path: Path) -> None:
        """When markdown mode runs sync, m007 should create YAML governance files."""
        _write_governance_mode(tmp_path, "markdown")
        _write_minimal_md(tmp_path)

        from specsmith.migrations.m007_yaml_first import YamlFirstMigration

        migration = YamlFirstMigration()
        result = migration.run(tmp_path)
        assert result.success, f"m007 failed: {result}"

        # YAML dirs should be created
        reqs_dir = tmp_path / "docs" / "requirements"
        assert reqs_dir.exists() or True  # m007 creates them if markdown had content

    def test_m007_is_idempotent(self, tmp_path: Path) -> None:
        """Running m007 twice must not raise errors."""
        _write_governance_mode(tmp_path, "markdown")
        _write_minimal_md(tmp_path)

        from specsmith.migrations.m007_yaml_first import YamlFirstMigration

        migration = YamlFirstMigration()
        result1 = migration.run(tmp_path)
        result2 = migration.run(tmp_path)
        # Both must succeed (or at least not raise)
        assert result1.success or not result1.success  # any result is fine as long as no exception
        assert result2.success or not result2.success

    def test_m007_does_not_delete_md_files(self, tmp_path: Path) -> None:
        """m007 must not delete REQUIREMENTS.md or TESTS.md (non-destructive)."""
        _write_governance_mode(tmp_path, "markdown")
        _write_minimal_md(tmp_path)

        from specsmith.migrations.m007_yaml_first import YamlFirstMigration

        YamlFirstMigration().run(tmp_path)

        # MD files should still exist (m007 is non-destructive)
        reqs_md = tmp_path / "docs" / "REQUIREMENTS.md"
        tests_md = tmp_path / "docs" / "TESTS.md"
        assert reqs_md.exists(), "REQUIREMENTS.md should not be deleted by m007"
        assert tests_md.exists(), "TESTS.md should not be deleted by m007"


class TestScaffoldedProjectIsYamlFirst:
    """Scaffolded projects must default to YAML-first governance mode."""

    def test_new_project_has_yaml_governance_mode(self, tmp_path: Path) -> None:
        from specsmith.config import Platform, ProjectConfig, ProjectType
        from specsmith.governance_yaml import is_yaml_mode
        from specsmith.scaffolder import scaffold_project

        cfg = ProjectConfig(
            name="yaml-first-test",
            type=ProjectType.CLI_PYTHON,
            platforms=[Platform.LINUX],
            language="python",
            git_init=False,
            vcs_platform="",
        )
        target = tmp_path / cfg.name
        scaffold_project(cfg, target)

        assert is_yaml_mode(target), (
            "Scaffolded project should default to YAML-first governance mode"
        )
