# Specsmith

**Lean Applied Epistemic Engineering governance for AI-assisted development.**

> Intelligence proposes. Constraints decide. The ledger remembers.

Specsmith sits around the coding agent and tools you already use. It keeps
requirements durable, links them to enforceable tests, bounds epistemic context,
and records evidence so a plausible model answer cannot silently become a fact.

## The essential loop

```text
requirement -> linked test -> preflight -> native implementation
            -> observed validation -> verification -> checkpoint
```

The host agent owns code editing, Git, browsers, deployment, and framework
skills. Specsmith owns scope, test traceability, uncertainty, confidence gates,
and durable evidence.

## Quick start

```bash
pipx install specsmith
cd your-project
specsmith import --project-dir .
specsmith audit --project-dir .
specsmith preflight "Fix the pagination boundary. Scope: REQ-123" --json
# Edit and test with your normal tools.
specsmith verify --project-dir .
specsmith checkpoint --project-dir .
```

Generate a focused host integration with `specsmith integrate`, or start Grace
with `specsmith run` when a terminal/local-model fallback is useful.

## Core capabilities

- durable requirements with explicit epistemic boundaries;
- tests linked to accepted requirements;
- deterministic mutation, destructive-operation, and release gates;
- compact context that preserves knowns, unknowns, and provenance;
- bounded verification based on observed diffs and test results;
- SQLite evidence storage with an optional ChronoMemory backend;
- MCP and focused integrations for common coding agents;
- safe repair of older Specsmith-managed Zoo/Roo Code configuration;
- equivalent behavior on Windows, Linux, and macOS.

## Grace

Grace is the friendly optional REPL, not a separate orchestration layer. It uses
the same preflight, context, verification, and evidence paths as every external
integration. `/help`, `/status`, `/why`, provider switching, and actionable error
guidance make the first local session straightforward.

## Governance efficiency evidence

The published benchmark reports task-dependent results rather than a universal
claim. Current evidence identifies where lightweight governance helps, where it
adds token cost, and which paths need improvement. See the
[governance efficiency report](efficiency-benchmark.md) and
[model comparison](model-comparison.md).

## Documentation

- [Getting started](getting-started.md)
- [Quick start](quickstart.md)
- [CLI commands](commands.md)
- [Agent integrations](agent-integrations.md)
- [Grace](standalone-cli.md)
- [Governance model](governance.md)
- [API stability](api-stability.md)
- [ESDB](esdb.md)
- [Release process](releasing.md)
