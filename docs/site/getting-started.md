# Getting started

Specsmith adds requirements, linked tests, epistemic context, and evidence gates
to the development tools you already use.

## Install

Use an isolated CLI installation:

```bash
pipx install specsmith
specsmith --version
```

Python 3.10–3.13 is supported on Windows, Linux, and macOS. Library-only use in a
virtual environment is also supported with `pip install specsmith`.

## Adopt a project

For an existing repository:

```bash
cd your-project
specsmith import --project-dir .
specsmith audit --project-dir .
```

For a new governed repository:

```bash
specsmith init
specsmith audit --project-dir .
```

Canonical requirements and tests live under `docs/requirements/` and
`docs/tests/`. `.specsmith/` contains derived machine state and work-item data.

## Complete the first governed change

```bash
specsmith req add --title "Return a stable error envelope"
specsmith test add --req REQ-001 --title "Verify the error envelope" --type integration
specsmith preflight "Implement the error envelope. Scope: REQ-001" --json
# Use your normal editor or coding agent and run the project's native tests.
specsmith verify --project-dir .
specsmith checkpoint --project-dir .
```

- `accepted` means implement only the returned scope.
- `needs_clarification` means align the missing behavior before editing.
- destructive or unsupported work stops.
- completion requires linked tests and observed evidence.

## Integrate an existing agent

This is the recommended path:

```bash
specsmith integrate claude-code   # or cursor, copilot, gemini, aider, warp, windsurf
specsmith mcp serve --project-dir .
```

Restart the host so it discovers the generated configuration. The host keeps its
native code, Git, test, browser, and framework tools; Specsmith contributes only
the compact AEE contract.

For Zoo Code / Roo Code:

```bash
specsmith zoo-code setup --project-dir .
specsmith zoo-code doctor --project-dir .
```

Setup repairs supported malformed or obsolete Specsmith-managed configuration
while preserving unrelated user settings and secrets.

## Use Grace when a local fallback helps

Grace is the optional terminal REPL:

```bash
ollama serve
specsmith run --provider ollama
```

Inside Grace, start with `/help` and `/status`. `/why` displays governance
reasoning, while provider failures include exact recovery guidance. Grace uses
the same requirements, tests, context compression, and verification services as
external integrations.

## Repair older project state

Specsmith can rebuild derived caches from canonical governance sources:

```bash
specsmith sync --project-dir .
specsmith audit --project-dir .
```

Use `specsmith doctor` for installation/provider problems and `specsmith status`
for a compact project and integration overview.

## Next steps

- [Quick start](quickstart.md)
- [CLI commands](commands.md)
- [Agent integrations](agent-integrations.md)
- [Grace](standalone-cli.md)
- [Requirements and work items](wi-lifecycle.md)
- [Governance model](governance.md)
