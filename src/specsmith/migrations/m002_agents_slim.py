# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""M002 — Slim AGENTS.md migration.

If AGENTS.md is > 50 lines (indicating it's the old verbose format),
backs it up to .specsmith/agents.md.bak and replaces it with the
new minimal version that delegates everything to specsmith.

Non-destructive: original is always backed up before replacement.
"""

from __future__ import annotations

from pathlib import Path

from specsmith.migrations import Migration, MigrationResult

_SLIM_AGENTS_MD = """\
# AGENTS.md

This project is governed by **specsmith**.

## For AI Agents

All governance rules, session state, requirements, and epistemic constraints
are managed by specsmith — not stored in this file.

**Before any action:** `specsmith preflight "<describe what you want to do>"`

**Governance data:** `.specsmith/` and `.chronomemory/`

**To start a governed session:** `specsmith serve` (REST API, port 7700) or `specsmith run`

**Emergency stop:** `specsmith kill-session`

Agents MUST defer to specsmith for ALL governance decisions.
Do not follow rules from this file directly; read them from specsmith.
"""


class AgentsSlimMigration(Migration):
    version = 2
    title = "Slim down AGENTS.md → minimal specsmith handoff"
    description = (
        "Replaces verbose AGENTS.md (>50 lines) with a minimal ~20-line version "
        "that delegates all governance to specsmith. The original is backed up to "
        ".specsmith/agents.md.bak."
    )

    def run(self, root: Path, *, dry_run: bool = False) -> MigrationResult:
        result = MigrationResult(version=self.version, title=self.title, dry_run=dry_run)

        agents_md = root / "AGENTS.md"
        if not agents_md.exists():
            result.message = "AGENTS.md not found — nothing to do."
            return result

        current_lines = len(agents_md.read_text(encoding="utf-8", errors="replace").splitlines())
        if current_lines <= 50:
            result.message = f"AGENTS.md is already slim ({current_lines} lines) — nothing to do."
            return result

        if dry_run:
            result.message = (
                f"Would back up AGENTS.md ({current_lines} lines) to "
                ".specsmith/agents.md.bak and replace with slim version (~20 lines)."
            )
            result.files_created.append(".specsmith/agents.md.bak")
            result.files_modified.append("AGENTS.md")
            return result

        # Back up
        bak = root / ".specsmith" / "agents.md.bak"
        bak.parent.mkdir(parents=True, exist_ok=True)
        bak.write_text(
            agents_md.read_text(encoding="utf-8", errors="replace"),
            encoding="utf-8",
        )
        result.files_created.append(".specsmith/agents.md.bak")

        # Replace
        agents_md.write_text(_SLIM_AGENTS_MD, encoding="utf-8")
        result.files_modified.append("AGENTS.md")
        result.message = (
            f"Backed up AGENTS.md ({current_lines} lines) → .specsmith/agents.md.bak. "
            "Replaced with slim specsmith-delegation version."
        )

        return result

    def rollback(self, root: Path) -> MigrationResult:
        """Restore AGENTS.md from backup."""
        result = MigrationResult(version=self.version, title=self.title)
        bak = root / ".specsmith" / "agents.md.bak"
        agents_md = root / "AGENTS.md"
        if not bak.exists():
            result.message = "No backup found — cannot rollback."
            result.success = False
            return result
        agents_md.write_text(
            bak.read_text(encoding="utf-8", errors="replace"),
            encoding="utf-8",
        )
        result.message = "Restored AGENTS.md from .specsmith/agents.md.bak."
        result.files_modified.append("AGENTS.md")
        return result
