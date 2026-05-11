# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Sub-agent spawner — spawn isolated agent workers with tool subsets.

ARCHITECTURE.md §13 Phase 2: Multi-Agent Layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SpawnedAgent:
    """Metadata for a spawned sub-agent."""

    id: str
    role: str
    tools: list[str]
    status: str = "idle"  # idle, running, completed, failed
    result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "tools": self.tools,
            "status": self.status,
            "result": self.result,
        }


# Tool subsets for different agent roles
ROLE_TOOLS: dict[str, list[str]] = {
    "coder": ["read_file", "write_file", "run_shell", "apply_diff"],
    "reviewer": ["read_file", "run_shell", "git_diff"],
    "tester": ["read_file", "run_shell", "run_tests"],
    "architect": ["read_file", "write_file"],
    "researcher": ["read_file", "search_web", "search_repo"],
}


class SubAgentSpawner:
    """Spawn and manage isolated agent workers.

    Each spawned agent gets a restricted tool subset based on its role,
    preventing accidental cross-domain actions (e.g., a reviewer can't
    write files).
    """

    def __init__(self) -> None:
        self._agents: dict[str, SpawnedAgent] = {}
        self._counter = 0

    def spawn(self, role: str, tools: list[str] | None = None) -> SpawnedAgent:
        """Spawn a new sub-agent with the given role and tool set."""
        self._counter += 1
        agent_id = f"agent-{role}-{self._counter:03d}"
        effective_tools = tools or ROLE_TOOLS.get(role, [])
        agent = SpawnedAgent(id=agent_id, role=role, tools=effective_tools)
        self._agents[agent_id] = agent
        return agent

    def get(self, agent_id: str) -> SpawnedAgent | None:
        """Get a spawned agent by ID."""
        return self._agents.get(agent_id)

    def list_active(self) -> list[SpawnedAgent]:
        """List all agents that are not completed/failed."""
        return [a for a in self._agents.values() if a.status in ("idle", "running")]

    def list_all(self) -> list[SpawnedAgent]:
        """List all spawned agents."""
        return list(self._agents.values())

    def complete(self, agent_id: str, result: dict[str, Any]) -> None:
        """Mark an agent as completed with its result."""
        agent = self._agents.get(agent_id)
        if agent:
            agent.status = "completed"
            agent.result = result

    def fail(self, agent_id: str, error: str) -> None:
        """Mark an agent as failed."""
        agent = self._agents.get(agent_id)
        if agent:
            agent.status = "failed"
            agent.result = {"error": error}


__all__ = ["ROLE_TOOLS", "SpawnedAgent", "SubAgentSpawner"]
