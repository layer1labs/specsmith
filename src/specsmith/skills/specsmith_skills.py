# SPDX-License-Identifier: MIT
"""Specsmith self-referential skills — how to USE specsmith in any project.

These skills teach AI agents (Warp, Claude Code, Codex, Cursor, etc.) the
core specsmith governance workflows. Install in any project via:

    specsmith skill install specsmith
    specsmith skill install specsmith-save
    specsmith skill install specsmith-audit
"""

from specsmith.skills import SkillDomain, SkillEntry

SKILLS: list[SkillEntry] = [
    SkillEntry(
        slug="specsmith",
        name="Specsmith \u2014 AEE governance CLI reference",
        description=(
            "Master reference for the specsmith AEE governance tool: key concepts, "
            "common commands, session workflow, phase advancement, and audit codes. "
            "Use whenever working in a specsmith-governed project."
        ),
        domain=SkillDomain.GOVERNANCE,
        tags=[
            "specsmith", "aee", "governance", "session", "workflow",
            "audit", "phase", "save", "esdb", "ledger",
        ],
        prerequisites=["specsmith"],
        body="""\
# Specsmith \u2014 Project Governance Tool

Specsmith is the AEE (Agile Epistemic Engineering) governance CLI. It manages
requirements, phases, audit trails, and session state. It wraps git with
governance-aware commits and backs up the epistemic state DB (ESDB).

## Key concepts

- **ESDB** \u2014 Epistemic State Database. Tracks certainty, audit state, session memory.
  Backed up on `specsmith save`.
- **Phases** \u2014 AEE lifecycle: Inception \u2192 Elaboration \u2192 Construction \u2192
  Transition \u2192 Validation \u2192 Hardening \u2192 Release.
- **Ledger** \u2014 Running log of changes in `LEDGER.md`. Auto-updated by commits.
- **Audit** \u2014 Checks requirements vs tests vs architecture for drift.
  Required before phase advance.
- **Save** \u2014 ESDB backup + governance-aware git commit + push.

## Session workflow

```
1. specsmith audit          # check for drift before working
2. <make code changes>
3. specsmith save           # commit + push + ESDB backup
```

## Common commands

| Command | What it does |
|---------|-------------|
| `specsmith save` | ESDB backup \u2192 commit (if needed) \u2192 push |
| `specsmith audit` | Drift/health check \u2014 requirements vs tests vs arch |
| `specsmith audit --suppress <CODE>` | Accept a known false positive |
| `specsmith phase` | Show current AEE phase |
| `specsmith phase advance` | Advance to next phase (requires clean audit) |
| `specsmith commit` | Governance-aware commit (wraps git commit) |
| `specsmith ledger` | Show/manage the change ledger |
| `specsmith compress` | Compress old ledger entries |
| `specsmith req` | Manage requirements |
| `specsmith test` | Manage test cases |
| `specsmith status` | VCS/CI/PR status |
| `specsmith skill list` | List built-in installable skills |
| `specsmith skill install <slug>` | Install a skill into `.agents/skills/` |

## Commit conventions

Specsmith commits follow: `type: message` where type is one of:
`feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`

Always append `Co-Authored-By: Oz <oz-agent@warp.dev>` when committing as an AI agent.

## Important rules

- **Never use `git commit` directly** \u2014 use `specsmith save` or `specsmith commit`.
- **Run `specsmith audit` before advancing a phase** \u2014 drift will cause failure.
- **Suppressed audit findings** are stored permanently; only suppress genuine false positives.
- After `specsmith save` outputs `\u2713 push: Everything up-to-date`, the repo is clean.

## Audit result codes

- `PASS` \u2014 requirement/test/arch is consistent
- `WARN` \u2014 drift detected, investigate
- `SKIP` / suppressed \u2014 accepted false positive
- IDs like `R20`, `R21` \u2014 requirement IDs in ARCHITECTURE.md

## Phase advancement

```bash
specsmith audit          # must be all-pass (or suppressed)
specsmith phase advance  # bumps phase, writes ledger entry
specsmith save           # commit the phase bump
```

## Installing skills in any project

```bash
specsmith skill install specsmith        # this reference card
specsmith skill install specsmith-save   # save workflow
specsmith skill install specsmith-audit  # audit workflow
```
""",
    ),
    SkillEntry(
        slug="specsmith-save",
        name="Specsmith Save \u2014 commit and push with governance state backup",
        description=(
            "How and when to run `specsmith save`: backs up the ESDB, commits any "
            "staged/unstaged changes, and pushes to the remote. Use at the end of "
            "any work session or after completing a feature/fix."
        ),
        domain=SkillDomain.GOVERNANCE,
        tags=[
            "specsmith", "save", "commit", "push", "esdb", "governance", "session",
        ],
        prerequisites=["specsmith"],
        body="""\
# Specsmith Save

Saves governance state: backs up the ESDB, commits any staged/unstaged changes,
and pushes to the remote.

## When to use

- At the end of any work session
- After implementing a feature, fix, or refactor
- After advancing a phase
- Whenever the user says \"save\", \"commit and push\", or \"specsmith save\"

## How to run

```bash
specsmith save
```

## What it does (in order)

1. **ESDB backup** \u2014 snapshots the epistemic state database
2. **Commit** \u2014 stages all changes and commits (or reports \"Nothing to commit\")
3. **Push** \u2014 pushes the branch to origin (or reports \"Everything up-to-date\")

## Expected successful output

```
  \u2713 esdb_backup: JSON fallback (no WAL to backup)
  \u2713 commit: Nothing to commit          \u2190 or a commit hash
  \u2713 push: Everything up-to-date        \u2190 or \"pushed to origin/branch\"
```

## If there are changes to commit

Specsmith auto-stages and commits. You can also pre-stage manually:

```bash
git add -A
git commit -m \"feat: description

Co-Authored-By: Oz <oz-agent@warp.dev>\"
specsmith save   # will see nothing to commit, just pushes
```

## Do NOT use `git push` directly

Always use `specsmith save` \u2014 it ensures the ESDB backup runs before the push,
keeping governance state consistent with the remote.
""",
    ),
    SkillEntry(
        slug="specsmith-audit",
        name="Specsmith Audit \u2014 governance drift check",
        description=(
            "How to run `specsmith audit` to check for governance drift between "
            "requirements, tests, and architecture. Required before advancing an AEE phase."
        ),
        domain=SkillDomain.GOVERNANCE,
        tags=[
            "specsmith", "audit", "drift", "requirements", "governance",
            "aee", "phase", "verification",
        ],
        prerequisites=["specsmith"],
        body="""\
# Specsmith Audit

Checks the project for drift between requirements (ARCHITECTURE.md), test cases,
and the codebase. Must pass before advancing an AEE phase.

## How to run

```bash
specsmith audit
```

## Interpreting results

```
29 PASS   \u2190 all requirements have matching tests and implementation
 2 WARN   \u2190 drift detected \u2014 investigate these
 0 FAIL
```

**All items must be PASS or suppressed before `specsmith phase advance`.**

## When a WARN appears

1. Read the warning \u2014 it references a requirement ID (e.g. `R20`) and describes what's missing
2. Fix it: add the missing test, update ARCHITECTURE.md, or implement the requirement
3. Re-run `specsmith audit` to confirm it passes
4. If it's a confirmed false positive: `specsmith audit --suppress <CODE>`

## Suppressing a false positive

Only suppress if you've verified the requirement IS met but the audit can't detect it:

```bash
specsmith audit --suppress SEAL-XXXX-001
```

Suppressions are permanent \u2014 use sparingly.

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
""",
    ),
]
