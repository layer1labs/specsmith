# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Applied Epistemic Engineering — standalone Python library.

Install
-------
    pip install specsmith        # installs both specsmith and epistemic

The ``epistemic`` package is co-installed with specsmith and has **zero
external dependencies** beyond Python 3.10+. It can be imported by any
Python project to incorporate AEE practices.

Quick start
-----------
The simplest entry point is ``AEESession``::

    from epistemic import AEESession

    session = AEESession(project_name="my-research")
    session.add_belief(
        artifact_id="HYP-001",
        propositions=["Our decipherment hypothesis is internally consistent"],
        epistemic_boundary=["Corpus: 500 inscriptions, phase 1 only"],
        domain="linguistics",
    )
    result = session.run()
    print(result.summary())

For non-trivial projects you'll want to:

1. ``add_belief()`` — register claims, hypotheses, requirements
2. ``add_evidence()`` / ``mark_covered()`` — record what's been validated
3. ``accept()`` — elevate to ACCEPTED status (binds stress-testing)
4. ``run()`` — execute the full AEE pipeline
5. ``seal()`` — cryptographically seal the epistemic state

What AEE provides
-----------------
Applied Epistemic Engineering treats belief systems like code: codable,
testable, and deployable. Its formal mathematical foundations include:

**Five axioms:**
  1. Observability      — every belief must be inspectable (hidden assumptions → stop)
  2. Falsifiability     — every belief must be challengeable (dogma ≠ engineering)
  3. Irreducibility     — decompose to atomic primitives (compound claims → Logic Knots)
  4. Reconstructability — every failed belief can be reconstructed (scope may narrow)
  5. Convergence        — S+R iteration always converges to equilibrium E

**Core process: Frame → Disassemble → Stress-Test → Reconstruct**

**Key operators:**
  S(B) = StressTester — adversarial challenge function
  R(K) = RecoveryOperator — resolves Logic Knots K
  G     = FailureModeGraph — maps stress-test → breakpoint relations
  E     = Equilibrium point where S(G) yields no new failures
  C     = Certainty score ∈ [0, 1] from CertaintyEngine

Real-world use cases
--------------------
  Software engineering:  requirements as BeliefArtifacts, tests as falsifiers
  Linguistics research:  hypotheses as BeliefArtifacts, experiments as evidence
  AI alignment:          model assumptions as BeliefArtifacts, red-teaming as stress-tests
  Policy/compliance:     regulations as BeliefArtifacts, audits as failure modes
  Patent prosecution:    claims as BeliefArtifacts, prior art as stress-tests

glossa-lab example
------------------
    from epistemic import AEESession, ConfidenceLevel, BeliefStatus
    from pathlib import Path

    # Create a session for Indus script decipherment research
    session = AEESession(
        project_name="glossa-lab-indus",
        threshold=0.65,
        state_file=Path(".epistemic/indus.json"),
        trace_dir=Path(".epistemic"),
    )

    # Load previous session state
    session.load()

    # Register competing hypotheses
    session.add_belief(
        artifact_id="HYP-IND-001",
        propositions=["The Indus script is logosyllabic"],
        epistemic_boundary=["Mahadevan corpus, 2977 inscriptions, 1977 edition"],
        domain="epigraphy",
        status=BeliefStatus.ACCEPTED,
        confidence=ConfidenceLevel.LOW,
    )
    session.add_belief(
        artifact_id="HYP-IND-002",
        propositions=["Indus sign frequency follows Zipf distribution"],
        epistemic_boundary=["Same corpus as HYP-IND-001"],
        inferential_links=["HYP-IND-001"],  # confidence propagates from HYP-IND-001
        domain="epigraphy",
        status=BeliefStatus.ACCEPTED,
    )

    # Record experimental evidence
    session.add_evidence("HYP-IND-001", "Rao et al. 2009 — conditional entropy study")
    session.add_evidence("HYP-IND-002", "Mahadevan 1977 — sign frequency tables")
    session.mark_covered("HYP-IND-001")  # has experimental coverage

    # Run the full AEE pipeline
    result = session.run()
    print(result.summary())

    # If there are Logic Knots (competing theories), inspect them:
    for id1, id2, reason in result.stress_result.logic_knots:
        print(f"Conflict: {id1} vs {id2}: {reason}")

    # See the certainty map by domain
    for score in result.certainty_report.scores:
        print(f"  {score.artifact_id}: {score.propagated_score:.2f} [{score.label}]")

    # Seal this session's epistemic state
    session.seal("stress-test", "Indus decipherment hypothesis stress-test v2")
    session.save()

References
----------
- AEE:    https://appliedepistemicengineering.com/
- ARE:    https://github.com/organvm-i-theoria/auto-revision-epistemic-engine
- VERITAS: https://github.com/AionSystem/VERITAS
- Springer: https://doi.org/10.1007/s11948-023-00451-3
"""

from __future__ import annotations

from epistemic.belief import (
    BeliefArtifact,
    BeliefStatus,
    ConfidenceLevel,
    FailureMode,
    FailureSeverity,
    beliefs_from_dicts,
    parse_requirements_as_beliefs,
)
from epistemic.certainty import ArtifactCertainty, CertaintyEngine, CertaintyReport
from epistemic.failure_graph import FailureModeGraph, GraphNode
from epistemic.recovery import RecoveryOperator, RecoveryProposal, RecoveryStrategy
from epistemic.session import AEEResult, AEESession
from epistemic.stress_tester import StressTester, StressTestResult

__version__ = "0.3.0"

__all__ = [
    # Session facade (primary entry point)
    "AEESession",
    "AEEResult",
    # Belief model
    "BeliefArtifact",
    "BeliefStatus",
    "ConfidenceLevel",
    "FailureMode",
    "FailureSeverity",
    "parse_requirements_as_beliefs",
    "beliefs_from_dicts",
    # Stress testing
    "StressTester",
    "StressTestResult",
    # Failure graph
    "FailureModeGraph",
    "GraphNode",
    # Recovery
    "RecoveryOperator",
    "RecoveryProposal",
    "RecoveryStrategy",
    # Certainty
    "CertaintyEngine",
    "CertaintyReport",
    "ArtifactCertainty",
]
