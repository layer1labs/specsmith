# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Only versions published to PyPI are listed. Intermediate development versions are
consolidated into the next published release.

## [Unreleased]
### Added
- ESDB-first dual-write architecture (REQ-403..416) - Every governance event now writes to ESDB alongside the append-only LEDGER.md
- `specsmith inspect` command (REQ-409) - Session-start command that emits a bordered governance block with audit health, active work items, ESDB EFF-CURRENT efficiency stats, and epistemic quality breakdown
- M010 post-ESDB cleanup migration - Removes legacy files superseded by YAML+ESDB governance
- 49 new ESDB tests covering dual-write correctness, sweep runner, EFF-CURRENT computation, epistemic quality dimensions, audit chain validation, and ChronoStore compatibility paths
- 142 new agent/REPL/benchmark tests

### Changed
- Markdown governance mode deprecated - Running `specsmith sync` in markdown mode now emits a DeprecationWarning and auto-triggers m007 migration
- Auditor YAML dir checks are mode-aware - The yaml-requirements-dir and yaml-tests-dir audit checks now only fail for projects in YAML-first mode
- `specsmith architect` is now a group command - `specsmith architect` (without a subcommand) retains its original behavior, new subcommands `interview`, `gap`, and `update` are added
- Req-test coverage check uses testcases.json - In YAML-first mode, the auditor now also uses `requirement_id` from `testcases.json` and `test_ids` from `requirements.json` to determine test coverage

### Fixed
- Issue #263 - `esdb status --json` emitted bare "Aborted!" on Windows when Click's _winconsole stream detection raised a KeyboardInterrupt
- Issue #264 - `specsmith save` false positive dirty-tree warning - Post-commit _get_dirty_files() check now correctly ignores untracked files
- CI matrix: Python 3.10-3.13 fully green - _read_project_name in quality_report.py now uses tomllib → tomli → regex fallback chain so pyproject.toml is parsed correctly on Python 3.10

---

## [0.20.1] - 2026-06-29
Docs + packaging-metadata refresh. No changes to `src/specsmith/` runtime behavior
from 0.20.0 — this release exists primarily to refresh the README rendered on the
PyPI project page and to clear a CI deprecation warning.
### Changed
- **README refreshed for v0.20.0** — documents native Warp integration
  (`specsmith integrate warp` + Warp-aware REPL, REQ-444), VRAM-aware
  `specsmith local-model recommend` (REQ-445), corrected built-in skill count
  (138 across 16 domains) and the requirement domain-files table, and added the
  missing `brief-lang` project type to the grouped listing.
- **release-pilot skill** now documents the PR-merge flow for the protected `main`
  branch (tags point at the main merge commit) instead of a fast-forward push.
### Fixed
- **`release.yml` pypi-publish input** — renamed the deprecated `skip_existing`
  input to kebab-case `skip-existing` for `pypa/gh-action-pypi-publish`, clearing
  the deprecation warning on every tagged release.

---

## [0.20.0] - 2026-06-29

### Added

- **VRAM-aware local model recommendations (REQ-445)** — New first-class
  recommendation engine in `local_model.py`: `recommend_models(vram_gb)` and
  `recommend_for_hardware()` produce a complete role lineup (default / fast /
  harder pass / general) keyed by the detected GPU VRAM tier, with a per-model
  fit assessment (`fits` / `tight` / `spills`) computed against an approximate
  Q4 footprint catalog so CPU-spillover is flagged before you pull. The lineup
  includes `deepseek-coder-v2:16b` for the heavier "harder C/Python pass" slot.
  Surfaced via the new `specsmith local-model recommend` command (+ `--json`).
  Existing `detect_local_model` / `detect_local_models` behavior is unchanged.

