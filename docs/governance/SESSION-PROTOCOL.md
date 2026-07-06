# Session Protocol

This document defines the session protocol that specsmith follows to ensure consistent governance across all development sessions.

## Session Lifecycle

1. **Session Start**
   - Kill any orphaned processes
   - Verify governance health
   - Confirm machine state matches governance YAML
   - Emit governance anchor

2. **Session Execution**
   - All commands must pass preflight checks
   - Changes are tracked through work items
   - Audit logs are maintained for all actions

3. **Session End**
   - Save governance state
   - Commit changes with governance-aware message
   - Push to remote repository

## Governance Enforcement

- All commands are subject to preflight gates
- Agent actions are monitored and audited
- Compliance checks are performed at each step
- Session integrity is maintained throughout

## Session Bootstrap

Run these steps at the start of **every** session before touching any code:

```bash
# Governance operations use the global pipx specsmith (specsmith 0.11.6 at ~/.local/bin/specsmith).
# For active development of specsmith itself, set up a dev venv: python -m venv .venv && .venv\Scripts\pip install -e .
# NEVER install specsmith via plain pip into any other environment.

# 1. Apply any pending migrations (always answer Y to migration prompts)
specsmith migrate run

# 2. Verify governance health
specsmith audit

# 3. Confirm machine state matches governance YAML
specsmith sync
```

Only proceed with the requested task once all three steps complete without errors.
If `audit` reports failures, surface them to the user before starting work.
