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

## 3. Existing Specsmith System

Specsmith currently includes:

- Click-based CLI entrypoint
- scaffold generation
- governance file generation
- AEE commands
- agentic client commands
- auditor/exporter/importer functionality
- optional LLM/provider support
- GUI workbench
- trace vault and ledger functionality
- compatibility shim for the standalone `epistemic` package

Existing major modules include:

- `cli.py`
- `config.py`
- `scaffolder.py`
- `tools.py`
- `importer.py`
- `exporter.py`
- `auditor.py`
- `ledger.py`
- `integrations/`
- `vcs/`
- `src/epistemic/`
- `src/specsmith/agent/`
- `src/specsmith/gui/`

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

### Phase 2 — Multi-Agent Layer

Planned modules:

- `src/specsmith/agent/spawner.py`
- `src/specsmith/agent/teams.py`
- `src/specsmith/agent/orchestrator.py`
- `src/specsmith/agent/flags.py`
- `src/specsmith/memory.py`

Phase 2 goals:

- subagent spawning
- team coordination
- orchestrator-worker routing
- feature-flagged tool schema visibility
- cross-session memory

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

## 15. Bootstrap Sequencing Rules

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

## 16. Non-Goals During Bootstrap

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

## 17. ChronoMemory ESDB

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

## 18. AI Skills Builder

Source: `src/specsmith/skills_builder.py`

Builds agent skills from natural-language descriptions following the SkillNet-style ontology. Each skill is a folder containing `SKILL.md` + `skill.json` with structured metadata: name, purpose, activation rules, input/output schema, epistemic contract, tools used, tests required, stop conditions.

REST endpoint: `GET /api/skills`.

## 19. MCP Server Generator

Source: `src/specsmith/mcp_generator.py`

Auto-scaffolds Model Context Protocol servers from natural-language tool descriptions using the FastMCP pattern. Generates `server.py`, `tool_schema.json`, `README.md` per server. Supports stdio and Streamable HTTP transports.

REST endpoint: `GET /api/mcp/servers`.

## 20. Kairos UX Integration

Kairos Settings pages that expose specsmith features via the governance REST API:

- **Governance page** — specsmith health, BYOE endpoint, project context, updater, bug report links
- **Compliance page** — requirement coverage, test coverage, gaps, traceability matrix
- **ESDB page** — ChronoMemory status, record counts, backend type, refresh
- Skills, Eval, Teams pages consume `GET /api/skills`, `GET /api/eval/suites`, `GET /api/teams`

All pages use async health polling via `GovernanceClient.get_json()` and follow the monolith SettingsWidget pattern.

## 21. HuggingFace Open LLM Leaderboard Integration

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

## 22. Bucket Scoring Engine

Source: `src/specsmith/agent/hf_leaderboard.py` (`_compute_bucket_scores`)

Three task-bucket scores computed from raw benchmark values (normalised 0–100):

- **Reasoning** = 0.35×MATH + 0.30×GPQA + 0.25×BBH + 0.10×IFEval
- **Conversational** = 0.40×IFEval + 0.35×MMLU-PRO + 0.25×BBH
- **Longform** = 0.35×MUSR + 0.35×IFEval + 0.30×MMLU-PRO

Ranked recommendation returns the top-10 models for a requested bucket. The engine merges HF-synced data with the existing `BASELINE_SCORES` so both cloud and local Ollama models appear in rankings.

Base+org-prefix deduplication: `Qwen/Qwen3-14B` is stored under both its full name and `Qwen3-14B` so vLLM-style repo-ID model names match correctly.

## 23. Model Capability Profiles

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

## 24. AI Model Pacer v2

Source: `src/specsmith/rate_limits.py` (upgraded `ModelRateLimitScheduler`)

Enhancements over the existing rolling-window scheduler:

- **EMA utilisation tracking** — exponentially-weighted moving average of RPM/TPM utilisation (`alpha=0.25`) surfaced in `snapshot()`
- **Adaptive concurrency** — `dynamic_concurrency` decreases on `on_rate_limit()`, restores after 120 s (incrementally, 60 s between steps)
- **Retry-After parsing** — `parse_retry_after_seconds()` extracts `"try again in Xs"` from provider error strings; used when exponential backoff alone is insufficient
- **Image token estimation** — `estimate_request_tokens()` accepts `image_count` and multiplies by a per-model `image_token_estimate` (default 4096)
- **Pre-dispatch budget check** — `acquire()` blocks until RPM + TPM budgets allow dispatch; `release()` wakes waiting callers

All operations are guarded by a single `threading.Condition` lock so the pacer is safe for concurrent agent sessions.

## 25. Multi-Provider LLM Client with Fallback

Source: `src/specsmith/agent/llm_client.py`

Provider-agnostic chat client that tries a configurable ordered list of providers, falling back on 401/403/429/5xx. No optional packages required — uses `urllib` only.

**LLMProvider ABC**: `name`, `key_name`, `default_model`, `is_configured()`, `chat()`.

Concrete providers: `MistralProvider`, `OpenAIProvider`, `GoogleProvider`, `OllamaProvider`, `MockProvider` (test-only).

**O-series translation**: OpenAI o1/o3/o4 models receive `max_completion_tokens` instead of `max_tokens` and their `system` messages are renamed to `developer`.

**vLLM guided-JSON**: endpoints of type `byoe` or `huggingface` receive `guided_json` + `chat_template_kwargs: {enable_thinking: false}` when a JSON schema is provided.

**Gemini parts extraction**: handles models that return answer text in `parts` rather than `content`.

**JSON extraction helper** (`_extract_json`): tries direct parse → `\`\`\`json` fence → first balanced `{}` block before raising.

Provider fallback decision: `_is_fallback_status(code)` returns True for 401, 403, 404, 408, 409, 425, 429, 5xx.

## 26. Endpoint Preset Registry

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

## 27. Suggested Profile Generation

Source: `src/specsmith/agent/provider_registry.py` (`suggest_profiles`)

Generates a list of ready-to-add `ProviderEntry` suggestions by inspecting:

1. Cloud API keys present in environment variables
2. Ollama models currently installed (`/api/tags`)
3. Custom BYOE endpoints in `providers.json`

For each backend, role-tuned parameter sets (temperature, max_tokens) are proposed following the AEE bucket taxonomy: `reasoning`, `conversational`, `longform`.

Suggestions are inert previews — the user calls `specsmith agent providers add` to persist.

CLI: `specsmith agent suggest-profiles`.

## 28. OEA Anti-Hallucination Governance Layer

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

## 29. YAML-Native Governance Layer
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
| `docs/requirements/yaml_governance.yml` | REQ-300..399 | YAML governance layer |

**Architecture invariants for YAML governance:**
- REQUIREMENTS.md and TESTS.md MUST NOT be hand-edited when governance-mode is `yaml`.
- The JSON cache MUST be regenerated by `specsmith sync` before any CI check.
- `specsmith validate --strict` MUST run on every push and PR (CI gate).

**CI integration**: The `validate-strict` job in `.github/workflows/ci.yml` runs `specsmith validate --strict --json` on every push and PR. The `sync-check` step runs `specsmith sync --check`. Both block the build on failure.

**Migration**: `scripts/migrate_governance_to_yaml.py` — idempotent script converting an existing Markdown-primary project to YAML-first mode:
1. Remove duplicate REQs from REQUIREMENTS.md
2. Re-sync `.specsmith/` JSON from cleaned Markdown
3. Export JSON to grouped YAML domain files under `docs/requirements/` and `docs/tests/`
4. Write `.specsmith/governance-mode = yaml`

Re-running the script on an already-migrated project produces no changes.
