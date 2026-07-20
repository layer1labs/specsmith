# API stability (pre-1.0)

Specsmith is a pre-1.0 project. Intentional breaking changes use a minor release
and are called out in the changelog; compatible fixes use a patch release.

## Stable contracts

The following contracts are stable in spirit and require explicit migration
notes when changed:

- `preflight` JSON fields and decision exit codes;
- `verify` JSON fields, equilibrium result, and retry/stop exit codes;
- requirement and linked-test IDs in canonical YAML;
- work-item lifecycle states and project-scoped identity;
- governance checkpoints, ledger event provenance, and ESDB integrity;
- Grace block events consumed by supported integrations.

## Focused CLI contract

Normal help exposes the mission-essential workflow:

```text
init  import  run  preflight  verify  req  test  audit  checkpoint
status  sync  save  integrate  doctor  kill-session  commands
```

`specsmith commands` lists the supporting governance, context, provider, MCP,
policy, ESDB, integration, and validation commands. Git hosting, deployment,
browsers, generic multi-agent orchestration, model leaderboards, dashboards,
voice, patent search, wireframes, and workspaces are not public CLI contracts.

## API-surface snapshot

`specsmith api-surface` emits the machine-readable command, exit-code, and event
surface used by CI. The canonical fixture is
`tests/fixtures/api_surface.json`. Any intentional change must update the fixture,
focused CLI tests, documentation, and changelog in the same reviewed change.

Removing or renaming a root command is breaking. Adding a supporting command or
an additive event field is normally compatible, provided existing consumers can
ignore it.

## Internal interfaces

Modules under `src/specsmith/agent/`, local cache layout, provider adapters, and
prompt wording may evolve before 1.0. They must not weaken deterministic
preflight, verification, provenance, or user-configuration preservation.

## Versioning policy

- `0.MINOR.0` may contain clearly documented intentional breaking changes.
- `0.MINOR.PATCH` contains compatible fixes and maintenance.
- Published tags and package versions are immutable.
- Release candidates must pass the fixed-point repository workflow before a tag
  is created.
