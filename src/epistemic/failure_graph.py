# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Failure-Mode Graph (G) — maps stress-test → breakpoint relations.

Part of the standalone ``epistemic`` library. Zero external dependencies.
    from epistemic import FailureModeGraph
"""

from __future__ import annotations

from dataclasses import dataclass, field

from epistemic.belief import BeliefArtifact, FailureMode
from epistemic.stress_tester import StressTestResult


@dataclass
class GraphNode:
    artifact_id: str
    failure_count: int = 0
    critical_count: int = 0
    logic_knot_partner: str = ""
    children: list[str] = field(default_factory=list)


class FailureModeGraph:
    """Directed graph of failure-mode relations between BeliefArtifacts.

    from epistemic import FailureModeGraph, StressTester, BeliefArtifact

    artifacts = [...]
    tester = StressTester()
    result = tester.run(artifacts)

    graph = FailureModeGraph()
    graph.build(artifacts, result)
    print(f"Equilibrium: {graph.equilibrium_check()}")
    print(graph.render_text())
    """

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[tuple[str, str, str]] = []
        self._logic_knots: list[tuple[str, str, str]] = []

    def build(self, artifacts: list[BeliefArtifact], stress_result: StressTestResult) -> None:
        self._nodes = {}
        self._edges = []
        self._logic_knots = list(stress_result.logic_knots)

        for artifact in artifacts:
            node = GraphNode(artifact_id=artifact.artifact_id)
            node.failure_count = len(artifact.failure_modes)
            node.critical_count = len(artifact.critical_failures)
            self._nodes[artifact.artifact_id] = node

        for artifact in artifacts:
            for link in artifact.inferential_links:
                if link in self._nodes:
                    self._edges.append((artifact.artifact_id, link, "depends-on"))
                    self._nodes[link].children.append(artifact.artifact_id)

        for id1, id2, _ in self._logic_knots:
            if id1 in self._nodes:
                self._nodes[id1].logic_knot_partner = id2
            if id2 in self._nodes:
                self._nodes[id2].logic_knot_partner = id1

    def equilibrium_check(self) -> bool:
        """True when S(G) yields no new failures (AEE Convergence)."""
        has_critical = any(n.critical_count > 0 for n in self._nodes.values())
        return not has_critical and len(self._logic_knots) == 0

    def logic_knot_detect(self) -> list[tuple[str, str, str]]:
        return list(self._logic_knots)

    def nodes_with_failures(self) -> list[GraphNode]:
        return [n for n in self._nodes.values() if n.failure_count > 0]

    def nodes_with_critical_failures(self) -> list[GraphNode]:
        return [n for n in self._nodes.values() if n.critical_count > 0]

    def render_text(self, all_failure_modes: list[FailureMode] | None = None) -> str:
        lines: list[str] = []
        eq = self.equilibrium_check()
        knots = self.logic_knot_detect()

        lines.append("Failure-Mode Graph")
        lines.append("=" * 50)
        lines.append(
            f"Equilibrium: {'✓ YES' if eq else '✗ NO'} | "
            f"Nodes: {len(self._nodes)} | Logic Knots: {len(knots)}"
        )

        if knots:
            lines.append("\n⚠ Logic Knots:")
            for id1, id2, reason in knots:
                lines.append(f"  ✗ {id1} ↔ {id2}: {reason}")

        failure_by_artifact: dict[str, list[FailureMode]] = {}
        if all_failure_modes:
            for fm in all_failure_modes:
                failure_by_artifact.setdefault(fm.artifact_id, []).append(fm)

        affected = [n for n in self._nodes.values() if n.failure_count > 0]
        if not affected:
            lines.append("\n✓ No failure modes detected.")
        else:
            lines.append("\nAffected belief artifacts:")
            for node in sorted(affected, key=lambda n: -n.critical_count):
                crit = f" [{node.critical_count} CRITICAL]" if node.critical_count else ""
                lines.append(f"  {node.artifact_id}{crit}")
                for fm in failure_by_artifact.get(node.artifact_id, []):
                    sev = fm.severity.value.upper()
                    lines.append(f"    [{sev}] {fm.challenge}")
                    lines.append(f"      → {fm.breakpoint[:100]}")
                    if fm.recovery_hint:
                        lines.append(f"      ↻ {fm.recovery_hint[:100]}")

        return "\n".join(lines)

    def render_mermaid(self) -> str:
        lines = ["graph TD"]
        for node in self._nodes.values():
            label = node.artifact_id
            if node.critical_count > 0:
                lines.append(f'  {_sid(node.artifact_id)}["{label}\\n⚠CRITICAL"]')
                lines.append(f"  style {_sid(node.artifact_id)} fill:#ff4444,color:#fff")
            elif node.failure_count > 0:
                lines.append(
                    f'  {_sid(node.artifact_id)}["{label}\\n{node.failure_count} failures"]'
                )  # noqa: E501
                lines.append(f"  style {_sid(node.artifact_id)} fill:#ff9900,color:#000")
            else:
                lines.append(f'  {_sid(node.artifact_id)}["{label}"]')
        for from_id, to_id, label in self._edges:
            lines.append(f"  {_sid(from_id)} -->|{label}| {_sid(to_id)}")
        for id1, id2, _ in self._logic_knots:
            lines.append(f"  {_sid(id1)} <-->|⚠ Logic Knot| {_sid(id2)}")
        return "\n".join(lines)

    def summary_stats(self) -> dict[str, int]:
        return {
            "total_nodes": len(self._nodes),
            "nodes_with_failures": len(self.nodes_with_failures()),
            "nodes_with_critical": len(self.nodes_with_critical_failures()),
            "logic_knots": len(self._logic_knots),
            "total_edges": len(self._edges),
        }


def _sid(artifact_id: str) -> str:
    return artifact_id.replace("-", "_").replace(".", "_")


__all__ = ["FailureModeGraph", "GraphNode"]
