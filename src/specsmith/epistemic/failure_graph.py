# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Failure-Mode Graph (G) — maps stress-test → breakpoint relations.

The Failure-Mode Graph is a directed graph where:
- Nodes are BeliefArtifact IDs
- Edges represent "artifact A's failure mode implies artifact B's confidence
  should be reviewed" (dependency propagation)

The two key operations on G are:
  equilibrium_check() → True when S(G) yields no new failure modes
  logic_knot_detect() → returns detected Logic Knots (irreducible conflicts)

These correspond to the AEE convergence proof: systematic application of S
and R always converges to an Equilibrium Point E where no new failures emerge.

Graph rendering
---------------
The graph can be rendered as:
- text tree (default) — for terminal output
- Mermaid diagram — for embedding in docs/governance/failure-modes.md
"""

from __future__ import annotations

from dataclasses import dataclass, field

from specsmith.epistemic.belief import BeliefArtifact, FailureMode
from specsmith.epistemic.stress_tester import StressTestResult


@dataclass
class GraphNode:
    """A node in the Failure-Mode Graph."""

    artifact_id: str
    failure_count: int = 0
    critical_count: int = 0
    logic_knot_partner: str = ""  # ID of conflicting artifact if knot exists
    children: list[str] = field(default_factory=list)  # dependent artifact IDs


class FailureModeGraph:
    """Directed graph of failure-mode relations between BeliefArtifacts.

    Construction::

        graph = FailureModeGraph()
        graph.build(artifacts, stress_result)

    After building, the graph supports:
    - ``equilibrium_check()`` — True if no unresolved critical failures exist
    - ``logic_knot_detect()`` — returns all detected knots
    - ``render_text()``  — text tree representation
    - ``render_mermaid()`` — Mermaid diagram string
    """

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[tuple[str, str, str]] = []  # (from_id, to_id, label)
        self._logic_knots: list[tuple[str, str, str]] = []

    def build(
        self,
        artifacts: list[BeliefArtifact],
        stress_result: StressTestResult,
    ) -> None:
        """Build the graph from artifact data and stress-test results."""
        self._nodes = {}
        self._edges = []
        self._logic_knots = list(stress_result.logic_knots)

        # Create a node for every artifact
        for artifact in artifacts:
            node = GraphNode(artifact_id=artifact.artifact_id)
            node.failure_count = len(artifact.failure_modes)
            node.critical_count = len(artifact.critical_failures)
            self._nodes[artifact.artifact_id] = node

        # Build edges from inferential links (dependency propagation)
        for artifact in artifacts:
            for link in artifact.inferential_links:
                if link in self._nodes:
                    self._edges.append(
                        (
                            artifact.artifact_id,
                            link,
                            "depends-on",
                        )
                    )
                    self._nodes[link].children.append(artifact.artifact_id)

        # Mark logic knot partners
        for id1, id2, _ in self._logic_knots:
            if id1 in self._nodes:
                self._nodes[id1].logic_knot_partner = id2
            if id2 in self._nodes:
                self._nodes[id2].logic_knot_partner = id1

    def equilibrium_check(self) -> bool:
        """Return True if the graph has reached epistemic equilibrium.

        Equilibrium (E) is the AEE state where S(G) yields no new failures:
        no unresolved critical failures exist and no Logic Knots remain.
        """
        has_critical = any(node.critical_count > 0 for node in self._nodes.values())
        return not has_critical and len(self._logic_knots) == 0

    def logic_knot_detect(self) -> list[tuple[str, str, str]]:
        """Return all detected Logic Knots.

        Each knot is a tuple (artifact_id_1, artifact_id_2, reason).
        """
        return list(self._logic_knots)

    def get_node(self, artifact_id: str) -> GraphNode | None:
        return self._nodes.get(artifact_id)

    def nodes_with_failures(self) -> list[GraphNode]:
        """Return nodes that have at least one failure mode."""
        return [n for n in self._nodes.values() if n.failure_count > 0]

    def nodes_with_critical_failures(self) -> list[GraphNode]:
        """Return nodes with at least one critical failure mode."""
        return [n for n in self._nodes.values() if n.critical_count > 0]

    def render_text(
        self,
        all_failure_modes: list[FailureMode] | None = None,
    ) -> str:
        """Render graph as a text tree for terminal output."""
        lines: list[str] = []
        eq = self.equilibrium_check()
        knots = self.logic_knot_detect()

        lines.append("Failure-Mode Graph")
        lines.append("=" * 50)
        lines.append(
            f"Equilibrium: {'✓ YES' if eq else '✗ NO'} | "
            f"Nodes: {len(self._nodes)} | "
            f"Logic Knots: {len(knots)}"
        )
        lines.append("")

        if knots:
            lines.append("⚠ Logic Knots (irreducible conflicts):")
            for id1, id2, reason in knots:
                lines.append(f"  ✗ {id1} ↔ {id2}")
                lines.append(f"    {reason}")
            lines.append("")

        failure_by_artifact: dict[str, list[FailureMode]] = {}
        if all_failure_modes:
            for fm in all_failure_modes:
                failure_by_artifact.setdefault(fm.artifact_id, []).append(fm)

        # Show only artifacts with failures
        affected = [n for n in self._nodes.values() if n.failure_count > 0]
        if not affected:
            lines.append("✓ No failure modes detected.")
        else:
            lines.append("Affected belief artifacts:")
            for node in sorted(affected, key=lambda n: -n.critical_count):
                crit = f" [{node.critical_count} CRITICAL]" if node.critical_count else ""
                lines.append(f"  {node.artifact_id}{crit}")
                for fm in failure_by_artifact.get(node.artifact_id, []):
                    sev = fm.severity.value.upper()
                    resolved = " [resolved]" if fm.resolved else ""
                    lines.append(f"    [{sev}]{resolved} {fm.challenge}")
                    lines.append(f"      → {fm.breakpoint[:100]}")
                    if fm.recovery_hint:
                        lines.append(f"      ↻ {fm.recovery_hint[:100]}")

        return "\n".join(lines)

    def render_mermaid(self) -> str:
        """Render graph as a Mermaid diagram string."""
        lines = ["graph TD"]

        for node in self._nodes.values():
            label = node.artifact_id
            if node.critical_count > 0:
                shape = f'["{label}\\n⚠CRITICAL"]'
                lines.append(f"  {_safe_id(node.artifact_id)}{shape}")
                lines.append(f"  style {_safe_id(node.artifact_id)} fill:#ff4444,color:#fff")
            elif node.failure_count > 0:
                shape = f'["{label}\\n{node.failure_count} failures"]'
                lines.append(f"  {_safe_id(node.artifact_id)}{shape}")
                lines.append(f"  style {_safe_id(node.artifact_id)} fill:#ff9900,color:#000")
            else:
                lines.append(f'  {_safe_id(node.artifact_id)}["{label}"]')

        for from_id, to_id, label in self._edges:
            lines.append(f"  {_safe_id(from_id)} -->|{label}| {_safe_id(to_id)}")

        for id1, id2, _ in self._logic_knots:
            lines.append(f"  {_safe_id(id1)} <-->|⚠ Logic Knot| {_safe_id(id2)}")

        return "\n".join(lines)

    def summary_stats(self) -> dict[str, int]:
        """Return summary statistics for the graph."""
        return {
            "total_nodes": len(self._nodes),
            "nodes_with_failures": len(self.nodes_with_failures()),
            "nodes_with_critical": len(self.nodes_with_critical_failures()),
            "logic_knots": len(self._logic_knots),
            "total_edges": len(self._edges),
        }


def _safe_id(artifact_id: str) -> str:
    """Convert artifact ID to a Mermaid-safe node identifier."""
    return artifact_id.replace("-", "_").replace(".", "_")
