# Ledger Archive

Archived ledger entries. See `LEDGER.md` for current entries.

## Session 2026-04-01 — Initial CLI implementation

**Status:** Complete
**Scope:** Full CLI tool with 5 commands, 4 agent adapters, CI/CD, tests

### Proposal
Build specsmith CLI tool with: init (scaffold generation), audit (health checks),
validate (consistency), compress (ledger archival), upgrade (spec version migration).
Add agent integration adapters for Warp, Claude Code, Cursor, and Copilot.

Estimated cost: high

### Changes
- `src/specsmith/cli.py` — click CLI with init, audit, validate, compress, upgrade
- `src/specsmith/scaffolder.py` — Jinja2 template renderer with project type logic
- `src/specsmith/config.py` — pydantic ProjectConfig with 8 project types
- `src/specsmith/auditor.py` — governance file checks, REQ↔TEST coverage, ledger health
- `src/specsmith/validator.py` — scaffold.yml, AGENTS.md refs, REQ uniqueness
- `src/specsmith/compressor.py` — ledger archival with configurable thresholds
- `src/specsmith/upgrader.py` — governance template re-rendering on version bump
- `src/specsmith/integrations/` — base adapter + Warp, Claude Code, Cursor, Copilot
- `src/specsmith/templates/` — 30+ Jinja2 templates for governed scaffolds
- `.github/workflows/ci.yml` — lint + typecheck + test matrix + security audit
- `.github/workflows/release.yml` — tag-triggered build → GitHub Release
- `REQUIREMENTS.md` — 37 formal requirements
- `TESTS.md` — 30 test specifications

### Verification
- 36 tests passing (pytest)
- ruff lint: clean
- ruff format: clean
- mypy strict: clean
- CI: lint ✓, security ✓, typecheck pending (fix pushed)

### Open TODOs
- [x] Add VCS platform integrations (GitHub/GitLab/Bitbucket CLI)
- [x] Add Gemini, Windsurf, Aider agent adapters
- [x] Expand CLI runner test coverage
- [x] Self-host governance (this file)


## Session 2026-04-05 — AEE epistemic layer, agentic client, CI/CD, meta-governance

**Status:** Complete
**Branch:** develop
**Spec version:** 0.3.0 (switched from 0.3.0a1 → X.Y.Z.devN scheme)

### What was done

**Applied Epistemic Engineering (AEE) — core implementation:**
- `src/epistemic/` standalone library (7 modules, zero deps): BeliefArtifact, StressTester, FailureModeGraph, RecoveryOperator, CertaintyEngine, TraceVault, AEESession. `from epistemic import AEESession` works in any Python 3.10+ project.
- `src/specsmith/epistemic/` shim re-exporting from `epistemic` (backward compat)
- `src/specsmith/trace.py` — STP-inspired SHA-256 audit chain
- `ledger.py` — CryptoAuditChain (tamper-evident ledger entries)
- 8 new CLI commands: stress-test, epistemic-audit, belief-graph, trace seal/verify/log, integrate
- H13 hard rule (Epistemic Boundaries Required) in governance templates
- 4 new governance templates: epistemic-axioms, belief-registry, failure-modes, uncertainty-map
- 3 new project types: epistemic-pipeline, knowledge-engineering, aee-research
- 33 project types total (up from 30)
- 25 new tests, all passing

**Agentic client (`src/specsmith/agent/`):**
- `specsmith run` — AEE-integrated REPL (Anthropic, OpenAI, Gemini, Ollama; all optional extras)
- 20 specsmith commands as native LLM tools with epistemic contracts
- HookRegistry: H13 enforcement, ledger hints, context budget warning
- SKILL.md loader with domain priority
- Built-in profiles: planner, verifier, epistemic-auditor

**Issue resolutions (all closed):**
- #52: CreditBudget.enforcement_mode soft|hard, specsmith credits check
- #37: specsmith auth set/list/remove/check (OS keyring > file; tokens never logged)
- #17: specsmith workspace init/audit/export (workspace.yml multi-project)
- #16: specsmith watch (polling daemon, LEDGER.md staleness alerts)
- #10: specsmith patent search/prior-art (USPTO ODP API)
- #18: governance templates marketplace (deferred, plugin system is the foundation)

**CI/CD fixes:**
- 5 rounds of CI fixes: ruff SIM violations, mypy errors (auth.py, trace.py, runner.py, cli.py), test count assertions, sandbox upgrade test
- Dev-release workflow: RTD token validation, HTTP status logging, develop/latest build triggers
- RTD “latest”: PATCH /versions/latest/ with identifier=develop (HTTP 204) — root fix confirmed
- PyPI badge: removed dev badge (shields.io couldn’t show .devN reliably)
- v0.3.0a1 GitHub release/tag deleted; versioning changed to X.Y.Z.devN

