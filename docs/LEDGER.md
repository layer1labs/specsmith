# Ledger — specsmith

## Archived (39 entries)

*Archived on 2026-06-25*

- ## Archived (32 entries) — —
- ## 2026-04-27T20:20 — WI-NEXUS-021: ruff lint + format baseline clean on develop (REQ-101) — —
- ## 2026-04-27T20:20 — WI-NEXUS-022: mypy typecheck baseline clean (69 source files) on develop (REQ-102) — —
- ## 2026-04-27T20:20 — WI-NEXUS-023: CI security baseline upgraded; pip-audit ignore-vuln CVE-2026-3219 documented; no open Dependabot alerts (REQ-103) — —
- ## 2026-04-27T20:53 — WI-NEXUS-024: workitems.json synced via scripts/sync_workitems.py - 107 work items mirrored to REQ-001..REQ-107 (REQ-104) — —
- ## 2026-04-27T20:53 — WI-NEXUS-025: live l1-nexus smoke evidence refreshed at .specsmith/runs/WI-NEXUS-011/logs.txt - skip with documented hardware reason (12GB GPU vs ~20GB needed) (REQ-105) — —
- ## 2026-04-27T20:53 — WI-NEXUS-026: VS Code extension parity - specsmith.runPreflight, specsmith.runVerify, specsmith.toggleWhy commands shipped in specsmith-vscode PR #28 (REQ-106) — —
- ## 2026-04-27T20:53 — WI-NEXUS-027: ARCHITECTURE.md gained 'Current State (post-WI-NEXUS-023)' section listing realized broker, harness, retry strategies, CI baseline, VS Code parity, smoke evidence, and docs surface (REQ-107) — —
- ## 2026-04-27T20:53 — WI-NEXUS-028: bumped pyproject.toml to 0.4.0; CHANGELOG [Unreleased] -> [0.4.0]; release prep complete (REQ-049, REQ-050) — —
- ## 2026-04-28T09:05 — Nexus 1.0 roadmap groundwork landed (REQ-108..REQ-129): real verifier signal, JSONL chat block protocol (chat/notebook subcommands), persistent session memory, MCP loader, dynamic router, project-rules auto-injection, --predict-only and --comment flags, doctor --onboarding, perf smoke harness, e2e+unit tests, API-stability doc. Pre-1.0; no version bump. — —
- ## 2026-05-07T08:10 — specsmith migration: 0.3.13 → 0.10.1 — —
- ## 2026-05-11T17:45 --- WI-0511: Sprint complete (REQ-248..REQ-262) — —
- ## 2026-05-12T13:00 --- WI-0512-AI: Glossa-lab AI patterns ported to specsmith (REQ-263..REQ-281) — —
- ## 2026-05-14T16:00 --- WI-0514c: Phase 2 Token/Context UX — kairos REQ-020/021/022 — —
- ## 2026-05-14T12:42 --- WI-0514b: specsmith issue group + kairos bug report page (REQ-303, REQ-304) — —
- ## 2026-05-14T10:55 --- WI-0514: v0.11.3 release prep (REQ-302) — —
- ## 2026-05-15T14:08 --- WI-0516: EU/NA compliance, governance consolidation, AGENTS.md slim, migration framework — —
- ## 2026-05-15T13:30 --- WI-0515-INFRA: ESDB write layer, CI/CD automation, context orchestration, session persistence, OEA hardening — —
- ## 2026-05-15T12:42 --- WI-0515-GOV: Governance H15–H22 + OEA paper integration — —
- ## 2026-05-12T13:06 --- WI-0512-GAPS: Arch/req/test gap audit + TEST-282/TEST-283 added (REQ-263, REQ-265) — —
- ## 2026-05-17T15:45 — Implemented multi-agent DAG dispatcher (REQ-321..REQ-334): dispatch/ package with TaskDAG/AgentDispatcher/EventEmitter, orchestrator.run_dispatch(), spawner.spawn_worker(), CLI dispatch group, serve.py SSE+REST dispatch endpoints, Kairos Rust dispatch panel (DispatchPanelView, GanttStrip, controls). Added compiler/tool support: run_gcc, run_arm_gcc, run_aarch64_gcc, run_iar_compiler, run_intel_compiler, run_clang_format, run_clang_tidy, run_vsg. — —
- ## 2026-05-17T16:01 — Full traceability sweep: added docs/requirements/dispatch.yml + docs/tests/dispatch.yml (YAML source for REQ-321..334), ran specsmith sync (0 errors, 0 warnings), fixed ARCHITECTURE.md section numbering (duplicate 15/16 corrected), added REQ-313..320 reservation note, updated README.md (dispatch+compiler sections), CHANGELOG.md (v0.11.3-post2), docs/site/commands.md (dispatch group + compiler tools), docs/site/tool-registry.md (agent tools + ROLE_TOOLS). All tests: 777 passed. — —
- ## 2026-05-17T16:12 — Final gap sweep: added apply_diff/search_web/search_repo tool stubs to close ROLE_TOOLS vs AVAILABLE_TOOLS mismatch (23 tools total, no refs missing); added Dispatch to README 50+ CLI Commands section; restored yaml_governance.yml row in ARCHITECTURE.md domain table (REQ-300..312); fixed Kairos post_action to spawn background thread (no UI-thread blocking on retry/abort POST). — —
- ## 2026-05-17T16:31 — Resolved all deferred items: (1) abort mid-LLM-call via _invoke_worker_monitored sub-thread with 0.5s abort polling; (2) CLI dispatch run uses Orchestrator._call_planner when AG2 available (Path A/B fallback); (3) Kairos topological DAG layout with depends_on payload, compute_levels(), bezier edge drawing; (4) REQ-313..320 compliance plan 5939f743 implemented and tested. — —
- ## 2026-05-17T16:53 — Removed all specsmith-vscode / VS Code extension references across specsmith and Kairos docs. Deleted docs/site/vscode-extension.md. Updated mkdocs.yml nav (Kairos Client page). Fixed index.md, quickstart.md, commands.md, getting-started.md, troubleshooting.md, endpoints.md, PRIVACY.md, runner.py, core.py, events.py, suggester.py, languages.py, cli.py, agent.yml REQs/TESTs, README.md. Kairos is now the sole documented client. — —
- ## 2026-05-22T18:53 — KILL SWITCH ACTIVATED: emergency stop — —
- ## 2026-05-24T09:55 — specsmith migration: 0.11.3.dev420 → 0.11.6 — —
- ## 2026-05-24T11:08 — specsmith migration: 0.11.6 → 0.11.7 — —
- ## 2026-06-11T20:45 — specsmith migration: 0.11.7 → 0.13.0 — —
- ## 2026-06-11T20:45 — KILL SWITCH ACTIVATED: emergency stop — —
- ## 2026-06-11T22:22 — specsmith migration: 0.14.0 → 0.13.0 — —
- ## 2026-06-14T14:00 — KILL SWITCH ACTIVATED: emergency stop — —
- ## 2026-06-14T19:51 — KILL SWITCH ACTIVATED: emergency stop — —
- ## 2026-06-14T22:42 — KILL SWITCH ACTIVATED: emergency stop — —
- ## 2026-06-14T22:42 — specsmith migration: 0.14.1 → 0.15.3 — —
- ## 2026-06-14T23:08 — KILL SWITCH ACTIVATED: emergency stop — —
- ## 2026-06-15T11:08 — KILL SWITCH ACTIVATED: emergency stop — —
- ## 2026-06-22T07:41 — KILL SWITCH ACTIVATED: emergency stop — —
- ## 2026-06-23T14:00 — KILL SWITCH ACTIVATED: emergency stop — —

