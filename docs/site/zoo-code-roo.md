# Zoo Code / Roo Code Integration

Specsmith integrates with Zoo Code / Roo Code through reusable global assets, a repo-local `.roo/` directory, and the Specsmith MCP governance server.

## Setup

Install or upgrade Specsmith with pipx, then configure the active project:

```bash
pipx upgrade specsmith
cd /path/to/project
specsmith zoo-code setup --project-dir .
specsmith zoo-code doctor --project-dir .
```

The setup command installs reusable Specsmith rules, slash commands, and skills under `~/.roo`. It also merges the `specsmith-governance` MCP server into the project `.roo/mcp.json` without removing unrelated servers.

Use `--global-roo PATH` or `ROO_GLOBAL_DIR` to override the global directory. `--scope global` and `--scope project` limit the operation. `--dry-run` previews changes, and `--preserve-existing` refuses to replace unmanaged files at reserved Specsmith paths.

## Ownership boundary

Specsmith owns reusable global governance assets and their setup, migration, doctor, and uninstall lifecycle. Repositories should contain only project-specific rules, commands, skills, custom modes, and provider/model settings.

Existing generic Specsmith rules duplicated inside a project are removed only when they match a recognized legacy asset or carry a Specsmith managed marker. Customized project files are preserved and reported.

## MCP setup

The generated repo-local MCP entry is:

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
read AGENTS.md and applicable global/project rules
call governance_checkpoint
call governance_phase
call governance_req_list
call governance_preflight before edits
edit only within accepted scope
run tests/build checks
run verification
seal meaningful decisions
```

Do not edit files unless `governance_preflight` returns `accepted` or the request is classified as a permitted environment-only operation.

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

## Operator checklist

1. Start the local model router when using local models.
2. Run `specsmith zoo-code setup --project-dir .`.
3. Run `specsmith zoo-code doctor --project-dir .`.
4. Reload the editor so Zoo Code discovers the final rules, commands, skills, and MCP configuration.
5. Start governed work with `/specsmith-intake` or the appropriate project-specific command.

## Remove managed integration state

```bash
specsmith zoo-code uninstall --project-dir .
```

Uninstall removes only marker-owned global assets and removes the MCP entry only when it still matches the Specsmith-managed value. Unmanaged and customized files are preserved.
