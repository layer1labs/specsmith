# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Stress-Test Operator (S) — AEE adversarial challenge engine.

Part of the standalone ``epistemic`` library. Zero external dependencies.
    from epistemic import StressTester
    from epistemic.stress_tester import StressTestResult
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from epistemic.belief import (
    BeliefArtifact,
    ConfidenceLevel,
    FailureMode,
    FailureSeverity,
)


@dataclass
class StressTestResult:
    """Outcome of applying StressTester to a collection of BeliefArtifacts."""

    artifacts_tested: int = 0
    failure_modes: list[FailureMode] = field(default_factory=list)
    logic_knots: list[tuple[str, str, str]] = field(default_factory=list)
    equilibrium: bool = False

    @property
    def total_failures(self) -> int:
        return len(self.failure_modes)

    @property
    def critical_count(self) -> int:
        return sum(1 for fm in self.failure_modes if fm.severity == FailureSeverity.CRITICAL)

    @property
    def has_logic_knots(self) -> bool:
        return len(self.logic_knots) > 0


_VAGUE_TERMS = re.compile(
    r"\b(appropriate|reasonable|sufficient|adequate|relevant|suitable|"
    r"timely|efficient|as needed|where necessary|if applicable|"
    r"may or may not|tbd|todo|placeholder|stub)\b",
    re.IGNORECASE,
)
_VAGUE_QUANTITY = re.compile(
    r"\b(some|many|few|several|numerous|various|multiple)\b(?!\s+\d)",
    re.IGNORECASE,
)
_COMPOUND_INDICATORS = re.compile(r"\band\b.{20,}\band\b|\bsupports?.+\band\b", re.IGNORECASE)

_STOP_WORDS = {
    "must",
    "shall",
    "should",
    "could",
    "would",
    "have",
    "that",
    "this",
    "with",
    "from",
    "into",
    "each",
    "when",
    "where",
    "which",
    "their",
    "there",
    "these",
    "those",
    "after",
    "before",
    "project",
    "system",
    "command",
    "using",
    "defined",
    "allow",
}


