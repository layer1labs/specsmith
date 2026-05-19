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
        slug="chronomemory-esdb",
        name="ChronoMemory ESDB — epistemic state database (v0.1.1)",
        description=(
            "Full API reference and critical rules for chronomemory v0.1.1: "
            "ChronoStore WAL, query module, ContextPackCompiler, DepGraph, "
            "token metrics, skills system, and Rust acceleration."
        ),
        domain=SkillDomain.GOVERNANCE,
        tags=[
            "esdb", "chronomemory", "epistemics", "wal", "persistence",
            "context-pack", "query", "dep-graph", "rollback", "token-metrics",
            "aee", "anti-hallucination",
        ],
        prerequisites=["chronomemory"],
        body=("""\
# ChronoMemory ESDB Skill (v0.1.1)

EpiStemic State Database for Layer1Labs agentic projects.
WAL at `<root>/.chronomemory/events.wal` — NDJSON, append-only, SHA-256 chained.

## Imports
```python
from chronomemory import (
    ChronoStore, ChronoRecord, WalEvent, open_store,   # Core
    EsdbBridge,                                         # Backward-compat bridge
    DepGraph, DependencyEdge,                           # Phase 2: dep graph
    RollbackReport, invalidate,                         # Phase 2: rollback
    ContextPack, ContextPackCompiler, ContextPackEntry, # Phase 2: context packs
    RustChronoStore, RustRecord, RUST_BACKEND,          # Phase 3: Rust (optional)
)
from chronomemory import query    # 18 ESDB §23 query functions
from chronomemory import metrics  # token metrics + skill system

# Or via specsmith.esdb namespace (preferred within specsmith code):
from specsmith.esdb import ChronoStore, query, metrics, ContextPackCompiler
```

## Critical rules — never break these
1. `dependencies = []` in pyproject.toml must stay empty — chronomemory is stdlib-only.
2. Never physically delete WAL records — always `store.delete(id)` (tombstone only).
3. Use `query.what_is_known(store)` not `store.query(rag_filter=True)` for LLM context
   — the former excludes infra record kinds (edge, rollback_event, token_metric, skill_run).
4. Governance status (`defined`/`implemented`) ≠ ESDB status (`active`/`tombstone`)
   — never conflate when migrating from `.specsmith/*.json`.
5. WAL is append-only NDJSON — one JSON object per line, SHA-256 chained.

## Core write/read
```python
with ChronoStore(project_root) as store:
    store.upsert(ChronoRecord(
        id="FACT-001", kind="fact",
        label="CPSC projection is the sole validity authority",
        source_type="observed", confidence=0.99,
        evidence=["CPSC-Specification.md §9"],
    ))
    store.delete("OLD-001")     # tombstone only — never physically removes
    store.chain_valid()         # verify SHA-256 WAL integrity

# For LLM context — always use query.what_is_known (rule #3)
with ChronoStore(project_root) as store:
    beliefs = query.what_is_known(store)   # active, conf>=0.6, no infra records
    hypotheses = query.what_requires_reverification(store)
    done = query.has_this_work_been_done(store, "migrate flat JSON")
```

## Backward-compat bridge
```python
bridge = EsdbBridge(project_root)
bridge.status().backend  # "ChronoStore WAL" or "json"
store.migrate_from_json(Path(project_root) / ".specsmith")
```

## Dependency graph
```python
g = DepGraph(store=store)
g.add_edge("HYP-001", "FACT-001", "depends_on")
# Valid edge types: assumes contradicts depends_on derived_from
#                  generated_from invalidates supports supersedes validated_by
```

## Epistemic rollback
```python
report = store.invalidate("FACT-001", "reason", dep_graph=g)
# Cascades depends_on/derived_from → status=hypothesis, confidence halved
```

## Context pack for LLM injection
```python
pack = ContextPackCompiler(store).compile(
    task_id="TASK-42", goal="fix ruff errors", token_budget=4096
)
context_json = pack.to_dict()  # inject into LLM context
# Excludes: tombstone/invalidated/hypothesis, conf<0.6, infra kinds, over-budget
```

## Query API (18 functions — all degrade gracefully without dep_graph)
```python
query.what_is_known(store)                   # active beliefs, no infra kinds
query.what_requires_reverification(store)    # hypotheses needing confirmation
query.has_this_work_been_done(store, label)  # bool — check prior decisions
query.why_do_we_believe(store, "FACT-001")   # evidence chain for a record
query.what_skills_apply(store, "run lint")   # skills matching task label
query.what_changed_since(store, seq)         # records written after WAL seq N
query.what_confidence_collapsed(store, 0.6)  # hypotheses below threshold
query.what_can_agent_do_next(store, goal)    # unblocked action records
query.what_should_agent_not_do(store)        # stop_condition records
query.is_this_action_duplicate(store, label) # alias for has_this_work_been_done
```

## Token metrics
```python
metrics.record_token_metric(
    store, task_id="TASK-1",
    context_tokens=512, input_tokens=256, output_tokens=128,
    tool_calls=4, elapsed_ms=1800, success=True,
)
metrics.token_efficiency_report(store)  # {tokens_per_success, avg_tool_calls, ...}
```

## Skills system
```python
# Register a skill
store.upsert(ChronoRecord(
    id="SKILL-ruff", kind="skill", label="ruff linter", confidence=0.9,
    data={"activation": ["lint", "ruff", "python"]},
))
metrics.find_skills(store, "run ruff lint")    # returns matching skill records
metrics.record_skill_run(store, "SKILL-ruff",  # writes a skill_run WAL record
    success=True, tokens_used=150, output={"errors": 0})
```

## Rust acceleration (Phase 3)
```python
from chronomemory import RUST_BACKEND
# False by default — requires: pip install maturin
#   maturin develop --manifest-path crates/chronomemory-py/Cargo.toml
# When True, RustChronoStore and RustRecord are available.
print("Rust backend:", RUST_BACKEND)
```
"""),
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
