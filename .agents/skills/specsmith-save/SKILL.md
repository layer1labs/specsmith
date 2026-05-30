---
name: specsmith-save
description: Run specsmith save to commit and push all current changes with governance state backup. Use at the end of any work session or after completing a feature/fix.
---

# Specsmith Save

Saves governance state: backs up the ESDB, commits any staged/unstaged changes,
and pushes to the remote.

## When to use

- At the end of any work session
- After implementing a feature, fix, or refactor
- After advancing a phase
- Whenever the user says "save", "commit and push", or "specsmith save"

## How to run

```bash
specsmith save
```

## What it does (in order)

1. **ESDB backup** — snapshots the epistemic state database
2. **Commit** — stages all changes and commits with a governance-aware message (or reports "Nothing to commit")
3. **Push** — pushes the branch to origin (or reports "Everything up-to-date")

## Expected successful output

```
  ✓ esdb_backup: JSON fallback (no WAL to backup)
  ✓ commit: Nothing to commit          ← or a commit hash
  ✓ push: Everything up-to-date        ← or "pushed to origin/branch"
```

## If there are changes to commit

Specsmith auto-stages and commits. You can also pre-stage manually:

```bash
git add -A
git commit -m "feat: description

Co-Authored-By: Oz <oz-agent@warp.dev>"
specsmith save   # will see nothing to commit, just pushes
```

## Do NOT use `git push` directly

Always use `specsmith save` — it ensures the ESDB backup runs before the push,
keeping governance state consistent with the remote.
