# Gemini CLI — specsmith Governance Integration

## One-time setup
```bash
specsmith integrate gemini   # generates GEMINI.md in project root
```

Gemini CLI reads `GEMINI.md` from the project root automatically.

## Every Gemini CLI session — mandatory protocol
1. Run at session start:
```bash
specsmith kill-session  # idempotent; safe when no processes exist
specsmith audit --project-dir .
specsmith sync  --project-dir .
specsmith checkpoint --project-dir .
```
2. Output checkpoint block verbatim.
3. Before every code change: `specsmith preflight "<intent>" --json`
4. Every 8–10 turns: `specsmith checkpoint` (output verbatim)
5. Session end: `specsmith save && specsmith kill-session`

## Key files
- `GEMINI.md` — Gemini CLI project instructions
- `AGENTS.md` — universal governance hub
- `.agents/skills/` — skill files referenced from GEMINI.md
