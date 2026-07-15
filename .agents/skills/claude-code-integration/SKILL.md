# Claude Code — specsmith Governance Integration

## One-time setup
```bash
specsmith integrate claude-code   # generates CLAUDE.md in project root
```

For MCP server (structured tool calls without shell roundtrips), add to `.mcp.json`:
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
Or run: `specsmith mcp install-claude-code`

## Every Claude Code session — mandatory protocol
1. Run at session start:
```bash
specsmith kill-session  # idempotent; safe when no processes exist
specsmith audit --project-dir .
specsmith sync  --project-dir .
specsmith checkpoint --project-dir .
```
2. Output the checkpoint block verbatim before any other response.
3. Before every code change: `specsmith preflight "<intent>" --json`
   - `decision == "accepted"` → proceed with `work_item_id` in scope
   - `decision == "needs_clarification"` → surface instruction to user first
4. Every 8–10 turns: `specsmith checkpoint` (output verbatim)
5. Session end: `specsmith save && specsmith kill-session`

## Via MCP (preferred when configured)
Claude can call `governance_preflight`, `governance_audit`, `governance_checkpoint`,
`governance_req_list`, `governance_phase`, and `governance_trace_seal` as native tools.

## Key files
- `CLAUDE.md` — project-level governance instructions (read by Claude automatically)
- `.mcp.json` — MCP server config (project root or `~/.claude/mcp.json` for global)
- `.agents/skills/` — skill files auto-discovered by Claude Code 3.x+