## 2026-06-23T14:05 — specsmith migration: 0.16.0 → 0.16.2
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `ffa59e79424ae198...`


## 2026-06-24T12:29 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `106b11e4e66d5a38...`


## 2026-06-24T21:26 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `303499039d2651b9...`


## 2026-06-24T22:10 — specsmith migration: 0.16.2 → 0.16.5
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `4cd715ea85f416ce...`


## 2026-06-24T22:12 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `80b7af3000e19013...`


## 2026-06-24T22:36 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `ed801f6f42ba86ed...`


## 2026-06-25T04:00 — WI-BEAADF17: YAML-first governance, ESDB auto-promotion, BA Interview, cleanup (REQ-371–REQ-379)
- **Author**: oz-agent
- **Type**: feature
- **REQs affected**: REQ-371,REQ-372,REQ-373,REQ-374,REQ-375,REQ-376,REQ-377,REQ-378,REQ-379
- **Status**: complete
- **Chain hash**: auto
- **Description**: Major YAML-first governance and epistemic architecture sprint:

  **YAML-first mode (REQ-373, REQ-378)**: `scaffold_project()` now writes `.specsmith/governance-mode=yaml`
  and creates `docs/requirements/core.yml` + `docs/tests/core.yml` starter files so all new projects
  are in YAML-first mode from day one. Markdown mode remains supported but emits a `DeprecationWarning`
  and auto-triggers m007 migration.

  **m007 migration**: `src/specsmith/migrations/m007_yaml_first.py` converts REQUIREMENTS.md/TESTS.md
  to YAML source files. Idempotent and non-destructive (MD files not deleted).

  **ESDB auto-promotion (REQ-371)**: `esdb/__init__.py` adds `_maybe_promote_sqlite_to_chrono()` that
  prompts to migrate SQLite records into ChronoStore when ChronoStore is empty. Auto-accepts in
  non-interactive/agent mode.

  **`specsmith esdb switch-backend` (REQ-372)**: New `esdb` subcommand migrates records between
  SQLite and ChronoStore. `--to sqlite` requires `--confirm-data-loss`.

  **`specsmith cleanup` (REQ-374)**: New top-level command removes runtime cache dirs (runs, sessions,
  chat, perf, recovery, logs, dispatch, pids, agent-reports, migration-backups, chronomemory/backup,
  Python caches). Dry-run by default, `--apply` to delete, `--json` for machine output. Protected
  files (requirements.json, testcases.json, governance-mode, docs/) never removed.

  **Epistemic BA Interview (REQ-375–377)**: `src/specsmith/architect.py` gains `run_interview()`,
  `run_gap_analysis()`, `run_arch_update()`. Tracks 9 architectural dimensions with confidence scoring.
  CLI: `specsmith architect interview/gap/update`. SKILL.md created at
  `.agents/skills/specsmith-architect/SKILL.md`.

  **Auditor mode-aware (REQ-379)**: yaml-requirements-dir/yaml-tests-dir checks now only fail for
  projects in YAML mode; legacy markdown-mode projects get an informational pass.

  **Test coverage**: 4 new test files: test_markdown_deprecation.py, test_esdb_backend_switch.py,
  test_cleanup_cmd.py, test_architect_interview.py (116 new tests). All 1347 tests pass.
  ruff: zero violations. specsmith audit: Healthy.


