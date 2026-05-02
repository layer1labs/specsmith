# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Shared agent runtime primitives (REQ-145).

Hosts low-level enums and dataclasses that span :mod:`specsmith.agent.runner`,
:mod:`specsmith.serve`, :mod:`specsmith.agent.profiles`, and
:mod:`specsmith.agent.fallback` without forcing them to import each other.

The historical ``cli.py`` referenced ``ModelTier`` from this module before
it existed in the source tree (the file was lost in an earlier refactor),
which produced an ``ImportError`` the moment ``specsmith run`` was
invoked. Restoring the symbol here is the prerequisite for the bridge
``ready`` event handshake to land before the VS Code extension's 20 s
startup timeout fires.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class ModelTier(str, enum.Enum):
    """Capability tier for an LLM call.

    Ordered cheapest → most capable so that a fallback chain can iterate
    in declaration order without external metadata.
    """

    FAST = "fast"
    BALANCED = "balanced"
    POWERFUL = "powerful"

    @classmethod
    def parse(cls, value: str | "ModelTier" | None, default: "ModelTier" = None) -> "ModelTier":
        """Tolerant parser used by CLI option handlers."""
        if value is None or value == "":
            return default or cls.BALANCED
        if isinstance(value, cls):
            return value
        try:
            return cls(str(value).strip().lower())
        except ValueError:
            return default or cls.BALANCED


@dataclass
class AgentState:
    """Mutable per-session metrics surfaced via ``specsmith serve``'s
    ``GET /api/status`` endpoint and the VS Code TokenMeter chip.

    Field names mirror what :class:`specsmith.serve._AgentThread` reads off
    ``runner._state``; do not rename without updating that consumer.
    """

    provider_name: str = ""
    model_name: str = ""
    profile_id: str = ""
    session_tokens: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    total_cost_usd: float = 0.0
    tool_calls_made: int = 0
    elapsed_minutes: float = 0.0
    by_profile: dict[str, dict[str, Any]] = field(default_factory=dict)

    def credit(
        self,
        *,
        profile_id: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        cost_usd: float = 0.0,
        tool_calls: int = 0,
    ) -> None:
        """Aggregate one turn's metrics into the running totals."""
        self.tokens_in += int(tokens_in)
        self.tokens_out += int(tokens_out)
        self.session_tokens = self.tokens_in + self.tokens_out
        self.total_cost_usd += float(cost_usd)
        self.tool_calls_made += int(tool_calls)
        bucket = self.by_profile.setdefault(
            profile_id or "(default)",
            {"tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0, "tool_calls": 0, "turns": 0},
        )
        bucket["tokens_in"] += int(tokens_in)
        bucket["tokens_out"] += int(tokens_out)
        bucket["cost_usd"] = round(bucket["cost_usd"] + float(cost_usd), 6)
        bucket["tool_calls"] += int(tool_calls)
        bucket["turns"] += 1


__all__ = ["AgentState", "ModelTier"]
