# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Task DAG — directed acyclic graph of agent work items.

REQ-322: TaskDAGBuilder validates acyclicity before any dispatch.
REQ-323: TaskNode carries id, title, role, depends_on, status, context_in,
         context_out, and result.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

from specsmith.agent.dispatch._status import TaskStatus

if TYPE_CHECKING:
    from specsmith.agent.dispatch.result import DispatchResult


# ---------------------------------------------------------------------------
# Enums — re-exported from _status for backwards compatibility
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Core dataclass
# ---------------------------------------------------------------------------


@dataclass
class TaskNode:
    """A single unit of dispatched work in the DAG.

    REQ-323 fields:
      id          — unique within the DAG
      title       — human-readable description
      role        — maps to a key in spawner.ROLE_TOOLS
      depends_on  — list of node ids that must be COMPLETED first
      status      — TaskStatus lifecycle state
      context_in  — ESDB ChronoRecord IDs to inject as context
      context_out — ESDB ChronoRecord ID written on completion
      result      — DispatchResult once the node finishes
    """

    id: str
    title: str
    role: str
    depends_on: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    context_in: list[str] = field(default_factory=list)
    context_out: str | None = None
    result: DispatchResult | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "role": self.role,
            "depends_on": list(self.depends_on),
            "status": self.status.value,
            "context_in": list(self.context_in),
            "context_out": self.context_out,
            "result": self.result.to_dict() if self.result is not None else None,
        }


# ---------------------------------------------------------------------------
# DAG container
# ---------------------------------------------------------------------------


class DAGValidationError(ValueError):
    """Raised when a cycle is detected or the graph is malformed."""


class TaskDAG:
    """Directed acyclic graph of TaskNodes.

    Provides:
      - add_node()              — register a node
      - runnable_nodes()        — nodes whose dependencies are all COMPLETED
      - blocked_by_failure(id)  — propagate FAILED → BLOCKED transitively
      - topological_sort()      — Kahn's algorithm; raises on cycle
      - all_terminal()          — True when no node is PENDING or RUNNING
    """

    def __init__(self, dag_id: str) -> None:
        self.dag_id = dag_id
        self._nodes: dict[str, TaskNode] = {}

    # -- Mutation ----------------------------------------------------------

    def add_node(self, node: TaskNode) -> None:
        if node.id in self._nodes:
            raise DAGValidationError(f"Duplicate node id: {node.id!r}")
        self._nodes[node.id] = node

    # -- Queries -----------------------------------------------------------

    def nodes(self) -> list[TaskNode]:
        return list(self._nodes.values())

    def get(self, node_id: str) -> TaskNode | None:
        return self._nodes.get(node_id)

    def runnable_nodes(self) -> list[TaskNode]:
        """Return PENDING nodes whose every dependency is COMPLETED."""
        ready = []
        for node in self._nodes.values():
            if node.status != TaskStatus.PENDING:
                continue
            if all(
                self._nodes.get(dep, _MISSING_NODE).status == TaskStatus.COMPLETED
                for dep in node.depends_on
            ):
                ready.append(node)
        return ready

    def blocked_by_failure(self, failed_id: str) -> list[str]:
        """Mark all transitive dependents of *failed_id* as BLOCKED.

        Returns list of node IDs that were newly blocked (REQ-325).
        """
        newly_blocked: list[str] = []
        to_visit = {failed_id}
        while to_visit:
            current = to_visit.pop()
            for node in self._nodes.values():
                if current in node.depends_on and node.status in (
                    TaskStatus.PENDING,
                    TaskStatus.RUNNING,
                ):
                    node.status = TaskStatus.BLOCKED
                    newly_blocked.append(node.id)
                    to_visit.add(node.id)
        return newly_blocked

    def all_terminal(self) -> bool:
        """True when every node is COMPLETED, FAILED, or BLOCKED."""
        terminal = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.BLOCKED}
        return all(n.status in terminal for n in self._nodes.values())

    def topological_sort(self) -> list[TaskNode]:
        """Kahn's algorithm — raises DAGValidationError on cycle."""
        in_degree: dict[str, int] = dict.fromkeys(self._nodes, 0)
        for node in self._nodes.values():
            for dep in node.depends_on:
                if dep not in self._nodes:
                    raise DAGValidationError(f"Node {node.id!r} depends on unknown node {dep!r}")
                in_degree[node.id] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        result: list[TaskNode] = []
        while queue:
            nid = queue.pop(0)
            result.append(self._nodes[nid])
            for candidate in self._nodes.values():
                if nid in candidate.depends_on:
                    in_degree[candidate.id] -= 1
                    if in_degree[candidate.id] == 0:
                        queue.append(candidate.id)

        if len(result) != len(self._nodes):
            raise DAGValidationError("Cycle detected in task DAG — execution aborted.")
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "dag_id": self.dag_id,
            "nodes": [n.to_dict() for n in self._nodes.values()],
        }


