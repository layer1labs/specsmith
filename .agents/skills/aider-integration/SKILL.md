# Aider — specsmith Governance Integration

## One-time setup
```bash
specsmith integrate aider   # generates .aider.conf.yml
```

Manual: add to `.aider.conf.yml`:
```yaml
read:
  - AGENTS.md
  - .agents/skills/specsmith/SKILL.md
  - .agents/skills/specsmith-session-governance/SKILL.md
  - .agents/skills/specsmith-save/SKILL.md
```

Or pass at startup:
```bash
aider --read AGENTS.md       --read .agents/skills/specsmith-session-governance/SKILL.md
```

## Every Aider session — mandatory protocol
1. Run before starting aider:
```bash
specsmith kill-session  # idempotent; safe when no processes exist
specsmith audit --project-dir .
specsmith sync  --project-dir .
specsmith checkpoint --project-dir .
```
2. Tell aider the governance anchor before any request:
   `"Session anchor: [paste checkpoint output here]. Use preflight before changes."`
3. Before aider makes code changes, verify preflight in a separate terminal:
   `specsmith preflight "<intent>" --json`
4. After aider commits, run: `specsmith save` to add ESDB backup.

## Note
Aider auto-commits via git. For full governance, configure aider with
`--no-auto-commits` and manage commits through `specsmith save` instead.

## Key files
- `.aider.conf.yml` — aider configuration (reads AGENTS.md + skills)
- `AGENTS.md` — universal governance hub
- `.agents/skills/` — skills loaded via `read:` in aider config
