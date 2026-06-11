# GitHub Copilot — specsmith Governance Integration

## One-time setup
```bash
specsmith integrate copilot   # generates .github/copilot-instructions.md
```

Copilot reads `.github/copilot-instructions.md` automatically for all workspace
interactions. The generated file embeds the preflight gate, session protocol,
and hard rules.

## Every Copilot session — mandatory protocol
1. Run at session start:
```bash
specsmith kill-session 2>/dev/null || true
specsmith audit --project-dir .
specsmith sync  --project-dir .
specsmith checkpoint --project-dir .
```
2. Output checkpoint block verbatim.
3. Before every code change: `specsmith preflight "<intent>" --json`
   - Only proceed if `decision == "accepted"`
4. Every 8–10 turns: `specsmith checkpoint` (output verbatim)
5. Session end: `specsmith save && specsmith kill-session`

## Key files
- `.github/copilot-instructions.md` — Copilot workspace instructions
- `AGENTS.md` — universal governance hub
- `.agents/skills/specsmith/SKILL.md` — master CLI reference

## Note
Copilot does not natively support MCP as of 2026. Governance is enforced
through `.github/copilot-instructions.md` and AGENTS.md.
