# Ledger — specsmith

## Archived (3 entries)

*Archived on 2026-04-23*

- ## Session 2026-04-01 — Initial CLI implementation — ** Complete
- ## Session 2026-04-05 — AEE epistemic layer, agentic client, CI/CD, meta-governance — ** Complete
- ## Session 2026-04-02 — v0.2.0→v0.2.2 release cycle — ** Complete

## 2026-04-05T15:25 — specsmith migration: 0.3.0 → 0.3.0a1.dev8
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `5a6995207163ba49...`


## 2026-04-05T15:57 — specsmith migration: 0.3.0a1.dev8 → 0.3.0
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `30255640fa4f54c2...`

---


## Session 2026-04-09 — v0.3.6: VCS awareness, Ollama context, English enforcement hardening

**Status:** Complete
**Branch:** main
**Release:** v0.3.6 (stable)

### What changed

**VCS state awareness at session start:**
- `build_system_prompt()`: runs `git status --short` + `git log --oneline -5` at session
  creation and embeds the snapshot in the system prompt. Agent knows working-tree state
  immediately without running tools.
- `start` quick command rewritten: explicitly steps through git status, git log, AGENTS.md,
  LEDGER.md; summarizes in 3–4 sentences; proposes next action.

**Ollama context reliability:**
- `keep_alive: -1` added to all three `/api/chat` call paths (complete, complete-with-tools,
  stream). Prevents model unloading between turns, eliminating context loss on slow sessions.

**Agent continuity and language fixes:**
- CONTINUITY RULE added to system prompt: agent must reference prior findings when user
  sends a follow-up; “I’m not sure what you’re referring to” is a CRITICAL FAILURE.
- `llm_chunk` event deferred in json_events mode until after `_has_non_english()` check.
  Non-English responses are now silently corrected before the UI ever renders them.
- Non-English correction fires on any iteration (not just iteration 0).
- Non-English partial text before tool calls is silently dropped.

**Windows fixes:**
- `subprocess.run` in `tools.py` forces `encoding='utf-8'` and `errors='replace'`.
  Fixes `UnicodeDecodeError` (cp1252) on Windows audit/doctor commands.

### Verification
- ruff check + format: clean
- All CI workflows green
- v0.3.6 tagged and released to PyPI

### Open TODOs
- [ ] Add action button in VS Code session chat when agent finds a fixable issue
- [ ] Add VCS status live refresh (currently only at session start)


## 2026-04-09T08:43 — specsmith migration: 0.3.0 → 0.3.6.dev178
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `45890fddd2d61233...`


## 2026-04-09T16:38 — specsmith migration: 0.3.6 → 0.3.8
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `c6cbccdf4558bd52...`

---


## Session 2026-04-10 — Architecture research, gap analysis, and roadmap

**Status:** Complete (planning/documentation only — no code changes)
**Branch:** main

### Scope

Extensive research and gap analysis session to bring specsmith architecture to full parity with the state-of-the-art AI agent harness ecosystem. Sources researched: ECC, Claude Code (including the March 2026 source map leak), OpenClaw, NanoClaw, Theia AI, Anthropic eval harness documentation, and modern multi-agent orchestration frameworks.

### Key findings from code audit

- `executor.py` is PID/process tracking only — NOT a typed operation layer. All tool handlers still use raw shell strings.
- `commands/__init__.py` is completely empty despite the package existing.
- Only 3 bundled agent profiles (planner, verifier, epistemic-auditor).
- `retrieval.py` uses term-frequency scoring, not BM25.
- The OpenAI provider already accepts `base_url` — no new provider class needed for Jan/LM Studio/vLLM/llama.cpp.
- No multi-agent spawning, no orchestrator, no instinct system, no eval harness, no service daemon.

### Key research findings

**Claude Code leaked architecture (March 31, 2026 source map):**
- `AgentTool` is the single tool that spawns all subagents. Parent picks model tier per task at spawn time.
- Team spawning uses tmux panes + filesystem mailbox (`.claude/teams/{team}/mailbox/{agent}.json`). No message broker needed.
- Agent Teams (Feb 2026, Opus 4.6): peer-to-peer via `SendMessage`; ~7x token cost.
- 44 feature flags gate tool schema visibility — model cannot call gated tools it has never seen.
- KAIROS daemon mode: monitors GitHub webhooks, runs tasks from queue, uses worktree isolation.
- Subagents are for research (read-only); implementation stays in the parent session.

