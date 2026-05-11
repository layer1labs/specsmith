# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.11.2] — 2026-05-11
### Added
- **esdb rollback real restore (REQ-252)** — now finds the N-th most recent backup in .specsmith/backups/ and restores equirements.json + 	estcases.json from it. Exits non-zero when no backups exist.
- **esdb compact real deduplication (REQ-253)** — reads .specsmith/requirements.json and .specsmith/testcases.json, deduplicates by ID (last-write-wins), drops ID-less entries, writes compacted lists back to disk.
- **12 CodeQL security fixes** — py/path-injection (10): _safe_resolve() + _safe_file_read() helpers reject null bytes and .. traversal before file reads; py/http-response-splitting (1): strip CR/LF from HTTP response headers; py/incomplete-url-substring-sanitization (1): urlparse() hostname comparison in test.
### Changed
- esdb import now writes directly to .specsmith/requirements.json and .specsmith/testcases.json (real persistence, not staging).
- esdb rollback --steps N selects the Nth most recent backup (1 = latest).
- Test suite updated to match new esdb rollback/compact contracts. 670 passing.
### Validation
- pytest: **670 passed, 2 skipped, 5 xfailed**.
- uff check + uff format --check: clean.
## [0.11.1] â€” 2026-05-11
### Added
- **`specsmith channel` group (REQ-248)** â€” `channel set {stable|dev}`, `channel get [--json]`, `channel clear`. Persists preferred update channel to `~/.specsmith/channel`; `self-update` and project-update checks honour the resolved channel.
- **ESDB extended lifecycle (REQ-249..253)** â€” five new `esdb` subcommands with `--json` flag:
  - `esdb export [--output PATH]` â€” JSON snapshot of all records.
  - `esdb import <source>` â€” validate + stage a JSON export.
  - `esdb backup [--dir DIR]` â€” timestamped snapshot (ISO UTC filename).
  - `esdb rollback [--steps N]` â€” WAL rollback report (stub mode).
  - `esdb compact` â€” WAL compaction request (stub mode).
- **Skills lifecycle (REQ-254..255)** â€” two new `skills` subcommands:
  - `skills deactivate <skill-id>` â€” set `active: false` in `skill.json`.
  - `skills delete <skill-id> [--yes]` â€” permanently remove skill directory.
- **`specsmith mcp generate <description> [--json]` (REQ-256)** â€” deterministic MCP server config stub from natural-language description.
- **`specsmith agent ask <prompt> [--json-output]` (REQ-257)** â€” keyword dispatcher routes compliance/audit/skills/esdb/mcp/session queries without an LLM.
- **Kairos settings integration (REQ-258..262)** â€” Specsmith umbrella in sidebar (ESDB, Skills, Eval pages), AI Providers table with column clipping, MCP AI Builder card.
- **60 new pytest tests** (`tests/test_req_248_262.py`) â€” regression coverage for REQ-248..257; Kairos UI tests registered as xfail.
- **docs/REQUIREMENTS.md** â€” REQ-248..REQ-262 defined and linked to architecture.
- **docs/TESTS.md** â€” TEST-248..TEST-262 with pytest cross-references.
- **ARCHITECTURE.md** â€” new sections: Update Channel, AI Skills Builder Phase A, ESDB Extended, MCP Generator, Agent Ask Dispatcher, Kairos Settings Extensions.
- **docs/site/commands.md** â€” documented `channel`, extended `esdb`, extended `skills`, `mcp generate`, `agent ask`.
### Changed
- CI badge and sponsor links updated from `BitConcepts` â†’ `layer1labs`.
- Kairos repo migrated to `layer1labs/kairos`; specsmith repo to `layer1labs/specsmith`.
- `specsmith-vscode` extension deprecated; Kairos is the flagship client.
### Validation
- `pytest`: **669 passed, 2 skipped, 5 xfailed**.
- `ruff check` + `ruff format --check`: clean.
- `api-surface` snapshot: updated.

## [0.11.0] â€” 2026-05-07
### Added
- **Governance structure overhaul** â€” all governance files (REQUIREMENTS.md, TESTS.md, LEDGER.md, scaffold config) moved to `docs/`; `AGENTS.md` remains the only root-level governance file. Backward compatibility preserved via `find_scaffold()` / `find_ledger()` helpers.
- **`docs/SPECSMITH.yml`** â€” scaffold config renamed to uppercase (`SPECSMITH.yml`) for consistency with all other uppercase governance files. `paths.py` constant `SCAFFOLD_FILE = "SPECSMITH.yml"`.
- **`src/specsmith/paths.py`** â€” canonical path constants (`DOCS_DIR`, `SCAFFOLD_FILE`, `SCAFFOLD_REL`, etc.) and lookup helpers (`find_scaffold`, `find_ledger`, `find_requirements`, `find_tests`) with backward-compat root fallback.
- **`src/specsmith/safe_write.py`** â€” append-only + backup-protected governance file writes. `append_file()` never truncates; `safe_overwrite()` creates a timestamped `.bak` before any overwrite; `json_append()`, `compute_diff()`, SHA-256 integrity helper, and atomic temp+rename writes throughout. Satisfies REG-007/REG-008.
- **AI regulation compliance (REG-001..REG-015)** â€” 15 requirements from BTWS 2027 Agentic AI Governance Report (EU AI Act, NIST AI RMF, OMB M-24-10, Colorado SB24-205, FTC, California ADMT, Utah SB149). Key implementations:
  - REG-001: `log_agent_action()` in `tools.py` â€” SHA-256 chained tamper-evident agent action log at `.specsmith/agent-actions.jsonl`.
  - REG-002: `ToolSpec` + `build_tool_registry()` â€” explicit capability declaration for all 12 agent tools.
  - REG-004: `specsmith preflight --escalate-threshold <float>` â€” surfaces `escalation_required` when confidence < threshold.
  - REG-005: `specsmith kill-session [--reason]` â€” emergency kill-switch; terminates all tracked sessions and records a kill-switch ledger event.
  - REG-007: `upgrader.py` uses `safe_overwrite()` for governance template regeneration.
  - REG-009: `specsmith preflight` output includes `ai_disclosure` metadata (governed_by, provider, model, spec_version).
  - REG-010: `specsmith export` includes **AI System Inventory** section (agent capabilities, EU AI Act risk tier, human oversight controls).
  - REG-012: Least-privilege agent permissions â€” `ToolSpec` epistemic contracts declare filesystem-mutating tools.
- **Phase checks updated** â€” all phase checks now use canonical `docs/` paths (`docs/REQUIREMENTS.md`, `docs/SPECSMITH.yml`, `docs/LEDGER.md`).
- **76 planned architecture requirements migrated** (REQ-130..REQ-205): OPS, CMD, MAS, ORC, FLG, LRN, EDD, MEM, HRK, SRV, RTR, MCP, SEC, IDE domains.
- **15 AI regulation requirements added** (REQ-206..REQ-220).
- **docs/COMPLIANCE.md** â€” machine-generated compliance export with AI System Inventory, REQâ†”TEST coverage, audit summary, and governance file inventory.
- **`specsmith audit`** â€” duplicate-file enforcement: warns when root copy AND `docs/` canonical copy both exist.
- **kairos** â€” sister repository (`BitConcepts/kairos`) bootstrapped: Rust governance client (`src/governance/client.rs`, `server.rs`, `mod.rs`) with `GovernanceClient` (health/preflight/verify), `GovernanceServer` (managed child process), `GovernanceConfig` with I2 invariant enforcement.
### Changed
- `ledger.py`: `add_entry()` / `list_entries()` use `find_ledger()` (docs/LEDGER.md canonical).
- `compressor.py`: uses `find_ledger()` + `safe_overwrite()`.
- `auditor.py`: `_get_thresholds()` and `check_phase_readiness()` use `find_scaffold()`.
- `phase.py`: all phase checks updated for canonical docs/ paths.
- `cli.py`: `init` writes to `docs/SPECSMITH.yml`; `_maybe_prompt_project_update` uses `find_scaffold()`.
- `upgrader.py`: `run_upgrade()` uses `find_scaffold()`; governance templates use `safe_overwrite()`.
- `exporter.py`: `run_export()` uses `find_scaffold()`; adds AI System Inventory.
### Validation
- `pytest`: **448 passed, 1 skipped**.
- `ruff`: clean.
- `api-surface` snapshot: regenerated with `kill-session` command.

