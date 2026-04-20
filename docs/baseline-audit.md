# Baseline Audit — specsmith

> Generated: 2026-04-20 (Phase 0 — AG2 Realignment)

## 1. Architecture Map

### Entrypoints

| Entrypoint | Module | Description |
|---|---|---|
| `specsmith` CLI | `cli.py` → Click `_AutoUpdateGroup` | 50+ commands. Auto-checks spec_version and PyPI updates on invocation. |
| `specsmith run` | `agent/runner.py` → `AgentRunner` REPL | Agent loop: system prompt → provider → tool dispatch → hooks. Supports `/help`, `/tools`, `/model`, `/status`, `/save`, `/clear`. |
| `specsmith gui` | `gui/app.py` → `launch()` | PySide6 (Qt6) desktop app. `GUIAgentRunner(AgentRunner)` overrides print/provider/tool methods to emit Qt signals. `AgentWorker(QThread)` runs off UI thread. |
| VS Code extension | `extension.ts` → `activate()` | Activation event: `onStartupFinished`. 14 TypeScript source files. 30+ contributed commands. |

### Service Boundaries

```
CLI Layer (cli.py)
├── scaffolder.py          — Jinja2 template render → project files
├── auditor.py             — health checks (file existence, REQ↔TEST, ledger)
├── exporter.py            — compliance reports, REQ coverage matrix
├── importer.py            — detect language/build/test → generate overlay
├── config.py              — Pydantic model for scaffold.yml (33 project types)
├── differ.py              — governance file drift detection
├── doctor.py              — environment diagnostic
├── phase.py               — project lifecycle phase management
├── compressor.py          — LEDGER.md archival
├── ledger.py              — CryptoAuditChain (SHA-256 append-only)
├── retrieval.py           — keyword scoring index (term-frequency, not BM25)
├── profiles.py            — execution profiles
├── credit_analyzer.py     — LLM credit spend analysis
└── credits.py             — rate limit profiles

Agent Layer (agent/)
├── runner.py              — REPL loop, tool execution, streaming, session state
├── core.py                — Message, Tool, CompletionResponse, ModelTier, BaseProvider
├── tools.py               — 20 tool handlers (all use _run_specsmith → subprocess)
├── hooks.py               — HookRegistry: Pre/PostTool, SessionStart, SessionEnd, H13
├── skills.py              — SKILL.md loader with domain priority
├── optimizer.py           — TokenEstimator, ResponseCache, ContextManager, ModelRouter, ToolFilter
└── providers/
    ├── anthropic.py       — Claude (SDK: anthropic>=0.56)
    ├── openai.py          — GPT (SDK: openai>=1.0, also used for Mistral via base_url)
    ├── gemini.py          — Gemini (SDK: google-genai>=1.0, fallback google-generativeai)
    ├── ollama.py          — Ollama v0.3+ (stdlib urllib, /api/chat, tool calling, streaming)
    └── mistral.py         — Mistral via openai SDK pointed at api.mistral.ai

Epistemic Layer (epistemic/ + specsmith/epistemic/)
├── belief.py              — BeliefArtifact dataclass
├── stress_tester.py       — 8 adversarial challenges, Logic Knot detection
├── failure_graph.py       — FailureModeGraph, equilibrium_check, Mermaid render
├── recovery.py            — RecoveryOperator, bounded proposals
├── certainty.py           — CertaintyEngine, weakest-link propagation
├── session.py             — AEESession facade
└── trace.py               — TraceVault SHA-256 append-only chain

GUI Layer (gui/)
├── app.py                 — QApplication bootstrap, dark AEE theme
├── main_window.py         — QTabWidget, status bar, menu bar
├── session_tab.py         — per-tab: chat + input + meter + tool panel + provider bar
├── worker.py              — GUIAgentRunner + AgentWorker(QThread)
└── widgets/               — chat_view, input_bar, provider_bar, token_meter, tool_panel, update_checker
```

### VS Code Plugin Structure

