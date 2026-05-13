# Ledger — specsmith

## Archived (32 entries)

*Archived on 2026-05-07*

- ## Archived (3 entries) — —
- ## 2026-04-05T15:25 — specsmith migration: 0.3.0 → 0.3.0a1.dev8 — —
- ## 2026-04-05T15:57 — specsmith migration: 0.3.0a1.dev8 → 0.3.0 — —
- ## Session 2026-04-09 — v0.3.6: VCS awareness, Ollama context, English enforcement hardening — ** Complete
- ## 2026-04-09T08:43 — specsmith migration: 0.3.0 → 0.3.6.dev178 — —
- ## 2026-04-09T16:38 — specsmith migration: 0.3.6 → 0.3.8 — —
- ## Session 2026-04-10 — Architecture research, gap analysis, and roadmap — ** Complete (planning/documentation only — no code changes)
- ## Session 2026-04-10 (cont.) — VS Code plugin fixes, releases, implementation plan — ** Complete
- ## Session 2026-04-20 — AG2 Realignment: Phases 0–3 — ** Complete
- ## Session 2026-04-21/22 — VS Code Extension Overhaul + Critical Fixes — ** Complete
- ## Session 2026-04-22 (cont.) \u2014 Service Mode, Settings Overhaul, Stable Release — ** Complete
- ## 2026-04-27T18:06 — specsmith migration: 0.3.8 → 0.3.13 — —
- ## 2026-04-27T18:07 — Implement Nexus runtime (rename from Warp), fix AG2 executor override warnings, add 12 Nexus REQs/TESTs, add tests/test_nexus.py with 21 passing tests, update ARCHITECTURE.md with Nexus boundary. — —
- ## 2026-04-27T18:14 — WI-NEXUS-002: reconcile machine state JSON (REQ-065..REQ-080), remove stale legacy tests (test_agent.py, test_optimizer.py), add Safe Repository Cleanup boundary + cleanup module + 4 cleanup tests, execute apply cleanup reclaiming 52MB of stale build/cache/archive artifacts. Full suite green: 202 tests pass. — —
- ## 2026-04-27T18:21 — WI-NEXUS-003: add specsmith clean CLI subcommand (REQ-081), add UTF-8 safe console factory and fix Windows cp1252 UnicodeEncodeError in specsmith validate (REQ-082), reconcile machine state to 82 reqs/82 tests, full suite 206 tests pass. — —
- ## 2026-04-27T18:25 — WI-NEXUS-004: rename canonical test-spec governance file from TEST_SPEC.md to TESTS.md across code, docs, ReadTheDocs site, templates, governance, and machine state. Add REQ-083/TEST-083 plus 3 pytest tests guarding against regression. Updated 58 files; full suite green at 209 tests. — —
- ## 2026-04-27T19:09 — WI-NEXUS-005: add Natural-Language Governance Broker (REQ-084). New module specsmith.agent.broker provides classify_intent, infer_scope, run_preflight, narrate_plan, and execute_with_governance. Wired into Nexus REPL as default mode with /why toggle. Hides REQ/TEST/WI tokens by default, bounds retries per REQ-014, escalates with single clarifying question per REQ-063, and never invents governance content. Full suite green: 227 tests pass. — —
- ## 2026-04-27T19:18 — WI-NEXUS-006: specsmith preflight CLI + Nexus REPL execution gating (REQ-085, REQ-086) — —
- ## 2026-04-27T19:28 — WI-NEXUS-007: Wire bounded-retry harness into Nexus REPL (REQ-087) — —
- ## 2026-04-27T19:28 — WI-NEXUS-008: Populate preflight test_case_ids from .specsmith/testcases.json (REQ-088) — —
- ## 2026-04-27T19:28 — WI-NEXUS-009: Live l1-nexus smoke test script + skip-by-default integration test (REQ-089) — —
- ## 2026-04-27T19:28 — WI-NEXUS-010: Documentation pass for Nexus broker, preflight, gate, and harness (REQ-090) — —
- ## 2026-04-27T19:42 — WI-NEXUS-011: Live l1-nexus smoke evidence captured (REQ-095) — —
- ## 2026-04-27T19:42 — WI-NEXUS-012: Structured TaskResult dataclass returned by orchestrator.run_task (REQ-091) — —
- ## 2026-04-27T19:42 — WI-NEXUS-013: /why post-run governance block in REPL (REQ-094) — —
- ## 2026-04-27T19:42 — WI-NEXUS-014: specsmith preflight CLI decision-specific exit codes (REQ-092) — —
- ## 2026-04-27T19:42 — WI-NEXUS-015: Accepted preflight records preflight ledger event (REQ-093) — —
- ## 2026-04-27T19:53 — WI-NEXUS-016: Retry strategy mapping in execute_with_governance (REQ-096) — —
- ## 2026-04-27T19:53 — WI-NEXUS-017: specsmith verify CLI subcommand (REQ-097) — —
- ## 2026-04-27T19:53 — WI-NEXUS-018: Confidence threshold from .specsmith/config.yml (REQ-098) — —
- ## 2026-04-27T19:53 — WI-NEXUS-019: work_proposal ledger event distinct from preflight (REQ-099) — —
- ## 2026-04-27T19:53 — WI-NEXUS-020: Stress-test bridge in preflight CLI (REQ-100) — —

