---
name: specsmith-audit
description: Run specsmith audit to check for governance drift between requirements, tests, and architecture. Required before advancing an AEE phase.
---

# Specsmith Audit

Checks the project for drift between requirements (ARCHITECTURE.md), test cases,
and the codebase. Must pass before advancing an AEE phase.

## How to run

```bash
specsmith audit
```

## Interpreting results

```
29 PASS   ← all requirements have matching tests and implementation
 2 WARN   ← drift detected — investigate these
 0 FAIL
```

**All items must be PASS or suppressed before `specsmith phase advance`.**

## When a WARN appears

1. Read the warning — it references a requirement ID (e.g. `R20`) and describes what's missing
2. Fix it: add the missing test, update ARCHITECTURE.md, or implement the requirement
3. Re-run `specsmith audit` to confirm it passes
4. If it's a confirmed false positive: `specsmith audit --suppress <CODE>`

## Suppressing a false positive

Only suppress if you've verified the requirement IS met but the audit can't detect it:

```bash
specsmith audit --suppress SEAL-XXXX-001
```

Suppressions are permanent — use sparingly.

## Common causes of WARN

- Requirement in ARCHITECTURE.md has no corresponding test case
- Test exists but requirement ID reference is missing from the test
- Implementation exists but the architecture doc wasn't updated to match

## After fixing all warnings

```bash
specsmith audit          # confirm all pass
specsmith phase advance  # advance the phase
specsmith save           # commit the phase bump
```

## Quick audit before a session

Run `specsmith audit` at the start of a session to catch drift from the previous
session before making new changes.
