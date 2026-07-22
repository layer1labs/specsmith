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
# The twelve benchmark conditions (6 original + 6 real-world tool styles)
# ---------------------------------------------------------------------------

# ── New condition prose blocks ────────────────────────────────────────────

_CURSOR_RULES = textwrap.dedent("""\
    ---
    description: Python project coding rules
    globs: ["**/*.py", "**/tests/**"]
    alwaysApply: true
    ---
    # Project Rules (Cursor)

    ## Code style
    - Python 3.11+; use built-in generics (list[X], dict[X, Y], X | None).
    - All functions and public methods require type annotations.
    - Line length ≤ 100 chars. Ruff-enforced.

    ## Testing
    - New behaviour MUST have at least one pytest test.
    - Tests live in tests/. Use pytest fixtures, not unittest.
    - Run `ruff check .` and `pytest` before declaring done.

    ## Safety
    - Never hardcode secrets or credentials.
    - Never delete files without reading them first.
    - Prefer surgical edits over wholesale rewrites.
""")

_COPILOT_INSTRUCTIONS = textwrap.dedent("""\
    <!-- .github/copilot-instructions.md -->
    # GitHub Copilot Instructions

    ## Project context
    This is a Python project using FastAPI / Click. Existing tests must not
    break. All changes must pass `ruff check .` and `pytest`.

    ## When writing code
    - Match the existing code style and naming conventions.
    - Write tests for every new function or changed behaviour.
    - Prefer standard library solutions over adding new dependencies.
    - Check whether a similar utility already exists before writing new code.

    ## When asked to delete or restructure
    - Read the relevant files first.
    - Confirm scope with the user if the request affects more than 3 files.
    - Preserve any functionality that is not explicitly in scope.

    ## Completion signal
    Only call done() after `ruff check .` AND `pytest` both return exit 0.
""")

_CODEX_AGENTS_MD = textwrap.dedent("""\
    # AGENTS.md (OpenAI Codex CLI)

    ## Session bootstrap
    Before writing code:
    1. Read the relevant source files with read_file.
    2. Run `pytest` to understand the current test baseline.
    3. Confirm your planned change in one sentence.

    ## Implementation
    - Make incremental changes. One logical change per write_file call.
    - After each write_file, run `ruff check .` to catch syntax errors early.
    - Keep the public API surface stable unless explicitly asked to change it.

    ## Verification (REQUIRED)
    Before calling done():
    - `ruff check .` → exit 0
    - `pytest`        → exit 0, all tests pass
    - Review your changes against the acceptance criteria one more time.

    ## Scope discipline
    - Do not refactor code outside the task scope.
    - Do not add dependencies not already in pyproject.toml.
    - If the task description is ambiguous, ask one clarifying question.
""")

_CLINE_RULES = textwrap.dedent("""\
    # .clinerules (Cline / Claude Dev)

    ## Always
    - Read a file before modifying it.
    - Run `ruff check .` after every write_file.
    - Run the full test suite before declaring a task complete.
    - Ask a clarifying question if the task has ambiguous scope or
      would delete/overwrite more than one file at once.

    ## Never
    - Delete a file without first reading it and confirming the deletion
      is within scope.
    - Make a change that silently removes functionality (even deprecated
      functionality) without noting it in your explanation.
    - Skip writing tests because "the change is small."

    ## Defaults
    - Python code: follow PEP 8, use type hints, docstrings on public API.
    - Test files: pytest, located in tests/, one file per module under test.
    - All new code must pass `ruff check .` with zero violations.
""")

_AGILE_TDD = textwrap.dedent("""\
    # Agile / BDD-TDD Development Protocol

    You are implementing a user story using test-driven development.
    Follow the RED → GREEN → REFACTOR cycle.

    ## Before writing implementation code
    1. Write the failing test(s) first (RED).
       - Express each acceptance criterion as a `pytest` test.
       - Use Given / When / Then naming: `test_given_X_when_Y_then_Z`.
       - Run `pytest` to confirm the test fails for the right reason.

    2. Write the minimum implementation to make the tests pass (GREEN).
       - Do not over-engineer. Make it work, then make it right.

    3. Refactor (REFACTOR).
       - Clean up duplication and naming without changing behaviour.
       - Re-run `pytest` to confirm still green.

    ## Done criteria
    - All acceptance criteria have a corresponding test.
    - `pytest` passes with zero failures.
    - `ruff check .` passes with zero violations.
    - No test was deleted or weakened to make the suite pass.
""")

