# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""AEESession — high-level facade for Applied Epistemic Engineering.

This is the primary entry point for projects that want to use AEE practices
outside of specsmith's CLI governance workflow. Zero dependencies beyond Python's
stdlib.

    pip install specsmith
    from epistemic import AEESession

Designed for use in:
- Research projects (glossa-lab, cpac, etc.) — hypotheses as BeliefArtifacts
- Compliance pipelines — regulatory claims as BeliefArtifacts
- AI alignment workflows — model assumptions as BeliefArtifacts
- Any Python project that needs structured epistemic rigor

Quick start — glossa-lab decipherment research::

    from epistemic import AEESession, ConfidenceLevel, BeliefStatus

    session = AEESession(project_name="glossa-lab")

    # Register hypotheses as belief artifacts
    session.add_belief(
        artifact_id="HYP-IND-001",
        propositions=["The Indus script uses logosyllabic encoding"],
        epistemic_boundary=["Corpus: Mahadevan 2977 inscriptions, 1977 edition"],
        domain="linguistics",
    )
    session.add_belief(
        artifact_id="HYP-IND-002",
        propositions=["Indus sign frequency follows Zipf's law"],
        epistemic_boundary=["Corpus: same as HYP-IND-001"],
        inferential_links=["HYP-IND-001"],
        domain="linguistics",
    )

    # Add experimental evidence
    session.add_evidence("HYP-IND-001", "Rao et al. 2009 — conditional entropy study")

    # Run the AEE pipeline
    result = session.run()
    print(result.summary())

    # Seal the epistemic state to a tamper-evident trace
    session.seal("stress-test", "Indus hypothesis stress-test complete")
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from epistemic.belief import (
    BeliefArtifact,
    BeliefStatus,
    ConfidenceLevel,
    beliefs_from_dicts,
    parse_requirements_as_beliefs,
)
from epistemic.certainty import CertaintyEngine, CertaintyReport
from epistemic.failure_graph import FailureModeGraph
from epistemic.recovery import RecoveryOperator, RecoveryProposal
from epistemic.stress_tester import StressTester, StressTestResult


@dataclass
class AEEResult:
    """Combined result from a full AEE pipeline run."""

    artifacts: list[BeliefArtifact]
    stress_result: StressTestResult
    certainty_report: CertaintyReport
    proposals: list[RecoveryProposal]
    graph: FailureModeGraph

    def summary(self) -> str:
        lines = [
            "AEE Session Report",
            "=" * 60,
            f"Artifacts:        {len(self.artifacts)}",
            f"Equilibrium:      {'✓ YES' if self.stress_result.equilibrium else '✗ NO'}",
            f"Failure modes:    {self.stress_result.total_failures}",
            f"Critical:         {self.stress_result.critical_count}",
            f"Logic knots:      {len(self.stress_result.logic_knots)}",
            f"Overall certainty:{self.certainty_report.overall_score:.2f} "
            f"(threshold {self.certainty_report.threshold:.2f})",
            f"Below threshold:  {len(self.certainty_report.below_threshold)}",
            f"Recovery proposals:{len(self.proposals)}",
            "",
        ]
        if self.stress_result.logic_knots:
            lines.append("⚠ Logic Knots detected:")
            for id1, id2, reason in self.stress_result.logic_knots:
                lines.append(f"  {id1} ↔ {id2}: {reason[:80]}")
            lines.append("")
        if self.proposals:
            lines.append("Top recovery proposals:")
            for p in self.proposals[:5]:
                lines.append(f"  [{p.strategy.value}] {p.artifact_id}: {p.description[:70]}")
        return "\n".join(lines)

    def is_healthy(self) -> bool:
        """True when the belief system has reached epistemic equilibrium."""
        return (
            self.stress_result.equilibrium
            and self.certainty_report.overall_score >= self.certainty_report.threshold
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "equilibrium": self.stress_result.equilibrium,
            "artifacts_count": len(self.artifacts),
            "failure_modes": self.stress_result.total_failures,
            "critical_count": self.stress_result.critical_count,
            "logic_knots": len(self.stress_result.logic_knots),
            "overall_certainty": self.certainty_report.overall_score,
            "threshold": self.certainty_report.threshold,
            "below_threshold": self.certainty_report.below_threshold,
            "proposals_count": len(self.proposals),
        }


