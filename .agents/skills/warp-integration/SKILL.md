# Warp — specsmith Governance Integration

## One-time setup
```bash
specsmith integrate warp   # generates .warp/ artifacts + .agents/skills/SKILL.md
```

This writes:
- `.warp/specsmith-mcp.json` — governance MCP server config (identical to `specsmith mcp install-warp`)
- `.warp/launch_configs/specsmith-governed.yaml` — Warp launch configuration that opens a governed `specsmith run` session
- `.agents/skills/SKILL.md` — governance skill Warp discovers automatically

For MCP in Warp (Settings → Agents → MCP servers), paste the contents of
`.warp/specsmith-mcp.json`, or generate it directly:
```bash
specsmith mcp install-warp          # human-readable instructions
specsmith mcp install-warp --json   # raw JSON snippet
specsmith mcp register              # register this project (run once per project)
```

## Native REPL awareness
`specsmith run` detects when it is running inside Warp (via `TERM_PROGRAM` /
`WARP_*` env vars) and advertises native integration in its banner and the
`ready` event frame. Behavior is unchanged outside Warp.

## Every Warp session — mandatory protocol
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
- `AGENTS.md` — universal governance hub (Warp reads this as project Rules)
- `.warp/specsmith-mcp.json` — governance MCP server config
- `.warp/launch_configs/specsmith-governed.yaml` — governed-session launch config
- `.agents/skills/` — skill files Warp discovers automatically
