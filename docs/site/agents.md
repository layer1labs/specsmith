# Multi-Agent Profiles & Activity Routing

`specsmith agents` (REQ-146) lets you bind activities — a slash command, an
AEE phase, an MCP tool category — to a named **profile**: a
`(provider, model, endpoint_id?, prompt_prefix, capabilities, fallback_chain)`
bundle. The runner consults the routing table on every turn so a `/plan`
goes to the architect, `/fix` goes to the coder, and `/review` goes to a
reviewer that runs on a *different* model family.

This page walks you from **install → preset → custom profile → per-session
override → BYOE endpoint** in five minutes.

---

## 1. Install a preset

Profiles are stored in `~/.specsmith/agents.json`. The fastest way to seed
the file is to apply one of the four built-in presets:

```bash
specsmith agents preset list
specsmith agents preset apply default          # frontier + local fallback (recommended)
specsmith agents preset apply local-only       # 100% Ollama
specsmith agents preset apply frontier-only    # Claude Opus everywhere
specsmith agents preset apply cost-conscious   # Haiku coder, Sonnet architect
```

After applying:

```bash
specsmith agents list
* coder          role=coder       anthropic/claude-sonnet-4-5
                fallback: mistral/codestral-latest → ollama/qwen2.5-coder:32b
  architect      role=architect   anthropic/claude-opus-4
                fallback: openai/gpt-5 → ollama/qwen2.5:32b
  reviewer       role=reviewer    openai/gpt-5-codex     ← different family!
  …
```

The `*` marks the **default profile**, used when no route matches.

---

## 2. Inspect & customise the routing table

```bash
specsmith agents route show
* chat                 → coder
  /plan                → architect
  /fix                 → coder
  /review              → reviewer
  phase:requirements   → researcher
  …
```

Re-bind any activity:

```bash
specsmith agents route set /review opus-reviewer
specsmith agents route clear /audit
```

The `phase:<key>` routes are auto-maintained: `specsmith phase next` (G3)
also pins a `phase:active` route to the new phase's preferred profile so
the runner can flip the whole session by listening for one activity.

---

## 3. Add your own profile

```bash
specsmith agents add \
  --id sonnet-coder \
  --role coder \
  --provider anthropic \
  --model claude-sonnet-4-5 \
  --capability code \
  --capability function-calling \
  --fallback ollama/qwen2.5-coder:32b
```

If your new coder shares a provider family with the existing reviewer,
the **diversity guard** (G1) prints a warning so the cross-check the
reviewer is supposed to provide doesn't degenerate:

```
✓ saved profile sonnet-coder
⚠ reviewer (reviewer, anthropic/claude-opus-4) shares the 'anthropic'
  family with sonnet-coder (coder, anthropic/claude-sonnet-4-5);
  diversity is recommended so the reviewer can catch the coder's blind spots.
```

The warning is non-fatal — the profile still saves — but you should
either pick a reviewer in a different family or accept the trade-off
deliberately.

### Filter by capability

```bash
specsmith agents list --capability code-review
specsmith agents list --capability mcp --json
```

`--capability` is the easiest way to find every profile that advertises
a given strength so the right `route set` command writes itself.

---

## 4. Per-session overrides

Three knobs override the routing table for one session:

```bash
specsmith run --agent opus-reviewer       # pin a profile
specsmith chat --agent haiku-coder        # one-shot
specsmith run --endpoint home-vllm        # pin a BYOE endpoint
```

Inside a running session, the slash command `/agent <id>` flips the
profile mid-session:

```
nexus> /agent opus-reviewer
ℹ profile = opus-reviewer
```

Pinning a profile via `/agent` writes a **TraceVault decision seal**
(G4) into `.specsmith/trace.jsonl`, so every "I switched to model X for
this turn" choice is cryptographically chained into the audit trail.
You can confirm with `specsmith trace log --type decision`.

### Token accounting (C1)

The runner now reports real `tokens_in` / `tokens_out` for every turn
on every provider that exposes them (Ollama via `prompt_eval_count` +
`eval_count`, Anthropic via `final_message.usage`, OpenAI via
`stream_options.include_usage`, Gemini via `usage_metadata`). When the
SDK omits usage, a 4-chars/token fallback gives the TokenMeter chip a
non-zero value to show. Per-profile totals show up in
`AgentState.by_profile` and the VS Code TokenMeter splits accordingly.

---

## 5. Bring-Your-Own-Endpoint (BYOE)

A **profile** can bind to a registered OpenAI-v1-compatible endpoint
instead of a built-in provider:

```bash
# Register the endpoint once
specsmith endpoints add \
  --id home-vllm \
  --base-url http://10.0.0.4:8000/v1 \
  --default-model qwen2.5-coder \
  --auth bearer-keyring          # token prompted, stored in OS keyring

# Bind a profile to it
specsmith agents add \
  --id local-coder \
  --role coder \
  --provider openai-compat \
  --endpoint home-vllm \
  --fallback ollama/qwen2.5-coder:7b

specsmith agents route set /code local-coder
```

The runner now routes `/code` through `home-vllm`. If the box is
unreachable, the fallback chain walks `ollama/qwen2.5-coder:7b` next
(see `tests/test_fallback_chain.py` for the full retry policy: 408,
429, and 5xx fall through, 4xx surfaces immediately).

---

## Reference

- [REQ-146 — Agent profiles + activity routing](../REQUIREMENTS.md)
- [`specsmith.agent.profiles`](../../src/specsmith/agent/profiles.py) — `Profile`, `ProfileStore`, `apply_preset`, `provider_family`
- [`specsmith.agent.fallback`](../../src/specsmith/agent/fallback.py) — `run_with_fallback`, `parse_target`
- [`docs/site/api-stability.md`](api-stability.md) — public surface contract