# Sentinel for missing dependency nodes during runnable check
class _MissingNode:
    status = TaskStatus.PENDING  # unknown dep → not yet completed


_MISSING_NODE = _MissingNode()


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

_NODE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


class TaskDAGBuilder:
    """Convert a planner output string or structured dict into a TaskDAG.

    The planner is expected to emit a JSON list of node dicts.  If the input
    is a plain string, the builder extracts the first JSON array it finds.
    If parsing fails or a cycle is detected, ``DAGValidationError`` is raised
    and the orchestrator falls back to the flat GroupChat path.

    Node dict schema::

        {
            "id":         "unique-slug",
            "title":      "Human description",
            "role":       "coder",            # must be in ROLE_TOOLS
            "depends_on": ["node-id", ...]    # optional
        }
    """

    SUPPORTED_ROLES = {"coder", "reviewer", "tester", "architect", "researcher"}

    @classmethod
    def build(
        cls,
        task: str,
        dag_id: str | None = None,
        *,
        planner_output: str | list[dict[str, Any]] | None = None,
    ) -> TaskDAG:
        """Build and validate a TaskDAG.

        When *planner_output* is provided it is used directly (dict list or
        JSON string containing a list).  Otherwise a minimal single-node DAG
        is generated from *task* so dispatch still works without a live LLM.
        """
        import uuid

        if dag_id is None:
            dag_id = uuid.uuid4().hex[:12]

        dag = TaskDAG(dag_id=dag_id)

        raw: list[dict[str, Any]] = []
        if planner_output is not None:
            raw = cls._parse_nodes(planner_output)
        else:
            # Fallback: single node wrapping the whole task
            raw = [{"id": "task-main", "title": task, "role": "coder", "depends_on": []}]

        for item in raw:
            node_id = str(item.get("id", "")).strip()
            if not node_id:
                raise DAGValidationError("Node is missing required 'id' field.")
            if not _NODE_ID_RE.match(node_id):
                raise DAGValidationError(f"Node id {node_id!r} contains invalid characters.")
            role = str(item.get("role", "coder")).strip()
            dag.add_node(
                TaskNode(
                    id=node_id,
                    title=str(item.get("title", node_id)),
                    role=role,
                    depends_on=[str(d) for d in item.get("depends_on", [])],
                ),
            )

        # Validate: topological sort will raise on cycle
        dag.topological_sort()
        return dag

    @classmethod
    def _parse_nodes(cls, source: str | list[dict[str, Any]]) -> list[dict[str, Any]]:
        if isinstance(source, list):
            return source
        # Extract first JSON array from string
        text = str(source)
        start = text.find("[")
        if start == -1:
            raise DAGValidationError("Planner output contains no JSON array.")
        # Find balanced closing bracket
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    try:
                        return cast("list[dict[str, Any]]", json.loads(text[start : i + 1]))
                    except json.JSONDecodeError as exc:
                        raise DAGValidationError(
                            f"Malformed JSON in planner output: {exc}",
                        ) from exc
        raise DAGValidationError("Planner output JSON array is not closed.")


__all__ = [
    "DAGValidationError",
    "TaskDAG",
    "TaskDAGBuilder",
    "TaskNode",
    "TaskStatus",  # re-exported from _status
]
