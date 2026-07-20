# Quick Start

Specsmith is the requirements, test, and evidence layer around your preferred AI
tool. Choose one path: integrate an agent you already use, or start **Grace**, the
optional local REPL.

## 1. Install and adopt a project

```bash
pipx install specsmith
cd your-project
specsmith import --project-dir .   # use `specsmith init` for a new project
specsmith audit --project-dir .
```

If the audit reports a repairable old configuration, run:

```bash
specsmith sync --project-dir .
specsmith audit --project-dir .
```

## 2A. Use an existing agent (recommended)

Generate the host's native rules or MCP configuration:

```bash
specsmith integrate claude-code   # or cursor, copilot, gemini, aider, warp, windsurf
specsmith mcp serve --project-dir .
```

Restart the host agent so it discovers the generated integration. The agent keeps
its own code, Git, test, browser, and framework tools. Specsmith adds only the AEE
contract: scoped requirements, linked tests, uncertainty, and verification evidence.

For Zoo Code / Roo Code, use:

```bash
specsmith zoo-code setup --project-dir .
specsmith zoo-code doctor --project-dir .
```

The setup flow safely repairs malformed or obsolete Specsmith-managed assets while
preserving user-owned settings and secrets.

## 2B. Use Grace, the local fallback REPL

Grace is useful when you want a terminal-only workflow or a private local model.

```bash
ollama serve
specsmith run --provider ollama
```

Inside Grace:

```text
grace> /help
grace> /status
grace> explain the current requirements and missing tests
grace> /fix repair the pagination boundary bug
grace> /why
grace> /exit
```

Use `/models`, `/model NAME`, or `/provider NAME` to change the active model. Grace
compresses older epistemic context before it enters the model token path and reports
whether compression occurred in `/status`.

If no provider is available, start Ollama or configure one cloud provider:

```bash
pipx inject specsmith openai       # then set OPENAI_API_KEY
pipx inject specsmith anthropic    # then set ANTHROPIC_API_KEY
pipx inject specsmith google-genai # then set GOOGLE_API_KEY
```

## 3. Complete one governed change

Whether a host agent or Grace performs the work, the essential loop is the same:

```bash
specsmith preflight "fix pagination boundary behavior; scope REQ-123" --json
# Make the accepted change with your native agent and run its normal tests.
specsmith verify --project-dir .
specsmith checkpoint --project-dir .
```

- `accepted`: implement only the linked scope.
- `needs_clarification`: answer the instruction; do not bypass it.
- destructive or ambiguous work stops before mutation.
- completion requires passing relevant tests and durable evidence.

That is the bare AEE kernel. Audit, release, and compliance controls remain
available, but they should not occupy model context unless the task or risk calls for
them.

## Next steps

- [Agent integrations](agent-integrations.md)
- [Grace and the standalone CLI](standalone-cli.md)
- [Zoo Code / Roo Code](zoo-code-roo.md)
- [Focused skills](skills-index.md)
- [Invocation strategy](invocation-strategy.md)
