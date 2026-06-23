"""Condition definitions for the governance efficiency benchmark.

Each condition represents a distinct governance/scaffolding strategy.
A condition defines:
  - system_prompt: the governance context prepended to every agent call
  - setup_hook: callable run once before tasks execute (e.g. specsmith init)
  - teardown_hook: callable run once after tasks complete
  - overhead_turns: expected number of governance turns per task (for analysis)

Conditions are ordered from least to most governance overhead so that a
sequential sweep from index 0 produces a legible comparison table.
"""

from __future__ import annotations

import textwrap
from collections.abc import Callable
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Shared prose blocks reused across conditions
# ---------------------------------------------------------------------------

_CLAUDE_MD_CONTENT = textwrap.dedent("""\
    # Project Guidelines

    - Write clean, well-tested Python.
    - All changes must pass `ruff check .` and `pytest` before commit.
    - Follow existing project conventions.
    - Do not break existing tests.
    - Prefer small, focused commits.
""")

_BMAD_BLUEPRINT = textwrap.dedent("""\
    # BMAD Blueprint

    ## Project Vision
    Deliver a working, tested feature that satisfies the acceptance criteria
    below without introducing regressions.

    ## Milestone
    M1 – Feature implementation complete, all tests green.

    ## Artifacts Required
    - Implementation code
    - Unit tests covering the new behaviour
    - Updated docstrings / inline comments where appropriate

    ## Definition of Done
    - [ ] All existing tests still pass
    - [ ] New feature tests pass
    - [ ] `ruff check .` reports zero violations
    - [ ] No hard-coded secrets or debug prints remain
""")

_OPENSPEC_HEADER = textwrap.dedent("""\
    # REQUIREMENTS.md (OpenSpec format)

    ## Project
    See the project README for context.

    ## Requirement: TASK-SPECIFIC-REQ
    **Status:** planned
    **Priority:** P0
    **Description:** {task_description}
    **Acceptance Criteria:**
    {acceptance_criteria}

    ## Constraints
    - Must not break existing tests.
    - Must satisfy `ruff check .` with zero violations.
    - Must include at least one new unit test covering the new behaviour.
""")


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class Condition:
    """A governance/scaffolding condition for benchmarking."""

    id: str
    name: str
    description: str
    system_prompt_template: str  # may contain {task_description}, {acceptance_criteria}
    overhead_turns: int = 0  # expected extra governance turns beyond the raw task turn
    setup_hook: Callable[..., None] | None = None
    teardown_hook: Callable[..., None] | None = None
    tags: list[str] = field(default_factory=list)

    def render_prompt(self, task_description: str = "", acceptance_criteria: str = "") -> str:
        """Render the system prompt with task-specific context."""
        try:
            return self.system_prompt_template.format(
                task_description=task_description,
                acceptance_criteria=acceptance_criteria,
            )
        except KeyError:
            return self.system_prompt_template


# ---------------------------------------------------------------------------
# The six canonical benchmark conditions
# ---------------------------------------------------------------------------

