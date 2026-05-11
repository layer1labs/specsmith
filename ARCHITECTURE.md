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

### Model Intelligence

Role-based scoring engine using HuggingFace benchmark data.
10 roles × benchmark weights. See `specsmith.agent.model_intelligence`.

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
