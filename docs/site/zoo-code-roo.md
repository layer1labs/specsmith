# Zoo Code / Roo Code Integration

Specsmith supports Zoo Code and Roo Code as governed local agent clients.

The intended architecture is:

```text
Zoo Code / Roo Code
  -> project-local .roo MCP config
  -> specsmith-governance MCP server
  -> LiteLLM local router
  -> vLLM resident role models
```

Zoo/Roo are the hands. LiteLLM is the router. vLLM is the local model pool. Specsmith is the engineering governance layer.

## Project-local files

The repo-local integration surface is `.roo/`:

| File | Purpose |
|---|---|
| `.roo/mcp.json` | Registers the `specsmith-governance` MCP server for this repository. |
| `.roo/specsmith-rules.md` | Defines mandatory governed-agent behavior. |
| `.roo/modes.local.json` | Project-local reference mapping of modes to local model roles. |
| `.roo/global-settings.copy-to-zoo-code.json` | Copyable global provider/model settings for clients that do not read project-local mode config. |

Do not commit real API keys or secrets into `.roo/`.

## MCP server

`.roo/mcp.json` starts Specsmith's MCP server from the current repository:

```json
{
  "mcpServers": {
    "specsmith-governance": {
      "command": "specsmith",
      "args": ["mcp", "serve", "--project-dir", "."]
    }
  }
}
```

The MCP tools provide the governance loop:

- `governance_checkpoint`
- `governance_preflight`
- `governance_phase`
- `governance_req_list`
- `governance_trace_seal`

## Required workflow

Every Zoo/Roo coding session should follow this loop:

```text
1. Read AGENTS.md and .roo/specsmith-rules.md.
2. Call governance_checkpoint.
3. Call governance_phase and governance_req_list.
4. Call governance_preflight before editing.
5. Edit only within accepted scope.
6. Run targeted tests or build checks.
7. Review the diff with a separate reviewer role.
8. Seal meaningful decisions or release evidence.
```

The model that writes the patch must not be the only model that approves it.

## Local model routing

Use a LiteLLM-compatible endpoint when a ChronoCortex local agent pool is available:

```text
http://localhost:4000/v1
```

Recommended role mapping:

| Zoo/Roo mode | Local model role |
|---|---|
| Architect | `architect` |
| Code | `editor` |
| Debug / Tool | `tool-fast` |
| Review | `reviewer` |

## Operator setup

1. Start the local model pool and LiteLLM router.
2. Export `LITELLM_MASTER_KEY` in the environment that launches Zoo/Roo.
3. Copy `.roo/global-settings.copy-to-zoo-code.json` values into Zoo Code global settings when required by the client.
4. Confirm the MCP server appears as `specsmith-governance`.
5. Start work from Architect mode and require preflight before edits.

## Safety defaults

Zoo/Roo agents should not perform these actions without explicit user approval and accepted Specsmith preflight:

- dependency upgrades
- public API changes
- large generated rewrites
- destructive file operations
- secret or `.env` edits
- git push, release, or deploy actions

## Embedded and firmware work

For firmware, FPGA, Zephyr, or low-level systems work, Zoo/Roo must ground changes in actual repository evidence:

- headers
- vendor SDK files
- bindings
- generated output
- compiler/build logs
- tests

Do not accept invented SDK, HAL, register, device-tree, or build-system APIs.