- **Native Warp integration (REQ-444)** — New `warp` integration adapter:
  `specsmith integrate warp` generates `.warp/specsmith-mcp.json` (governance MCP
  config, identical to `specsmith mcp install-warp`),
  `.warp/launch_configs/specsmith-governed.yaml` (a Warp launch configuration that
  opens a governed `specsmith run` session), and the shared `.agents/skills/SKILL.md`.
  The MCP-config JSON is now produced by a shared `build_warp_mcp_config()` helper in
  `mcp_server.py` consumed by both `mcp install-warp` and the adapter. The `warp`
  name is now a first-class adapter (previously a legacy alias to `agent-skill`).
  Added `.agents/skills/warp-integration/SKILL.md`.

- **Warp-aware REPL (REQ-444)** — New `specsmith.agent.terminal_env.detect_terminal()`
  detects when `specsmith run` is hosted inside Warp (via `TERM_PROGRAM` / `WARP_*`
  env vars). The interactive banner shows a `terminal: Warp … — native integration
  active` line and the JSON `ready` frame carries a `terminal` field. Behavior is
  unchanged outside Warp.

### Fixed

- **`specsmith integrate` scaffold lookup** — `integrate` now locates project config
  via `find_scaffold()`/`find_requirements()` (canonical `docs/SPECSMITH.yml` /
  `docs/REQUIREMENTS.md` with legacy fallback) and normalizes legacy keys, instead of
  hardcoding `scaffold.yml` / `docs/REQUIREMENTS.md`.

- **Benchmark CI workflow on Node 24** — `bench.yml` bumped `actions/checkout@v6→v7`,
  `actions/upload-artifact@v4→v7`, and `actions/download-artifact@v4→v8` to clear the
  Node 20 deprecation warnings and align with the rest of the repo's workflows.

---

## [0.19.2] - 2026-06-28

### Added

- **HuggingFace provider for GovernanceBench (REQ-427)** — `provider=huggingface` in
  `harness.py` routes agent calls through the HF Inference API
  (`https://api-inference.huggingface.co/v1/`), which is OpenAI-compatible. Authenticated
  via `HF_TOKEN`. Five open-source models added as a new `open_source` tier in the
  benchmark matrix: `Qwen/Qwen2.5-7B-Instruct`, `Qwen/Qwen2.5-72B-Instruct`,
  `meta-llama/Llama-3.1-8B-Instruct`, `meta-llama/Llama-3.3-70B-Instruct`,
  `mistralai/Mistral-7B-Instruct-v0.3`. `HF_TOKEN=` added to `.env.example`.

- **Full multi-provider benchmark matrix — 15 models × 5 tiers × 4 providers (REQ-427)**
  — `bench.yml` rewritten with `include:` matrix entries covering
  `nano/mini/mid/frontier/open_source`. API key gate skips jobs gracefully when
  a secret is not configured. `compare` job discovers all model artifacts dynamically.
  Default `reps` bumped to **5** (publication-quality Wilson CI intervals).

- **Smoke test now validates both OpenAI and HuggingFace providers** — The dry-run
  smoke job runs two benchmark passes: OpenAI (`gpt-4o-mini`) and HuggingFace
  (`Qwen/Qwen2.5-7B-Instruct`), both in `--dry-run` mode, catching provider-path
  regressions on every push.

- **REQ-437–443: Gap coverage for 4 feature areas + 3 CLI commands** — Added planned
  requirements for: datasource adapter contracts (REQ-437), GUI governed parity
  (REQ-438), IDE integration contracts (REQ-439), plugin lifecycle (REQ-440),
  `plugin` CLI surface (REQ-441), `pr` CLI surface (REQ-442), `ps` CLI surface
  (REQ-443). Placeholder tests TEST-453–459 added. REQ coverage now spans all
  major module families and CLI commands identified in the gap report.

### Fixed

- **Closed 11 stale open WIs** — WI-51D364FC through WI-4A06F23E and WI-1C05961C
  were all implemented but left open. All closed with test links confirmed.
  `specsmith audit` returns **Healthy — 59 checks passed**.

---

## [0.19.1] - 2026-06-28

### Fixed

- **`check_governance_yaml_content` now accepts m001 content-blob format (REQ-432)**
  — Governance YAML files generated by `specsmith migrate m001` use a
  `content: '...' / kind: <stem>` structure rather than the `<stem>: [...]` list
  format the check originally required. The auditor now recognises this format as
  valid, clearing the 7 false-positive `governance-yaml:*` audit failures that
  appeared after upgrading to 0.19.0. Added regression test
  `test_check_governance_yaml_content_passes_m001_content_blob`.

