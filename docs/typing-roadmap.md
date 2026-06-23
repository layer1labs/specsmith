# Typing Roadmap
Current mypy run:
`python -m mypy src/specsmith --ignore-missing-imports`
Current results:
- 2 errors in 2 files.
- Unused mypy module sections noted in `pyproject.toml`.
Current `# type: ignore` baseline in `src/specsmith/`: 60

## Current violations and carveouts
- module: `src/specsmith/transcripts.py`
  - violation_type: `typeddict-item`
  - owner: `core-governance`
  - reason: `Transcript turn metadata allows nullable/details variants that do not yet align with strict TypedDict contract.`
  - expiration_target: `v0.16`
- module: `src/specsmith/commands/reporting.py`
  - violation_type: `attr-defined`
  - owner: `cli-reporting`
  - reason: `Command-group typing path reaches Click command object that is dynamically populated; static attribute contract needs explicit protocol.`
  - expiration_target: `v0.16`
- module: `src/specsmith/*` (`# type: ignore` carveouts)
  - violation_type: `type-ignore carveout`
  - owner: `module owners`
  - reason: `Mixed dynamic/plugin interfaces, optional commercial backends, and framework-level attributes pending stricter typing wrappers.`
  - expiration_target: `v0.17`
