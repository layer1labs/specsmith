# Architecture — Specsmith Self-Governing AEE System

## 1. Purpose

Specsmith is an Applied Epistemic Engineering toolkit and governance engine.

It scaffolds epistemically governed projects, records project beliefs, derives requirements, maps requirements to tests, verifies evidence, tracks uncertainty, and records decisions in a tamper-evident ledger.

Specsmith must be capable of governing its own development.

This repository is being bootstrapped so Specsmith can use its own governance system to manage future changes.

## 2. Core Boundary

Specsmith has two major layers:

### Governance Layer

The governance layer owns:

- `ARCHITECTURE.md`
- `REQUIREMENTS.md`
- `TESTS.md`
- `LEDGER.md`
- `.specsmith/requirements.json`
- `.specsmith/testcases.json`
- `.specsmith/workitems.json`
- `.specsmith/ledger.jsonl`
- `.specsmith/ledger-chain.txt`

The governance layer decides:

- what the system is supposed to do
- what requirements exist
- what tests prove those requirements
- what work items should be created
- whether output satisfies the requirements
- whether epistemic confidence is sufficient
- whether retry or escalation is needed

### Runtime Layer

The runtime layer executes actions through:

- Specsmith CLI commands
- OpenCode sessions
- agent commands
- test runners
- filesystem tools
- git operations
- future integrations

The runtime layer performs work, but governance determines whether the work is valid.

## 3. Implemented Specsmith System (Current State)

Specsmith is a fully implemented AEE toolkit as of v0.11.3. This section documents the actual implemented system, not planned behavior.

### Core CLI and Scaffold Layer
- `cli.py` — Click-based CLI with 60+ commands (preflight, verify, validate, audit, compliance, migrate, ci, esdb, context, session, etc.)
- `config.py` — Project configuration and type system
- `scaffolder.py` — Project scaffold generation for 30+ project types
- `importer.py` / `exporter.py` — Project import and compliance export
- `auditor.py` — Governance drift and health checks (28 checks)
- `ledger.py` — Ledger event management and hash chaining
- `integrations/` — Adapter layer for GitHub, GitLab, Bitbucket
- `vcs/` — VCS platform abstraction

### Agent and Agentic Runtime
- `src/specsmith/agent/` — Full agentic client: runner, broker, tools, providers, profiles, spawner, teams, permissions, memory, optimizer, model intelligence, rate limits
- `src/specsmith/agent/broker.py` — Natural-language governance broker (classify intent, infer scope, preflight, verify, execute_with_governance)
- `src/specsmith/agent/runner.py` — AgentRunner with multi-provider support (Anthropic, OpenAI, Gemini, Ollama)
- `src/specsmith/agent/execution_profiles.py` — Execution profiles with provider filtering

### AEE / Epistemic Layer
- `src/specsmith/epistemic/` — AEE machinery: BeliefArtifact, StressTester, FailureModeGraph, RecoveryOperator, CertaintyEngine, TraceVault
- `src/specsmith/trace.py` — STP-inspired cryptographic trace vault (SHA-256 chained seals)

### EU/NA Compliance Package (v0.11)
- `src/specsmith/compliance/` — 8-regulation AI compliance framework:
  - `regulations.py` — EU AI Act 2024/1689, NIST AI RMF 1.0, OMB M-24-10, Colorado SB24-205, Texas HB 1709, Illinois AIETA, California AB 2930 / CPPA ADMT, NYC Local Law 144
  - `checker.py` — Per-regulation compliance checker with ESDB evidence storage
  - `reporter.py` — Markdown/JSON/HTML compliance report generation
  - `evidence.py` — Evidence collection from project governance files

### ESDB / ChronoStore (v0.11)
- `src/specsmith/esdb/` — Epistemic State Database:
  - `store.py` — `ChronoStore`: WAL-based per-project epistemic state database at `<project>/.chronomemory/events.wal`. NDJSON with SHA-256 hash chaining. Snapshot every 50 events. Crash-safe via write-to-temp-then-rename.
  - `bridge.py` — `EsdbBridge`: Python adapter; delegates to ChronoStore when WAL exists, falls back to flat JSON read-only mode otherwise
- Every `ChronoRecord` carries OEA anti-hallucination fields: `source_type`, `confidence`, `evidence`, `epistemic_boundary`, `is_hypothesis`, `model_assumptions`, `recursion_depth`

### Session Persistence (v0.11)
- `src/specsmith/session_store.py` — `SessionStore`: persists session context to `.specsmith/session-state.json` and conversation history to `.specsmith/conversation-history.jsonl` (capped at 200 turns). Injects a synthetic resume message on reload.
- `src/specsmith/session_init.py` — `init_session()`: loads project state, health score, compliance score, phase readiness into a `SessionContext`

### Context Orchestrator (v0.11)
- `src/specsmith/context_orchestrator.py` — `ContextOrchestrator`: three-tier auto-optimization:
  - Tier 1 (60–79% fill): compresses LEDGER.md history
  - Tier 2 (80–84%): summarizes conversation history and evicts low-confidence ESDB records
  - Tier 3 (≥85%): emergency-drops records with confidence < 0.7. Data on disk is never deleted.

### Migration Framework (v0.11)
- `src/specsmith/migrations/` — Versioned migration framework:
  - `m001_governance_yaml.py` — YAML-first governance migration
  - `m002_agents_slim.py` — Slim AGENTS.md migration
  - `m003_compliance_init.py` — Compliance structure initialization
  - `m004_ledger_esdb.py` — Ledger to ESDB migration
  - `runner.py` — `MigrationRunner`: tracks applied migrations in `.specsmith/migration-state.json`

