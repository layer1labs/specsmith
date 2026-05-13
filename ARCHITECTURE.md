# Architecture — specsmith

## Overview

specsmith is a CLI tool + governance engine for AI-assisted development.
It treats belief systems like code: codable, testable, deployable.

## Nexus Runtime

The Nexus runtime is the local-first agentic REPL that integrates with
the governance broker for safe, auditable AI-assisted development.

### Nexus Broker Boundary

The broker (`specsmith.agent.broker`) classifies natural-language
utterances into intents (read_only_ask, change, release, destructive)
and maps them to governance requirements via `infer_scope()`.

### Nexus Preflight CLI Subcommand

`specsmith preflight "<utterance>"` gates every change through the
governance broker. It returns a JSON payload with decision, work_item_id,
requirement_ids, test_case_ids, and confidence_target.

### Nexus REPL Execution Gate

The REPL (`specsmith.agent.repl`) uses `execute_with_governance()` to
wrap every agent action in a preflight → execute → verify cycle. The
`/why` toggle shows the governance trace in human-readable form.

### Nexus Bounded-Retry Harness

The harness (`specsmith.agent.broker.execute_with_governance`) retries
failed actions up to `DEFAULT_RETRY_BUDGET` times using strategy
classification (`classify_retry_strategy`). Strategies include
`fix_tests`, `reduce_scope`, `manual_review`, and `stop`.

## AI Provider & Model Intelligence

### Provider Registry

Unified flat list of all configured AI backends (cloud, ollama, vllm,
byoe, huggingface). See `specsmith.agent.provider_registry`.

### Execution Profiles

Profiles constrain which providers a session can use (unrestricted,
local-only, budget, performance, air-gapped).
See `specsmith.agent.execution_profiles`.

### Model Intelligence — HF Leaderboard Sync

Syncs benchmark data from the HuggingFace Open LLM Leaderboard and computes
three task-specific bucket scores per model:
- **Reasoning** = 0.35×MATH + 0.30×GPQA + 0.25×BBH + 0.10×IFEval
- **Conversational** = 0.40×IFEval + 0.35×MMLU-PRO + 0.25×BBH
- **Longform** = 0.35×MUSR + 0.35×IFEval + 0.30×MMLU-PRO

Falls back to 40+ built-in static scores when HF is unreachable.
Background sync runs 15 s after startup, then daily. CLI:
`specsmith model-intel sync/scores/recommendations/connection`.
See `specsmith.agent.hf_leaderboard` (REQ-263..REQ-269).

### Model Capability Profiles

40+ pre-built profiles for all major providers (OpenAI, Anthropic, Google,
Mistral, Llama, Qwen, DeepSeek, Ollama variants). Each profile carries:
`max_tokens`, `prompt_style`, `supports_vision`, `supports_tool_calls`,
`reasoning_mode`, `context_window`. Context-aware `trim_history()` preserves
system messages while summarising older turns. See `specsmith.agent.model_profiles`
(REQ-270..REQ-271).

### LLM Client

`LLMClient` wraps multiple providers with automatic fallback on 429/401,
O-series parameter translation (`max_completion_tokens`, temperature=1,
developer role), and vLLM guided-JSON payload injection.
See `specsmith.agent.llm_client` (REQ-275..REQ-277).

### Rate Limit Scheduler

EMA-based adaptive rate limit scheduler with per-model RPM/TPM profiles,
rolling-window tracking, dynamic concurrency backoff on 429, and image
token estimation. See `specsmith.rate_limits` (REQ-272..REQ-274).

### Endpoint Preset Registry

10+ built-in presets for common OpenAI-compatible providers (vllm, lm_studio,
llama_cpp, openrouter, together, groq, fireworks, deepinfra, perplexity,
azure_openai). Each preset has `id`, `label`, `base_url`, `endpoint_kind`,
`needs_key`. `suggest_profiles()` inspects env for API keys and Ollama
availability and returns inert (never-persisted) suggestions.
See `specsmith.agent.provider_registry` (REQ-278..REQ-280).

### USPTO Data Sources

7 bundled client modules for patent/IP work (PatentsView, PPUBS, ODP,
PFW, Citations, FPD, PTAB). All stdlib urllib, no external dependencies.
See `specsmith.datasources.*`.

