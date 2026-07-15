# Cursor — specsmith Governance Integration

## One-time setup
```bash
specsmith integrate cursor   # generates .cursor/rules/governance.mdc
```

For MCP in Cursor (Settings → MCP or `.cursor/mcp.json`):
```json
{
  "specsmith-governance": {
    "command": "specsmith",
    "args": ["mcp", "serve", "--project-dir", "${workspaceFolder}"]
  }
}
```

## Every Cursor session — mandatory protocol
1. Run at session start:
```bash
specsmith kill-session  # idempotent; safe when no processes exist
specsmith audit --project-dir .
specsmith sync  --project-dir .
specsmith checkpoint --project-dir .
```
2. Output the checkpoint block verbatim.
3. Before every code change: `specsmith preflight "<intent>" --json`
4. Every 8–10 turns: `specsmith checkpoint` (output verbatim)
5. Session end: `specsmith save && specsmith kill-session`

## Key files
- `.cursor/rules/governance.mdc` — Cursor rule file (applied to all files)
- `.cursor/mcp.json` — project-level MCP config
- `AGENTS.md` — universal governance hub (Cursor reads this as project context)
- `.agents/skills/` — skill files (Cursor Agent mode discovers these)
