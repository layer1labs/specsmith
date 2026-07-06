# Standalone CLI

Use specsmith entirely from the terminal — no IDE, no AI agent client required.
The governance CLI, Nexus REPL, and multi-agent dispatcher all work standalone with just `pipx install specsmith`.

---

## When to use the standalone CLI

| Situation | Recommendation |
|---|---|
| CI pipelines and automation | Standalone CLI — no agent session needed |
| Terminal-first workflows (no IDE) | Standalone CLI + `specsmith run` REPL |
| Governance checks on a headless server | Standalone CLI |
| You use Warp, Cursor, Claude Code, etc. | [Agent Integrations](agent-integrations.md) instead |
| You want governance + an LLM in one command | `specsmith run` (Nexus REPL) |
| Larger projects with token cost concerns | Governance reduces token costs by 2-6x compared to ungoverned approaches |
| Local LLMs (LMStudio, vLLM, llama.cpp) | Bring your own endpoint support for maximum cost control and privacy |
| You want to use LMStudio or other local LLM tools | Native support for Bring-Your-Own-Endpoint (BYOE) workflows |

---

## Session workflow

The same governance protocol applies whether you are an AI agent or a human at a terminal.

### Session start

Run once at the beginning of every work session:

```bash
specsmith kill-session 2>/dev/null || true   # kill any orphaned processes
specsmith migrate run                         # apply pending schema migrations
specsmith audit --project-dir .              # verify governance health
specsmith sync  --project-dir .              # YAML → JSON → MD sync
specsmith checkpoint --project-dir .         # emit GOVERNANCE ANCHOR
```

The `specsmith checkpoint` output is your session anchor — keep it visible.
If you lose track of the current phase or active work items, re-run it.

### Before every code change

```bash
specsmith preflight "<describe the change>" --json
```

- `decision == "accepted"` → proceed; note the `work_item_id`
- `decision == "needs_clarification"` → read the `instruction` field and refine your intent

Never make a code change without an accepted preflight. The work item ID links the change to governance.

### During work

```bash
specsmith wi list --status open       # see all open work items
specsmith wi show WI-XXXXXXXX         # inspect a specific work item
specsmith phase                       # check current AEE phase + readiness %
specsmith audit --project-dir .       # re-check governance health at any time
```

### After making changes

```bash
specsmith verify                      # check requirement equilibrium
specsmith checkpoint --project-dir .  # emit heartbeat anchor (every 8–10 significant changes)
```

### Session end

```bash
specsmith save            # ESDB backup + commit + push
specsmith kill-session    # stop governance-serve and tracked processes
```

Never end a session with uncommitted governance changes.

---

## Nexus REPL — governance-gated LLM terminal

`specsmith run` starts the Nexus REPL: a local-first agentic terminal where every utterance
is preflighted before execution.

```bash
# Start with a local Ollama model (no API key needed)
specsmith run --provider ollama --model qwen2.5:14b

# Start with a cloud provider
specsmith run --provider anthropic   # requires ANTHROPIC_API_KEY
specsmith run --provider openai      # requires OPENAI_API_KEY
specsmith run --provider google      # requires GOOGLE_API_KEY

# Start with a local LLM via BYOE (Bring Your Own Endpoint)
specsmith run --provider local --endpoint http://localhost:1234/v1/chat/completions
```

Inside the REPL:

```
nexus> fix the cleanup dry-run regression    # change → preflighted → executed → verified
nexus> what does the audit module do?         # read-only → answered directly
nexus> delete the dist directory              # destructive → needs_clarification returned
nexus> /why                                   # show governance trace for last action
nexus> /exit
```

### Inject LLM SDKs into the pipx environment

If you installed via pipx, inject the provider SDK only for cloud LLM use:

```bash
pipx inject specsmith anthropic     # for ANTHROPIC_API_KEY
pipx inject specsmith openai        # for OPENAI_API_KEY
pipx inject specsmith google-genai  # for GOOGLE_API_KEY
```

Ollama requires no injection — specsmith uses stdlib HTTP.

### VRAM-aware model selection (local models)

```bash
specsmith ollama gpu                   # detect GPU VRAM tier
specsmith ollama available             # list models that fit your VRAM budget
specsmith local-model recommend        # per-role lineup with fits/tight/spills assessment
specsmith local-model setup            # download the best hardware-appropriate model
```

---

## Multi-agent dispatcher

Decompose a task into a DAG of agent work items and run them concurrently:

```bash
specsmith dispatch run "add API endpoint with tests" --max-workers 4
specsmith dispatch run "refactor auth module" --json   # stream JSONL events
specsmith dispatch status --dag-id <id>                # check run status
specsmith dispatch list                                 # list all runs
specsmith dispatch retry --node impl --dag-id <id>     # retry a failed node
```

Combine with governance: `specsmith preflight` the top-level task before dispatching,
and the dispatcher propagates the work item context to each node automatically.

---

## Key commands at a glance

```bash
# Governance
specsmith audit                       # full health check (48+ checks)
specsmith validate --strict           # schema: dup IDs, orphans, coverage gaps
specsmith preflight "<intent>" --json # gate a change
specsmith checkpoint                  # emit GOVERNANCE ANCHOR
specsmith sync                        # YAML → JSON → MD
specsmith save                        # ESDB backup + commit + push
specsmith export --format markdown    # compliance report

# Phase management
specsmith phase                       # current phase + readiness %
specsmith phase next                  # advance to next phase
specsmith phase list                  # all 7 phases

# Work items
specsmith wi list --status open
specsmith wi show WI-XXXXXXXX
specsmith wi close WI-XXXXXXXX --reason "covered by REQ-042"
specsmith wi promote WI-XXXXXXXX --title "..." --domain governance

# Requirements
specsmith req list
specsmith req gaps                    # uncovered requirements
specsmith stress-test                 # adversarial AEE challenges on all REQs
specsmith epistemic-audit             # certainty scores + logic knot detection

# Session
specsmith kill-session
specsmith migrate run
specsmith doctor                      # tool availability check
```

---

## CI usage

The standalone CLI is designed for headless CI. All commands exit with code 0 on success, non-zero on failure.

```yaml
# GitHub Actions example
- name: Governance health check
  run: |
    pipx install specsmith
    specsmith migrate run
    specsmith audit --project-dir .
    specsmith sync --check             # exits 1 if YAML cache is out of sync
    specsmith validate --strict
```

The `specsmith audit` step is a complete governance gate — it checks file existence, YAML validity,
requirement coverage, WI gate satisfaction, and ESDB chain integrity.

---

## Next steps

- [Agent Integrations](agent-integrations.md) — add an AI agent client (Warp, Claude Code, Cursor, etc.)
- [Warp Integration](warp-integration.md) — native MCP server + Ctrl+Shift+R workflows
- [CLI Commands](commands.md) — full command reference
- [Getting Started](getting-started.md) — new project or import an existing one
