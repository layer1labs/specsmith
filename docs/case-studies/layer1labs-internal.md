# Case Study: Layer1Labs Internal (Dogfooding Specsmith)
## Project type
Python CLI governance tool with supporting documentation, integrations, and CI pipelines.

## Problem
Agentic development produced fast iteration but made traceability and audit reconstruction difficult across concurrent changes.

## Workflow before specsmith governance
- Ad hoc intent capture in chat and commit messages.
- Inconsistent requirement-to-test linkage.
- Limited reproducibility for post-hoc audits.

## Workflow with specsmith governance
- `preflight` establishes accepted intent and mints work items.
- `verify` checks implementation equilibrium and captures outcomes.
- `audit` and export commands consolidate evidence for review.
- Trace and ESDB records provide tamper-evident change history.

## Measurable benefits
- Stronger ESDB chain integrity checks across sessions.
- More complete audit trails for decision and implementation paths.
- Clearer preflight gating for ambiguous or risky tasks.

## Limitations
- Governance setup introduces upfront process overhead.
- Teams still need discipline for requirement/test quality.
- Very lightweight projects may prefer lower-ceremony configurations.
