# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Dispatch result types — structured outcomes of node and DAG execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from specsmith.agent.dispatch._status import TaskStatus


@dataclass
class DispatchResult:
    """Structured outcome of a single TaskNode execution."""

    node_id: str
    role: str
    status: TaskStatus
    summary: str = ""
    files_changed: list[str] = field(default_factory=list)
    esdb_record_id: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "role": self.role,
            "status": self.status.value,
            "summary": self.summary,
            "files_changed": list(self.files_changed),
            "esdb_record_id": self.esdb_record_id,
            "error": self.error,
        }


@dataclass
class DispatchSummary:
    """Aggregate outcome of a full DAG dispatch run."""

    dag_id: str
    completed: list[DispatchResult] = field(default_factory=list)
    failed: list[DispatchResult] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)  # node IDs
    equilibrium: bool = False
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "dag_id": self.dag_id,
            "completed": [r.to_dict() for r in self.completed],
            "failed": [r.to_dict() for r in self.failed],
            "blocked": list(self.blocked),
            "equilibrium": self.equilibrium,
            "confidence": round(self.confidence, 3),
        }

    @classmethod
    def from_task_result(cls, dag_id: str) -> DispatchSummary:
        """Create an empty summary for a given DAG run."""
        return cls(dag_id=dag_id)


__all__ = ["DispatchResult", "DispatchSummary"]
