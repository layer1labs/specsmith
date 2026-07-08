# Zoo Code / Roo Code Integration

Specsmith integrates with Zoo Code / Roo Code through a repo-local `.roo/` directory and the Specsmith MCP governance server.

## What belongs in the repository

Project-local integration files:

| File | Purpose |
|---|---|
| `.roo/mcp.json` | Registers the `specsmith-governance` MCP server for this repo. |
| `.roo/specsmith-rules.md` | Mandatory rules for governed Zoo/Roo sessions. |
| `.roo/modes.local.json` | Reference mode-to-model mapping for this project. |
| `.roo/global-settings.copy-to-zoo-code.json` | Copyable global provider/model settings for Zoo Code. |

Zoo Code global settings are not automatically loaded from a repository. Keep copyable global settings in the project as a reference, then copy them into Zoo Code global/user settings manually.

## MCP setup

The repo-local MCP config should look like this:

```json
{
  "mcpServers": {
    "specsmith-governance": {
      "command": "specsmith",
      "args": ["mcp", "serve", "--project-dir", "."],
      "env": {
        "SPECSMITH_ALLOW_NON_PIPX": "1",
        "SPECSMITH_NO_AUTO_UPDATE": "1",
        "SPECSMITH_PYPI_CHECKED": "1"
      }
    }
  }
}
```

The MCP server exposes governance tools such as:

- `governance_checkpoint`
- `governance_phase`
- `governance_req_list`
- `governance_preflight`
- `governance_audit`
- `governance_trace_seal`

## Required agent flow

Every Zoo/Roo session should follow this sequence:

```text
read AGENTS.md + .roo/specsmith-rules.md
call governance_checkpoint
call governance_phase
call governance_req_list
call governance_preflight before edits
edit only within accepted scope
run tests/build checks
run verification
seal meaningful decisions
```

Do not edit files unless `governance_preflight` returns `accepted`.

## Local model routing

When a local LiteLLM/vLLM pool is available, use the router endpoint:

```text
Base URL: http://localhost:4000/v1
API key:  $LITELLM_MASTER_KEY
```

Recommended role mapping:

| Zoo/Roo mode | Model |
|---|---|
| Specsmith Architect | `architect` |
| Specsmith Code | `editor` |
| Specsmith Debug / Tool | `tool-fast` |
| Specsmith Review | `reviewer` |

The model that writes a patch must not be the only model that approves it.

## Operator setup checklist

1. Start the local model router if using local models.
2. Copy `.roo/global-settings.copy-to-zoo-code.json` into Zoo Code global settings, adapting field names to the current extension version.
3. Ensure Zoo/Roo sees `.roo/mcp.json` for the active workspace.
4. Start a session by asking the agent to read `.roo/specsmith-rules.md` and call `governance_checkpoint`.
5. Run governed tasks using the role split: Architect -> Code -> Debug/Tool -> Review.

## Safe defaults

- Architect mode plans and reads; it should not directly edit production code.
- Code mode implements accepted preflight tasks.
- Debug/Tool mode runs safe commands and parses logs.
- Review mode critiques diffs against requirements, tests, and prior decisions.
- Specsmith blocks or escalates work when confidence, phase, or scope checks fail.
