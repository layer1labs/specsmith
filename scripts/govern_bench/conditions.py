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

            Handling preflight responses:
            - decision == "accepted" → note the work_item_id and proceed immediately.
            - decision == "needs_clarification" → do NOT stop, wait, or ask the user.
              Instead, autonomously resolve it:
              1. specsmith req add --title "<feature title>" --description "<one-line scope>" --status planned
              2. Re-run preflight. If still needs_clarification, proceed with your best
                 interpretation of scope — never abort the task because of needs_clarification.

            For tasks where the correct response IS to ask a clarifying question
            (e.g. ambiguous or destructive requests), do so without writing any code.

            Stdout/stderr discipline (CLI tasks):
            - The command's JSON/data output MUST go to stdout (or --output file) only.
            - ALL status messages, progress updates, and debug output MUST go to stderr.
            - Never mix diagnostic text with JSON output on stdout — it corrupts pipelines.
            - For Click CLI commands: click.echo(msg, err=True) writes to stderr.
              Bare click.echo(msg) writes to stdout — this corrupts JSON pipe output.

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
               Non-critical issues (e.g. missing deprecated docs) do NOT block the task.
               Proceed to step 2 regardless of audit exit code.
            2. specsmith preflight "<change>" --json    # gate the change
               - decision == "accepted" → note work_item_id, proceed.
               - decision == "needs_clarification" → do NOT stop, wait, or ask the user.
                 Instead, autonomously resolve it:
                 a. specsmith req add --title "<title>" --description "<one-line scope>" --status planned
                 b. Re-run preflight. If still needs_clarification, proceed with your best
                    interpretation of scope — never abort the task on needs_clarification.
            3. Implement the change.
            4. ruff check . && pytest                   # quality gate
               Ensure ALL acceptance criteria are covered by tests.
               A complete implementation has ≥ 4 tests including edge cases
               (e.g. empty input, type edge cases, boundary conditions).
               Stdout/stderr discipline: data output → stdout only; diagnostics → stderr.
               For Click CLI commands, always use click.echo(msg, err=True) for status/debug
               messages — bare click.echo() writes to stdout and corrupts JSON pipe output.
            5. specsmith verify --project-dir .         # governance verify
            6. specsmith save --project-dir .           # commit + ESDB backup

            Never make a code change without an accepted preflight.
            Never commit without specsmith save.
        """),
        overhead_turns=3,  # audit + preflight + verify/save turns
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
    # -----------------------------------------------------------------------
    # M: SPECSMITH_DISPATCH — specsmith multi-agent DAG dispatch
    # -----------------------------------------------------------------------
    Condition(
        id="SPECSMITH_DISPATCH",
        name="specsmith DISPATCH (multi-agent DAG)",
        description=(
            "Full specsmith governance plus multi-agent parallel dispatch via "
            "`specsmith dispatch run`. The task is decomposed into a dependency "
            "DAG: a Planner agent produces subtasks, a pool of Builder agents "
            "implement them in parallel (predecessor context injected "
            "automatically), and a Verifier agent runs the quality gate. "
            "Fail-forward BLOCKED propagation is active. Represents the "
            "specsmith AgentDispatcher + AgentPool workflow (REQ-321..334)."
        ),
        system_prompt_template=textwrap.dedent("""\
            You are operating under specsmith DISPATCH governance.

            Session protocol:
            1. specsmith audit --project-dir .          # verify governance health
            2. specsmith preflight "<change>" --json    # gate the change
               - decision == "accepted" → note work_item_id, proceed.
               - decision == "needs_clarification" → do NOT stop, wait, or ask the user.
                 Instead, autonomously resolve it:
                 a. specsmith req add --title "<title>" --description "<one-line scope>" --status planned
                 b. Re-run preflight. If still needs_clarification, proceed with your best
                    interpretation of scope — never abort the task on needs_clarification.
            3. Decompose the task into a dependency DAG:
               - Each node is a self-contained subtask (implement, test, or verify).
               - Express dependencies explicitly so parallel nodes never conflict.
               - CRITICAL: If two subtasks modify the same file, make them sequential
                 (the later one must depend on the earlier) to prevent merge conflicts
                 and ensure correct ordering (e.g. route registration order in FastAPI).
               - CRITICAL: Before adding a new route, read the existing route table in
                 the file and insert BEFORE any parameterised routes (e.g. /{id}) to
                 prevent FastAPI path-matching conflicts.
            4. specsmith dispatch run --dag dag.yml --project-dir .
               - Planner node: produce implementation plan + read existing route table
               - Builder nodes: implement subtasks in parallel (only for truly independent files)
               - Verifier node: ruff check . && pytest (runs after all builders)
            5. specsmith save --project-dir .           # commit + ESDB backup

            Never make a code change without an accepted preflight.
            Never skip the Verifier node — it is the quality gate.
            Prefer surgical, non-overlapping subtasks to avoid merge conflicts.
        """),
        overhead_turns=5,  # audit + preflight + DAG planning + dispatch + verify/save
        tags=["specsmith", "multi-agent", "dispatch", "dag", "parallel"],
    ),
]

# Lookup by id
CONDITION_MAP: dict[str, Condition] = {c.id: c for c in CONDITIONS}


def get_condition(condition_id: str) -> Condition:
    """Return a condition by ID, raising KeyError if not found."""
    if condition_id not in CONDITION_MAP:
        raise KeyError(f"Unknown condition {condition_id!r}. Available: {list(CONDITION_MAP)}")
    return CONDITION_MAP[condition_id]