### CI Automation Manager (v0.11)
- `src/specsmith/ci_manager.py` — `CiManager`: generates CI, Dependabot, and CodeQL configs per project. `specsmith ci enable/status/watch`. State persisted to `.specsmith/config.yml`.

### Governance Store (v0.11)
- `src/specsmith/governance_store.py` — `GovernanceStore`: manages `.specsmith/governance/rules.yaml` for project-level governance rules

### Context Window Management
- `src/specsmith/context_window.py` — GPU-aware context window sizing, fill tracking, and auto-compression. See Section 14.

## 4. Governance Files

Specsmith governance is represented in both human-readable and machine-readable forms.

### Human-readable governance files

- `ARCHITECTURE.md` — canonical architectural source of truth
- `REQUIREMENTS.md` — declarative requirement list
- `TESTS.md` — test specification and requirement-to-test expectations
- `LEDGER.md` — human-readable audit trail

### Machine-readable governance files

- `.specsmith/requirements.json`
- `.specsmith/testcases.json`
- `.specsmith/workitems.json`
- `.specsmith/ledger.jsonl`
- `.specsmith/ledger-chain.txt`

Machine-readable files are the bridge between governance documents and agent/tool execution.

## 5. Machine State

Machine state lives under `.specsmith/`.

Current required state files:

- `.specsmith/requirements.json`
- `.specsmith/testcases.json`
- `.specsmith/workitems.json`
- `.specsmith/ledger.jsonl`
- `.specsmith/ledger-chain.txt`

Planned future state may include:

- `.specsmith/runs/`
- `.specsmith/evals/`
- `.specsmith/instincts.json`
- `.specsmith/teams/`
- `.specsmith/worktrees/`
- `.specsmith/agent-memory/`

Machine state must not replace the human-readable governance documents. Both must stay aligned.

## 6. Requirement Flow

Planned behavior:

1. `ARCHITECTURE.md` defines architectural intent.
2. Specsmith derives requirements from `ARCHITECTURE.md`.
3. Requirements are written to `REQUIREMENTS.md`.
4. Structured requirements are written to `.specsmith/requirements.json`.
5. Requirements are assigned stable IDs.
6. Requirements are linked to test cases.
7. Work items are created from accepted requirements or user requests.
8. Every change is recorded in the ledger.

A requirement must be:

- atomic
- testable where practical
- traceable to a source
- stable across repeated ingestion
- linked to verification evidence

## 7. Test Case Flow

Planned behavior:

1. Accepted requirements produce or link to test cases.
2. Test cases are recorded in `TESTS.md`.
3. Structured test cases are written to `.specsmith/testcases.json`.
4. Tests are executed through pytest or other registered tools.
5. Test results are attached to work items.
6. Verification evaluates whether tests provide sufficient evidence.
7. Results are recorded in `LEDGER.md` and `.specsmith/ledger.jsonl`.

Test cases must map back to requirement IDs.

## 8. AEE Verification Flow

AEE verification is Specsmith’s epistemic evaluation layer.

The verification flow includes:

1. Frame — identify the belief, requirement, or work item under evaluation.
2. Disassemble — break the claim into concrete assertions.
3. Stress-Test — challenge assertions using tests, evidence, contradictions, and failure modes.
4. Score — calculate confidence based on coverage, evidence quality, freshness, and failures.
5. Reconstruct — propose bounded recovery or retry steps.
6. Seal — record the result in the ledger and trace chain.

Verification must produce more than pass/fail.

It should produce:

- status
- confidence
- target confidence
- equilibrium state
- failures
- uncertainties
- contradictions
- retry recommendation

Epistemic equilibrium is reached only when confidence meets the target and no blocking contradictions remain.

## 9. OpenCode Integration Boundary

OpenCode is the first external execution environment for this governance model.

OpenCode should:

- execute filesystem operations
- run shell commands
- edit code
- run tests
- gather diffs
- provide output evidence

Specsmith should:

- preflight requests
- map requests to requirements
- map requirements to tests
- decide priority
- verify evidence
- recommend retries
- record ledger events

Specsmith core must not depend on OpenCode.

OpenCode-specific behavior must live behind an integration adapter.

## 10. Integration-Agnostic Adapter Model

Specsmith must support future integrations beyond OpenCode.

Potential integrations include:

- OpenCode
- Cursor
- Claude Code
- GitHub Actions
- VS Code
- JetBrains
- Theia-based Specsmith IDE
- CI/CD systems
- future project management systems

Core governance logic must remain independent from any one integration.

Adapters translate between the host environment and Specsmith’s standard governance contract.

## 11. AEE / Epistemic Layer

The standalone `epistemic` package is the canonical location for AEE machinery.

Key components include:

- `BeliefArtifact`
- `StressTester`
- `FailureModeGraph`
- `RecoveryOperator`
- `CertaintyEngine`
- `AEESession`
- `TraceVault`

Specsmith re-exports AEE symbols through `specsmith.epistemic` for compatibility.

The verification engine should use AEE concepts rather than simple binary validation.

## 12. Ledger and Trace Chain

Specsmith must maintain a durable audit trail.

Ledger artifacts:

- `LEDGER.md`
- `.specsmith/ledger.jsonl`
- `.specsmith/ledger-chain.txt`

The ledger records:

- architecture changes
- requirement creation
- test case creation
- work item creation
- verification results
- retry recommendations
- final status changes

The trace chain must be tamper-evident using chained hashes.

## 13. Planned Architecture Evolution

### Phase 1 — Core Harness Depth

Planned modules:

- `src/specsmith/operations.py`
- `src/specsmith/commands/`
- `src/specsmith/instinct.py`
- `src/specsmith/eval/`

Phase 1 goals:

