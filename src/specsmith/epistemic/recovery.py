# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Recovery Operator (R) — resolves Logic Knots and Failure Modes.

The Recovery Operator R resolves Logic Knots by proposing minimal primitive
modifications to affected BeliefArtifacts. R never auto-applies changes —
it always emits bounded RecoveryProposals that require human approval before
any belief artifact is modified. This enforces Hard Rule H2 (No proposal =
no execution) at the epistemic level.

Recovery strategies
-------------------
1. DECOMPOSE   — Split a compound belief into independent primitives.
                 Addresses Irreducibility violations (Axiom 3).
2. CONSTRAIN   — Add an epistemic boundary to bound the claim's scope.
                 Addresses Observability violations (Axiom 1).
3. FALSIFY     — Add or improve a test to create a falsification path.
                 Addresses Falsifiability violations (Axiom 2).
4. QUANTIFY    — Replace vague terms with measurable criteria.
                 Addresses vagueness failure modes.
5. RESOLVE     — For Logic Knots: propose narrowing or superseding one
                 of the conflicting beliefs to eliminate the contradiction.
6. DEPRECATE   — Mark the artifact as deprecated and reference a
                 replacement. Used when the belief cannot be reconstructed
                 without fundamental scope change.

References
----------
AEE Recovery Operator (R): https://appliedepistemicengineering.com/
Axiom 4 (Reconstructability): Every failed belief yields a reconstructed
belief that satisfies Observability and Falsifiability.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from specsmith.epistemic.belief import BeliefArtifact, FailureMode, FailureSeverity
from specsmith.epistemic.stress_tester import StressTestResult


class RecoveryStrategy(str, Enum):
    """Strategy to apply when recovering a failed BeliefArtifact."""

    DECOMPOSE = "decompose"  # Split compound beliefs
    CONSTRAIN = "constrain"  # Add epistemic boundary
    FALSIFY = "falsify"  # Add/improve test
    QUANTIFY = "quantify"  # Replace vague terms with measures
    RESOLVE = "resolve"  # Resolve Logic Knot (narrow or supersede)
    DEPRECATE = "deprecate"  # Mark deprecated, add replacement note


@dataclass
class RecoveryProposal:
    """A bounded, human-reviewable proposal to resolve a failure mode.

    RecoveryProposals are always proposals — they are NEVER applied
    automatically. The human operator must approve each proposal before
    the corresponding BeliefArtifact is modified.

    Fields
    ------
    artifact_id : str
        The artifact this proposal targets.
    failure_mode_challenge : str
        The challenge string from the FailureMode being addressed.
    strategy : RecoveryStrategy
        The recovery strategy to apply.
    description : str
        Human-readable description of the proposed change.
    suggested_change : str
        Concrete suggestion (new text, boundary clause, test ID, etc.)
    estimated_cost : str
        Credit cost estimate (low / medium / high) per Section 25.
    priority : int
        Execution priority (1 = highest, higher numbers = lower priority).
        Ranked by severity: CRITICAL=1, HIGH=2, MEDIUM=3, LOW=4.
    """

    artifact_id: str
    failure_mode_challenge: str
    strategy: RecoveryStrategy
    description: str
    suggested_change: str
    estimated_cost: str = "low"
    priority: int = 3


