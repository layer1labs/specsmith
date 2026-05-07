# Planned Architecture Requirements — specsmith

> These requirements were captured during the April 2026 research session using
> domain-prefixed IDs (OPS, CMD, MAS, etc.). They are **not yet formally assigned
> sequential IDs** and are not in `.specsmith/requirements.json`.
>
> Migration work item: assign each group sequential REQ-NNN IDs, add to
> `scripts/rebuild_requirements_md.py`, regenerate machine state, and create
> corresponding TEST-NNN entries in root TESTS.md.
>
> See [`/REQUIREMENTS.md`](../REQUIREMENTS.md) for the active machine-authoritative
> requirement set (REQ-001..REQ-128).

---

## OPS — Typed Execution Layer

- OPS-001: All tool handlers MUST use a typed `ProjectOperations` class for file, git/VCS, and search operations. Direct raw shell string assembly in tool handlers is prohibited.
- OPS-002: `ProjectOperations` MUST expose file operations (`read_file`, `write_file`, `list_dir`, `glob`, `search`) implemented via Python `pathlib`/`stdlib` — no subprocess calls.
- OPS-003: `ProjectOperations` MUST expose git/VCS operations (`status`, `log`, `diff`, `add`, `commit`, `push`, `create_branch`, `create_pr`) returning structured result objects.
- OPS-004: All `ProjectOperations` methods MUST return a typed result containing at minimum `exit_code`, `stdout`, `stderr`, and `elapsed_ms`.
- OPS-005: The existing `executor.py` `run_tracked()` function MUST be preserved as a narrow fallback for commands that have no Python equivalent.
- OPS-006: `ProjectOperations` MUST be cross-platform (Windows, Linux, macOS) without platform-specific code branches in call sites.

## CMD — Harness Commands

- CMD-001: The `commands/` package MUST implement all priority harness slash commands available inside `specsmith run`.
- CMD-002: Session management commands MUST include: `/model`, `/provider`, `/tier`, `/status`, `/save`, `/clear`, `/compact`, `/export`.
- CMD-003: Multi-agent commands MUST include: `/spawn`, `/team`, `/team-status`, `/worktree`.
- CMD-004: Continuous learning commands MUST include: `/learn`, `/learn-eval`, `/instinct-status`, `/instinct-import`, `/instinct-export`.
- CMD-005: Evaluation commands MUST include: `/eval define`, `/eval run`, `/eval report`, `/eval compare`.
- CMD-006: Orchestration commands MUST include: `/multi-plan`, `/multi-execute`, `/route`.
- CMD-007: Hook control commands MUST include: `/hooks-enable`, `/hooks-disable`, `/hook-profile`.
- CMD-008: MCP commands MUST include: `/mcp-list`, `/mcp-add`, `/mcp-configure`.
- CMD-009: Security commands MUST include: `/security-scan`, `/audit-prompt`.

## MAS — Multi-Agent Spawning

- MAS-001: The runner MUST provide an `AgentTool` (TaskTool) as a native LLM-callable tool that spawns subagent instances.
- MAS-002: Subagent spawning MUST support hub-and-spoke and agent-teams (peer-to-peer via filesystem mailbox) coordination modes.
- MAS-003: The filesystem mailbox for agent teams MUST be stored at `.specsmith/teams/{team}/mailbox/{agent}.json`.
- MAS-004: When `isolation=worktree`, the spawner MUST create a git worktree at `.specsmith/worktrees/{agent_id}/`.
- MAS-005: Subagents MUST NOT be able to spawn further subagents (no recursive nesting).
- MAS-006: The parent agent MUST receive a distilled summary from each subagent on completion, not the full transcript.
- MAS-007: Agent team mode MUST be gated behind a feature flag (`SPECSMITH_AGENT_TEAMS=1`).

## ORC — Orchestrator Meta-Agent

- ORC-001: specsmith MUST provide an orchestrator meta-agent for task classification, routing, and optimization — not execution.
- ORC-002: The orchestrator MUST default to a small local Ollama model so orchestration incurs zero cloud API cost.
- ORC-003: The orchestrator MUST maintain an agent registry with type, model, provider, cost_tier, capabilities, avg_latency_ms, confidence.
- ORC-004: The orchestrator MUST emit exactly one structured next-action per task.
- ORC-005: The orchestrator MUST route cheap tasks to Ollama workers and complex tasks to cloud providers.
- ORC-006: The orchestrator MUST run a post-session self-evaluation to update routing thresholds.

## FLG — Feature Flag System

- FLG-001: specsmith MUST implement a feature-flag system controlling which tool schemas are sent to the LLM.
- FLG-002: Feature flags MUST be configurable via environment variables and `scaffold.yml` under `agent.flags`.
- FLG-003: Agent teams, worktree isolation, KAIROS daemon mode, security scanner, and MCP tools MUST be flag-gated.

## LRN — Instinct / Continuous Learning System

- LRN-001: specsmith MUST implement an instinct persistence system in `src/specsmith/instinct.py`.
- LRN-002: Each instinct record MUST contain: id, trigger_pattern, content, confidence, project_scope, created, last_used, use_count.
- LRN-003: The `SESSION_END` hook MUST extract candidate instincts for user review.
- LRN-004: The `/learn` command MUST promote a pattern to an instinct with an initial confidence score.
- LRN-005: Instinct confidence MUST be updated based on application success/rejection.
- LRN-006: Instincts MUST be importable and exportable as `.md` files.
- LRN-007: `/instinct-status` MUST display all active instincts sorted by confidence.