- add typed project operations
- reduce raw shell usage
- expose harness slash commands
- persist reusable session patterns
- support Eval-Driven Development

### Phase 2 — Multi-Agent DAG Dispatcher (REQ-321..334)

Implemented in `src/specsmith/agent/dispatch/`. The dispatcher replaces the flat
GroupChat round-robin with a governed, dependency-aware DAG scheduler.

**Task DAG** (`dispatch/dag.py`):
- `TaskStatus` — PENDING | RUNNING | COMPLETED | FAILED | BLOCKED
- `TaskNode` — carries id, title, role, depends_on, context_in/out, result
- `TaskDAG` — Kahn topological sort, `runnable_nodes()`, `blocked_by_failure()` (transitive)
- `TaskDAGBuilder` — builds from planner JSON or falls back to a single-node DAG; raises `DAGValidationError` on cycles

**Dispatcher** (`dispatch/dispatcher.py`):
- `AgentPool` — lazy per-role `ConversableAgent` pool with idle worker reuse, `max_workers` ceiling
- `AgentDispatcher` — `ThreadPoolExecutor` scheduler; dispatches runnable nodes concurrently; on FAILED propagates BLOCKED to transitive dependents while siblings continue; writes ESDB `dispatch_result` records on completion and injects them into successor context_in

**Events** (`dispatch/events.py`):
- `EventEmitter` — appends JSONL to `.specsmith/dispatch/<dag_id>/events.jsonl` and fans out to SSE subscriber queues; supports static `replay()` for DAG resume (REQ-330)

**Compiler / tool support** (`agent/tools.py`):
- `run_gcc`, `run_arm_gcc` (bare-metal), `run_aarch64_gcc`, `run_iar_compiler`, `run_intel_compiler`
- `run_clang_format`, `run_clang_tidy`, `run_vsg` (VHDL Style Guide)
- All registered in `AVAILABLE_TOOLS` and wired into `ROLE_TOOLS` for `coder`, `reviewer`, `tester`, and the new `embedded-coder` role

**Entry point** (`agent/orchestrator.py`):
- `run_task(task, use_dag=False)` — DAG path enabled with `use_dag=True`; falls back to flat GroupChat on `DAGValidationError`
- `run_dispatch(task, max_workers=4, planner_output, project_root)` — always uses DAG path; returns `DispatchSummary`

**CLI** (`specsmith dispatch`):
- `dispatch run <TASK> [--max-workers N] [--json] [--no-dag]`
- `dispatch status [--dag-id ID]`
- `dispatch list`
- `dispatch retry --node NODE_ID --dag-id ID`

**serve.py additions**:
- `POST /api/dispatch/run` — start background DAG run, returns `dag_id`
- `GET  /api/dispatch/events?dag_id=` — SSE replay + live stream
- `GET  /api/dispatch/status?dag_id=` — node status JSON
- `GET  /api/dispatch/list` — saved run IDs
- `POST /api/dispatch/retry` / `POST /api/dispatch/abort`

**Kairos UI** (`app/` — Rust, egui/eframe):
- `dispatch_panel/mod.rs` — `DispatchApp` SSE subscriber; DAG graph with nodes coloured by status
- `dispatch_panel/gantt.rs` — `GanttStrip` timeline showing parallelism
- `dispatch_panel/controls.rs` — Retry (FAILED/BLOCKED) and Abort (RUNNING) buttons

**Architecture invariants for Phase 2**:
- The Orchestrator is the sole dispatch entry point; workers MUST NOT spawn further dispatches
- DAG validation (cycle detection) MUST happen before any worker is started
- `max_workers` ceiling MUST be enforced by `AgentPool`
- Completed node output MUST flow to successors via ESDB, not in-memory sharing
- Every state transition MUST be emitted as a persisted `DispatchEvent` before any SSE fan-out

### Phase 3 — Service and IDE

Planned modules:

- `src/specsmith/server/`
- `specsmith-ide/`

Phase 3 goals:

- local HTTP/WebSocket service
- Theia-based IDE
- AEE visual panels
- eval dashboards
- ledger browser
- instinct registry

## 14. Context Window Management
Source: `src/specsmith/context_window.py`

Specsmith implements GPU-aware context window management to prevent context overflow and enable auto-compression (REQ-244–247).

**GPU VRAM detection** (`detect_gpu_vram() -> float`): tries `nvidia-smi` for NVIDIA, then `rocm-smi` for AMD. Returns 0.0 when neither is available — safe to call on any platform without raising.

**Context window sizing** (`suggest_context_window(vram_gb) -> int`): maps VRAM to an Ollama `num_ctx` recommendation:
- ≥ 20 GB → 32 768
- ≥ 12 GB → 16 384
- ≥ 6 GB → 8 192
- < 6 GB / CPU-only → 4 096

**Context fill tracking** (`ContextFillTracker`): accumulates token usage per turn and emits structured JSONL events:
```json
{"type": "context_fill", "used": 3200, "limit": 4096, "pct": 78.12}
```
When `pct >= effective_ceiling_pct` (default 85 %, tightened by `MIN_FREE_TOKENS=2048`), `record()` raises `ContextFullError` — the caller MUST trigger emergency compression before accepting further input.

**Architecture invariant (I8):** The context window MUST NEVER reach 100 % fill. A minimum of 15 % or 2048 tokens must always remain free.

## 15. Compliance Mechanical Tests
Source: `tests/test_compliance.py`

`tests/test_compliance.py` provides deterministic pytest coverage for REQ-206 through REQ-220 (EU AI Act / NIST AI RMF compliance mechanisms) and REQ-244 through REQ-247 (context window management). All tests run in CI without LLM access.

