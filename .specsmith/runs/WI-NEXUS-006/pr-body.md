# feat(nexus): natural-language broker, preflight CLI, and gated REPL execution

Adds the **Nexus** local-first agent runtime under Specsmith governance. All
implementation work is governed by Specsmith requirements and verified by
pytest. **Suite: 232 passing.**

## Work items in this PR

- **WI-NEXUS-001..003** — AG2 orchestrator (Planner/Shell/Code/Reviewer/Memory/Git/HumanProxy/Executor),
  safety middleware (`is_safe_command`, `validate_json_args`, `normalize_path`),
  repo indexer that populates `.repo-index/`, REPL with slash commands
  (`/plan /ask /fix /test /commit /pr /undo /context /exit`), pinned vLLM
  `l1-nexus` docker-compose service with hermes tool-call parser, safe-cleanup
  module + `specsmith clean` CLI subcommand, and UTF-8 console factory
  (REQ-065..REQ-082).
- **WI-NEXUS-004** — Repository-wide rename `TEST_SPEC.md → TESTS.md`
  including code, docs, templates, ReadTheDocs site, and machine state, with a
  regression scan that fails the build if any legacy name is reintroduced
  (REQ-083).
- **WI-NEXUS-005** — Natural-language **governance broker**
  (`src/specsmith/agent/broker.py`) exposing `Intent`, `RequirementSummary`,
  `ScopeProposal`, `PreflightDecision`, `RunResult`, and the
  `classify_intent / parse_requirements / infer_scope / run_preflight /
  narrate_plan / execute_with_governance / broker_step` API. Governance IDs
  (REQ/TEST/WI) are hidden by default; the REPL `/why` toggle reveals them.
  Bounded retries (`DEFAULT_RETRY_BUDGET = 3`) and a single clarifying
  question on stop-and-align (REQ-084).
- **WI-NEXUS-006** — `specsmith preflight <utterance> [--project-dir]
  [--json] [--verbose]` CLI subcommand that classifies intent, infers scope,
  and emits a JSON decision payload. The Nexus REPL now gates
  `orchestrator.run_task` behind `decision.accepted`; rejected utterances
  surface a single plain-English clarification (REQ-085, REQ-086).

## Why

Translates the user's plain-English vision — *"can the agent be smart enough
to drive Specsmith governance so the user can interact with words, not having
to think about requirements and things, and have the agent broker the needed
due diligence in easy human terms?"* — into a real implementation boundary.
Specsmith remains the sole governance authority. Nexus only executes inside
that envelope.

## Verification

- `py scripts/sync_governance_state.py` → 86 requirements / 86 test cases.
- `py -m pytest -q` → **232 passed in 16.6s**.
- Evidence captured for each WI under `.specsmith/runs/WI-NEXUS-XXX/`.
- Ledger entries chained for WI-NEXUS-001..006 in `LEDGER.md`.

## Out of scope (follow-ups planned)

- WI-NEXUS-007: wire `execute_with_governance` retry harness into the REPL.
- WI-NEXUS-008: populate `test_case_ids` in preflight output from
  `.specsmith/testcases.json`.
- WI-NEXUS-009: live `l1-nexus` smoke test against the vLLM container.
- WI-NEXUS-010: end-to-end documentation pass for the broker → preflight →
  gated execution flow.

---

🤖 Generated with [Warp](https://app.warp.dev) — agent conversation:
[link](https://app.warp.dev/conversation/6f8aa790-049b-4ddf-9c52-4840728faee5)

Plan artifact: [Warp Agent Implementation Plan](https://app.warp.dev/drive/notebook/rfCwIZUgJPCakjJ2S552DX)

Co-Authored-By: Oz <oz-agent@warp.dev>
