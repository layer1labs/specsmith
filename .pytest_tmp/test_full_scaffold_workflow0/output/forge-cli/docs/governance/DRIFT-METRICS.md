# Drift Detection and Feedback Loops

## Health Signals
Evaluate on `audit` command. Optionally evaluate at session start.

### Consistency score
- Every requirement has at least one test
- Every test maps to at least one requirement
- Architecture supports all accepted requirements
- Target: **100%**

### Ledger health
- Every entry has all required fields
- Open TODOs are accurate
- Stale TODOs identified (open > 5 sessions)
- No completed TODO listed as open

### Documentation currency
- Architecture reflects implementation
- README reflects current structure and status
- Requirements/tests reflect accepted architecture

### Governance size health
- AGENTS.md within ~100-150 lines
- Governance docs remain focused
- LEDGER.md under ~500 lines or archived

### Rule compliance
Check last 5 ledger entries:
- Proposal present?
- Verification recorded?
- Next step recorded?
- Scope respected?

## Drift Response Protocol
If a health signal fails:
1. Report the failure explicitly
2. Reference exact files/sections
3. Record in ledger under Risks
4. Recommend smallest bounded corrective task

## Ledger Compression
When LEDGER.md > ~500 lines:
- Archive older entries to `docs/ledger-archive.md`
- Keep summary block + recent entries + active TODOs in LEDGER.md
- Archive preserves full history — no information deleted

## Feedback Loop Priority
Correct cheapest root cause first:
1. Compress/optimize context
2. Update stale docs
3. Split oversized governance files
4. Strengthen rules or load order
5. Revise workflow if same failure repeats
