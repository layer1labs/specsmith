# AGENTS.md — specsmith

## Identity
- **Project**: specsmith
- **Type**: CLI tool (Python) + AEE library — Spec Section 17.3
- **Spec version**: 0.3.0
- **Language**: Python 3.10+
- **Platforms**: Windows, Linux, macOS

## Purpose
Applied Epistemic Engineering toolkit for AI-assisted development. Treats belief systems
like code: codable, testable, deployable. Co-installs the `epistemic` standalone library.
Includes an AEE-integrated agentic client (`specsmith run`) supporting Claude, GPT, Gemini,
and local Ollama models.

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
- `specsmith agent providers` — check provider status

## File Registry
- `src/specsmith/` — specsmith CLI package
- `src/epistemic/` — standalone AEE library (canonical location)
- `src/specsmith/epistemic/` — compatibility shim (re-exports from epistemic)
- `src/specsmith/agent/` — agentic client (providers, tools, runner, hooks, skills)
- `src/specsmith/templates/` — Jinja2 scaffold templates (incl. 4 new epistemic templates)
- `src/specsmith/integrations/` — agent platform adapters
- `tests/` — test suite
- `docs/REQUIREMENTS.md` — formal requirements
- `docs/TEST_SPEC.md` — test specifications
- `docs/governance/` — modular governance docs
- `docs/AGENT-WORKFLOW-SPEC.md` — the specification itself
- `C:\Users\trist\Development\BitConcepts\everything-claude-code` — ECC reference (local clone)

## Governance
This project follows its own specification. See:
- [Agent Workflow Specification](docs/AGENT-WORKFLOW-SPEC.md) — the full spec (H1–H13, session lifecycle, proposal format, ledger format)
- [Epistemic Axioms](docs/governance/epistemic-axioms.md) — AEE axioms applied to specsmith

Note: modular governance files are not generated for specsmith's own repo since
AGENTS.md is < 200 lines. Run `specsmith upgrade --full` to generate them if needed.

## Tech Stack
- CLI: click
- Templates: jinja2
- Config: pydantic + pyyaml
- Output: rich
- Lint: ruff
- Types: mypy (strict)
- Tests: pytest + pytest-cov
- CI: GitHub Actions (3 OS × 3 Python)
- Docs: Read the Docs (specsmith.readthedocs.io)

## Documentation Rule

The Read the Docs site (`docs/site/`) is the authoritative user manual.
When ANY feature is added, changed, or removed:
1. Update the relevant `docs/site/*.md` page(s) in the SAME commit
2. Update `README.md` if it affects the project summary
3. Update `CHANGELOG.md` under [Unreleased]
4. README.md links to RTD for details — do NOT duplicate RTD content in README
