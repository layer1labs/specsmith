# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Migration direction enforcement tests — REQ-369, REQ-370, TEST-369..371."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_scaffold(tmp_path: Path, spec_version: str) -> Path:
    """Create a minimal scaffold.yml with the given spec_version."""
    scaffold = tmp_path / "scaffold.yml"
    data = {
        "name": "test-proj",
        "type": "cli-python",
        "language": "python",
        "spec_version": spec_version,
    }
    scaffold.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# TEST-370 / REQ-369: agents.md.j2 template has correct migration instructions
# ---------------------------------------------------------------------------

_TEMPLATE_PATH = Path(__file__).parent.parent / "src" / "specsmith" / "templates" / "agents.md.j2"


class TestAgentsTemplate:
    def test_agents_template_no_pip_install(self) -> None:
        """agents.md.j2 must not instruct agents to pip install specsmith (REQ-369)."""
        content = _TEMPLATE_PATH.read_text(encoding="utf-8")
        assert "pip install" not in content, (
            "agents.md.j2 must not contain 'pip install'. specsmith is installed via pipx only."
        )

    def test_agents_template_uses_current_health_check(self) -> None:
        """The agent template must use the focused CLI for migration health (REQ-369)."""
        content = _TEMPLATE_PATH.read_text(encoding="utf-8")
        assert "specsmith doctor" in content
        assert "specsmith migrate" not in content

    def test_agents_template_no_yn_prompt_for_migration(self) -> None:
        """agents.md.j2 must not contain a Y/n prompt for migration (REQ-369)."""
        content = _TEMPLATE_PATH.read_text(encoding="utf-8")
        # The template must not have a "[Y/n]" interactive prompt for migration
        assert "[Y/n]" not in content, (
            "agents.md.j2 must not contain '[Y/n]' prompts — forward migration is auto-accepted."
        )

    def test_agents_template_mentions_downgrade_error(self) -> None:
        """agents.md.j2 must note that backward migration is not supported (REQ-370)."""
        content = _TEMPLATE_PATH.read_text(encoding="utf-8")
        has_note = "not supported" in content or "hard error" in content or "downgrade" in content
        assert has_note, (
            "agents.md.j2 must state that backward migration / downgrade is not supported."
        )


# ---------------------------------------------------------------------------
# TEST-371 / REQ-370: run_upgrade rejects backward migration
# ---------------------------------------------------------------------------


class TestUpgraderDowngrade:
    def test_run_upgrade_rejects_downgrade(self, tmp_path: Path) -> None:
        """run_upgrade with target < project spec_version returns downgrade_error=True (REQ-370)."""
        from specsmith.upgrader import run_upgrade

        # Scaffold project with future version
        _make_scaffold(tmp_path, spec_version="99.99.0")

        result = run_upgrade(tmp_path, target_version="0.1.0")

        assert result.downgrade_error is True, (
            "run_upgrade must set downgrade_error=True when target < project spec_version"
        )
        assert "ERROR" in result.message or "not supported" in result.message, (
            f"run_upgrade downgrade message should explain the error; got: {result.message!r}"
        )

    def test_run_upgrade_no_files_mutated_on_downgrade(self, tmp_path: Path) -> None:
        """run_upgrade must not modify any files when a downgrade is detected (REQ-370)."""
        from specsmith.upgrader import run_upgrade

        _make_scaffold(tmp_path, spec_version="99.99.0")
        scaffold = tmp_path / "scaffold.yml"
        original_mtime = scaffold.stat().st_mtime

        result = run_upgrade(tmp_path, target_version="0.1.0")

        assert scaffold.stat().st_mtime == original_mtime, (
            "scaffold.yml must not be modified when a downgrade is attempted"
        )
        assert result.updated_files == [], (
            f"run_upgrade must not list any updated files on downgrade; got: {result.updated_files}"
        )


# ---------------------------------------------------------------------------
# TEST-371 / REQ-370: run_migration rejects backward migration
# ---------------------------------------------------------------------------


class TestMigrationDowngrade:
    def test_run_migration_rejects_downgrade(self, tmp_path: Path) -> None:
        """run_migration must return an ERROR string when installed < project version (REQ-370)."""
        from specsmith.updater import run_migration

        # Create scaffold with a version higher than installed
        _make_scaffold(tmp_path, spec_version="99.99.0")

        actions = run_migration(tmp_path)

        assert len(actions) == 1, f"Expected exactly one action (error), got: {actions}"
        assert actions[0].startswith("ERROR:"), (
            f"run_migration must return 'ERROR:' string for downgrade; got: {actions[0]!r}"
        )
        assert "not supported" in actions[0] or "Backward" in actions[0], (
            f"run_migration error message should explain backward migration; got: {actions[0]!r}"
        )

    def test_run_migration_forward_succeeds(self, tmp_path: Path) -> None:
        """run_migration with older project version completes without an ERROR (REQ-369)."""
        from specsmith.updater import run_migration

        _make_scaffold(tmp_path, spec_version="0.1.0")
        actions = run_migration(tmp_path)

        assert not any(a.startswith("ERROR:") for a in actions), (
            f"run_migration must not return errors for forward migration; got: {actions}"
        )


# ---------------------------------------------------------------------------
# TEST-371 / REQ-370: upgrade CLI command rejects downgrade
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TEST-369 / REQ-368: govern_bench structure placeholder
# ---------------------------------------------------------------------------


class TestGovernBenchStructure:
    def test_govern_bench_structure(self) -> None:
        """scripts/govern_bench/ should exist with task definitions (REQ-368).

        This is a *planned* feature.  The test is marked xfail until the
        benchmark suite is implemented so the audit does not block CI.
        """
        bench_dir = Path(__file__).parent.parent / "scripts" / "govern_bench"
        task_yamls = (
            list(bench_dir.glob("*.yml")) + list(bench_dir.glob("*.yaml"))
            if bench_dir.exists()
            else []
        )
        if not task_yamls:
            pytest.xfail(
                "scripts/govern_bench/ not yet implemented (REQ-368 is 'planned'). "
                "Create the directory with at least one task YAML to pass this test."
            )
        # If we reach here, the directory exists and has task YAMLs.
        assert task_yamls, "Unreachable — xfail above handles the empty case."