---

## [0.19.0] - 2026-06-28

### Added

- **`specsmith wi link-test`** — New CLI command to link one or more `TEST-NNN` IDs to a work
  item (`wi link-test <WI_ID> --test TEST-NNN`, repeatable). Clears the `linked tests` gate
  that the auditor checks on medium-risk WIs. Backed by `WorkItemStore.add_test_case_ids()`
  which deduplicates and persists test case IDs to `workitems.json` + ESDB.

- **`check_governance_yaml_content` auditor check (REQ-432)** — `specsmith audit` now validates
  every file under `.specsmith/governance/*.yaml`: confirms the top-level key matches the file
  stem, rejects empty lists, and rejects single `{note: …}` fallback entries. Wired into
  `run_audit()`. Migration `m001_governance_yaml` now emits warnings (not silent no-ops) when
  expected source markdown files are missing.

- **Sync markdown-reconcile warning (REQ-433)** — `specsmith sync` now emits a `SyncWarning`
  when `REQUIREMENTS.md` or `TESTS.md` contain IDs (e.g. `REQ-NNN`, `TEST-NNN`) that are
  absent from the YAML source files, alerting teams to IDs that exist only in the deprecated
  markdown layer. `scripts/rebuild_workitems.py` also fixed to pass `ensure_ascii=False` to
  `json.dump`, preventing unicode mojibake in work-item exports.

- **WI lifecycle: `verify_cmd` wiring + `files_touched` + `human_review_status` (REQ-434)**
  — `specsmith verify --work-item-id <WI>` now calls `governance_logic.run_verify` when
  equilibrium is reached, automatically transitioning the WI to `implemented` and persisting
  `files_touched`. `specsmith approve` sets `human_review_status="approved"` on the bound WI.
  `WorkItemStore.set_files_touched()` is fully wired in both the CLI and the governance layer.

- **Broker scope `min_score` threshold (REQ-435)** — `infer_scope` in `broker.py` now
  applies a `min_score=0.15` threshold; requirement matches below this confidence floor are
  dropped. `run_preflight` passes this threshold through, preventing spurious scope
  attribution from weak token overlap. Guards against false-positive `accepted` decisions
  caused by single-word matches.

- **Session metrics flush (REQ-436)** — `flush_session_metrics()` in `project_metrics.py`
  now appends a structured JSON record (session ID, total tokens, model, timestamp) to
  `.specsmith/session_metrics.jsonl` after every governed run. `runner.py` calls
  `flush_session_metrics()` after `write_token_metric`, completing the token-usage pipeline
  from agent run → ESDB → JSONL audit log.

- **Requirements gap report** (`docs/REQUIREMENTS_GAP_REPORT.md`) — Comprehensive audit
  of feature coverage: 47 CLI commands inventoried, 4 feature families without explicit REQs
  identified (datasources, GUI, external integrations, plugin lifecycle), and 3 commands
  lacking explicit requirement linkage flagged (plugin, pr, ps).

### Fixed

- **`test_needs_clarification_does_not_create_wi`** renamed and corrected to
  `test_needs_clarification_destructive_creates_wi` — REQ-431 intentionally allocates a WI
  for DESTRUCTIVE/RELEASE `needs_clarification` decisions so users can pass `--work-item` on
  retry. The old test asserted no-WI; the new test asserts WI IS created. A companion test
  (`test_needs_clarification_scope_creep_does_not_create_wi`) verifies non-destructive
  ambiguous CHANGE intents still produce no WI.

---

## [0.18.0] - 2026-06-26

### Added

- **ESDB-first dual-write architecture (REQ-403..416)** — Every governance event now writes
  to ESDB alongside the append-only `LEDGER.md`. `esdb_writer.py` provides atomic writer
  helpers; `efficiency.py` computes rolling `EFF-CURRENT` (tokens/pass, cost-of-pass, EuTB
  metric, and 5-dimension epistemic quality score); `esdb_sweep.py` back-fills ESDB from the
  existing ledger on first activation. `ledger.py`, `trace.py`, and `project_metrics.py`
  all participate in dual-write.

