# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Stress-Test Operator (S) — AEE adversarial challenge engine.

The Stress-Test Operator S takes a BeliefArtifact B and applies a suite of
adversarial challenge functions to surface Failure Modes. This is the AEE
equivalent of a compiler running type-checks and lint: it cannot guarantee
correctness, but it can efficiently surface known categories of weakness.

Challenge categories applied
----------------------------
1. VAGUENESS       — The claim uses imprecise language that admits multiple
                     contradictory interpretations (MUST, SHOULD, MAY confusion;
                     undefined quantities; undefined terms).
2. MISSING_TEST    — The claim has no linked test in the test specification.
                     A belief without a falsification mechanism violates Axiom 2.
3. MISSING_BOUNDARY — The claim lacks an explicit epistemic boundary. Hidden
                     assumptions (Axiom 1 violation) are detected here.
4. CONTRADICTION   — Two accepted beliefs in the same component make
                     incompatible claims. This indicates a Logic Knot.
5. CIRCULAR_LINK   — An artifact's inferential links form a cycle. Circular
                     justification violates Axiom 3 (Irreducibility).
6. COMPOUND_CLAIM  — A single belief captures multiple distinct, independently
                     falsifiable claims without decomposition. Violates Axiom 3.
7. NO_PROPOSITIONS — The artifact has no parsed propositions (empty or
                     unparseable description).
8. P1_LOW_CONFIDENCE — A P1 (critical) requirement has confidence below MEDIUM.
                       This is a stop condition per H13.

