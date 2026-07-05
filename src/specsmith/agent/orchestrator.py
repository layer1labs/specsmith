from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from specsmith.agent.dispatch.result import DispatchSummary

try:
    import autogen
    from autogen import ConversableAgent, GroupChat, GroupChatManager
except ImportError:
    # Handle gracefully if autogen is not installed
    autogen = None
    ConversableAgent = object
    GroupChat = object
    GroupChatManager = object

from specsmith.agent.tools import AVAILABLE_TOOLS

NEXUS_NAME = "Nexus"


@dataclass
class TaskResult:
    """Structured outcome of an orchestrator run (REQ-091).

    The Nexus REPL's bounded-retry harness (REQ-087) consumes this directly
    instead of synthesizing equilibrium from a boolean cast of a free-form
    summary string. Each field is a contract:

    - ``equilibrium``: True when the orchestrator considers the work done
      and the verifier did not reject the change set.
    - ``confidence``: numeric verifier/orchestrator confidence in the result
      (0.0 - 1.0). Used by ``execute_with_governance`` to compare against the
      preflight ``confidence_target`` before retrying.
    - ``summary``: human-readable summary; matches the existing Nexus output
      contract (REQ-073).
    - ``files_changed``: paths the orchestrator believes it modified.
    - ``test_results``: free-form dict (e.g. {"passed": int, "failed": int}).
    """

    equilibrium: bool = False
    confidence: float = 0.0
    summary: str = ""
    files_changed: list[str] = field(default_factory=list)
    test_results: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "equilibrium": self.equilibrium,
            "confidence": self.confidence,
            "summary": self.summary,
            "files_changed": list(self.files_changed),
            "test_results": dict(self.test_results),
        }


class Orchestrator:
    """Nexus orchestrator: AG2-based local-first agentic development runtime.

    Specsmith governs all work; Nexus only executes within governance bounds.
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:8000/v1",
        model: str = "Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int8",
        api_key: str = "specsmith-local-key",
    ):
        if autogen is None:
            raise ImportError(
                "ag2 (autogen) is not installed. Please install it via "
                "`pip install ag2[ollama]` or `pip install pyautogen`.",
            )

        self.llm_config = {
            "config_list": [
                {
                    "model": model,
                    "api_key": api_key,
                    "base_url": endpoint,
                },
            ],
            "temperature": 0.0,
        }

        self.setup_agents()
        self.register_tools()

    def setup_agents(self):
        """Initialize all required AG2 agents."""
        self.planner = ConversableAgent(
            name="PlannerAgent",
            system_message=(
                "You are the Planner. Break down the user's task into "
                "manageable steps. Once steps are generated, pass to "
                "CodeAgent or ShellAgent to execute."
            ),
            llm_config=self.llm_config,
        )

        self.shell_agent = ConversableAgent(
            name="ShellAgent",
            system_message=(
                "You execute shell commands using the run_shell tool "
                "to inspect the environment or run tests."
            ),
            llm_config=self.llm_config,
        )

        self.code_agent = ConversableAgent(
            name="CodeAgent",
            system_message="You write, read, and patch code files using the available tools.",
            llm_config=self.llm_config,
        )

        self.reviewer_agent = ConversableAgent(
            name="ReviewerAgent",
            system_message=(
                "You review code changes and test results to ensure they "
                "meet the requirements. Provide feedback or approval."
            ),
            llm_config=self.llm_config,
        )

        self.memory_agent = ConversableAgent(
            name="MemoryAgent",
            system_message="You store and retrieve project facts and context from the .repo-index.",
            llm_config=self.llm_config,
        )

        self.git_agent = ConversableAgent(
            name="GitAgent",
            system_message="You handle git status, diffs, and staging changes.",
            llm_config=self.llm_config,
        )

        self.human_proxy = ConversableAgent(
            name="HumanProxyAgent",
            system_message=(
                "You are the human proxy. You provide approval for actions "
                "and relay task outcomes to the user."
            ),
            llm_config=False,
            human_input_mode="ALWAYS",
        )

        # Tools execution node
        self.executor = ConversableAgent(
            name="Executor",
            system_message="Execute the tools and return the results.",
            llm_config=False,
            human_input_mode="NEVER",
        )

    def register_tools(self):
        """Register tools so multiple callers can invoke them but the executor
        only registers each tool once (avoids AG2 "is being overridden" warnings).
        """
        agents_with_tools = [self.shell_agent, self.code_agent, self.git_agent, self.memory_agent]
        for tool in AVAILABLE_TOOLS:
            # Register the tool's LLM-side signature on every caller agent
            for agent in agents_with_tools:
                agent.register_for_llm(
                    name=tool.__name__,
                    description=tool.__doc__ or tool.__name__,
                )(tool)
            # Register the actual execution function ONCE on the executor.
            self.executor.register_for_execution(name=tool.__name__)(tool)

    def run_task(self, task: str, *, use_dag: bool = False) -> TaskResult:
        """Run a task through the agent orchestration group (REQ-091).

        When *use_dag* is True the task is decomposed into a TaskDAG and
        dispatched via AgentDispatcher (REQ-322).  On DAGValidationError the
        method falls back to the existing flat GroupChat path with a warning.
        The Orchestrator remains the sole entry point in both paths (REQ-321).

        Returns a :class:`TaskResult` so the Nexus REPL's bounded-retry
        harness can compare ``confidence`` against the preflight target and
        retry on non-equilibrium outcomes without inventing signal.
        """
        if use_dag:
            try:
                summary = self.run_dispatch(task)
                return TaskResult(
                    equilibrium=summary.equilibrium,
                    confidence=summary.confidence,
                    summary=(
                        f"DAG dispatch complete: {len(summary.completed)} completed, "
                        f"{len(summary.failed)} failed, {len(summary.blocked)} blocked."
                    ),
                    files_changed=[f for r in summary.completed for f in r.files_changed],
                )
            except Exception as dag_err:  # noqa: BLE001
                import warnings

                warnings.warn(
                    f"DAG dispatch failed ({dag_err!s}), falling back to flat GroupChat.",
                    stacklevel=2,
                )
        groupchat = GroupChat(
            agents=[
                self.human_proxy,
                self.planner,
                self.shell_agent,
                self.code_agent,
                self.reviewer_agent,
                self.memory_agent,
                self.git_agent,
                self.executor,
            ],
            messages=[],
            max_round=50,
        )
        manager = GroupChatManager(groupchat=groupchat, llm_config=self.llm_config)

        # Format enforcement for the output
        formatting_instructions = """