**Theia AI (Jan 2026, Theia 1.68+):**
- Agent Skills (SKILL.md + `{{skills}}` variable), ShellExecutionTool, custom agents via YAML, agent memory directories, MCP support, Change Sets — all shipped.
- `specsmith-ide` build is now writing Theia extensions, not building LLM infrastructure from scratch.

**Eval harness best practices (Anthropic, Jan 2026):**
- EDD: define evals before coding. Task/Trial/Grader/Transcript/Outcome/Harness terminology.
- Three grader types: CodeGrader (deterministic), ModelGrader (LLM-as-judge), HumanFlag.
- pass@k (capability ceiling) vs pass^k (reliability floor).
- Grade outcomes (git state + test results), not execution paths.

### Decisions made

- Implement typed `ProjectOperations` class first — prerequisite for everything else.
- Use filesystem mailbox (JSON files on disk) for all inter-agent communication — no message broker.
- Feature flags remove tool schemas from LLM calls — not just block at execution time.
- EventSink protocol abstracts stdout vs WebSocket emission — existing event schema unchanged.
- Orchestrator runs on small local Ollama model — never spend cloud credits on routing.
- Theia AI is the IDE foundation — specsmith-ide writes Theia extensions, not LLM infrastructure.
- Grade outcomes not paths in all specsmith evals.

### Changes made this session

- `docs/REQUIREMENTS.md` — 15 new requirement domains (OPS, CMD, MAS, ORC, FLG, LRN, EDD, MEM, HRK, SRV, RTR, LPR, MCP, SEC, IDE) with 60+ formal requirements
- `docs/ARCHITECTURE.md` — Added "Planned Architecture Evolution" section covering all new components, multi-agent patterns, eval design, and architecture invariants
- `AGENTS.md` — Added planned commands, planned file registry entries, updated tech stack
- Architecture plan document updated in Warp Oz with full gap analysis and 16-workstream roadmap

### Open TODOs (Phase 1 — next immediate actions)

- [ ] Implement `src/specsmith/operations.py` — typed `ProjectOperations` class
- [ ] Refactor tool handlers in `agent/tools.py` to use `ProjectOperations`
- [ ] Populate `src/specsmith/commands/` with priority slash commands
- [ ] Implement `src/specsmith/instinct.py` — instinct persistence
- [ ] Implement `src/specsmith/eval/` — EDD harness with pass@k
- [ ] Expose `--base-url` in `specsmith run` CLI
- [ ] Upgrade `retrieval.py` to BM25 with `rank_bm25`

### Next step
Begin Phase 1: `operations.py` first (it blocks tool handler refactoring), then commands surface, then instinct and eval systems. Each phase should have eval coverage before moving to the next.

---


## Session 2026-04-10 (cont.) — VS Code plugin fixes, releases, implementation plan

**Status:** Complete
**Branch:** develop (both repos)

### What changed

