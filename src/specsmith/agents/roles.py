# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""AG2 agent roles — Planner, Builder, Verifier.

Each function creates a configured ConversableAgent with the right
system prompt, tools, and Ollama model for its role.

Requires: pip install ag2[ollama]
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from specsmith.agents.config import AgentConfig

PLANNER_PROMPT = """\
You are the Planner agent for the specsmith project.

Your job:
1. Understand the task given to you.
2. Inspect the repository structure and relevant files.
3. Generate a concrete execution plan.

Your output must be a structured plan with:
- Task breakdown (ordered steps)
- Assumptions
- Risks
- Acceptance criteria (how to verify success)
- Files likely to be touched

Rules:
- Do NOT make code changes. Only plan.
- Use the filesystem and git tools to inspect the project before planning.
- Be specific — no vague steps like "improve code quality".
- Each step must be a single, concrete action.
"""

BUILDER_PROMPT = """\
You are the Builder agent for the specsmith project.

Your job:
1. Follow the plan provided by the Planner.
2. Make code and documentation changes.
3. Report what you changed.

Your output must include:
- Files changed (with brief description of each change)
- Any issues encountered
- Summary of what was done

Rules:
- Follow the plan step by step.
- Use write_file or patch_file for changes — never output code as text only.
- Preserve existing code style and conventions.
- If a step is unclear, state what you assumed.
"""

VERIFIER_PROMPT = """\
You are the Verifier agent for the specsmith project.

Your job:
1. Run tests to verify changes are correct.
2. Check for regressions.
3. Accept or reject the changes.

Your output must include:
- Tests run and their results (pass/fail)
- Any new failures introduced
- Accept/Reject decision with reasoning

Rules:
- Always run the narrowest relevant tests first.
- If tests fail, report exact failures — do not guess.
- A change is rejected if it introduces any new test failures.
- Report "ACCEPT" or "REJECT" as the final word.
"""


def create_planner(config: AgentConfig, project_dir: str) -> Any:
    """Create the Planner agent with read-only filesystem + git tools."""
    from autogen import ConversableAgent, LLMConfig

    from specsmith.agents.tools.filesystem import list_tree, read_file, search_content
    from specsmith.agents.tools.git import git_branch_info, git_changed_files, git_status

    llm_config = LLMConfig(config.llm_config_dict())

    # Bind project_dir into tool closures
    pd = project_dir

    def _read_file(path: str) -> str:
        return read_file(path, project_dir=pd)

    def _list_tree(directory: str = ".", max_depth: int = 3) -> str:
        return list_tree(directory, max_depth, project_dir=pd)

    def _search(pattern: str, directory: str = ".", glob: str = "") -> str:
        return search_content(pattern, directory, glob, project_dir=pd)

    def _git_status() -> str:
        return git_status(project_dir=pd)

    def _git_changed() -> str:
        return git_changed_files(project_dir=pd)

    def _git_branch() -> str:
        return git_branch_info(project_dir=pd)

    agent = ConversableAgent(
        name="Planner",
        system_message=PLANNER_PROMPT,
        human_input_mode="NEVER",
        llm_config=llm_config,
        functions=[_read_file, _list_tree, _search, _git_status, _git_changed, _git_branch],
    )
    return agent


def create_builder(config: AgentConfig, project_dir: str) -> Any:
    """Create the Builder agent with full filesystem + shell tools."""
    from autogen import ConversableAgent, LLMConfig

    from specsmith.agents.tools.filesystem import list_tree, patch_file, read_file, write_file
    from specsmith.agents.tools.git import git_diff, git_status
    from specsmith.agents.tools.shell import run_project_command

    llm_config = LLMConfig(config.llm_config_dict())
    pd = project_dir

    def _read_file(path: str) -> str:
        return read_file(path, project_dir=pd)

    def _write_file(path: str, content: str) -> str:
        return write_file(path, content, project_dir=pd)

    def _patch_file(path: str, old_text: str, new_text: str) -> str:
        return patch_file(path, old_text, new_text, project_dir=pd)

    def _list_tree(directory: str = ".", max_depth: int = 3) -> str:
        return list_tree(directory, max_depth, project_dir=pd)

    def _run_command(command: str) -> str:
        return run_project_command(command, project_dir=pd)

    def _git_status() -> str:
        return git_status(project_dir=pd)

    def _git_diff() -> str:
        return git_diff(project_dir=pd)

    agent = ConversableAgent(
        name="Builder",
        system_message=BUILDER_PROMPT,
        human_input_mode="NEVER",
        llm_config=llm_config,
        functions=[
            _read_file,
            _write_file,
            _patch_file,
            _list_tree,
            _run_command,
            _git_status,
            _git_diff,
        ],
    )
    return agent


def create_verifier(config: AgentConfig, project_dir: str) -> Any:
    """Create the Verifier agent with test + inspection tools."""
    from autogen import ConversableAgent, LLMConfig

    from specsmith.agents.tools.filesystem import read_file
    from specsmith.agents.tools.git import git_diff, git_status
    from specsmith.agents.tools.shell import run_project_command
    from specsmith.agents.tools.tests import run_unit_tests, summarize_failures

    llm_config = LLMConfig(config.llm_config_dict(model=config.effective_utility_model))
    pd = project_dir

    def _run_tests(test_path: str = "tests/", extra_args: str = "--tb=short -q") -> str:
        return run_unit_tests(test_path, extra_args, project_dir=pd)

    def _summarize(test_output: str) -> str:
        return summarize_failures(test_output)

    def _read_file(path: str) -> str:
        return read_file(path, project_dir=pd)

    def _run_command(command: str) -> str:
        return run_project_command(command, project_dir=pd)

    def _git_status() -> str:
        return git_status(project_dir=pd)

    def _git_diff() -> str:
        return git_diff(project_dir=pd)

    agent = ConversableAgent(
        name="Verifier",
        system_message=VERIFIER_PROMPT,
        human_input_mode="NEVER",
        llm_config=llm_config,
        functions=[_run_tests, _summarize, _read_file, _run_command, _git_status, _git_diff],
    )
    return agent