Coverage summary:
- **REQ-206** — `TraceVault` SHA-256 chain: create seals → verify intact; tamper → verify fails.
- **REQ-207** — Preflight JSON includes `ai_disclosure` with required keys.
- **REQ-208** — `run_export()` contains "AI System Inventory", "Risk Classification", "Human Oversight Controls".
- **REQ-209** — Preflight `--escalate-threshold` above `confidence_target` sets `escalation_required: true`.
- **REQ-210** — `kill-session` CLI exits 0 with no active sessions and writes kill-switch ledger entry.
- **REQ-213** — `safe_write.append_file()` preserves prior content; `safe_overwrite()` creates `.bak` before replacing.
- **REQ-215** — `run_export()` produces all required compliance sections.
- **REQ-217** — `agent permissions-check <tool>` exits 3 (denied) / 0 (allowed) correctly.
- **REQ-220** — `is_safe_command()` blocks dangerous commands; allows safe ones.
- **REQ-244–247** — `suggest_context_window`, `detect_gpu_vram`, `ContextFillTracker`, `ContextFullError`.

## 16. Architecture Invariants

The following invariants must hold:

- Specsmith core MUST remain integration-agnostic.
- OpenCode-specific logic MUST NOT live in core.
- Governance files MUST remain human-readable.
- Machine state MUST remain synchronized with governance files.
- Requirements MUST be traceable to architecture or explicit user input.
- Test cases MUST map to requirements.
- Verification MUST use AEE concepts: confidence, uncertainty, contradiction, equilibrium.
- Retries MUST be bounded.
- Ledger events MUST be recorded for governance changes.
- Feature flags MUST remove hidden tool schemas from LLM calls, not merely block execution.
- Project operations MUST be cross-platform.
- Eval grading MUST measure outcomes, not execution paths.
- Instinct extraction MUST be user-reviewed before promotion.
- Subagents MUST NOT recursively spawn subagents.
- Filesystem mailbox communication MUST remain simple and debuggable.
- Orchestration SHOULD prefer local Ollama for routing when possible.

## 17. Bootstrap Sequencing Rules

Current bootstrap sequence:

1. Establish governance files.
2. Align `ARCHITECTURE.md`.
3. Derive initial requirements into `REQUIREMENTS.md`.
4. Write structured requirements to `.specsmith/requirements.json`.
5. Generate initial test specs.
6. Write structured test cases to `.specsmith/testcases.json`.
7. Create work item flow.
8. Add verification flow.
9. Record all actions in ledger.
10. Only then begin deeper implementation changes.

Specsmith must not claim to govern itself until architecture, requirements, test specs, work items, and ledger flow are aligned.

## 18. Non-Goals During Bootstrap

During bootstrap, do not yet implement:

- full model orchestration
- full OpenCode plugin runtime
- GUI changes
- multi-agent teams
- daemon service
- Theia IDE
- automatic unbounded retries
- hidden background governance loops

Bootstrap is limited to making Specsmith capable of governing its own future development.

## 19. ChronoMemory ESDB

ChronoMemory is a Rust Epistemic State Database engine (`crates/chronomemory/`) that replaces flat JSON state files with governed, replayable, dependency-aware epistemic cognition.

Core modules:
- `types.rs` — 26 record types (Fact, Hypothesis, Requirement, TestCase, etc.), EsdbId, RecordStatus, Confidence, EdgeType
- `wal.rs` — append-only WAL with SHA-256 hash chain (Invariant 8)
- `store.rs` — in-memory materialized state with BTreeMap indexes
- `projection.rs` — projection engine gating all canonical state transitions (Invariants 1, 3, 4, 5)
- `dependency.rs` — directed graph with 9 edge types + transitive closure
- `rollback.rs` — dependency-aware cascade invalidation (Invariants 2, 9)
- `context_pack.rs` — minimal verified context compiler (Invariant 7)
- `replay.rs` — deterministic state reconstruction
- `metrics.rs` — token-per-success optimization
- `query.rs` — semantic query API

Python bridge: `src/specsmith/esdb/bridge.py` reads `.specsmith/*.json` through ESDB-compatible query interfaces.

REST endpoints: `GET /api/esdb/status`, `GET /api/esdb/counts`.

10 system invariants enforced: anti-hallucination, no-forgetfulness, no-stale-override, no-duplicate-work, stop-on-violation, replay-visible tombstones, dependency-linked actions, replayable state, context-pack freshness, action-linked governance.

## 20. AI Skills Builder

Source: `src/specsmith/skills_builder.py`

Builds agent skills from natural-language descriptions following the SkillNet-style ontology. Each skill is a folder containing `SKILL.md` + `skill.json` with structured metadata: name, purpose, activation rules, input/output schema, epistemic contract, tools used, tests required, stop conditions.

REST endpoint: `GET /api/skills`.

## 21. MCP Server Generator

Source: `src/specsmith/mcp_generator.py`

Auto-scaffolds Model Context Protocol servers from natural-language tool descriptions using the FastMCP pattern. Generates `server.py`, `tool_schema.json`, `README.md` per server. Supports stdio and Streamable HTTP transports.

REST endpoint: `GET /api/mcp/servers`.

## 22. Kairos UX Integration

Kairos Settings pages that expose specsmith features via the governance REST API:

- **Governance page** — specsmith health, BYOE endpoint, project context, updater, bug report links
- **Compliance page** — requirement coverage, test coverage, gaps, traceability matrix
- **ESDB page** — ChronoMemory status, record counts, backend type, refresh
- Skills, Eval, Teams pages consume `GET /api/skills`, `GET /api/eval/suites`, `GET /api/teams`

All pages use async health polling via `GovernanceClient.get_json()` and follow the monolith SettingsWidget pattern.

## 23. HuggingFace Open LLM Leaderboard Integration

