# specsmith — Governed Project Skill

## Context
This project follows the Agentic AI Development Workflow Specification (v0.3.7.dev2).
Project type: CLI tool (Python) (Section 17.3).
Description: Applied Epistemic Engineering toolkit for AI-assisted development..

## Session Start
1. Read `AGENTS.md` — the governance hub
2. Read `LEDGER.md` — check last session state and open TODOs
3. Read `docs/governance/RULES.md` — hard rules and stop conditions

## Workflow
All changes follow: **propose → check → execute → verify → record**.
- Every code change requires a proposal in the ledger
- Every proposal needs verification before marking complete
- Never skip the ledger entry

## Key Files
- `AGENTS.md` — governance hub (read first)
- `LEDGER.md` — session ledger (read second)
- `docs/governance/` — modular governance docs (load on demand)
- `REQUIREMENTS.md` — formal requirements (root, machine-authoritative)
- `TESTS.md` — test specifications (root, machine-authoritative)
- `ARCHITECTURE.md` — architecture reference

## Session Start
Before any work, run: `specsmith update --check --project-dir .`
If outdated, run: `specsmith update --yes`

## Commands
When user says `commit`: run `specsmith commit --project-dir .`
When user says `push`: run `specsmith push --project-dir .`
When user says `sync`: run `specsmith sync --project-dir .`
When user says `pr`: run `specsmith pr --project-dir .`
When user says `audit`: run `specsmith audit --project-dir .`
When user says `session-end`: run `specsmith session-end --project-dir .`

## Verification
Before marking any task complete, run: ruff check, pytest, mypy

## Credit Tracking
After completing tasks, record token usage:
```
specsmith credits record --model <model> --provider <provider>   --tokens-in <N> --tokens-out <N> --task "<desc>"
```
Check budget: `specsmith credits summary`

## Rules
- Proposals before changes (no exceptions)
- Verify before recording completion
- Use execution shims (`scripts/exec.cmd` / `scripts/exec.sh`) for external commands
- Keep AGENTS.md under 200 lines
- Record every session in the ledger
- Record credit usage at session end
