# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Agent skill integration adapter.

Generates a generic ``SKILL.md`` file under ``.agents/skills/`` for any
terminal-native AI agent that supports the SKILL.md convention.

This adapter previously shipped under the name ``warp`` and wrote to
``.warp/skills/SKILL.md``. The legacy name is still resolved as an alias
in :mod:`specsmith.integrations` so existing ``scaffold.yml`` configs
continue to work, but the canonical adapter name is ``agent-skill`` and
the canonical output path is ``.agents/skills/SKILL.md``.
"""

from __future__ import annotations

from pathlib import Path

from specsmith.config import ProjectConfig
from specsmith.integrations.base import AgentAdapter


class AgentSkillAdapter(AgentAdapter):
    """Generate a generic agent skill file (.agents/skills/SKILL.md)."""

    @property
    def name(self) -> str:
        return "agent-skill"

    @property
    def description(self) -> str:
        return "Agent skill file (.agents/skills/SKILL.md)"

    def generate(self, config: ProjectConfig, target: Path) -> list[Path]:
        skill_dir = target / ".agents" / "skills"
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
3. Read `docs/governance/RULES.md` — hard rules and stop conditions

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
- `docs/TESTS.md` — test specifications
- `docs/ARCHITECTURE.md` — system architecture

## Session Start
Before any work, run: `specsmith update --check --project-dir .`
If outdated, run: `specsmith update --yes`

## Commands
When user says `commit`: run `specsmith commit --project-dir .`
When user says `push`: run `specsmith push --project-dir .`
When user says `sync`: run `specsmith sync --project-dir .`
When user says `pr`: run `specsmith pr --project-dir .`
When user says `audit`: run `specsmith audit --project-dir .`
When user says `session-end`: run `specsmith session-end --project-dir .`

## Verification
Before marking any task complete, run: {verify_line}

## Credit Tracking
After completing tasks, record token usage:
```
specsmith credits record --model <model> --provider <provider> \\
  --tokens-in <N> --tokens-out <N> --task "<desc>"
```
Check budget: `specsmith credits summary`

## Rules
- Proposals before changes (no exceptions)
- Verify before recording completion
- Use execution shims (`scripts/exec.cmd` / `scripts/exec.sh`) for external commands
- Keep AGENTS.md under 200 lines
- Record every session in the ledger
- Record credit usage at session end
"""