Source: `src/specsmith/agent/hf_leaderboard.py`

Syncs model benchmark data from the HuggingFace Datasets Server (`datasets-server.huggingface.co/rows?dataset=open-llm-leaderboard/contents`). Supports paginated fetch, exponential-backoff 429 handling with `RateLimit: t=` header parsing, optional HF API token (doubles rate limit to 1000 req/5min), and a static fallback of 50+ known models for offline operation.

Background task runs 15 s after startup then every 24 h. Scores are persisted to `~/.specsmith/model_scores.json` under a `bucket_scores` key alongside existing role scores.

Benchmarks mapped: IFEval, BBH, MATH Lvl 5, GPQA, MUSR, MMLU-PRO (HF field names → internal keys).

REST endpoints exposed by governance server:
- `GET /api/model-intel/scores` — all cached scores
- `GET /api/model-intel/scores/{name}` — one model
- `GET /api/model-intel/recommendations?bucket=reasoning` — top-10
- `POST /api/model-intel/sync` — force re-sync
- `POST /api/model-intel/test-hf` — connectivity + token probe

CLI: `specsmith model-intel sync | scores | recommendations | test-hf`

## 24. Bucket Scoring Engine

Source: `src/specsmith/agent/hf_leaderboard.py` (`_compute_bucket_scores`)

Three task-bucket scores computed from raw benchmark values (normalised 0–100):

- **Reasoning** = 0.35×MATH + 0.30×GPQA + 0.25×BBH + 0.10×IFEval
- **Conversational** = 0.40×IFEval + 0.35×MMLU-PRO + 0.25×BBH
- **Longform** = 0.35×MUSR + 0.35×IFEval + 0.30×MMLU-PRO

Ranked recommendation returns the top-10 models for a requested bucket. The engine merges HF-synced data with the existing `BASELINE_SCORES` so both cloud and local Ollama models appear in rankings.

Base+org-prefix deduplication: `Qwen/Qwen3-14B` is stored under both its full name and `Qwen3-14B` so vLLM-style repo-ID model names match correctly.

## 25. Model Capability Profiles

Source: `src/specsmith/agent/model_profiles.py`

Per-model capability descriptors resolved by prefix matching (longest key wins):

| Field | Type | Meaning |
|---|---|---|
| `max_tokens` | int | Max completion tokens to request |
| `temperature` | float | Sampling temperature |
| `ctx_budget` | int | Approx. chars of conversation history to keep |
| `action_capable` | bool | Reliably produces structured actions/JSON |
| `prompt_style` | str | `plain` \| `sections` \| `xml` |

Covers 40+ models across Ollama (Mistral, Qwen, Llama, Gemma, Phi, DeepSeek), cloud (OpenAI o-series, Claude, Mistral API), and a `_DEFAULT` fallback.

Context history trimmer (`trim_history`) summarises dropped turns into a compact `[Earlier conversation summary — N turns condensed]` assistant message to preserve research continuity.

## 26. AI Model Pacer v2

Source: `src/specsmith/rate_limits.py` (upgraded `ModelRateLimitScheduler`)

Enhancements over the existing rolling-window scheduler:

- **EMA utilisation tracking** — exponentially-weighted moving average of RPM/TPM utilisation (`alpha=0.25`) surfaced in `snapshot()`
- **Adaptive concurrency** — `dynamic_concurrency` decreases on `on_rate_limit()`, restores after 120 s (incrementally, 60 s between steps)
- **Retry-After parsing** — `parse_retry_after_seconds()` extracts `"try again in Xs"` from provider error strings; used when exponential backoff alone is insufficient
- **Image token estimation** — `estimate_request_tokens()` accepts `image_count` and multiplies by a per-model `image_token_estimate` (default 4096)
- **Pre-dispatch budget check** — `acquire()` blocks until RPM + TPM budgets allow dispatch; `release()` wakes waiting callers

All operations are guarded by a single `threading.Condition` lock so the pacer is safe for concurrent agent sessions.

## 27. Multi-Provider LLM Client with Fallback

Source: `src/specsmith/agent/llm_client.py`

Provider-agnostic chat client that tries a configurable ordered list of providers, falling back on 401/403/429/5xx. No optional packages required — uses `urllib` only.

**LLMProvider ABC**: `name`, `key_name`, `default_model`, `is_configured()`, `chat()`.

Concrete providers: `MistralProvider`, `OpenAIProvider`, `GoogleProvider`, `OllamaProvider`, `MockProvider` (test-only).

**O-series translation**: OpenAI o1/o3/o4 models receive `max_completion_tokens` instead of `max_tokens` and their `system` messages are renamed to `developer`.

**vLLM guided-JSON**: endpoints of type `byoe` or `huggingface` receive `guided_json` + `chat_template_kwargs: {enable_thinking: false}` when a JSON schema is provided.

**Gemini parts extraction**: handles models that return answer text in `parts` rather than `content`.

**JSON extraction helper** (`_extract_json`): tries direct parse → `\`\`\`json` fence → first balanced `{}` block before raising.

Provider fallback decision: `_is_fallback_status(code)` returns True for 401, 403, 404, 408, 409, 425, 429, 5xx.

## 28. Endpoint Preset Registry

Source: `src/specsmith/agent/provider_registry.py` (`ENDPOINT_PRESETS`)

Built-in connection presets for common local and hosted inference backends:

