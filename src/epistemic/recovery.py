# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Recovery Operator (R) — resolves Logic Knots and Failure Modes.

Part of the standalone ``epistemic`` library. Zero external dependencies.
    from epistemic import RecoveryOperator, RecoveryProposal
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from epistemic.belief import BeliefArtifact, FailureMode, FailureSeverity
from epistemic.stress_tester import StressTestResult


class RecoveryStrategy(str, Enum):
    DECOMPOSE = "decompose"
    CONSTRAIN = "constrain"
    FALSIFY = "falsify"
    QUANTIFY = "quantify"
    RESOLVE = "resolve"
    DEPRECATE = "deprecate"


@dataclass
class RecoveryProposal:
    """A bounded, human-reviewable proposal to resolve a failure mode.

    NEVER auto-applied. Human must approve before modification.
    """

    artifact_id: str
    failure_mode_challenge: str
    strategy: RecoveryStrategy
    description: str
    suggested_change: str
    estimated_cost: str = "low"
    priority: int = 3


class RecoveryOperator:
    """Propose minimal recovery actions for Failure Modes and Logic Knots.

    from epistemic import RecoveryOperator

    operator = RecoveryOperator()
    proposals = operator.propose(artifacts, stress_result)
    print(operator.format_proposals(proposals))
    """

    def propose(
        self,
        artifacts: list[BeliefArtifact],
        stress_result: StressTestResult,
    ) -> list[RecoveryProposal]:
        proposals: list[RecoveryProposal] = []
        artifact_map = {a.artifact_id: a for a in artifacts}

        for artifact in artifacts:
            for fm in artifact.unresolved_failures:
                proposals.extend(self._propose_for_failure(artifact, fm))

        for id1, id2, reason in stress_result.logic_knots:
            a1 = artifact_map.get(id1)
            a2 = artifact_map.get(id2)
            proposals.extend(self._propose_for_knot(a1, a2, id1, id2, reason))

        proposals.sort(key=lambda p: p.priority)
        return proposals

    def _propose_for_failure(
        self,
        artifact: BeliefArtifact,
        fm: FailureMode,
    ) -> list[RecoveryProposal]:
        challenge = fm.challenge.lower()
        priority = _severity_priority(fm.severity)
        proposals: list[RecoveryProposal] = []

        if "vagueness" in challenge:
            strategy = (
                RecoveryStrategy.QUANTIFY
                if "unquantified" in challenge
                else RecoveryStrategy.QUANTIFY
            )
            proposals.append(
                RecoveryProposal(
                    artifact_id=artifact.artifact_id,
                    failure_mode_challenge=fm.challenge,
                    strategy=strategy,
                    description=f"Replace imprecise language in {artifact.artifact_id}.",
                    suggested_change=fm.recovery_hint
                    or "Replace vague terms with measurable criteria.",
                    priority=priority,
                ),
            )
        elif "falsifiability" in challenge or "no test" in challenge:
            proposals.append(
                RecoveryProposal(
                    artifact_id=artifact.artifact_id,
                    failure_mode_challenge=fm.challenge,
                    strategy=RecoveryStrategy.FALSIFY,
                    description=f"Add a test for {artifact.artifact_id}.",
                    suggested_change=f"Add a test entry that covers: {artifact.source_text[:80]}",
                    priority=priority,
                ),
            )
        elif "observability" in challenge or "boundary" in challenge:
            proposals.append(
                RecoveryProposal(
                    artifact_id=artifact.artifact_id,
                    failure_mode_challenge=fm.challenge,
                    strategy=RecoveryStrategy.CONSTRAIN,
                    description=f"Add epistemic boundary to {artifact.artifact_id}.",
                    suggested_change="Declare scope, assumptions, and platform constraints.",
                    priority=priority,
                ),
            )
            if not artifact.propositions:
                proposals.append(
                    RecoveryProposal(
                        artifact_id=artifact.artifact_id,
                        failure_mode_challenge=fm.challenge,
                        strategy=RecoveryStrategy.DECOMPOSE,
                        description=f"Add propositions to {artifact.artifact_id} — currently empty.",  # noqa: E501
                        suggested_change="Add a description as a testable claim.",
                        priority=1,
                    ),
                )
        elif "irreducibility" in challenge or "compound" in challenge:
            proposals.append(
                RecoveryProposal(
                    artifact_id=artifact.artifact_id,
                    failure_mode_challenge=fm.challenge,
                    strategy=RecoveryStrategy.DECOMPOSE,
                    description=f"Decompose {artifact.artifact_id} into independent beliefs.",
                    suggested_change="Split into separate beliefs, each with a single proposition.",
                    estimated_cost="medium",
                    priority=priority,
                ),
            )
        elif "confidence" in challenge:
            proposals.append(
                RecoveryProposal(
                    artifact_id=artifact.artifact_id,
                    failure_mode_challenge=fm.challenge,
                    strategy=RecoveryStrategy.FALSIFY,
                    description=f"Raise confidence for P1 belief {artifact.artifact_id}.",
                    suggested_change="Add test coverage, evidence citations, and mark as stress-tested.",  # noqa: E501
                    estimated_cost="medium",
                    priority=1,
                ),
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
        if "duplicate" in reason.lower():
            return [
                RecoveryProposal(
                    artifact_id=id1,
                    failure_mode_challenge=f"Logic Knot: {reason[:60]}",
                    strategy=RecoveryStrategy.DEPRECATE,
                    description=f"Resolve duplicate ID conflict between {id1} and {id2}.",
                    suggested_change="Merge or rename one with a unique ID.",
                    priority=1,
                ),
            ]
        return [
            RecoveryProposal(
                artifact_id=id1,
                failure_mode_challenge=f"Logic Knot: {reason[:60]}",
                strategy=RecoveryStrategy.RESOLVE,
                description=f"Resolve Logic Knot between {id1} and {id2}.",
                suggested_change=(
                    f"Review both {id1} and {id2}. Options:\n"
                    "  1. Narrow epistemic boundary of one\n"
                    "  2. Supersede one (mark as DEPRECATED)\n"
                    "  3. Decompose both into non-conflicting primitives"
                ),
                estimated_cost="medium",
                priority=1,
            ),
        ]

    def format_proposals(self, proposals: list[RecoveryProposal]) -> str:
        if not proposals:
            return "✓ No recovery proposals needed. Equilibrium reached."

        lines = [
            f"Recovery Proposals ({len(proposals)} total)",
            "=" * 50,
            "PROPOSALS — all require human approval before applying.",
            "",
        ]
        for i, p in enumerate(proposals, 1):
            lines.append(
                f"{i}. [{p.strategy.value.upper()}] {p.artifact_id} (cost: {p.estimated_cost})",
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


__all__ = ["RecoveryOperator", "RecoveryProposal", "RecoveryStrategy"]