## [0.10.1] â€” 2026-05-04
### Added â€” Multi-Agent + BYOE (rolled into the 0.10.x line)
- **`AgentRunner` + ready event (REQ-145).** New `agent/runner.py` with `_print_banner()` emitting a JSONL `ready` event, slash-command dispatch (`/agent`, `/profile`, `/status`), `AgentState` metrics, and `_hard_stop` cleanup. `agent/core.py` adds the `ModelTier` enum.
- **Agent profiles + activity routing (REQ-146).** `agent/profiles.py` (`Profile`, `ProfileStore`, `RoutingTable`), `agent/fallback.py` (transient-aware fallback chain with `FallbackAttempt` / `FallbackResult` dataclasses), `templates/agent-profiles.default.json` presets (default / local-only / frontier-only / cost-conscious), and a full `specsmith agents` CLI group (`list`, `add`, `remove`, `default`, `test`, `route`, `preset`). `--agent <id>` flag accepted on `chat`, `run`, and `serve`.
- **Bring-Your-Own-Endpoint (REQ-142, BYOE 0.8.0).** Endpoints registry + openai-compat provider; `specsmith endpoints add/list/test/default/remove`.
- **CLI JSON surfaces.** `specsmith phase show --json`, `specsmith mcp list/test/start/stop --json`, `specsmith rules list --json`, `specsmith notebook new <slug> [--from-run]` + `templates/notebook.md.j2`.
- **`api-surface` CI guard.** New CI job diffs live `specsmith api-surface` output against `tests/fixtures/api_surface.json`.
- **Diversity guard.** `ProfileStore.diversity_warnings` + `PROVIDER_FAMILIES` table warns when the reviewer/architect shares a provider family with the coder. CLI prints yellow warnings (non-fatal); `--json` output includes `diversity_warnings`.
- **Capability filter.** `ProfileStore.filter_by_capability` + `specsmith agents list --capability <cap>` flag.
- **Phase auto-routing.** `specsmith phase next` now auto-pins `phase:active` to the new phase's preferred profile and seeds `phase:<key>` if absent.
- **TraceVault seal on `/agent`.** `runner._seal_profile_pin()` writes a `decision` seal into `.specsmith/trace.jsonl` whenever the in-chat `/agent <id>` command pins a profile.
- **Real token cost threading.** Each provider driver now returns `(text, _UsageDelta)` with real token counts (Ollama `prompt_eval_count`+`eval_count`, Anthropic `final_message.usage`, OpenAI `stream_options.include_usage`, Gemini `usage_metadata`); 4-chars/token fallback. Counts flow into `ChatRunResult.tokens_in/out/cost_usd` and `AgentState.credit()`'s `by_profile` bucket.
- **`tests/test_fallback_chain.py`** â€” 33 new tests covering parse_target, transient HTTPError 408/429/5xx + network errors, non-transient 4xx + RuntimeError, blank-target skip, on_attempt callback resilience.
- **Docs.** `docs/site/agents.md` (preset â†’ route â†’ per-session â†’ BYOE walkthrough), `docs/site/quickstart.md` reproduction script, README "0.10.0 â€” Multi-Agent + BYOE" elevator pitch.
- **`.pre-commit-config.yaml`** with ruff + ruff-format + pre-commit-hooks.
### Removed
- **Cloud Runs feature retired.** `specsmith cloud spawn`, `specsmith cloud-serve`, `src/specsmith/cloud_serve.py`, `docs/site/cloud-agents.md`, the `.specsmith/cloud/` storage convention, and all related tests/fixtures have been removed. The deferred REQ-126/REQ-136 cloud-agent surface is no longer part of the 1.0 contract.
### Changed
- `pyproject.toml` version bumped from 0.7.0 to 0.10.1; `src/specsmith/__init__.py` fallback `__version__` updated to match.
### Validation
- `pytest`: **448 passed, 1 skipped**.
- `ruff`: clean.
- `api-surface` snapshot: matches fixture.
## [0.7.0] â€” 2026-04-30
### Added
- **`specsmith serve --auth-token` (REQ-137).** Optional bearer-token gate on every `/api/*` endpoint. `/api/health` stays open so liveness probes still work behind a load balancer that strips `Authorization`. New `make_server()` factory in `src/specsmith/serve.py` exposes a fully wired server for tests; `run_server()` adds the banner + `serve_forever` loop. `_Handler._authorize()` enforces `Authorization: Bearer <token>` on `do_GET`, `do_POST`, and `do_DELETE`.
- **`specsmith voice transcribe <wav>` (REQ-141).** New `src/specsmith/agent/voice.py` wraps the optional `whisper-cpp-python` extra. Three resolution modes: real (library + model file under `~/.specsmith/voice/` or `SPECSMITH_VOICE_MODEL`), stub (`SPECSMITH_VOICE_STUB=<text>` for tests/CI), or unavailable (raises `VoiceUnavailableError` with an actionable install hint). CLI exposes `voice transcribe --json` and `voice status`.
- **`tests/test_warp_parity_followup.py`** â€” covers serve auth-gate (open `/api/health`, 401 on missing/wrong token, 200 on correct token), voice (stub mode, missing-file error, unavailable-when-no-library + no-stub, status output), and the api-surface stability snapshot (matches fixture, required commands present, exit codes + event types frozen).
- **`docs/site/api-stability.md`** â€” documents the `api-surface` snapshot mechanism: payload shape, regeneration command, the required-command spot check, and what is *not* covered by the snapshot.
- **Specsmith Drive (REQ-133).** New `src/specsmith/drive.py` module exposes `push()`, `pull()`, `listing()`; mirrors project rules / workflows / notebooks under `~/.specsmith/drive/<project>/<kind>/`. Round-trip safe; default backend is filesystem-only so the user can `git push` themselves.
- **Per-block share / export (REQ-134).** New `src/specsmith/block_export.py` plus `specsmith chat-export-block --session-id <id> --block-id <id> [--format md|json|html]` slices a single block out of `.specsmith/sessions/<id>/events.jsonl` (fallback `turns.jsonl`) and emits a self-contained markdown / JSON / HTML snippet. Raises `FileNotFoundError` for missing sessions and `KeyError` for missing blocks; the CLI exits non-zero in either case.
- **AI-searchable history (REQ-135).** New `src/specsmith/history_search.py` adds a deterministic keyword `search()` over every `.specsmith/sessions/<id>/turns.jsonl` plus an optional `semantic=True` mode that uses `sentence-transformers` when available and silently falls back to keyword matching otherwise. New `[history-semantic]` extra in `pyproject.toml`.
- **`specsmith api-surface` (REQ-140).** Top-level command emits the frozen 1.0 public surface (`cli_commands`, `exit_codes`, `event_types`) as JSON; `--snapshot <path>` writes the same payload to disk for CI diffing.
- **`[voice]` optional extra (REQ-141).** Pyproject extra carrying `whisper-cpp-python` for the upcoming agent voice-input integration (not yet wired into the CLI).
- **`tests/test_warp_parity.py`** -- pytest cases covering the new drive / block-export / history-search modules, the API-surface contract, and the CLI wiring.

- **Real MCP JSON-RPC client (REQ-130).** `agent.mcp` now ships a full stdio client (`MCPSession`) that runs the official MCP handshake (`initialize` -> `notifications/initialized` -> `tools/list`) against any configured server, exposes each discovered tool as an `MCPTool` whose `invoke_with_safety()` runs every call through the supplied safety check. Protocol pinned at `2024-11-05`. The chat session header now reports tools-per-server counts.
- **`tests/fixtures/mcp_fake_server.py`** -- pure-Python stdio MCP server fixture for hermetic tests.
- **`tests/test_mcp_client.py`** -- 8 new pytest cases (handshake, protocol pin, idempotent close, text/error/unknown-tool, safety integration, crash recovery, loader silent-skip).

- **MCP server announcement in chat sessions (REQ-121).** When `.specsmith/mcp.yml` is present, `specsmith chat` now loads the configured servers via `agent.mcp.load_mcp_tools` and emits a `[mcp servers: <names>]` token at the top of the message block so consumers (and the user) see which external tool surfaces are in play. The Specsmith safety middleware still gates every call.
- **`specsmith notebook record --session-id <id>`** now reads `.specsmith/sessions/<id>/turns.jsonl` and embeds each turn as a `### <role>` section in the generated `docs/notebooks/<slug>.md`, alongside any `--work-item-id` artifacts. Both flags may be combined; either may be omitted (with a friendlier placeholder when neither is supplied). Closes the gap between TESTS.md TEST-123 and the existing implementation.
- **`tests/test_phase34_completion.py`** â€” pytest cases covering: MCP loader (config-missing, single entry, malformed entries dropped, unparseable yaml, MCPServerSpec round-trip), notebook record (session-turns capture, helpful placeholder), notebook replay (success + missing slug exit-code), and a stubbed `scripts/perf_smoke.py` smoke test that asserts the baseline.json schema without spawning real subprocesses.

### Changed
- `specsmith chat` imports `load_mcp_tools` and emits the MCP-servers token after the rules-loaded notice.
- `notebook_record` gained `--session-id` and merges `.specsmith/runs/<WI>/` artifacts and `.specsmith/sessions/<id>/turns.jsonl` content into a single notebook.