| Preset | Base URL | Key needed |
|---|---|---|
| vLLM (local) | `http://localhost:8000/v1` | No |
| LM Studio | `http://localhost:1234/v1` | No |
| llama.cpp server | `http://localhost:8080/v1` | No |
| OpenRouter | `https://openrouter.ai/api/v1` | Yes |
| Together AI | `https://api.together.xyz/v1` | Yes |
| Groq | `https://api.groq.com/openai/v1` | Yes |
| Fireworks AI | `https://api.fireworks.ai/inference/v1` | Yes |
| DeepInfra | `https://api.deepinfra.com/v1/openai` | Yes |
| Perplexity | `https://api.perplexity.ai` | Yes |
| Azure OpenAI | _(user-supplied)_ | Yes |

Probe function enriches model list with `context_length` (from `max_model_len` on vLLM), `owner`, and `description` fields.

CLI: `specsmith agent endpoint-presets`.

## 29. Suggested Profile Generation

Source: `src/specsmith/agent/provider_registry.py` (`suggest_profiles`)

Generates a list of ready-to-add `ProviderEntry` suggestions by inspecting:

1. Cloud API keys present in environment variables
2. Ollama models currently installed (`/api/tags`)
3. Custom BYOE endpoints in `providers.json`

For each backend, role-tuned parameter sets (temperature, max_tokens) are proposed following the AEE bucket taxonomy: `reasoning`, `conversational`, `longform`.

Suggestions are inert previews — the user calls `specsmith agent providers add` to persist.

CLI: `specsmith agent suggest-profiles`.

## 30. OEA Anti-Hallucination Governance Layer

Source: `src/specsmith/compliance.py` §`get_governance_rules_status`; rules `H15`–`H22`

Specsmith v0.11.3 integrates the findings of the *"Ontology-Epistemic-Agentic (OEA)
Recursive Generative Stability"* study (BitConcepts Research, 2026) as eight enforceable
governance rules, extending the core H1–H14 engineering rules:

| Rule | Name | Primary OEA Control |
|---|---|---|
| H15 | Epistemic Scope Bounding | Epistemic calibration |
| H16 | Anti-Drift Recursion Guard | Recursion guarding |
| H17 | Calibration Direction | Epistemic calibration |
| H18 | RAG Retrieval Filtering | Retrieval filtering |
| H19 | Synthetic Contamination Prevention | Data provenance |
| H20 | Falsifiability Required | Epistemic calibration |
| H21 | No Undisclosed Model Assumptions | Scope bounding |
| H22 | Cross-Platform CI Enforcement | Infrastructure validity |

The OEA study validated through ablation that these four control categories are the
primary levers for suppressing hallucination rates across model families:

1. **Epistemic calibration** (H17, H15, H20) — uncertainty expression
2. **Scope bounding** (H15, H21) — refusing out-of-domain claims
3. **Retrieval filtering** (H18) — relevance threshold before RAG injection
4. **Recursion guarding** (H16) — chain depth limit

Statusof H15–H22 is surfaced in the Kairos Compliance page
(Settings → Compliance → Governance Hard Rules H1–H22) alongside H1–H14.

**Architecture invariant (I9):** The compliance rule set MUST cover all four OEA control
categories. Adding or removing categories requires an explicit OEA-impact assessment
recorded in LEDGER.md.

## 31. YAML-Native Governance Layer
Source: `src/specsmith/governance_yaml.py`, `scripts/migrate_governance_to_yaml.py`

As of v0.12, specsmith operates in **YAML-first governance mode** when `.specsmith/governance-mode` contains `yaml`.

**Authority direction:**

- **Canonical source**: `docs/requirements/*.yml` and `docs/tests/*.yml`
- **Derived artifacts**: `docs/REQUIREMENTS.md`, `docs/TESTS.md`, `.specsmith/requirements.json`, `.specsmith/testcases.json`

**Sync pipeline** (`specsmith sync` in YAML-first mode):
1. Load and merge all `docs/requirements/*.yml` and `docs/tests/*.yml` files
2. Sort by numeric ID; deduplicate by `id` field
3. Write `.specsmith/requirements.json` + `testcases.json` (JSON cache)
4. Regenerate `docs/REQUIREMENTS.md` + `docs/TESTS.md` (Markdown artifacts, never hand-edit)

`specsmith sync --check` exits 1 if the JSON cache is out of sync with YAML — used as a CI gate.

**Strict schema validation** (`specsmith validate --strict`):
Enforces 8 governance schema checks (REQ-301):

1. Duplicate REQ IDs
2. Duplicate TEST IDs
3. Missing required REQ fields (`id`, `title`, `status`)
4. Missing required TEST fields (`id`, `title`, `requirement_id`)
5. Orphaned TESTs (reference a non-existent REQ)
6. Untested REQs (warning — does not block)
7. Duplicate REQ titles (warning)
8. Machine-state drift between YAML and JSON cache (warning)

Exits 1 on errors; warnings emit but do not block. `--json` flag emits a structured `{ok, strict_errors, strict_warnings, details}` payload.

**generate docs command** (`specsmith generate docs`):
Reads YAML sources and regenerates Markdown artifacts. Does not rewrite the JSON cache. `--check` flag reports what would change without writing any file.

**governance-mode flag**:
`.specsmith/governance-mode` — a plain-text file containing `yaml` or `markdown`.
`governance_yaml.is_yaml_mode(root)` reads this flag. Absence or `markdown` activates legacy Markdown-primary mode.

**Domain YAML files:**