**Meta-governance bootstrapping:**
- `scaffold.yml` created for specsmith itself (hand-crafted, enable_epistemic: true)
- west-env: specsmith import run, 14 governance files generated, spec_version 0.3.0, committed

**Documentation:**
- docs/site/aee-primer.md — 10-part comprehensive AEE guide
- docs/site/epistemic-library.md — standalone library API reference + glossa-lab examples
- docs/site/agent-client.md — specsmith run reference
- docs/site/index.md — AEE-first homepage
- README.md, AGENTS.md, mkdocs.yml, CHANGELOG.md all updated
- ECC reference cloned: C:\Users\trist\Development\layer1labs\everything-claude-code

### Verification
- 25 new epistemic tests (all pass)
- ruff check + format: clean
- mypy strict: clean (0 errors in 62 files)
- CI: green (all 4 jobs pass)
- 0 open GitHub issues
- 0 security/dependabot alerts

### Open TODOs
- [ ] RTD latest: verify homepage shows AEE content after version identifier fix
- [ ] Yank 0.3.0a1 from PyPI (optional — pip install --pre gets 0.3.0a1 until 0.3.0 releases)
- [ ] glossa-lab: adopt epistemic library (AEESession for decipherment hypotheses)
- [ ] scaffolder.py: render epistemic templates for epistemic project types (foundation done, rendering hook pending)
- [ ] Release 0.3.0 stable when ready (merge develop → main, tag v0.3.0)

### Next step
Begin glossa-lab integration — AEESession for Indus hypothesis tracking. Separately, run specsmith import on cpac and cpsc-engine-python to extend governance to the full layer1labs portfolio.

---


## Session 2026-04-02 — v0.2.0→v0.2.2 release cycle

**Status:** Complete
**Scope:** Major feature release + two patch releases