## 2026-04-27T20:20 — WI-NEXUS-021: ruff lint + format baseline clean on develop (REQ-101)
- **Author**: specsmith
- **Type**: baseline
- **REQs affected**: REQ-101
- **Status**: complete
- **Chain hash**: `334a9bbfb434660b...`


## 2026-04-27T20:20 — WI-NEXUS-022: mypy typecheck baseline clean (69 source files) on develop (REQ-102)
- **Author**: specsmith
- **Type**: baseline
- **REQs affected**: REQ-102
- **Status**: complete
- **Chain hash**: `21d93939267d1bd6...`


## 2026-04-27T20:20 — WI-NEXUS-023: CI security baseline upgraded; pip-audit ignore-vuln CVE-2026-3219 documented; no open Dependabot alerts (REQ-103)
- **Author**: specsmith
- **Type**: baseline
- **REQs affected**: REQ-103
- **Status**: complete
- **Chain hash**: `61b8dcb9f748149d...`


## 2026-04-27T20:53 — WI-NEXUS-024: workitems.json synced via scripts/sync_workitems.py - 107 work items mirrored to REQ-001..REQ-107 (REQ-104)
- **Author**: specsmith
- **Type**: sync
- **REQs affected**: REQ-104
- **Status**: complete
- **Chain hash**: `c1e83204390b35e3...`


## 2026-04-27T20:53 — WI-NEXUS-025: live l1-nexus smoke evidence refreshed at .specsmith/runs/WI-NEXUS-011/logs.txt - skip with documented hardware reason (12GB GPU vs ~20GB needed) (REQ-105)
- **Author**: specsmith
- **Type**: evidence
- **REQs affected**: REQ-105
- **Status**: complete
- **Chain hash**: `b375b793d5b016c4...`


## 2026-04-27T20:53 — WI-NEXUS-026: VS Code extension parity - specsmith.runPreflight, specsmith.runVerify, specsmith.toggleWhy commands shipped in specsmith-vscode PR #28 (REQ-106)
- **Author**: specsmith
- **Type**: feature
- **REQs affected**: REQ-106
- **Status**: complete
- **Chain hash**: `68a8ba78f45bb418...`


## 2026-04-27T20:53 — WI-NEXUS-027: ARCHITECTURE.md gained 'Current State (post-WI-NEXUS-023)' section listing realized broker, harness, retry strategies, CI baseline, VS Code parity, smoke evidence, and docs surface (REQ-107)
- **Author**: specsmith
- **Type**: docs
- **REQs affected**: REQ-107
- **Status**: complete
- **Chain hash**: `f2026d5eb9729534...`


