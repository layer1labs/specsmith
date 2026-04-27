# Contributing to forge-cli

Thank you for your interest in contributing! This project uses the [Agentic AI Development Workflow Specification](https://github.com/BitConcepts/specsmith) for governance.

## Getting Started

1. Fork the repository and clone your fork
2. Create a feature branch from `develop`: `git checkout -b feat/your-feature`
3. Make your changes following the guidelines below
4. Push and open a pull request against `develop`

## Development Workflow

This project follows a **propose → check → execute → verify → record** workflow:

1. **Read** `AGENTS.md` and `LEDGER.md` before starting work
2. **Propose** your change (issue or PR description)
3. **Implement** on a feature branch
4. **Verify** — run all checks before submitting:
   - Lint: `ruff check`
   - Type check: `mypy`
   - Test: `pytest`
   - Security: `pip-audit`
5. **Record** — update `LEDGER.md` with what you changed and why

## Pull Request Guidelines

- Reference the issue number in your PR title (e.g., `feat: add widget support (#123)`)
- All CI checks must pass before merge
- At least 1 approval(s) required
- Keep commits focused and well-described
- Update `docs/REQUIREMENTS.md` and `docs/TEST_SPEC.md` if your change adds or modifies requirements

## Code Style

- Format: `ruff format`
- Lint: `ruff check`

## Governance

This project's governance is defined in `AGENTS.md` with modular details in `docs/governance/`. Please respect the authority hierarchy described there.

## License

By contributing, you agree that your contributions will be licensed under the project's MIT license.