### Changes
- **v0.2.0**: Uppercase governance filenames, community templates (#42), AI credit tracking (#50/#51), architect command (#49), self-update, multi-language detection, dynamic versioning, VCS commands, ledger/req/test CLIs, plugin scaffold
- **v0.2.1**: Process abort/PID tracking (exec/ps/abort commands), language-specific templates (#41 — Rust, Go, JS/TS), RTD integration (#38), release workflow templates (#44), PyPI integration (#36), template refactor (#45), upgrade --full sync mechanism
- **v0.2.2**: Auto-fix AGENTS.md references on lowercase→uppercase migration, alternate path detection (docs/LEDGER.md, docs/architecture/**), case-insensitive architecture check, CI-gated dev releases

### Issues closed
- #36, #38, #41, #42, #44, #45 (closed), #55, #56 (filed)
- Created v0.3.0 milestone, assigned 6 remaining issues

### Verification
- 115 tests passing (pytest, 3 OS × 3 Python)
- ruff check + format: clean (src/ + tests/)
- mypy strict: clean
- CI: 19/19 checks pass on all PRs before merge
- CodeQL: 0 open alerts
- Dependabot: 0 open alerts

### Open TODOs
- [ ] #55: Fix governance table rendering on RTD (double pipe)
- [ ] #56: Document 15+ missing CLI commands in RTD
- [ ] #52: Credit budget cap enforcement
- [ ] #37: Secure API key management
- [ ] #10: USPTO/MCP patent integration
- [ ] #17: Multi-project workspace management

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
- Architecture plan document updated with full gap analysis and 16-workstream roadmap

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
- **Author**: Tristen Pierson <tpierson@layer1labs.tech>
- **Type**: feature
- **REQs affected**: REQ-065,REQ-066,REQ-067,REQ-068,REQ-069,REQ-070,REQ-071,REQ-072,REQ-073,REQ-074,REQ-075,REQ-076
- **Status**: complete
- **Chain hash**: `ff611e6a7ac0ca62...`


## 2026-04-27T18:14 — WI-NEXUS-002: reconcile machine state JSON (REQ-065..REQ-080), remove stale legacy tests (test_agent.py, test_optimizer.py), add Safe Repository Cleanup boundary + cleanup module + 4 cleanup tests, execute apply cleanup reclaiming 52MB of stale build/cache/archive artifacts. Full suite green: 202 tests pass.
- **Author**: Tristen Pierson <tpierson@layer1labs.tech>
- **Type**: feature
- **REQs affected**: REQ-003,REQ-077,REQ-078,REQ-079,REQ-080
- **Status**: complete
- **Chain hash**: `176531aa559ed8de...`


## 2026-04-27T18:21 — WI-NEXUS-003: add specsmith clean CLI subcommand (REQ-081), add UTF-8 safe console factory and fix Windows cp1252 UnicodeEncodeError in specsmith validate (REQ-082), reconcile machine state to 82 reqs/82 tests, full suite 206 tests pass.
- **Author**: Tristen Pierson <tpierson@layer1labs.tech>
- **Type**: feature
- **REQs affected**: REQ-081,REQ-082
- **Status**: complete
- **Chain hash**: `ac851adc0fd1aca7...`


## 2026-04-27T18:25 — WI-NEXUS-004: rename canonical test-spec governance file from TEST_SPEC.md to TESTS.md across code, docs, ReadTheDocs site, templates, governance, and machine state. Add REQ-083/TEST-083 plus 3 pytest tests guarding against regression. Updated 58 files; full suite green at 209 tests.
- **Author**: Tristen Pierson <tpierson@layer1labs.tech>
- **Type**: feature
- **REQs affected**: REQ-002,REQ-083
- **Status**: complete
- **Chain hash**: `e24fb649a8ef5ce1...`


## 2026-04-27T19:09 — WI-NEXUS-005: add Natural-Language Governance Broker (REQ-084). New module specsmith.agent.broker provides classify_intent, infer_scope, run_preflight, narrate_plan, and execute_with_governance. Wired into Nexus REPL as default mode with /why toggle. Hides REQ/TEST/WI tokens by default, bounds retries per REQ-014, escalates with single clarifying question per REQ-063, and never invents governance content. Full suite green: 227 tests pass.
- **Author**: Tristen Pierson <tpierson@layer1labs.tech>
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


## 2026-04-27T19:53 — WI-NEXUS-016: Retry strategy mapping in execute_with_governance (REQ-096)
- **Author**: agent
- **Type**: feature
- **REQs affected**: REQ-096
- **Status**: complete
- **Chain hash**: `0a696105c598f0cd...`


## 2026-04-27T19:53 — WI-NEXUS-017: specsmith verify CLI subcommand (REQ-097)
- **Author**: agent
- **Type**: feature
- **REQs affected**: REQ-097
- **Status**: complete
- **Chain hash**: `b6a7f5cccf5d0e70...`


## 2026-04-27T19:53 — WI-NEXUS-018: Confidence threshold from .specsmith/config.yml (REQ-098)
- **Author**: agent
- **Type**: feature
- **REQs affected**: REQ-098
- **Status**: complete
- **Chain hash**: `b0caf9452cdd3cd1...`


## 2026-04-27T19:53 — WI-NEXUS-019: work_proposal ledger event distinct from preflight (REQ-099)
- **Author**: agent
- **Type**: feature
- **REQs affected**: REQ-099
- **Status**: complete
- **Chain hash**: `32c2742d1f5b3323...`


## 2026-04-27T19:53 — WI-NEXUS-020: Stress-test bridge in preflight CLI (REQ-100)
- **Author**: agent
- **Type**: feature
- **REQs affected**: REQ-100
- **Status**: complete
- **Chain hash**: `1b5b01b80278aabd...`

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
- **Description**: Ported 7 AI intelligence systems from glossa-lab: HF Open LLM Leaderboard sync with paginated fetch, bucket scoring (reasoning/conversational/longform), static fallback, and CLI (`model-intel scores/sync/recommendations/connection`); 40+ model capability profiles with context-aware history trimming; LLMClient with O-series parameter translation, vLLM guided-JSON, and provider fallback; EMA-based rate limit scheduler with adaptive concurrency; endpoint preset registry (10+ presets) with `/api/model-intel/*` REST endpoints; `agent suggest-profiles` and `agent endpoint-presets` CLI commands; AI Providers page bucket score columns and Sync Scores button. ARCHITECTURE.md §21-27 added. 280 REQs, 258 TESTs. All CI green.
- **Status**: complete
- **Chain hash**: auto



## 2026-05-14T16:00 --- WI-0514c: Phase 2 Token/Context UX — REQ-020/021/022
- **Author**: oz-agent
- **Type**: feature
- **REQs affected**: REQ-020, REQ-021, REQ-022
- **Description**: Phase 2 Token/Context UX landed in specsmith. New `ContextFillState`
  singleton (`context_fill_state.py`) tracks fill % and num_ctx; registered in
  `initialize_app()`. New Settings → Token Usage page (`token_usage_page.py`) fetches
  `specsmith credits summary --json` and displays tokens, cost, per-model breakdown,
  budget. Governance page enhanced with Context Window card: real-time fill dot from
  `ContextFillState`, editable num_ctx input saved via `specsmith config set
  ollama.num_ctx`. Docs: REQ-019..022 and TEST-019..022 added to specsmith governance
  artifacts. commit: 1025ed5.
- **Status**: complete
- **Chain hash**: auto



## 2026-05-14T12:42 --- WI-0514b: specsmith issue group + bug report page (REQ-303, REQ-304)
- **Author**: oz-agent
- **Type**: feature
- **REQs affected**: REQ-303,REQ-304
- **Description**: Added duplicate-guarded GitHub issue filing. `src/specsmith/issue_reporter.py`: `search_issues`, `check_duplicate`, `file_issue`, `ai_enhance_report` (Jaccard similarity, `gh` CLI + unauthenticated REST fallback). `specsmith issue` CLI group (check/file/search, all with --json). 32 passing tests. api_surface.json updated. CHANGELOG [0.11.3-post1] added. specsmith `bug_report_page.py` added: in-app form with repo selector, title/description inputs, Check Duplicates, File Report; `SettingsSection::BugReport` wired into settings infrastructure; Help menu updated. FTL strings, REQ-019/TEST-019 added.
- **Status**: complete
- **Chain hash**: auto



## 2026-05-14T10:55 --- WI-0514: v0.11.3 release prep (REQ-302)
- **Author**: oz-agent
- **Type**: release
- **REQs affected**: REQ-302
- **Description**: Session cleanup and release. Added `_diag_*.py` to .gitignore (diagnostic-only script, never commit). Documented 4 unreleased post-v0.11.2 commits in CHANGELOG [0.11.3]: YAML-first `specsmith req add` / `specsmith test add` commands (REQ-302), real `esdb migrate` + `esdb replay` implementations (stub removal), lint/format fixes. Bumped pyproject.toml and __init__.py from 0.11.2 to 0.11.3. CI was already green; Dependabot clean.
- **Status**: complete
- **Chain hash**: auto



## 2026-05-15T14:08 --- WI-0516: EU/NA compliance, governance consolidation, AGENTS.md slim, migration framework
- **Author**: oz-agent
- **Type**: feature / governance / docs
- **REQs affected**: REQ-313,REQ-314,REQ-315,REQ-316,REQ-317,REQ-318,REQ-319,REQ-320
- **Status**: complete
- **Chain hash**: auto
- **Description**: Major compliance and governance consolidation sprint:

  **Compliance package** (`src/specsmith/compliance/`): Structured regulation definitions for
  8 EU/NA regulations (May 2026): EU AI Act 2024/1689 (Arts. 5/9/12/13/14/15/52/72),
  NIST AI RMF 1.0 + AI 600-1 GenAI Profile, OMB M-24-10, Colorado SB24-205 (eff. Feb 2026),
  Texas HB 1709 (eff. Sep 2025), Illinois AIETA, California ADMT, NYC LL 144.
  ESDB-backed evidence collection (EvidenceCollector), per-regulation compliance checking
  (ComplianceChecker), JSON/Markdown/HTML report generation (ComplianceReporter).
  CLI: `specsmith compliance check/report/audit/list`. REST: `GET /api/compliance/status`.
  Compliance results stored as ChronoRecord(kind=compliance_result) in ESDB.
  Old `compliance.py` content moved to `compliance/_compat.py` and re-exported.

  **Governance consolidation** (`src/specsmith/governance_store.py`): GovernanceStore reads
  `.specsmith/governance/*.yaml` (preferred) with fallback to `docs/governance/*.md`.
  `.specsmith/governance/rules.yaml` written with H1-H22 as structured YAML.
  REST: `GET /api/governance/rules`.

  **AGENTS.md slim**: `templates/agents.md.j2` → minimal 20-line specsmith-delegation template.
  specsmith `AGENTS.md` updated to slim format. Original backed up by M002 migration.

  **Migration framework** (`src/specsmith/migrations/`): Versioned, isolated, droppable.
  4 migrations: M001 (governance YAML), M002 (slim AGENTS.md), M003 (compliance init),
  M004 (ledger ESDB). Runner tracks applied versions in `.specsmith/migration-state.json`.
  `specsmith migrate list/run` CLI. `upgrader.py` runs `MigrationRunner.run_pending()`.
  Drop path: delete `src/specsmith/migrations/` + one line in upgrader.py for v1.0 release.

  **`serve.py`**: `GET /api/compliance/status`, `GET /api/governance/rules` added.

  **`tests/fixtures/api_surface.json`**: +compliance, +migrate commands.

  **`.specsmith/governance/rules.yaml`**: H1-H22 rules as canonical YAML.



## 2026-05-15T13:30 --- WI-0515-INFRA: ESDB write layer, CI/CD automation, context orchestration, session persistence, OEA hardening
- **Author**: oz-agent
- **Type**: feature
- **REQs affected**: REQ-305,REQ-306,REQ-307,REQ-308,REQ-309,REQ-310,REQ-311,REQ-312
- **Status**: complete
- **Chain hash**: auto
- **Description**: Major infrastructure sprint across 9 workstreams:

  **Phase A — CI/CD fixes**: Fixed all GitHub Actions version references in specsmith CIs
  (checkout@v6→v4, setup-python@v6→v5, cache@v5→v4, upload-artifact@v7→v4, download-artifact@v8→v4).
  Added `.github/dependabot.yml` to specsmith repo. Added CodeQL workflow to specsmith. Added
  `cargo audit` job to specsmith CI. Added `specsmith ci enable/status/watch` commands via
  `src/specsmith/ci_manager.py`. Added `GET /api/ci/status` to serve.py. Updated
  `vcs/github.py` CI generator to emit correct action versions.

  **Phase B — ChronoStore ESDB**: Implemented `src/specsmith/esdb/store.py` with
  `ChronoStore` — a pure-Python WAL-based per-project ESDB at `.chronomemory/events.wal`.
  SHA-256 hash chain, crash-safe atomic WAL appends, snapshot.json every 50 events.
  All records carry OEA anti-hallucination fields: source_type (H19), confidence (H17),
  evidence (H20), epistemic_boundary (H15), is_hypothesis (H20), model_assumptions (H21),
  recursion_depth (H16). `EsdbBridge` updated to delegate to `ChronoStore` when available.
  `esdb migrate` updated to call `ChronoStore.migrate_from_json()`. `upgrader.py` auto-migrates
  on `specsmith upgrade`. `retrieval.py` injects only confidence >= 0.6 records (H18).
  `tests/fixtures/api_surface.json` updated with ci + context commands.

  **Phase C — Session persistence**: New `src/specsmith/session_store.py`: atomic
  `.specsmith/session-state.json` + `.specsmith/conversation-history.jsonl` (200-turn cap).
  `GET /api/session/history` and `POST /api/session/save` added to serve.py.

  **Phase D — Context orchestrator**: New `src/specsmith/context_orchestrator.py` with
  three-tier auto-optimization (Tier1@60%, Tier2@80%, Tier3@85% emergency). `specsmith
  context optimize [--dry-run]` CLI command. "Never delete from WAL" invariant enforced.

  **Phase F — Governance**: REQ-305 through REQ-312 added to `docs/REQUIREMENTS.md`.
  Governance invariants I-ESDB-1/2, I-SES-1, I-CTX-1, I-CI-1 added to `docs/governance/RULES.md`.



## 2026-05-15T12:42 --- WI-0515-GOV: Governance H15–H22 + OEA paper integration
- **Author**: oz-agent
- **Type**: docs / governance
- **REQs affected**: REQ-001 (governance rules)
- **Status**: complete
- **Chain hash**: auto
- **Description**: Extended specsmith governance hard rules from H1–H14 to H1–H22.
  H12 updated for cross-platform coverage (Windows `.cmd/.ps1`, macOS/Linux `sh/bash`).
  H15–H22 added covering anti-hallucination principles from the OEA Recursive Generative
  Stability research (BitConcepts Research, 2026): epistemic scope bounding (H15),
  anti-drift recursion guard (H16), calibration direction (H17), RAG retrieval filtering (H18),
  synthetic contamination prevention (H19), falsifiability required (H20), no undisclosed
  model assumptions (H21), cross-platform CI enforcement (H22).
  Documentation updated across: `docs/governance/RULES.md`, `docs/site/governance.md`,
  `docs/site/index.md`, `docs/governance/EPISTEMIC-AXIOMS.md`, `docs/ARCHITECTURE.md §28`,
  `README.md`. specsmith compliance page header range updated to H1–H22.
  OEA paper cited as external empirical validation of the five AEE axioms via
  axiom↔OEA control mechanism correspondence table in `EPISTEMIC-AXIOMS.md`.



## 2026-05-12T13:06 --- WI-0512-GAPS: Arch/req/test gap audit + TEST-282/TEST-283 added (REQ-263, REQ-265)
- **Author**: oz-agent
- **Type**: test
- **REQs affected**: REQ-263,REQ-265
- **Description**: Audit revealed REQ-263 (HF paginated sync persists bucket scores) and REQ-265 (HF API token in Authorization header) lacked explicit pytest coverage. Added TEST-282 (`TestHFSyncPersistsBucketScores` — verifies scores.json created with bucket_scores dict and all required keys per entry) and TEST-283 (`TestHFTokenInHeaders` — verifies token_set flag, rate_limit_tier, and Authorization header capture via mock). Both entries added to docs/TESTS.md. `specsmith sync` updated testcases.json to 260 entries.
- **Status**: complete
- **Chain hash**: auto


## 2026-05-17T15:45 — Implemented multi-agent DAG dispatcher (REQ-321..REQ-334): dispatch/ package with TaskDAG/AgentDispatcher/EventEmitter, orchestrator.run_dispatch(), spawner.spawn_worker(), CLI dispatch group, serve.py SSE+REST dispatch endpoints. Added compiler/tool support: run_gcc, run_arm_gcc, run_aarch64_gcc, run_iar_compiler, run_intel_compiler, run_clang_format, run_clang_tidy, run_vsg.
- **Author**: oz-agent
- **Type**: feature
- **Status**: complete
- **Chain hash**: `a412cb4f3ac05f14...`


## 2026-05-17T16:01 — Full traceability sweep: added docs/requirements/dispatch.yml + docs/tests/dispatch.yml (YAML source for REQ-321..334), ran specsmith sync (0 errors, 0 warnings), fixed ARCHITECTURE.md section numbering (duplicate 15/16 corrected), added REQ-313..320 reservation note, updated README.md (dispatch+compiler sections), CHANGELOG.md (v0.11.3-post2), docs/site/commands.md (dispatch group + compiler tools), docs/site/tool-registry.md (agent tools + ROLE_TOOLS). All tests: 777 passed.
- **Author**: oz-agent
- **Type**: documentation
- **Status**: complete
- **Chain hash**: `e519c3f3fc417915...`


## 2026-05-17T16:12 — Final gap sweep: added apply_diff/search_web/search_repo tool stubs to close ROLE_TOOLS vs AVAILABLE_TOOLS mismatch (23 tools total, no refs missing); added Dispatch to README 50+ CLI Commands section; restored yaml_governance.yml row in ARCHITECTURE.md domain table (REQ-300..312); fixed post_action to spawn background thread (no UI-thread blocking on retry/abort POST).
- **Author**: oz-agent
- **Type**: fix
- **Status**: complete
- **Chain hash**: `9a0d63f844078d5a...`


## 2026-05-17T16:31 — Resolved all deferred items: (1) abort mid-LLM-call via _invoke_worker_monitored sub-thread with 0.5s abort polling; (2) CLI dispatch run uses Orchestrator._call_planner when AG2 available (Path A/B fallback); (3) topological DAG layout with depends_on payload, compute_levels(), bezier edge drawing; (4) REQ-313..320 compliance plan 5939f743 implemented and tested.
- **Author**: oz-agent
- **Type**: feature
- **Status**: complete
- **Chain hash**: `f91cae2487897572...`


## 2026-05-17T16:53 — Removed all specsmith-vscode / VS Code extension references across specsmith docs. Deleted docs/site/vscode-extension.md. Updated mkdocs.yml nav. Fixed index.md, quickstart.md, commands.md, getting-started.md, troubleshooting.md, endpoints.md, PRIVACY.md, runner.py, core.py, events.py, suggester.py, languages.py, cli.py, agent.yml REQs/TESTs, README.md. The specsmith client is now the sole documented client.
- **Author**: oz-agent
- **Type**: fix
- **Status**: complete
- **Chain hash**: `1e48aaf097e11726...`


## 2026-05-22T18:53 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `13907d72d47f3708...`


## 2026-05-24T09:55 — specsmith migration: 0.11.3.dev420 → 0.11.6
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `dfc79bb72cce492a...`


## 2026-05-24T11:08 — specsmith migration: 0.11.6 → 0.11.7
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `cb6ac2e2627ddadd...`


## 2026-06-11T20:45 — specsmith migration: 0.11.7 → 0.13.0
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `6f2d456167fa563c...`


## 2026-06-11T20:45 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `bafb85feabbffbaf...`


## 2026-06-11T22:22 — specsmith migration: 0.14.0 → 0.13.0
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `efee1a532b2b0e16...`


## 2026-06-14T14:00 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `e81de5496a99ee5c...`


## 2026-06-14T19:51 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `532736306dbbf018...`


## 2026-06-14T22:42 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `f055079d3e57990c...`


## 2026-06-14T22:42 — specsmith migration: 0.14.1 → 0.15.3
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `54603a5b5f64b6f1...`


## 2026-06-14T23:08 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `a1bcebb9fd40ee9a...`


## 2026-06-15T11:08 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `fb2b08ce5753c5bb...`


## 2026-06-22T07:41 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `df60bb80a2e8f1e1...`


## 2026-06-23T14:00 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `36a1aa7c382e4a8e...`

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
- ## 2026-05-14T16:00 --- WI-0514c: Phase 2 Token/Context UX — REQ-020/021/022 — —
- ## 2026-05-14T12:42 --- WI-0514b: specsmith issue group + bug report page (REQ-303, REQ-304) — —
- ## 2026-05-14T10:55 --- WI-0514: v0.11.3 release prep (REQ-302) — —
- ## 2026-05-15T14:08 --- WI-0516: EU/NA compliance, governance consolidation, AGENTS.md slim, migration framework — —
- ## 2026-05-15T13:30 --- WI-0515-INFRA: ESDB write layer, CI/CD automation, context orchestration, session persistence, OEA hardening — —
- ## 2026-05-15T12:42 --- WI-0515-GOV: Governance H15–H22 + OEA paper integration — —
- ## 2026-05-12T13:06 --- WI-0512-GAPS: Arch/req/test gap audit + TEST-282/TEST-283 added (REQ-263, REQ-265) — —
- ## 2026-05-17T15:45 — Implemented multi-agent DAG dispatcher (REQ-321..REQ-334): dispatch/ package with TaskDAG/AgentDispatcher/EventEmitter, orchestrator.run_dispatch(), spawner.spawn_worker(), CLI dispatch group, serve.py SSE+REST dispatch endpoints. Added compiler/tool support: run_gcc, run_arm_gcc, run_aarch64_gcc, run_iar_compiler, run_intel_compiler, run_clang_format, run_clang_tidy, run_vsg. — —
- ## 2026-05-17T16:01 — Full traceability sweep: added docs/requirements/dispatch.yml + docs/tests/dispatch.yml (YAML source for REQ-321..334), ran specsmith sync (0 errors, 0 warnings), fixed ARCHITECTURE.md section numbering (duplicate 15/16 corrected), added REQ-313..320 reservation note, updated README.md (dispatch+compiler sections), CHANGELOG.md (v0.11.3-post2), docs/site/commands.md (dispatch group + compiler tools), docs/site/tool-registry.md (agent tools + ROLE_TOOLS). All tests: 777 passed. — —
- ## 2026-05-17T16:12 — Final gap sweep: added apply_diff/search_web/search_repo tool stubs to close ROLE_TOOLS vs AVAILABLE_TOOLS mismatch (23 tools total, no refs missing); added Dispatch to README 50+ CLI Commands section; restored yaml_governance.yml row in ARCHITECTURE.md domain table (REQ-300..312); fixed post_action to spawn background thread (no UI-thread blocking on retry/abort POST). — —
- ## 2026-05-17T16:31 — Resolved all deferred items: (1) abort mid-LLM-call via _invoke_worker_monitored sub-thread with 0.5s abort polling; (2) CLI dispatch run uses Orchestrator._call_planner when AG2 available (Path A/B fallback); (3) topological DAG layout with depends_on payload, compute_levels(), bezier edge drawing; (4) REQ-313..320 compliance plan 5939f743 implemented and tested. — —
- ## 2026-05-17T16:53 — Removed all specsmith-vscode / VS Code extension references across specsmith docs. Deleted docs/site/vscode-extension.md. Updated mkdocs.yml nav. Fixed index.md, quickstart.md, commands.md, getting-started.md, troubleshooting.md, endpoints.md, PRIVACY.md, runner.py, core.py, events.py, suggester.py, languages.py, cli.py, agent.yml REQs/TESTs, README.md. The specsmith client is now the sole documented client. — —
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


## 2026-06-26T13:24 — specsmith migration: 0.17.0 → 0.17.1
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `e8034ede0d786d14...`


## 2026-06-26T13:25 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `c481074e0b828d95...`


## 2026-06-27T17:43 — specsmith migration: 0.17.1 → 0.18.0
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `3bf0f8567e3120e0...`


## 2026-06-28T11:11 — wi_promote WI-0CEA445B → REQ-424: CI pipeline must produce zero CodeQL static analysis alerts on every run
- **Author**: specsmith
- **Type**: wi_promote
- **Status**: complete
- **Chain hash**: `297b1aa2359c38f5...`


## 2026-06-28T11:11 — wi_promote WI-B73B339B → REQ-425: Governed agents must autonomously resolve preflight needs_clarification without blocking
- **Author**: specsmith
- **Type**: wi_promote
- **Status**: complete
- **Chain hash**: `a1595baa2a82e9c2...`


## 2026-06-28T11:11 — wi_promote WI-122A76C4 → REQ-426: Benchmark governance conditions must achieve 100% pass rate across all tasks
- **Author**: specsmith
- **Type**: wi_promote
- **Status**: complete
- **Chain hash**: `e8a20807f2c5b195...`


## 2026-06-28T13:56 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `cbfea526acb6bc39...`


## 2026-06-28T14:34 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `c68bf6b1ac640968...`


## 2026-06-28T15:53 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `820f2a813c365cde...`


## 2026-06-29T10:44 — wi_close WI-0CB81412: done
- **Author**: specsmith
- **Type**: wi_close
- **Status**: complete
- **Chain hash**: `6705d87a2a6a2059...`


## 2026-06-29T14:07 — specsmith migration: 0.19.2 → 0.20.1
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `087ee05e1059ce80...`


## 2026-07-05T11:18 — specsmith cleanup --apply removed 7 target(s), 2495138 bytes reclaimed.
- **Author**: specsmith
- **Type**: cleanup
- **REQs affected**: REQ-374
- **Status**: complete
- **Chain hash**: `1c1c68ddafb6b809...`


## 2026-07-05T15:52 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `cf98c08d1f8ceb46...`


## 2026-07-10T18:38 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `faaf06ea12574c6a...`


## 2026-07-13T07:33 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `07ad8108e3860a7c...`


## 2026-07-13T10:30 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `b864898ee975ecce...`


## 2026-07-13T11:12 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `b960aeeee661d07c...`


## 2026-07-13T11:23 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `82c26ea54d1780a8...`


## 2026-07-13T11:31 — wi_archive WI-2B89DD4E: Deferred: governance requires the user to explicitly confirm deletion of refs/heads/feat/zoo-roo-mcp-integration.
- **Author**: specsmith
- **Type**: wi_archive
- **Status**: complete
- **Chain hash**: `050e3319e536e818...`


## 2026-07-13T11:31 — wi_archive WI-0DA3685B: Deferred: governance requires the user to explicitly confirm deletion of refs/heads/feat/zoo-roo-mcp-integration.
- **Author**: specsmith
- **Type**: wi_archive
- **Status**: complete
- **Chain hash**: `7aca009cad3ae1a1...`


## 2026-07-13T11:31 — wi_archive WI-71E9EDBB: Deferred: GitHub rejects authors approving their own protected pull request; an independent code owner is required.
- **Author**: specsmith
- **Type**: wi_archive
- **Status**: complete
- **Chain hash**: `f2361802e838e239...`


## 2026-07-13T11:32 — wi_close WI-094C4FE3: Published archive/feat-zoo-roo-mcp-integration-20260713 at the closed branch head after verification.
- **Author**: specsmith
- **Type**: wi_close
- **Status**: complete
- **Chain hash**: `b19ddba9a15b5658...`


## 2026-07-13T14:38 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `0fcf05a9931e039e...`


## 2026-07-13T14:42 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `1d6d373b06cfc948...`


## 2026-07-13T14:59 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `c16a7c48273e40f7...`


## 2026-07-13T15:14 — test-ran TEST-467: passed (status: pending → implemented)
- **Author**: specsmith
- **Type**: test-ran
- **REQs affected**: TEST-467
- **Status**: complete
- **Chain hash**: `15ebd5761b79a512...`


## 2026-07-13T15:14 — test-ran TEST-470: passed (status: pending → implemented)
- **Author**: specsmith
- **Type**: test-ran
- **REQs affected**: TEST-470
- **Status**: complete
- **Chain hash**: `3b3775a522076719...`


## 2026-07-13T15:30 — test-ran TEST-371: passed (status: pending → implemented)
- **Author**: specsmith
- **Type**: test-ran
- **REQs affected**: TEST-371
- **Status**: complete
- **Chain hash**: `92ad46273e1a25c0...`


## 2026-07-13T15:30 — test-ran TEST-470: passed (status: pending → implemented)
- **Author**: specsmith
- **Type**: test-ran
- **REQs affected**: TEST-470
- **Status**: complete
- **Chain hash**: `77af924fed83a344...`


## 2026-07-13T15:47 — KILL SWITCH ACTIVATED: emergency stop
- **Author**: specsmith-operator
- **Type**: kill-switch
- **REQs affected**: REG-005
- **Status**: complete
- **Epistemic status**: high
- **Chain hash**: `702e7876aafc9f6b...`

