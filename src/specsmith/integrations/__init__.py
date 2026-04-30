# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Agent integration adapters for specsmith."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from specsmith.integrations.base import AgentAdapter

ADAPTER_REGISTRY: dict[str, type[AgentAdapter]] = {}

# Legacy adapter names that have been superseded. Mapped to the current
# canonical name. Lookups for legacy keys still succeed (backward compat for
# existing scaffold.yml files) but only the canonical names are returned by
# ``list_adapters()``.
LEGACY_ALIASES: dict[str, str] = {
    # Pre-0.5.0 the agent-skill adapter shipped under the name ``warp`` and
    # wrote to ``.warp/skills/SKILL.md``. New scaffolds use ``agent-skill``
    # and ``.agents/skills/SKILL.md``.
    "warp": "agent-skill",
}


def _load_adapters() -> None:
    """Populate the adapter registry."""
    from specsmith.integrations.agent_skill import AgentSkillAdapter
    from specsmith.integrations.aider import AiderAdapter
    from specsmith.integrations.claude_code import ClaudeCodeAdapter
    from specsmith.integrations.copilot import CopilotAdapter
    from specsmith.integrations.cursor import CursorAdapter
    from specsmith.integrations.gemini import GeminiAdapter
    from specsmith.integrations.windsurf import WindsurfAdapter

    for cls in (
        AgentSkillAdapter,
        ClaudeCodeAdapter,
        CursorAdapter,
        CopilotAdapter,
        GeminiAdapter,
        WindsurfAdapter,
        AiderAdapter,
    ):
        ADAPTER_REGISTRY[cls().name] = cls


def get_adapter(name: str) -> AgentAdapter:
    """Get an adapter instance by name.

    Legacy names listed in :data:`LEGACY_ALIASES` are silently rewritten to
    their canonical equivalent, so older ``scaffold.yml`` integration lists
    keep working without manual migration.
    """
    if not ADAPTER_REGISTRY:
        _load_adapters()
    resolved = LEGACY_ALIASES.get(name, name)
    cls = ADAPTER_REGISTRY.get(resolved)
    if cls is None:
        available = ", ".join(sorted(ADAPTER_REGISTRY.keys()))
        msg = f"Unknown integration '{name}'. Available: {available}"
        raise ValueError(msg)
    return cls()


def list_adapters() -> list[str]:
    """List available adapter names (canonical only; legacy aliases hidden)."""
    if not ADAPTER_REGISTRY:
        _load_adapters()
    return sorted(ADAPTER_REGISTRY.keys())
