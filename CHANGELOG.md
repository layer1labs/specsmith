# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Only versions published to PyPI are listed. Intermediate development versions are
consolidated into the next published release.

## [Unreleased]

---

## [0.16.1] - 2026-06-23

### Added

- **Governance efficiency benchmark suite** — 12-condition benchmark comparing specsmith
  against ungoverned, BMAD, Cursor rules, Copilot, Aider, Cline, Codex CLI, OpenSpec,
  Agile BDD/TDD, and context injection across real coding tasks with `gpt-4o-mini`
  and `gpt-5.5`. Key result: specsmith FULL achieves 100% pass rate with 2.6x fewer
  tokens; governance is 6.3x cheaper per correct answer on gpt-5.5.
- **Real OpenAI agent harness** (`scripts/govern_bench/harness.py`) — multi-turn tool
  loop with specsmith preflight gating, cost tracking, and per-condition scoring.
- **Cross-model comparison report** (`scripts/govern_bench/compare_runs.py`) — per-task
  and summary tables with cost-of-pass, pass rates, and monthly projections side-by-side.
- **CI matrix** (`.github/workflows/bench.yml`) — parallel bench jobs for both models
  with auto-generated comparison report posted to GitHub job summary.
- **Benchmark documentation** — `docs/site/efficiency-benchmark.md`,
  `docs/site/model-comparison.md`; Benchmarks nav section in `mkdocs.yml`.
- Benchmark callout table and headline findings in README and `docs/site/index.md`.

### Fixed

- **CI: `test_github_issue_plan_and_create_dry_run`** — `github issue-create --dry-run`
  no longer calls `gh issue list` against the live GitHub API (timed out in CI without
  auth token). `_gh_open_issue_titles` also catches `subprocess.TimeoutExpired`.

### Changed

- README Quick Start rewritten as a clear 6-step day-1 flow.
- Mermaid architecture flowchart replaced with plain ASCII for PyPI compatibility.
- `brief-lang` removed from project types showcase and GitHub repo About description.
- Orphaned git tags and GitHub releases for non-PyPI versions removed.

---

## [0.16.0] - 2026-06-22

Stabilisation milestone consolidating the full 0.15.x development cycle into a single
release. Version set to `0.16.0` to restore correct PyPI semver ordering above `0.15.3`
(previous `0.2.5`/`0.2.6` tags were semver-lower than `0.15.3`).
1 607 tests passing across Python 3.10-3.13 x Ubuntu + Windows.

### Added

- **New CLI commands (20+):**
  - `specsmith quickstart` — interactive governance mode and project-type wizard
  - `specsmith expand --to team|regulated` — upgrade governance tier in-place
  - `specsmith verify-integrations` — checks Claude, Cursor, Copilot, agent-skill, MCP
  - `specsmith import spec-kit|openspec|bmad` — import from common spec formats
  - `specsmith export markdown|json|github-issues|evidence-pack` — multi-format export
  - `specsmith github issue-plan|issue-create` — generate and post issue plans via gh CLI
  - `specsmith transcript import` — import agent action logs into ESDB
  - `specsmith approve` — human approval gate with ESDB-backed audit record
  - `specsmith policy validate|simulate` — validate and dry-run governance policies
  - `specsmith plugin list|validate` — plugin registry management
  - `specsmith recover` — guided recovery from governance drift
  - `specsmith dashboard build` — generate governance dashboard HTML
  - `specsmith audit verify-chain` — cryptographic audit hash-chain verification
  - `specsmith migrate --check` — preflight migration without writing
  - `specsmith governed-pr check` — PR governance gate (branch, CI, sign-off)
  - `specsmith drift-check` — detect requirement/test/code drift in a diff
  - `specsmith trace score` — score a decision against the trace vault
- **New modules:** `transcripts.py`, `risk.py`, `approvals.py`, `policy.py`,
  `governed_pr.py`, `recover.py`, `dashboard.py`, `plugins.py`.