class AEESession:
    """High-level facade for Applied Epistemic Engineering.

    The primary entry point for non-specsmith projects. Bundles all AEE
    machinery into a simple 3-step pattern::

        session = AEESession(project_name="my-project")
        session.add_belief(...)
        result = session.run()
        print(result.summary())

    Persistence
    -----------
    Pass ``state_file`` to save/restore belief state as JSON::

        session = AEESession("my-project", state_file=Path("beliefs.json"))
        session.load()     # load from file
        session.add_belief(...)
        session.run()
        session.save()     # persist updated state

    Trace vault
    -----------
    Pass ``trace_dir`` to enable cryptographic decision sealing::

        session = AEESession("my-project", trace_dir=Path(".epistemic"))
        session.seal("milestone", "Phase 1 complete")
    """

    def __init__(
        self,
        project_name: str,
        threshold: float = 0.7,
        state_file: Path | None = None,
        trace_dir: Path | None = None,
    ) -> None:
        self.project_name = project_name
        self.threshold = threshold
        self._state_file = state_file
        self._trace_dir = trace_dir
        self._artifacts: list[BeliefArtifact] = []
        self._covered: set[str] = set()
        self._vault: object = None  # Lazy-init TraceVault if trace_dir given

        if trace_dir is not None:
            try:
                from epistemic.trace import TraceVault

                self._vault = TraceVault(trace_dir)
            except ImportError:
                pass

    # ------------------------------------------------------------------
    # Belief management
    # ------------------------------------------------------------------

    def add_belief(
        self,
        artifact_id: str,
        propositions: list[str],
        *,
        epistemic_boundary: list[str] | None = None,
        inferential_links: list[str] | None = None,
        confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN,
        status: BeliefStatus = BeliefStatus.DRAFT,
        domain: str = "",
        priority: str = "",
        component: str = "",
        source_text: str = "",
    ) -> BeliefArtifact:
        """Add or replace a BeliefArtifact. Returns the artifact."""
        # Clear existing failure modes if replacing
        existing = {a.artifact_id: i for i, a in enumerate(self._artifacts)}
        artifact = BeliefArtifact(
            artifact_id=artifact_id,
            propositions=propositions,
            epistemic_boundary=epistemic_boundary or [],
            inferential_links=inferential_links or [],
            confidence=confidence,
            status=status,
            domain=domain,
            priority=priority,
            component=component,
            source_text=source_text or (propositions[0] if propositions else ""),
        )
        if not artifact.epistemic_boundary:
            artifact.epistemic_boundary = ["Assumed correct environment"]
        if artifact_id in existing:
            self._artifacts[existing[artifact_id]] = artifact
        else:
            self._artifacts.append(artifact)
        return artifact

    def accept(self, artifact_id: str) -> None:
        """Mark an artifact as ACCEPTED (binds it to stress-testing requirements)."""
        for a in self._artifacts:
            if a.artifact_id == artifact_id:
                a.status = BeliefStatus.ACCEPTED
                if a.confidence == ConfidenceLevel.UNKNOWN:
                    a.confidence = ConfidenceLevel.LOW
                return
        raise KeyError(f"Artifact '{artifact_id}' not found in session.")

    def add_evidence(self, artifact_id: str, citation: str) -> None:
        """Add an evidence citation to an artifact and elevate confidence."""
        for a in self._artifacts:
            if a.artifact_id == artifact_id:
                a.add_evidence(citation)
                return
        raise KeyError(f"Artifact '{artifact_id}' not found in session.")

    def mark_covered(self, artifact_id: str) -> None:
        """Mark an artifact as having test/experimental coverage."""
        self._covered.add(artifact_id)

    def load_from_requirements(self, path: Path) -> int:
        """Load BeliefArtifacts from a specsmith REQUIREMENTS.md file.

        Returns the number of artifacts loaded.
        """
        new_artifacts = parse_requirements_as_beliefs(path)
        existing_ids = {a.artifact_id for a in self._artifacts}
        added = 0
        for a in new_artifacts:
            if a.artifact_id not in existing_ids:
                self._artifacts.append(a)
                added += 1
        return added

    def load_from_dicts(self, data: list[dict[str, object]]) -> int:
        """Load BeliefArtifacts from a list of dicts (from JSON/YAML/DB)."""
        new_artifacts = beliefs_from_dicts(data)
        existing_ids = {a.artifact_id for a in self._artifacts}
        added = 0
        for a in new_artifacts:
            if a.artifact_id not in existing_ids:
                self._artifacts.append(a)
                added += 1
        return added

    # ------------------------------------------------------------------
    # AEE pipeline
    # ------------------------------------------------------------------

    def run(
        self,
        accepted_only: bool = False,
        test_path: Path | None = None,
    ) -> AEEResult:
        """Run the full AEE pipeline and return an AEEResult.

        Steps:
        1. Frame: parse artifacts
        2. Disassemble: identify primitives and boundaries
        3. Stress-Test (S): apply 8 adversarial challenge functions
        4. Build Failure-Mode Graph (G)
        5. Check equilibrium S(G)
        6. Compute certainty scores (C = base × coverage × freshness)
        7. Propagate via weakest-link rule
        8. Emit recovery proposals (R operator)
        """
        artifacts = self._artifacts
        if accepted_only:
            artifacts = [a for a in artifacts if a.is_accepted]

        # Clear previous failure modes for clean re-run
        for a in artifacts:
            a.failure_modes = []

        tester = StressTester(test_path=test_path)
        tester._covered_reqs = self._covered
        stress_result = tester.run(artifacts)

        graph = FailureModeGraph()
        graph.build(artifacts, stress_result)

        engine = CertaintyEngine(threshold=self.threshold)
        certainty = engine.run(artifacts, covered_reqs=self._covered)

        operator = RecoveryOperator()
        proposals = operator.propose(artifacts, stress_result)

        return AEEResult(
            artifacts=artifacts,
            stress_result=stress_result,
            certainty_report=certainty,
            proposals=proposals,
            graph=graph,
        )

    def stress_test(self, **kwargs: object) -> StressTestResult:
        """Run just the stress-test phase."""
        for a in self._artifacts:
            a.failure_modes = []
        tester = StressTester()
        tester._covered_reqs = self._covered
        return tester.run(self._artifacts)

    def score(self) -> CertaintyReport:
        """Run just the certainty scoring phase."""
        engine = CertaintyEngine(threshold=self.threshold)
        return engine.run(self._artifacts, covered_reqs=self._covered)

    def equilibrium_check(self) -> bool:
        """Quick equilibrium check without building the full graph."""
        result = self.stress_test()
        return result.equilibrium

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Path | None = None) -> Path:
        """Save belief state as JSON. Uses state_file if path not given."""
        out = path or self._state_file
        if out is None:
            raise ValueError("No path provided and no state_file configured.")
        out.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "project_name": self.project_name,
            "threshold": self.threshold,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "beliefs": [a.to_dict() for a in self._artifacts],
            "covered": sorted(self._covered),
        }
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return out

    def load(self, path: Path | None = None) -> int:
        """Load belief state from JSON. Returns number of artifacts loaded."""
        src = path or self._state_file
        if src is None or not src.exists():
            return 0
        data = json.loads(src.read_text(encoding="utf-8"))
        self._covered = set(data.get("covered", []))
        return self.load_from_dicts(data.get("beliefs", []))

    # ------------------------------------------------------------------
    # Trace vault
    # ------------------------------------------------------------------

    def seal(
        self,
        seal_type: str,
        description: str,
        author: str = "aee-session",
        artifact_ids: list[str] | None = None,
    ) -> object | None:
        """Seal the current epistemic state to the trace vault.

        Returns the SealRecord if a trace vault is configured, else None.
        """
        if self._vault is None:
            return None
        from epistemic.trace import TraceVault  # type: ignore[attr-defined]

        vault: TraceVault = self._vault  # type: ignore[assignment]
        ids = artifact_ids or [a.artifact_id for a in self._artifacts]
        return vault.seal(
            seal_type=seal_type,
            description=description,
            author=author,
            artifact_ids=ids,
        )

    def verify_trace(self) -> tuple[bool, list[str]]:
        """Verify cryptographic integrity of the trace vault."""
        if self._vault is None:
            return True, []
        from epistemic.trace import TraceVault  # type: ignore[attr-defined]

        vault: TraceVault = self._vault  # type: ignore[assignment]
        return vault.verify()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def artifacts(self) -> list[BeliefArtifact]:
        return list(self._artifacts)

    @property
    def artifact_count(self) -> int:
        return len(self._artifacts)

    def get(self, artifact_id: str) -> BeliefArtifact | None:
        for a in self._artifacts:
            if a.artifact_id == artifact_id:
                return a
        return None

    def __repr__(self) -> str:
        return (
            f"AEESession(project='{self.project_name}', "
            f"artifacts={self.artifact_count}, "
            f"threshold={self.threshold})"
        )


__all__ = ["AEEResult", "AEESession"]