| File | REQ range | Domain |
|---|---|---|
| `docs/requirements/governance.yml` | REQ-001..064 | Core AEE governance |
| `docs/requirements/agent.yml` | REQ-065..129 | Nexus + CI |
| `docs/requirements/harness.yml` | REQ-130..160 | Slash commands + subagents |
| `docs/requirements/intelligence.yml` | REQ-161..220 | Instinct, eval, memory |
| `docs/requirements/context.yml` | REQ-244..247 | Context window |
| `docs/requirements/esdb.yml` | REQ-248..262 | ESDB + skills + MCP |
| `docs/requirements/ai_intelligence.yml` | REQ-263..299 | AI model intelligence |
| `docs/requirements/yaml_governance.yml` | REQ-300..312 | YAML governance layer (canonical) |
| `docs/requirements/overflow.yml` | REQ-300..312 | Same REQs as yaml_governance.yml; contains reservation comment |
| `docs/requirements/multiagent_compliance.yml` | REQ-313..320 | Multi-agent governance traceability (plan 5939f743) |
| `docs/requirements/dispatch.yml` | REQ-321..334 | Multi-agent DAG dispatcher |

**Implemented:**
- REQ-313..320: multi-agent governance compliance (docs/requirements/multiagent_compliance.yml)

**Architecture invariants for YAML governance:**
- REQUIREMENTS.md and TESTS.md MUST NOT be hand-edited when governance-mode is `yaml`.
- The JSON cache MUST be regenerated by `specsmith sync` before any CI check.
- `specsmith validate --strict` MUST run on every push and PR (CI gate).

**CI integration**: The `validate-strict` job in `.github/workflows/ci.yml` runs `specsmith validate --strict --json` on every push and PR. The `sync-check` step runs `specsmith sync --check`. Both block the build on failure.

## 32. CI Automation Manager — save/load Commands
Source: `src/specsmith/cli.py` §`save`, `load`; `src/specsmith/ci_manager.py`

Two top-level CLI commands provide a complete governance checkpoint cycle:

**`specsmith save`** (REQ-336):
1. Create a timestamped ESDB backup via `ChronoStore.backup()` (written to `.chronomemory/backup/<timestamp>/`)
2. `git add` all governance files and `git commit` with an auto-generated message
3. `git push` the current branch to origin
- `--json` emits `{backup_path, commit_hash, push_ok}`
- Exits 0 on success; exits 1 on any step failure

**`specsmith load`** (REQ-337):
1. `git pull` the current branch from origin
2. Optionally restore the latest ESDB backup when `--restore-backup` is passed
3. Print a summary of files changed
- `--json` emits `{pull_ok, files_changed, backup_restored}`
- Exits 1 on unresolvable merge conflict

**`specsmith ci watch`**:
Uses `gh run watch --exit-status` (native blocking for GitHub) or exponential-backoff polling (other platforms, starting at 10 s, capped at 60 s). Eliminates busy-wait `time.sleep` loops.

## 33. Agent Tool Registry — specsmith_run
Source: `src/specsmith/agent/tools.py` §`specsmith_run`, `AVAILABLE_TOOLS`, `build_tool_registry`

`specsmith_run(command)` is the canonical agent tool for all specsmith governance operations (REQ-338). It normalises three input forms:

| Input form | Example | Resolved command |
|---|---|---|
| Slash prefix | `/specsmith save` | `specsmith save` |
| Verb shortcut | `save` | `specsmith save` |
| Full passthrough | `specsmith audit --strict` | `specsmith audit --strict` |

Verb shortcuts: `audit`, `commit`, `doctor`, `load`, `pull`, `push`, `run`, `save`, `status`, `sync`, `validate`, `watch`.

Registered in `AVAILABLE_TOOLS` and `build_tool_registry()` with REG-001/REG-002 epistemic claims:
- `invokes specsmith CLI; may write to .specsmith/ and .chronomemory/`
- `save/push/commit modify git history`
- `load/pull may overwrite local governance state`

**Architecture invariant (I10):** Agents MUST use `specsmith_run` for all governance CLI operations. Direct `run_shell('specsmith ...')` calls are prohibited when `specsmith_run` is available in the tool registry.

## 34. Migration Framework — M005 Agent-Run-Tool Migration
Source: `src/specsmith/migrations/m005_agent_run_tool.py`; `src/specsmith/migrations/__init__.py`

M005 (version=5) is the auto-upgrade migration that registers `specsmith_run` as the primary governance command for existing projects (REQ-339).

**Step 1 — Write `.specsmith/agent-tools.json`:**
```json
{
  "schema_version": 1,
  "primary_governance_command": "specsmith_run",
  "slash_prefix": "/specsmith",
  "verb_shortcuts": ["audit", "commit", "doctor", "load", ...]
}
```

**Step 2 — Patch `AGENTS.md`:**
Appends a "Governance commands (specsmith_run / /specsmith)" section documenting all slash-command forms and verb shortcuts. Original `AGENTS.md` is backed up to `.specsmith/agents.md.m005.bak` before modification.

Both steps support `dry_run=True` (reports what would change without writing) and `rollback()` (restores backup, removes `agent-tools.json`). M005 is registered in `MigrationRegistry` and runs automatically via `specsmith migrate-project`.

## 35. Nexus REPL — /specsmith Slash-Command Handler
Source: `src/specsmith/agent/repl.py` §`/specsmith` handler

The Nexus REPL (`specsmith run`) handles `/specsmith <args>` as a first-class slash command (REQ-340):

```
nexus> /specsmith save
nexus> /specsmith audit --strict
nexus> /specsmith status
```

Implementation:
- `command == '/specsmith'` branch intercepts the input before the broker
- Invokes `subprocess.run(f'specsmith {sm_args}', shell=True, capture_output=False)` — output streams directly to terminal
- Timeout: 120 s; graceful error handling (no REPL crash)
- Empty `/specsmith` (no args) shows `specsmith --help`
- Startup banner advertises the command: `"Use /specsmith <args> to run any specsmith CLI command directly."`

**Architecture invariant (I11):** The `/specsmith` handler MUST precede the broker branch in the REPL dispatch loop so governance commands bypass the LLM preflight path entirely.

