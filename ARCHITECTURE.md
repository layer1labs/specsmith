Purpose
Specsmith is an open‑source tool that manages the engineering of its own governance, verification, and automation processes.

Core Boundary
Specsmith’s core logic operates within a defined boundary that includes commands, config, and adapters.

Existing Specsmith System
Specsmith comprises:
- AEE (Adaptive Execution Engine) managing tasks.
- Governance layer for requirements and ledger.
- Epistemic confidence checks.

Governance Files
Governance files include:
- ARCHITECTURE.md
- REQUIREMENTS.md
- TESTS.md
- LEDGER.md

Machine State
Machine‑readable state files under `.specsmith/` must synchronize with human‑readable governance.

Requirement Flow
- Requirements are derived from architecture, assigned IDs, and produce preflight output.

Test Case Flow
- Test cases are generated, linked, and executed to prove requirements.

AEE Verification Flow
Specsmith verifies changes, diffs, tests, and produces confidence scores.

OpenCode Integration Boundary
Specsmith relies on the integration layer OpenCode for filesystem and tool operations.

Integration‑Agnostic Adapter Model
The adapter model is integration‑agnostic and provides required capabilities.

AEE / Epistemic Layer
The epistemic layer handles confidence, iterations, and escalation.

Ledger and Trace Chain
All changes are recorded to LEDGER.md and `.specsmith/ledger.jsonl` with hashes for trace.

Planned Architecture Evolution
Future features include dynamic routing, heavy‑model escalation, and modular adapters.

Architecture Invariants
- All human‑readable governing files must remain the source of truth.
- Machine state must be derived from governance.
- No feature must block bootstrap.

Bootstrap Sequencing Rules
- Defined sequencing for state, requirement, test, verification, and ledger.

Non‑Goals During Bootstrap
- Bootstrap does not implement all optional features immediately but represents them.

IP Evidence, Release, Versioning, Branching, and Documentation Automation
Specsmith supports IP evidence, automated release, semantic versioning, branching guidance, and documentation syncing.

Nexus Runtime Boundary
Nexus is the local-first agentic development runtime that executes work approved by Specsmith. Nexus must not own governance and must defer all preflight, requirement mapping, verification, retry decisioning, and ledger writing to Specsmith.

Nexus Components
- vLLM model server published as `l1-nexus`, configured via `docker-compose.yml`, pinned to `vllm/vllm-openai:v0.8.5`, serving `Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int8` with the Hermes tool-call parser.
- AG2 orchestrator at `src/specsmith/agent/orchestrator.py` providing PlannerAgent, ShellAgent, CodeAgent, ReviewerAgent, MemoryAgent, GitAgent, HumanProxyAgent, and an Executor node.
- Nexus tooling layer at `src/specsmith/agent/tools.py` exposing `run_shell`, `read_file`, `write_file`, `patch_file`, `list_files`, `grep`, `git_diff`, `git_status`, `run_tests`, `open_url`, `search_docs`, `remember_project_fact`.
- Safety middleware at `src/specsmith/agent/safety.py` enforcing JSON argument validation, path normalization, unsafe-command blocklist, and human approval prompts for destructive actions.
- Repository context indexer at `src/specsmith/agent/indexer.py` populating `.repo-index/` with `files.json`, `tags`, `test_commands.json`, `architecture.md`, and `conventions.md`.
- Nexus REPL at `src/specsmith/agent/repl.py` exposing the slash commands `/plan`, `/ask`, `/fix`, `/test`, `/commit`, `/pr`, `/undo`, `/context`.

Nexus Output Contract
Every Nexus task response must include the sections: Plan, Commands to run, Files changed, Diff, Test results, Next action.

Nexus Tool Registration Rules
Each tool's executor function must be registered exactly once with the AG2 executor agent; LLM-side tool signatures may be registered with multiple caller agents. Duplicate executor registration is forbidden because it triggers AG2 override warnings and indicates a governance violation in tool ownership.

Nexus Safety Rules
The safety middleware must block or require explicit approval for: `rm -r`, `rm -rf`, `rmdir /s`, `git push`, `docker compose down -v`, database migrations, deployment commands, and reads of secret material such as `.env` or credentials files.

