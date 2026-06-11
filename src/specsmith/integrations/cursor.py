# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Cursor integration adapter."""

from __future__ import annotations

from pathlib import Path

from specsmith.config import ProjectConfig
from specsmith.integrations.base import AgentAdapter


class CursorAdapter(AgentAdapter):
    """Generate .cursor/rules/ for Cursor IDE."""

    @property
    def name(self) -> str:
        return "cursor"

    @property
    def description(self) -> str:
        return "Cursor .cursor/rules/ files"

    def generate(self, config: ProjectConfig, target: Path) -> list[Path]:
        rules_dir = target / ".cursor" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)

        created: list[Path] = []

        # Main governance rule
        governance_path = rules_dir / "governance.mdc"
        governance_path.write_text(self._render_governance(config), encoding="utf-8")
        created.append(governance_path)

        return created

    def _render_governance(self, config: ProjectConfig) -> str:
        return f"""---
description: Project governance rules from Agentic AI Workflow Spec v{config.spec_version}
globs: **/*
alwaysApply: true
---

# Governance

This project follows the Agentic AI Development Workflow Specification.
Project type: {config.type_label} (Section {config.section_ref}).

## Required reading
1. `AGENTS.md` — governance hub
2. `LEDGER.md` — session state
3. `docs/governance/RULES.md` — hard rules

## Workflow
All changes: propose → check → execute → verify → record.

## Constraints
- Keep AGENTS.md under 200 lines
- All commands must have timeouts
- Use exec shims for external commands
- Record every session in LEDGER.md
"""
