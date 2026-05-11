# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Team definitions for multi-agent coordination.

ARCHITECTURE.md §13 Phase 2: predefined agent team compositions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TeamMember:
    """A role slot within a team."""

    role: str
    required: bool = True
    tools_override: list[str] | None = None


@dataclass
class TeamDefinition:
    """A named team of agent roles that work together."""

    id: str
    name: str
    description: str
    members: list[TeamMember] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "members": [{"role": m.role, "required": m.required} for m in self.members],
        }


# Pre-defined teams
PAIR_REVIEW = TeamDefinition(
    id="pair-review",
    name="Pair Review",
    description="Coder + Reviewer pair for code changes with built-in review",
    members=[
        TeamMember(role="coder"),
        TeamMember(role="reviewer"),
    ],
)

FULL_STACK = TeamDefinition(
    id="full-stack",
    name="Full Stack",
    description="Architect + Coder + Tester trio for complete feature development",
    members=[
        TeamMember(role="architect"),
        TeamMember(role="coder"),
        TeamMember(role="tester"),
    ],
)

IP_ANALYSIS = TeamDefinition(
    id="ip-analysis",
    name="IP Analysis",
    description="IP Analyst + Researcher + Strategist for patent work",
    members=[
        TeamMember(role="ip-analyst"),
        TeamMember(role="researcher"),
        TeamMember(role="strategist"),
    ],
)

SPEC_DRAFT = TeamDefinition(
    id="spec-draft",
    name="Specification Drafting",
    description="Architect + Drafter + Reviewer for specification writing",
    members=[
        TeamMember(role="architect"),
        TeamMember(role="drafter"),
        TeamMember(role="reviewer"),
    ],
)

BUILTIN_TEAMS: dict[str, TeamDefinition] = {
    "pair-review": PAIR_REVIEW,
    "full-stack": FULL_STACK,
    "ip-analysis": IP_ANALYSIS,
    "spec-draft": SPEC_DRAFT,
}


def get_team(team_id: str) -> TeamDefinition | None:
    """Get a built-in team by ID."""
    return BUILTIN_TEAMS.get(team_id)


def list_teams() -> list[TeamDefinition]:
    """List all available teams."""
    return list(BUILTIN_TEAMS.values())


__all__ = ["BUILTIN_TEAMS", "TeamDefinition", "TeamMember", "get_team", "list_teams"]
