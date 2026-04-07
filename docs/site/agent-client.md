# Agentic Client

`specsmith run` starts an AEE-integrated agentic REPL that wraps any LLM provider,
exposes specsmith commands as native tools, loads skills from the project, and enforces
epistemic governance (H13) through the hook system.

## Installation

```bash
pip install specsmith[anthropic]   # Claude (claude-sonnet-4-5 etc.)
pip install specsmith[openai]      # GPT-4o, O-series + any OpenAI-compat
pip install specsmith[gemini]      # Gemini 2.5 Pro/Flash
# Ollama: install locally from https://ollama.ai — no pip extra needed
```

## Quick Start

```bash
# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...  # or OPENAI_API_KEY, GOOGLE_API_KEY

# Start interactive REPL (auto-detects provider)
specsmith run

# Run a single task non-interactively
specsmith run --task "run audit and fix any issues"

# Use a specific provider/model
specsmith run --provider anthropic --model claude-opus-4-5 --tier powerful

# Use local Ollama (no API key needed)
specsmith run --provider ollama --model qwen2.5:14b
```

## Provider Auto-Detection

The client detects your provider from environment variables in priority order:

| Variable | Provider |
|----------|----------|
| `SPECSMITH_PROVIDER=anthropic` | Override (explicit) |
| `ANTHROPIC_API_KEY` | Anthropic Claude |
| `OPENAI_API_KEY` | OpenAI GPT/O-series |
| `GOOGLE_API_KEY` | Google Gemini |
| Ollama at localhost:11434 | Local Ollama |

## Model Tiers

Use `--tier` to select models by capability:

| Tier | Anthropic | OpenAI | Gemini | Ollama |
|------|-----------|--------|--------|--------|
| `fast` | claude-haiku-4-5 | gpt-4o-mini | gemini-2.5-flash | llama3.2:latest |
| `balanced` (default) | claude-sonnet-4-6 | gpt-4o | gemini-2.5-flash | qwen3:14b |
| `powerful` | claude-opus-4-6 | o4-mini | gemini-3.1-pro-preview | qwen3:32b |

!!! note "Gemini 2.0 Flash deprecation"
    `gemini-2.0-flash` is being **shut down June 1, 2026**. Migrate to `gemini-2.5-flash` or `gemini-3-flash-preview`.

!!! note "OpenAI o-series"
    o-series models (o1, o3, o4-mini) use `developer` role instead of `system` role for instructions.
    specsmith handles this automatically.

From ECC's guidance: use `fast` for routine tasks (ledger entries, doc updates), `balanced` for most coding, `powerful` for architecture decisions and Logic Knot resolution.

## REPL Commands

Once in the REPL, use these slash commands:

```
/help           — show all commands
/tools          — list available tools with descriptions
/skills         — list loaded skills
/skill <name>   — inject a skill into context
/model <name>   — switch model mid-session
/status         — session tokens, cost, elapsed time
/hooks          — list active hooks
/clear          — clear conversation history (keeps system prompt)
/save           — write LEDGER.md entry for this session
exit            — end session (triggers session-end hooks)
```

Quick commands (just type the word):

```
start      — sync + update check + load AGENTS.md + LEDGER.md
resume     — load last LEDGER.md entry and propose next task
save       — write ledger entry
audit      — run specsmith audit --fix
commit     — run specsmith commit
push       — run specsmith push
sync       — run specsmith sync
epistemic  — run full epistemic audit
stress     — run stress-test on requirements
status     — session status
```

## Available Tools

The agent has 20+ tools registered, grouped by category:

**Governance:** `audit`, `validate`, `diff`, `export`, `doctor`, `epistemic_audit`, `stress_test`, `belief_graph`

**VCS:** `commit`, `push`, `sync`, `create_pr`, `create_branch`

**Ledger:** `ledger_add`, `ledger_list`

**Trace:** `trace_seal`, `trace_verify`

**Requirements:** `req_list`, `req_gaps`, `req_trace`

**Utility:** `read_file`, `session_end`

Each tool has an **epistemic contract** — a declaration of what it claims to know and what it cannot detect. This is used by the H13 hook to warn when tools are called in epistemically risky contexts.

## Skills System

The agent automatically loads SKILL.md files from (priority order):

1. `.warp/skills/` — Warp/Oz native skills
2. `.claude/skills/` — Claude Code skills
3. `.agents/skills/` — Generic agent skills
4. `src/specsmith/agent/profiles/` — Built-in specsmith profiles

Built-in profiles:
- **epistemic-auditor** — Full AEE audit protocol with seal and ledger recording
- **verifier** — 5-gate verification loop (audit, validate, doctor, coverage, epistemic)
- **planner** — AEE-governed proposal template with H13 enforcement

Load a skill mid-session: `/skill epistemic-auditor`

## Hook System

Hooks fire automatically at lifecycle events:

| Hook | Trigger | What it does |
|------|---------|-------------|
| H13 check | Before AEE tools | Warns if P1 requirements are at LOW confidence |
| Ledger hint | After commit/push/trace | Reminds to add LEDGER.md entry |
| Context budget | Every turn | Warns at ~160k tokens, suggests /save + fresh session |
| Session start | On session begin | Reminds to run sync, load AGENTS.md |

## Inspect Configuration

```bash
specsmith agent providers    # check LLM provider status
specsmith agent tools        # list all 20+ tools
specsmith agent skills       # list loaded skills
```
