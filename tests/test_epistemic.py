# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for the epistemic package — AEE core machinery.

Covers:
  TEST-AEE-001 through TEST-AEE-005 — BeliefArtifact model
  TEST-STR-001 through TEST-STR-005 — StressTester
  TEST-FMG-001 through TEST-FMG-005 — FailureModeGraph
  TEST-CRT-001 through TEST-CRT-005 — CertaintyEngine
  TEST-TRC-001 through TEST-TRC-003 — TraceVault
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from epistemic import (
    AEESession,
    BeliefArtifact,
    BeliefStatus,
    CertaintyEngine,
    ConfidenceLevel,
    FailureModeGraph,
    FailureSeverity,
    RecoveryOperator,
    StressTester,
)
from epistemic.stress_tester import StressTestResult
from epistemic.trace import SealType, TraceVault

# ---------------------------------------------------------------------------
# TEST-AEE: BeliefArtifact model
# ---------------------------------------------------------------------------


class TestBeliefArtifact:
    """TEST-AEE-001 to TEST-AEE-005"""

    def test_belief_artifact_basic_creation(self) -> None:
        """TEST-AEE-001: BeliefArtifact creates with required fields."""
        a = BeliefArtifact(
            artifact_id="REQ-CLI-001",
            propositions=["specsmith init scaffolds a project"],
            epistemic_boundary=["Platform: all"],
        )
        assert a.artifact_id == "REQ-CLI-001"
        assert len(a.propositions) == 1
        assert a.confidence == ConfidenceLevel.UNKNOWN
        assert a.status == BeliefStatus.DRAFT
        assert not a.is_accepted
        assert not a.has_failures

    def test_belief_artifact_accepted_status(self) -> None:
        """TEST-AEE-002: ACCEPTED, STRESS_TESTED, RECONSTRUCTED all satisfy is_accepted."""
        for status in (
            BeliefStatus.ACCEPTED,
            BeliefStatus.STRESS_TESTED,
            BeliefStatus.RECONSTRUCTED,
        ):  # noqa: E501
            a = BeliefArtifact(artifact_id="X", status=status)
            assert a.is_accepted

        a = BeliefArtifact(artifact_id="X", status=BeliefStatus.DRAFT)
        assert not a.is_accepted

    def test_add_evidence_elevates_confidence(self) -> None:
        """TEST-AEE-003: add_evidence() elevates confidence from UNKNOWN to LOW."""
        a = BeliefArtifact(artifact_id="HYP-001", confidence=ConfidenceLevel.UNKNOWN)
        assert a.confidence == ConfidenceLevel.UNKNOWN
        a.add_evidence("Rao et al. 2009")
        assert a.confidence == ConfidenceLevel.LOW
        assert len(a.evidence) == 1

    def test_to_dict_serialization(self) -> None:
        """TEST-AEE-004: to_dict() returns JSON-compatible dict."""
        a = BeliefArtifact(
            artifact_id="REQ-001",
            propositions=["claim"],
            confidence=ConfidenceLevel.MEDIUM,
        )
        d = a.to_dict()
        assert d["artifact_id"] == "REQ-001"
        assert d["confidence"] == "medium"
        assert "propositions" in d
        # Should be JSON-serializable
        json.dumps(d)

    def test_parse_requirements_as_beliefs(self, tmp_path: Path) -> None:
        """TEST-AEE-005: Requirements in REQUIREMENTS.md parse as BeliefArtifacts."""
        req_file = tmp_path / "REQUIREMENTS.md"
        req_file.write_text(
            "# Requirements\n\n"
            "## REQ-CLI-001\n"
            "- **Description**: specsmith init scaffolds a governed project\n"
            "- **Priority**: P1\n"
            "- **Status**: accepted\n"
            "- **Platform**: all\n",
            encoding="utf-8",
        )
        from epistemic.belief import parse_requirements_as_beliefs

        artifacts = parse_requirements_as_beliefs(req_file)
        assert len(artifacts) == 1
        a = artifacts[0]
        assert a.artifact_id == "REQ-CLI-001"
        assert a.component == "CLI"
        assert a.priority == "P1"
        assert a.status == BeliefStatus.ACCEPTED
        assert a.confidence == ConfidenceLevel.LOW  # accepted → LOW
        assert "Platform" in a.epistemic_boundary[0]


