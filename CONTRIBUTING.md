# Contributing to specsmith

## Development Setup

```bash
git clone https://github.com/BitConcepts/specsmith.git
cd specsmith
pip install -e ".[dev]"
```

## Running Checks

```bash
# Tests
pytest tests/ -v

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/specsmith/

# All at once
ruff check src/ tests/ && ruff format --check src/ tests/ && mypy src/specsmith/ && pytest tests/ -v
```

## Pre-commit Hooks

```bash
pre-commit install
```

This runs ruff lint/format on every commit.

## Docker Local CI

```bash
docker compose -f docker-compose.test.yml run test
docker compose -f docker-compose.test.yml run lint
docker compose -f docker-compose.test.yml run typecheck
```

## Making Changes

This project follows its own Agentic AI Development Workflow Specification.

1. Read `AGENTS.md` for project context
2. Check `LEDGER.md` for open TODOs and current state
3. Propose changes before implementing
4. Write tests for new functionality
5. Ensure all checks pass before submitting a PR

## Pull Requests

- Branch from `main`
- Include tests for new features
- All CI checks must pass (lint, typecheck, test × 9 matrix, security)
- Update `CHANGELOG.md` under `[Unreleased]`
- Update `docs/REQUIREMENTS.md` and `docs/TEST_SPEC.md` if adding new features
