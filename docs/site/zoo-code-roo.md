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
- `governance_context_transition`
- `governance_context_verify`

## Governed context authority

In governed mode, Specsmith is the only semantic checkpoint and replacement
packet authority. Zoo supplies token telemetry to
`governance_context_transition`, applies the returned packet without adding its
own summary, then reports the applied SHA-256 digest to
`governance_context_verify`. Work resumes only when the digest and context
health gate pass.

Zoo's autonomous conversation condensation must be disabled for each governed
mode. In Zoo Code, open **Settings → Context → Auto Condense**, set it to
**Off** for orchestrator, architect, code, debug, ask, and reviewer modes, then
reload the editor and run `specsmith zoo-code doctor --project-dir .`. This
setting is UI/version owned when Zoo does not expose a supported settings key;
Specsmith reports `partial_manual_required` until the value can be verified.

If Specsmith is unavailable, packet verification fails, or required constraints
are missing, preserve raw history and enter `blocked_degraded`. Do not invoke
Zoo's default `summarizeConversation` or sliding-window truncation. A provider
hard-limit emergency may avoid a failed request but remains degraded until a
Specsmith checkpoint and rebuilt packet validate. An explicit user opt-out is
reported as **unmanaged** and carries no Specsmith context assurance.

Zoo workspace checkpoints remain file snapshots. They may be paired with a
Specsmith semantic checkpoint ID, but restoring or rewinding a workspace does
not roll back evidence; it invalidates the applied packet and requires
reconciliation. When the controller returns `spawn_fresh_task`, Zoo must create
the child from the exact governed handoff packet and report the new task ID.

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

### Local-LLM import profile

Use the dedicated lifecycle command rather than editing Zoo Code Secret Storage
or legacy `cline_settings.json` files:

```bash
specsmith zoo-code litellm setup --project-dir .
specsmith zoo-code litellm doctor --project-dir .
```

This produces `.zoo-code/specsmith-zoo-local-llm.json`, a current Zoo Code
settings-import document. It uses the dedicated `litellm` provider, the default
`http://127.0.0.1:4000` endpoint, a stable Specsmith governance prefix, and
mode-to-profile mappings. It never contains `litellmApiKey`; configure an
authenticated proxy through Zoo Code's secret-backed UI.

Prompt-cache controls are included only after the LiteLLM `/v1/model/info`
metadata explicitly advertises `supports_prompt_caching`. An unreachable proxy
does not block asset generation: `doctor` reports the reachability problem and
the asset stays usable when the proxy becomes available.

For startup import, add the asset through Zoo Code Settings or run setup with
`--enable-auto-import`. The latter is intentionally opt-in because Zoo imports
the file at every startup; disable it after initial provisioning if you later
customize the `Local-LLM` profile or a mapping. Specsmith safely repairs only
its provenance-marked assets, preserving user-created files and backing up a
broken managed or legacy asset before replacement.

Setup and doctor use a versioned ownership registry. Automatable managed drift
is repaired only after a fresh-read digest check; concurrent edits fail and are
retried. Manual-only gaps include the exact UI path, label, value, reload need,
verification command, and assurance impact. Uninstall restores a recorded prior
value only if the setting still equals Specsmith's managed value, so later user
edits win. Secrets are never copied into settings, manifests, logs, or docs.

The generated import defaults Zoo's `globalSettings.allowedCommands` to the
single literal entry `"*"`, permitting all terminal commands. This is an
intentional Zoo execution setting—not a substitute for Specsmith governance or
verification. Restrict the command-prefix list in Zoo Code before running an
agent in an untrusted repository; Specsmith preserves a non-default user list
on later setup runs.

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