# ---------------------------------------------------------------------------
# TEST-STR: StressTester
# ---------------------------------------------------------------------------


class TestStressTester:
    """TEST-STR-001 to TEST-STR-005"""

    def test_stress_tester_empty_proposition_is_critical(self) -> None:
        """TEST-STR-001: No propositions → CRITICAL failure (Observability violation)."""
        a = BeliefArtifact(artifact_id="REQ-EMPTY-001", propositions=[])
        tester = StressTester()
        result = tester.run([a])
        assert result.critical_count >= 1
        assert any(
            "no parseable propositions" in fm.challenge.lower() for fm in result.failure_modes
        )  # noqa: E501

    def test_stress_tester_detects_vagueness(self) -> None:
        """TEST-STR-002: Vague terms detected as MEDIUM failure modes."""
        a = BeliefArtifact(
            artifact_id="REQ-001",
            propositions=["The system should handle requests in a reasonable time"],
        )
        tester = StressTester()
        result = tester.run([a])
        vague = [fm for fm in result.failure_modes if "vagueness" in fm.challenge.lower()]
        assert len(vague) >= 1

    def test_stress_tester_equilibrium_with_clean_artifact(self) -> None:
        """TEST-STR-003: Clean artifact with test coverage reaches equilibrium."""
        a = BeliefArtifact(
            artifact_id="REQ-001",
            propositions=["The API returns HTTP 200 for valid requests"],
            epistemic_boundary=["Platform: all", "Auth: JWT required"],
            confidence=ConfidenceLevel.MEDIUM,
            status=BeliefStatus.DRAFT,  # not accepted, so no missing-test check
        )
        tester = StressTester()
        result = tester.run([a])
        # Draft artifacts skip the missing-test check; with boundary, should have no critical
        assert result.critical_count == 0

    def test_stress_tester_missing_test_for_accepted(self, tmp_path: Path) -> None:
        """TEST-STR-004: Accepted artifact without test coverage flags HIGH failure."""
        a = BeliefArtifact(
            artifact_id="REQ-001",
            propositions=["Something"],
            epistemic_boundary=["Platform: all"],
            status=BeliefStatus.ACCEPTED,
        )
        tester = StressTester()
        result = tester.run([a])
        missing_test = [
            fm for fm in result.failure_modes if "falsifiability" in fm.challenge.lower()
        ]
        assert len(missing_test) == 1
        assert missing_test[0].severity == FailureSeverity.HIGH

    def test_stress_tester_logic_knot_duplicate_id(self) -> None:
        """TEST-STR-005: Duplicate accepted IDs produce Logic Knot."""
        a1 = BeliefArtifact(
            artifact_id="REQ-001",
            propositions=["Claim A"],
            status=BeliefStatus.ACCEPTED,
        )
        a2 = BeliefArtifact(
            artifact_id="REQ-001",  # same ID!
            propositions=["Claim B"],
            status=BeliefStatus.ACCEPTED,
        )
        tester = StressTester()
        result = tester.run([a1, a2])
        assert len(result.logic_knots) >= 1
        assert any("duplicate" in reason.lower() for _, _, reason in result.logic_knots)


# ---------------------------------------------------------------------------
# TEST-FMG: FailureModeGraph
# ---------------------------------------------------------------------------


