# No Hardcoded Versions Rule

## Policy

Version strings MUST NOT be hardcoded in documentation, tests, or application code outside of `pyproject.toml`.

## Single Source of Truth

- **`pyproject.toml`** `version` field is the sole source of truth for the package version.
- **`__init__.py`** reads the version at runtime via `importlib.metadata.version()`.
- **Documentation** uses `{{ version }}` placeholders resolved by a MkDocs hook at build time.
- **Tests** compare against `importlib.metadata.version()`, never hardcoded strings.

## What to Check

Before every commit, verify:

- No literal version strings (e.g., `0.1.3`, `0.2.0`) appear in:
  - `docs/site/*.md` — use `{{ version }}` instead
  - Test assertions — use `from specsmith import __version__` or `importlib.metadata`
  - README.md badge text — use shields.io dynamic badges
  - Troubleshooting docs — say "latest version" not "v0.1.x+"
- `pyproject.toml` is the ONLY file that contains the actual version number
- `__init__.py` fallback value is only for uninstalled source runs

## For Managed Projects

Projects scaffolded by specsmith follow the same pattern:
- `init.py.j2` generates `importlib.metadata.version()` code
- `pyproject.toml.j2` sets the initial version; all other code reads it dynamically
- CI dev-release workflows calculate dev versions from git tags, not source files

## Release Process

When bumping versions, `specsmith release` updates `pyproject.toml` (the source of truth). The releaser also updates `config.py` spec_version default so new scaffolds use the current version. No other files need version string changes.
