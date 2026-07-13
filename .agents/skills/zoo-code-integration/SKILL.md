# Zoo Code — Specsmith Governance Integration

Use this skill when working in Zoo Code or Roo Code on a Specsmith-governed repository.

## Goal

Make Zoo/Roo behave like a governed local engineering agent, not an unconstrained chat assistant.

The required pattern is:

```text
Architect plans
Coder edits
Debug/Tool runs and parses commands
Reviewer critiques
Specsmith preflight/verify/trace gates the work
```

The model that writes a patch must not be the only model that approves it.

## Required local project files

Project-local Zoo/Roo integration lives in `.roo/`:

- `.roo/mcp.json` — repo-local MCP server registration for `specsmith-governance`
- `.roo/specsmith-rules.md` — mandatory agent protocol for Zoo/Roo
- `.roo/modes.local.json` — project-local reference mode definitions
- `.roo/global-settings.copy-to-zoo-code.json` — copyable global Zoo Code/OpenAI-compatible provider settings

Only `.roo/mcp.json` and `.roo/specsmith-rules.md` are intended to be active project files. Global provider/model settings must be copied into Zoo Code global settings by the operator.

## Session start

1. Read `AGENTS.md` and `.roo/specsmith-rules.md`.
2. Call the MCP tool `governance_checkpoint`.
3. Call `governance_phase` and `governance_req_list` before changing code.
4. Summarize the current phase, failing checks, relevant requirements, and permitted scope.

## Before any code change

Call `governance_preflight` with one sentence describing the intended change.

Do not edit files unless the decision is `accepted`.

If the decision is `needs_clarification`, ask a narrow question or reduce the change scope.

If the decision is `rejected`, stop and report why.

## During implementation

Follow role separation:

- Architect mode may plan and inspect but should not directly edit production code.
- Code mode may edit only within the accepted preflight scope.
- Debug/Tool mode should run safe commands and parse outputs; it should not make large edits.
- Review mode should read diffs, requirements, and tests; it should not rewrite the patch unless explicitly promoted.

Prefer small diffs. Ground API, register, binding, and build-system claims in actual repository files or command output.

## Verification

After edits:

1. Run the relevant tests/build checks.
2. Capture command output.
3. Run `specsmith verify` or use MCP governance tools when available.
4. Call `governance_trace_seal` for meaningful milestones, accepted reviews, or release gates.

## Portable handoffs

When a session must continue in another agent, export the latest governed
context instead of writing an ungrounded prose summary:

```powershell
specsmith zoo-code export-handoff --project-dir . --output handoff.json
```

The resulting envelope retains source IDs, confidence, and uncertainty. The
receiving agent must verify the cited source IDs before treating an excerpt as
a decision or a fact.

## Embedded/firmware discipline

Never invent SDK, HAL, register, device-tree, or build-system APIs.

For Zephyr/devicetree-style work, ground claims in:

- `bindings/*.yaml`
- board DTS/DTSI files
- generated devicetree output
- exact build errors

For C/firmware work, ground claims in:

- headers
- vendor SDK files
- compiler output
- tests or reproducible logs

## Local model routing

When using a LiteLLM/vLLM local pool, route by task:

| Task | Model role |
|---|---|
| repo planning, architecture, ambiguous debugging | `architect` |
| implementation, tests, refactors | `editor` |
| shell commands, build logs, JSON/YAML, quick summaries | `tool-fast` |
| adversarial review, regression risk, final critique | `reviewer` |

Use the LiteLLM router endpoint when available:

```text
http://localhost:4000/v1
```
