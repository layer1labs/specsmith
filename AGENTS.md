# AGENTS.md — specsmith

## Identity
- **Project**: specsmith
- **Type**: CLI tool (Python) + AEE library + AG2 agent shell — Spec Section 17.3
- **Spec version**: 0.3.10
- **Language**: Python 3.10+
- **Platforms**: Windows, Linux, macOS
- **Agent layer**: AG2 (`ag2[ollama]`) over Ollama local models

## Purpose
Applied Epistemic Engineering toolkit for AI-assisted development. Treats belief systems
like code: codable, testable, deployable. Co-installs the `epistemic` standalone library.
Includes an AEE-integrated agentic client (`specsmith run`) and an AG2-based agent shell
(`specsmith agent run`) supporting Planner/Builder/Verifier agents over local Ollama models.

## Agent Architecture (AG2 Realignment — April 2026)

The system has four layers:

1. **Product Surface** — specsmith CLI, VS Code plugin, PySide6 GUI, existing REPL
2. **Agent Layer (AG2)** — Planner/Builder/Verifier agents in `src/specsmith/agents/`
3. **Model Runtime (Ollama)** — local inference via `OllamaProvider`, structured outputs, tool calling
4. **Verification Layer** — pytest, VS Code extension tests, traces, golden outputs

Do not collapse these layers into one blob. Each has clear boundaries.

### Agent Roles
- **Planner**: understands tasks, generates execution plans, outputs breakdown + acceptance criteria
- **Builder**: makes code/doc changes, wires features, patches defects
- **Verifier**: runs tests, validates behavior, accepts or rejects changes

### Ollama Policy
- Ollama is the default local model backend
- Use structured outputs and tool calling whenever possible
- Abstract model selection behind config — never hardcode one model
- Primary orchestration model + optional lighter utility model

## Quick Commands
- `pip install -e ".[dev]"` — dev install
- `pytest tests/ -v` — run tests
- `ruff check src/ tests/` — lint
- `ruff format src/ tests/` — format
- `mypy src/specsmith/` — typecheck
- `specsmith init` — scaffold a new project
- `specsmith audit` — health checks
- `specsmith validate` — governance consistency
- `specsmith stress-test` — AEE adversarial challenges
- `specsmith epistemic-audit` — full AEE pipeline
- `specsmith belief-graph` — belief artifact dependency graph
- `specsmith trace seal/verify/log` — cryptographic trace vault
- `specsmith run` — agentic REPL (requires provider)
- `specsmith run --base-url <url>` — run with custom local provider (Jan, LM Studio, vLLM)
- `specsmith serve` — start local daemon with REST + WebSocket API _(planned)_
- `specsmith agent providers` — check provider status

### Planned agentic REPL slash commands (Phase 1–2)
- `/model <name>` — switch model mid-session
- `/spawn <type> <prompt>` — spawn a subagent worker
- `/team <name>` — create a peer-to-peer agent team
- `/learn [pattern]` — promote a session pattern to an instinct
- `/instinct-status` — show active instincts with confidence scores
- `/eval define <feature>` — create an eval task definition
- `/eval run [--trials k]` — run eval trials and compute pass@k
- `/hooks-enable <name>` / `/hooks-disable <name>` — runtime hook control
- `/security-scan` — run OWASP-style security analysis
- `/mcp-list` — list configured MCP servers

