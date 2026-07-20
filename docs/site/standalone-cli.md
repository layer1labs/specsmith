# Standalone CLI and Grace

Use the standalone CLI when an editor integration is unavailable, a local model
is preferred, or CI needs deterministic governance commands. If a coding agent
already provides Git, browser, test, and framework tools, keep using them.

## Install

```bash
pipx install specsmith
specsmith doctor --onboarding
```

`pipx` keeps the executable isolated. Library imports work from a normal
`pip install specsmith` environment.

## Choose a path

| Need | Start here |
|---|---|
| Add governance to an existing repository | `specsmith import --project-dir . --yes` |
| Create a new repository | `specsmith init` |
| Use an existing coding agent | `specsmith integrate <tool>` |
| Run locally without another agent | `specsmith run` |
| Expose governance over MCP/HTTP | `specsmith mcp --help` or `specsmith serve` |

## First change

```bash
specsmith req add --title "Describe an observable behavior"
specsmith test add --req REQ-001 --title "Prove the behavior" --type unit
specsmith preflight "Implement the behavior. Scope: REQ-001" --json
```

Run the repository's native formatter and tests after editing, then:

```bash
specsmith audit --project-dir .
specsmith checkpoint --project-dir .
```

## Grace

```bash
specsmith run
```

Grace starts with a compact project summary and explains provider recovery if no
model is reachable.

```text
grace> /help
grace> /status
grace> /why
grace> /specsmith audit --project-dir .
```

- `/help` lists the small local command set.
- `/status` reports provider, model, context pressure, and governance state.
- `/why` reveals the requirement/test/work-item basis for decisions.
- `/specsmith` invokes the same governed CLI contract used by integrations.

Long histories are compressed into evidence-linked summaries before model calls.
Recent turns stay verbatim; unsupported claims remain marked unknown.

## Provider recovery

Grace tries configured providers and explains the missing prerequisite. Common
recovery paths:

```bash
specsmith doctor --onboarding
specsmith endpoints --help
specsmith local-model recommend
specsmith local-model setup
```

Secrets belong in environment variables or the supported credential store, not
in committed configuration.

## Session protocol

At the beginning:

```bash
specsmith kill-session
specsmith audit --project-dir .
specsmith sync --project-dir .
specsmith checkpoint --project-dir .
```

Before an edit:

```bash
specsmith preflight "Describe the exact change. Scope: REQ-001" --json
```

At the end:

```bash
specsmith save --project-dir .
specsmith kill-session
```

## Windows and Linux

Commands accept `--project-dir` instead of relying on shell-specific path
expansion. Use quoted paths when they contain spaces. Zoo Code/Roo Code config
repair normalizes path separators and preserves unrelated user settings on both
platforms.

## Complete surface

```bash
specsmith --help       # mission-essential workflow
specsmith commands     # every supported command
specsmith COMMAND --help
```

The CLI intentionally does not wrap Git hosting, deployment, browsers, patent
search, voice, wireframes, generic multi-agent orchestration, or model
leaderboards. Use the native host tool for those jobs.