_AIDER_CONVENTIONS = textwrap.dedent("""\
    # CONVENTIONS.md (Aider)

    ## Architecture
    - FastAPI routes live in app/main.py; business logic in app/services.py.
    - Pydantic models (request/response schemas) live in app/models.py.
    - Middleware lives in app/middleware/.
    - Do not mix route handling with business logic.

    ## Naming
    - Functions: snake_case. Classes: PascalCase. Constants: UPPER_SNAKE_CASE.
    - Test functions: test_<what>_<expected_outcome>.
    - Route handlers: <verb>_<resource> (e.g. list_todos, create_todo).

    ## Change discipline
    - One concern per commit. Do not bundle unrelated changes.
    - Run `ruff check .` before every change to establish a clean baseline.
    - After implementing, run `pytest -x` (stop on first failure).
    - Do not change test files to make failing tests pass; fix the
      implementation instead.

    ## Dependencies
    - Do not add new packages. Use what is already in pyproject.toml.
""")

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
        name="specsmith LIGHT (slim AEE gate)",
        description=(
            "The harness runs an isolated deterministic preflight before the model. "
            "Accepted requirement and test IDs are injected as a compact evidence contract. "
            "Ambiguous or destructive work short-circuits without an implementation call."
        ),
        system_prompt_template=textwrap.dedent("""\
            Follow the injected AEE evidence contract.
            Implement only the linked requirement; preserve unrelated behavior.
            Treat unverified assumptions as unknown, not fact.
            Add or update the smallest tests needed for the changed behavior.
            Do not claim completion unless the available validators pass.
        """),
        overhead_turns=0,  # deterministic controller work consumes no LLM turn
        tags=["specsmith", "preflight-only", "light"],
    ),
    # -----------------------------------------------------------------------
    # F: SPECSMITH_FULL — complete session (preflight + verify + save)
    # -----------------------------------------------------------------------
    Condition(
        id="SPECSMITH_FULL",
        name="specsmith FULL (adaptive AEE)",
        description=(
            "A slim AEE controller performs isolated preflight and post-change verification. "
            "The model receives only requirement, linked-test, confidence, and uncertainty "
            "evidence; repository ceremony remains outside the token path."
        ),
        system_prompt_template=textwrap.dedent("""\
            Follow the injected AEE evidence contract.
            Scope every change to the linked requirement and preserve unrelated behavior.
            Distinguish evidence, inference, and unknowns; inspect before assuming.
            Add focused tests for changed behavior and relevant boundaries.
            Call done when the implementation and focused tests are ready. The deterministic
            completion gate runs every missing linked validator without another model turn;
            do not call run_command or run_validator before done. Repair any failures the
            gate returns, then call done again. Run a validator directly only when the gate's
            failure output is insufficient to diagnose the repair.
        """),
        overhead_turns=0,  # preflight/verify are deterministic controller operations
        tags=["specsmith", "full-governance", "primary"],
    ),
    # =======================================================================
    # Real-world tool style conditions (G–L)
    # These represent what agents receive when developers use popular
    # AI coding tools without additional governance scaffolding.
    # =======================================================================
    # -----------------------------------------------------------------------
    # G: CURSOR_RULES — Cursor .cursor/rules MDX format
    # -----------------------------------------------------------------------
    Condition(
        id="CURSOR_RULES",
        name="Cursor rules (.cursor/rules/*.mdc)",
        description=(
            "Cursor's native per-project rules format. Rules are MDX files "
            "with frontmatter (description, globs, alwaysApply) injected "
            "as additional context when matching files are in scope. "
            "Represents what Cursor users get with well-maintained rules files."
        ),
        system_prompt_template=_CURSOR_RULES,
        overhead_turns=0,
        tags=["cursor", "ide-native", "context-injection", "real-world"],
    ),
    # -----------------------------------------------------------------------
    # H: COPILOT_INSTRUCTIONS — GitHub Copilot .github/copilot-instructions.md
    # -----------------------------------------------------------------------
    Condition(
        id="COPILOT_INSTRUCTIONS",
        name="GitHub Copilot (.github/copilot-instructions.md)",
        description=(
            "GitHub Copilot's native custom instructions file. "
            "Injected as a system prompt supplement for all Copilot interactions. "
            "Represents the GitHub Copilot / Copilot Workspace baseline "
            "when a developer has configured their repository correctly."
        ),
        system_prompt_template=_COPILOT_INSTRUCTIONS,
        overhead_turns=0,
        tags=["github-copilot", "ide-native", "context-injection", "real-world"],
    ),
    # -----------------------------------------------------------------------
    # I: CODEX_AGENTS_MD — OpenAI Codex CLI AGENTS.md format
    # -----------------------------------------------------------------------
    Condition(
        id="CODEX_AGENTS_MD",
        name="OpenAI Codex CLI (AGENTS.md)",
        description=(
            "OpenAI Codex CLI reads AGENTS.md files hierarchically. "
            "Includes explicit verification steps (run tests, check lint) "
            "and scope discipline rules. Represents a well-configured "
            "Codex CLI or similar agentic-coding tool baseline."
        ),
        system_prompt_template=_CODEX_AGENTS_MD,
        overhead_turns=0,
        tags=["codex-cli", "openai", "agents-md", "real-world"],
    ),
    # -----------------------------------------------------------------------
    # J: CLINE_RULES — Cline .clinerules format
    # -----------------------------------------------------------------------
    Condition(
        id="CLINE_RULES",
        name="Cline / Claude Dev (.clinerules)",
        description=(
            "Cline (formerly Claude Dev) reads .clinerules for project-specific "
            "conventions. Emphasises read-before-modify, ask-before-delete, "
            "and test-always patterns. One of the most widely deployed "
            "agentic IDE extensions."
        ),
        system_prompt_template=_CLINE_RULES,
        overhead_turns=0,
        tags=["cline", "claude-dev", "ide-native", "real-world"],
    ),
    # -----------------------------------------------------------------------
    # K: AGILE_TDD — BDD Given/When/Then test-first methodology
    # -----------------------------------------------------------------------
    Condition(
        id="AGILE_TDD",
        name="Agile BDD / TDD (Given-When-Then)",
        description=(
            "Applies a test-driven development protocol: write failing tests "
            "first (RED), implement (GREEN), refactor. Each acceptance criterion "
            "maps to a named pytest case. Comparable to structured AI-assisted "
            "TDD workflows used in agile engineering teams."
        ),
        system_prompt_template=_AGILE_TDD,
        overhead_turns=1,  # test-writing turn before implementation
        tags=["tdd", "bdd", "agile", "test-first", "real-world"],
    ),
    # -----------------------------------------------------------------------
    # L: AIDER_CONVENTIONS — Aider CONVENTIONS.md format
    # -----------------------------------------------------------------------
    Condition(
        id="AIDER_CONVENTIONS",
        name="Aider (CONVENTIONS.md)",
        description=(
            "Aider reads CONVENTIONS.md for architecture patterns, naming "
            "conventions, and change discipline rules. Represents Aider's "
            "recommended project setup where the developer has invested in "
            "a well-structured conventions document."
        ),
        system_prompt_template=_AIDER_CONVENTIONS,
        overhead_turns=0,
        tags=["aider", "conventions-md", "real-world"],
    ),
]

# DISPATCH is intentionally excluded until the benchmark invokes the real
# dispatcher.  A prompt that merely describes a DAG is not a valid measurement
# of multi-agent execution and must not appear in published comparisons.
EXPERIMENTAL_CONDITIONS: list[Condition] = []

# Lookup by id
CONDITION_MAP: dict[str, Condition] = {c.id: c for c in CONDITIONS + EXPERIMENTAL_CONDITIONS}


def get_condition(condition_id: str) -> Condition:
    """Return a condition by ID, raising KeyError if not found."""
    if condition_id not in CONDITION_MAP:
        raise KeyError(f"Unknown condition {condition_id!r}. Available: {list(CONDITION_MAP)}")
    return CONDITION_MAP[condition_id]