class StressTester:
    """Apply adversarial challenge functions to a set of BeliefArtifacts.

    Zero external dependencies. Works with any Python project::

        from epistemic import StressTester, BeliefArtifact, BeliefStatus

        artifacts = [BeliefArtifact(
            artifact_id="HYP-001",
            propositions=["The Indus script is logosyllabic"],
            status=BeliefStatus.ACCEPTED,
        )]
        tester = StressTester()
        result = tester.run(artifacts)
        print(f"Equilibrium: {result.equilibrium}")
        print(f"Failures: {result.total_failures}")
    """

    def __init__(
        self,
        req_path: Path | None = None,
        test_path: Path | None = None,
    ) -> None:
        self._req_path = req_path
        self._test_path = test_path
        self._covered_reqs: set[str] = set()
        if test_path and test_path.exists():
            self._covered_reqs = _extract_covered_reqs(test_path)

    def run(self, artifacts: list[BeliefArtifact]) -> StressTestResult:
        """Run all challenge functions. Mutates artifact.failure_modes in place."""
        result = StressTestResult(artifacts_tested=len(artifacts))
        id_set = {a.artifact_id for a in artifacts}

        for artifact in artifacts:
            fms = (
                self._challenge_vagueness(artifact)
                + self._challenge_missing_test(artifact)
                + self._challenge_missing_boundary(artifact)
                + self._challenge_compound_claim(artifact)
                + self._challenge_no_propositions(artifact)
                + self._challenge_p1_confidence(artifact)
                + self._challenge_circular_links(artifact, id_set)
            )
            artifact.failure_modes.extend(fms)
            result.failure_modes.extend(fms)

        knots = self._detect_logic_knots(artifacts)
        result.logic_knots.extend(knots)
        result.equilibrium = result.critical_count == 0 and not result.has_logic_knots
        return result

    def _challenge_vagueness(self, artifact: BeliefArtifact) -> list[FailureMode]:
        fms = []
        for prop in artifact.propositions:
            if _VAGUE_TERMS.search(prop):
                fms.append(
                    FailureMode(
                        artifact_id=artifact.artifact_id,
                        challenge="Vagueness: imprecise term detected",
                        breakpoint=f"Proposition '{prop[:80]}' contains imprecise language.",
                        severity=FailureSeverity.MEDIUM,
                        recovery_hint="Replace vague terms with specific, measurable criteria.",
                    ),
                )
            if _VAGUE_QUANTITY.search(prop):
                fms.append(
                    FailureMode(
                        artifact_id=artifact.artifact_id,
                        challenge="Vagueness: unquantified quantity",
                        breakpoint=f"Proposition '{prop[:80]}' uses an unquantified quantity.",
                        severity=FailureSeverity.LOW,
                        recovery_hint="Replace with a specific numeric bound or threshold.",
                    ),
                )
        return fms

    def _challenge_missing_test(self, artifact: BeliefArtifact) -> list[FailureMode]:
        if not artifact.is_accepted:
            return []
        if artifact.artifact_id in self._covered_reqs:
            return []
        return [
            FailureMode(
                artifact_id=artifact.artifact_id,
                challenge="Falsifiability: no test exists to challenge this belief",
                breakpoint=(
                    f"{artifact.artifact_id} is accepted but has no test. "
                    "A belief without a falsification mechanism violates Axiom 2."
                ),
                severity=FailureSeverity.HIGH,
                recovery_hint="Add a test entry that covers this requirement.",
            ),
        ]

    def _challenge_missing_boundary(self, artifact: BeliefArtifact) -> list[FailureMode]:
        if artifact.epistemic_boundary and any(
            b
            for b in artifact.epistemic_boundary
            if b.strip() and b.strip() != "Assumed correct project environment"
        ):
            return []
        if not artifact.propositions:
            return []
        return [
            FailureMode(
                artifact_id=artifact.artifact_id,
                challenge="Observability: no explicit epistemic boundary declared",
                breakpoint=(
                    f"{artifact.artifact_id} makes claims without stating boundary conditions. "
                    "Hidden assumptions violate Axiom 1 (Observability)."
                ),
                severity=FailureSeverity.LOW,
                recovery_hint="Add an explicit epistemic boundary declaring scope and assumptions.",
            ),
        ]

    def _challenge_compound_claim(self, artifact: BeliefArtifact) -> list[FailureMode]:
        if len(artifact.propositions) > 3:
            return [
                FailureMode(
                    artifact_id=artifact.artifact_id,
                    challenge="Irreducibility: compound belief with too many propositions",
                    breakpoint=(
                        f"{artifact.artifact_id} has {len(artifact.propositions)} propositions. "
                        "Beliefs with >3 propositions often hide Logic Knots."
                    ),
                    severity=FailureSeverity.LOW,
                    recovery_hint="Split into multiple, independently testable beliefs.",
                ),
            ]
        for prop in artifact.propositions:
            if _COMPOUND_INDICATORS.search(prop):
                return [
                    FailureMode(
                        artifact_id=artifact.artifact_id,
                        challenge="Irreducibility: compound claim structure detected",
                        breakpoint=f"Proposition '{prop[:80]}' contains multiple claims.",
                        severity=FailureSeverity.LOW,
                        recovery_hint="Decompose into separate propositions.",
                    ),
                ]
        return []

    def _challenge_no_propositions(self, artifact: BeliefArtifact) -> list[FailureMode]:
        if artifact.propositions:
            return []
        return [
            FailureMode(
                artifact_id=artifact.artifact_id,
                challenge="Observability: no parseable propositions",
                breakpoint=(
                    f"{artifact.artifact_id} has no propositions. "
                    "An empty belief cannot be observed, tested, or falsified."
                ),
                severity=FailureSeverity.CRITICAL,
                recovery_hint="Add a description or explicit propositions.",
            ),
        ]

    def _challenge_p1_confidence(self, artifact: BeliefArtifact) -> list[FailureMode]:
        if artifact.priority.upper() != "P1":
            return []
        if artifact.confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH):
            return []
        return [
            FailureMode(
                artifact_id=artifact.artifact_id,
                challenge="Confidence: P1 belief below medium confidence",
                breakpoint=(
                    f"{artifact.artifact_id} is P1 but confidence='{artifact.confidence.value}'. "
                    "P1 beliefs with confidence below MEDIUM are a stop condition."
                ),
                severity=FailureSeverity.CRITICAL,
                recovery_hint="Stress-test, add evidence, or lower the priority.",
            ),
        ]

    def _challenge_circular_links(
        self,
        artifact: BeliefArtifact,
        id_set: set[str],
    ) -> list[FailureMode]:
        fms = []
        for link in artifact.inferential_links:
            if link not in id_set and link != artifact.artifact_id:
                fms.append(
                    FailureMode(
                        artifact_id=artifact.artifact_id,
                        challenge="Irreducibility: dangling inferential link",
                        breakpoint=f"{artifact.artifact_id} references '{link}' which does not exist.",  # noqa: E501
                        severity=FailureSeverity.MEDIUM,
                        recovery_hint=f"Remove or correct the link to '{link}'.",
                    ),
                )
        return fms

    def _detect_logic_knots(self, artifacts: list[BeliefArtifact]) -> list[tuple[str, str, str]]:
        knots: list[tuple[str, str, str]] = []
        accepted = [a for a in artifacts if a.is_accepted]

        seen: dict[str, str] = {}
        for a in accepted:
            if a.artifact_id in seen:
                knots.append(
                    (
                        a.artifact_id,
                        seen[a.artifact_id],
                        "Duplicate belief ID — two accepted beliefs share the same identifier.",
                    ),
                )
            seen[a.artifact_id] = a.artifact_id

        by_component: dict[str, list[BeliefArtifact]] = {}
        for a in accepted:
            by_component.setdefault(a.component, []).append(a)

        for comp, group in by_component.items():
            if not comp:
                continue
            for i, a1 in enumerate(group):
                for a2 in group[i + 1 :]:
                    if _has_negation_conflict(a1, a2):
                        knots.append(
                            (
                                a1.artifact_id,
                                a2.artifact_id,
                                f"Negation conflict in '{comp}': contradictory MUST/MUST NOT claims.",  # noqa: E501
                            ),
                        )
        return knots


