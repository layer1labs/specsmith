# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Regression tests for the Windows-safe generated-skill migration."""

from pathlib import Path

from specsmith.migrations.m011_windows_skill_shell import (
    _LEGACY_COMMAND,
    _SAFE_COMMAND,
    WindowsSkillShellMigration,
)
from specsmith.migrations.m012_normalize_skill_shell import (
    _PREVIOUS_SAFE_COMMAND,
    NormalizeSkillShellMigration,
)


def test_migration_rewrites_materialized_skill_command(tmp_path: Path) -> None:
    skill_path = tmp_path / ".agents" / "skills" / "warp-integration" / "SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text(f"# Warp\n{_LEGACY_COMMAND}\n", encoding="utf-8")

    result = WindowsSkillShellMigration().run(tmp_path)

    assert result.success
    assert result.files_modified == [".agents/skills/warp-integration/SKILL.md"]
    content = skill_path.read_text(encoding="utf-8")
    assert _LEGACY_COMMAND not in content
    assert _SAFE_COMMAND in content


def test_migration_dry_run_and_repeat_are_safe(tmp_path: Path) -> None:
    skill_path = tmp_path / ".agents" / "skills" / "cursor-integration" / "SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text(_LEGACY_COMMAND, encoding="utf-8")
    migration = WindowsSkillShellMigration()

    dry_run = migration.run(tmp_path, dry_run=True)

    assert dry_run.files_modified == [".agents/skills/cursor-integration/SKILL.md"]
    assert skill_path.read_text(encoding="utf-8") == _LEGACY_COMMAND

    migration.run(tmp_path)
    repeated = migration.run(tmp_path)

    assert repeated.success
    assert repeated.files_modified == []


def test_normalization_migration_rewrites_prior_safe_command(tmp_path: Path) -> None:
    skill_path = tmp_path / ".agents" / "skills" / "aider-integration" / "SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text(_PREVIOUS_SAFE_COMMAND, encoding="utf-8")

    result = NormalizeSkillShellMigration().run(tmp_path)

    assert result.files_modified == [".agents/skills/aider-integration/SKILL.md"]
    assert skill_path.read_text(encoding="utf-8") == _SAFE_COMMAND
