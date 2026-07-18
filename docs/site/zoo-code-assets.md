# Portable Zoo Code integration

Specsmith is the canonical distribution point for reusable Zoo Code rules, slash commands, skills, and MCP configuration. Project repositories retain only project-specific `.roo` assets and model/provider settings.

## Install or update

```bash
pipx upgrade specsmith
cd /path/to/project
specsmith zoo-code setup --project-dir .
specsmith zoo-code doctor --project-dir .
```

By default, setup installs reusable Specsmith assets under `~/.roo`, merges the `specsmith-governance` MCP server into `.roo/mcp.json`, and removes recognized generic Specsmith rule duplicates from the workspace.

Use `ROO_GLOBAL_DIR` or `--global-roo` to override the global Zoo Code directory. Use `--scope global` or `--scope project` to operate on one side only. `--dry-run` previews changes. `--preserve-existing` refuses to adopt an unmanaged file at a reserved Specsmith path.

## Safety

Existing unmanaged files at reserved global paths are backed up before adoption. Customized workspace files are preserved and reported. Setup removes stale assets only when they carry a Specsmith managed marker. Uninstall removes only managed assets and removes the MCP entry only when it still matches the Specsmith-managed value.

## Local LiteLLM profile

To provision Zoo Code with Specsmith's `Local-LLM` profile, generate the
portable import asset in the project:

```bash
specsmith zoo-code litellm setup --project-dir .
specsmith zoo-code litellm validate --project-dir .
specsmith zoo-code litellm doctor --project-dir .
```

The asset is `.zoo-code/specsmith-zoo-local-llm.json`. It follows Zoo Code's
current settings-import schema, creates a dedicated `litellm` profile at
`http://127.0.0.1:4000`, assigns the built-in and generated Specsmith modes to
that profile, and uses a deterministic governance prefix with current-time and
current-cost injections disabled. No API key is written: Zoo Code keeps real
keys in VS Code Secret Storage, while an unauthenticated LiteLLM proxy uses
Zoo's own dummy-key behavior.

The setup command queries `/v1/model/info` when the proxy is reachable and
sets `litellmUsePromptCache` only if LiteLLM explicitly reports
`supports_prompt_caching: true`. It never infers cache support from a model
name or a plain model list.

Zoo Code can import the asset from Settings, or you can opt into its documented
startup importer with `--enable-auto-import`. Auto-import re-applies the asset
on every extension startup, so disable it after first provisioning when you
intend to customize `Local-LLM` or a mode mapping in Zoo Code. Specsmith does
not overwrite user-owned assets; it backs up and repairs only assets carrying
its provenance marker (including the obsolete pre-release asset format).

### Command approval default

The managed import asset uses Zoo Code's current `globalSettings.allowedCommands`
field with exactly one literal value: `"*"`. This intentionally permits every
terminal command in a newly imported profile; it is not a shell glob that
Specsmith expands. Command approval is a Zoo Code execution control, separate
from Specsmith's requirements, validation, ledger, and audit controls.

Review this setting before using agents in an untrusted repository. You can
replace the wildcard in Zoo Code Settings with a narrower list of command
prefixes. On a later `specsmith zoo-code litellm setup`, Specsmith preserves a
non-default command list. It migrates its older no-policy asset to the wildcard
only when the asset manifest proves it was never edited.

```bash
specsmith zoo-code litellm setup --project-dir . --enable-auto-import
specsmith zoo-code litellm uninstall --project-dir .
```

Windows, Linux, and macOS VS Code settings paths are resolved by the command.
When a VS Code `settings.json` contains JSONC comments or malformed JSON, the
command refuses to rewrite it and tells you to add the auto-import setting
manually, preserving the existing editor configuration.

## Remove

```bash
specsmith zoo-code uninstall --project-dir .
```

## Repository ownership boundary

Specsmith owns reusable global rules, commands, skills, lifecycle manifests, migration, doctor, uninstall, and the standard MCP merge. Individual repositories own project-specific rules, commands, skills, custom modes, provider configuration, and local model routing.
