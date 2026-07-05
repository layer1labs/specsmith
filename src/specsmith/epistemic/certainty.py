# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Certainty Engine — confidence scoring and propagation (CERTUS-inspired).

The CertaintyEngine assigns numeric uncertainty scores to BeliefArtifacts
and propagates those scores through chains of inferentially linked artifacts.
This is inspired by the CERTUS Damage Confidence Index (DCI) methodology
from the VERITAS platform by AionSystem.

Scoring model
-------------
Each BeliefArtifact receives a composite certainty score C ∈ [0, 1]:

    C = base_score × coverage_weight × freshness_weight

Where:
  base_score     = ConfidenceLevel.score (UNKNOWN=0.0, LOW=0.25,
                                          MEDIUM=0.55, HIGH=0.85)
  coverage_weight = fraction of propositions that have test coverage
                    (0.0 if no tests, 1.0 if fully covered)
  freshness_weight = penalty for artifacts with unresolved failure modes
                    (full weight if no failures, reduced by severity)

Propagation
-----------
Confidence propagates through inferential links using the weakest-link rule:
if artifact A depends on artifact B (A → B), then A's effective certainty
cannot exceed B's certainty. This models the epistemic reality that a claim
built on uncertain foundations is itself uncertain.

Equilibrium threshold: 0.7 (configurable)
Artifacts below this threshold in accepted/stress-tested status trigger a
warning in the epistemic-audit report.

References
----------
CERTUS/DCI methodology: https://github.com/AionSystem/VERITAS
AEE Convergence Axiom (5): Systematic S+R application converges to E.

"""

from __future__ import annotations

from dataclasses import dataclass, field

from specsmith.epistemic.belief import BeliefArtifact, FailureSeverity


@dataclass
class ArtifactCertainty:
    """Certainty score for a single BeliefArtifact."""

    artifact_id: str
    base_score: float
    coverage_weight: float
    freshness_weight: float
    propagated_score: float  # After applying weakest-link propagation
    above_threshold: bool
    component: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def composite_score(self) -> float:
        return self.base_score * self.coverage_weight * self.freshness_weight

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
    """Report produced by CertaintyEngine.run()."""

    scores: list[ArtifactCertainty] = field(default_factory=list)
    overall_score: float = 0.0
    threshold: float = 0.7
    below_threshold: list[str] = field(default_factory=list)  # artifact IDs

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
            f"Threshold:      {self.threshold:.2f}",
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

    Usage::

        engine = CertaintyEngine(threshold=0.7)
        report = engine.run(artifacts, covered_reqs={"REQ-CLI-001", ...})

    ``covered_reqs`` is the set of requirement IDs that have test coverage.
    If not provided, coverage_weight defaults to 0.5 for all artifacts.
    """

    def __init__(self, threshold: float = 0.7) -> None:
        self.threshold = threshold

    def run(
        self,
        artifacts: list[BeliefArtifact],
        covered_reqs: set[str] | None = None,
    ) -> CertaintyReport:
        """Compute certainty scores and propagate through dependency links."""
        if covered_reqs is None:
            covered_reqs = set()

        # Step 1: compute base scores
        scores: dict[str, ArtifactCertainty] = {}
        for artifact in artifacts:
            ac = self._compute_base(artifact, covered_reqs)
            scores[artifact.artifact_id] = ac

        # Step 2: propagate via weakest-link rule
        artifact_map = {a.artifact_id: a for a in artifacts}
        self._propagate(scores, artifact_map)

        # Step 3: build report
        score_list = list(scores.values())
        below = [s.artifact_id for s in score_list if not s.above_threshold]

        overall = (
            sum(s.propagated_score for s in score_list) / len(score_list) if score_list else 0.0
        )

        return CertaintyReport(
            scores=score_list,
            overall_score=overall,
            threshold=self.threshold,
            below_threshold=below,
        )

    def _compute_base(self, artifact: BeliefArtifact, covered_reqs: set[str]) -> ArtifactCertainty:
        """Compute base certainty before propagation."""
        base = artifact.confidence.score
        notes: list[str] = []

        # Coverage weight: how many propositions have test coverage
        if not artifact.propositions:
            coverage = 0.0
            notes.append("No propositions → coverage weight 0.0")
        elif artifact.artifact_id in covered_reqs:
            coverage = 1.0
        else:
            coverage = 0.4  # Partial: no direct test, but propositions exist
            notes.append(f"No test coverage found → coverage weight {coverage}")

        # Freshness weight: penalty for unresolved failures
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
            # LOW failures: no penalty

        composite = base * coverage * freshness
        above = composite >= self.threshold

        return ArtifactCertainty(
            artifact_id=artifact.artifact_id,
            base_score=base,
            coverage_weight=coverage,
            freshness_weight=freshness,
            propagated_score=composite,
            above_threshold=above,
            component=artifact.component,
            notes=notes,
        )

    def _propagate(
        self,
        scores: dict[str, ArtifactCertainty],
        artifact_map: dict[str, BeliefArtifact],
    ) -> None:
        """Apply weakest-link propagation through inferential links.

        If A depends on B (A → B in inferential_links), then:
          A.propagated_score = min(A.propagated_score, B.propagated_score)

        Multiple passes until stable (handles transitive chains).
        """
        changed = True
        max_passes = 20  # Safety cap — convergence is guaranteed for DAGs
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
                            ac.notes.append(
                                f"Propagated from {link}: score reduced to {upstream:.2f}",
                            )
                            changed = True
