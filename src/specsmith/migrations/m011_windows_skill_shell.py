# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""M011 -- replace Bash-only session cleanup in generated agent skills."""

from __future__ import annotations

import os
from pathlib import Path

from specsmith.migrations import Migration, MigrationResult

_LEGACY_COMMAND = "specsmith kill-session 2>/dev/null || true"
_COMMAND_PREFIX = "specsmith kill-session"
_PREVIOUS_SAFE_COMMAND = f"{_COMMAND_PREFIX}{' ' * 24}# idempotent; safe when no processes exist"
_SAFE_COMMAND = "specsmith kill-session  # idempotent; safe when no processes exist"


class WindowsSkillShellMigration(Migration):
    """Keep generated agent instructions usable in PowerShell and POSIX shells."""

    version = 11
    title = "Replace Bash-only generated skill session cleanup"
    description = (
        "Replaces Bash stderr redirection in generated agent skill session-start "
        "instructions with a shell-neutral idempotent specsmith command."
    )

    def run(self, root: Path, *, dry_run: bool = False) -> MigrationResult:
        """Rewrite only materialized skill files inside the project root."""
        result = MigrationResult(version=self.version, title=self.title, dry_run=dry_run)
        safe_root = os.path.realpath(str(root))
        safe_skills_dir = os.path.realpath(str(Path(safe_root) / ".agents" / "skills"))
        skills_dir = Path(safe_skills_dir)
        changed: list[str] = []

        if not skills_dir.is_dir():
            result.message = "No materialized agent skills found -- nothing to migrate."
            return result

        for skill_path in sorted(skills_dir.rglob("SKILL.md")):
            safe_skill_path = os.path.realpath(str(skill_path))
            if not safe_skill_path.startswith(safe_skills_dir + os.sep):
                continue

            path = Path(safe_skill_path)
            content = path.read_text(encoding="utf-8")
            if _LEGACY_COMMAND not in content:
                continue

            if not dry_run:
                path.write_text(
                    content.replace(_LEGACY_COMMAND, _SAFE_COMMAND).replace(
                        _PREVIOUS_SAFE_COMMAND,
                        _SAFE_COMMAND,
                    ),
                    encoding="utf-8",
                )
            changed.append(str(path.relative_to(safe_root)).replace("\\", "/"))

        result.files_modified.extend(changed)
        result.message = (
            f"{'Would update' if dry_run else 'Updated'} {len(changed)} generated skill file(s)."
        )
        return result
