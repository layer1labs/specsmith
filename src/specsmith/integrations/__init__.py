"""Agent integration adapters for specsmith."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from specsmith.integrations.base import AgentAdapter

ADAPTER_REGISTRY: dict[str, type[AgentAdapter]] = {}


def _load_adapters() -> None:
    """Populate the adapter registry."""
    from specsmith.integrations.aider import AiderAdapter
    from specsmith.integrations.claude_code import ClaudeCodeAdapter
    from specsmith.integrations.copilot import CopilotAdapter
    from specsmith.integrations.cursor import CursorAdapter
    from specsmith.integrations.gemini import GeminiAdapter
    from specsmith.integrations.warp import WarpAdapter
    from specsmith.integrations.windsurf import WindsurfAdapter

    for cls in (
        WarpAdapter,
        ClaudeCodeAdapter,
        CursorAdapter,
        CopilotAdapter,
        GeminiAdapter,
        WindsurfAdapter,
        AiderAdapter,
    ):
        ADAPTER_REGISTRY[cls().name] = cls


def get_adapter(name: str) -> AgentAdapter:
    """Get an adapter instance by name."""
    if not ADAPTER_REGISTRY:
        _load_adapters()
    cls = ADAPTER_REGISTRY.get(name)
    if cls is None:
        available = ", ".join(sorted(ADAPTER_REGISTRY.keys()))
        msg = f"Unknown integration '{name}'. Available: {available}"
        raise ValueError(msg)
    return cls()


def list_adapters() -> list[str]:
    """List available adapter names."""
    if not ADAPTER_REGISTRY:
        _load_adapters()
    return sorted(ADAPTER_REGISTRY.keys())
