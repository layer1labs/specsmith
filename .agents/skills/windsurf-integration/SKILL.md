# Windsurf — specsmith Governance Integration

## One-time setup
```bash
specsmith integrate windsurf   # generates .windsurfrules
```

For MCP in Windsurf (Settings → MCP Servers):
```json
{
  "specsmith-governance": {
    "command": "specsmith",
    "args": ["mcp", "serve"]
  }
}
```

## Every Windsurf session — mandatory protocol
1. Run at session start:
```bash
specsmith kill-session 2>/dev/null || true
specsmith audit --project-dir .
specsmith sync  --project-dir .
specsmith checkpoint --project-dir .
```
2. Output checkpoint block verbatim.
3. Before every code change: `specsmith preflight "<intent>" --json`
4. Every 8–10 turns: `specsmith checkpoint` (output verbatim)
5. Session end: `specsmith save && specsmith kill-session`

## Key files
- `.windsurfrules` — Windsurf global rules file
- `AGENTS.md` — universal governance hub
- `.agents/skills/` — skill directory (Cascade agent reads these)
