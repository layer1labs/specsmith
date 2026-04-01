# AGENTS.md — specsmith

## Identity
- **Project**: specsmith
- **Type**: CLI tool (Python) — Spec Section 17.3
- **Spec version**: 0.1.0-alpha.1
- **Language**: Python 3.10+
- **Platforms**: Windows, Linux, macOS

## Purpose
Forge governed project scaffolds from the Agentic AI Development Workflow Specification.

## Quick Commands
- `pip install -e ".[dev]"` — dev install
- `pytest tests/ -v` — run tests
- `ruff check src/ tests/` — lint
- `ruff format src/ tests/` — format
- `mypy src/specsmith/` — typecheck
- `specsmith init` — scaffold a new project
- `specsmith audit` — health checks
- `specsmith validate` — governance consistency

## File Registry
- `src/specsmith/` — package source
- `src/specsmith/templates/` — Jinja2 scaffold templates
- `src/specsmith/integrations/` — agent platform adapters
- `tests/` — test suite
- `docs/REQUIREMENTS.md` — formal requirements (37 REQs)
- `docs/TEST_SPEC.md` — test specifications (30 TESTs)
- `docs/governance/` — modular governance docs
- `AGENT-WORKFLOW-SPEC.md` — the specification itself

## Governance
This project follows its own specification. See:
- [Rules](docs/governance/rules.md) — hard rules and stop conditions
- [Workflow](docs/governance/workflow.md) — session lifecycle
- [Roles](docs/governance/roles.md) — agent role boundaries
- [Context budget](docs/governance/context-budget.md) — token optimization
- [Verification](docs/governance/verification.md) — acceptance criteria
- [Drift metrics](docs/governance/drift-metrics.md) — health signals

## Tech Stack
- CLI: click
- Templates: jinja2
- Config: pydantic + pyyaml
- Output: rich
- Lint: ruff
- Types: mypy (strict)
- Tests: pytest + pytest-cov
- CI: GitHub Actions (3 OS × 3 Python)
