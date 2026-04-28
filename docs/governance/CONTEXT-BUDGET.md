# Context Window Management and Credit Optimization

## Core principle
Treat unnecessary credit consumption as a process defect.

## Session load protocol (lazy loading)
On session start, load only:
- `AGENTS.md` (in full)
- `docs/governance/RULES.md`
- `docs/governance/CONTEXT-BUDGET.md`
- Last ~300 lines of `LEDGER.md`

Load on demand:
- `docs/governance/SESSION-PROTOCOL.md` — when preparing proposals or ledger entries
- `docs/governance/LIFECYCLE.md` — when checking phase readiness or advancing
- `docs/governance/ROLES.md` — when role boundaries are relevant
- `docs/governance/VERIFICATION.md` — when testing or accepting work
- `docs/governance/DRIFT-METRICS.md` — when running `audit`
- `docs/REQUIREMENTS.md` — first ~200 lines, expand by section
- `docs/TESTS.md` — first ~200 lines, expand by section
- `docs/ARCHITECTURE.md` — first ~40 lines, expand by section

## During a session
- NEVER re-read a file already in context unless modified since last read
- Use line ranges for files > ~200 lines
- Prefer grep/semantic search over reading entire files
- Batch file reads into a single call
- Summarize rather than echo file contents
- Do not repeat proposals after creating them

## Conversation summarization recovery
If the conversation is summarized or truncated, re-read AGENTS.md in full before any further actions.

## Response economy
- No echoing file contents back
- No repeating proposal content after creation
- No "status theater" messages that add no information
- Provide only evidence needed to support conclusions

## Efficient verification order
1. Static validation / lint / syntax (cheapest)
2. Type checks / unit tests
3. Integration tests
4. Expensive builds / hardware flows (most expensive)

If a cheaper check fails, fix that before running more expensive checks.

## Cost tiers
- **low** — docs-only, single-file edits, small scaffolds
- **medium** — multi-file implementation, routine refactors, standard test runs
- **high** — architecture changes, large builds, broad audits

## Credit tracking

This project tracks AI credit spend automatically. At the end of each session:

1. Record usage: `specsmith credits record --model <model> --provider <provider> --tokens-in <N> --tokens-out <N> --task "<description>"`
2. Check budget: `specsmith credits summary`
3. If budget alerts appear, review with: `specsmith credits analyze`

Budget configuration: `specsmith credits budget --cap <USD> --alert-pct 80`
Credit data stored in `.specsmith/credits.json` (gitignored).
