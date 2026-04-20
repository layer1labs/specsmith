# Ledger — specsmith

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
- `docs/REQUIREMENTS.md` — 37 formal requirements
- `docs/TEST_SPEC.md` — 30 test specifications

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
- ECC reference cloned: C:\Users\trist\Development\BitConcepts\everything-claude-code

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
Begin glossa-lab integration — AEESession for Indus hypothesis tracking. Separately, run specsmith import on cpac and cpsc-engine-python to extend governance to the full BitConcepts portfolio.

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
