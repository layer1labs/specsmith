# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""specsmith agentic client REPL — main runner.

A minimal, cross-platform Python REPL that:
- Wraps any LLM provider (Anthropic, OpenAI, Gemini, Ollama)
- Exposes specsmith commands as native tools
- Loads skills from the project
- Fires hooks at lifecycle events
- Tracks credit spend
- Integrates with the AEE epistemic layer
- Persists session state through LEDGER.md

Inspired by ECC's NanoClaw REPL but native to specsmith and Python.

Special REPL commands (not sent to the LLM):
  /help          — show this help
  /tools         — list available tools
  /skills        — list loaded skills
  /model <name>  — switch model
  /provider <name> — switch provider
  /status        — session status, credits, epistemic health
  /save          — save session to LEDGER.md
  /hooks         — list active hooks
  /clear         — clear conversation history (keeps system prompt)
  exit / quit    — end session
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from specsmith.agent.core import (
    CompletionResponse,
    Message,
    ModelTier,
    Role,
    Tool,
    ToolResult,
)
from specsmith.agent.hooks import HookContext, HookRegistry, HookTrigger
from specsmith.agent.optimizer import OptimizationConfig, OptimizationEngine
from specsmith.agent.skills import Skill, format_skills_context, load_skills
from specsmith.agent.tools import build_tool_registry, get_tool_by_name


@dataclass
class SessionState:
    """Running session state."""

    messages: list[Message] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    start_time: float = field(default_factory=time.time)
    tool_calls_made: int = 0
    project_dir: str = "."
    model_name: str = ""
    provider_name: str = ""

    @property
    def session_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    @property
    def elapsed_minutes(self) -> float:
        return (time.time() - self.start_time) / 60


def build_system_prompt(
    project_dir: str,
    skills: list[Skill],
    include_aee: bool = True,
) -> str:
    """Build the system prompt for the agent session."""
    root = Path(project_dir)

    # Load AGENTS.md if present
    agents_md = ""
    agents_path = root / "AGENTS.md"
    if agents_path.exists():
        content = agents_path.read_text(encoding="utf-8")
        # Only take first 200 lines to save context
        lines = content.splitlines()[:200]
        agents_md = "\n".join(lines)

    # Load spec version from scaffold.yml
    spec_version = "unknown"
    scaffold_path = root / "scaffold.yml"
    if scaffold_path.exists():
        try:
            import yaml

            with open(scaffold_path) as f:
                raw = yaml.safe_load(f) or {}
            spec_version = raw.get("spec_version", "unknown")
        except Exception:  # noqa: BLE001
            pass

    aee_section = ""
    if include_aee:
        aee_section = """
## Applied Epistemic Engineering (AEE)

You operate under AEE principles. Before any significant action:
- Frame: what are you claiming to know?
- Disassemble: what are the assumptions?
- Stress-Test: what could break this?
- Reconstruct: what's the minimal viable belief that survives?

Use `epistemic_audit` for deep knowledge quality checks.
Use `stress_test` to challenge requirements adversarially.
Use `trace_seal` to record significant decisions.
H13: All proposals must state their epistemic boundaries. Hidden assumptions are a stop condition.
"""

    skills_section = format_skills_context(skills, max_tokens=2000)

    governance_text = (
        agents_md or f"Spec version: {spec_version}. AGENTS.md not found — run specsmith audit."
    )

    prompt = f"""You are an AEE-integrated specsmith agent for this project.

## Project Governance
{governance_text}

## Your Role
- You are a proposal generator, not an authority
- Use tools to inspect and modify the project
- Always propose before executing non-trivial changes
- Record work in LEDGER.md after every significant task
- Verify before declaring done
- The ledger + accepted repo state is authority
{aee_section}
{skills_section}

## Quick Commands
Users may type these shortcuts:
- `start` — new session protocol (sync + update check + load state)
- `resume` — resume from LEDGER.md
- `save` — write ledger entry
- `audit` — run specsmith audit
- `commit` — commit with governance check
- `epistemic` — run epistemic audit
"""
    return prompt.strip()


