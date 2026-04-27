# Contributing

## Setup

```bash
git clone https://github.com/BitConcepts/specsmith.git
cd specsmith
pip install -e ".[dev]"
pre-commit install
```

## Running Checks

```bash
ruff check src/ tests/          # Lint
ruff format --check src/ tests/  # Format check
mypy src/specsmith/              # Type check (strict)
pytest tests/ -v                 # All tests
pytest tests/sandbox/ -v         # Sandbox integration tests only
specsmith audit --project-dir .  # Self-governance check
```

## Adding a New Project Type

This is the most common contribution. Follow these 10 steps:

1. **Enum** — Add value to `ProjectType` in `config.py`
2. **Labels** — Add to `_TYPE_LABELS` and `_SECTION_REFS` in `config.py`
3. **Directories** — Add to `_get_empty_dirs()` in `scaffolder.py`
4. **Tools** — Add `ToolSet` to `_TOOL_REGISTRY` in `tools.py`
5. **CI metadata** — Add to `LANG_CI_META` in `tools.py` if the language is new
6. **AGENTS.md rules** — Add type branch to `templates/agents.md.j2`
7. **Requirements template** — Add domain starters to `templates/docs/requirements.md.j2`
8. **Test spec template** — Add domain test stubs to `templates/docs/test-spec.md.j2`
9. **Tests** — Add sandbox test in `tests/sandbox/`
10. **Documentation** — Update `docs/site/project-types.md` and `README.md`

Use the [New Project Type](https://github.com/BitConcepts/specsmith/issues/new?template=new_project_type.md) issue template.

## Code Standards

- SPDX headers on all `.py` files: `# SPDX-License-Identifier: MIT`
- Must pass `ruff check`, `ruff format --check`, `mypy --strict`
- All features require tests
- Windows scripts: `.cmd` only (no `.ps1`)
- Line length: 100
- Python 3.10+ compatibility

## Documentation Rule

When making changes that affect user-facing behavior, **always update in the same commit**:

1. `README.md` — commands, types, features
2. `docs/site/` — the Read the Docs pages
3. `CHANGELOG.md` — all notable changes
4. `docs/REQUIREMENTS.md` and `docs/TESTS.md` — if applicable

## Pull Request Process

1. Branch from `develop` (features) or `main` (hotfixes)
2. All CI must pass (lint, typecheck, test × 9 matrix, security)
3. `specsmith audit` must pass on specsmith itself
4. One approval required
5. Use the [PR template](https://github.com/BitConcepts/specsmith/blob/main/.github/PULL_REQUEST_TEMPLATE.md) checklist

## Reporting Issues

- [Bug Report](https://github.com/BitConcepts/specsmith/issues/new?template=bug_report.md)
- [Feature Request](https://github.com/BitConcepts/specsmith/issues/new?template=feature_request.md)
- [New Project Type](https://github.com/BitConcepts/specsmith/issues/new?template=new_project_type.md)
- [Discussions](https://github.com/BitConcepts/specsmith/discussions) for questions and ideas