- **`specsmith inspect`** (REQ-409) — Session-start command that emits a bordered governance
  block: audit health, active work items, ESDB `EFF-CURRENT` efficiency stats
  (tokens/correct-answer, context fill rate), and the 5-dimension epistemic quality breakdown
  (confidence density, recency, coherence, closure, non-contradiction). `--json` flag for
  machine-readable output. Replaces `specsmith checkpoint` as the recommended agent
  context-injection call at the start of every session.

- **Benchmark tasks T10–T13** — Three new `govern_bench` scenarios: T10 (add stats
  endpoint), T11 (add tags field), T13 (ambiguous production-readiness prompt); `bench.yml`
  workflow updated to include these tasks in the default `workflow_dispatch` task set.

- **`specsmith.agent.token_pricing` module** — `cost_for_tokens(model, input_tokens,
  output_tokens)`, `cost_for_tokens_breakdown(...)`, and `tokens_per_correct_answer(...)` with
  Q2-2026 pricing for 20+ OpenAI, Anthropic, and Google models. Ollama models always return
  `0.0` (free local inference). Import with
  `from specsmith.agent.token_pricing import cost_for_tokens`.

- **49 new ESDB tests** (TEST-404..411) covering dual-write correctness, sweep runner,
  `EFF-CURRENT` computation, epistemic quality dimensions, audit chain validation, and
  ChronoStore compatibility paths.

- **142 new agent/REPL/benchmark tests** — `tests/test_token_cost.py` (57 tests),
  `tests/test_parallel_agents.py` (37 tests), `tests/test_repl_extended.py` (30 tests),
  `tests/test_benchmark_harness.py` (27 tests).

- **M010 post-ESDB cleanup migration** — `specsmith migrate run` removes files now
  superseded by YAML+ESDB governance: `docs/REQUIREMENTS.md`, `docs/TESTS.md`,
  `.specsmith/requirements.json`, `.specsmith/testcases.json`, the M006 AGENTS.md backup,
  and old `migration-backups/` dirs (newest kept). Guards require all YAML source files
  and ESDB marker files to exist before deletion; idempotent via migration marker file.

### Fixed

- **`write_token_metric` ESDB guard** — returns `False` gracefully when the ESDB SQLite
  file does not yet exist (e.g. fresh project before first `specsmith audit`).

- **mypy strict compliance** — added `from typing import Any` to `token_pricing.py`;
  resolved `Sequence` covariance annotation in `context_seed.py`; fixed `TypedDict`
  narrowing in M008 migration; resolved type-arg errors in `test_parallel_agents.py`.

- **ruff format** — reformatted 8 files after ESDB-first changes to satisfy `ruff format --check`.

---

## [0.17.1] - 2026-06-25

### Fixed

- **Issue #265 — scaffold canonical path/schema mismatch** — All CLI commands
  (`migrate`, `apply`, `tools scan`, `diff`, `doctor`, `validate`, `export`,
  `ci enable`, `upgrade`, `push`, `create-pr`, `save`) now locate the scaffold
  config via `find_scaffold()` from `paths.py`, which checks `docs/SPECSMITH.yml`
  (canonical) before `scaffold.yml` (legacy). Previously these commands
  hardcoded `root / "scaffold.yml"`, silently failing for projects already
  migrated to the canonical path.

- **Legacy `project:` key normalization** — Added `_normalize_scaffold_raw()`
  to `config.py`. All `ProjectConfig(**raw)` call sites now pass raw YAML
  through this helper first, mapping the legacy `project:` key to `name:` so
  scaffold files created by specsmith ≤ 0.9 continue to load without a
  `ValidationError`.

- **`updater.py` migration log message** — The `run_migration()` action log
  now reports the actual filename (`SPECSMITH.yml` or `scaffold.yml`) instead
  of always saying `"Updated scaffold.yml"`.