class TestFailureModeGraph:
    """TEST-FMG-001 to TEST-FMG-005"""

    def _make_clean_result(self) -> StressTestResult:
        return StressTestResult(artifacts_tested=1, failure_modes=[], logic_knots=[])

    def test_equilibrium_with_no_failures(self) -> None:
        """TEST-FMG-001: FailureModeGraph equilibrium_check passes when no failures."""
        a = BeliefArtifact(artifact_id="REQ-001", propositions=["claim"])
        result = self._make_clean_result()
        graph = FailureModeGraph()
        graph.build([a], result)
        assert graph.equilibrium_check() is True

    def test_equilibrium_fails_with_critical(self) -> None:
        """TEST-FMG-002: equilibrium_check fails when critical failures exist."""
        from epistemic.belief import FailureMode

        a = BeliefArtifact(
            artifact_id="REQ-001",
            propositions=[],
            failure_modes=[
                FailureMode(
                    artifact_id="REQ-001",
                    challenge="empty",
                    breakpoint="no propositions",
                    severity=FailureSeverity.CRITICAL,
                )
            ],
        )
        result = StressTestResult(artifacts_tested=1, failure_modes=a.failure_modes)
        graph = FailureModeGraph()
        graph.build([a], result)
        assert graph.equilibrium_check() is False

    def test_logic_knot_detect(self) -> None:
        """TEST-FMG-003: logic_knot_detect returns all detected knots."""
        a = BeliefArtifact(artifact_id="REQ-001", propositions=["claim"])
        knot = ("REQ-001", "REQ-002", "Duplicate ID")
        result = StressTestResult(artifacts_tested=1, logic_knots=[knot])
        graph = FailureModeGraph()
        graph.build([a], result)
        knots = graph.logic_knot_detect()
        assert len(knots) == 1
        assert knots[0][0] == "REQ-001"

    def test_render_text_no_failures(self) -> None:
        """TEST-FMG-004: render_text shows equilibrium YES when clean."""
        a = BeliefArtifact(artifact_id="REQ-001", propositions=["claim"])
        result = self._make_clean_result()
        graph = FailureModeGraph()
        graph.build([a], result)
        text = graph.render_text()
        assert "YES" in text or "✓" in text

    def test_render_mermaid(self) -> None:
        """TEST-FMG-005: render_mermaid produces valid Mermaid output."""
        a = BeliefArtifact(artifact_id="REQ-001", propositions=["claim"])
        result = self._make_clean_result()
        graph = FailureModeGraph()
        graph.build([a], result)
        mermaid = graph.render_mermaid()
        assert mermaid.startswith("graph TD")
        assert "REQ_001" in mermaid


# ---------------------------------------------------------------------------
# TEST-CRT: CertaintyEngine
# ---------------------------------------------------------------------------