- **New test files:** `test_esdb_sqlite.py`, `test_esdb_enforcement.py`,
  `test_esdb_verify_chain_cli.py`, `test_architecture.py`, `test_golden_path.py`,
  `test_init_modes.py`, `test_schema_migrations.py`, `test_typing_guardrails.py`.
- **New docs:** `docs/ROADMAP.md`, `docs/SECURITY.md`, `docs/stability.md`,
  `docs/editions.md`, `docs/security-threat-model.md`, plain-English glossary,
  skills and comparison docs.

### Fixed

- **Python 3.10 compatibility** — `from datetime import UTC` replaced with
  `datetime.now(timezone.utc)` throughout `esdb/sqlite_store.py`.
- **mypy strict compliance** — resolved `typeddict-item` narrowing in `transcripts.py`,
  unused `# type: ignore` comments, and `open_default_store` return type.
- **Sync check drift** — YAML requirements/testcases/docs regenerated from sources.
- **`.gitignore` ESDB policy** — explicit `!` include entries for `.specsmith/esdb.sqlite3`,
  `.specsmith/requirements.json`, `.specsmith/testcases.json`, and `.chronomemory/`.

### Changed

- **chronomemory >= 0.2.0** — pinned to the 0.2.0 milestone release (Rust WAL migrated
  to NDJSON, PyO3 bindings via maturin, cross-compatible with Python).

---

## [0.15.3] - 2026-06-14

### Changed

- Dev Release workflow isolated to the `develop` branch only; release deployments from
  `main` exclusively use `release.yml` triggered by a version tag push.

---

## [0.15.2] - 2026-06-14

### Added

- **`bare-metal-c` built-in skill** — startup code, vector tables, linker scripts,
  C runtime initialization, interrupt-safe C, atomics/volatile guidance, cross-compilation,
  diagnostics, and hardware-in-loop testing patterns.
- **Expanded embedded skills** — `zephyr-rtos` updated for Zephyr 4.4/3.x (sysbuild,
  Kconfig/devicetree, MCUboot/TF-M, Twister/ztest); `freertos` updated with tasks,
  queues, direct notifications, event groups, SMP/MPU notes, tracing.
- **Skills index** — 136 unique built-in skills documented in RTD
  (`docs/site/skills-index.md`).

### Fixed

- **PyPI README links** — relative links that break on PyPI converted to absolute
  GitHub or RTD URLs.
- **RTD navigation** — previously orphaned pages added to `mkdocs.yml`: Quickstart,
  Multi-Agent Profiles, BYOE Endpoints, Kairos Terminal, YAML Governance, API Stability.
- **Skill catalog duplicate slugs** — `specsmith skill list` now deduplicates
  `specsmith`, `specsmith-save`, and `specsmith-audit`.
- **Security policy version table** — updated supported versions to `0.15.x` / `0.14.x`.

---

## [0.15.1] - 2026-06-14

### Added

- **WI lifecycle subsystem** (`specsmith/wi_store.py`) — `WorkItem` dataclass with
  6-state machine (`open -> implemented -> closed / archived / rejected / promoted`),
  atomic JSON persistence, enforced transitions, and `force` override.
- **`specsmith wi` CLI group** — `list`, `show`, `close`, `archive`, `promote`, `tag`,
  `import` with `--json` output and `--project-dir` support.
- **Preflight -> WI wiring** — every accepted `preflight` mints a `WI-XXXXXXXX` and
  returns `work_item_id` in the result.
- **Verify -> WI wiring** — `run_verify` auto-transitions the active WI to `implemented`
  on equilibrium (diff present + zero test failures).
- **`docs/compliance/regulation_versions.yml`** — freshness sentinel tracking article
  counts for EU AI Act, NIST RMF, OMB M-24-10, Colorado SB24-205, Texas HB1709,
  Illinois AIETA, California ADMT, NYC LL 144. CI fails when counts drift.