CONDITIONS: list[Condition] = [
    # -----------------------------------------------------------------------
    # A: UNGOVERNED — raw agent with just the task prompt
    # -----------------------------------------------------------------------
    Condition(
        id="UNGOVERNED",
        name="Ungoverned (raw agent)",
        description=(
            "No governance context. The agent receives only the task prompt. "
            "Represents the baseline 'vibe coding' experience."
        ),
        system_prompt_template="",
        overhead_turns=0,
        tags=["baseline", "no-governance"],
    ),

    # -----------------------------------------------------------------------
    # B: CONTEXT_ONLY — CLAUDE.md / AGENTS.md static injection
    # -----------------------------------------------------------------------
    Condition(
        id="CONTEXT_ONLY",
        name="Context injection only (CLAUDE.md/AGENTS.md)",
        description=(
            "A static CLAUDE.md (or AGENTS.md) file is prepended as the system "
            "prompt. This is the default Claude Code / Copilot experience when "
            "the developer has written project instructions but uses no scaffolding tool."
        ),
        system_prompt_template=_CLAUDE_MD_CONTENT,
        overhead_turns=0,
        tags=["context-injection", "claude-md"],
    ),

    # -----------------------------------------------------------------------
    # C: BMAD_STYLE — Blueprint→Milestone→Artifact→Delivery structured prompting
    # -----------------------------------------------------------------------
    Condition(
        id="BMAD_STYLE",
        name="BMAD-style structured prompting",
        description=(
            "Uses the BMAD (Blueprint → Milestone → Artifact → Delivery) framework. "
            "A blueprint document and milestone definition are injected before the task. "
            "Comparable to the open-source BMAD-METHOD agentic workflow."
        ),
        system_prompt_template=_BMAD_BLUEPRINT,
        overhead_turns=1,  # one blueprint-review turn
        tags=["bmad", "structured-prompting", "external-scaffold"],
    ),

    # -----------------------------------------------------------------------
    # D: OPENSPEC_STYLE — structured REQUIREMENTS.md context
    # -----------------------------------------------------------------------
    Condition(
        id="OPENSPEC_STYLE",
        name="OpenSpec-style requirements document",
        description=(
            "A structured REQUIREMENTS.md in OpenSpec format is injected. "
            "The task is expressed as a formal requirement with acceptance criteria. "
            "Comparable to GitHub Spec Kit / OpenSpec agentic scaffolding."
        ),
        system_prompt_template=_OPENSPEC_HEADER,
        overhead_turns=0,
        tags=["openspec", "requirements-driven", "external-scaffold"],
    ),

    # -----------------------------------------------------------------------
    # E: SPECSMITH_LIGHT — preflight gate only
    # -----------------------------------------------------------------------
    Condition(
        id="SPECSMITH_LIGHT",
        name="specsmith LIGHT (preflight only)",
        description=(
            "The agent must pass `specsmith preflight` before writing any code. "
            "The preflight result (requirement_ids, work_item_id, confidence_target) "
            "is injected into the agent context. No verify or save steps."
        ),
        system_prompt_template=textwrap.dedent("""\
            You are operating under specsmith governance (LIGHT mode).

            Before writing any code you must call:
                specsmith preflight "<describe the change>" --json

            If the decision is "needs_clarification", surface the instruction
            to the user and wait. If "accepted", note the work_item_id and proceed.

            After implementation:
            - Run: ruff check .
            - Run: pytest
            Both must pass with zero violations before the task is complete.
        """),
        overhead_turns=1,  # preflight turn
        tags=["specsmith", "preflight-only", "light"],
    ),

    # -----------------------------------------------------------------------
    # F: SPECSMITH_FULL — complete session (preflight + verify + save)
    # -----------------------------------------------------------------------
    Condition(
        id="SPECSMITH_FULL",
        name="specsmith FULL (preflight + verify + save)",
        description=(
            "Full specsmith session workflow: "
            "audit → preflight → implement → verify → save. "
            "The agent context includes the GOVERNANCE ANCHOR from `specsmith checkpoint`. "
            "This is the condition being benchmarked as the primary specsmith proposition."
        ),
        system_prompt_template=textwrap.dedent("""\
            You are operating under full specsmith governance.

            Session protocol:
            1. specsmith audit --project-dir .          # verify health
            2. specsmith preflight "<change>" --json    # gate the change
               - decision == "accepted" → note work_item_id, proceed
               - decision == "needs_clarification" → surface instruction, wait
            3. Implement the change.
            4. ruff check . && pytest                   # quality gate
            5. specsmith verify --project-dir .         # governance verify
            6. specsmith save --project-dir .           # commit + ESDB backup

            Never make a code change without an accepted preflight.
            Never commit without specsmith save.
        """),
        overhead_turns=3,  # audit + preflight + verify/save turns
        tags=["specsmith", "full-governance", "primary"],
    ),
]

# Lookup by id
CONDITION_MAP: dict[str, Condition] = {c.id: c for c in CONDITIONS}


def get_condition(condition_id: str) -> Condition:
    """Return a condition by ID, raising KeyError if not found."""
    if condition_id not in CONDITION_MAP:
        raise KeyError(
            f"Unknown condition {condition_id!r}. "
            f"Available: {list(CONDITION_MAP)}"
        )
    return CONDITION_MAP[condition_id]
