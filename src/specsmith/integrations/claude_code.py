# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Claude Code integration adapter."""

from __future__ import annotations

from pathlib import Path

from specsmith.config import ProjectConfig
from specsmith.integrations.base import AgentAdapter


class ClaudeCodeAdapter(AgentAdapter):
    """Generate CLAUDE.md for Claude Code / Claude CLI."""

    @property
    def name(self) -> str:
        return "claude-code"

    @property
    def description(self) -> str:
        return "Claude Code CLAUDE.md"

    def generate(self, config: ProjectConfig, target: Path) -> list[Path]:
        claude_path = target / "CLAUDE.md"
        content = self._render(config)
        claude_path.write_text(content, encoding="utf-8")
        return [claude_path]

    def _render(self, config: ProjectConfig) -> str:
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

        return f"""# CLAUDE.md

This project follows the Agentic AI Development Workflow Specification (v{config.spec_version}).
Project type: {config.type_label}. Description: {config.description or "See README.md"}.

## Start here
1. Read `AGENTS.md` for project identity, governance hub, and file registry
2. Read `LEDGER.md` for session state and open TODOs
3. Read `docs/governance/rules.md` for hard rules

## Workflow
All changes follow: propose → check → execute → verify → record.
Never modify code without a proposal in the ledger first.

## Project type
{config.type_label} (Spec Section {config.section_ref})

## Key constraints
- AGENTS.md is the governance hub — keep it under 200 lines
- Modular governance docs live in `docs/governance/`
- All agent-invoked commands must have timeouts
- Use `scripts/exec.cmd` or `scripts/exec.sh` for bounded execution
- Record every session in LEDGER.md

## Verification
Before marking any task complete, run: {verify_line}

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
"""