- **`docs/site/wi-lifecycle.md`** — RTD documentation for the WI lifecycle subsystem.
- **80-test suite** (`tests/test_wi_lifecycle.py`) covering the full WI lifecycle.
- **150-test compliance CI gate** (`tests/test_compliance_governance.py`).
- **Sandbox smoke tests** — parametrized over all 63 project types.
- **`specsmith-error-reporting` skill** — structured issue triage protocol for AI agents.
- **`specsmith-mcp-configs` skill** — 20+ tested MCP server configurations
  (filesystem, github, brave-search, postgres, sqlite, exa, tavily, linear, etc.).
- **Compliance best-effort disclaimer** added throughout CLI output, JSON/HTML reports,
  module docstrings, and compliance docs.
- **`ComplianceReporter.summary_dict()`** — public API replacing private `_summary_dict`.

### Fixed

- **`governance_logic.py` WI NameError** — `WorkItemStore(root)` used undefined `root`;
  fixed to `WorkItemStore(_root_str)` so WIs are now persisted correctly.
- **`pyproject.toml` pytest config** — added `pythonpath = ["src"]` so pytest discovers
  `specsmith` without requiring `pip install -e .`.
- **ESDB `chain_valid()` display** — `esdb status` and `checkpoint` now use
  `chain_valid() is not False` to handle non-bool returns from chronomemory.
- **Governance anchor emoji alignment** — phase emoji removed from the fixed-width
  anchor box (multi-column glyphs caused border misalignment).
- **`cli.py` wi_promote_cmd** — removed dead `new_req` dict assignment (F841).
- **S603/S607 subprocess calls** — two `subprocess.run` sites annotated safe with
  explanatory `# noqa`.

### Changed

- `specsmith` and `specsmith-session-governance` SKILL.md files updated: full WI
  lifecycle explanation, compliance disclaimer, MCP tool governance rule, updated
  command tables.

---

## [0.14.1] - 2026-06-12

### Added

- **Two-tier ESDB architecture** (REQ-365, REQ-366) — free built-in SQLite backend
  (MIT, no license key) plus commercial `chronomemory` ChronoStore:
  - `specsmith.esdb.sqlite_store.SqliteStore` — activated automatically on every
    `pip install specsmith`. DB at `.specsmith/esdb.sqlite3`.
  - `specsmith[esdb]` extra — installs `chronomemory` from PyPI; requires a valid
    Ed25519 license key from Layer1Labs to activate ChronoStore.
  - `open_default_store()` backend selector: env override -> license check -> SQLite.
- **ESDB license gate** (REQ-367) — offline Ed25519 signature verification via
  `~/.specsmith/esdb.key`; no internet connection required once activated.
- **ESDB CLI command group** (`specsmith esdb ...`):
  `status`, `enable --key-file`, `migrate`, `export`, `import`, `backup`,
  `rollback --steps N`, `compact`, `replay`.
- **ESDB documentation** (`docs/site/esdb.md`) — backend comparison, licensing,
  ChronoStore activation (pip and pipx), CLI reference, Python API, migration guide.
- **Native MCP governance server** (`specsmith mcp serve`, REQ-363) — zero-dependency
  stdio MCP server (JSON-RPC 2.0, MCP 2024-11-05) exposing six tools:
  `governance_audit`, `governance_checkpoint`, `governance_preflight`,
  `governance_phase`, `governance_req_list`, `governance_trace_seal`.
- **`specsmith mcp install-warp`** — prints the Warp MCP config JSON snippet for
  one-paste setup in Settings -> Agents -> MCP servers.
- **Warp repository workflows** (`.warp/workflows/`) — seven `Ctrl+Shift+R`-searchable
  workflow YAML files: Session Start, Audit, Checkpoint, Preflight, Save, Phase Status,
  Session End.
