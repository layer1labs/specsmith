"""Aider integration adapter."""

from __future__ import annotations

from pathlib import Path

from specsmith.config import ProjectConfig
from specsmith.integrations.base import AgentAdapter


class AiderAdapter(AgentAdapter):
    """Generate .aider.conf.yml for Aider."""

    @property
    def name(self) -> str:
        return "aider"

    @property
    def description(self) -> str:
        return "Aider .aider.conf.yml"

    def generate(self, config: ProjectConfig, target: Path) -> list[Path]:
        conf_path = target / ".aider.conf.yml"
        conf_path.write_text(self._render(config), encoding="utf-8")
        return [conf_path]

    def _render(self, config: ProjectConfig) -> str:
        return (
            f"# Aider configuration — {config.name}\n"
            f"# Spec version: {config.spec_version}\n"
            f"# Project type: {config.type_label}\n\n"
            f"read:\n"
            f"  - AGENTS.md\n"
            f"  - LEDGER.md\n"
            f"  - docs/governance/rules.md\n"
        )