## Update Channel Selection

The `specsmith channel` group lets users persist a `stable` or `dev`
release-channel preference to `~/.specsmith/channel`.
`effective_channel_with_source()` in `specsmith.channel` resolves the
active channel from: (1) the persisted file, (2) the installed version
string (`.devN` suffix → dev, otherwise stable).
Self-update (`specsmith self-update`) and project-update checks both
honour the resolved channel.

Subcommands: `channel get [--json]`, `channel set {stable|dev}`, `channel clear`.

## AI Skills Builder (Phase A)

The `specsmith skills` group generates, lists, activates, deactivates,
tests, and deletes reusable AI agent skills stored as structured SKILL.md
specifications under `.specsmith/skills/<skill-id>/`.

- `skills build <description>` — deterministic skill spec generation from
  natural-language description; writes `SKILL.md` + `skill.json`.
- `skills list [--json]` — enumerate installed skills with active/inactive badge.
- `skills test <skill-id>` — dry-run validation of skill spec fields.
- `skills activate <skill-id>` — set `active: true` in `skill.json`.
- `skills deactivate <skill-id>` — set `active: false` in `skill.json`.
- `skills delete <skill-id> [--yes]` — permanently remove skill directory.

All read/write operations use `specsmith.skills_builder`.

## ESDB Extended Management

The `specsmith esdb` group provides full lifecycle management for the
ChronoMemory Epistemic State Database.

**Existing:** `status`, `migrate`, `replay`

**New (Phase ESDB):**
- `esdb export [--output PATH] [--json]` — dumps all records to a JSON
  snapshot at `<project>/.specsmith/esdb_export.json`.
- `esdb import <source> [--json]` — validates and stages a JSON export;
  run `esdb migrate` to apply.
- `esdb backup [--dir DIR] [--json]` — creates a timestamped snapshot at
  `.specsmith/backups/esdb_backup_<UTC>.json`.
- `esdb rollback [--steps N] [--json]` — reports WAL events that would be
  undone (stub until ChronoMemory native engine is linked).
- `esdb compact [--json]` — requests WAL compaction / vacuum.

## MCP Server Generator

`specsmith mcp generate <description> [--json]` produces a deterministic
MCP server configuration stub from a natural-language description.
The stub is a JSON object with `id`, `name`, `command`, and `args` fields
suitable for appending to `~/.specsmith/mcp.json`.

Implemented in `specsmith.cli.main_group → mcp_group → mcp_generate_cmd`.

## Agent Ask Dispatcher

`specsmith agent ask <prompt> [--project-dir DIR] [--json-output]` is a
keyword-based routing dispatcher that answers settings and status queries
without an LLM.

Routing table (evaluated in order):
1. `compliance / coverage / gaps / trace` → `get_compliance_summary()`
2. `audit / health / governance / drift` → `run_audit()`
3. `skill / build skill / create skill` → hints to `specsmith skills build`
4. `esdb / database / backup / export / records` → `EsdbBridge.status()`
5. `mcp / server / tool server` → hints to `specsmith mcp generate`
6. `session / phase / status / project` → `init_session()`

Returns `{"reply": "...", "action": "...", "prompt": "..."}`.

## Context Window Management

GPU-aware context sizing, live fill tracking, auto-compression, and hard
ceiling enforcement. Implemented in `specsmith.context_window`.

### VRAM Tiers (REQ-244)

`detect_gpu_vram()` reads NVIDIA/AMD VRAM via nvidia-smi/rocm-smi, falls
back to 0.0 on any error. `suggest_context_window(vram_gb)` maps:
<6 GB → 4096, 6–11 GB → 8192, 12–19 GB → 16384, ≥20 GB → 32768 tokens.

### Context Fill Tracker (REQ-245..REQ-247)

`ContextFillTracker(limit=N)` emits `ContextFillEvent` on every `record(used)`
call. At ≥ compression_threshold (default 80%) the event signals that
summarisation should run. At ≥ 85% (hard ceiling), `ContextFullError` is
raised — the caller must trigger emergency compression before proceeding.

## YAML-Native Governance Layer