- **`specsmith-session-governance` skill** — drift prevention, heartbeat, preflight gate.
- **`release-pilot` skill** — gitflow release-cut workflow for the Release phase.
- **New test coverage** — `tests/test_esdb_sqlite.py` (278 lines),
  `tests/test_esdb_license.py` (261 lines), `tests/test_mcp_server.py` (671 lines).

### Fixed

- **10 CodeQL security alerts resolved** — `py/path-injection` (sanitiser now inline in
  `run_preflight`), `py/import-and-import-from` (4 sites), `py/module-import-repeat`
  (3 sites in `test_mcp_server.py`), `py/non-standard-exception-in-special-method`
  (raises `AttributeError` not `ImportError`), `py/empty-except` (bare `pass` replaced).
- **Broken RTD links** — `readthedocs.io/esdb` URLs corrected to `/en/stable/esdb/`.
- Release helper: `--no-edit` added to `git merge`; `git core.editor=true` set to
  prevent editor prompts.

### Changed

- `specsmith[esdb]` extra: `chronomemory>=0.1.7` (wheel-only; no sdist from v0.1.7).
  Old chronomemory versions 0.1.2-0.1.6 yanked from PyPI.

---

## [0.13.0] - 2026-06-04

### Added

- **16 new project types** (47 -> 63 total):
  - AI / LLM / Agents: `llm-app`, `agent-orchestration`, `mcp-server`, `rag-pipeline`,
    `mlops-platform` — with auto-detection from dependency signals.
  - JVM: `java-spring`, `java-library`.
  - Infrastructure: `serverless`, `kubernetes-operator`, `streaming-pipeline`,
    `data-warehouse`.
  - Game: `game-unity`, `game-godot`.
  - Web3: `smart-contract`.
  - Desktop: `desktop-electron`, `desktop-tauri`.
- **55 new built-in skills** (76 -> 131 skills across 16 domains):
  - `ai-agents` (14): LLM app dev, MCP server dev, agent orchestration, prompt
    engineering, RAG, context engineering, AI safety, LangChain, LangGraph, vector DB,
    model evaluation, fine-tuning, computer vision, MLOps.
  - `software-engineering` (12): code review, TDD, debugging, refactoring, security
    hardening, performance, API design, database design, dependency management, git
    workflow, PR workflow, ADRs.
  - `web-backend` (11), `data-engineering` (8), `platform-engineering` (10).
- **`_EXPLICIT_ONLY_TYPES`** — `kubernetes-operator`, `streaming-pipeline`, `serverless`,
  `agent-orchestration`, `mcp-server`, `rag-pipeline`, `mlops-platform`, `game-unity`,
  `game-godot`, `data-warehouse` use explicit configuration to prevent auto-detection
  false positives.
- **`specsmith-*` self-referential skills** — `specsmith`, `specsmith-save`,
  `specsmith-audit` added to the governance catalog; installable via
  `specsmith skill install <slug>`; written to `<slug>/SKILL.md` subdirectory for
  Warp/Claude Code/Codex auto-discovery.
- **`accepted_warnings` audit suppression** — `scaffold.yml` now supports
  `accepted_warnings: [alias, ...]` to suppress specific audit checks.
  Suppressed checks show as `~ <check> (accepted)` and are excluded from the failure
  count and exit code. Supported: `scaffold_type_mismatch`, `ledger_line_threshold`,
  `open_todo_count`.
- **`SPECSMITH_ALLOW_NON_PIPX=1` autouse fixture** — test suite no longer requires pipx
  under editable installs.

### Fixed

- **LEDGER open-TODO false positive** (`#195`) — `check_ledger_health` now uses
  `line.lstrip().startswith("- [ ]")` to avoid counting prose references to
  checklist syntax.
- **`check_type_mismatch` FPGA false positive** (`#194`) — auto-detection is now skipped
  entirely when `config.type` is in `_EXPLICIT_ONLY_TYPES`.
- **Sync Markdown fallback in YAML mode** — `specsmith sync` falls back to Markdown
  parsing when YAML mode is active but no YAML requirement files exist.
