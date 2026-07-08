# Specsmith Rules for Zoo Code / Roo Code

This repository uses Specsmith governance. Follow these rules for all agentic work in Zoo Code or Roo Code.

## Mandatory protocol

1. Read `AGENTS.md` and this file before changing code.
2. Use the `specsmith-governance` MCP server from `.roo/mcp.json`.
3. Call `governance_checkpoint` at session start and every 8-10 turns.
4. Call `governance_preflight` before any code edit.
5. Do not edit files unless preflight returns `accepted`.
6. Run tests/build checks after edits.
7. Run verification before reporting success.
8. Seal meaningful decisions with `governance_trace_seal`.

## Role separation

Use separate modes/models for separate jobs:

| Work | Preferred mode | Preferred local model role |
|---|---|---|
| requirements, architecture, plans | Architect | `architect` |
| implementation and tests | Code | `editor` |
| command generation and log parsing | Debug / Tool | `tool-fast` |
| adversarial diff review | Review | `reviewer` |

The model that writes a patch must not be the only model that approves it.

## Scope control

Keep changes inside the accepted preflight scope.

Do not perform these actions unless the user explicitly asks and preflight accepts:

- dependency upgrades
- public API changes
- file tree deletions
- generated code rewrites over 200 lines
- git push or release actions
- secret, credential, or `.env` edits

## Grounding rules

Do not invent APIs, flags, registers, CLI options, package names, or configuration keys.

Ground technical claims in one of:

- repository files
- generated outputs
- test/build logs
- official vendor/project docs already present in the workspace

For firmware, Zephyr, RTL, FPGA, or low-level systems work, cite exact headers, bindings, source files, generated files, or build output before editing.

## Completion report

Every completed task should report:

- accepted preflight work item id, when available
- files changed
- tests/builds run
- reviewer findings
- remaining risks
- follow-up work, if any
