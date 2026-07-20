# Architecture — Specsmith

Specsmith is a lean Applied Epistemic Engineering (AEE) governance layer for
AI-assisted development. It does not replace a coding agent, test runner, Git
client, browser, deployment platform, or orchestration framework. It supplies
the small contract those tools need to make requirement-scoped, test-backed,
epistemically bounded changes.

## Mission-essential kernel

1. **Requirements** — canonical behavior lives in
   `docs/requirements/*.yml` with durable IDs.
2. **Linked tests** — `docs/tests/*.yml` records the evidence expected for each
   accepted requirement.
3. **Deterministic preflight** — `specsmith preflight` classifies mutation
   intent, resolves scope, and stops ambiguous or destructive work.
4. **Verification** — `specsmith verify` and `specsmith audit` evaluate observed
   diffs, test results, traceability, and confidence.
5. **Epistemic context** — checkpoints and compression preserve knowns,
   unknowns, active work, and evidence without sending the full project history
   through a model.
6. **Durable evidence** — the ledger and ESDB retain provenance and integrity
   across sessions.

## Runtime boundaries

- `src/specsmith/governance_logic.py` implements deterministic preflight and
  verification wiring.
- `src/specsmith/agent/broker.py` classifies intent and requirement scope.
- `src/specsmith/cli.py` exposes the focused CLI.
- `src/specsmith/auditor.py` checks governance health and coverage.
- `src/specsmith/context_orchestrator.py` compiles bounded context.
- `src/specsmith/esdb/` provides the default SQLite evidence store and optional
  ChronoMemory bridge.
- `src/specsmith/integrations/` translates the AEE contract into host-native
  agent configuration.
- `src/specsmith/agent/repl.py` powers Grace, the optional local fallback REPL.

The host tool remains responsible for editing code, Git operations, native test
execution, browsing, deployment, and generic skills.

## Governed change loop

```text
intent
  -> deterministic preflight
  -> requirement + linked-test scope
  -> host-native implementation and tests
  -> verification and confidence gate
  -> durable checkpoint / evidence
```

No model decides whether governance passed. Model output is evidence input;
deterministic policy and observed tests decide.

## State model

Canonical human-reviewed sources live under `docs/requirements/` and
`docs/tests/`. Derived machine caches live under `.specsmith/` and are rebuilt
with `specsmith sync`. Work items connect an accepted intent to requirements,
tests, verification, and final disposition. `LEDGER.md` and ESDB records provide
session continuity and tamper-evident provenance.

## Integration model

`specsmith integrate`, MCP, and Zoo/Roo Code setup exchange only the smallest
sufficient contract: mutation intent, accepted scope, linked tests, uncertainty,
and verification evidence. Integrations must preserve user-owned configuration,
repair obsolete Specsmith-managed configuration, and behave consistently on
Windows, Linux, and macOS.

## Grace Broker Boundary

Grace is a convenience fallback, not a second product architecture. It uses the
same preflight, context, verification, and evidence paths as external agents. It
adds local-provider selection, clear recovery guidance, `/help`, `/status`,
`/why`, and bounded context reporting.

### Grace Preflight CLI Subcommand

Grace sends every proposed mutation through the same deterministic
`specsmith preflight` contract used by external agents.

### Grace REPL Execution Gate

The REPL executes only accepted work. Clarification and rejection decisions are
shown to the user before any tool or model action can mutate the project.

### Grace Bounded-Retry Harness

Provider retries are bounded and preserve the original governance decision,
requirement scope, and error evidence instead of silently widening the task.

## Release boundary

The public CLI validates release readiness but cannot publish Specsmith. Reviewed
`release/*` branches, fixed-point candidate checks, immutable tags, GitHub
Actions, PyPI trusted publishing, and release evidence own publication.

The detailed component map is maintained in `docs/ARCHITECTURE.md`.