- **Phase check H2 REQ headings** — `_req_count` now counts both `##` and `###` REQ
  headings, fixing false phase-readiness failures for projects using the `## REQ-` format.
- ruff format drift in `cli.py` and `mcp_server.py` resolved.

### Changed

- Documentation comprehensively updated: README, `docs/site/project-types.md`,
  `docs/site/skills-index.md`, `docs/site/configuration.md`.

---

## [0.11.7] - 2026-05-24

This release consolidates the full 0.11.x development cycle (0.11.0-0.11.6),
multi-agent dispatch, BYOE, and the foundational Applied Epistemic Engineering layer.
See git history for per-commit details on intermediate versions.

### Added — Pipx and update check

- **Pipx-only enforcement** — `specsmith` rejects invocations from non-pipx Python
  environments at startup with a clear error and install instructions.
  Override for CI: `SPECSMITH_ALLOW_NON_PIPX=1`.
- **Persistent 24-hour update check** — PyPI contacted at most once per
  `SPECSMITH_UPDATE_INTERVAL_HOURS` hours (default 24). Timestamp persisted to
  `~/.specsmith/last-update-check`. Disable: `SPECSMITH_NO_UPDATE_CHECK=1`.
- **Hardened `is_pipx_install()`** — detects Windows pipx venvs at `~/pipx/venvs/`
  without requiring `PIPX_HOME`.

### Added — Agentic REPL improvements

- **`specsmith run` silent no-response fix** — resolved three compounding bugs: wrong
  default Ollama model (404 swallowed silently), `_handle_command` returning `None`,
  and `EventEmitter.token()` emitting raw JSONL in interactive mode.
- **`PlainTextEmitter`** — new `EventEmitter` subclass; `token()` writes raw text,
  `emit()` is a no-op. Eliminates JSONL blobs in the interactive REPL.
- **`specsmith run --check`** — validates all LLM provider configurations, exits 0/1
  without starting the REPL.
- **`specsmith run` startup banner** — full provider status table (Ollama/Anthropic/
  OpenAI/Gemini) with resolved models and hints before the first prompt.
- **`_pick_ollama_model()`** — queries Ollama `/api/tags` and selects the first
  installed model from a preference list.
- **H23 governance rule** — "No bare sleep delays in scripts"; added to `RULES.md`
  and `specsmith validate` checker (`_check_bare_sleep()`).
- **`req trace` fix** — `_TEST_ID_PATTERN` extended to `\d+[a-z]*` to handle
  letter-suffix TEST IDs like `TEST-NN-002a`.

### Added — Codity.ai integration

- **`specsmith integrate codity`** — scaffolds AI code review CI workflows; supports
  GitHub (default), GitLab, and Azure DevOps; VCS auto-detected from `scaffold.yml`.
- **`codity-ai-review` governance skill** — full CLI workflow reference including
  install, auth, `codity review --staged`, VCS-specific PAT setup.
- **AGENTS.md template Codity section** — HIGH-severity findings block commits,
  MEDIUM requires inline acknowledgement (REQ-354/355/356).

### Added — Multi-Agent DAG Dispatcher

- **`specsmith dispatch` command group** (REQ-321..334) backed by
  `src/specsmith/agent/dispatch/`:
  - `TaskDAG`, `TaskDAGBuilder` — Kahn topological sort + cycle detection.
  - `AgentPool` — lazy per-role `ConversableAgent` pool with idle worker reuse.
  - `AgentDispatcher` — `ThreadPoolExecutor` scheduler with fail-forward BLOCKED
    propagation; writes ESDB `dispatch_result` records; injects predecessor context
    into successors.
  - `EventEmitter` — atomic JSONL event persistence to
    `.specsmith/dispatch/<dag_id>/events.jsonl` with SSE fan-out.
  - `specsmith dispatch run/status/list/retry` CLI subcommands.
