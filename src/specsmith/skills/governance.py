# SPDX-License-Identifier: MIT
"""Governance skills — project lifecycle, verification, review, and release."""

from specsmith.skills import SkillDomain, SkillEntry

SKILLS: list[SkillEntry] = [
    SkillEntry(
        slug="verifier",
        name="Verifier — five-gate verification",
        description=(
            "Runs the standard five-gate loop: ruff, mypy, pytest, pip-audit, "
            "and specsmith audit/validate. Halts at the first failing gate."
        ),
        domain=SkillDomain.GOVERNANCE,
        tags=["verification", "ci", "python", "lint", "test", "security"],
        project_types=["cli-python", "library-python", "backend-frontend"],
        platforms=[],
        prerequisites=["ruff", "mypy", "pytest", "pip-audit"],
        body=(
            "# Verifier Skill\n\n"
            "## Purpose\n"
            "Enforce a deterministic, ordered quality gate before any commit.\n\n"
            "## Gates (run in strict order — halt at first failure)\n"
            "1. `ruff check .` — zero lint errors.\n"
            "2. `ruff format --check src tests` — zero format drift.\n"
            "3. `mypy src/` — zero type errors.\n"
            "4. `pytest -q --tb=short` — all tests green.\n"
            "5. `pip-audit` — no known vulnerabilities.\n"
            "6. `specsmith audit && specsmith validate --strict` — governance clean.\n\n"
            "## Rules\n"
            "- Never skip a gate. Never amend a commit to bypass failures.\n"
            "- Surface the first failing gate's output verbatim in your response.\n"
            "- If gate 6 fails with a sync-drift warning, run `specsmith sync` first.\n\n"
            "## After all gates pass\n"
            '```\nspecsmith ledger add "All gates passed — ready to commit"\n'
            'git add -A && git commit -m "<msg>"\n```\n'
        ),
    ),
    SkillEntry(
        slug="planner",
        name="Planner — propose-then-execute",
        description=(
            "Forces the agent to emit a Plan block with explicit success criteria "
            "before any tool call. Each step is gated on prior-step success."
        ),
        domain=SkillDomain.GOVERNANCE,
        tags=["planning", "governance", "aee"],
        prerequisites=[],
        body=(
            "# Planner Skill\n\n"
            "## Purpose\n"
            "Prevent surprise changes. All work must be planned before execution.\n\n"
            "## Protocol\n"
            "1. Emit a `Plan:` block listing each step with a measurable success criterion.\n"
            "2. Wait for user confirmation (`safe` profile) or proceed (`yolo` profile).\n"
            "3. Execute steps one at a time; update `status: done | failed` after each.\n"
            "4. Never call tools outside the plan. If new work is discovered, amend the plan.\n"
            "5. Log plan completion to LEDGER.md.\n\n"
            "## Plan block format\n"
            "```\nPlan:\n  1. [step] — success: [criterion]\n"
            "  2. [step] — success: [criterion]\n```\n"
        ),
    ),
    SkillEntry(
        slug="diff-reviewer",
        name="Diff Reviewer — surface changes for approval",
        description=(
            "Emits a diff block per changed file and waits for Accept/Reject "
            "before committing. Rejected diffs feed the next retry."
        ),
        domain=SkillDomain.GOVERNANCE,
        tags=["review", "diff", "governance", "approval"],
        prerequisites=[],
        body=(
            "# Diff Reviewer Skill\n\n"
            "## When to use\n"
            "Any task that modifies source files, config, or governance docs.\n\n"
            "## Protocol\n"
            "1. Perform all changes in working tree (do not commit yet).\n"
            "2. Run `git diff HEAD` and emit one fenced diff block per file.\n"
            "3. Pause and wait for `accept` / `reject` / `comment` per diff.\n"
            "4. For rejected diffs: revert that file, apply the comment as context, retry.\n"
            "5. Only commit once every diff has been accepted.\n\n"
            "## Rules\n"
            "- Never auto-accept your own changes.\n"
            "- Surface the full diff, not a summary. Summaries hide bugs.\n"
        ),
    ),
    SkillEntry(
        slug="onboarding-coach",
        name="Onboarding Coach — guided first session",
        description=(
            "Walks a new user through the project: scaffold check, REQUIREMENTS "
            "tour, AGENTS.md rules summary, and a suggested first action."
        ),
        domain=SkillDomain.GOVERNANCE,
        tags=["onboarding", "documentation", "new-user"],
        prerequisites=["specsmith"],
        body=(
            "# Onboarding Coach Skill\n\n"
            "## Sequence\n"
            "1. `specsmith doctor --onboarding` — surface any missing setup step.\n"
            "2. Read `AGENTS.md`; summarise hard rules in ≤ 5 bullets.\n"
            "3. Read `docs/REQUIREMENTS.md`; list top 5 P1 requirements.\n"
            "4. `specsmith phase show` — report current AEE phase and readiness %.\n"
            "5. Suggest one concrete preflight utterance the user can run next.\n\n"
            "## Output format\n"
            "```\n🌱 Phase: <phase> (<pct>% ready)\n"
            "📋 Top requirements: ...\n📌 Rules: ...\n"
            '→ Suggested next: specsmith preflight "..."\n```\n'
        ),
    ),
    SkillEntry(
        slug="release-pilot",
        name="Release Pilot — gitflow release cut",
        description=(
            "Drives a full gitflow release: CI green check, version bump, "
            "CHANGELOG entry, tag, and publish."
        ),
        domain=SkillDomain.GOVERNANCE,
        tags=["release", "vcs", "gitflow", "automation", "pypi", "github"],
        prerequisites=["gh", "git"],
        body=(
            "# Release Pilot Skill\n\n"
            "## Preconditions (abort if any fail)\n"
            "- `gh run list --branch develop --limit 1 --json conclusion` = `SUCCESS`.\n"
            "- `gh pr list --state open --base main` returns 0 open PRs.\n"
            "- `CHANGELOG.md` has the new version section already drafted.\n"
            "- `specsmith audit && specsmith validate --strict` clean on develop.\n\n"
            "## Sequence\n"
            "1. Bump version: `specsmith release <version>`.\n"
            "2. `git add -A && git commit -m 'release: v<version>'`.\n"
            "3. Push develop: `git push origin develop`.\n"
            "4. Wait for CI: `gh run watch`.\n"
            "5. Merge to main: `git checkout main && git merge --ff-only develop`.\n"
            "6. Tag: `git tag -a v<version> -m 'v<version>'`.\n"
            "7. Push: `git push origin main --tags`.\n"
            "8. Release workflow handles PyPI upload + GitHub Release automatically.\n\n"
            "## Rollback\n"
            "If step 7 fails: `git tag -d v<version> && git reset --hard HEAD~1`.\n"
        ),
    ),
    SkillEntry(
        slug="issue-triage",
        name="Issue Triage — classify and prioritise GitHub issues",
        description=(
            "Reads open GitHub issues, deduplicates, labels by type/severity, "
            "and produces a prioritised action list."
        ),
        domain=SkillDomain.GOVERNANCE,
        tags=["github", "issues", "triage", "project-management"],
        prerequisites=["gh", "specsmith"],
        body=(
            "# Issue Triage Skill\n\n"
            "## Sequence\n"
            "1. `gh issue list --state open --limit 100 --json number,title,labels,createdAt`\n"
            "2. Group by type: bug / enhancement / question / docs.\n"
            "3. Detect duplicates: flag issues with >60% title-word overlap.\n"
            "4. Score severity: crash/data-loss = P0; broken feature = P1;"
            " UX = P2; nice-to-have = P3.\n"
            "5. Emit a prioritised table: `| # | Title | Type | Severity | Duplicate of |`\n"
            "6. Ask: 'Which should I implement first this session?'\n\n"
            "## Rules\n"
            "- Never close an issue without fixing it or explicitly marking as won't-fix.\n"
            "- Link PRs: `gh issue develop <number> --checkout` creates a fix branch.\n"
        ),
    ),
]
