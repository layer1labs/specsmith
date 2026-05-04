# API Stability (Pre-1.0)
Specsmith is currently a **pre-1.0** project. This document captures the
contracts the project intends to honor as it approaches 1.0, and which
contracts are still subject to change.
## Stable contracts (held since 0.4)
The following surfaces are treated as stable in spirit: any breaking change
ships with a CHANGELOG entry, a deprecation note, and at least one minor
release of overlap.
- `specsmith preflight <utterance>` JSON payload schema:
  `decision`, `work_item_id`, `requirement_ids`, `test_case_ids`,
  `confidence_target`, `instruction`, `intent`, optional `narration`,
  optional `predicted_refinement` (REQ-117), optional `stress_warnings`.
- `specsmith verify` JSON payload schema:
  `equilibrium`, `confidence`, `summary`, `files_changed`, `test_results`,
  `retry_strategy`, `work_item_id`, `retry_budget`, `confidence_threshold`,
  optional `reviewer_comment` (REQ-116).
- Exit codes: preflight emits 0/2/3 per `decision`; verify emits 0/2/3 per
  `equilibrium`/`retry_strategy` (REQ-092 / REQ-097).
- Governance machine state: `.specsmith/workitems.json`,
  `.specsmith/testcases.json`, `LEDGER.md` event types
  (`preflight`, `work_proposal`, `cleanup`, `task_complete`, ...).
- Nexus chat block protocol (REQ-113): `block_start`, `block_complete`,
  `token`, `tool_call`, `tool_request`, `tool_result`, `plan`, `plan_step`,
  `diff`, `task_complete` event kinds.
## Pre-1.0 caveats (subject to change)
Until the project is stamped 1.0, the following surfaces may evolve. Each
change ships with a CHANGELOG entry but does not require a major bump.
- `src/specsmith/agent/*` Python APIs (verifier, events, memory, mcp,
  router, rules). Their **shape** is stable but signatures may grow.
- The `specsmith chat` CLI flags. New event kinds and flags may be added;
  existing keys will not be removed without a deprecation cycle.
- `.specsmith/sessions/<id>/turns.jsonl` schema (REQ-120). Fields will be
  additive, but the file format itself may switch from JSONL to a
  database in a future release.
## Versioning policy
- We follow SemVer once the project hits 1.0.
- Until then, the `0.MINOR.PATCH` line is used as a "preview" channel:
  minor bumps may include intentional breaking changes that are clearly
  called out in `CHANGELOG.md`.
- `pyproject.toml` will keep the `Development Status :: 4 - Beta`
  classifier until 1.0 ships.
## What "1.0" will mean
We will only stamp 1.0 once:
1. The Nexus chat block protocol has been used by at least one external
   IDE integration for two minor releases.
2. The mypy strict carveout in `pyproject.toml` has been emptied except
   for explicitly third-party-typed modules.
3. The performance baseline (REQ-124) has been published in
   `.specsmith/perf/baseline.json` for at least three releases without
   regression.
Until those criteria are met, expect a steady stream of pre-1.0 minor
releases.
## The `api-surface` snapshot (REQ-140)
The `specsmith api-surface` command emits the **frozen public surface** as
JSON. It exists so external automation, IDE plugins, and the CI pipeline
can diff against a known-good snapshot and detect drift before a release
ships.
The payload has three top-level keys:
- `cli_commands` — sorted list of top-level subcommand names. Adding new
  commands is non-breaking; renaming/removing is.
- `exit_codes` — the semantic exit codes for `preflight` (0/2/3) and
  `verify` (0/2/3). These are part of the contract and downstream
  automation depends on them.
- `event_types` — the JSONL event kinds emitted by `specsmith chat` and
  the `serve` SSE endpoint: `block_start`, `block_complete`, `token`,
  `plan_step`, `tool_call`, `tool_request`, `tool_result`, `diff`,
  `task_complete`. Adding new event types is non-breaking.
### Snapshot file
The canonical snapshot lives at `tests/fixtures/api_surface.json`. The
test `tests/test_warp_parity_followup.py::test_api_surface_matches_fixture`
asserts equality between the live output and the fixture. If you have
intentionally changed the public surface, regenerate the fixture:
```bash
py -m specsmith.cli api-surface > tests/fixtures/api_surface.json
```
Then call out the change in the next CHANGELOG entry.
### Required-command spot check
A second test, `test_api_surface_contains_required_1_0_commands`, asserts
that a hand-picked subset of 1.0-contract commands (`preflight`, `verify`,
`audit`, `validate`, `doctor`, `scan`, `init`, `import`, `ledger`,
`drive`, `history`, `chat`, `chat-export-block`, `voice`, `api-surface`,
`suggest-command`, `serve`) is *always* present. This catches accidental
command removal even when someone updates the fixture without checking
what they removed.
### What is *not* covered by the snapshot
- Subcommand names of Click groups (e.g. `voice transcribe`). The group
  name is in `cli_commands`; the subcommands are covered by their own
  `--help` text and focused integration tests.
- The shape of internal Click options not documented in `--help`.
- The wire format of the `~/.specsmith/` cache directory.
- Banner text, log formatting, prompt wording.
- Module-level Python APIs (`specsmith.agent.runner`,
  `specsmith.history_search`, etc.). These are reserved for internal use.
