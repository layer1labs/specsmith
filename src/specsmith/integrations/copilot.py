# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""GitHub Copilot integration adapter."""

from __future__ import annotations

from pathlib import Path

from specsmith.config import ProjectConfig
from specsmith.integrations.base import AgentAdapter


class CopilotAdapter(AgentAdapter):
    """Generate .github/copilot-instructions.md for GitHub Copilot."""

    @property
    def name(self) -> str:
        return "copilot"

    @property
    def description(self) -> str:
        return "GitHub Copilot .github/copilot-instructions.md"

    def generate(self, config: ProjectConfig, target: Path) -> list[Path]:
        github_dir = target / ".github"
        github_dir.mkdir(parents=True, exist_ok=True)

        instructions_path = github_dir / "copilot-instructions.md"
        content = self._render(config)
        instructions_path.write_text(content, encoding="utf-8")
        return [instructions_path]

    def _render(self, config: ProjectConfig) -> str:
        return f"""# Copilot Instructions

This project follows the Agentic AI Development Workflow Specification (v{config.spec_version}).

## Context
- Project type: {config.type_label} (Spec Section {config.section_ref})
- Governance hub: `AGENTS.md`
- Session ledger: `LEDGER.md`
- Modular governance: `docs/governance/`

## Rules
1. Read `AGENTS.md` before making changes
2. All changes require a proposal in `LEDGER.md`
3. Follow propose → check → execute → verify → record workflow
4. All commands must have timeouts (use `scripts/exec.cmd` or `scripts/exec.sh`)
5. Keep `AGENTS.md` under 200 lines — delegate to `docs/governance/`
6. Record every session outcome in `LEDGER.md`

## Health checks
Run `specsmith audit` to check project health.
Run `specsmith validate` to verify governance consistency.
"""