class AgentRunner:
    """The specsmith agentic REPL.

    Usage::

        runner = AgentRunner(project_dir=".", provider_name="anthropic")
        runner.run_interactive()   # starts REPL
        # or
        result = runner.run_task("run audit and fix any issues")
    """

    QUICK_COMMANDS = {
        "start": "Run session start protocol: sync, load AGENTS.md, read last LEDGER.md entries",
        "resume": "Resume from last LEDGER.md entry — summarize state and propose next task",
        "save": "Write a ledger entry summarizing this session's work",
        "audit": "Run specsmith audit --fix",
        "commit": "Run specsmith commit",
        "push": "Run specsmith push",
        "sync": "Run specsmith sync",
        "epistemic": "Run full epistemic audit",
        "stress": "Run stress-test on requirements",
        "status": "Show session status and credit spend",
    }

    def __init__(
        self,
        project_dir: str = ".",
        provider_name: str | None = None,
        model: str | None = None,
        tier: ModelTier = ModelTier.BALANCED,
        stream: bool = True,
        max_tool_iterations: int = 10,
        optimize: bool = False,
        optimization_config: OptimizationConfig | None = None,
    ) -> None:
        self.project_dir = str(Path(project_dir).resolve())
        self._provider_name = provider_name
        self._model = model
        self._tier = tier
        self._stream = stream
        self._max_iterations = max_tool_iterations

        self._provider: Any = None
        self._state = SessionState(project_dir=self.project_dir)
        self._tools: list[Tool] = build_tool_registry(self.project_dir)
        self._skills: list[Skill] = load_skills(Path(self.project_dir))
        self._hooks = HookRegistry()
        self._system_prompt = ""

        # Token / credit optimization engine (opt-in)
        self._optimizer: OptimizationEngine | None = (
            OptimizationEngine(
                config=optimization_config or OptimizationConfig(),
                project_dir=self.project_dir,
            )
            if optimize
            else None
        )

    def _ensure_provider(self) -> None:
        """Lazy-initialize the LLM provider."""
        if self._provider is not None:
            return
        from specsmith.agent.providers import get_provider

        self._provider = get_provider(
            provider_name=self._provider_name,
            model=self._model,
            tier=self._tier,
        )
        self._state.provider_name = self._provider.provider_name
        self._state.model_name = self._provider.model

    def run_interactive(self) -> None:
        """Start the interactive REPL."""
        self._ensure_provider()
        self._system_prompt = build_system_prompt(self.project_dir, self._skills)

        # Fire session start hooks
        ctx = HookContext(
            trigger=HookTrigger.SESSION_START,
            project_dir=self.project_dir,
        )
        results = self._hooks.fire(HookTrigger.SESSION_START, ctx)
        for r in results:
            if r.message:
                self._print(f"\n{r.message}\n")

        self._print_banner()

        while True:
            try:
                user_input = self._prompt()
            except (EOFError, KeyboardInterrupt):
                self._print("\nSession ended.")
                break

            if not user_input.strip():
                continue

            # Handle exit
            if user_input.strip().lower() in ("exit", "quit", "q"):
                self._print("Ending session...")
                self._on_session_end()
                break

            # Handle slash/special commands
            if user_input.startswith("/") or user_input.strip() in self.QUICK_COMMANDS:
                self._handle_meta_command(user_input)
                continue

            # Expand quick commands
            cmd = user_input.strip().lower()
            if cmd in self.QUICK_COMMANDS:
                user_input = self.QUICK_COMMANDS[cmd]

            # Regular LLM turn
            self._agent_turn(user_input)

    def run_task(self, task: str, max_turns: int = 5) -> str:
        """Run a single task non-interactively. Returns final response."""
        self._ensure_provider()
        self._system_prompt = build_system_prompt(self.project_dir, self._skills)
        return self._agent_turn(task, silent=True)

    def _agent_turn(self, user_input: str, silent: bool = False) -> str:
        """Execute one user→agent turn with tool loop."""
        # Add user message
        self._state.messages.append(Message(role=Role.USER, content=user_input))

        final_response = ""
        for _iteration in range(self._max_iterations):
            messages_with_system = [
                Message(role=Role.SYSTEM, content=self._system_prompt)
            ] + self._state.messages

            try:
                response = self._call_provider(messages_with_system, silent=silent)
            except Exception as e:  # noqa: BLE001
                error_msg = f"[Provider error] {e}"
                if not silent:
                    self._print(error_msg)
                return error_msg

            # Update credit tracking
            self._state.total_input_tokens += response.input_tokens
            self._state.total_output_tokens += response.output_tokens
            self._state.total_cost_usd += response.estimated_cost_usd

            if response.content:
                final_response = response.content

            if not response.has_tool_calls:
                # Final response — add to history
                self._state.messages.append(Message(role=Role.ASSISTANT, content=response.content))
                break

            # Process tool calls
            tool_results = self._execute_tool_calls(response.tool_calls, silent=silent)
            self._state.tool_calls_made += len(tool_results)

            # Add assistant message with tool calls
            self._state.messages.append(
                Message(
                    role=Role.ASSISTANT,
                    content=response.content or "",
                    tool_calls=response.tool_calls,
                )
            )

            # Add tool result messages
            for tr in tool_results:
                self._state.messages.append(
                    Message(
                        role=Role.TOOL,
                        content=tr.content,
                        tool_call_id=tr.tool_call_id,
                    )
                )

        return final_response

    def _call_provider(self, messages: list[Message], silent: bool = False) -> CompletionResponse:
        """Call the LLM provider with optimization engine pre/post hooks.

        Streaming is disabled when tools are registered (streaming drops tool_call blocks).
        When an OptimizationEngine is active, pre_call() may return a cache hit
        or transform messages/model/tools before the actual provider call.
        """
        provider: Any = self._provider
        tools = self._tools
        model = str(provider.model)
        provider_name = str(getattr(provider, "provider_name", ""))

        # ── Optimization pre-call ────────────────────────────────────────────
        hint = None
        if self._optimizer is not None:
            hint = self._optimizer.pre_call(messages, tools, model, provider_name)
            if hint.cache_hit:
                # Serve from cache — no API call needed
                if not silent and hint.cached_response:
                    self._print(f"[cache] {hint.cached_response[:60]}...")
                return CompletionResponse(
                    content=hint.cached_response,
                    model=model,
                )
            # Apply routing: switch model if engine suggests cheaper tier
            if hint.model and hint.model != model:
                provider.model = hint.model
            messages = hint.messages
            tools = hint.tools

        use_stream = self._stream and not silent and not tools
        if use_stream:
            accumulated = ""
            for token in provider.stream(messages, tools=None):
                if token.text:
                    self._print(token.text, end="", flush=True)
                    accumulated += token.text
                if token.is_final:
                    self._print()
            response = CompletionResponse(content=accumulated, model=str(provider.model))
        else:
            response = cast(CompletionResponse, provider.complete(messages, tools=tools))
            if not silent and response.content:
                self._print(response.content)

        # ── Optimization post-call ───────────────────────────────────────────
        if self._optimizer is not None and hint is not None:
            self._optimizer.post_call(
                hint,
                response=response.content or "",
                in_tokens=response.input_tokens,
                out_tokens=response.output_tokens,
                cost_usd=response.estimated_cost_usd,
                provider=provider_name,
                model=str(provider.model),
            )
            # Restore original model for next call
            if hint.original_model:
                provider.model = hint.original_model

        return response

    def _execute_tool_calls(
        self, tool_calls: list[dict[str, Any]], silent: bool = False
    ) -> list[ToolResult]:
        """Execute tool calls and return results."""
        results: list[ToolResult] = []
        for tc in tool_calls:
            name = tc.get("name", "")
            call_id = tc.get("id", f"call_{len(results)}")
            inputs = tc.get("input", {})

            if not silent:
                self._print(f"\n[Tool: {name}]")

            # Fire pre_tool hooks
            pre_ctx = HookContext(
                trigger=HookTrigger.PRE_TOOL,
                tool_name=name,
                tool_input=inputs,
                project_dir=self.project_dir,
                session_tokens=self._state.session_tokens,
            )
            pre_results = self._hooks.fire(HookTrigger.PRE_TOOL, pre_ctx)
            blocked, block_msg = self._hooks.has_blocking_result(pre_results)
            if blocked:
                results.append(
                    ToolResult(
                        tool_name=name,
                        tool_call_id=call_id,
                        content=f"[BLOCKED by hook] {block_msg}",
                        error=True,
                    )
                )
                continue

            # Show hook warnings
            for hr in pre_results:
                if hr.action == "warn" and hr.message and not silent:
                    self._print(f"  ⚠ {hr.message}")

            # Find and execute the tool
            tool = get_tool_by_name(self._tools, name)
            start_ms = time.time() * 1000

            if tool and tool.handler:
                try:
                    output = tool.handler(**inputs)
                    error = False
                except Exception as e:  # noqa: BLE001
                    output = f"[ERROR] {e}"
                    error = True
            else:
                output = f"[Unknown tool: {name}]"
                error = True

            elapsed = time.time() * 1000 - start_ms

            if not silent:
                # Truncate long outputs for display
                display = output[:500] + "..." if len(output) > 500 else output
                self._print(f"  → {display}")

            tr = ToolResult(
                tool_name=name,
                tool_call_id=call_id,
                content=output,
                error=error,
                elapsed_ms=elapsed,
            )
            results.append(tr)

            # Fire post_tool hooks
            post_ctx = HookContext(
                trigger=HookTrigger.POST_TOOL,
                tool_name=name,
                tool_input=inputs,
                tool_output=output,
                project_dir=self.project_dir,
            )
            post_results = self._hooks.fire(HookTrigger.POST_TOOL, post_ctx)
            for hr in post_results:
                if hr.message and not silent:
                    self._print(f"  {hr.message}")

        return results

    def _handle_meta_command(self, cmd: str) -> None:
        """Handle slash commands and meta operations."""
        cmd = cmd.strip()
        cmd_lower = cmd.lower()

        if cmd_lower in ("/help", "help"):
            self._print_help()
        elif cmd_lower in ("/tools", "tools"):
            self._print(f"\nAvailable tools ({len(self._tools)}):")
            for t in self._tools:
                self._print(f"  {t.name:25s} {t.description[:60]}")
        elif cmd_lower in ("/skills", "skills"):
            if not self._skills:
                self._print("No skills loaded.")
            else:
                self._print(f"\nLoaded skills ({len(self._skills)}):")
                for s in self._skills:
                    self._print(f"  [{s.domain:12s}] {s.name}: {s.description[:50]}")
        elif cmd_lower in ("/hooks", "hooks"):
            self._print("\nActive hooks:")
            for h in self._hooks._hooks:
                status = "✓" if h.enabled else "✗"
                self._print(f"  {status} [{h.trigger.value:15s}] {h.name}")
        elif cmd_lower in ("/status", "status"):
            self._print_status()
        elif cmd_lower in ("/clear", "clear"):
            # Keep system prompt, clear history
            self._state.messages = []
            self._print("Conversation history cleared.")
        elif cmd_lower.startswith("/model "):
            new_model = cmd[7:].strip()
            if self._provider:
                self._provider.model = new_model
                self._state.model_name = new_model
                self._print(f"Model set to: {new_model}")
        elif cmd_lower.startswith("/skill "):
            skill_name = cmd[7:].strip()
            from specsmith.agent.skills import get_skill_by_name

            skill = get_skill_by_name(self._skills, skill_name)
            if skill:
                self._print(f"\n--- Skill: {skill.name} ---")
                self._print(skill.content[:2000])
                # Inject skill as next context
                self._state.messages.append(
                    Message(
                        role=Role.USER,
                        content=f"[Skill loaded: {skill.name}]\n{skill.content[:3000]}",
                    )
                )
                self._print("\nSkill injected into context.")
            else:
                self._print(f"Skill '{skill_name}' not found.")
        elif cmd_lower in ("/save", "save"):
            self._agent_turn(
                "Please write a LEDGER.md entry summarizing what we've done this session. "
                "Include: what changed, what was verified, open TODOs, and next step."
            )
        else:
            # Unknown slash command — treat as message to LLM
            self._agent_turn(cmd)

    def _on_session_end(self) -> None:
        """Run session-end cleanup."""
        ctx = HookContext(
            trigger=HookTrigger.SESSION_END,
            project_dir=self.project_dir,
            session_tokens=self._state.session_tokens,
        )
        self._hooks.fire(HookTrigger.SESSION_END, ctx)
        self._print_status()

    def _print_banner(self) -> None:
        provider = getattr(self._provider, "provider_name", "?")
        model = getattr(self._provider, "model", "?")
        self._print(
            f"\n[specsmith agent — AEE-integrated]"
            f"\n  Project: {self.project_dir}"
            f"\n  Provider: {provider}/{model}"
            f"\n  Tools: {len(self._tools)} | Skills: {len(self._skills)}"
            f"\n  Type /help for commands, exit to quit\n"
        )

    def _print_status(self) -> None:
        self._print(
            f"\n  Session status:"
            f"\n  Provider:     {self._state.provider_name}/{self._state.model_name}"
            f"\n  Tokens:       {self._state.session_tokens:,} "
            f"(in={self._state.total_input_tokens:,} / out={self._state.total_output_tokens:,})"
            f"\n  Cost:         ${self._state.total_cost_usd:.4f} (estimated)"
            f"\n  Tool calls:   {self._state.tool_calls_made}"
            f"\n  Elapsed:      {self._state.elapsed_minutes:.1f} min\n"
        )

    def _print_help(self) -> None:
        self._print(
            "\nspecsmith agent — slash commands:"
            "\n  /help            — this help"
            "\n  /tools           — list available tools"
            "\n  /skills          — list loaded skills"
            "\n  /skill <name>    — inject a skill into context"
            "\n  /model <name>    — switch model"
            "\n  /status          — session status and credit spend"
            "\n  /hooks           — list active hooks"
            "\n  /clear           — clear conversation history"
            "\n  /save            — write LEDGER.md entry"
            "\n  exit             — end session"
            "\nQuick commands (just type the word):"
        )
        for cmd, desc in self.QUICK_COMMANDS.items():
            self._print(f"  {cmd:15s} — {desc[:60]}")

    def _prompt(self) -> str:
        """Read a line of input from stdin."""
        try:
            return input("\n> ")
        except EOFError:
            raise

    def _print(self, text: str = "", end: str = "\n", flush: bool = False) -> None:
        """Print to stdout."""
        print(text, end=end, flush=flush)
