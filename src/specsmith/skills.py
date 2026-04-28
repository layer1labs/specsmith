# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Skill marketplace — discover and install reusable agent skill files.

specsmith ships a small built-in catalog of community skills (Markdown
SKILL.md files) that any user can drop into their project's
``.agents/skills/`` directory. The catalog is keyed by slug; each entry
has a name, description, tags, and the SKILL.md body. Future versions
may federate to a remote registry behind a ``--registry-url`` flag, but
the built-in catalog is sufficient for the 1.0-class user experience:
``specsmith skill search testing`` lists matching skills,
``specsmith skill install verifier`` copies the SKILL.md into the
project, and ``specsmith skill list`` shows what's already installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SkillEntry:
    """A single skill catalog entry."""

    slug: str
    name: str
    description: str
    tags: list[str] = field(default_factory=list)
    body: str = ""


# ---------------------------------------------------------------------------
# Built-in catalog
# ---------------------------------------------------------------------------

CATALOG: list[SkillEntry] = [
    SkillEntry(
        slug="verifier",
        name="Verifier — five-gate verification",
        description=(
            "Runs the standard five-gate verification loop: ruff, mypy, pytest, "
            "pip-audit, and the project's own audit/validate. Halts with a clear "
            "report at the first failing gate."
        ),
        tags=["verification", "ci", "python"],
        body=(
            "# Verifier Skill\n\n"
            "## When to use\n"
            "Run this skill before committing any change.\n\n"
            "## Gates (in order)\n"
            "1. `ruff check .` — lint clean.\n"
            "2. `ruff format --check src tests` — format clean.\n"
            "3. `mypy src/` — type-check clean.\n"
            "4. `pytest -q` — tests pass.\n"
            "5. `specsmith audit && specsmith validate` — governance clean.\n\n"
            "Halt at the first failing gate and surface its output verbatim.\n"
        ),
    ),
    SkillEntry(
        slug="planner",
        name="Planner — propose-then-execute",
        description=(
            "Forces the agent to emit a Plan block before any tool call. Each "
            "plan step is recorded with explicit success criteria so the user "
            "can review the approach before any code changes."
        ),
        tags=["planning", "governance"],
        body=(
            "# Planner Skill\n\n"
            "## Protocol\n"
            "1. Emit a Plan block listing each intended step with a success "
            "criterion.\n"
            "2. Wait for user confirmation when the profile is `safe`.\n"
            "3. Execute steps one at a time, updating plan_step status as each "
            "completes or fails.\n"
            "4. Never run tool calls outside the plan.\n"
        ),
    ),
    SkillEntry(
        slug="diff-reviewer",
        name="Diff Reviewer — surface changes for approval",
        description=(
            "After every change set, emit a `diff` block per modified file and "
            "wait for an Accept / Reject decision before committing. Comments "
            "are fed into the next retry as additional context."
        ),
        tags=["review", "diff", "governance"],
        body=(
            "# Diff Reviewer Skill\n\n"
            "## When to use\n"
            "Any task that modifies files.\n\n"
            "## Protocol\n"
            "1. Emit one `diff` block per file in `Files changed`.\n"
            "2. Wait for `diff_decision` events on stdin (accept / reject / "
            "comment).\n"
            "3. If any diff is rejected, fold the comment into the next harness "
            "retry.\n"
            "4. Only commit once every diff has been accepted.\n"
        ),
    ),
    SkillEntry(
        slug="onboarding-coach",
        name="Onboarding Coach — guided first session",
        description=(
            "Walks a brand-new user through a project: scaffold check, "
            "REQUIREMENTS.md tour, AGENTS.md tour, suggested next preflight "
            "utterance. Pairs with `specsmith doctor --onboarding`."
        ),
        tags=["onboarding", "documentation"],
        body=(
            "# Onboarding Coach Skill\n\n"
            "## Sequence\n"
            "1. Run `specsmith doctor --onboarding` and surface any failing "
            "step.\n"
            "2. Read AGENTS.md and summarise the project's hard rules in 5 "
            "bullets.\n"
            "3. List the top 5 P1 requirements from REQUIREMENTS.md.\n"
            "4. Suggest one preflight utterance the user can run next.\n"
        ),
    ),
    SkillEntry(
        slug="release-pilot",
        name="Release Pilot — gitflow release cut",
        description=(
            "Drives a full gitflow release: develop -> main fast-forward, "
            "version bump, CHANGELOG entry, tag, PyPI publish, GitHub release. "
            "Refuses to run if CI is not green."
        ),
        tags=["release", "vcs", "automation"],
        body=(
            "# Release Pilot Skill\n\n"
            "## Preconditions\n"
            "- `gh pr list --state open` returns 0 open PRs.\n"
            "- All CI checks on develop are SUCCESS.\n"
            "- CHANGELOG.md has the new version entry already drafted.\n\n"
            "## Sequence\n"
            "1. Bump `pyproject.toml` version.\n"
            "2. Commit and push to develop.\n"
            "3. Fast-forward main from develop.\n"
            "4. Create annotated tag.\n"
            "5. Push tags. Release workflow handles PyPI + GitHub Release.\n"
        ),
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def search(query: str) -> list[SkillEntry]:
    """Case-insensitive substring search across slug, name, description, tags."""
    needle = query.strip().lower()
    if not needle:
        return list(CATALOG)
    matches: list[SkillEntry] = []
    for entry in CATALOG:
        haystack = " ".join(
            [entry.slug, entry.name, entry.description, " ".join(entry.tags)]
        ).lower()
        if needle in haystack:
            matches.append(entry)
    return matches


def get(slug: str) -> SkillEntry | None:
    """Return the catalog entry for ``slug`` or ``None``."""
    for entry in CATALOG:
        if entry.slug == slug:
            return entry
    return None


def installed_skills(project_dir: Path) -> list[Path]:
    """Return SKILL.md files installed under ``.agents/skills/``."""
    base = project_dir / ".agents" / "skills"
    if not base.is_dir():
        return []
    return sorted(p for p in base.iterdir() if p.is_file() and p.suffix == ".md")


def install(slug: str, project_dir: Path, *, force: bool = False) -> Path:
    """Copy the catalog skill into ``project_dir/.agents/skills/<slug>.md``.

    Raises ``FileExistsError`` if the file is already present and ``force``
    is ``False``. Raises ``KeyError`` if the slug is unknown.
    """
    entry = get(slug)
    if entry is None:
        raise KeyError(f"Unknown skill: {slug}")
    base = project_dir / ".agents" / "skills"
    base.mkdir(parents=True, exist_ok=True)
    target = base / f"{slug}.md"
    if target.exists() and not force:
        raise FileExistsError(f"Already installed: {target}. Pass --force to overwrite.")
    target.write_text(entry.body, encoding="utf-8")
    return target
