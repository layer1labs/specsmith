# Contributing

See the full [CONTRIBUTING.md](https://github.com/BitConcepts/specsmith/blob/main/CONTRIBUTING.md) in the repository.

## Quick Setup

```bash
git clone https://github.com/BitConcepts/specsmith.git
cd specsmith
pip install -e ".[dev]"
pre-commit install
```

## Running Checks

```bash
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/specsmith/
pytest tests/ -v
```

## Adding a New Project Type

1. Add enum value to `config.py` (`ProjectType`)
2. Add type label and section ref (`_TYPE_LABELS`, `_SECTION_REFS`)
3. Add directory structure to `scaffolder.py` (`_get_empty_dirs`)
4. Add tool entries to `tools.py` (`_TOOL_REGISTRY`)
5. Add CI metadata to `tools.py` (`LANG_CI_META`) if the language is new
6. Add type-specific rules to `templates/agents.md.j2`
7. Add domain-specific starters to `templates/docs/requirements.md.j2` and `test-spec.md.j2`
8. Add tests
9. Update documentation site (`docs/site/project-types.md`)
10. Update `README.md`

## Code Standards

- SPDX headers on all `.py` files (MIT, BitConcepts, LLC.)
- Must pass `ruff check`, `ruff format --check`, `mypy --strict`
- All features require tests
- Windows scripts: `.cmd` only (no `.ps1`)
- Line length: 100

## Documentation

When making changes that affect user-facing behavior, **always update**:

1. `README.md` — if commands, types, or features change
2. `docs/site/` — the Read the Docs site pages
3. `CHANGELOG.md` — all notable changes
4. `docs/REQUIREMENTS.md` — if new requirements are introduced
5. `docs/TEST_SPEC.md` — if new tests are added
