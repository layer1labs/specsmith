# CLAUDE.md

This project follows the Agentic AI Development Workflow Specification (v0.3.7.dev2).
Project type: CLI tool (Python). Description: Applied Epistemic Engineering toolkit for AI-assisted development..

## Start here
1. Read `AGENTS.md` for project identity, governance hub, and file registry
2. Read `LEDGER.md` for session state and open TODOs
3. Read `docs/governance/RULES.md` for hard rules

## Workflow
All changes follow: propose → check → execute → verify → record.
Never modify code without a proposal in the ledger first.

## Project type
CLI tool (Python) (Spec Section 17.3)

## Key constraints
- AGENTS.md is the governance hub — keep it under 200 lines
- Modular governance docs live in `docs/governance/`
- All agent-invoked commands must have timeouts
- Use `scripts/exec.cmd` or `scripts/exec.sh` for bounded execution
- Record every session in LEDGER.md

## Verification
Before marking any task complete, run: ruff check, pytest, mypy

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

## Credit Tracking
At session end, record token usage:
`specsmith credits record --model <model> --provider anthropic   --tokens-in <N> --tokens-out <N> --task "<desc>"`
Check budget: `specsmith credits summary`