def _has_negation_conflict(a1: BeliefArtifact, a2: BeliefArtifact) -> bool:
    must_re = re.compile(r"\bMUST\b(?!\s+NOT)", re.IGNORECASE)
    must_not_re = re.compile(r"\bMUST\s+NOT\b", re.IGNORECASE)

    def _subjects(artifact: BeliefArtifact) -> set[str]:
        words: set[str] = set()
        for prop in artifact.propositions:
            words.update(
                w.lower()
                for w in re.findall(r"\b[a-zA-Z]{5,}\b", prop)
                if w.lower() not in _STOP_WORDS
            )
        return words

    def _has_must(a: BeliefArtifact) -> bool:
        return any(must_re.search(p) for p in a.propositions)

    def _has_must_not(a: BeliefArtifact) -> bool:
        return any(must_not_re.search(p) for p in a.propositions)

    if not (_has_must(a1) and _has_must_not(a2)) and not (_has_must_not(a1) and _has_must(a2)):
        return False

    overlap = _subjects(a1) & _subjects(a2)
    return len(overlap) >= 2


def _extract_covered_reqs(test_path: Path) -> set[str]:
    """Extract REQ/HYP/ART IDs referenced in a test spec or any markdown file."""
    content = test_path.read_text(encoding="utf-8")
    # Match specsmith REQ-XXX-NNN and also generic ID patterns
    pattern = re.compile(r"\b(?:REQ|HYP|ART|DEC|COMP)-[A-Z0-9_]+-\d+\b")
    return set(pattern.findall(content))


__all__ = ["StressTestResult", "StressTester"]