- **`vcs_commands.run_sync` governance watch-list** — `docs/SPECSMITH.yml` is
  now included alongside `scaffold.yml` in the list of governance files that
  trigger a post-pull warning when changed upstream.

- **8 CodeQL alerts resolved (all alerts → 0)**:
  - `governance_logic.py` — inline `os.path.realpath()` so CodeQL tracks the
    taint sanitizer correctly (`py/path-injection`).
  - `quality_report.py` — removed duplicate `\'` from two regex character
    classes (`py/regex/duplicate-in-character-class`); replaced adjacent string
    literals with explicit `+` concatenation
    (`py/string-concat-implicit-operands`); replaced bare
    `except ValueError: pass` with `contextlib.suppress(ValueError)`
    (`py/empty-except`).
  - `cli.py` — consolidated `specsmith.esdb` imports to a single
    `import specsmith.esdb as _esdb_mod_dr` style throughout the `doctor`
    command, removing `from specsmith.esdb import …` mixed usage
    (`py/import-and-import-from`); replaced `try/except OSError: pass`
    with `contextlib.suppress(OSError)` (`py/empty-except`).

---

## [0.17.0] - 2026-06-25

### Added

- **`specsmith architect interview`** — Epistemic BA interview system that asks 9 targeted
  questions (problem domain, users, integrations, constraints, deployment, scale, data model,
  security, failure modes), tracks per-dimension confidence, and produces `docs/ARCHITECTURE.md`
  with confidence annotations and `docs/requirements/proposed.yml` with draft REQs.
  Session state is crash-safe (persisted to `.specsmith/arch-interview.json`).
  Non-interactive/CI mode auto-generates synthetic answers.

- **`specsmith architect gap`** — Diffs current `ARCHITECTURE.md` against a stored snapshot;
  proposes new REQs for added sections and flags potentially-stale REQs for removed sections.
  Outputs `docs/requirements/arch-gap.yml` and `docs/tests/arch-gap.yml`.

- **`specsmith architect update`** — Re-engages the BA interview for a project with existing
  `ARCHITECTURE.md`, restoring confidence from inline annotations and running gap analysis.

- **`specsmith cleanup`** — Removes runtime cache files (runs, sessions, chat, perf, recovery,
  logs, dispatch, pids, agent-reports, migration-backups, chronomemory/backup, Python caches).
  Dry-run by default; `--apply` to delete; `--json` for structured output.
  Protected files (requirements.json, testcases.json, governance-mode, YAML source dirs) are
  never removed.

- **`specsmith esdb switch-backend`** — Migrates ESDB records between SQLite and ChronoStore.
  `--to chronomemory` requires a valid ESDB license. `--to sqlite` requires `--confirm-data-loss`.

- **ESDB auto-promotion** — When ChronoStore is selected but SQLite has existing records and
  ChronoStore is empty, specsmith prompts to migrate records automatically. Auto-accepts in
  non-interactive/agent mode (`SPECSMITH_AGENT=1`).

- **YAML-first governance for new projects** — `specsmith init` now writes
  `.specsmith/governance-mode=yaml` and creates `docs/requirements/core.yml` +
  `docs/tests/core.yml` starter files. New projects are in YAML-first mode from day one.

- **m007 migration** — `specsmith migrate run` now includes m007 which converts
  `docs/REQUIREMENTS.md` and `docs/TESTS.md` to YAML source files under `docs/requirements/`
  and `docs/tests/`. Idempotent and non-destructive (MD files are not deleted).

- **BA Interview SKILL.md** — `.agents/skills/specsmith-architect/SKILL.md` documents the
  epistemic BA interview protocol for AI agent use.

- **BA project-type detection** — `specsmith import` now detects BA (Business Analyst)
  project types and enriches scaffold metadata with domain classification, stakeholder
  roles, and integration surface signals extracted from the project structure.

- **Feature gap catalog + `specsmith github issues`** — Scans governance YAML and open
  GitHub issues to identify feature gaps; generates a gap catalog and can bulk-create
  GitHub issues via `gh` CLI (`specsmith github issue-plan|issue-create`).