```
specsmith-vscode/src/
├── extension.ts           — activate(): tree views, commands, startup checks
├── bridge.ts              — SpecsmithBridge: child process (specsmith run --json-events), JSONL protocol
├── SessionPanel.ts        — webview: agent chat, auto-approve, model/provider switching
├── GovernancePanel.ts     — webview: 6-tab settings (General, Models, Execution, Tools, Agents, Help)
├── SettingsPanel.ts       — webview: global extension settings
├── HelpPanel.ts           — webview: help/docs
├── OllamaManager.ts       — Ollama model management (list, pull, delete, GPU detection)
├── ModelRegistry.ts       — fetch available models per provider
├── ApiKeyManager.ts       — secret storage for LLM API keys
├── VenvManager.ts         — Python venv detection/management
├── ProjectTree.ts         — sidebar tree: project folders + file operations
├── EpistemicBar.ts        — status bar: epistemic health indicator
├── BugReporter.ts         — interactive bug report filing
└── types.ts               — SpecsmithEvent, SessionConfig, SessionStatus types
```

**Bridge protocol:** `SpecsmithBridge` spawns `specsmith run --json-events` as a child process. Communication is stdin (user messages, one per line) / stdout (JSONL events: `ready`, `llm_chunk`, `tool_started`, `tool_finished`, `tokens`, `turn_done`, `error`, `system`). Turn timeout: 5 minutes.

**Activation:** `onStartupFinished`. On activate: apply venv path, create tree views, register 30+ commands, startup checks (privacy notice, fetch models, update check, venv check, auto-open governance panel).

**No integration tests exist** for the VS Code extension.

### Model/Backend Assumptions per Provider

- **Anthropic:** SDK `anthropic>=0.56`. Streaming via SDK. Tool calling native.
- **OpenAI:** SDK `openai>=1.0`. Also serves Mistral (base_url override). Tool calling native.
- **Gemini:** SDK `google-genai>=1.0` (preferred) or `google-generativeai` (fallback). Auto-detects.
- **Ollama:** Stdlib only (`urllib.request`). `/api/chat` for all completions. Tool calling v0.3+. `num_ctx` via `SPECSMITH_OLLAMA_NUM_CTX` (default 4096). `keep_alive=-1` to prevent model unload. Think parameter for reasoning models.
- **Mistral:** Uses OpenAI SDK pointed at `api.mistral.ai`.

All providers are optional extras — specsmith core has zero LLM SDK dependencies.

## 2. Verification Results (2026-04-20)

### pytest (226 collected)

- **Passed:** 208
- **Failed:** 18
- **Skipped:** 0

**Failing tests (all sandbox/lifecycle + 1 scaffolder):**

| Test | Category |
|---|---|
| `test_sandbox_import::test_full_import_workflow` | sandbox import |
| `test_sandbox_import::test_import_force_overwrites` | sandbox import |
| `test_sandbox_import::test_import_idempotent_restart` | sandbox import |
| `test_sandbox_import::test_import_preserves_existing_project_docs` | sandbox import |
| `test_sandbox_import::test_import_force_overwrites_existing_docs` | sandbox import |
| `test_sandbox_lifecycle_import::test_import_sets_inception_phase` | lifecycle import |
| `test_sandbox_lifecycle_import::test_import_creates_governance_files` | lifecycle import |
| `test_sandbox_lifecycle_import::test_import_then_phase_operations` | lifecycle import |
| `test_sandbox_lifecycle_import::test_import_audit_includes_phase_readiness` | lifecycle import |
| `test_sandbox_lifecycle_new::test_full_lifecycle_phases` | lifecycle new |
| `test_sandbox_lifecycle_new::test_phase_gating_without_force` | lifecycle new |
| `test_sandbox_lifecycle_new::test_governance_files_present` | lifecycle new |
| `test_sandbox_lifecycle_upgrade::test_upgrade_migrates_workflow_to_session_protocol` | lifecycle upgrade |
| `test_sandbox_lifecycle_upgrade::test_upgrade_preserves_workflow_content` | lifecycle upgrade |
| `test_sandbox_lifecycle_upgrade::test_upgrade_then_audit_runs` | lifecycle upgrade |
| `test_sandbox_lifecycle_upgrade::test_upgrade_idempotent` | lifecycle upgrade |
| `test_sandbox_new::test_full_scaffold_workflow` | sandbox new |
| `test_scaffolder::test_creates_expected_files` | scaffolder |