### Validation
- `pytest`: **316 passed, 1 skipped** (was 304; +12 in test_phase34_completion.py).
- `ruff check` + `ruff format --check`: clean.
- `mypy src/specsmith/`: same status as develop (no regressions; pre-existing `chat_runner.py` errors only surface when optional `anthropic`/`openai` SDKs are locally installed; CI installs only `[dev]` so `ignore_missing_imports` keeps it green there).

## [0.6.0] â€” 2026-04-28

### Added
- **Skill marketplace** â€” new `specsmith skill` subcommand group (`search`, `list`, `install`) backed by a small built-in catalog (`verifier`, `planner`, `diff-reviewer`, `onboarding-coach`, `release-pilot`). `specsmith skill install <slug>` writes the SKILL.md into the project's `.agents/skills/` directory so the local Nexus runtime picks it up. New module `src/specsmith/skills.py` exposes `SkillEntry`, `CATALOG`, `search()`, `get()`, `install()`, `installed_skills()`.
- **`specsmith chat --interactive` stdin decision protocol** â€” when launched with `--interactive`, the chat command reads JSONL decision events from stdin so an IDE consumer (e.g. the VS Code extension) can drive the safe-mode approval flow and the inline diff review. The new `--decision-timeout <seconds>` flag bounds the wait. Approved tool calls fall through to the standard tool_call/plan_step/task_complete flow; denied calls emit `task_complete success=False`. The first non-accept `diff_decision` comment is folded into the persisted turn's `reviewer_comment` field so the next harness retry can consume it.
- **Real chat orchestrator** â€” new `src/specsmith/agent/chat_runner.py` powers `specsmith chat` with a streaming LLM turn. Provider preference is local-first: Ollama (default `http://127.0.0.1:11434`, model `qwen2.5:7b`), then the `anthropic`, `openai`, and `google-genai` SDKs gated on the corresponding API-key env vars. Tokens are streamed to the existing `EventEmitter` as `token` events, and the model's `Plan: / Files changed: / Test results:` sections feed `specsmith.agent.verifier.score()` so `task_complete.confidence` and the `success` flag now reflect a real verdict. Any provider error or missing SDK transparently falls back to the deterministic stub; set `SPECSMITH_DISABLE_REAL_CHAT=1` to force the stub explicitly (used by the test suite).
- **Diff-decision tests** â€” `tests/test_chat_diff_decision.py` adds three end-to-end tests for the inline diff review path (accept, reject-with-comment threaded into the final summary, timeout becomes `status="timeout"`).
- **Hermetic test fixture** â€” a new autouse fixture in `tests/conftest.py` sets `SPECSMITH_NO_AUTO_UPDATE=1` and `SPECSMITH_PYPI_CHECKED=1` so the project-update prompt and the PyPI version check do not consume stdin or hit the network during tests. This made the existing `test_chat_stdin_protocol.py` tests pass deterministically when run individually, not just as part of the full suite.
- **Documentation** â€” `docs/site/commands.md` now documents `specsmith chat` (block protocol, stdin decision protocol, real-LLM provider order, fallback behaviour) and `specsmith skill` (`list`, `search`, `install`).
- **Tests** â€” `tests/test_skill_marketplace.py` (18 tests), `tests/test_chat_stdin_protocol.py` (3 tests), and `tests/test_chat_diff_decision.py` (3 tests) cover the new surfaces.

### Changed
- **`pyproject.toml`** version bumped from `0.5.0` to `0.6.0`. `Development Status :: 4 - Beta` classifier preserved (1.0.0 stays deferred per the pre-1.0 stance).

### Fixed
- **`specsmith chat` diff block kwarg** â€” the inline diff review path called `EventEmitter.diff(path=..., diff=...)` but the helper takes `body=`. The kwarg mismatch was latent because no existing test created a `REQUIREMENTS.md` that triggered scope-matched diff blocks. Fixed in `src/specsmith/cli.py` and exercised by `tests/test_chat_diff_decision.py`.

## [0.5.0] â€” 2026-04-28

### Changed
- **Agent skill adapter renamed** â€” the integration adapter that previously generated `.warp/skills/SKILL.md` is now named `agent-skill` and writes to `.agents/skills/SKILL.md`. Existing `scaffold.yml` files that still list `warp` continue to work via a backward-compat alias resolved in `specsmith.integrations.get_adapter`. The legacy `.warp/skills/SKILL.md` path is still patched on `specsmith upgrade` for projects that have not yet rebuilt.
- **Customer-facing docs** â€” Read the Docs pages (`agent-integrations.md`, `getting-started.md`, `configuration.md`, `commands.md`, `agent-client.md`) and `TESTS.md` no longer reference any specific terminal-AI vendor by name. The `agent-skill` adapter is described as a generic SKILL.md integration for terminal-native AI agents.
- **REQ-079 / ARCHITECTURE.md cleanup boundary text** â€” protected-paths description generalised to â€œthird-party agent integration directories (e.g. `.agents/`)â€. Defensive code in `agent/cleanup.py` continues to protect both `.agents/` and `.warp/` for users who already have either directory in their project.
- **`pyproject.toml`** version bumped to `0.5.0`. `Development Status :: 4 - Beta` classifier preserved (1.0.0 stays deferred per the pre-1.0 stance).
- **`scaffold.yml`** integration list switched to the new `agent-skill` adapter name in this repo's own scaffold.

### Internal
- New module `src/specsmith/integrations/agent_skill.py` (`AgentSkillAdapter`) replaces `src/specsmith/integrations/warp.py` (file removed). `LEGACY_ALIASES = {"warp": "agent-skill"}` in `src/specsmith/integrations/__init__.py` keeps existing configs working without manual migration.
- `tests/test_integrations.py` covers the new canonical name, the legacy alias, and the new `.agents/skills/` output path.
## [0.4.0] â€” 2026-04-28
### Added
- **Nexus broker, preflight, verify** â€” `specsmith preflight <utterance> --json` and `specsmith verify [--stdin|--diff|--tests|--logs|--changed]` are first-class CLI subcommands. The natural-language broker (`specsmith.agent.broker`) classifies intent, infers scope from `REQUIREMENTS.md` / `.repo-index`, calls the CLI, and renders plain-language plans (REQ-084..REQ-100).
- **Bounded-retry harness with canonical retry strategies** â€” `execute_with_governance` honors `DEFAULT_RETRY_BUDGET` and surfaces `narrow_scope` / `expand_scope` / `fix_tests` / `rollback` / `stop` on stop-and-align (REQ-014, REQ-028, REQ-063, REQ-096).
- **`/why` post-run governance block** in the Nexus REPL (REQ-094) and decision-specific exit codes for `preflight` (0 / 2 / 3, REQ-092).
- **`work_proposal` ledger event** distinct from the `preflight` event for brand-new work-item ids (REQ-044, REQ-085, REQ-099).
- **`--stress` bridge** â€” preflight optionally runs the AEE `StressTester` over matched requirements and surfaces critical failures as `stress_warnings` (REQ-100).
- **`.specsmith/config.yml` confidence threshold** â€” `epistemic.confidence_threshold` is honored as the floor for `confidence_target` in both `preflight` and `verify` (REQ-058, REQ-098).
- **CI baseline contract** â€” ruff lint + format clean, mypy strict-clean over 69 source files, and `pip-audit --ignore-vuln CVE-2026-3219` (REQ-101..REQ-103).
- **VS Code extension commands** â€” `specsmith.runPreflight`, `specsmith.runVerify`, `specsmith.toggleWhy` (REQ-106). *The `specsmith-vscode` extension has since been deprecated; Kairos is the flagship client.*
- **`scripts/sync_workitems.py`** keeps `.specsmith/workitems.json` mirrored to the implemented REQ/TEST set (REQ-104).
- **103 REQs / 103 TESTs / 259 passing tests + 1 skipped** â€” governance state synced.
- **Read the Docs Nexus surface** â€” `docs/site/commands.md` documents `preflight`, `verify`, the Nexus REPL, the bounded-retry harness, and `/why` (REQ-090).
- **ARCHITECTURE.md "Current State" section** describing the system as built (REQ-107).
### Changed
- **Type checking** â€” the dynamic Nexus agent surface (`broker`, `cleanup`, `indexer`, `orchestrator`, `repl`, `safety`, `tools`, `console_utils`, `serve`) is enumerated in the `[[tool.mypy.overrides]] ignore_errors=true` carveout in `pyproject.toml`. Strict-mypy is preserved everywhere else.
- **CI workflow** â€” every job upgrades pip first; security job tolerates the upstream-unfixed pip CVE-2026-3219 advisory.
- **TaskResult dataclass** returned by `orchestrator.run_task`; the broker harness consumes structured fields directly instead of synthesizing equilibrium from `bool(summary)` (REQ-091).
### Fixed
- **REPL closure bug** â€” `B023` in `repl._executor` was capturing the loop variable `user_input`; now bound via default arg.
- **134 ruff findings â†’ 0** across `src/specsmith/agent/*`, `src/specsmith/cli.py`, `src/specsmith/requirements_parser.py`, `src/specsmith/agent/broker.py`, and `tests/test_nexus.py`.
- **`tests/test_data_definition_001.py`** removed (corrupt single-line scaffolded fixture).
- **TEST-096 imports** moved to top of `tests/test_nexus.py` (E402).
## [Unreleased â€” pre-0.4.0 working notes]
### Added
- **Nexus governance documentation** â€” Read the Docs `commands.md` and `index.md` now describe `specsmith preflight`, `specsmith verify`, the natural-language broker, the bounded-retry harness, the `/why` toggle, and the `--stress` flag (REQ-090, REQ-101..REQ-103).
- **REQ-101 / TEST-101** â€” lint baseline contract; `ruff check` and `ruff format --check` must both exit zero on develop.
- **REQ-102 / TEST-102** â€” typecheck baseline contract; `mypy src/specsmith/` must exit zero on develop. Dynamic agent modules are explicitly enumerated under `[[tool.mypy.overrides]] ignore_errors=true`.
- **REQ-103 / TEST-103** â€” security baseline contract; CI security job upgrades pip and runs `pip-audit --ignore-vuln CVE-2026-3219` until the upstream pip fix lands.
### Changed
- **CI workflow** â€” every job now upgrades pip first; security job tolerates the currently-unfixed pip advisory via `--ignore-vuln`.
- **Type checking** â€” added `specsmith.agent.broker`, `specsmith.agent.cleanup`, `specsmith.agent.indexer`, `specsmith.agent.orchestrator`, `specsmith.agent.repl`, `specsmith.agent.safety`, `specsmith.agent.tools`, `specsmith.console_utils`, `specsmith.serve` to the mypy `ignore_errors` carveout in `pyproject.toml`.
### Fixed
- **Lint** â€” fixed 134 ruff findings to zero across the agent module, cli, requirements_parser, broker, and tests (E501 long lines, B023 closure-binding bug in REPL, B904 raise-from in safety, SIM110 / SIM105 simplifications, F401/I001 import hygiene).
- **Format** â€” applied `ruff format` to 12 files; CI now enforces format clean.
- **Tests** â€” `tests/test_data_definition_001.py` (a corrupt single-line scaffolded fixture) removed. TEST-096 imports moved to the top of `tests/test_nexus.py` (E402).
## [0.3.13] \u2014 2026-04-23

