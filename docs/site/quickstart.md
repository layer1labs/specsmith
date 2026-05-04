# Five-Minute Quickstart
This page is the **reproducible** version of the README's elevator pitch:
copy the commands top-to-bottom and you'll end up with a fresh project,
a multi-agent profile set, a routed `/plan` → architect → coder pipeline,
and a TraceVault sealed audit chain you can verify after the fact.

> **GIF placeholder.** A 30-second screen recording showing the same
> commands running end-to-end will live at
> `docs/site/_static/quickstart.gif`. Until that lands, the script in
> [scripts/quickstart.sh](#reproduction-script) is the source of truth.

---

## Prerequisites
- Python 3.10+ (`pipx install specsmith` or `pip install specsmith`)
- One LLM provider configured (any of):
  - `ANTHROPIC_API_KEY=sk-…` for Claude
  - `OPENAI_API_KEY=sk-…` for GPT/O-series
  - `GOOGLE_API_KEY=…` for Gemini
  - Ollama running locally (`ollama serve`) — no key needed

The reproduction script intentionally has *no* timing-sensitive steps so
it's safe to run unattended in CI.

---

## Reproduction script
```bash
#!/usr/bin/env bash
# scripts/quickstart.sh — five-minute walkthrough, idempotent.
set -euo pipefail
export SPECSMITH_NO_AUTO_UPDATE=1
export SPECSMITH_PYPI_CHECKED=1

# 1. Scaffold a fresh project.
specsmith init --output-dir /tmp \
  --config <(cat <<'YAML'
name: quickstart-demo
type: cli-python
language: python
description: "specsmith multi-agent quickstart demo"
YAML
)
cd /tmp/quickstart-demo

# 2. Install the recommended profile preset.
specsmith agents preset apply default
specsmith agents list
specsmith agents route show

# 3. Add a custom local-coder profile (diversity guard fires).
specsmith agents add \
  --id local-coder \
  --role coder \
  --provider ollama \
  --model qwen2.5-coder:32b \
  --capability code \
  --fallback ollama/qwen2.5-coder:7b

# 4. Filter by capability — handy for finding "what can do X".
specsmith agents list --capability code --json

# 5. Optional: register a self-hosted endpoint (BYOE).
# specsmith endpoints add \
#   --id home-vllm \
#   --base-url http://10.0.0.4:8000/v1 \
#   --default-model qwen2.5-coder \
#   --auth bearer-keyring

# 6. Drive a single turn through the routing table.
echo "/plan add a hello-world handler" | \
  specsmith run --json-events --task "/plan add a hello-world handler"

# 7. Pin a profile mid-session — emits a TraceVault decision seal.
echo "/agent opus-reviewer" | specsmith run --json-events
specsmith trace log --type decision

# 8. Advance the AEE phase — auto-routes phase:active to the new phase.
specsmith phase next --force
specsmith agents route show | grep phase:active
```

Save the script anywhere on your machine and run it; the only side
effects are inside `/tmp/quickstart-demo`, `~/.specsmith/agents.json`,
and (if you uncomment step 5) `~/.specsmith/endpoints.json`.

---

## What you should see
| Step | Expected output                                                                 |
|------|---------------------------------------------------------------------------------|
| 1    | `Done. N files created in /tmp/quickstart-demo`                                 |
| 2    | `✓ applied preset default — 7 profiles, 22 routes`                              |
| 3    | `✓ saved profile local-coder` *plus* a yellow `⚠ … shares the 'ollama' family…` diversity warning if a same-family reviewer exists. |
| 4    | A JSON document with one entry whose `id` is `local-coder`.                     |
| 6    | A JSONL stream beginning with `{"type": "ready", …}` followed by `block_start`, `token`, `block_complete`, `task_complete`. |
| 7    | `✓ Sealed as SEAL-0001` (or whichever sequence number is next).                |
| 8    | A `phase:active` line in the routing table pointing at the new phase's profile. |

If any step fails, run `specsmith doctor --onboarding` to surface what's
missing and re-run from that step.

---

## Next steps
- [`docs/site/agents.md`](agents.md) — the full multi-agent walkthrough
- [`docs/site/api-stability.md`](api-stability.md) — the public surface contract
- [`docs/site/vscode-extension.md`](vscode-extension.md) — VS Code Workbench surfaces