- **`specsmith resume` / `specsmith load`** — Resume a previous agent session from the
  last LEDGER.md entry; `load` restores full session context without starting the REPL.

- **Multi-model routing for `specsmith run`** — `AgentRunner` now auto-detects the
  intent of each user turn (general / coding / reasoning) and routes to the best local
  Ollama model for that role using `ModelRouter`. Hardware-tier–aware detection via
  `detect_local_models()`. New `/models` slash command shows the current routing table.
  Model switches are announced inline so users always know which model is active.

- **Local model hardware selector** — `detect_local_models()` queries available Ollama
  models and categorises them by role (general / coding / reasoning) using heuristics
  based on model name and hardware tier (CPU-only → 7B cap; GPU ≥ 8 GB → up to 32B).
  Config is saved to `.specsmith/local-models.yml` and reloaded across sessions.

- **Guided Ollama setup** — When `specsmith run` is invoked with no configured provider,
  the CLI now detects whether Ollama is installed and prints step-by-step setup instructions
  with the recommended `ollama pull` commands for each hardware tier.

### Changed

- **Markdown governance mode deprecated** — Running `specsmith sync` in markdown mode now
  emits a `DeprecationWarning` and auto-triggers m007 migration. Markdown mode will be
  removed in a future release. Run `specsmith migrate run` to upgrade.

- **Auditor YAML dir checks are mode-aware** — The `yaml-requirements-dir` and
  `yaml-tests-dir` audit checks now only fail for projects in YAML-first mode. Legacy
  markdown-mode projects get an informational pass.

- **`specsmith architect` is now a group command** — `specsmith architect` (without a
  subcommand) retains its original behavior (scan + generate architecture docs). New
  subcommands `interview`, `gap`, and `update` are added.

- **Req-test coverage check uses testcases.json** — In YAML-first mode, the auditor
  now also uses `requirement_id` from `testcases.json` and `test_ids` from
  `requirements.json` to determine test coverage, rather than only TESTS.md.

- **ChronoMemory bumped to `>=0.2.7`** — The `specsmith[esdb]` extra now requires
  chronomemory 0.2.7 or newer (available on PyPI). The git-URL dependency is fully
  replaced; `pip install specsmith[esdb]` works without any extra index.

### Fixed

- **Issue #263 — `esdb status --json` emitted bare "Aborted!"** on Windows when Click's
  `_winconsole` stream detection raised a `KeyboardInterrupt`. Now uses `sys.stdout.write`
  directly; on write failure writes a structured JSON error payload to stderr and exits 1.

- **Issue #264 — `specsmith save` false positive dirty-tree warning** — Post-commit
  `_get_dirty_files()` check now correctly ignores untracked files so a clean commit
  no longer triggers a spurious warning.

- **CI matrix: Python 3.10–3.13 fully green** — `_read_project_name` in `quality_report.py`
  now uses `tomllib` → `tomli` → regex fallback chain so `pyproject.toml` is parsed
  correctly on Python 3.10 (where `tomllib` is not in stdlib). Chronomemory-dependent
  ESDB status tests now use `patch.dict(sys.modules)` to inject a `MagicMock`, removing
  the need for chronomemory to be installed in the test environment.

---

## [0.16.5] - 2026-06-25

### Added

- **Published `COMMERCIAL-LICENSE.md` in specsmith** as the canonical public
  terms document for the **ChronoMemory commercial ESDB backend**.

### Changed

- ESDB docs and install guidance now link directly to
  `COMMERCIAL-LICENSE.md` and explicitly distinguish:
  - ChronoMemory commercial backend licensing scope, and
  - SQLite default backend (`specsmith`) remaining MIT/free.

---

## [0.16.4] - 2026-06-24

### Changed

- **Codity AI Review removed from specsmith's default CI** —
  `.github/workflows/codity-review.yml` deleted from the specsmith repository.
  The check was failing on every pull request because `CODITY_ACCESS_TOKEN`
  is not a required repo secret. Codity remains a fully supported opt-in
  integration: run `specsmith integrate codity` to scaffold the workflow into
  your own project.