### Added
- **`specsmith serve`** \u2014 persistent HTTP server for agent sessions. Zero-dependency
  stdlib server with SSE events, POST /api/send, GET /api/status. Eliminates
  Python startup + Ollama cold-load overhead between turns.
- **EXEC-001 rule** \u2014 agent system prompt forbids `python -c` for non-trivial code.
  Agents must write to file then execute.
- **Supplementary rules audit** \u2014 `check_supplementary_rules()` scans for `*_RULES.md`
  files not referenced in AGENTS.md auto-load registry.

### Changed
- **Minimal startup protocol** \u2014 `start` quick command no longer runs git, reads
  AGENTS.md, or reads LEDGER.md. Just a brief greeting. VCS state and governance
  checks run separately in the extension (instant, no LLM calls).
- **Version bumped to 0.3.13** for pre-release channel (dev builds as 0.3.13.devN).

### Fixed
- CI: ruff lint (unused imports, import sorting, line length), ruff format,
  mypy type errors (dict return type, Any return, autogen stubs).
- `conftest.py`: SIM105 contextlib.suppress.

---

## [0.3.11] \u2014 2026-04-22

### Added
- **AG2 agent shell** (`src/specsmith/agents/`) â€” Planner/Builder/Verifier agents over Ollama.
  New CLI commands: `specsmith agent run/plan/status/verify/improve/reports`.
  Uses AG2 v0.12.0 with native Ollama tool calling. Configurable per-project via `scaffold.yml`.
- **Self-improvement workflow** (`agents/workflows/improve.py`) â€” `specsmith agent improve <task>`
  runs Planâ†’Buildâ†’Verify, produces structured ChangeReport at `.specsmith/agent-reports/`.
- **AG2 tool surface** â€” 12 typed tools: filesystem (pathlib, no subprocess), shell, git, tests.
  Replaces the old `operations.py` concept.
- **Phase 0â€“3 documentation** â€” `docs/baseline-audit.md`, `docs/system-proof.md`.
- **23 new agent tests** (`tests/test_agent.py`) â€” tool registry, tool handlers, system prompt,
  AgentRunner init, SessionState, meta-commands, Ollama integration (live).
- **tests/conftest.py** â€” WinError 448 pytest cleanup fix for Windows.

### Changed
- **Ollama timeout** â€” 120s â†’ 600s for completion, 300s for streaming. Fixes frequent
  `[Provider error] timed out` in VS Code sessions.
- **AgentConfig** â€” `effective_utility_model` (defaults to primary), `effective_max_iterations`
  (0 = unlimited, maps to 999).
- **AGENTS.md** â€” AG2 four-layer architecture, 12 project rules, updated file registry.
- **pyproject.toml** â€” `ag2[ollama]` optional dependency added.

---

## [0.3.10] â€” 2026-04-10

