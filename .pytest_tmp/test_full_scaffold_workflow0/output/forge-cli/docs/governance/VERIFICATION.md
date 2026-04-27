# Verification and Acceptance Standards

## Verification minimum
Every meaningful task must record:
- What changed
- What was tested
- What passed
- What failed
- What is unknown

"Not tested" is acceptable. "Tested" without evidence is not.

## Project Verification Tools
**Lint:** ruff check
**Typecheck:** mypy
**Test:** pytest
**Security:** pip-audit
**Format:** ruff format

Run these tools before marking any task as complete. Record tool output in the ledger.

## Acceptance standard
Work is accepted ONLY if:
- Proposal matched execution (no scope creep)
- Checks were run and results recorded
- Ledger was updated
- Next step was defined

If any condition is not met, the work is **provisional only** and must be marked as such in the ledger.

## Conflict and consistency handling
If an agent detects:
- A requirement without a corresponding test
- A test without a corresponding requirement
- Architecture that contradicts requirements
- Ledger inconsistencies
- Documentation that contradicts implementation

The agent SHALL:
1. Report the issue explicitly
2. Reference exact document locations
3. NOT propose fixes unless requested by the human
4. Record the inconsistency in the ledger under "Risks"