## EDD — Eval Harness (Eval-Driven Development)

- EDD-001: specsmith MUST implement an eval harness in `src/specsmith/eval/`.
- EDD-002: The eval model MUST define: Task, Trial, Grader, Transcript, Outcome.
- EDD-003: Tasks MUST be stored as Markdown at `.specsmith/evals/{feature}.md` with YAML frontmatter.
- EDD-004: The harness MUST support CodeGrader, ModelGrader, and HumanFlag grader types.
- EDD-005: The harness MUST compute `pass@k` and `pass^k` metrics.
- EDD-006: Default grading MUST be git-based outcome grading, not execution-path assertion.
- EDD-007: `/eval run --trials k` MUST run k independent trials and report results.
- EDD-008: The harness MUST distinguish capability evals from regression evals.

## MEM — Agent Memory Persistence

- MEM-001: specsmith MUST implement cross-session agent memory in `src/specsmith/memory.py`.
- MEM-002: Agent memory MUST be structured JSON with accumulated patterns, preferred approaches, known project facts, and failure history.
- MEM-003: The `SESSION_START` hook MUST inject relevant memories into the system prompt (token-budget-aware).
- MEM-004: Agent memory layout MUST be compatible with Theia AI's `~/.theia/agent-memory/` convention.

## HRK — Hook Runtime Controls

- HRK-001: Hooks MUST be enable/disable-able at runtime without restarting the session.
- HRK-002: Hook profiles MUST be loadable via `/hook-profile`.
- HRK-003: New triggers: `SUBAGENT_START`, `SUBAGENT_STOP`, `CONTEXT_COMPACT`, `EVAL_PASS`, `EVAL_FAIL`.
- HRK-004: `SUBAGENT_START` MUST fire before spawning; a hook MAY block the spawn.
- HRK-005: `SUBAGENT_STOP` MUST fire when a subagent completes.
- HRK-006: `CONTEXT_COMPACT` MUST fire before context trimming.

## SRV — Service / Daemon

- SRV-001: specsmith MUST provide a `specsmith serve` command (already shipped in v0.7.0).
- SRV-002: REST endpoints: `GET/POST /sessions`, `GET /agents`, `GET /instincts`, `GET /evals`, `POST /index`, `GET /health`.
- SRV-003: WebSocket endpoint at `/ws/session/{id}` for live session I/O using the existing JSONL event schema.
- SRV-004: `AgentRunner._emit_event()` MUST use an `EventSink` protocol (`StdoutSink` / `WebSocketSink`).
- SRV-005: The Praxis terminal MUST connect to `specsmith serve` over HTTP/WebSocket for all governance operations.

## RTR — Retrieval Upgrade

- RTR-001: `retrieval.py` MUST be upgraded from term-frequency to BM25 ranking using `rank_bm25`.
- RTR-002: The retrieval index MUST support file-watcher-based refresh.
- RTR-003: Retrieval results MUST be token-counted before injection to prevent context budget overruns.

## MCP — MCP Management

- MCP-001: specsmith MUST provide MCP server configuration templates via `/mcp-add` or `specsmith mcp add`.
- MCP-002: The MCP server registry MUST list configured servers with status and tool surfaces.
- MCP-003: MCP configuration MUST be storable in `scaffold.yml` under `agent.mcp_servers`.

## SEC — Security Scan

- SEC-001: specsmith MUST provide a `/security-scan` command running a dedicated security analysis agent.
- SEC-002: The security scan MUST check dependency vulnerabilities, OWASP-style code patterns, and exposed secrets.
- SEC-003: `/audit-prompt` MUST analyze a prompt string for injection vectors.
- SEC-004: Security scan results MUST be structured and stored at `.specsmith/security-reports/`.

## IDE — Theia IDE Application

- IDE-001: A `specsmith-ide` application MUST be created on Eclipse Theia with `@theia/ai-core`, `@theia/ai-chat`, `@theia/ai-ide`.
- IDE-002: specsmith-ide MUST ship: `@specsmith/ai-agents`, `@specsmith/epistemic-ui`, `@specsmith/eval-ui`, `@specsmith/service-client`.
- IDE-003: specsmith-ide MUST connect to `specsmith serve` over WebSocket.
- IDE-004: specsmith-ide MUST leverage Theia AI's existing MCP support, ShellExecutionTool, and agent skills system.
- IDE-005: specsmith-ide MUST be packageable as an Electron desktop application.

## PRX — Praxis Terminal Integration (NEW)

- PRX-001: `specsmith serve` MUST be the sole interface between the Praxis Rust terminal and the Python governance stack.
- PRX-002: Praxis MUST spawn `specsmith serve` as a managed child process at terminal startup.
- PRX-003: Praxis MUST call `specsmith preflight` via the REST API before executing any governance-gated action.
- PRX-004: Praxis MUST call `specsmith verify` via the REST API after changes and display confidence scores in the terminal UI.
- PRX-005: Praxis settings and governance dashboard MUST be implemented as a WebView panel for Playwright testability.
- PRX-006: The Praxis terminal MUST be based on the open-source Warp fork that includes BYOE endpoint support.
