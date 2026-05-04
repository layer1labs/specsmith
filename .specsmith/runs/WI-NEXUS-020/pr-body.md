# feat(nexus): retry strategies, verify CLI, config threshold, work_proposal, stress bridge

Closes the second half of the broker contract and tightens preflight to the
existing AEE epistemic infrastructure. **Suite: 259 passing, 1 skipped
(`NEXUS_LIVE`).**

## Work items in this PR

- **WI-NEXUS-016 (REQ-096)** — `broker.execute_with_governance` now classifies
  exhausted-budget failures against the canonical retry strategies defined by
  REQ-028: `narrow_scope`, `expand_scope`, `fix_tests`, `rollback`, `stop`. The
  result is exposed on `RunResult.strategy` and surfaced in the clarifying
  question so the user gets one concrete next-action label.
- **WI-NEXUS-017 (REQ-097)** — New `specsmith verify` CLI subcommand consumes
  the REQ-027 verification input contract (file diffs, test results, logs,
  changed files) via `--stdin` or `--diff/--tests/--logs/--changed` flags.
  Emits a JSON object with `equilibrium`, `confidence`, `summary`,
  `files_changed`, `test_results`, and `retry_strategy`. Exit codes: 0 on
  equilibrium, 2 when retry is recommended, 3 on stop-and-align.
- **WI-NEXUS-018 (REQ-098)** — `specsmith preflight` reads
  `epistemic.confidence_threshold` from `.specsmith/config.yml` and uses it as
  the floor for the JSON `confidence_target`. Falls back to the heuristic
  default when the file is absent or unparseable.
- **WI-NEXUS-019 (REQ-099)** — Accepted preflight now emits a distinct
  `work_proposal` ledger event (tagged with REQ-044, REQ-085, and matched
  requirement ids) when the assigned `work_item_id` is brand-new. A pre-write
  snapshot of `LEDGER.md` ensures the proposal is never skipped because the
  preflight event itself contains the new id.
- **WI-NEXUS-020 (REQ-100)** — `specsmith preflight --stress` runs the AEE
  `StressTester` over matched requirements and surfaces critical failures as
  `stress_warnings` in the JSON payload. Verbose narration mentions the
  warning. The flag defaults off so unrelated tests stay green.

## Verification

- `py scripts/sync_governance_state.py` → 100 requirements / 100 test cases.
- `py -m pytest -q` → **259 passed, 1 skipped** in ≈15s.
- Cumulative diff and pytest log: `.specsmith/runs/WI-NEXUS-020/`.
- Five new ledger entries chained for WI-NEXUS-016..020.

## Notes for reviewers

- The verify CLI's heuristic confidence (0.85 on equilibrium, 0.4 partial) is
  documented as a placeholder for a real verifier; the retry-strategy mapping
  is fully deterministic and shared with `execute_with_governance`.
- The `_stress_test_warnings` helper is best-effort — any error in the AEE
  stress-tester is swallowed and `stress_warnings` is simply omitted.
- All new ledger writes are wrapped in `try/except` so ledger errors never
  block the CLI.

