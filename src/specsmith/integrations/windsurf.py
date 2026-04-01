"""Windsurf integration adapter."""

from __future__ import annotations

from pathlib import Path

from specsmith.config import ProjectConfig
from specsmith.integrations.base import AgentAdapter


class WindsurfAdapter(AgentAdapter):
    """Generate .windsurfrules for Windsurf IDE."""

    @property
    def name(self) -> str:
        return "windsurf"

    @property
    def description(self) -> str:
        return "Windsurf .windsurfrules"

    def generate(self, config: ProjectConfig, target: Path) -> list[Path]:
        rules_path = target / ".windsurfrules"
        rules_path.write_text(self._render(config), encoding="utf-8")
        return [rules_path]

    def _render(self, config: ProjectConfig) -> str:
        return (
            f"# Windsurf Rules — {config.name}\n\n"
            f"This project follows the Agentic AI Development Workflow "
            f"Specification (v{config.spec_version}).\n"
            f"Project type: {config.type_label} (Section {config.section_ref}).\n\n"
            f"## Required reading\n"
            f"1. Read `AGENTS.md` — governance hub\n"
            f"2. Read `LEDGER.md` — session state\n"
            f"3. Read `docs/governance/rules.md` — hard rules\n\n"
            f"## Workflow\n"
            f"All changes: propose → check → execute → verify → record.\n\n"
            f"## Constraints\n"
            f"- Keep AGENTS.md under 200 lines\n"
            f"- All commands must have timeouts\n"
            f"- Use exec shims for external commands\n"
            f"- Record every session in LEDGER.md\n"
        )