class RecoveryOperator:
    """Propose minimal recovery actions for a set of Failure Modes.

    Usage::

        operator = RecoveryOperator()
        proposals = operator.propose(artifacts, stress_result)

    Proposals are ranked by priority (CRITICAL failures first) and grouped
    by artifact. Use ``format_proposals()`` to render them for display.
    """

    def propose(
        self,
        artifacts: list[BeliefArtifact],
        stress_result: StressTestResult,
    ) -> list[RecoveryProposal]:
        """Generate recovery proposals for all failure modes and logic knots.

        Returns proposals sorted by priority (most critical first).
        """
        proposals: list[RecoveryProposal] = []
        artifact_map = {a.artifact_id: a for a in artifacts}

        # Per-artifact failure mode proposals
        for artifact in artifacts:
            for fm in artifact.unresolved_failures:
                proposals.extend(self._propose_for_failure(artifact, fm))

        # Logic knot proposals (cross-artifact)
        for id1, id2, reason in stress_result.logic_knots:
            a1 = artifact_map.get(id1)
            a2 = artifact_map.get(id2)
            proposals.extend(self._propose_for_knot(a1, a2, id1, id2, reason))

        # Sort by priority
        proposals.sort(key=lambda p: p.priority)
        return proposals

    def _propose_for_failure(
        self, artifact: BeliefArtifact, fm: FailureMode
    ) -> list[RecoveryProposal]:
        """Generate recovery proposals for a single failure mode."""
        challenge = fm.challenge.lower()
        priority = _severity_priority(fm.severity)
        proposals: list[RecoveryProposal] = []

        if "vagueness" in challenge:
            if "unquantified" in challenge:
                proposals.append(
                    RecoveryProposal(
                        artifact_id=artifact.artifact_id,
                        failure_mode_challenge=fm.challenge,
                        strategy=RecoveryStrategy.QUANTIFY,
                        description=(
                            f"Replace vague quantity in {artifact.artifact_id} with "
                            "a specific numeric bound or threshold."
                        ),
                        suggested_change=(
                            "Replace terms like 'some', 'many', 'several' with "
                            "explicit numbers (e.g., 'at least 3', 'within 500ms', "
                            "'no more than 10')."
                        ),
                        estimated_cost="low",
                        priority=priority,
                    )
                )
            else:
                proposals.append(
                    RecoveryProposal(
                        artifact_id=artifact.artifact_id,
                        failure_mode_challenge=fm.challenge,
                        strategy=RecoveryStrategy.QUANTIFY,
                        description=(
                            f"Replace imprecise language in {artifact.artifact_id} "
                            "with specific, measurable criteria."
                        ),
                        suggested_change=fm.recovery_hint
                        or (
                            "Identify the vague term and replace it with a concrete, "
                            "measurable specification."
                        ),
                        estimated_cost="low",
                        priority=priority,
                    )
                )

        elif "falsifiability" in challenge or "missing_test" in challenge or "no test" in challenge:
            proposals.append(
                RecoveryProposal(
                    artifact_id=artifact.artifact_id,
                    failure_mode_challenge=fm.challenge,
                    strategy=RecoveryStrategy.FALSIFY,
                    description=(
                        f"Add a TEST entry in docs/TESTS.md for {artifact.artifact_id}."
                    ),
                    suggested_change=(
                        f"Add: `- **TEST-XXX**: Covers: {artifact.artifact_id}\\n"
                        f"  - **Type**: unit | integration\\n"
                        f"  - **Description**: Verify that {artifact.source_text[:80]}\\n"
                        "  - **Pass criteria**: [define pass criteria]`"
                    ),
                    estimated_cost="low",
                    priority=priority,
                )
            )

        elif "observability" in challenge or "boundary" in challenge:
            proposals.append(
                RecoveryProposal(
                    artifact_id=artifact.artifact_id,
                    failure_mode_challenge=fm.challenge,
                    strategy=RecoveryStrategy.CONSTRAIN,
                    description=(f"Add an explicit epistemic boundary to {artifact.artifact_id}."),
                    suggested_change=(
                        f"Add to {artifact.artifact_id}: "
                        "`- **Platform:** all | windows | linux | macos\\n"
                        "- **Boundary:** [assumptions and context within which this "
                        "requirement must hold]`"
                    ),
                    estimated_cost="low",
                    priority=priority,
                )
            )
            if not artifact.propositions:
                proposals.append(
                    RecoveryProposal(
                        artifact_id=artifact.artifact_id,
                        failure_mode_challenge=fm.challenge,
                        strategy=RecoveryStrategy.DECOMPOSE,
                        description=(
                            f"Add a description to {artifact.artifact_id} — currently empty."
                        ),
                        suggested_change=(
                            f"Add `- **Description:** [what {artifact.artifact_id} "
                            "must do, stated as a testable claim]`"
                        ),
                        estimated_cost="low",
                        priority=1,  # Always highest for empty artifacts
                    )
                )

        elif "irreducibility" in challenge or "compound" in challenge:
            proposals.append(
                RecoveryProposal(
                    artifact_id=artifact.artifact_id,
                    failure_mode_challenge=fm.challenge,
                    strategy=RecoveryStrategy.DECOMPOSE,
                    description=(
                        f"Decompose {artifact.artifact_id} into independent, "
                        "separately-testable requirements."
                    ),
                    suggested_change=(
                        f"Split {artifact.artifact_id} into {len(artifact.propositions)} "
                        "or more requirements, each with a single proposition and its "
                        "own test. Use sequential IDs (e.g., "
                        f"{artifact.artifact_id}a, {artifact.artifact_id}b, etc.)."
                    ),
                    estimated_cost="medium",
                    priority=priority,
                )
            )

        elif "confidence" in challenge and "p1" in challenge.lower():
            proposals.append(
                RecoveryProposal(
                    artifact_id=artifact.artifact_id,
                    failure_mode_challenge=fm.challenge,
                    strategy=RecoveryStrategy.FALSIFY,
                    description=(
                        f"Stress-test {artifact.artifact_id} (P1, low confidence) to "
                        "raise confidence to MEDIUM or higher."
                    ),
                    suggested_change=(
                        "Run specsmith stress-test, add test coverage, add explicit "
                        "boundary, and mark status as 'stress-tested' after evidence "
                        "is recorded in LEDGER.md."
                    ),
                    estimated_cost="medium",
                    priority=1,
                )
            )

        return proposals

    def _propose_for_knot(
        self,
        a1: BeliefArtifact | None,
        a2: BeliefArtifact | None,
        id1: str,
        id2: str,
        reason: str,
    ) -> list[RecoveryProposal]:
        """Generate recovery proposals for a Logic Knot."""
        proposals: list[RecoveryProposal] = []

        if "duplicate" in reason.lower():
            proposals.append(
                RecoveryProposal(
                    artifact_id=id1,
                    failure_mode_challenge=f"Logic Knot: {reason[:60]}",
                    strategy=RecoveryStrategy.DEPRECATE,
                    description=(f"Resolve duplicate ID conflict between {id1} and {id2}."),
                    suggested_change=(
                        f"Merge the two definitions of {id1} into one, or rename one "
                        "with a new unique ID. Record the decision in LEDGER.md."
                    ),
                    estimated_cost="low",
                    priority=1,
                )
            )
        else:
            proposals.append(
                RecoveryProposal(
                    artifact_id=id1,
                    failure_mode_challenge=f"Logic Knot: {reason[:60]}",
                    strategy=RecoveryStrategy.RESOLVE,
                    description=(f"Resolve Logic Knot between {id1} and {id2}: {reason[:120]}"),
                    suggested_change=(
                        f"Review both {id1} and {id2}. Options:\n"
                        "  1. Narrow the epistemic boundary of one so they no longer conflict\n"
                        "  2. Supersede one with the other (mark superseded as DEPRECATED)\n"
                        "  3. Decompose both into non-conflicting primitives\n"
                        "Record the resolution in LEDGER.md."
                    ),
                    estimated_cost="medium",
                    priority=1,
                )
            )
        return proposals

    def format_proposals(self, proposals: list[RecoveryProposal]) -> str:
        """Format proposals as a human-readable text summary."""
        if not proposals:
            return "✓ No recovery proposals needed. Equilibrium reached."

        lines = [
            f"Recovery Proposals ({len(proposals)} total)",
            "=" * 50,
            "These are PROPOSALS — all require human approval before applying.",
            "",
        ]

        for i, p in enumerate(proposals, 1):
            lines.append(
                f"{i}. [{p.strategy.value.upper()}] {p.artifact_id} (cost: {p.estimated_cost})"
            )
            lines.append(f"   Problem: {p.failure_mode_challenge}")
            lines.append(f"   Action:  {p.description}")
            lines.append(f"   Change:  {p.suggested_change[:200]}")
            lines.append("")

        return "\n".join(lines)


def _severity_priority(severity: FailureSeverity) -> int:
    return {
        FailureSeverity.CRITICAL: 1,
        FailureSeverity.HIGH: 2,
        FailureSeverity.MEDIUM: 3,
        FailureSeverity.LOW: 4,
    }[severity]