## 2026-04-27T20:53 — WI-NEXUS-028: bumped pyproject.toml to 0.4.0; CHANGELOG [Unreleased] -> [0.4.0]; release prep complete (REQ-049, REQ-050)
- **Author**: specsmith
- **Type**: release
- **REQs affected**: REQ-049,REQ-050
- **Status**: complete
- **Chain hash**: `dd0115de0abeff8d...`


## 2026-04-28T09:05 — Nexus 1.0 roadmap groundwork landed (REQ-108..REQ-129): real verifier signal, JSONL chat block protocol (chat/notebook subcommands), persistent session memory, MCP loader, dynamic router, project-rules auto-injection, --predict-only and --comment flags, doctor --onboarding, perf smoke harness, e2e+unit tests, API-stability doc. Pre-1.0; no version bump.
- **Author**: specsmith-agent
- **Type**: feature
- **REQs affected**: REQ-108,REQ-109,REQ-110,REQ-111,REQ-112,REQ-113,REQ-114,REQ-115,REQ-116,REQ-117,REQ-118,REQ-119,REQ-120,REQ-121,REQ-122,REQ-123,REQ-124,REQ-125,REQ-126,REQ-127,REQ-128,REQ-129
- **Status**: complete
- **Chain hash**: `48a8719093e2e87d...`


## 2026-05-07T08:10 — specsmith migration: 0.3.13 → 0.10.1
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `ccc21c85ec4a8807...`


## 2026-05-11T17:45 --- WI-0511: Sprint complete (REQ-248..REQ-262)
- **Author**: oz-agent
- **Type**: feature
- **REQs affected**: REQ-248,REQ-249,REQ-250,REQ-251,REQ-252,REQ-253,REQ-254,REQ-255,REQ-256,REQ-257,REQ-258,REQ-259,REQ-260,REQ-261,REQ-262
- **Status**: complete
- **Chain hash**: auto


## 2026-05-12T13:00 --- WI-0512-AI: Glossa-lab AI patterns ported to specsmith (REQ-263..REQ-281)
- **Author**: oz-agent
- **Type**: feature
- **REQs affected**: REQ-263,REQ-264,REQ-265,REQ-266,REQ-267,REQ-268,REQ-269,REQ-270,REQ-271,REQ-272,REQ-273,REQ-274,REQ-275,REQ-276,REQ-277,REQ-278,REQ-279,REQ-280,REQ-281
- **Description**: Ported 7 AI intelligence systems from glossa-lab: HF Open LLM Leaderboard sync with paginated fetch, bucket scoring (reasoning/conversational/longform), static fallback, and CLI (`model-intel scores/sync/recommendations/connection`); 40+ model capability profiles with context-aware history trimming; LLMClient with O-series parameter translation, vLLM guided-JSON, and provider fallback; EMA-based rate limit scheduler with adaptive concurrency; endpoint preset registry (10+ presets) with `/api/model-intel/*` REST endpoints; `agent suggest-profiles` and `agent endpoint-presets` CLI commands; Kairos AI Providers page bucket score columns and Sync Scores button. ARCHITECTURE.md §21-27 added. 280 REQs, 258 TESTs. All CI green.
- **Status**: complete
- **Chain hash**: auto


## 2026-05-12T13:06 --- WI-0512-GAPS: Arch/req/test gap audit + TEST-282/TEST-283 added (REQ-263, REQ-265)
- **Author**: oz-agent
- **Type**: test
- **REQs affected**: REQ-263,REQ-265
- **Description**: Audit revealed REQ-263 (HF paginated sync persists bucket scores) and REQ-265 (HF API token in Authorization header) lacked explicit pytest coverage. Added TEST-282 (`TestHFSyncPersistsBucketScores` — verifies scores.json created with bucket_scores dict and all required keys per entry) and TEST-283 (`TestHFTokenInHeaders` — verifies token_set flag, rate_limit_tier, and Authorization header capture via mock). Both entries added to docs/TESTS.md. `specsmith sync` updated testcases.json to 260 entries.
- **Status**: complete
- **Chain hash**: auto