---

## [0.16.3] - 2026-06-24

### Changed

- **Docs navigation tab ergonomics** — `mkdocs.yml` now keeps Material
  `navigation.tabs` enabled while grouping pages under fewer top-level
  categories (`Getting Started`, `Foundations`, `Agentic Runtime`,
  `Reference`, `ESDB`, `Benchmarks`) to reduce tab overflow.
- **MkDocs defaults and guidance aligned** — the scaffold docs template
  (`src/specsmith/templates/docs/mkdocs.yml.j2`) now enables
  `navigation.expand`, `search.suggest`, and `navigation.tabs`; the MkDocs
  skill example (`src/specsmith/skills/docs.py`) now demonstrates grouped
  top-level navigation.

---

## [0.16.2] - 2026-06-23

### Fixed

- **Issue #257 — `audit industrial_artifacts` false positive on Windows** —
  `check_industrial_artifacts` now handles both plain-string entries
  (`- path/to/file.eds`) and dict entries (`- path: ..., device: ...`) in
  `canopen_eds`. Previously only dict entries were matched, so string-format
  declarations always appeared undeclared regardless of OS.
- **6 CodeQL alerts resolved (all alerts → 0)**:
  - `src/specsmith/sync.py` — `...` replaced with `pass` in `_MigratableStore`
    Protocol stub methods (`py/ineffectual-statement` #192 #193).
  - `scripts/govern_bench/harness.py` — removed dead variable initializations
    before an if/elif/else block that always assigns all four variables
    (`py/multiple-definition` #196).
  - `scripts/govern_bench/projects/` — excluded from CodeQL via
    `.github/codeql/codeql-config.yml`; this directory contains intentional
    benchmark bugs (mutable default argument = the T2 task agents must fix)
    (`py/modification-of-default-value` #195, `py/unused-global-variable` #197,
    `py/import-and-import-from` #194).
- **Pre-existing broken test fixed** — `test_industrial_artifacts_normalizes_
  windows_declared_paths` was writing double-backslash to YAML which normalised
  to `//` and never matched the found path; corrected to a single backslash.

### Added

- Two regression tests for #257: plain-string-only entries and mixed
  string+dict entries in `canopen_eds`.

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

[Unreleased]: https://github.com/layer1labs/specsmith/compare/v0.20.1...HEAD
[0.20.1]: https://github.com/layer1labs/specsmith/compare/v0.20.0...v0.20.1
[0.20.0]: https://github.com/layer1labs/specsmith/compare/v0.19.2...v0.20.0
[0.17.1]: https://github.com/layer1labs/specsmith/compare/v0.17.0...v0.17.1
[0.17.0]: https://github.com/layer1labs/specsmith/compare/v0.16.5...v0.17.0
[0.16.5]: https://github.com/layer1labs/specsmith/compare/v0.16.4...v0.16.5
[0.16.4]: https://github.com/layer1labs/specsmith/compare/v0.16.3...v0.16.4
[0.16.3]: https://github.com/layer1labs/specsmith/compare/v0.16.2...v0.16.3
[0.16.2]: https://github.com/layer1labs/specsmith/compare/v0.16.1...v0.16.2
[0.16.1]: https://github.com/layer1labs/specsmith/compare/v0.16.0...v0.16.1
[0.16.0]: https://github.com/layer1labs/specsmith/compare/v0.15.3...v0.16.0
[0.15.3]: https://github.com/layer1labs/specsmith/compare/v0.15.2...v0.15.3
[0.15.2]: https://github.com/layer1labs/specsmith/compare/v0.15.1...v0.15.2
[0.15.1]: https://github.com/layer1labs/specsmith/compare/v0.14.1...v0.15.1
[0.14.1]: https://github.com/layer1labs/specsmith/compare/v0.13.0...v0.14.1
[0.13.0]: https://github.com/layer1labs/specsmith/compare/v0.11.7...v0.13.0
[0.11.7]: https://github.com/layer1labs/specsmith/releases/tag/v0.11.7
