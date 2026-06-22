# Public 1.0 Stability Contract

This document defines what SpecSmith treats as public and how compatibility is managed for the 1.0 line.

## Stability levels

### Stable
- Backward compatible within 1.x except for explicitly announced deprecations.
- Changes require migration notes before release.
- Covered by regression tests and release checklist.

### Beta
- Public and documented, but may change with minor-version migrations.
- Changes require release-note callouts.
- Intended for active feedback before promotion to Stable.

### Experimental
- May change or be removed at any time.
- No compatibility guarantees.
- Not suitable for production compliance baselines.

### Internal
- Not part of the public contract.
- Any change is allowed without migration support.

## Public CLI command stability

The command surface below is the 1.0 contract baseline.

### Stable CLI commands (core governance and lifecycle)
- `specsmith init`
- `specsmith import`
- `specsmith sync`
- `specsmith validate`
- `specsmith audit`
- `specsmith checkpoint`
- `specsmith preflight`
- `specsmith verify`
- `specsmith save`
- `specsmith kill-session`
- `specsmith phase` (`show`, `list`, `next`, `set`)
- `specsmith wi` (`list`, `show`, `close`, `archive`, `promote`, `tag`)
- `specsmith req` (`list`, `trace`, `gaps`, `add`)
- `specsmith export`
- `specsmith trace` (`seal`, `verify`, `log`)
- `specsmith esdb` (`status`, `export`, `import`, `backup`)
- `specsmith mcp serve`

### Beta CLI commands (public, evolving)
- `specsmith dispatch` (`run`, `status`, `list`, `retry`)
- `specsmith model-intel` (`sync`, `scores`, `recommendations`, `connection`)
- `specsmith agent` (`run`, `plan`, `verify`, `improve`, `reports`, `ask`)
- `specsmith mcp generate`
- `specsmith channel` (`set`, `get`)
- `specsmith skills` (`deactivate`, `delete`)
- `specsmith ollama` (`gpu`, `available`, `suggest`, `pull`, `list`)
- `specsmith endpoints` (`add`, related endpoint management)

### Experimental CLI commands
- Any command explicitly documented as experimental in command help or release notes.
- New command groups introduced without inclusion in this document.

### Internal CLI
- Hidden/dev/test-only subcommands.
- Internal maintenance commands used by test harnesses.

## Generated file format stability

### Stable
- `docs/REQUIREMENTS.md` generated structure and identifiers.
- `docs/TESTS.md` generated structure and requirement references.
- `.specsmith/workitems.json` core schema (`id`, `state`, `kind`, `requirement_ids`, timestamps).
- `.specsmith/trace.jsonl` append-only hash-chain event envelope (`seq`, `type`, `hash`, `prev`).
- `.specsmith/ledger.jsonl` append-only event log envelope.

### Beta
- Generated compliance export report shape (`specsmith export`) for advanced sections.
- Dispatch run artifacts under `.specsmith/dispatch/<dag_id>/`.
- Extended model-intelligence cache files and recommendation metadata.

### Experimental
- Any newly added generated report marked as experimental in docs.

### Internal
- Temporary files, cache internals, and migration scratch files.

## MCP tool schema stability

### Stable tool schemas
- `governance_audit`
- `governance_checkpoint`
- `governance_preflight`
- `governance_phase`
- `governance_req_list`
- `governance_trace_seal`

Stable guarantee includes tool names, top-level request/response fields, and decision enum semantics.

### Beta MCP schemas
- Newly introduced MCP tools not listed above.
- Optional metadata extensions that may graduate to Stable.

### Experimental/Internal MCP schemas
- Debug or test-only MCP endpoints.
- Internal fields not documented in public MCP docs.

## ESDB schema stability

### Stable
- Core SQLite ESDB entities required for requirements, tests, work items, and audit linkage.
- ChronoStore WAL hash-chain invariants.
- Snapshot compatibility for same-major-version restore.

### Beta
- OEA extension fields and advanced anti-hallucination metadata.
- Performance/acceleration metadata from Rust fast paths.

### Experimental/Internal
- Storage-engine internals and private optimization tables.

## Python public API stability

### Stable APIs
- `epistemic.AEESession`
- `epistemic.BeliefArtifact`
- `epistemic.StressTester`
- `epistemic.CertaintyEngine`
- `specsmith.esdb.SqliteStore`

### Beta APIs
- `specsmith.agent.orchestrator.Orchestrator`
- `specsmith.agent.model_profiles.get_profile`
- `specsmith.agent.model_profiles.trim_history`
- `specsmith.agent.llm_client.LLMClient`

### Experimental/Internal APIs
- Modules under `specsmith.agent.*` not explicitly listed as Stable or Beta.
- Private helpers and underscore-prefixed functions.

## Deprecation policy

- Stable surfaces must be deprecated for at least one minor release before removal.
- Every deprecation must include:
  - first release where deprecation appears
  - removal target release
  - migration path
- Deprecated commands and APIs emit warnings where possible.

## Migration policy

- Any Stable breaking change requires:
  - migration guide section in release notes
  - deterministic migration steps or automated migration command
  - backward-compatibility tests for prior minor baseline
- Schema migration behavior must be documented before release.
- Automated schema-version-field checks are tracked in #218.

## Changelog rules for breaking changes

- Breaking changes must be grouped under a dedicated `Breaking Changes` heading.
- Each entry must list:
  - impacted surface (CLI, file format, MCP schema, ESDB, Python API)
  - old behavior
  - new behavior
  - migration steps
  - deprecation/removal timeline
- Patch releases must not introduce breaking changes to Stable surfaces.