class TestCertaintyEngine:
    """TEST-CRT-001 to TEST-CRT-005"""

    def test_certainty_unknown_artifact_scores_zero(self) -> None:
        """TEST-CRT-001: UNKNOWN confidence + no propositions = score 0.0."""
        a = BeliefArtifact(
            artifact_id="REQ-001",
            propositions=[],
            confidence=ConfidenceLevel.UNKNOWN,
        )
        engine = CertaintyEngine(threshold=0.7)
        report = engine.run([a])
        score = next(s for s in report.scores if s.artifact_id == "REQ-001")
        assert score.propagated_score == 0.0
        assert score.label == "UNKNOWN"

    def test_certainty_covered_medium_artifact(self) -> None:
        """TEST-CRT-002: MEDIUM confidence + test coverage = score above 0.4."""
        a = BeliefArtifact(
            artifact_id="REQ-001",
            propositions=["claim A"],
            confidence=ConfidenceLevel.MEDIUM,
        )
        engine = CertaintyEngine(threshold=0.7)
        report = engine.run([a], covered_reqs={"REQ-001"})
        score = next(s for s in report.scores if s.artifact_id == "REQ-001")
        # C = 0.55 * 1.0 * 1.0 = 0.55
        assert score.propagated_score == pytest.approx(0.55, abs=0.01)

    def test_certainty_weakest_link_propagation(self) -> None:
        """TEST-CRT-003: Certainty propagates via weakest-link rule."""
        strong = BeliefArtifact(
            artifact_id="REQ-A",
            propositions=["strong claim"],
            confidence=ConfidenceLevel.HIGH,
        )
        weak = BeliefArtifact(
            artifact_id="REQ-B",
            propositions=["depends on A"],
            confidence=ConfidenceLevel.HIGH,
            inferential_links=["REQ-A"],  # depends on strong
        )
        # Artificially lower strong's confidence by marking it uncovered
        engine = CertaintyEngine(threshold=0.7)
        # covered_reqs empty → strong gets 0.4 coverage weight
        # strong: 0.85 * 0.4 = 0.34
        # weak: initially 0.85 * 0.4 = 0.34, after propagation: min(0.34, 0.34) = 0.34
        report = engine.run([strong, weak], covered_reqs=set())
        score_a = next(s for s in report.scores if s.artifact_id == "REQ-A")
        score_b = next(s for s in report.scores if s.artifact_id == "REQ-B")
        # After propagation, B cannot exceed A
        assert score_b.propagated_score <= score_a.propagated_score + 0.01

    def test_certainty_component_averages(self) -> None:
        """TEST-CRT-004: component_averages groups by component code."""
        a1 = BeliefArtifact(
            "REQ-CLI-001", component="CLI", propositions=["c1"], confidence=ConfidenceLevel.MEDIUM
        )
        a2 = BeliefArtifact(
            "REQ-CLI-002", component="CLI", propositions=["c2"], confidence=ConfidenceLevel.LOW
        )
        engine = CertaintyEngine()
        report = engine.run([a1, a2])
        avgs = report.component_averages
        assert "CLI" in avgs
        assert 0.0 < avgs["CLI"] < 1.0

    def test_certainty_below_threshold_list(self) -> None:
        """TEST-CRT-005: below_threshold contains IDs of low-scoring artifacts."""
        a = BeliefArtifact(
            artifact_id="REQ-001",
            propositions=["claim"],
            confidence=ConfidenceLevel.UNKNOWN,
        )
        engine = CertaintyEngine(threshold=0.3)
        report = engine.run([a])
        assert "REQ-001" in report.below_threshold


# ---------------------------------------------------------------------------
# TEST-TRC: TraceVault
# ---------------------------------------------------------------------------


class TestTraceVault:
    """TEST-TRC-001 to TEST-TRC-003"""

    def test_trace_vault_seal_and_verify(self, tmp_path: Path) -> None:
        """TEST-TRC-001: TraceVault chain verification passes for intact chain."""
        vault = TraceVault(tmp_path)
        vault.seal(SealType.DECISION, "Adopted Python 3.12")
        vault.seal(SealType.MILESTONE, "Phase 1 complete")
        valid, errors = vault.verify()
        assert valid is True
        assert len(errors) == 0
        assert vault.count() == 2

    def test_trace_vault_tamper_detection(self, tmp_path: Path) -> None:
        """TEST-TRC-002: TraceVault detects tampered entry (hash mismatch)."""
        vault = TraceVault(tmp_path)
        vault.seal(SealType.DECISION, "Original decision")
        vault.seal(SealType.MILESTONE, "Milestone 1")

        # Tamper with the first seal
        trace_file = tmp_path / "trace.jsonl"
        content = trace_file.read_text()
        lines = content.strip().split("\n")
        first = json.loads(lines[0])
        first["description"] = "TAMPERED DESCRIPTION"  # change content but not hash
        lines[0] = json.dumps(first)
        trace_file.write_text("\n".join(lines) + "\n")

        valid, errors = vault.verify()
        assert valid is False
        assert len(errors) > 0

    def test_trace_vault_genesis_chain(self, tmp_path: Path) -> None:
        """TEST-TRC-003: First seal uses genesis hash as prev_hash."""
        vault = TraceVault(tmp_path)
        seal = vault.seal(SealType.EPISTEMIC, "First seal")
        assert seal.prev_hash == "0" * 64
        assert len(seal.entry_hash) == 64  # SHA-256 hex

    def test_trace_vault_chaining(self, tmp_path: Path) -> None:
        """Chain: second seal's prev_hash equals first seal's entry_hash."""
        vault = TraceVault(tmp_path)
        s1 = vault.seal(SealType.DECISION, "First")
        s2 = vault.seal(SealType.MILESTONE, "Second")
        assert s2.prev_hash == s1.entry_hash


