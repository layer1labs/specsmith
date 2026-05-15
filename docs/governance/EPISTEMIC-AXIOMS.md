# Epistemic Axioms — specsmith

specsmith is built on Applied Epistemic Engineering (AEE) principles. This document
defines the five axioms as they apply to specsmith's own development.

See the full AEE primer: https://specsmith.readthedocs.io/en/stable/aee-primer/

---

## Axiom 1: Observability

Every requirement in `docs/REQUIREMENTS.md` must be fully inspectable. Hidden assumptions
are a stop condition (H13).

**In practice:**
- All REQ-XXX entries must have `**Platform:**` or `**Boundary:**` fields
- Technology decisions in architecture.md must declare alternatives considered
- AGENTS.md proposals must include `Assumptions:` field

---

## Axiom 2: Falsifiability

Every accepted requirement must have a corresponding test. Unchallenged claims are not
engineering artifacts.

**In practice:**
- Every REQ-XXX with status ACCEPTED must have TEST-XXX in TESTS.md with `Covers:` reference
- `specsmith audit` enforces REQ↔TEST consistency
- `specsmith epistemic-audit` detects accepted requirements without test coverage

---

## Axiom 3: Irreducibility

Requirements must be decomposed to atomic, independently verifiable primitives.

**In practice:**
- Requirements with more than one core claim should be split
- `specsmith stress-test` flags compound claim patterns
- Each REQ-XXX should be independently testable

---

## Axiom 4: Reconstructability

Every failed requirement can be reconstructed. Failure modes are recovery opportunities.

**In practice:**
- `specsmith epistemic-audit` emits `RecoveryProposal` objects for all failure modes
- Recovery proposals require human approval before applying (H2)
- DEPRECATED requirements are kept in the ledger — never deleted

---

## Axiom 5: Convergence

Systematic application of stress-test (S) and recovery (R) will converge to equilibrium.

**In practice:**
- Run `specsmith stress-test` after every batch of new requirements
- A passing `specsmith epistemic-audit` with `Equilibrium: YES` is the milestone gate
- CI can gate on `specsmith epistemic-audit --threshold 0.6`

---

## Current Epistemic Status

Run `specsmith epistemic-audit --project-dir .` to check current status:
- Equilibrium: [run to check]
- Overall certainty: [run to check]
- Logic knots: [run to check]

---

## Certainty Threshold

specsmith's epistemic threshold: **0.7** (configured in `scaffold.yml`)

P1 requirements with confidence below MEDIUM are a stop condition per H13.

---

## External Validation: OEA Recursive Generative Stability

The five AEE axioms above describe the engineering properties that a governed AI system
must have. The question of *why* these axioms specifically prevent hallucination and drift
was answered empirically by the study:

> *"Ontology-Epistemic-Agentic (OEA) Recursive Generative Stability: A Unified Framework
> for Preventing Hallucination and Drift in Large Language Models"*
> — BitConcepts Research, 2026

The OEA study ran controlled ablation experiments across several LLM families and
identified the following correspondences between AEE axioms and measurable hallucination
control mechanisms:

| AEE Axiom | OEA Control Mechanism | Hard Rule |
|---|---|---|
| Axiom 1 — Observability | Epistemic scope bounding (H15) | H15 |
| Axiom 2 — Falsifiability | Calibration direction (H17); Falsifiability required (H20) | H17, H20 |
| Axiom 3 — Irreducibility | No undisclosed model assumptions (H21) | H21 |
| Axiom 4 — Reconstructability | Anti-drift recursion guard (H16) | H16 |
| Axiom 5 — Convergence | RAG retrieval filtering (H18); Synthetic contamination prevention (H19) | H18, H19 |

H22 (cross-platform CI enforcement) addresses the infrastructure dimension of the OEA
cross-platform validity requirement.

In concrete terms: a system that enforces H15–H22 operationalises the OEA framework.
Specsmith's governance layer is the first open-source AEE toolkit to encode these
findings as machine-enforceable rules via `specsmith validate`.
