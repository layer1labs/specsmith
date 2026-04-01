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

5. **docs/TEST_SPEC.md** — Update if new test categories are added

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

## Rule

If any documentation update is needed, make the updates in the SAME commit as the code changes — do not defer documentation to a separate commit.
