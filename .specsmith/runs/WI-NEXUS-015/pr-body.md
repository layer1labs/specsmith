# feat(nexus): TaskResult, preflight exit codes, ledger event, /why post-run, smoke evidence

Tightens the **Nexus** ↔ **Specsmith** contract that landed in PR #72. Five
follow-up work items, all governed by Specsmith and verified by pytest.
**Suite: 247 passing, 1 skipped (live l1-nexus integration test).**

## Work items in this PR

- **WI-NEXUS-011 (REQ-095)** — Captured live `l1-nexus` smoke evidence at
  `.specsmith/runs/WI-NEXUS-011/logs.txt`. The smoke script ran offline and
  returned a structured `ok=false` transport error; the log includes a
  reproducible note describing how to re-run it against a live container.
- **WI-NEXUS-012 (REQ-091)** — `orchestrator.run_task` now returns a
  `TaskResult` dataclass (`equilibrium`, `confidence`, `summary`,
  `files_changed`, `test_results`). The Nexus REPL's bounded-retry harness
  consumes it directly instead of synthesizing equilibrium from
  `bool(summary)`. Adds a tolerant parser for the existing Nexus output
  contract (Plan/Commands/Files changed/Diff/Test results/Next action).
- **WI-NEXUS-013 (REQ-094)** — Nexus REPL emits a `[/why]` post-run
  governance block when `verbose_governance` is on, listing the assigned
  `work_item_id`, matched `requirement_ids`/`test_case_ids`, post-run
  `confidence`, and harness `equilibrium`.
- **WI-NEXUS-014 (REQ-092)** — `specsmith preflight` exits `0` for
  `accepted`, `2` for `needs_clarification`, and `3` for
  `blocked`/`rejected`. The JSON payload continues to print on stdout for
  every exit code so CI pipelines can branch on intent without re-parsing.
- **WI-NEXUS-015 (REQ-093)** — Every accepted `specsmith preflight` invocation
  appends a `preflight` ledger event tagged with `REQ-085` plus the matched
  `requirement_ids`, recording the utterance, assigned `work_item_id`, and
  `confidence_target`. Non-accepted decisions never touch the ledger.

## Verification

- `py scripts/sync_governance_state.py` → 95 requirements / 95 test cases.
- `py -m pytest -q` → **247 passed, 1 skipped** (≈17s; the skip is the
  `NEXUS_LIVE=1`-gated integration test).
- Smoke evidence: `.specsmith/runs/WI-NEXUS-011/logs.txt`.
- Cumulative diff + final pytest log: `.specsmith/runs/WI-NEXUS-015/`.
- Five new ledger entries chained for WI-NEXUS-011..015.

## Notes for reviewers

- The post-run `[/why]` block is gated entirely behind the existing `/why`
  toggle; default REPL behavior remains plain English with no governance
  identifiers leaking to the user.
- The orchestrator's heuristic confidence (0.85 on full contract, 0.4
  partial) is documented as a placeholder for a real verifier signal; the
  retry harness already honors whatever value the executor returns.
- The preflight ledger writer is best-effort — ledger errors never block
  the CLI from emitting its JSON or returning its exit code.

---

🤖 Generated with [Warp](https://app.warp.dev) — agent conversation:
[link](https://app.warp.dev/conversation/6f8aa790-049b-4ddf-9c52-4840728faee5)

Plan artifact: [Warp Agent Implementation Plan](https://app.warp.dev/drive/notebook/rfCwIZUgJPCakjJ2S552DX)

Co-Authored-By: Oz <oz-agent@warp.dev>
