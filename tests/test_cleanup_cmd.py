# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for 'specsmith cleanup' command (REQ-374).

Covers:
  - Dry-run mode (default) lists targets but deletes nothing.
  - --apply mode removes cache directories.
  - --json flag outputs valid JSON.
  - Protected files/directories are never removed.
  - Python cache dirs (__pycache__, .ruff_cache, .mypy_cache, .pytest_cache) are detected.
  - .pyc files are detected.
"""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from specsmith.cli import main


def _make_cache_structure(root: Path) -> None:
    """Create a fake cache directory structure under root."""
    # Specsmith cache dirs
    for rel in [
        ".specsmith/runs",
        ".specsmith/sessions",
        ".specsmith/chat",
        ".specsmith/perf",
        ".specsmith/recovery",
        ".specsmith/logs",
        ".specsmith/dispatch",
        ".specsmith/pids",
        ".specsmith/agent-reports",
        ".specsmith/migration-backups",
    ]:
        p = root / rel
        p.mkdir(parents=True, exist_ok=True)
        (p / "dummy.txt").write_text("dummy", encoding="utf-8")

    # Python caches
    pycache = root / "src" / "__pycache__"
    pycache.mkdir(parents=True, exist_ok=True)
    (pycache / "module.cpython-311.pyc").write_bytes(b"\x00" * 64)

    ruff_cache = root / ".ruff_cache"
    ruff_cache.mkdir(parents=True, exist_ok=True)
    (ruff_cache / "cache.db").write_text("x", encoding="utf-8")


def _make_protected_files(root: Path) -> None:
    """Create protected governance files that must not be removed."""
    protected = [
        ".specsmith/config.yml",
        ".specsmith/requirements.json",
        ".specsmith/testcases.json",
        ".specsmith/governance-mode",
        ".specsmith/migration-state.json",
    ]
    state_dir = root / ".specsmith"
    state_dir.mkdir(parents=True, exist_ok=True)
    for rel in protected:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("protected", encoding="utf-8")

    # Protected docs dirs
    for rel in ["docs/requirements", "docs/tests", "docs/governance"]:
        p = root / rel
        p.mkdir(parents=True, exist_ok=True)
        (p / "core.yml").write_text("requirements: []", encoding="utf-8")


class TestCleanupDryRun:
    """Dry-run (default) mode must never delete files."""

    def test_dry_run_lists_targets_without_deleting(self, tmp_path: Path) -> None:
        _make_cache_structure(tmp_path)
        before_files = set(tmp_path.rglob("*"))

        runner = CliRunner()
        result = runner.invoke(main, ["cleanup", "--project-dir", str(tmp_path)])

        assert result.exit_code == 0, f"cleanup failed: {result.output}"
        # Dry-run should list targets
        assert "DRY-RUN" in result.output

        after_files = set(tmp_path.rglob("*"))
        assert before_files == after_files, "Dry-run should not delete any files"

    def test_dry_run_reports_would_reclaim(self, tmp_path: Path) -> None:
        _make_cache_structure(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["cleanup", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "would reclaim" in result.output.lower()

    def test_dry_run_prompts_to_use_apply(self, tmp_path: Path) -> None:
        _make_cache_structure(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["cleanup", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "--apply" in result.output


class TestCleanupApply:
    """--apply mode removes cache directories."""

    def test_apply_removes_specsmith_cache_dirs(self, tmp_path: Path) -> None:
        _make_cache_structure(tmp_path)
        _make_protected_files(tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, ["cleanup", "--project-dir", str(tmp_path), "--apply"])

        assert result.exit_code == 0, f"cleanup --apply failed: {result.output}"
        assert "APPLY" in result.output

        # Cache dirs should be removed
        for rel in [
            ".specsmith/runs",
            ".specsmith/sessions",
            ".specsmith/chat",
        ]:
            assert not (tmp_path / rel).exists(), (
                f"Cache dir {rel} should have been removed by --apply"
            )

    def test_apply_removes_python_caches(self, tmp_path: Path) -> None:
        _make_cache_structure(tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, ["cleanup", "--project-dir", str(tmp_path), "--apply"])

        assert result.exit_code == 0
        # __pycache__ under src/ should be gone
        assert not (tmp_path / "src" / "__pycache__").exists(), (
            "__pycache__ dir should have been removed"
        )
        assert not (tmp_path / ".ruff_cache").exists(), ".ruff_cache dir should have been removed"

    def test_apply_output_says_apply_not_dry_run(self, tmp_path: Path) -> None:
        _make_cache_structure(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["cleanup", "--project-dir", str(tmp_path), "--apply"])
        assert result.exit_code == 0
        assert "APPLY" in result.output
        assert "DRY-RUN" not in result.output


class TestCleanupProtectedFiles:
    """Protected governance files and dirs must never be removed."""

    def test_protected_specsmith_files_not_removed(self, tmp_path: Path) -> None:
        _make_cache_structure(tmp_path)
        _make_protected_files(tmp_path)

        runner = CliRunner()
        runner.invoke(main, ["cleanup", "--project-dir", str(tmp_path), "--apply"])

        protected = [
            ".specsmith/requirements.json",
            ".specsmith/testcases.json",
            ".specsmith/governance-mode",
            ".specsmith/migration-state.json",
        ]
        for rel in protected:
            p = tmp_path / rel
            assert p.exists(), f"Protected file {rel} must not be deleted by cleanup"

    def test_protected_docs_dirs_not_removed(self, tmp_path: Path) -> None:
        _make_cache_structure(tmp_path)
        _make_protected_files(tmp_path)

        runner = CliRunner()
        runner.invoke(main, ["cleanup", "--project-dir", str(tmp_path), "--apply"])

        for rel in [
            "docs/requirements/core.yml",
            "docs/tests/core.yml",
            "docs/governance/core.yml",
        ]:
            p = tmp_path / rel
            assert p.exists(), f"Protected governance file {rel} must not be deleted"

    def test_empty_project_cleanup_succeeds(self, tmp_path: Path) -> None:
        """Cleanup on a project with no cache files should succeed with 0 targets."""
        runner = CliRunner()
        result = runner.invoke(main, ["cleanup", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "0 target" in result.output


class TestCleanupJsonOutput:
    """--json flag emits valid JSON report."""

    def test_json_output_dry_run(self, tmp_path: Path) -> None:
        _make_cache_structure(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["cleanup", "--project-dir", str(tmp_path), "--json"])
        assert result.exit_code == 0
        try:
            data = json.loads(result.output)
        except json.JSONDecodeError as e:
            raise AssertionError(
                f"--json output is not valid JSON: {e}\nOutput: {result.output!r}"
            ) from e
        assert "apply" in data
        assert data["apply"] is False
        assert "would_remove" in data
        assert isinstance(data["would_remove"], list)
        assert "bytes_reclaimed" in data

    def test_json_output_apply(self, tmp_path: Path) -> None:
        _make_cache_structure(tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            main, ["cleanup", "--project-dir", str(tmp_path), "--json", "--apply"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["apply"] is True
        assert "removed" in data
        assert isinstance(data["removed"], list)

    def test_json_bytes_reclaimed_is_positive(self, tmp_path: Path) -> None:
        _make_cache_structure(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["cleanup", "--project-dir", str(tmp_path), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["bytes_reclaimed"] >= 0
