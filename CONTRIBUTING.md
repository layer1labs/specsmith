# Contributing to specsmith

Thanks for helping improve specsmith. This guide covers local setup, quality gates, and pull request expectations for contributors.

## Local setup
```bash
git clone https://github.com/layer1labs/specsmith.git
cd specsmith
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e .[esdb]
```

## Test and quality commands
Run these before opening a PR:

```bash
python -m pytest tests/ -q
ruff check src/ tests/
ruff format src/ tests/
ruff format --check src/ tests/
```

### Two-tier ESDB validation
specsmith ships two Epistemic State Database backends: the built-in **SQLite**
backend (free, MIT) and the commercial **ChronoStore** backend (`chronomemory`
+ license). Before pushing changes that touch ESDB, storage, or migrations, run
the rebuildable two-tier harness. It builds specsmith into a fresh isolated venv
and exercises both backends end-to-end, mirroring the CI `esdb-backends` job:

```bash
# Windows (PowerShell) — recommended for correct Unicode
.\scripts\dev\test-esdb-backends.ps1

# macOS / Linux (or Windows without the wrapper)
python scripts/dev/test_esdb_backends.py
```

The commercial tier auto-skips when the `chronomemory` source or a license is
unavailable, so the free SQLite tier remains the zero-config default. All
backend dogfooding runs against an isolated copy of `.specsmith/`, so your
working tree is never mutated. See `scripts/dev/README.md` for flags such as
`--full`, `--free-only`, `--editable`, and `--chronomemory-src`.

## Architecture overview
specsmith is a Python CLI governance toolkit built around an AEE-inspired lifecycle. The core flow gates change-oriented work through preflight decisions, tracks intent as work items, verifies outcomes, and audits evidence in a traceable chain. Governance artifacts and machine state are synchronized through project metadata in `.specsmith/` and docs-generated requirement/test files. Integrations with agents and MCP clients layer on top of this governance core rather than bypassing it.

See also:
- `docs/product-principles.md`
- `docs/site/architecture-diagrams.md`
- `docs/site/compatibility.md`

## Good first issues
- Start with docs, tests, or small CLI UX improvements.
- Look for issues labeled `good first issue` or `documentation`.
- Prefer scoped changes that touch one subsystem at a time.

## Pull request checklist
- Branch from `develop` (or the branch requested by maintainers).
- Keep changes scoped and describe user-facing impact clearly.
- Run lint and tests locally.
- Update docs when behavior, commands, or workflows change.
- Link related issues in the PR description.

## Maintainer review expectations
- Reviews evaluate correctness, governance fit, docs quality, and test coverage.
- Contributors should address requested changes or ask clarifying questions.
- Security, compliance, and cross-platform concerns may require deeper review.
- PRs that change workflows should include concrete examples and migration notes where relevant.