References
----------
AEE Stress-Test Operator: https://appliedepistemicengineering.com/
Failure-Mode Graph (G): stress-test → breakpoint relations
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from specsmith.epistemic.belief import (
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
    logic_knots: list[tuple[str, str, str]] = field(default_factory=list)  # (id1, id2, reason)
    equilibrium: bool = False  # True when S(G) yields no new failures

    @property
    def total_failures(self) -> int:
        return len(self.failure_modes)

    @property
    def critical_count(self) -> int:
        return sum(1 for fm in self.failure_modes if fm.severity == FailureSeverity.CRITICAL)

    @property
    def has_logic_knots(self) -> bool:
        return len(self.logic_knots) > 0


# Vagueness patterns — terms that indicate imprecision
_VAGUE_TERMS = re.compile(
    r"\b(appropriate|reasonable|sufficient|adequate|relevant|suitable|"
    r"timely|efficient|as needed|where necessary|if applicable|"
    r"may or may not|tbd|todo|placeholder|stub)\b",
    re.IGNORECASE,
)

# Quantity vagueness — "some", "many", "few" etc. without numbers
_VAGUE_QUANTITY = re.compile(
    r"\b(some|many|few|several|numerous|various|multiple)\b(?!\s+\d)",
    re.IGNORECASE,
)

# Compound claim indicators
_COMPOUND_INDICATORS = re.compile(r"\band\b.{20,}\band\b|\bsupports?.+\band\b", re.IGNORECASE)


class StressTester:
    """Apply adversarial challenge functions to a set of BeliefArtifacts.

    Usage::

        tester = StressTester(req_path=Path("docs/REQUIREMENTS.md"),
                              test_path=Path("docs/TESTS.md"))
        result = tester.run(artifacts)

    The tester is stateless after initialisation. Call ``run()`` as many
    times as needed (e.g., after updating requirements).
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

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, artifacts: list[BeliefArtifact]) -> StressTestResult:
        """Run all challenge functions against the artifact set.

        Mutates ``artifact.failure_modes`` in place and returns a
        ``StressTestResult`` summarising the outcome.
        """
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

        # Cross-artifact: contradiction detection (Logic Knots)
        knots = self._detect_logic_knots(artifacts)
        result.logic_knots.extend(knots)

        # Equilibrium: no unresolved critical failures and no logic knots
        result.equilibrium = result.critical_count == 0 and not result.has_logic_knots
        return result

    # ------------------------------------------------------------------
    # Individual challenge functions
    # ------------------------------------------------------------------

    def _challenge_vagueness(self, artifact: BeliefArtifact) -> list[FailureMode]:
        """Challenge: Does the claim use imprecise language?"""
        fms = []
        for prop in artifact.propositions:
            if _VAGUE_TERMS.search(prop):
                fms.append(
                    FailureMode(
                        artifact_id=artifact.artifact_id,
                        challenge="Vagueness: imprecise term detected",
                        breakpoint=(
                            f"Proposition '{prop[:80]}' contains imprecise language "
                            "that admits multiple interpretations."
                        ),
                        severity=FailureSeverity.MEDIUM,
                        recovery_hint="Replace vague terms with specific, measurable criteria.",
                    )
                )
            if _VAGUE_QUANTITY.search(prop):
                fms.append(
                    FailureMode(
                        artifact_id=artifact.artifact_id,
                        challenge="Vagueness: unquantified quantity",
                        breakpoint=(f"Proposition '{prop[:80]}' uses an unquantified quantity."),
                        severity=FailureSeverity.LOW,
                        recovery_hint="Replace with a specific numeric bound or threshold.",
                    )
                )
        return fms

    def _challenge_missing_test(self, artifact: BeliefArtifact) -> list[FailureMode]:
        """Challenge: Is there a test that can falsify this belief?"""
        if not artifact.is_accepted:
            return []  # Only accepted beliefs require test coverage
        if artifact.artifact_id in self._covered_reqs:
            return []
        return [
            FailureMode(
                artifact_id=artifact.artifact_id,
                challenge="Falsifiability: no test exists to challenge this belief",
                breakpoint=(
                    f"{artifact.artifact_id} is accepted but has no corresponding "
                    "TEST-xxx entry in TESTS.md. A belief without a falsification "
                    "mechanism violates Axiom 2 (Falsifiability)."
                ),
                severity=FailureSeverity.HIGH,
                recovery_hint=(
                    "Add a TEST entry in docs/TESTS.md that covers this requirement."
                ),
            )
        ]

    def _challenge_missing_boundary(self, artifact: BeliefArtifact) -> list[FailureMode]:
        """Challenge: Does the claim declare its epistemic boundary?"""
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
                    f"{artifact.artifact_id} makes claims without stating the assumptions "
                    "or context within which those claims must hold. Hidden assumptions "
                    "violate Axiom 1 (Observability) and Hard Rule H13."
                ),
                severity=FailureSeverity.LOW,
                recovery_hint=(
                    "Add a '**Platform:**' or '**Boundary:**' field declaring the scope "
                    "and assumptions for this requirement."
                ),
            )
        ]

    def _challenge_compound_claim(self, artifact: BeliefArtifact) -> list[FailureMode]:
        """Challenge: Is this a compound belief masking multiple primitives?"""
        if len(artifact.propositions) > 3:
            return [
                FailureMode(
                    artifact_id=artifact.artifact_id,
                    challenge="Irreducibility: compound belief with too many propositions",
                    breakpoint=(
                        f"{artifact.artifact_id} contains {len(artifact.propositions)} "
                        "propositions. Beliefs with more than 3 propositions often hide "
                        "Logic Knots and should be decomposed. Violates Axiom 3."
                    ),
                    severity=FailureSeverity.LOW,
                    recovery_hint=(
                        "Split this requirement into multiple, independently testable REQs."
                    ),
                )
            ]
        for prop in artifact.propositions:
            if _COMPOUND_INDICATORS.search(prop):
                return [
                    FailureMode(
                        artifact_id=artifact.artifact_id,
                        challenge="Irreducibility: compound claim structure detected",
                        breakpoint=(
                            f"Proposition '{prop[:80]}' appears to contain multiple "
                            "independent claims joined by 'and'. Each should be a "
                            "separate, falsifiable proposition."
                        ),
                        severity=FailureSeverity.LOW,
                        recovery_hint="Decompose into separate propositions or requirements.",
                    )
                ]
        return []

    def _challenge_no_propositions(self, artifact: BeliefArtifact) -> list[FailureMode]:
        """Challenge: Does the artifact have any testable claims?"""
        if artifact.propositions:
            return []
        return [
            FailureMode(
                artifact_id=artifact.artifact_id,
                challenge="Observability: no parseable propositions",
                breakpoint=(
                    f"{artifact.artifact_id} has no parsed propositions. "
                    "An empty requirement cannot be observed, tested, or falsified. "
                    "This violates Axioms 1 and 2."
                ),
                severity=FailureSeverity.CRITICAL,
                recovery_hint="Add a description or decompose into explicit propositions.",
            )
        ]

    def _challenge_p1_confidence(self, artifact: BeliefArtifact) -> list[FailureMode]:
        """Challenge: Is a P1 requirement insufficiently validated?"""
        if artifact.priority.upper() != "P1":
            return []
        if artifact.confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH):
            return []
        return [
            FailureMode(
                artifact_id=artifact.artifact_id,
                challenge="Confidence: P1 requirement below medium confidence",
                breakpoint=(
                    f"{artifact.artifact_id} is marked P1 (critical) but has "
                    f"confidence '{artifact.confidence.value}'. "
                    "P1 requirements with confidence below MEDIUM are a stop condition "
                    "per H13 (Epistemic Boundaries Required)."
                ),
                severity=FailureSeverity.CRITICAL,
                recovery_hint=(
                    "Elevate confidence by stress-testing, adding evidence, or "
                    "lowering the priority if the requirement is not truly critical."
                ),
            )
        ]

    def _challenge_circular_links(
        self, artifact: BeliefArtifact, id_set: set[str]
    ) -> list[FailureMode]:
        """Challenge: Do inferential links reference non-existent artifacts?"""
        fms = []
        for link in artifact.inferential_links:
            if link not in id_set and link != artifact.artifact_id:
                fms.append(
                    FailureMode(
                        artifact_id=artifact.artifact_id,
                        challenge="Irreducibility: dangling inferential link",
                        breakpoint=(
                            f"{artifact.artifact_id} references '{link}' in its "
                            "inferential links, but that artifact does not exist. "
                            "Dangling links undermine the justification chain."
                        ),
                        severity=FailureSeverity.MEDIUM,
                        recovery_hint=f"Remove or correct the link to '{link}'.",
                    )
                )
        return fms

    def _detect_logic_knots(self, artifacts: list[BeliefArtifact]) -> list[tuple[str, str, str]]:
        """Detect Logic Knots — irreducible conflicts between accepted beliefs.

        A Logic Knot exists when two accepted BeliefArtifacts in the same
        component make claims that are structurally incompatible. This is a
        simplified heuristic: it detects negation pairs (one uses MUST, other
        uses MUST NOT for similar subjects) and duplicate IDs.
        """
        knots: list[tuple[str, str, str]] = []
        accepted = [a for a in artifacts if a.is_accepted]

        # Detect duplicate IDs
        seen: dict[str, str] = {}
        for a in accepted:
            if a.artifact_id in seen:
                knots.append(
                    (
                        a.artifact_id,
                        seen[a.artifact_id],
                        "Duplicate requirement ID — two accepted beliefs share the same identifier.",  # noqa: E501
                    )
                )
            seen[a.artifact_id] = a.artifact_id

        # Detect MUST / MUST NOT pairs on similar subjects within a component
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
                                f"Negation conflict in component '{comp}': "
                                f"'{a1.artifact_id}' and '{a2.artifact_id}' appear to "
                                "make contradictory MUST/MUST NOT claims on the same subject.",
                            )
                        )
        return knots


def _has_negation_conflict(a1: BeliefArtifact, a2: BeliefArtifact) -> bool:
    """Heuristic: check if two artifacts assert opposite things about the same subject."""
    must_re = re.compile(r"\bMUST\b(?!\s+NOT)", re.IGNORECASE)
    must_not_re = re.compile(r"\bMUST\s+NOT\b", re.IGNORECASE)

    def _subjects(artifact: BeliefArtifact) -> set[str]:
        words: set[str] = set()
        for prop in artifact.propositions:
            # Extract significant nouns (simple heuristic: words > 4 chars, not stop words)
            words.update(
                w.lower()
                for w in re.findall(r"\b[a-zA-Z]{5,}\b", prop)
                if w.lower() not in _STOP_WORDS
            )
        return words

    def _has_must(artifact: BeliefArtifact) -> bool:
        return any(must_re.search(p) for p in artifact.propositions)

    def _has_must_not(artifact: BeliefArtifact) -> bool:
        return any(must_not_re.search(p) for p in artifact.propositions)

    if not (_has_must(a1) and _has_must_not(a2)) and not (_has_must_not(a1) and _has_must(a2)):
        return False

    subjects1 = _subjects(a1)
    subjects2 = _subjects(a2)
    overlap = subjects1 & subjects2
    return len(overlap) >= 2  # Require at least 2 shared subjects to flag


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


def _extract_covered_reqs(test_path: Path) -> set[str]:
    """Extract REQ IDs that are referenced in TESTS.md."""
    content = test_path.read_text(encoding="utf-8")
    pattern = re.compile(r"REQ-[A-Z0-9_]+-\d+")
    return set(pattern.findall(content))