## 36. specsmith.esdb Namespace — chronomemory v0.1.1 Full API Surface
Source: `src/specsmith/esdb/__init__.py`; `src/specsmith/esdb/bridge.py`

`specsmith.esdb` is the canonical import namespace for the chronomemory ESDB within specsmith code. It re-exports the full chronomemory v0.1.1 public surface so internal modules never import chronomemory directly in more than one place (REQ-344).

**Re-exported types:**
- Core: `ChronoStore`, `ChronoRecord`, `WalEvent`, `open_store`
- Bridge: `EsdbBridge`, `EsdbRecord`, `EsdbStatus`
- Phase 2: `DepGraph`, `DependencyEdge`, `RollbackReport`, `invalidate`, `ContextPack`, `ContextPackCompiler`, `ContextPackEntry`
- Phase 3: `RustChronoStore`, `RustRecord`, `RUST_BACKEND`
- Modules: `query` (18 §23 query functions), `metrics` (token tracking + skill system)

**Architecture invariant (I12):** Code injecting ESDB records into LLM context MUST use `query.what_is_known(store)` not `store.query(rag_filter=True)`. The former excludes infrastructure record kinds (`edge`, `rollback_event`, `token_metric`, `skill_run`) which must never appear in agent-facing context (REQ-345).

## 37. Skills Catalog — Terminal Awareness, ESDB, CI Polling, GitHub CI Pattern
Source: `src/specsmith/skills/`

The specsmith skills catalog (`specsmith skill list`) includes four new governance skills added in v0.11.3 (REQ-341, REQ-349):

- **`terminal-awareness`** (cross-platform): Shell detection, PowerShell 5 vs 7 differences, cmd.exe rules, bash/zsh/fish patterns, Python subprocess spawn with PID tracking, hanging-process prevention, cross-platform command equivalents table.
- **`chronomemory-esdb`** (governance): Full chronomemory v0.1.1 API reference + 5 critical rules. Activated by `esdb`, `chronomemory`, `wal`, `query` tags.
- **`gh-ci-polling`** (governance): Documents `gh run watch` as the correct CI-wait primitive. Explicitly prohibits `sleep`/`Start-Sleep`/`time.sleep` as CI wait mechanisms (REQ-349).
- **`github-actions-ci`** (devops): Layer1Labs CI pattern — `permissions: {}` at workflow level, per-job `contents: read`, parallel jobs, Python 3.10–3.13 matrix, `--cov-fail-under=85`.

**Architecture invariant (I13):** Every new specsmith feature MUST be reflected in the skills catalog if it introduces a workflow an agent must follow. Skills are activated by tag matching against agent task labels.

## 38. VCS Force Operations — save --force, pull --discard, pull --clean
Source: `src/specsmith/cli.py`; `src/specsmith/vcs_commands.py`

Three escape-hatch VCS flags added to resolve agentic workflow blockers (REQ-346, REQ-347, REQ-348):

**`specsmith save --force`**
Propagates `--force` to the underlying `run_push()` call, bypassing the gitflow direct-to-main guard. Uses `git push --force-with-lease` (safer than `--force`). Equivalent to: `specsmith save --no-push && specsmith push --force`.

**`specsmith pull --discard`**
Hard-resets the working tree to `origin/<branch>` via `git fetch` + `git reset --hard origin/<branch>`. Discards all local uncommitted changes. Used when an agentic session has drifted and a clean slate is needed.

**`specsmith pull --clean`**
Same as `--discard` plus `git clean -fd` to remove all untracked files. Equivalent to a full workspace reset to remote state.

**Architecture invariant (I14):** `--force` and `--discard` flags MUST be used only when explicitly requested. They bypass safety guards intentionally designed to prevent accidental data loss. Agents MUST NOT invoke these flags without explicit user confirmation.

## 39. Codity.ai Integration — AI Code Review Adapter
Source: `src/specsmith/integrations/codity.py`; `src/specsmith/skills/governance.py` (`codity-ai-review`)

`CodityAdapter` (REQ-354) scaffolds Codity.ai AI-code-review CI workflows into target projects via `specsmith integrate codity`. It detects the VCS host from `scaffold.yml` content and directory heuristics (`.gitlab-ci.yml`, `azure-pipelines.yml`) and generates the appropriate CI file:

| VCS host | Generated file |
|---|---|
| GitHub (default) | `.github/workflows/codity-review.yml` |
| GitLab | `.gitlab-ci-codity.yml` |
| Azure DevOps | `.azure-pipelines/codity-review.yml` |

All variants: install Codity CLI via `curl -fsSL https://cli.codity.ai/install.sh | sh`, run `codity review --staged`, require `CODITY_ACCESS_TOKEN` secret. GitLab/Azure additionally call `codity config set-pat --provider <vcs>` with a PAT.

`generate()` also writes `docs/codity-setup.md` (one-time setup checklist) and appends a TODO checklist to `LEDGER.md`.

The **`codity-ai-review`** governance skill (REQ-356) documents the full Codity.ai CLI workflow for agents: install, `codity login` (magic-link auth), `codity init`, daily commands (`review --staged`, `scan --staged`, `test-gen --staged`, `doctor`), VCS-specific PAT setup, and the AGENTS.md rule.

The **AGENTS.md template** (REQ-355) includes a conditional Codity section: projects with Codity configured SHOULD run `codity review --staged` before commits touching production code; HIGH-severity findings block the commit; MEDIUM findings require inline acknowledgement.

**Architecture invariant (I15):** The VCS-detection heuristic MUST default to `"github"` when no signals are present (scaffold.yml absent, no `.gitlab-ci.yml`, no `azure-pipelines.yml`). New VCS hosts require a new detection heuristic AND a corresponding workflow writer method.