**specsmith (Python CLI):**
- v0.3.10 released to PyPI — no-placeholder-requirements rule in system prompt (#69)
- Architecture roadmap merged from main → develop (ARCHITECTURE.md, REQUIREMENTS.md, AGENTS.md, LEDGER.md)
- Implementation plan created covering all 3 phases (10 workstreams)

**specsmith-vscode (VS Code extension):**
- v0.3.13 released — Ollama startup update check (#14), model digest column (#15), develop branch + gitflow (#16)
- v0.3.13-dev.1 dev release — 6 bug fixes in single commit:
  - #17 CRITICAL: GovernancePanel._getSpecsmithTerminal() infinite recursion → fixed (createTerminal)
  - #18: Report Bug button delegates to LLM → fixed (routes to interactive BugReporter)
  - #19: Auto-approve still asks questions → fixed (system prompt injection + immediate fire)
  - #20: tools install --list fails → fixed (skip --project-dir for unsupported commands)
  - #21: Ollama model list mismatch → fixed (exact then base-tag matching + download progress)
  - #22: Auto-accept toggle in Project Settings → added (checkbox in Execution tab, saved to scaffold.yml)

### Verification
- specsmith: CI green on main and develop, PyPI v0.3.10 published
- specsmith-vscode: CI + Dev Release green on develop, v0.3.13 stable on main
- Both repos: develop and main in sync, zero failing workflows

### Open TODOs (Phase 1 — next)
- [x] Implement `src/specsmith/operations.py` — typed ProjectOperations class → replaced by AG2 tool surface
- [x] Refactor tool handlers in `agent/tools.py` → AG2 agents/tools/ replaces this
- [ ] Populate `src/specsmith/commands/` with priority slash commands
- [ ] Implement `src/specsmith/instinct.py` — instinct persistence
- [ ] Implement `src/specsmith/eval/` — EDD harness with pass@k
- [ ] Merge specsmith-vscode develop → main, tag v0.3.14 stable

---


## Session 2026-04-20 — AG2 Realignment: Phases 0–3

**Status:** Complete
**Branch:** develop
**AG2 version:** 0.12.0
**Ollama model:** qwen2.5:14b

### What changed

**AG2 Realignment — new architecture direction:**
Replaced the previous incremental roadmap with an AG2-based agent shell over Ollama.
Four-layer architecture: Product Surface → Agent Layer (AG2) → Model Runtime (Ollama) → Verification Layer.
Three agent roles: Planner (read-only inspection + planning), Builder (code/doc changes), Verifier (tests + accept/reject).

**Phase 0 — Baseline Audit (docs/baseline-audit.md):**
- Architecture map: 4 entrypoints (CLI, REPL, GUI, VS Code), service boundaries, provider assumptions
- Test inventory: 208 pass / 18 fail (stale pip install), ruff clean, mypy clean
- Gap analysis: 10 ranked gaps (no agent tests, empty commands/, raw subprocess tools)
- AGENTS.md: updated with AG2 four-layer architecture, 12 project rules

**Phase 1 — System Proof (docs/system-proof.md):**
- Root cause of 18 failures: stale v0.3.1 pip install vs v0.3.10 source → reinstall fixed all
- tests/conftest.py: WinError 448 pytest cleanup crash fix for Windows
- tests/test_agent.py: 23 new tests — tool registry (5), tool handlers (5), system prompt (3), AgentRunner init (2), SessionState (2), meta-commands (2), Ollama integration (4)
- 249 tests passing, lint clean, mypy clean

**Phase 2 — AG2 Agent Shell (src/specsmith/agents/):**
- agents/config.py: AgentConfig from scaffold.yml, AG2 LLMConfig dict generation
- agents/tools/filesystem.py: read_file, write_file, patch_file, list_tree, search_content (pathlib)
- agents/tools/shell.py: run_project_command (structured exit code + output)
- agents/tools/git.py: git_status, git_diff, git_changed_files, git_branch_info
- agents/tools/tests.py: run_unit_tests, summarize_failures
- agents/roles.py: Planner/Builder/Verifier via AG2 ConversableAgent + Ollama
- agents/cli.py: specsmith agent run/plan/status/verify commands
- cli.py: agent command group wired into main CLI
- pyproject.toml: ag2[ollama] optional dependency added
- Tested live: Planner calls tools via Ollama, full Plan→Build→Verify pipeline works

**Phase 3 — Self-Improvement Loop:**
- agents/workflows/improve.py: run_improvement() — inspect → plan → edit → test → report
- agents/reports.py: ChangeReport dataclass, save/list at .specsmith/agent-reports/
- agents/cli.py: specsmith agent improve <task>, specsmith agent reports

### Verification
- 249 tests passing (226 existing + 23 new agent tests)
- ruff check: clean across all agents/ code
- mypy: 0 errors in 72 source files
- AG2 + Ollama live tested: plan, run, and full pipeline all execute successfully
- Ollama tool calling proven with qwen2.5:14b (text completion + tool calling + provider protocol)

### Files changed (11 new + 5 modified)
- New: src/specsmith/agents/__init__.py, config.py, roles.py, cli.py, reports.py
- New: src/specsmith/agents/tools/__init__.py, filesystem.py, shell.py, git.py, tests.py
- New: src/specsmith/agents/workflows/__init__.py, improve.py
- New: tests/conftest.py, tests/test_agent.py
- New: docs/baseline-audit.md, docs/system-proof.md
- Modified: AGENTS.md, pyproject.toml, src/specsmith/cli.py

### Open TODOs
- [ ] Phase 4.1: Feature flags (REQ-FLG-001–003)
- [ ] Phase 4.2: Instinct/learning system (REQ-LRN-001–007)
- [ ] Phase 4.3: Eval harness (REQ-EDD-001–008)
- [ ] Phase 4.4: Agent memory persistence (REQ-MEM-001–004)
- [ ] Phase 4.5: Multi-agent coordination via AG2 GroupChat
- [ ] Phase 4.6: Server daemon (specsmith serve)
- [ ] Phase 4.7: Theia IDE (specsmith-ide repo)
- [ ] Populate src/specsmith/commands/ with slash commands
- [ ] Merge specsmith-vscode develop → main, tag v0.3.14 stable

### Next step
specsmith can now improve itself via `specsmith agent improve <task>`. Use it for Phase 4 tasks (feature flags, instinct, eval harness). Review changes before committing.

---


## Session 2026-04-21/22 — VS Code Extension Overhaul + Critical Fixes

**Status:** Complete
**Branch:** develop (both repos)

### What changed

**specsmith (Python CLI):**
- Ollama timeout: 120s → 600s completion, 300s streaming (fixed frequent timeouts)
- AgentConfig: effective_utility_model, effective_max_iterations (0=unlimited)
- Model recommendation: qwen2.5:14b as default agent model (not 7b coder)
- pip install -e after every code change

**specsmith-vscode (VS Code extension) — MAJOR OVERHAUL:**

*Architecture realignment:*
- Project ≠ Session: GovernancePanel decoupled from SessionPanel
- ⚙ on project row opens Project Settings without needing a session
- GovernancePanel stays open when sessions close
- Multiple sessions per project supported
- Renamed "specsmith Settings" → "Global Settings"
- Project name in tab title: "⚙ Project Settings (specsmith)"
- Removed duplicate settings buttons from sidebar menus

*New features:*
- Agent tab in Project Settings: per-project provider/model/context/iteration config
- Ollama model catalog: 16 models across 4 tiers (Tiny/Balanced/Capable/Powerful)
- Filter buttons: All / Installed / Available / ⭐ Recommended
- GPU-aware model recommendation (qwen2.5:14b for ≥8GB, coder:7b for 4GB, CPU fallback)
- ✔ DEFAULT indicator per model (replaces confusing ⭐ star)
- Model cards: name, size, VRAM, ctx, best-for, install status, pull/remove buttons
- Sorted: default → installed → fits GPU → needs more VRAM
- Conditional buttons: Update/Upgrade only shown when newer version available
- "Free (local)" cost display for Ollama provider
- View Full button for truncated errors/tool outputs
- Bridge timeout: 5min warn + 15min kill (was 5min kill)
- Governance auto-fix on session start
- Phase dropdown dark mode fix

*CRITICAL BUG FIXES:*
- **SessionPanel webview JS extracted to media/session.js** — the entire 462-line
  webview script was embedded in a TypeScript template literal. esbuild mangled
  escaped backticks (\`) and variable references (\${var}), crashing the browser
  JS parser and killing ALL chat functionality (Enter, Send, models, buttons).
  Fix: external .js file that esbuild doesn't touch.
- **SettingsPanel INST_VER variable mangled by esbuild** — same root cause.
  Fix: pass version via data-* attribute, read from DOM.
- **GovernancePanel LANGUAGES/FPGA_TOOLS mangled** — same root cause.
  Fix: pass via JSON script tags, parse from DOM.
- **All onclick quote escaping** — \\' in template literals became '' (empty).
  Fix: use &#39; HTML entities.
- **Model dropdown empty** — _refreshModels now always sends static fallback
  if live fetch fails or returns empty.
- **CSP blocking external session.js** — script-src needed both 'unsafe-inline'
  AND vscode-resource origins.

### Verification
- specsmith: 249 tests pass, ruff clean
- specsmith-vscode: lint clean, build clean
- GovernancePanel webview: Node syntax check PASSED
- SettingsPanel webview: Node syntax check PASSED
- SessionPanel (media/session.js): Node syntax check PASSED
- Chat session: loads, Enter sends, models populate, tools execute

### Open TODOs
- [ ] Agent tab: populate model dropdown from provider API
- [ ] Agent tab: pre-fill defaults from Global Settings
- [ ] Interactive architecture/requirements gap fixing
- [ ] Agent task visualization panel
- [ ] GPU support: AMD ROCm, Apple M, Intel Arc, CPU fallback detection
- [ ] Phase 4: feature flags, instinct, eval, memory, multi-agent, Theia

---


## Session 2026-04-22 (cont.) \u2014 Service Mode, Settings Overhaul, Stable Release

**Status:** Complete
**Branch:** develop \u2192 main
**Releases:** specsmith v0.3.13, specsmith-vscode v0.3.15

### What changed

**specsmith (Python CLI):**
- `specsmith serve --port 8421` \u2014 persistent HTTP server (stdlib, zero deps).
  SSE event stream, POST /api/send, GET /api/status. Keeps Python + Ollama warm.
- EXEC-001 rule in agent system prompt (no python -c for non-trivial code)
- Supplementary rules audit (check_supplementary_rules in auditor.py)
- Minimal startup protocol \u2014 no tools, no audit, just greeting
- Broader JSON filtering (suppress structured status/action JSON from LLM)
- Version bumped to 0.3.13 for pre-release channel
- CI fixes: ruff lint/format, mypy type errors, conftest.py SIM105

**specsmith-vscode (VS Code extension):**
- **Service mode**: Ollama keep-alive pings (3min), ProcessPool (10min idle),
  HTTP client auto-detects specsmith serve on localhost:8421
- **Platform-agnostic operations**: all pip/Ollama ops use cp.spawn (no shell).
  Removed all PowerShell/bash-specific code.
- **Settings panel overhaul**:
  - Version marker file (.specsmith-version) for instant version detection
  - Smart install tracking: polls version, inline Restart button
  - Channel switch: auto-check, show Install button for any version difference
  - Ollama upgrade: downloads OllamaSetup.exe via Node https, runs /SILENT
  - Update banner: shows both specsmith + Ollama updates with tab links
  - Auto-check on every panel reveal
  - Ollama tab matches specsmith UI (Check/Install/Last check)
- **Session panel**:
  - Tool-call JSON regression fixed (filter raw JSON from llm_chunk)
  - Startup busy state (setBusy(true) on ready, cleared by turn_done)
  - Accept All only after 2+ proposals
  - VCS bar: +additions (green) / -deletions (red), merged token stats
  - Governance check shows Fix Now / Skip proposal buttons
  - Broader proposal detection (i recommend, i suggest, etc.)
  - Removed chat spam (VCS state, starting session messages)
- **Bug fixes**:
  - SettingsPanel esbuild regression (\\' \u2192 &#39; in onclick)
  - _parseVer NaN for .devN builds (parseInt('dev') \u2192 parseInt(m[5]))
  - pip downgrade from pre-release (--force-reinstall)
  - Stale version marker invalidation
  - Corrupted pip temp dir cleanup (~pecsmith)
  - spawn EPERM/EBUSY handling
  - Mocha upgraded to 11.3.0 (jsdiff DoS fix)

### Verification
- specsmith: 249 tests pass, ruff clean, mypy clean, CI green
- specsmith-vscode: 23 tests pass, tsc clean, esbuild clean, CI green
- 0 open issues on both repos
- Pre-release 0.3.13.dev215 published to PyPI

### Next step
Phase 4: feature flags, instinct/learning, eval harness, agent memory, multi-agent coordination via AG2 GroupChat.

## 2026-04-27T18:06 — specsmith migration: 0.3.8 → 0.3.13
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `5201f75f6e54933f...`

## 2026-04-27T18:07 — Implement Nexus runtime (rename from Warp), fix AG2 executor override warnings, add 12 Nexus REQs/TESTs, add tests/test_nexus.py with 21 passing tests, update ARCHITECTURE.md with Nexus boundary.
- **Author**: Tristen Pierson <tpierson@bitconcepts.tech>
- **Type**: feature
- **REQs affected**: REQ-065,REQ-066,REQ-067,REQ-068,REQ-069,REQ-070,REQ-071,REQ-072,REQ-073,REQ-074,REQ-075,REQ-076
- **Status**: complete
- **Chain hash**: `ff611e6a7ac0ca62...`

## 2026-04-27T18:14 — WI-NEXUS-002: reconcile machine state JSON (REQ-065..REQ-080), remove stale legacy tests (test_agent.py, test_optimizer.py), add Safe Repository Cleanup boundary + cleanup module + 4 cleanup tests, execute apply cleanup reclaiming 52MB of stale build/cache/archive artifacts. Full suite green: 202 tests pass.
- **Author**: Tristen Pierson <tpierson@bitconcepts.tech>
- **Type**: feature
- **REQs affected**: REQ-003,REQ-077,REQ-078,REQ-079,REQ-080
- **Status**: complete
- **Chain hash**: `176531aa559ed8de...`

## 2026-04-27T18:21 — WI-NEXUS-003: add specsmith clean CLI subcommand (REQ-081), add UTF-8 safe console factory and fix Windows cp1252 UnicodeEncodeError in specsmith validate (REQ-082), reconcile machine state to 82 reqs/82 tests, full suite 206 tests pass.
- **Author**: Tristen Pierson <tpierson@bitconcepts.tech>
- **Type**: feature
- **REQs affected**: REQ-081,REQ-082
- **Status**: complete
- **Chain hash**: `ac851adc0fd1aca7...`

## 2026-04-27T18:25 — WI-NEXUS-004: rename canonical test-spec governance file from TEST_SPEC.md to TESTS.md across code, docs, ReadTheDocs site, templates, governance, and machine state. Add REQ-083/TEST-083 plus 3 pytest tests guarding against regression. Updated 58 files; full suite green at 209 tests.
- **Author**: Tristen Pierson <tpierson@bitconcepts.tech>
- **Type**: feature
- **REQs affected**: REQ-002,REQ-083
- **Status**: complete
- **Chain hash**: `e24fb649a8ef5ce1...`

## 2026-04-27T19:09 — WI-NEXUS-005: add Natural-Language Governance Broker (REQ-084). New module specsmith.agent.broker provides classify_intent, infer_scope, run_preflight, narrate_plan, and execute_with_governance. Wired into Nexus REPL as default mode with /why toggle. Hides REQ/TEST/WI tokens by default, bounds retries per REQ-014, escalates with single clarifying question per REQ-063, and never invents governance content. Full suite green: 227 tests pass.
- **Author**: Tristen Pierson <tpierson@bitconcepts.tech>
- **Type**: feature
- **REQs affected**: REQ-014,REQ-063,REQ-084
- **Status**: complete
- **Chain hash**: `050373fa73b9b15f...`

## 2026-04-27T19:18 — WI-NEXUS-006: specsmith preflight CLI + Nexus REPL execution gating (REQ-085, REQ-086)
- **Author**: agent
- **Type**: feature
- **REQs affected**: REQ-085,REQ-086
- **Status**: complete
- **Chain hash**: `cdc3fb4815489052...`

## 2026-04-27T19:28 — WI-NEXUS-007: Wire bounded-retry harness into Nexus REPL (REQ-087)
- **Author**: agent
- **Type**: feature
- **REQs affected**: REQ-087
- **Status**: complete
- **Chain hash**: `340e468840a68ac7...`

## 2026-04-27T19:28 — WI-NEXUS-008: Populate preflight test_case_ids from .specsmith/testcases.json (REQ-088)
- **Author**: agent
- **Type**: feature
- **REQs affected**: REQ-088
- **Status**: complete
- **Chain hash**: `a39dcae4c5b4338d...`

## 2026-04-27T19:28 — WI-NEXUS-009: Live l1-nexus smoke test script + skip-by-default integration test (REQ-089)
- **Author**: agent
- **Type**: feature
- **REQs affected**: REQ-089
- **Status**: complete
- **Chain hash**: `d0e80ec48ee0a854...`

## 2026-04-27T19:28 — WI-NEXUS-010: Documentation pass for Nexus broker, preflight, gate, and harness (REQ-090)
- **Author**: agent
- **Type**: docs
- **REQs affected**: REQ-090
- **Status**: complete
- **Chain hash**: `8d94f66001aed55c...`

## 2026-04-27T19:42 — WI-NEXUS-011: Live l1-nexus smoke evidence captured (REQ-095)
- **Author**: agent
- **Type**: evidence
- **REQs affected**: REQ-095
- **Status**: complete
- **Chain hash**: `414225ca221b7eb7...`

## 2026-04-27T19:42 — WI-NEXUS-012: Structured TaskResult dataclass returned by orchestrator.run_task (REQ-091)
- **Author**: agent
- **Type**: feature
- **REQs affected**: REQ-091
- **Status**: complete
- **Chain hash**: `7f161e088d82fcde...`

## 2026-04-27T19:42 — WI-NEXUS-013: /why post-run governance block in REPL (REQ-094)
- **Author**: agent
- **Type**: feature
- **REQs affected**: REQ-094
- **Status**: complete
- **Chain hash**: `7125182a6d402b2e...`

## 2026-04-27T19:42 — WI-NEXUS-014: specsmith preflight CLI decision-specific exit codes (REQ-092)
- **Author**: agent
- **Type**: feature
- **REQs affected**: REQ-092
- **Status**: complete
- **Chain hash**: `16eb05be2f953074...`

## 2026-04-27T19:42 — WI-NEXUS-015: Accepted preflight records preflight ledger event (REQ-093)
- **Author**: agent
- **Type**: feature
- **REQs affected**: REQ-093
- **Status**: complete
- **Chain hash**: `01f963eb2078b181...`