## File Registry
- `src/specsmith/` — specsmith CLI package
- `src/epistemic/` — standalone AEE library (canonical location)
- `src/specsmith/epistemic/` — compatibility shim (re-exports from epistemic)
- `src/specsmith/agent/` — existing agentic client (providers, tools, runner, hooks, skills)
- `src/specsmith/agent/profiles/` — built-in agent profiles (planner, verifier, epistemic-auditor)
- `src/specsmith/agents/` — **AG2 agent shell** (new — Planner, Builder, Verifier)
- `src/specsmith/agents/tools/` — AG2 tool surface (filesystem, shell, tests, git, docs, vscode)
- `src/specsmith/agents/workflows/` — AG2 workflows (analyze_edit_test, bugfix, improve_specsmith)
- `src/specsmith/agents/runtime/` — Ollama bridge for AG2
- `src/specsmith/agents/config.py` — AG2 agent config from scaffold.yml
- `src/specsmith/agents/cli.py` — `specsmith agent run|plan|status|verify` commands
- `src/specsmith/templates/` — Jinja2 scaffold templates (incl. 4 new epistemic templates)
- `src/specsmith/integrations/` — agent platform adapters
- `src/specsmith/commands/` — harness slash command implementations _(stub — not yet wired)_
- `src/specsmith/agents/instinct.py` — instinct persistence and continuous learning _(planned)_
- `src/specsmith/agents/memory.py` — cross-session agent memory _(planned)_
- `src/specsmith/agents/eval/` — EDD eval harness (Task/Trial/Grader/pass@k) _(planned)_
- `src/specsmith/agents/flags.py` — feature flag system for tool schema gating _(planned)_
- `src/specsmith/server/` — specsmith serve daemon (REST + WebSocket) _(planned)_
- `tests/` — test suite (208 pass, 18 sandbox failures as of 2026-04-20)
- `docs/baseline-audit.md` — Phase 0 architecture audit
- `docs/REQUIREMENTS.md` — formal requirements (extended April 2026)
- `docs/TEST_SPEC.md` — test specifications
- `docs/ARCHITECTURE.md` — architecture reference (extended April 2026)
- `docs/governance/` — modular governance docs
- `docs/AGENT-WORKFLOW-SPEC.md` — the specification itself

## Governance
This project follows its own specification. See:
- [Agent Workflow Specification](docs/AGENT-WORKFLOW-SPEC.md) — the full spec (H1–H13, session lifecycle, proposal format, ledger format)
- [Epistemic Axioms](docs/governance/EPISTEMIC-AXIOMS.md) — AEE axioms applied to specsmith

Note: modular governance files are not generated for specsmith's own repo since
AGENTS.md is < 200 lines. Run `specsmith upgrade --full` to generate them if needed.

## Tech Stack
- CLI: click
- Templates: jinja2
- Config: pydantic + pyyaml
- Output: rich
- Agent shell: AG2 (`ag2[ollama]`)
- Local LLM: Ollama v0.3+ (stdlib urllib, /api/chat)
- Lint: ruff
- Types: mypy (strict)
- Tests: pytest + pytest-cov
- CI: GitHub Actions (3 OS × 3 Python)
- Docs: Read the Docs (specsmith.readthedocs.io)
- Retrieval: rank_bm25 _(planned — upgrade from keyword scoring)_
- File watching: watchdog _(planned — index refresh)_
- Service: FastAPI or aiohttp + websockets _(planned — specsmith serve)_
- IDE: Eclipse Theia + @theia/ai-core _(planned — specsmith-ide repo)_

## Project Rules (AG2 Realignment)

These rules apply to all agents working on this codebase:

1. **Evidence over claims** — do not say "works" unless it is demonstrated with test output
2. **Small safe steps** — prefer small validated improvements over large speculative rewrites
3. **Preserve the existing product** — wrap and improve the current system before replacing major pieces
4. **Tooling first** — a good tool loop beats a clever prompt
5. **Tests are product** — if the system cannot prove itself, it is not ready to improve itself
6. **Inspect before editing** — always read the relevant files before proposing changes
7. **Preserve architectural boundaries** — do not collapse the four layers
8. **Run the narrowest relevant tests** — after every change, run only the tests that cover it
9. **Update docs alongside code** — undocumented features are governance violations (H14)
10. **Use Ollama as default** — local model provider; cloud providers are opt-in
11. **Keep AG2 shell modular** — tools, agents, workflows, and runtime are separate packages
12. **Leave clear follow-up tasks** — when work is partial, document what remains

## Documentation Rule (H14 — Hard Rule)

The Read the Docs site (`docs/site/`) is the authoritative user manual.
Before committing ANY change, verify documentation is current:
1. Check if the change affects user-facing behavior, CLI commands, governance files, or configuration
2. If yes: update the relevant `docs/site/*.md` page(s) in the SAME commit
3. Update `README.md` if it affects the project summary
4. Update `CHANGELOG.md` under [Unreleased]
5. README.md links to RTD for details — do NOT duplicate RTD content in README
6. The VS Code extension docs live in `docs/site/vscode-extension.md` — update when GovernancePanel, SettingsPanel, SessionPanel, or HelpPanel change

This is a hard rule. Undocumented features are governance violations. Never commit code without checking for documentation gaps.