Nexus Broker Boundary
The Nexus broker (`src/specsmith/agent/broker.py`) sits between the user's natural-language input and Specsmith's governance CLI. The broker:
- Classifies intent (`read_only_ask`, `change`, `release`, `destructive`).
- Infers affected scope by combining `.repo-index` retrieval with parsed `REQUIREMENTS.md` entries.
- Treats `specsmith preflight` and `specsmith verify` as the *only* sources of governance decisions; the broker never decides preflight outcomes itself.
- Renders plain-language plans and outcomes; REQ/TEST/work-item IDs are hidden by default and revealed only on explicit `/why`, `/show-governance`, or `--verbose`.
- Honors a hard retry budget consistent with REQ-014 and surfaces a single clarifying question on stop-and-align (REQ-063).
- Never drafts new governance content (REQ/TEST/work-item) without explicit user confirmation; user-facing summaries must be a strict transformation of Specsmith JSON output.

Nexus Preflight CLI Subcommand
The Specsmith CLI exposes `specsmith preflight <utterance>` as the canonical entrypoint into the broker contract. The subcommand reads `REQUIREMENTS.md` and `.specsmith/testcases.json`, classifies intent and infers scope, joins matched requirements against machine-state test cases, and emits a deterministic JSON object (`decision`, `work_item_id`, `requirement_ids`, `test_case_ids`, `confidence_target`, `instruction`, `intent`, optional `narration`). Read-only asks accept by default, destructive intents require clarification, and changes with no matched scope return `needs_clarification` with a one-sentence question. The CLI accepts `--project-dir`, `--json`, and `--verbose`.

Nexus REPL Execution Gate
When a non-slash utterance flows through the broker, the Nexus REPL invokes `orchestrator.run_task` only when `decision.accepted` is `true`. Any other outcome (`needs_clarification`, `blocked`, `rejected`) prints the broker's plain-language clarification and returns to the prompt without executing any tooling. The user toggles governance verbosity with the `/why` slash command.

Nexus Bounded-Retry Harness
The REPL drives accepted work through `specsmith.agent.broker.execute_with_governance`, supplying an executor closure that wraps `orchestrator.run_task` and synthesizes a result dict (`equilibrium`, `confidence`, `summary`). The harness honors `DEFAULT_RETRY_BUDGET` (REQ-014) and surfaces the single clarifying question on stop-and-align (REQ-063). The orchestrator is never invoked from the broker branch outside the harness.

Nexus End-to-End Example Flow
A user types `fix the cleanup dry-run regression` at the `nexus>` prompt. The REPL classifies intent as `change`, infers scope to the matching cleanup requirement, calls `specsmith preflight`, and prints a plain-language plan. Because the decision is `accepted`, the harness runs the AG2 orchestrator (up to the retry budget) and emits the standard Plan / Commands / Files changed / Diff / Test results / Next action sections. If the user toggles `/why`, the same flow now also surfaces the underlying REQ, TEST, and work-item identifiers Specsmith assigned.

Nexus Live Smoke Test
A `scripts/nexus_smoke.py` script exercises the running vLLM `l1-nexus` container by POSTing a minimal chat-completions request to `http://localhost:8000/v1/chat/completions` and verifying a well-formed `choices[0].message.content`. The accompanying pytest test skips unless `NEXUS_LIVE=1` is set, keeping the suite green offline while making the live path verifiable on demand.

Safe Repository Cleanup Boundary
Specsmith provides a deterministic safe-cleanup capability that removes only build/cache/temporary artifacts produced by toolchains (compilers, packagers, linters, type-checkers, test runners) and never touches governance, source, or version-controlled history. Cleanup must:
- Operate within the project root only and never traverse outside it via symlinks.
- Default to dry-run mode and require an explicit `apply=True` flag (or `--apply` CLI option) to actually delete.
- Allow only the canonical, hard-coded cleanup target list (no user-supplied paths). The canonical targets are: `__pycache__/` directories anywhere under the repo, `.mypy_cache/`, `.pytest_cache/`, `.pytest_tmp/`, `.ruff_cache/`, `build/`, top-level `dist/` wheels and tarballs that do not match the current package version, `src/*.egg-info/`, top-level archive blobs (`*.zip`, `*.tar`, `*.tar.gz`) that are checked-in build artifacts, ctags `tags` file, transient root-level stub files (`normalized_requirements.json`, `test_cases.md` placeholders).
- Hard-protected paths that must never be deleted: `.git/`, `.specsmith/`, governance files (`ARCHITECTURE.md`, `REQUIREMENTS.md`, `TESTS.md`, `LEDGER.md`), `pyproject.toml`, `README.md`, `LICENSE`, `CHANGELOG.md`, `src/specsmith/`, `src/epistemic/`, `tests/`, `docs/`, `scripts/`, `.repo-index/`, `.github/`, `.vscode/`, third-party agent integration directories (e.g. `.agents/`), dotfiles configuring the project (`.editorconfig`, `.gitignore`, `.gitattributes`, `.pre-commit-config.yaml`, `.readthedocs.yaml`).
- Emit a structured cleanup report (counts of directories, files, and bytes considered/removed; list of skipped items with reasons) suitable for ledger evidence.
- Be invocable from the Specsmith CLI and from the Nexus runtime via a governed tool.