The most significant architectural change in v0.12: governance files
(REQUIREMENTS.md, TESTS.md) are now **derived artifacts** generated from
canonical YAML sources. This is the authority flip from Markdown-primary
to YAML-primary governance.

### Authority Hierarchy (REQ-300..REQ-304)

```
docs/requirements/*.yml  ← CANONICAL (edit here)
docs/tests/*.yml         ← CANONICAL (edit here)
        │
        ▼  specsmith sync (YAML-first mode)
.specsmith/requirements.json  ← machine cache
.specsmith/testcases.json     ← machine cache
        │
        ▼  specsmith generate docs
docs/REQUIREMENTS.md  ← generated artifact (do not hand-edit)
docs/TESTS.md         ← generated artifact (do not hand-edit)
```

### Governance Mode Flag

`.specsmith/governance-mode` contains `yaml` when YAML-first mode is active.
`is_yaml_mode(root)` in `specsmith.governance_yaml` reads this flag.
In legacy Markdown mode (flag absent or `markdown`), the old sync behaviour
is preserved for backward compatibility with projects not yet migrated.

### YAML File Groups

Requirements and tests are grouped into domain files under
`docs/requirements/` and `docs/tests/` (7 files each):

| Stem | REQ Range | Domain |
|---|---|---|
| governance | REQ-001..064 | Core AEE governance |
| agent | REQ-065..129 | Nexus + CI |
| harness | REQ-130..160 | Slash commands + subagents |
| intelligence | REQ-161..220 | Instinct, eval, memory |
| context | REQ-244..247 | Context window management |
| esdb | REQ-248..262 | ESDB + skills + MCP builder |
| ai_intelligence | REQ-263..299 | AI model intelligence |

### Strict Validation (REQ-301)

`specsmith validate --strict` runs 8 schema checks:
1. Duplicate REQ IDs (errors)
2. Duplicate TEST IDs (errors)
3. Missing required REQ fields: `id`, `title`, `status` (errors)
4. Missing required TEST fields: `id`, `title`, `requirement_id` (errors)
5. Orphaned TESTs (TEST references non-existent REQ) (errors)
6. Untested REQs (REQs with no TEST) (warnings)
7. Duplicate REQ titles (warnings)
8. Machine-state drift (YAML ≠ JSON) (warnings)

Gated in CI via the `validate-strict` job in `.github/workflows/ci.yml`.

### Sync Pipeline (REQ-300)

In YAML-first mode, `specsmith sync` executes:
1. `load_yaml_requirements(root)` + `load_yaml_tests(root)` — read YAML
2. Normalise to `{id, title, description, source, status}` schema
3. Compare against existing JSON (detect drift)
4. Write `.specsmith/requirements.json` + `testcases.json` (JSON cache)
5. `generate_requirements_md()` + `generate_tests_md()` — render MD
6. Write `docs/REQUIREMENTS.md` + `docs/TESTS.md` (derived artifacts)

Legacy Markdown mode (steps 1–4 only, MD → JSON).

### Migration

`scripts/migrate_governance_to_yaml.py` is the idempotent migration script:
1. Removes duplicate REQs from REQUIREMENTS.md
2. Re-syncs machine state from cleaned MD
3. Exports JSON → grouped YAML files
4. Writes `.specsmith/governance-mode = yaml`

## Kairos Integration

Kairos (layer1labs/kairos) is the Rust terminal that consumes
`specsmith serve` as its governance backend via HTTP/WebSocket.
See `specsmith.governance_logic.GovernanceHTTPServer`.

### Kairos Settings Extensions (v0.11.x)

The Kairos settings view now includes Specsmith-specific pages grouped
under a **Specsmith** umbrella in the sidebar:

- **ESDB** — database status, export/import/backup/rollback/compact actions.
- **Skills** — skills listing and management instructions.
- **Eval** — evaluation suite tracking and report access.

The **Agents → Providers** subpage shows a fixed-width model table
(Name | Model ID | Context | Output columns) with `ConstrainedBox` +
`Clipped` cells to prevent text overflow on long model names such as
`o4-mini-deep-research`.

The **Agents → MCP servers** list page includes a collapsible
**AI Builder** card that invokes `specsmith mcp generate <description>`
and offers one-click append to `~/.specsmith/mcp.json`.