You MUST produce your final response in this exact format:
Plan:
Commands to run:
Files changed:
Diff:
Test results:
Next action:
"""
        initial_message = f"Task: {task}\n{formatting_instructions}"
        chat_result = self.human_proxy.initiate_chat(manager, message=initial_message)

        return self._build_task_result(chat_result, task)

    def run_dispatch(
        self,
        task: str,
        *,
        max_workers: int = 4,
        planner_output: str | list | None = None,
        project_root: str | None = None,
    ) -> DispatchSummary:
        """Decompose *task* into a TaskDAG and dispatch via AgentDispatcher.

        Always uses the DAG path (REQ-321: Orchestrator is the sole entry).
        Returns a :class:`DispatchSummary` with per-node outcomes.
        """
        import os
        from pathlib import Path

        from specsmith.agent.dispatch import (
            AgentDispatcher,
            AgentPool,
            EventEmitter,
            TaskDAGBuilder,
        )

        root = Path(project_root) if project_root else Path(os.getcwd())

        # If no planner_output provided, ask PlannerAgent to decompose the task
        # into a structured JSON list of TaskNode dicts (best-effort; falls back
        # to single-node DAG if the LLM is unavailable or returns invalid JSON).
        if planner_output is None:
            planner_output = self._call_planner(task)

        dag = TaskDAGBuilder.build(task, planner_output=planner_output)
        pool = AgentPool(self.llm_config, max_workers=max_workers)
        emitter = EventEmitter(root, dag.dag_id)
        dispatcher = AgentDispatcher(dag, pool, emitter, project_root=root, max_workers=max_workers)
        return dispatcher.run()

    def _call_planner(self, task: str) -> str | None:
        """Ask the PlannerAgent to decompose *task* into a JSON array of TaskNode dicts.

        Sends a single-turn prompt to the PlannerAgent that asks it to emit a
        structured JSON plan.  Returns the raw response string (which
        ``TaskDAGBuilder._parse_nodes`` will extract the JSON array from), or
        ``None`` if the LLM is unavailable or times out (falling back to
        single-node DAG).

        The prompt format instructs the LLM to output a JSON array like::

            [
              {"id": "arch", "title": "Design API", "role": "architect", "depends_on": []},
              {"id": "impl", "title": "Implement the API", "role": "coder", "depends_on": ["arch"]},
              {"id": "test", "title": "Write tests", "role": "tester", "depends_on": ["arch"]}
            ]
        """
        try:
            from autogen import ConversableAgent  # type: ignore[import]

            proxy = ConversableAgent(
                name="PlannerProxy",
                system_message="You collect the planner's JSON output and return it.",
                llm_config=False,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=1,
            )

            planner_prompt = (
                f"Decompose this task into a JSON array of agent work nodes.\n"
                f"Task: {task}\n\n"
                f"Output ONLY a JSON array. Each element must have:\n"
                f'  - "id": unique snake_case slug\n'
                f'  - "title": human-readable description\n'
                f'  - "role": one of coder | reviewer | tester | '
                f"architect | researcher | embedded-coder\n"
                f'  - "depends_on": list of node ids that must finish first ([] for root nodes)\n\n'
                f"The array MUST be a valid DAG with no cycles. Maximum 8 nodes."
            )

            result = proxy.initiate_chat(
                self.planner,
                message=planner_prompt,
                max_turns=1,
            )
            return getattr(result, "summary", None) or None
        except Exception:  # noqa: BLE001 — fallback to single-node DAG on any error
            return None

    def _build_task_result(self, chat_result: Any, task: str) -> TaskResult:
        """Translate the AG2 chat result into a structured TaskResult.

        AG2's ``initiate_chat`` returns a ``ChatResult`` whose ``summary`` is
        the last assistant message and whose ``chat_history`` lists every
        turn. We parse the Nexus output contract out of the summary and feed
        the structured signal through :func:`specsmith.agent.verifier.score`
        (REQ-108) so ``equilibrium`` and ``confidence`` reflect real test /
        ruff / mypy state instead of a hardcoded heuristic. When the LLM
        returns no contract sections at all we fall back to the previous
        conservative defaults so behaviour stays the same on degraded runs.
        """
        from specsmith.agent.verifier import report_from_chat_sections, score

        summary = ""
        if chat_result is not None:
            summary = getattr(chat_result, "summary", "") or ""
            if not isinstance(summary, str):
                summary = str(summary)

        sections = self._parse_output_contract(summary)

        files_changed: list[str] = []
        files_section = sections.get("files_changed", "")
        for line in files_section.splitlines():
            cleaned = line.strip("-* \t")
            if cleaned and cleaned.lower() != "none":
                files_changed.append(cleaned)

        test_results: dict[str, Any] = {}
        tests_section = sections.get("test_results", "").strip()
        if tests_section:
            test_results["raw"] = tests_section

        # REQ-108: derive confidence and equilibrium from the real verifier
        # signal rather than guessing from the presence of contract sections.
        if sections:
            report = report_from_chat_sections(sections, files_changed=files_changed)
            verdict = score(report, confidence_target=0.7)
            confidence = verdict.confidence
            # Treat "reached the next_action section" as a soft floor for
            # equilibrium so the harness still distinguishes a structurally
            # complete contract from a totally empty one.
            equilibrium = verdict.equilibrium or (
                "next_action" in sections and report.has_changes and report.test_failed == 0
            )
        else:
            equilibrium = False
            confidence = 0.4 if summary else 0.0

        return TaskResult(
            equilibrium=equilibrium,
            confidence=confidence,
            summary=summary,
            files_changed=files_changed,
            test_results=test_results,
        )

    @staticmethod
    def _parse_output_contract(text: str) -> dict[str, str]:
        """Parse the Nexus output contract sections out of a free-form summary.

        Returns a dict keyed by lowercase, underscore-joined section names
        (``plan``, ``commands_to_run``, ``files_changed``, ``diff``,
        ``test_results``, ``next_action``). Missing sections are simply
        absent; the parser is intentionally tolerant of small format drift.
        """
        if not text:
            return {}
        canonical = (
            "Plan:",
            "Commands to run:",
            "Files changed:",
            "Diff:",
            "Test results:",
            "Next action:",
        )
        lines = text.splitlines()
        sections: dict[str, list[str]] = {}
        current: str | None = None
        for line in lines:
            stripped = line.strip()
            matched = next((s for s in canonical if stripped.startswith(s)), None)
            if matched:
                current = matched.rstrip(":").lower().replace(" ", "_")
                remainder = stripped[len(matched) :].strip()
                sections.setdefault(current, [])
                if remainder:
                    sections[current].append(remainder)
            elif current is not None:
                sections[current].append(line)
        return {key: "\n".join(value).strip() for key, value in sections.items()}
