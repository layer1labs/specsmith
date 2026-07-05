# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Certainty Engine — confidence scoring and propagation (CERTUS-inspired).

Part of the standalone ``epistemic`` library. Zero external dependencies.
    from epistemic import CertaintyEngine, CertaintyReport
"""

from __future__ import annotations

from dataclasses import dataclass, field

from epistemic.belief import BeliefArtifact, FailureSeverity


@dataclass
class ArtifactCertainty:
    artifact_id: str
    base_score: float
    coverage_weight: float
    freshness_weight: float
    propagated_score: float
    above_threshold: bool
    component: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        s = self.propagated_score
        if s >= 0.75:
            return "HIGH"
        if s >= 0.45:
            return "MEDIUM"
        if s > 0.0:
            return "LOW"
        return "UNKNOWN"


@dataclass
class CertaintyReport:
    """Produced by CertaintyEngine.run()."""

    scores: list[ArtifactCertainty] = field(default_factory=list)
    overall_score: float = 0.0
    threshold: float = 0.7
    below_threshold: list[str] = field(default_factory=list)

    @property
    def component_averages(self) -> dict[str, float]:
        by_comp: dict[str, list[float]] = {}
        for s in self.scores:
            by_comp.setdefault(s.component, []).append(s.propagated_score)
        return {c: sum(v) / len(v) for c, v in by_comp.items() if v}

    def format_text(self) -> str:
        lines = [
            "Certainty Report",
            "=" * 50,
            f"Overall score:  {self.overall_score:.2f} "
            f"({'above' if self.overall_score >= self.threshold else 'below'} "
            f"threshold {self.threshold:.2f})",
            f"Artifacts:      {len(self.scores)}",
            f"Below threshold: {len(self.below_threshold)}",
            "",
        ]
        comp_avgs = self.component_averages
        if comp_avgs:
            lines.append("By component:")
            for comp, avg in sorted(comp_avgs.items(), key=lambda x: -x[1]):
                icon = "✓" if avg >= self.threshold else "✗"
                lines.append(f"  {icon} {comp:12s}  {avg:.2f}")
            lines.append("")

        low = [s for s in self.scores if not s.above_threshold]
        if not low:
            lines.append("✓ All artifacts meet the certainty threshold.")
        else:
            lines.append("Artifacts below threshold:")
            for s in sorted(low, key=lambda x: x.propagated_score):
                lines.append(
                    f"  ✗ {s.artifact_id:25s}  score={s.propagated_score:.2f}  [{s.label}]",
                )
                for note in s.notes[:2]:
                    lines.append(f"     {note}")
        return "\n".join(lines)


class CertaintyEngine:
    """Compute and propagate certainty scores through a belief artifact graph.

    Inspired by CERTUS/DCI methodology from VERITAS (AionSystem).
    Zero external dependencies.

        from epistemic import CertaintyEngine

        engine = CertaintyEngine(threshold=0.7)
        report = engine.run(artifacts, covered_reqs={"HYP-001", "HYP-002"})
        print(report.format_text())

    covered_reqs: set of artifact IDs that have experimental/test coverage.
    If not provided, a partial weight (0.4) is applied to all artifacts.
    """

    def __init__(self, threshold: float = 0.7) -> None:
        self.threshold = threshold

    def run(
        self,
        artifacts: list[BeliefArtifact],
        covered_reqs: set[str] | None = None,
    ) -> CertaintyReport:
        if covered_reqs is None:
            covered_reqs = set()

        scores: dict[str, ArtifactCertainty] = {}
        for artifact in artifacts:
            ac = self._compute_base(artifact, covered_reqs)
            scores[artifact.artifact_id] = ac

        artifact_map = {a.artifact_id: a for a in artifacts}
        self._propagate(scores, artifact_map)

        score_list = list(scores.values())
        below = [s.artifact_id for s in score_list if not s.above_threshold]
        if score_list:
            overall = sum(s.propagated_score for s in score_list) / len(score_list)
        else:
            overall = 0.0

        return CertaintyReport(
            scores=score_list,
            overall_score=overall,
            threshold=self.threshold,
            below_threshold=below,
        )

    def _compute_base(self, artifact: BeliefArtifact, covered_reqs: set[str]) -> ArtifactCertainty:
        base = artifact.confidence.score
        notes: list[str] = []

        if not artifact.propositions:
            coverage = 0.0
            notes.append("No propositions → coverage weight 0.0")
        elif artifact.artifact_id in covered_reqs:
            coverage = 1.0
        else:
            coverage = 0.4
            notes.append(f"No test/experiment coverage → coverage weight {coverage}")

        freshness = 1.0
        for fm in artifact.unresolved_failures:
            if fm.severity == FailureSeverity.CRITICAL:
                freshness *= 0.2
                notes.append(f"CRITICAL failure: {fm.challenge[:60]}")
            elif fm.severity == FailureSeverity.HIGH:
                freshness *= 0.6
                notes.append(f"HIGH failure: {fm.challenge[:60]}")
            elif fm.severity == FailureSeverity.MEDIUM:
                freshness *= 0.85

        composite = base * coverage * freshness
        return ArtifactCertainty(
            artifact_id=artifact.artifact_id,
            base_score=base,
            coverage_weight=coverage,
            freshness_weight=freshness,
            propagated_score=composite,
            above_threshold=composite >= self.threshold,
            component=artifact.component,
            notes=notes,
        )

    def _propagate(
        self,
        scores: dict[str, ArtifactCertainty],
        artifact_map: dict[str, BeliefArtifact],
    ) -> None:
        """Weakest-link propagation: A.score = min(A.score, B.score) for A→B."""
        changed = True
        max_passes = 20
        pass_count = 0
        while changed and pass_count < max_passes:
            changed = False
            pass_count += 1
            for artifact_id, artifact in artifact_map.items():
                if artifact_id not in scores:
                    continue
                ac = scores[artifact_id]
                for link in artifact.inferential_links:
                    if link in scores:
                        upstream = scores[link].propagated_score
                        if upstream < ac.propagated_score:
                            ac.propagated_score = upstream
                            ac.above_threshold = upstream >= self.threshold
                            ac.notes.append(f"Propagated from {link}: reduced to {upstream:.2f}")
                            changed = True


__all__ = ["ArtifactCertainty", "CertaintyEngine", "CertaintyReport"]
