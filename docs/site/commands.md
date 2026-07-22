# CLI commands

Specsmith's public CLI is deliberately small. Normal help shows the core change
loop; `specsmith commands` lists every supported command. Git, framework tests,
browsers, deployment, and generic agent skills stay with the host tool.

## Core workflow

| Command | Purpose |
|---|---|
| `init` | Start a new governed repository. |
| `import` | Add the governance overlay to an existing repository. |
| `req` | Add, list, and trace requirements. |
| `test` | Add test cases linked to requirements. |
| `preflight` | Decide whether an intended change is sufficiently scoped and safe. |
| `verify` | Evaluate diff/test/log evidence for a change. |
| `audit` | Check governance health and requirement/test coverage. |
| `checkpoint` | Emit a compact governance anchor for context continuity. |
| `status` | Show repository and governance status. |
| `sync` | Rebuild derived machine state from canonical YAML/Markdown. |
| `save` | Back up governance state and close its repository transaction. |
| `integrate` | Generate a focused adapter for a supported host tool. |
| `run` | Start Grace, the optional local fallback REPL. |
| `doctor` | Diagnose the local installation and provider setup. |
| `kill-session` | Stop tracked Specsmith session processes. |

## First governed change

```bash
specsmith import --project-dir . --yes
specsmith req add --title "Return a stable error envelope"
specsmith test add --req REQ-001 --title "Verify the error envelope" --type integration
specsmith preflight "Implement the error envelope. Scope: REQ-001" --json
# Edit with your normal coding agent and run the native tests.
specsmith audit --project-dir .
specsmith checkpoint --project-dir .
```

To correlate project health with post-run GovernanceBench weaknesses and write
one machine-readable report:

```bash
specsmith audit --project-dir . \
  --benchmark-results bench-results.json \
  --report benchmark-project-audit.json
```

High or critical benchmark weaknesses produce a non-zero exit. See
[Long-Horizon Benchmark and Weakness Audit](benchmark-audit.md).

## Preflight

```bash
specsmith preflight "Fix the parser. Scope: REQ-042" --json
```

Accepted output includes `work_item_id`, `requirement_ids`, `test_case_ids`, and
`confidence_target`. `needs_clarification` exits 2 and supplies a concrete
instruction. Destructive or unsupported work must not proceed until the scope is
explicit.

## Verification

`verify` consumes observed evidence rather than guessing whether work passed:

```bash
echo '{"diff":"...","files_changed":["src/parser.py"],"test_results":{"passed":8,"failed":0}}' |
  specsmith verify --stdin --work-item-id WI-123
```

Exit 0 means equilibrium; exit 2 recommends a bounded retry; exit 3 means stop
and align. `audit` remains the simpler whole-project health gate.

## Requirements and tests

```bash
specsmith req list
specsmith req add --title "Observable behavior" --status planned
specsmith test add --req REQ-001 --title "Prove the behavior" --type unit
specsmith req trace
```

A test without a requirement is an orphan. A requirement without a linked test
is a gap. Both are visible in audit output.

## Context and evidence

```bash
specsmith checkpoint --project-dir .
specsmith inspect --project-dir . --json
specsmith compress --project-dir .
specsmith esdb status
```

`checkpoint` is the normal agent handoff. `compress` bounds old ledger context;
ESDB retains confidence and provenance so compression cannot promote an
unsupported statement into a fact.

## Grace and providers

```bash
specsmith run
specsmith local-model recommend
specsmith providers --help
specsmith endpoints --help
specsmith auth --help
```

Grace supports `/help`, `/status`, `/why`, and `/specsmith ...`. Provider errors
include recovery guidance. Use Grace only when a local or standalone fallback is
useful; otherwise integrate the coding agent you already use.

## Integrations

```bash
specsmith integrate <tool> --project-dir .
specsmith mcp --help
specsmith zoo-code --help
specsmith skill list
```

The skill catalog contains only focused Specsmith governance integrations.
Generic Git, browser, test, cloud, and framework skills belong to the host.

## Supporting commands

The retained supporting surface is:

```text
approve  auth  compress  config  context  endpoints  esdb  inspect  load
local-model  mcp  policy  providers  serve  skill  update  validate
wi  zoo-code
```

Use `specsmith COMMAND --help` for exact options. Commands from older releases
that duplicated Git clients, orchestration frameworks, model leaderboards,
dashboards, patent tools, voice tools, wireframes, workspaces, or host-agent
skills are no longer part of the public CLI.
