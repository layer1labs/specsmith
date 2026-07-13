# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""M012 -- normalize the first Windows-safe generated-skill command."""

from __future__ import annotations

import os
from pathlib import Path

from specsmith.migrations import Migration, MigrationResult

_COMMAND_PREFIX = "specsmith kill-session"
_PREVIOUS_SAFE_COMMAND = f"{_COMMAND_PREFIX}{' ' * 24}# idempotent; safe when no processes exist"
_SAFE_COMMAND = "specsmith kill-session  # idempotent; safe when no processes exist"


class NormalizeSkillShellMigration(Migration):
    """Normalize a command emitted by M011 without changing its behavior."""

    version = 12
    title = "Normalize generated skill session cleanup"
    description = "Normalizes the shell-neutral session cleanup command emitted by M011."

    def run(self, root: Path, *, dry_run: bool = False) -> MigrationResult:
        """Rewrite only the prior M011 command inside materialized skill files."""
        result = MigrationResult(version=self.version, title=self.title, dry_run=dry_run)
        safe_root = os.path.realpath(str(root))
        safe_skills_dir = os.path.realpath(str(Path(safe_root) / ".agents" / "skills"))
        skills_dir = Path(safe_skills_dir)

        if not skills_dir.is_dir():
            result.message = "No materialized agent skills found -- nothing to normalize."
            return result

        for skill_path in sorted(skills_dir.rglob("SKILL.md")):
            safe_skill_path = os.path.realpath(str(skill_path))
            if not safe_skill_path.startswith(safe_skills_dir + os.sep):
                continue

            path = Path(safe_skill_path)
            content = path.read_text(encoding="utf-8")
            if _PREVIOUS_SAFE_COMMAND not in content:
                continue

            if not dry_run:
                path.write_text(
                    content.replace(_PREVIOUS_SAFE_COMMAND, _SAFE_COMMAND),
                    encoding="utf-8",
                )
            result.files_modified.append(str(path.relative_to(safe_root)).replace("\\", "/"))

        result.message = (
            f"{'Would normalize' if dry_run else 'Normalized'} "
            f"{len(result.files_modified)} generated skill file(s)."
        )
        return result
