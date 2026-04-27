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
