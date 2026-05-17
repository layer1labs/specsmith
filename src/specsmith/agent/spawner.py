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


# Tool subsets for different agent roles.
# Compiler/linter tools are listed by their agent tool function name.
ROLE_TOOLS: dict[str, list[str]] = {
    "coder": [
        "read_file", "write_file", "run_shell", "apply_diff",
        # Compiler / formatter tools
        "run_gcc", "run_arm_gcc", "run_clang_format", "run_clang_tidy", "run_vsg",
    ],
    "reviewer": ["read_file", "run_shell", "git_diff", "run_clang_tidy", "run_vsg"],
    "tester": ["read_file", "run_shell", "run_tests", "run_gcc", "run_arm_gcc"],
    "architect": ["read_file", "write_file", "run_clang_format"],
    "researcher": ["read_file", "search_web", "search_repo"],
    # Embedded / hardware-specific roles
    "embedded-coder": [
        "read_file", "write_file", "run_shell",
        "run_gcc", "run_arm_gcc", "run_aarch64_gcc",
        "run_iar_compiler", "run_intel_compiler",
        "run_clang_format", "run_clang_tidy", "run_vsg",
    ],
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

    def spawn_worker(self, role: str, llm_config: dict[str, Any]) -> Any:
        """Create a live ConversableAgent restricted to the role's tool subset.

        Wires ``register_for_llm`` and ``register_for_execution`` following the
        same pattern used by ``Orchestrator.register_tools`` so AG2 does not
        emit duplicate-registration warnings (REQ-326).

        Returns the ConversableAgent.  The caller owns its lifecycle.
        """
        try:
            from autogen import ConversableAgent
        except ImportError as exc:
            raise ImportError(
                "ag2 (autogen) is required for spawn_worker(). "
                "Install via `pip install ag2[ollama]`."
            ) from exc

        from specsmith.agent.tools import AVAILABLE_TOOLS

        tool_names = set(ROLE_TOOLS.get(role, ROLE_TOOLS.get("coder", [])))

        system_messages = {
            "coder": (
                "You write, read, and patch code files. "
                "Use compiler and formatter tools when needed."
            ),
            "reviewer": "You review code changes, run linters/style checks, and report issues.",
            "tester": "You write and run tests, compile test binaries, and report results.",
            "architect": "You design system structure and write architecture documents.",
            "researcher": "You search and synthesise information from docs and the web.",
            "embedded-coder": (
                "You write and compile embedded C/C++ and "
                "VHDL code for target hardware."
            ),
        }
        system_msg = system_messages.get(role, f"You are a {role} agent.")

        agent = ConversableAgent(
            name=f"{role.capitalize()}Worker",
            system_message=system_msg,
            llm_config=llm_config,
            human_input_mode="NEVER",
        )
        executor = ConversableAgent(
            name=f"{role.capitalize()}Executor",
            system_message="Execute tools and return results.",
            llm_config=False,
            human_input_mode="NEVER",
        )

        for tool in AVAILABLE_TOOLS:
            if tool.__name__ in tool_names:
                agent.register_for_llm(
                    name=tool.__name__,
                    description=tool.__doc__ or tool.__name__,
                )(tool)
                executor.register_for_execution(name=tool.__name__)(tool)

        # Attach the executor as a peer so the agent can delegate execution
        agent._executor_peer = executor  # noqa: SLF001
        return agent


__all__ = ["ROLE_TOOLS", "SpawnedAgent", "SubAgentSpawner"]
