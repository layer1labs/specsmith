"""Gemini CLI integration adapter."""

from __future__ import annotations

from pathlib import Path

from specsmith.config import ProjectConfig
from specsmith.integrations.base import AgentAdapter


class GeminiAdapter(AgentAdapter):
    """Generate GEMINI.md for Google Gemini CLI."""

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def description(self) -> str:
        return "Gemini CLI GEMINI.md"

    def generate(self, config: ProjectConfig, target: Path) -> list[Path]:
        gemini_path = target / "GEMINI.md"
        gemini_path.write_text(self._render(config), encoding="utf-8")
        return [gemini_path]

    def _render(self, config: ProjectConfig) -> str:
        return (
            f"# GEMINI.md\n\n"
            f"This project follows the Agentic AI Development Workflow "
            f"Specification (v{config.spec_version}).\n\n"
            f"## Project\n"
            f"- Type: {config.type_label} (Section {config.section_ref})\n"
            f"- Governance hub: `AGENTS.md`\n"
            f"- Session ledger: `LEDGER.md`\n\n"
            f"## Workflow\n"
            f"All changes follow: propose → check → execute → verify → record.\n\n"
            f"## Required reading\n"
            f"1. `AGENTS.md` — governance hub\n"
            f"2. `LEDGER.md` — session state and open TODOs\n"
            f"3. `docs/governance/rules.md` — hard rules and stop conditions\n\n"
            f"## Constraints\n"
            f"- Keep AGENTS.md under 200 lines\n"
            f"- All agent-invoked commands must have timeouts\n"
            f"- Use `scripts/exec.ps1` or `scripts/exec.sh` for bounded execution\n"
            f"- Record every session in LEDGER.md\n"
        )