**Root cause:** Likely governance template drift — scaffolder output changed but sandbox test expectations weren't updated.

**Platform issue:** pytest cleanup crashes with `WinError 448` (untrusted mount point in temp dir). Does not affect test results.

### ruff (lint)

All checks passed. Zero issues.

### mypy (typecheck)

Success: 0 errors across 72 source files. One note: unused `keyring.*` override in pyproject.toml.

## 3. Untested Modules

**Critical (agent layer — zero test coverage):**
- `agent/runner.py` — REPL loop, tool execution, streaming, session state, meta-commands
- `agent/tools.py` — 20 tool handlers (all route through `_run_specsmith` subprocess wrapper)
- `agent/hooks.py` — HookRegistry, trigger dispatch, H13 check
- `agent/skills.py` — SKILL.md loading, domain priority
- `agent/providers/anthropic.py` — Claude provider
- `agent/providers/openai.py` — GPT/Mistral provider
- `agent/providers/gemini.py` — Gemini provider
- `agent/providers/ollama.py` — Ollama provider (tool calling, streaming, think parameter)
- `commands/__init__.py` — empty stub, no slash commands implemented

**Secondary (supporting modules):**
- `architect.py`, `auth.py`, `credit_analyzer.py`, `credits.py`, `doctor.py`
- `ledger.py`, `ollama_cmds.py`, `patent.py`, `phase.py`, `plugins.py`
- `profiles.py`, `releaser.py`, `retrieval.py`, `session.py`

**Excluded from mypy strict:**
- `gui/` (requires PySide6)
- `ollama_cmds`, `languages`, `phase`, `cli`, `importer`, `agent.providers.gemini`, `agent.runner`, `profiles`, `toolrules`, `tool_installer`

**VS Code plugin:** Zero integration tests. No test runner configured.

## 4. Known Breakpoints

1. **18 sandbox/lifecycle test failures** — governance template expectations are stale. Severity: medium (blocks CI green).
2. **Tool handlers use raw subprocess** — `_run_specsmith()` in `tools.py` shells out to `python -m specsmith <args>`. No structured error handling, no cross-platform abstraction, no typed results.
3. **`commands/__init__.py` is empty** — slash commands documented in AGENTS.md and ARCHITECTURE.md are not implemented.
4. **No agent/runner tests** — the entire REPL loop, tool dispatch, streaming, and session state management is untested.
5. **No provider tests** — all 5 LLM providers have zero unit tests.
6. **No VS Code extension tests** — plugin activation, bridge protocol, panel rendering are all untested.
7. **Retrieval uses term-frequency** — not BM25 as documented in requirements.
8. **pytest WinError 448** — temp directory cleanup fails on Windows. Cosmetic but noisy.

## 5. Gap Summary (ranked by severity)

1. **No agent layer tests** — runner, tools, hooks, skills, providers all untested → high risk for AG2 integration
2. **18 failing sandbox tests** — CI is red → blocks safe development
3. **Empty commands/** — REPL meta-commands not wired → blocks slash command surface
4. **Tool handlers = raw subprocess** — no typed operations → AG2 tools must replace this
5. **No VS Code extension tests** — plugin correctness is assumed, not proven
6. **No AG2 integration** — the entire agent orchestration layer is missing
7. **No eval harness** — cannot measure agent quality
8. **No instinct/memory** — no cross-session learning
9. **No feature flags** — no way to gate capabilities
10. **No server daemon** — no WebSocket path for IDE integration