- **Cooperative abort during LLM invocation** — `abort_node()` fires mid-call via
  daemon sub-thread; `_run_node` raises `_NodeAbortedError` immediately.
- **Compiler / tool support** — `run_gcc`, `run_arm_gcc`, `run_aarch64_gcc`,
  `run_iar_compiler`, `run_intel_compiler`, `run_clang_format`, `run_clang_tidy`,
  `run_vsg`; all 8 registered in `AVAILABLE_TOOLS` and `ROLE_TOOLS`.

### Added — ESDB extended lifecycle and channels

- **`specsmith channel` group** — `channel set {stable|dev}`, `channel get [--json]`,
  `channel clear`; persisted to `~/.specsmith/channel`.
- **ESDB extended lifecycle** (REQ-249..253) — `esdb export`, `esdb import`,
  `esdb backup`, `esdb rollback --steps N` (real restore from backup), `esdb compact`
  (real deduplication by ID).
- **Skills lifecycle** — `skills deactivate <skill-id>`, `skills delete <skill-id>`.
- **`specsmith mcp generate <description>`** — deterministic MCP server config stub
  from natural-language description.
- **`specsmith agent ask <prompt>`** — keyword dispatcher routes compliance/audit/
  skills/ESDB/MCP queries without an LLM.
- **60 new pytest tests** covering REQ-248..257.
- **12 CodeQL security fixes** — `py/path-injection` (10 via `_safe_resolve` /
  `_safe_file_read`), `py/http-response-splitting` (1), `py/incomplete-url-substring-
  sanitization` (1).
- **`specsmith issue` group** (REQ-303/304) — `check`, `file`, `search` with Jaccard
  similarity dedup against open GitHub issues.
- **`specsmith req add` / `specsmith test add`** (REQ-302) — YAML-first CLI commands
  that append directly to canonical YAML sources.

### Added — Governance structure overhaul

- **All governance files moved to `docs/`** — `REQUIREMENTS.md`, `TESTS.md`,
  `LEDGER.md`, `SPECSMITH.yml` (uppercase); `AGENTS.md` remains the only root-level
  governance file. Backward-compat via `find_scaffold()` / `find_ledger()` helpers.
- **`src/specsmith/paths.py`** — canonical path constants and lookup helpers with
  backward-compat root fallback.
- **`src/specsmith/safe_write.py`** — append-only + backup-protected governance writes.
  `append_file()` never truncates; `safe_overwrite()` creates a timestamped `.bak`.
  Satisfies EU AI Act Art. 12.
- **AI regulation compliance** (REG-001..REG-015) — EU AI Act, NIST AI RMF, OMB
  M-24-10, Colorado SB24-205, FTC, California ADMT. Key implementations:
  - `log_agent_action()` — SHA-256 chained tamper-evident agent action log.
  - `ToolSpec` + `build_tool_registry()` — explicit capability declarations.
  - `--escalate-threshold` — surfaces `escalation_required` when confidence < threshold.
  - `specsmith kill-session` — emergency kill-switch (EU AI Act Art. 14 s4).
  - `ai_disclosure` metadata in every preflight response (EU AI Act Art. 13/53).
  - `specsmith export` AI System Inventory (NIST AI RMF MANAGE).

### Added — Multi-agent, BYOE, voice, drive

- **`AgentRunner` + profiles** (`agent/runner.py`, `agent/profiles.py`,
  `agent/fallback.py`) — `specsmith agents` CLI group with `list/add/remove/test/route`.
- **Bring-Your-Own-Endpoint (BYOE)** — endpoints registry + openai-compat provider;
  `specsmith endpoints add/list/test/default/remove`.
- **Real token cost tracking** — per-provider `_UsageDelta`; costs flow into
  `AgentState.credit()` by profile bucket.
- **`specsmith voice transcribe`** — wraps optional `whisper-cpp-python`.
- **Specsmith Drive** — `push()`, `pull()`, `listing()`; mirrors rules/workflows/
  notebooks under `~/.specsmith/drive/<project>/`.
