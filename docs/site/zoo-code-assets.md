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

## Remove

```bash
specsmith zoo-code uninstall --project-dir .
```

## Repository ownership boundary

Specsmith owns reusable global rules, commands, skills, lifecycle manifests, migration, doctor, uninstall, and the standard MCP merge. Individual repositories own project-specific rules, commands, skills, custom modes, provider configuration, and local model routing.