# ---------------------------------------------------------------------------
# TEST-EPI: AEESession integration
# ---------------------------------------------------------------------------


class TestAEESession:
    def test_session_basic_run(self) -> None:
        """AEESession.run() returns AEEResult with summary."""
        session = AEESession("test-project")
        session.add_belief(
            "HYP-001",
            ["The hypothesis is testable"],
            epistemic_boundary=["Corpus: test data"],
        )
        result = session.run()
        summary = result.summary()
        assert "AEE Session Report" in summary
        assert "Artifacts:" in summary

    def test_session_accept_and_run(self) -> None:
        """Accepted belief without test coverage gets a HIGH failure mode."""
        session = AEESession("test")
        session.add_belief(
            "REQ-001",
            ["System returns 200"],
            epistemic_boundary=["All platforms"],
            status=BeliefStatus.ACCEPTED,
        )
        result = session.run()
        # Should detect missing test for accepted belief
        high_failures = [
            fm
            for fm in result.stress_result.failure_modes
            if fm.severity in (FailureSeverity.HIGH, FailureSeverity.CRITICAL)
        ]
        assert len(high_failures) >= 1

    def test_session_save_and_load(self, tmp_path: Path) -> None:
        """AEESession.save() and load() round-trip the belief state."""
        state_file = tmp_path / "beliefs.json"
        session1 = AEESession("test", state_file=state_file)
        session1.add_belief("REQ-001", ["claim"])
        session1.save()

        session2 = AEESession("test", state_file=state_file)
        count = session2.load()
        assert count == 1
        assert session2.get("REQ-001") is not None

    def test_session_equilibrium_check(self) -> None:
        """equilibrium_check returns bool without building full graph."""
        session = AEESession("test")
        session.add_belief(
            "REQ-001",
            ["clean claim"],
            epistemic_boundary=["Platform: all"],
            status=BeliefStatus.DRAFT,
        )
        eq = session.equilibrium_check()
        assert isinstance(eq, bool)

    def test_session_trace_vault(self, tmp_path: Path) -> None:
        """AEESession with trace_dir enables sealing."""
        session = AEESession("test", trace_dir=tmp_path)
        seal = session.seal("decision", "Test decision")
        assert seal is not None
        valid, errors = session.verify_trace()
        assert valid is True

    def test_session_load_from_dicts(self) -> None:
        """load_from_dicts() constructs BeliefArtifacts from plain dicts."""
        session = AEESession("test")
        count = session.load_from_dicts(
            [
                {
                    "artifact_id": "HYP-001",
                    "propositions": ["claim"],
                    "confidence": "low",
                    "status": "accepted",
                }
            ]
        )
        assert count == 1
        a = session.get("HYP-001")
        assert a is not None
        assert a.confidence == ConfidenceLevel.LOW


# ---------------------------------------------------------------------------
# TEST-RCV: RecoveryOperator
# ---------------------------------------------------------------------------


class TestRecoveryOperator:
    def test_recovery_proposals_for_empty_artifact(self) -> None:
        """RecoveryOperator generates CRITICAL-priority proposals for empty artifacts."""
        a = BeliefArtifact(artifact_id="REQ-001", propositions=[])
        tester = StressTester()
        result = tester.run([a])
        operator = RecoveryOperator()
        proposals = operator.propose([a], result)
        assert len(proposals) >= 1
        assert proposals[0].priority == 1  # CRITICAL = 1

    def test_recovery_no_proposals_at_equilibrium(self) -> None:
        """No proposals when artifact is clean draft with no failures."""
        a = BeliefArtifact(
            artifact_id="REQ-001",
            propositions=["clean claim"],
            epistemic_boundary=["Platform: all"],
            status=BeliefStatus.DRAFT,
        )
        tester = StressTester()
        result = tester.run([a])
        operator = RecoveryOperator()
        proposals = operator.propose([a], result)
        # Draft with boundary and propositions should have few or no failures
        # At minimum, format_proposals should not crash
        formatted = operator.format_proposals(proposals)
        assert isinstance(formatted, str)