- **`specsmith api-surface`** — frozen 1.0 public surface JSON for CI diffing.
- **Real MCP JSON-RPC client** — `MCPSession` runs full MCP handshake
  (`initialize -> notifications/initialized -> tools/list`) against any server.
- Cloud Runs feature retired; `specsmith cloud spawn` and `cloud-serve` removed.

### Added — Applied Epistemic Engineering

- **`epistemic` standalone library** — zero-dep Python library; `from epistemic import
  AEESession` works in any Python 3.10+ project. Modules: `BeliefArtifact`,
  `StressTester` (8 challenge categories), `FailureModeGraph`, `CertaintyEngine`
  (CERTUS-inspired confidence scoring), `RecoveryOperator`, `TraceVault` (SHA-256 chain).
- **AEE CLI**: `specsmith stress-test`, `specsmith epistemic-audit`,
  `specsmith belief-graph`, `specsmith trace seal/verify/log`.
- **`specsmith run`** — AEE-integrated agentic REPL (Anthropic, OpenAI, Gemini, Ollama).
- **`specsmith serve`** — persistent HTTP server for agent sessions with SSE events,
  POST /api/send, GET /api/status.
- **7-phase AEE workflow tracker** (`specsmith phase`) —
  inception -> architecture -> requirements -> test-spec -> implementation ->
  verification -> release; per-phase readiness checklist and progress percentage.
- **`specsmith ollama` group** — `list`, `available [--task]`, `gpu`, `pull`,
  `suggest`; GPU-aware context sizing (4K/8K/16K/32K based on VRAM).
- **Skill marketplace** — `specsmith skill search/list/install`; built-in catalog.
- **Process tracking** — `specsmith exec`, `specsmith ps`, `specsmith abort`.
- **AI credit tracking** — `specsmith credits` (record, summary, report, analyze, budget).
- **H11/H12 governance rules** — deadline enforcement in agent scripts; Windows `.cmd`
  file requirement. `specsmith validate` scans scripts for infinite-loop patterns.
- **Proactive rate-limit pacing** — built-in RPM/TPM profiles for OpenAI, Anthropic,
  Gemini; `credits limits status/defaults` CLI.
- **FPGA project types** — `fpga-rtl-amd`, `fpga-rtl-intel`, `fpga-rtl-lattice`,
  `mixed-fpga-embedded`, `mixed-fpga-firmware`; full tool registry and CI templates.
- **30+ initial project types** — Python, Rust, Go, C, .NET, web, mobile, embedded,
  document, business, legal, and AEE research types.
- **`specsmith init`** / **`specsmith import`** — interactive scaffold wizard and
  project adoption.
- **`specsmith audit`** / **`specsmith validate`** — governance health and YAML schema.
- **`specsmith preflight`** / **`specsmith verify`** — change intent gating and
  post-execution equilibrium checks.

---

[Unreleased]: https://github.com/layer1labs/specsmith/compare/v0.16.1...HEAD
[0.16.1]: https://github.com/layer1labs/specsmith/compare/v0.16.0...v0.16.1
[0.16.0]: https://github.com/layer1labs/specsmith/compare/v0.15.3...v0.16.0
[0.15.3]: https://github.com/layer1labs/specsmith/compare/v0.15.2...v0.15.3
[0.15.2]: https://github.com/layer1labs/specsmith/compare/v0.15.1...v0.15.2
[0.15.1]: https://github.com/layer1labs/specsmith/compare/v0.14.1...v0.15.1
[0.14.1]: https://github.com/layer1labs/specsmith/compare/v0.13.0...v0.14.1
[0.13.0]: https://github.com/layer1labs/specsmith/compare/v0.11.7...v0.13.0
[0.11.7]: https://github.com/layer1labs/specsmith/releases/tag/v0.11.7