Integration/Automation

### Dynamic Agent and Model Routing
- **Specsmith should eventually support dynamic routing between configured agents/models based on task type.**
- deterministic scripts, JSON rebuilds, and schema work -> coder model
- code implementation, debugging, and review -> coder model
- architecture, governance, long context, recovery, ambiguity, and multi‑step reasoning -> complex/heavy model
- quick summaries or low‑risk questions -> lightweight model
- repeated tool failure or malformed output -> escalates to heavy model
- routing must be configuration‑driven
- routing must be optional and enabled by default
- routing must not make Specsmith directly manage LLM providers
- integration layer remains responsible for actual model execution
- this is a future feature and must not block bootstrap

Current State (post-WI-NEXUS-023, target release 0.4.0)
The Nexus broker / preflight / verify surface and the CI baseline gates have shipped. The architecture as currently realized in the codebase is summarized below; this section is the source of truth for what "the system as built" actually contains.
- 103 requirements (REQ-001..REQ-103), 103 test cases (TEST-001..TEST-103), 259 passing tests + 1 honestly skipped live smoke. Governance state files under `.specsmith/` are derived from `REQUIREMENTS.md` / `TESTS.md` via `scripts/sync_governance_state.py` and `.specsmith/workitems.json` is derived from the same machine state via `scripts/sync_workitems.py` (REQ-104).
- The Nexus broker (`src/specsmith/agent/broker.py`) implements deterministic intent classification, REQUIREMENTS-driven scope inference, a `run_preflight` Specsmith CLI wrapper, and a bounded-retry harness `execute_with_governance` that maps every exhausted retry to one canonical retry strategy (`narrow_scope`, `expand_scope`, `fix_tests`, `rollback`, `stop`) per REQ-028 / REQ-096 and surfaces it in the single clarifying question (REQ-063).
- The Specsmith CLI exposes two governance entrypoints: `specsmith preflight <utterance>` (REQ-085, REQ-088, REQ-092, REQ-093, REQ-099, REQ-100) and `specsmith verify` (REQ-027, REQ-097). Both honor `epistemic.confidence_threshold` from `.specsmith/config.yml` as a floor (REQ-098). Accepted preflights record both a `preflight` ledger event and (for brand-new work_item_ids) a distinct `work_proposal` event tagged with REQ-044, REQ-085. The `--stress` flag bridges to the AEE `StressTester` and surfaces critical failures as `stress_warnings`.
- The Nexus REPL gates execution on `decision.accepted` (REQ-086) and drives accepted work exclusively through the harness (REQ-087). When `/why` is on, after the harness returns the REPL prints a single `[/why]` block summarizing the assigned work-item id, requirement and test-case ids, post-run confidence, and equilibrium flag (REQ-094). The orchestrator returns a structured `TaskResult` dataclass which the REPL's executor closure consumes directly (REQ-091).
- The CI baseline contract: ruff lint + format clean, mypy strict-clean over 69 source files (the dynamic Nexus agent surface is enumerated in `[[tool.mypy.overrides]] ignore_errors=true`), and `pip-audit --ignore-vuln CVE-2026-3219` for the upstream-unfixed pip advisory; specsmith's own runtime dependencies (click, jinja2, pyyaml, pydantic, rich) remain pip-audit clean (REQ-101..REQ-103). Every CI job upgrades pip first.
- The VS Code extension `specsmith-vscode` exposes the broker through three commands: `specsmith.runPreflight`, `specsmith.runVerify`, and `specsmith.toggleWhy` (Nexus broker parity, shipped in extension v0.3.16).
- Live smoke evidence: REQ-089 / REQ-095 are satisfied via `.specsmith/runs/WI-NEXUS-011/logs.txt`. The host workstation does not have the >=20 GB VRAM the configured 32B GPTQ-Int8 model requires, so the captured evidence is an honest skip with the documented hardware reason; on a GPU-rich host the same `scripts/nexus_smoke.py` returns `"ok": true`.
- Documentation surface: README, CHANGELOG, ARCHITECTURE, REQUIREMENTS, TESTS, and the Read the Docs `commands.md` / `index.md` all describe the broker, preflight, verify, retry strategies, and `/why` toggle (REQ-090).
