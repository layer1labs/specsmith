# Documentation Update Rule

## When to Check

After making ANY code changes to the specsmith project, always evaluate whether the changes require documentation updates. This check is mandatory before committing.

## What to Update

### Always check these files:

1. **README.md** — Update if:
   - New CLI commands or options added
   - Project types added or modified
   - Feature descriptions change
   - Quick start examples change
   - VCS platform support changes

2. **docs/site/** (Read the Docs pages) — Update if:
   - `docs/site/commands.md` — New commands, options, or behavior changes
   - `docs/site/project-types.md` — New project types or tool changes
   - `docs/site/tool-registry.md` — New tools, languages, or CI metadata
   - `docs/site/importing.md` — Importer detection or overlay changes
   - `docs/site/configuration.md` — New scaffold.yml fields
   - `docs/site/governance.md` — Governance model changes
   - `docs/site/export.md` — Export report changes
   - `docs/site/getting-started.md` — Workflow or install changes
   - `docs/site/contributing.md` — Process or checklist changes
   - `docs/site/index.md` — Feature count or key feature changes

3. **CHANGELOG.md** — Update the `[Unreleased]` section for all notable changes

4. **docs/REQUIREMENTS.md** — Update if new requirements are introduced

5. **docs/TESTS.md** — Update if new test categories are added

## Evaluation Checklist

Before every commit, mentally answer:

- Did I add or change a CLI command? → Update commands.md + README
- Did I add a project type? → Update project-types.md + README + config.py counts
- Did I change the tool registry? → Update tool-registry.md
- Did I change the importer? → Update importing.md
- Did I add a config field? → Update configuration.md
- Did I change governance behavior? → Update governance.md
- Did I add a new feature? → Update CHANGELOG.md [Unreleased]
- Did I change test count? → Update CHANGELOG.md test count

## Release Checks

Before every release:
- Verify `pyproject.toml` classifier matches release status (not "Alpha" for stable releases)
- Verify no stale version references in docs (search for old version strings)
- Verify install commands say `pip install specsmith` (no `--pre` for stable)
- Follow the full checklist in `docs/site/releasing.md`

## Branch Protection

- **NEVER tag a stable release on develop.** Tags must only be created on main.
- **NEVER push tags from develop.** The stable release workflow publishes to PyPI — only main branch releases are allowed.
- All feature work happens on develop. Stable releases merge develop → main first, then tag on main.
- **Dev releases are automatic.** Every push to develop triggers `.devN` pre-release to PyPI.
- Dev releases use `X.Y.(Z+1).devN` version suffix — always the NEXT patch version, not the current.
- Example: if stable is `0.1.3`, dev builds are `0.1.4.dev1`, `0.1.4.dev2`, etc.
- Install dev builds: `pip install --pre specsmith`

## Rule

If any documentation update is needed, make the updates in the SAME commit as the code changes — do not defer documentation to a separate commit.