### Fixed
- No-placeholder-requirements rule added to system prompt (#69).

---

## [0.3.6] â€” 2026-04-09

### Added
- **VCS state in agent system prompt** â€” `build_system_prompt()` runs `git status --short` and
  `git log --oneline -5` at session start and embeds the snapshot so the agent immediately knows
  which files are modified, staged, or untracked without waiting for the first tool call.
- **Enhanced `start` quick command** â€” now explicitly runs git status, git log, reads AGENTS.md
  and LEDGER.md, and summarizes findings in 3â€“4 sentences before proposing the next action.
  Provides a full project orientation on every new session.
- **CONTINUITY RULE in system prompt** â€” prevents the agent from responding with â€œIâ€™m not sure
  what youâ€™re referring toâ€ when the user sends a follow-up like â€œfix itâ€ or â€œfix the issueâ€
  after the agent just described a finding. Instructs the agent to look back at the conversation
  history and act immediately.

### Changed
- **Ollama `keep_alive=-1`** on all `/api/chat` calls (complete, complete-with-tools, stream).
  Without this, Ollama unloads the model after 5 minutes of inactivity. When it reloads for the
  next turn it must re-prefill the full context, which under memory pressure causes apparent
  context loss between slow turns.
- **Deferred `llm_chunk` emission in json_events mode** (`runner.py`) â€” the `llm_chunk` event
  is now held back until after the non-English language check. Previously the Thai/Chinese
  response was sent to the VS Code extension and rendered before the correction turn could
  fire. Now the UI only ever sees the English reply.
- **Non-English correction on any iteration** â€” removed the `_iteration == 0` guard so the
  language check and correction turn fire on every agent response, not just the first.
- **Tool partial-text language filter** â€” non-English planning blurbs that precede tool calls
  are silently dropped rather than displayed.

### Fixed
- **Windows subprocess encoding** â€” `subprocess.run` calls in `tools.py` now force
  `encoding='utf-8'` and `errors='replace'`, fixing `UnicodeDecodeError` on Windows when
  tool output contained non-ASCII characters (cp1252 locale mismatch).

---

## [0.3.5] â€” 2026-04-07

### Added
- **`src/specsmith/profiles.py`** â€” `ExecutionProfile` dataclass with 4 built-in profiles: `safe` (read-only), `standard` (default), `open`, `admin`. Enforcement helpers `check_tool_allowed()`, `check_command_allowed()`, `check_write_allowed()`. Active profile loaded from `scaffold.yml` at session start.
- **`src/specsmith/toolrules.py`** â€” Curated AI context rulesets for 20+ tools (ghdl, vsg, verilator, iverilog, vivado, quartus, yosys, SymbiYosys, ruff, mypy, pytest, clang-tidy, cppcheck, cargo, go, golangci-lint, Terraform, oelint-adv, BitBake, git, Docker, Vale, markdownlint, Spectral). Rules auto-injected into the agent system prompt based on `scaffold.yml` project type and `fpga_tools`.
- **`src/specsmith/tool_installer.py`** â€” Platform-aware install commands for 25+ tools. Detects preferred package manager (winget/choco/scoop on Windows, brew on macOS, apt/dnf on Linux). `get_install_command(tool)` returns the best command for the current platform.
- **`specsmith tools install <tool>`** â€” Show or run the install command for a tool. Options: `--dry-run`, `--yes`, `--list`, `--category`.
- **`specsmith tools rules`** â€” Show AI context rules for the project or a specific tool. Options: `--tool <key>`, `--list`.
- **New FPGA project types**: `fpga-rtl-amd`, `fpga-rtl-intel`, `fpga-rtl-lattice`, `mixed-fpga-embedded`, `mixed-fpga-firmware` â€” with full tool registry, CI, and template support.
- **`specsmith import --yes/-y`** â€” Non-interactive mode flag for the import command (replaces `input='y\n'` in automation).
- **Language noise filter** â€” `importer.py` now excludes `toml`, `yaml`, `json`, `html` etc. from `primary_language` detection so Rust projects no longer report `toml` as the primary language.
- **`ProjectConfig`** gains `execution_profile`, `custom_allowed_commands`, `custom_blocked_commands`, `custom_blocked_tools` fields.

### Changed
- **AMD rebrand**: `fpga-rtl-xilinx` â†’ `fpga-rtl-amd` throughout (type labels, tool registry, CI templates, VS Code panel). Legacy `fpga-rtl-xilinx` id still accepted for backward compatibility.
- **Agent system prompt**: Strengthened English-only instruction (names Qwen/DeepSeek explicitly). `start` quick command prefixed with `[RESPOND IN ENGLISH ONLY]`.
- **`run_sync`**: Uses `ORIG_HEAD..HEAD` instead of `HEAD~1..HEAD` â€” more robust on first-ever pulls.
- **Ollama provider**: Added `_complete_native_with_fallback()` â€” if both tool-call path AND native path return HTTP 400 (e.g. `think` param unsupported on older Ollama), disable `think` and retry. Prevents cascading unhandled errors.
- All Jinja2 templates: `project.type.value` â†’ `project.type` (config.type is now `str`, not `ProjectType` enum).
- **pyproject.toml**: Added `keyring` to mypy `ignore_missing_imports` overrides. Added `profiles`, `toolrules`, `tool_installer` to `ignore_errors` overrides.

### Fixed
- `tools scan` FPGA tool entries missing for new AMD/Intel/Lattice types.
- Sandbox import tests: replaced fragile `input='y\n'` with `--yes` flag.
- CI: removed unused `format_install_table` import (F401), fixed f-string without placeholders (F541), split long string literals (E501).

---

## [0.3.4] â€” 2026-04-07

### Changed
- **Ollama provider**: Rewrote to use the native `/api/chat` endpoint for all completions including tool calling. Previous implementation used `/v1/chat/completions` (OpenAI-compat endpoint) which returned HTTP 400 for many local models. Native endpoint is the correct path for Ollama v0.3+.
- **Gemini provider**: Dual SDK support â€” prefers `google-genai` (GA May 2025) with fallback to legacy `google-generativeai`. Correct `system_instruction` parameter, token count extraction, default model updated to `gemini-2.5-flash`.
- **OpenAI provider**: Added `developer` role for o-series (o1, o3, o4) models, `max_completion_tokens` field.
- **Ollama model catalog**: Updated with Qwen3 7B/14B/32B, Gemma3 4B/27B, Llama3.3 70B entries.
- **VS Code ModelRegistry.ts**: Updated static fallbacks for April 2026 provider APIs.

---

## [0.3.3] â€” 2026-04-07

### Added
- **`specsmith phase`** â€” 7-phase AEE workflow tracker (`inception â†’ architecture â†’ requirements â†’ test_spec â†’ implementation â†’ verification â†’ release`). Each phase has a readiness checklist, recommended commands, and a progress percentage. Phase stored as `aee_phase` in `scaffold.yml`.
- **`specsmith phase show/set/next/list/status`** â€” full phase management CLI. `phase next` checks prerequisites before advancing; `--force` skips checks.
- **`src/specsmith/phase.py`** â€” standalone module with `Phase`, `PhaseCheck`, `evaluate_phase`, `read_phase`, `write_phase`, `phase_progress_pct`.
- **Governance Panel v3 AEE phase indicator** (VS Code extension) â€” live phase pill with readiness %, Next Phase button, and phase select dropdown between the topbar and tab bar.

### Changed
- `scaffold.yml` gains optional `aee_phase` field. All existing projects are backward-compatible (`inception` is the default).
- VS Code Governance Panel: phase selector in header updates `scaffold.yml` in real time.

## [0.3.2] â€” 2026-04-07

### Added
- **`src/specsmith/ollama_cmds.py`** â€” curated 9-model catalog, `get_installed_models()`, `get_vram_gb()` (nvidia-smi + Windows WMI), `recommend_models(vram_gb, task)`, `pull_model()` streaming progress.
- **`specsmith ollama`** group â€” 5 subcommands: `list`, `available [--task]`, `gpu`, `pull`, `suggest <task>`.
- **`OllamaProvider._resolve_model()`** â€” auto-resolves short model tags to exact installed names on 404, preventing quantization-suffix mismatches.

### Fixed
- Ollama 404 error when model installed under quantization tag (e.g. `qwen2.5:14b-instruct-q4_K_M`) but session saved short tag (`qwen2.5:14b`). Now auto-retries with resolved name.

## [0.3.1] â€” 2026-04-07

### Added
- **`specsmith run --json-events`** â€” JSONL event stream over stdout for IDE integration (VS Code extension bridge).
- **VS Code extension link** in README and readthedocs.
- Documentation for agentic client and VS Code extension.

### Fixed
- Duplicate `ollama` CLI group removed (auto-merge artifact from developâ†’main).
- Import sort and lint fixes for `ruff` compliance across all modules.

## [0.3.0] â€” 2026-04-06

### Added â€” Applied Epistemic Engineering layer
- **`epistemic` standalone library** â€” zero-dep Python library. `from epistemic import AEESession` works anywhere.
- `BeliefArtifact`, `StressTester` (8 challenge categories), `FailureModeGraph`, `CertaintyEngine` (CERTUS-inspired), `RecoveryOperator`, `TraceVault` (SHA-256 chain).
- **`specsmith stress-test`**, **`epistemic-audit`**, **`belief-graph`**, **`trace seal/verify/log`**, **`integrate`**.
- **`specsmith run`** â€” AEE-integrated agentic REPL (Anthropic, OpenAI, Gemini, Ollama). `--task`, `--provider`, `--model`, `--tier`, `--json-events`, `--optimize`.
- **`specsmith agent providers/tools/skills`** â€” agentic client introspection.
- Skills system: SKILL.md loader, built-in profiles (epistemic-auditor, verifier, planner).
- Hook system: H13 enforcement, ledger hints, context budget alerts.
- 3 new project types: `epistemic-pipeline`, `knowledge-engineering`, `aee-research`.
- New governance templates: `epistemic-axioms.md.j2`, `belief-registry.md.j2`, `failure-modes.md.j2`, `uncertainty-map.md.j2`. H13 added to `rules.md.j2`.
- `docs/site/aee-primer.md` â€” 10-part comprehensive AEE guide.
- `docs/site/epistemic-library.md` â€” full `epistemic` library API reference.

### Changed
- Version scheme: `X.Y.Z` (removed `.devN` suffix for stable releases).
- README: AEE-first framing, complete command reference.

## [Unreleased â€” pre-0.3.0]

### Added â€” Applied Epistemic Engineering

- **`epistemic` standalone library** (`src/epistemic/`): zero-dep Python library co-installed with specsmith. `from epistemic import AEESession` works in any Python 3.10+ project. Seven modules: `belief.py`, `stress_tester.py`, `failure_graph.py`, `recovery.py`, `certainty.py`, `session.py`, `trace.py`.
- **`AEESession`**: high-level facade bundling the full AEE pipeline (add_belief, accept, add_evidence, run, save, load, seal, verify_trace). Primary entry point for non-specsmith projects including glossa-lab, cpac, and compliance pipelines.
- **`BeliefArtifact`**: fundamental AEE primitive. Requirements, decisions, and hypotheses are all BeliefArtifacts with propositions, epistemic boundaries, confidence levels, and failure modes.
- **`StressTester`**: 8-category adversarial challenge engine (vagueness, falsifiability, observability, irreducibility, compound claim, no propositions, P1 confidence, logic knots).
- **`FailureModeGraph`**: directed graph of stress-testâ†’breakpoint relations with `equilibrium_check()` and `logic_knot_detect()`. Mermaid diagram rendering.
- **`CertaintyEngine`**: CERTUS-inspired confidence scoring. C = base Ã— coverage Ã— freshness. Weakest-link propagation through inferential links.
- **`RecoveryOperator`**: generates bounded `RecoveryProposal` objects for all failure modes. Never auto-applies. Ranked by severity.
- **`TraceVault`** (`src/epistemic/trace.py`): STP-inspired cryptographic decision sealing. SHA-256 chain, append-only `.specsmith/trace.jsonl`.
- **`CryptoAuditChain`** in `ledger.py`: SHA-256 chained hashes for all ledger entries. Tamper-evident history.
- **`specsmith.epistemic`**: backward-compatible shim that re-exports everything from `epistemic`.

### Added â€” New CLI Commands

- **`specsmith stress-test`**: AEE adversarial stress-tests on `docs/REQUIREMENTS.md`. Text and Mermaid output.
- **`specsmith epistemic-audit`**: full AEE pipeline â€” stress-test + failure graph + certainty scoring + recovery proposals. `--threshold` and `--mermaid` options.
- **`specsmith belief-graph`**: render belief artifact dependency graph by component. Text and Mermaid.
- **`specsmith trace seal/verify/log`**: cryptographic trace vault management.
- **`specsmith integrate <tool>`**: epistemic impact analysis before tool adapter scaffolding.
- **`specsmith run`**: AEE-integrated agentic REPL. Auto-detects provider. `--task`, `--provider`, `--model`, `--tier` options.
- **`specsmith agent providers/tools/skills`**: configure and inspect the agentic client.

### Added â€” Agentic Client

- **`src/specsmith/agent/`**: minimal, cross-platform Python agentic client.
  - `core.py`: `Message`, `Tool`, `CompletionResponse`, `ModelTier`, `BaseProvider` protocol
  - `providers/`: Anthropic, OpenAI (incl. Ollama via compat endpoint), Gemini, Ollama (stdlib-only)
  - `tools.py`: 20 specsmith commands as native agent tools with epistemic contracts
  - `hooks.py`: `HookRegistry` with Pre/PostTool, SessionStart, SessionEnd hooks. Built-in H13 enforcement.
  - `skills.py`: SKILL.md loader with domain prioritization (epistemic > governance > verification > testing > vcs)
  - `runner.py`: REPL loop with tool execution, model routing, session state, streaming support
  - Built-in profiles: `planner.md`, `verifier.md`, `epistemic-auditor.md`
- All LLM providers are optional extras: `pip install specsmith[anthropic]`, `specsmith[openai]`, `specsmith[gemini]`
- Ollama support via stdlib `urllib` only (zero deps)
- Model routing: `--tier fast/balanced/powerful` maps to appropriate models per provider

### Added â€” Project Types and Config

- **3 new project types**: `epistemic-pipeline` (ARE 8-phase), `knowledge-engineering`, `aee-research`
- **`ProjectConfig.enable_epistemic`**: opt-in AEE governance layer
- **`ProjectConfig.epistemic_threshold`**: configurable certainty threshold (default 0.7)
- **`ProjectConfig.enable_trace_vault`**: opt-in cryptographic trace vault

### Added â€” Governance Templates

- **`epistemic-axioms.md.j2`**: 5 AEE axioms applied to the project
- **`belief-registry.md.j2`**: catalog of BeliefArtifacts (decisions, assumptions, dependencies)
- **`failure-modes.md.j2`**: Failure-Mode Graph document
- **`uncertainty-map.md.j2`**: known unknowns and accepted uncertainties
- **H13** added to `rules.md.j2`: Epistemic Boundaries Required â€” proposals must state assumptions
- 3 new stop conditions in `rules.md.j2`: Logic Knot, P1 confidence, trace chain integrity

### Added â€” Documentation

- **`docs/site/aee-primer.md`**: 10-part comprehensive guide from zero AEE knowledge to full productivity. Covers theory, formal machinery, 4-step method, belief artifacts, logic knots, certainty engine, trace vault, practical workflow, domain examples, and references.
- **`docs/site/epistemic-library.md`**: full API reference for the standalone `epistemic` library with integration examples for glossa-lab, compliance, and FastAPI.
- RTD nav updated with "Applied Epistemic Engineering" section and "Agentic Client" section.
- ECC reference cloned locally: `C:\Users\trist\Development\BitConcepts\everything-claude-code`

### Changed

- **Version scheme**: switched to `X.Y.Z.devN` (no alpha/beta suffixes). `pyproject.toml` targets `0.3.0`; dev builds auto-publish as `0.3.0.devN`.
- **Package description**: AEE-first framing
- **pyproject.toml**: `epistemic` package in `package-data`, optional LLM extras (`[anthropic]`, `[openai]`, `[gemini]`, `[agent]`, `[all]`)
- **AGENTS.md**: updated identity, spec version 0.3.0, new commands, ECC reference
- **README.md**: leads with AEE identity, explains the paradigm shift, shows epistemic library usage
- **mkdocs.yml**: AEE and Agentic Client nav sections, navigation.tabs feature

## [0.2.3] - 2026-04-03

### Fixed
- **Governance RTD table rendering** (#55): rows 2â€“6 of the Modular Governance table in `docs/site/governance.md` started with `||` instead of `|`, breaking layout. Introduced during the uppercase filename migration.

### Added
- **RTD commands page complete** (#56): `docs/site/commands.md` now documents all 40+ commands â€” previously 13 of 40+ were documented. Added sections for `exec`/`ps`/`abort`, `commit`/`push`/`sync`/`branch`/`pr`, `session-end`, `update`, `apply`, `migrate-project`, `release`, `verify-release`, `ledger add/list/stats`, `req list/add/trace/gaps/orphans`, `plugin`, `serve`, and `credits limits`.
- **H11/H12 governance rules and blocking-loop enforcement** (#58): two new hard rules added to the `RULES.md` governance template. H11 requires every loop or blocking wait in agent-written scripts to have a deadline, fallback exit, and diagnostic message. H12 requires Windows multi-step automation to use `.cmd` files. `specsmith validate` now scans `.sh`/`.cmd`/`.ps1`/`.bash` files under `scripts/` and the project root and flags infinite-loop patterns without a recognised deadline/timeout guard.
- **Proactive per-model rate-limit pacing** (#59): `BUILTIN_PROFILES` constant ships conservative RPM/TPM defaults for OpenAI (gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo, o1, o1-mini, o3-mini, gpt-5.4, wildcard), Anthropic (claude-opus-4, claude-sonnet-4, claude-haiku-3-5, claude-3-5-sonnet, wildcard), and Google (gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash, gemini-2.5-pro, wildcard). Two new `credits limits` subcommands: `status` (rolling-window RPM/TPM/concurrency snapshot) and `defaults` (list or `--install` built-in profiles). Local overrides always take precedence over built-ins.
- **Rate Limit Pacing RTD page**: new `docs/site/rate-limits.md` documents the scheduler model, built-in profiles table, CLI commands, persistent state, and the Python API.
- **README updated**: new sections for Governance Rules (H11/H12) and Proactive Rate Limit Pacing with RTD links. Commands table expanded to all major command groups.
- **Dev release CI fixed**: workflow now uses `pyproject.toml` version directly (no patch bump) so dev builds publish as `0.2.3.devN` â€” PEP 440 compliant pre-releases of the upcoming stable version.

## [0.2.2] - 2026-04-02

### Fixed
- **Upgrade auto-fixes AGENTS.md references**: when `upgrade` renames governance files (lowercaseâ†’uppercase), it now rewrites path references in AGENTS.md, CLAUDE.md, GEMINI.md, SKILL.md, and all agent config files automatically.
- **Alternate path detection**: auditor and upgrader now find LEDGER.md at `docs/LEDGER.md` and architecture docs in subdirectories (e.g. `docs/architecture/`). No more false "missing" reports or duplicate stub creation.
- **Case-insensitive architecture check**: `docs/ARCHITECTURE.md` recommended check now works regardless of filename casing.
- **CI-gated dev releases**: dev-release workflow now runs full test suite (ruff check+format, mypy, pytest) before PyPI publish.

## [0.2.1] - 2026-04-02

### Added
- **Process execution with PID tracking**: `specsmith exec`, `specsmith ps`, `specsmith abort` â€” cross-platform (Windows taskkill / POSIX SIGTERM+SIGKILL) process tracking and abort. PID files in `.specsmith/pids/`.
- **`specsmith upgrade --full`**: full sync of infrastructure files â€” regenerates exec shims, CI configs, agent integrations. Creates missing community/config files. Safe: never overwrites user docs.
- **Language-specific scaffold templates** (#41): Rust (Cargo.toml, main.rs), Go (go.mod, main.go), JS/TS (package.json for web-frontend, fullstack-js).
- **ReadTheDocs templates** (#38): `.readthedocs.yaml` and `mkdocs.yml` for Python/doc projects.
- **Release workflow templates** (#44): `.github/workflows/release.yml` with test gate, language-aware build, GitHub Release, PyPI OIDC publish.
- **PyPI integration** (#36): OIDC-based trusted publishing via release workflow template.

### Changed
- **Template directory restructured** (#45): `pyproject.toml.j2` moved to `python/`. Templates organized into `python/`, `rust/`, `go/`, `js/`, `community/`, `governance/`, `docs/`, `scripts/`, `workflows/`.
- **CI-gated releases**: both dev-release and stable release workflows now run full test suite (ruff check+format, mypy, pytest) before PyPI publish.
- Exec shims (`exec.cmd`, `exec.sh`) now write PID files for `specsmith ps`/`specsmith abort`.

## [0.2.0] - 2026-04-02

### Added
- **Community templates** (#42): `CONTRIBUTING.md`, `LICENSE` (MIT/Apache-2.0), `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/` (bug report + feature request). Config fields: `license` (default MIT), `community_files` list.
- **AI credit tracking** (#50): `specsmith credits` subcommand group â€” record, summary, report, analyze, budget. Tracks tokens/cost per session, model, provider, and task. JSON storage at `.specsmith/credits.json`.
- **Credit spend analysis** (#51): `specsmith credits analyze` detects model inefficiency, token waste, governance bloat, cost trends. Generates optimization recommendations with estimated savings.
- **Credit budget/watermarks**: `specsmith credits budget --cap 50 --watermarks 5,10,25,50`. Monthly caps, alert thresholds, watermark notifications.
- **Auto-init credit tracking**: `init`, `import`, and `upgrade` all create `.specsmith/credit-budget.json` with unlimited default budget. `.specsmith/` gitignored.
- **`specsmith architect`** (#49): interactive architecture generation â€” scans project, interviews user about components/data flow/deployment, generates rich `docs/ARCHITECTURE.md`.
- **`specsmith self-update`**: auto-detects channel (stable/dev), supports `--channel` override and `--version` pinning.
- **Multi-language detection**: importer detects and reports all significant languages (primary + secondary).
- **Dynamic versioning**: `__version__` reads from `importlib.metadata`. Docs use `{{ version }}` hook. Tests are version-agnostic.
- **Dev-release workflow for managed projects** (#35): gitflow + GitHub + Python generates `.github/workflows/dev-release.yml`.
- **Type-specific templates**: .gitattributes (#39) for 15 language types, .gitignore (#40) expanded for all 30 types, .editorconfig (#43) with per-language indent settings.
- **Yocto/bitbake/devicetree/markdown**: `.bbclass`, `.inc`, `.dts`, `.dtsi` in language detection; `kas.yml` build system; enhanced CI metadata.
- **No-hardcoded-versions rule** (H10): governance template and WARP rule.
- **Agent credit instructions**: Warp and Claude adapters include credit recording commands.
- **Session-end credit summary**: `session-end` shows total spend and budget alerts.
- **VCS commands**: `specsmith commit`, `push`, `sync`, `branch`, `pr`, `session-end` for governed git workflows.
- **Structured ledger CLI**: `specsmith ledger add/list/stats` for append-only change tracking.
- **Requirements CLI**: `specsmith req list/add/trace/coverage` for requirements management.
- **Test gap analysis**: `specsmith test gaps/orphans/summary` for REQâ†”TEST coverage.
- **Plugin system scaffold**: `specsmith plugin list`, entry-point-based extensibility.

### Fixed
- **Import with large AGENTS.md** (#46): broader keyword extraction, diff marker stripping, paragraph dedup, existing doc detection.
- **UnboundLocalError on import** with existing docs: scoping fix for REQUIREMENTS/TEST_SPEC/architecture skip logic.
- **Audit false positive**: architecture docs found in subdirectories (e.g., `docs/architecture/DESIGN.md`).
- **`audit --fix`** now generates missing recommended files (ARCHITECTURE.md from scan, REQUIREMENTS.md, TESTS.md stubs).
- **Topic-aware section classification** (#47): body content keywords route sections to correct governance files.
- **Type-specific audit thresholds** (#48): FPGA/embedded get higher limits (rules=1000, verification=600).

### Changed
- **Uppercase governance filenames**: all scaffolded markdown files use uppercase stems (RULES.md, WORKFLOW.md, ROLES.md, CONTEXT-BUDGET.md, VERIFICATION.md, DRIFT-METRICS.md, ARCHITECTURE.md). Upgrader auto-migrates legacy lowercase filenames on both case-sensitive and case-insensitive filesystems.
- Auditor now recommends `CONTRIBUTING.md` and `LICENSE`.
- RTD default version set to `stable`, default branch set to `develop`.
- Docs version references use dynamic `{{ version }}` instead of hardcoded strings.
- `init.py.j2` template for managed projects uses `importlib.metadata` pattern.
- Governance file size thresholds raised globally (rules=800, verification=400).
- Yocto toolset: added `testimage`, `yocto-check-layer` compliance.
- Release workflow now runs full test suite before building.

## [0.1.3] - 2026-04-01

### Fixed
- **PyPI sidebar links**: added Documentation (specsmith.readthedocs.io) and Issues (GitHub) to project URLs.
- **PyPI badge**: switched to cache-busting shields.io URL.

## [0.1.2] - 2026-04-01

### Fixed
- **PyPI classifier**: updated from "Development Status :: 3 - Alpha" to "Production/Stable".
- **Stale alpha references**: removed `--pre` flag text and alpha-period notes from getting-started.md and troubleshooting.md.

### Added
- **Release workflow guide** (`docs/site/releasing.md`): complete gitflow release process with pre-release checklist, post-release verification, version locations (5 places), and lessons learned.
- **WARP rule**: added release checks (classifier, stale versions, install commands) to `.warp/rules/documentation-updates.md`.

## [0.1.1] - 2026-04-01

### Security
- **Fix incomplete URL substring sanitization** (CodeQL alert #1): VCS platform detection in the importer now uses proper URL host parsing (`urllib.parse.urlparse` for HTTPS, explicit host extraction for SSH remotes) instead of substring matching. Prevents potential misidentification from spoofed hostnames.

## [0.1.0] - 2026-04-01

### Added
- **11 CLI commands**: `init`, `import`, `audit`, `validate`, `compress`, `upgrade`, `status`, `diff`, `export`, `doctor`.
- **30 project types** across 6 categories: software (Python, Rust, Go, C/C++, .NET, JS/TS, mobile, monorepo, microservices, DevOps, data/ML, browser extension), hardware (FPGA, Yocto, PCB, embedded), documents (spec, manual, paper, API spec, requirements mgmt), business/legal (business plan, patent, legal/compliance).
- **Verification tool registry**: maps each type to lint/typecheck/test/security/build/format/compliance tools with CI metadata for 16 languages.
- **Tool-aware CI generation**: GitHub Actions, GitLab CI, Bitbucket Pipelines with correct tools per project type. Mixed-language support (Python+JS auto-detects Node.js).
- **Project importer**: `specsmith import` detects language, build system, test framework, CI, governance, modules, and entry points. Merge mode preserves existing files.
- **`specsmith export`**: compliance reports with REQâ†”TEST coverage matrix, audit summary, git activity, tool status, governance inventory.
- **`specsmith doctor`**: checks if verification tools are installed on PATH.
- **`specsmith init --guided`**: interactive architecture definition with REQ/TEST stub generation.
- **Auditor**: 6 health checks (files, REQâ†”TEST, ledger, governance size, tool config, consistency). `--fix` auto-repairs missing files and CI configs.
- **Domain-specific templates**: patent claims/spec/figures, legal contracts/regulatory, business exec-summary/financials, research citations/methodology, API endpoints/auth.
- **7 agent integrations**: AGENTS.md, Claude Code, Cursor, Copilot, Gemini, Windsurf, Aider.
- **3 VCS platforms**: GitHub (`gh`), GitLab (`glab`), Bitbucket (`bb`) with CI/CD, dependency management (Dependabot/Renovate per ecosystem), and status checks.
- **Config inheritance**: `extends` field in scaffold.yml for org-level defaults.
- **Type-specific .gitignore**: Rust, Go, Node, Kotlin, .NET, KiCad, FPGA, Zephyr, LaTeX, Terraform patterns.
- **Type-specific governance rules**: 20+ project types have tailored AGENTS.md rules.
- **Read the Docs**: 13-page user manual at specsmith.readthedocs.io.
- **PyPI publishing**: automated via trusted publishing (OIDC).
- **GitHub infrastructure**: issue templates (bug, feature, new type), PR template, Discussions, 12 labels.
- **Self-governance**: 74 requirements, 113 tests, 100% REQâ†”TEST coverage, audit healthy (9/9).
- **`python -m specsmith`** supported via `__main__.py`.

## [0.1.0-alpha.2] - 2026-04-01

### Added
- **specsmith CLI tool** with 9 commands: `init`, `import`, `audit`, `validate`, `compress`, `upgrade`, `status`, `diff`.
- **`specsmith import`**: walk an existing project, detect language/build/tests/CI, generate governance overlay (AGENTS.md, LEDGER.md, REQUIREMENTS.md, TESTS.md, architecture.md). Supports `--force` to overwrite existing files.
- **`specsmith init --guided`**: interactive architecture definition session that auto-generates REQ/TEST stubs and architecture.md from user-defined components.
- **Verification tool registry** (`tools.py`): maps all 20 project types to lint, typecheck, test, security, build, format, and compliance tools. Supports user overrides via `verification_tools` config field.
- **Tool-aware CI generation**: GitHub Actions, GitLab CI, and Bitbucket Pipelines generate correct tool commands per project type (not just Python). CI metadata for 13 languages including setup actions, Docker images, and cache keys.
- **20 project types** (up from 8): added web-frontend, fullstack-js, cli-rust, cli-go, cli-c, library-rust, library-c, dotnet-app, mobile-app, devops-iac, data-ml, microservices.
- **Project detection engine** (`importer.py`): detects language, build system, test framework, CI, governance files, modules, entry points, and VCS state from an existing project directory.
- **Auditor tool verification**: `specsmith audit` now checks that CI configs reference the expected verification tools for the project type.
- **Type-specific governance templates**: AGENTS.md and verification.md now include type-specific rules for Rust, Go, C/C++, web frontend, .NET, DevOps/IaC, data/ML, and microservices projects.
- **Mixed-language CI support**: projects with both Python and JS tools (e.g., backend-frontend) automatically get both runtime setups in CI.
- **Language-specific Dependabot ecosystems**: pip, cargo, gomod, npm, nuget, pub detected from project language.
- **Interactive prompts** for VCS platform, branching strategy, and agent integrations during `specsmith init`.
- **`specsmith status`**: pull CI status, dependency alerts, and open PRs from VCS platform CLI (gh/glab/bb).
- **`specsmith diff`**: compare governance files against what spec templates would generate.
- **`audit --fix`**: auto-repair missing governance files and compress oversized ledgers.
- **Config inheritance**: `extends` field in scaffold.yml to inherit org-level defaults.
- **7 agent integration adapters**: Claude Code, Cursor, Copilot, Gemini, Windsurf, Aider.
- **3 VCS platform integrations**: GitHub (`gh`), GitLab (`glab`), Bitbucket (`bb`) with CI/CD, dependency, and security config generation.
- **Domain-specific scaffold directories**: FPGA, Yocto, PCB, Embedded, Web, Rust, Go, C/C++, .NET, Mobile, DevOps, Data/ML, Microservices.
- **Branching strategy config**: gitflow, trunk-based, github-flow with tuning knobs.
- **98 tests** across 12 test files covering CLI, scaffolder, auditor, validator, compressor, integrations, VCS platforms, tool registry, and importer.
- **GitHub Actions CI**: lint (ruff), typecheck (mypy --strict), test (pytest, 3 OS Ã— 3 Python), security audit (pip-audit).
- **Release workflow**: tag-triggered build (sdist + wheel) â†’ GitHub Release artifacts.
- Dependabot, pre-commit, Docker local CI.
- SECURITY.md, MAINTAINERS.md, .github/CODEOWNERS.
- SPDX-License-Identifier: MIT headers on all source files.
- Self-hosted governance: AGENTS.md, LEDGER.md, CONTRIBUTING.md for specsmith itself.

### Changed
- **Windows scripts**: replaced all `.ps1` templates with `.cmd` for environment compatibility.
- **GitHub Actions**: bumped to `checkout@v6` + `setup-python@v6`.
- **Branch protection**: `main` branch protected via GitHub rulesets (no deletion, no force push).
- Gitflow branching with `develop` branch created and synced.

## [0.1.0-alpha.1] - 2026-03-31

### Added
- **Modular AGENTS.md architecture** (Section 24): focused hub (~100-150 lines) plus 6 delegated governance docs under `docs/governance/` (rules.md, workflow.md, roles.md, context-budget.md, verification.md, drift-metrics.md). Lazy-loaded per task type to minimize credit use.
- **Credit and token optimization** (Section 25): `Estimated cost:` field in proposals, `Token estimate:` field in ledger entries, lazy loading protocol, response economy rules, efficient verification ordering, credit-waste anti-patterns.
- **Drift detection and feedback loops** (Section 26): 5 health signals (consistency, ledger health, documentation currency, governance size, rule compliance), drift response protocol, ledger compression to `docs/ledger-archive.md`, `audit` command.
- **Execution safety and timeout protection** (Section 27): mandatory timeouts on all agent-invoked commands, non-interactive execution mandate, timeout handling protocol (kill â†’ record â†’ retry once â†’ escalate), `scripts/exec.ps1` and `scripts/exec.sh` shim/wrapper layer, known hung-process patterns catalog.
- **Multi-agent coordination** (Section 28): agent identity in ledger entries, scope isolation, conflict detection, test separation principle.
- **FPGA / RTL project type** (Section 17.6): directory structure, constraint files as governance artifacts, synthesis â†’ P&R â†’ timing closure verification vocabulary, batch-only tool invocation mandate.
- **Yocto / embedded Linux BSP project type** (Section 17.7): meta-layer structure, KAS YAML as governance artifacts, build-time awareness in proposals, sstate/download cache management.
- **PCB / hardware design project type** (Section 17.8): schematic-review gate, BOM as governance artifact, ERC â†’ DRC â†’ fab verification pipeline, ECAD-MCAD sync documentation requirement.
- 15 new requirement component codes for FPGA (RTL, SIM, SYN, IMPL), embedded Linux (BSP, IMG, PKG, DTS, KRN), and PCB (SCH, PCB, BOM, FAB, MCAD) domains.
- Hard rule **H9 â€” Execution timeout required**: all agent commands must have timeouts.
- Anti-patterns #11 (hung processes) and #12 (credit waste).
- `audit` command in quick command reference (Section 22).
- Drift and health metrics added to compliance checklist (Section 23).
- `scripts/exec.ps1` and `scripts/exec.sh` added to recommended scripts (Section 13.2).

### Changed
- **Version** set to 0.1.0-alpha.1 (SemVer pre-release; will not reach 1.0.0 until production-ready).
- **Purpose statement** (Section 1) expanded: now covers software, firmware, FPGA/RTL, embedded Linux, and hardware projects.
- **AGENTS.md definition** (Section 2.1) restructured: must be kept small (~100-150 lines), serves as a hub referencing modular governance docs.
- **Authority hierarchy** (Section 3) updated: `docs/governance/*` files inherit AGENTS.md's authority via explicit delegation.
- **Proposal format** (Section 5) gained `Estimated cost:` field.
- **Ledger entry format** (Section 6) gained `Token estimate:` field.
- **Bootstrap procedure** (Section 18 Step 3) now creates `docs/governance/` directory with all 6 modular governance files.
- **Section 17 intro** updated to reference project types 17.5-17.8 covering hardware domains.

### Fixed
- **G1**: Bootstrap procedure now explicitly exempt from proposal requirement (H2) â€” was ambiguous in original.
- **G2**: Authority hierarchy no longer mislabels LEDGER.md as "lowest" when workflow.md and services.md are below it.
- **G3**: Added "Derivation vs. conflict resolution" paragraph clarifying requirements-vs-architecture precedence.
- **G4**: Library/SDK project type (17.4) now includes required `scripts/` directory.
- **G5**: Embedded/hardware project type (17.5) now explicitly references Section 2 and Section 13.2 instead of vague "same core structure."
- **G6**: Bootstrap ledger template TODOs now annotated "(adapt to selected project type)."
- **G7**: AGENTS.md adaptation guidance in bootstrap now specifies what "adapt" means concretely.
- **G8**: Added CLI and CMD component codes to requirements schema; noted list is extensible.
- **G9**: Session start file list now marks services.md as conditional ("if it exists").
- **G10**: Open TODOs format specified as `- [ ]` / `- [x]` checkbox syntax.

[0.6.0]: https://github.com/BitConcepts/specsmith/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/BitConcepts/specsmith/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/BitConcepts/specsmith/compare/v0.3.13...v0.4.0
[Unreleased]: https://github.com/BitConcepts/specsmith/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/BitConcepts/specsmith/compare/v0.6.0...v0.7.0
[0.2.3]: https://github.com/BitConcepts/specsmith/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/BitConcepts/specsmith/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/BitConcepts/specsmith/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/BitConcepts/specsmith/compare/v0.1.3...v0.2.0
[0.1.3]: https://github.com/BitConcepts/specsmith/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/BitConcepts/specsmith/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/BitConcepts/specsmith/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/BitConcepts/specsmith/compare/v0.1.0-alpha.2...v0.1.0
[0.1.0-alpha.2]: https://github.com/BitConcepts/specsmith/compare/v0.1.0-alpha.1...v0.1.0-alpha.2
[0.1.0-alpha.1]: https://github.com/BitConcepts/specsmith/releases/tag/v0.1.0-alpha.1

