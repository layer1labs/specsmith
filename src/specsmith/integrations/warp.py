# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Warp / Oz skill integration adapter."""

from __future__ import annotations

from pathlib import Path

from specsmith.config import ProjectConfig
from specsmith.integrations.base import AgentAdapter


class WarpAdapter(AgentAdapter):
    """Generate a Warp skill file for the project."""

    @property
    def name(self) -> str:
        return "warp"

    @property
    def description(self) -> str:
        return "Warp / Oz skill file (.warp/skills/)"

    def generate(self, config: ProjectConfig, target: Path) -> list[Path]:
        skill_dir = target / ".warp" / "skills"
        skill_dir.mkdir(parents=True, exist_ok=True)

        skill_path = skill_dir / "SKILL.md"
        content = self._render_skill(config)
        skill_path.write_text(content, encoding="utf-8")
        return [skill_path]

    def _render_skill(self, config: ProjectConfig) -> str:
        from specsmith.tools import get_tools

        tools = get_tools(config)
        tool_cmds = []
        if tools.lint:
            tool_cmds.append(tools.lint[0])
        if tools.test:
            tool_cmds.append(tools.test[0])
        if tools.typecheck:
            tool_cmds.append(tools.typecheck[0])
        verify_line = ", ".join(tool_cmds) if tool_cmds else "project-specific tools"

        return f"""# {config.name} — Governed Project Skill

## Context
This project follows the Agentic AI Development Workflow Specification (v{config.spec_version}).
Project type: {config.type_label} (Section {config.section_ref}).
Description: {config.description or "See README.md"}.

## Session Start
1. Read `AGENTS.md` — the governance hub
2. Read `LEDGER.md` — check last session state and open TODOs
3. Read `docs/governance/rules.md` — hard rules and stop conditions

## Workflow
All changes follow: **propose → check → execute → verify → record**.
- Every code change requires a proposal in the ledger
- Every proposal needs verification before marking complete
- Never skip the ledger entry

## Key Files
- `AGENTS.md` — governance hub (read first)
- `LEDGER.md` — session ledger (read second)
- `docs/governance/` — modular governance docs (load on demand)
- `docs/REQUIREMENTS.md` — formal requirements
- `docs/TEST_SPEC.md` — test specifications
- `docs/architecture.md` — system architecture

## Commands
- `specsmith audit` — run health checks
- `specsmith validate` — check governance consistency
- `specsmith compress` — archive old ledger entries

## Verification
Before marking any task complete, run: {verify_line}

## Rules
- Proposals before changes (no exceptions)
- Verify before recording completion
- Use execution shims (`scripts/exec.cmd` / `scripts/exec.sh`) for external commands
- Keep AGENTS.md under 200 lines
- Record every session in the ledger
"""