## 2026-06-25T07:39 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `6e3248c993d07e12...`


## 2026-06-25T08:51 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `e0d0855229c3ad17...`


## 2026-06-25T09:05 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `1c187a5124c9f25e...`

## 2026-06-25T14:09 — specsmith migration: 0.17.0 → 0.2.6.dev591
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `d1731eab603f6f26...`

## 2026-06-25T14:09 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `b67602aceddb8387...`

## 2026-06-25T14:16 — specsmith migration: 0.2.6.dev591 → 0.17.0
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `a5fba06634f05138...`

## 2026-06-25T14:58 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `dc451c3e0c2ef776...`

## 2026-06-25T19:57 — ESDB Full Coverage: docs/ARCHITECTURE.md §19 record kinds table + §41 appended; chronomemory-esdb skill updated with write-path table, record kinds, M008 note; all ruff violations fixed; 15/15 tests pass
- **Author**: agent
- **Type**: task
- **Status**: complete
- **Chain hash**: `1e9d9f99eb4f4088...`

## 2026-06-25T20:44 — wi_archive WI-C6FAA737: ESDB full coverage implemented and verified: TEST-404..411 and tests in test_esdb_writer.py + test_esdb_integration.py cover REQ-395..402.
- **Author**: specsmith
- **Type**: wi_archive
- **Status**: complete
- **Chain hash**: `0ca9ac14a5f3fcbd...`

## 2026-06-25T21:12 — wi_close WI-9A9A9E22: REQ-084 implemented: governance_logic.run_preflight delegates from CLI; 1885 tests passing.
- **Author**: specsmith
- **Type**: wi_close
- **Status**: complete
- **Chain hash**: `7cbe46a5cf3b7756...`

## 2026-06-25T21:12 — wi_close WI-B6A6E24A: REQ-085 implemented: pipx install-origin guard active; SPECSMITH_ALLOW_NON_PIPX override for CI.
- **Author**: specsmith
- **Type**: wi_close
- **Status**: complete
- **Chain hash**: `1f4fc87febc37b92...`

## 2026-06-25T21:12 — wi_close WI-BEAADF17: REQ-371..374 implemented: ESDB auto-promotion, switch-backend, m007 YAML migration, cleanup command all present and tested.
- **Author**: specsmith
- **Type**: wi_close
- **Status**: complete
- **Chain hash**: `531f877f5d72b2f9...`

## 2026-06-26T10:36 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `ace65defe939991d...`
