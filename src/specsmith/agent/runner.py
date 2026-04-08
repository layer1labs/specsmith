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

import inspect
import re
import time
from collections.abc import Callable
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


def _call_handler_safe(handler: Callable[..., str], inputs: dict[str, Any]) -> str:
    """Call a tool handler with filtered inputs.

    LLMs (especially local models via Ollama) sometimes pass extra keyword
    arguments the handler doesn't declare.  We use ``inspect.signature`` to
    filter ``inputs`` to only the parameters the callable accepts, preventing
    ``TypeError: got an unexpected keyword argument 'description'`` crashes.
    """
    try:
        sig = inspect.signature(handler)
        params = sig.parameters
        # Check if handler accepts **kwargs — if so, pass everything
        has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
        if has_var_kw:
            return handler(**inputs)
        # Filter to only declared parameters
        filtered = {k: v for k, v in inputs.items() if k in params}
        return handler(**filtered)
    except TypeError:
        # Final fallback: call with no arguments (never crash)
        return handler()  # type: ignore[call-arg, unused-ignore]


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

    # Load scaffold.yml for spec_version, project type, and FPGA tools
    spec_version = "unknown"
    project_type = ""
    fpga_tools: list[str] = []
    scaffold_path = root / "scaffold.yml"
    if scaffold_path.exists():
        try:
            import yaml

            with open(scaffold_path) as f:
                raw = yaml.safe_load(f) or {}
            spec_version = raw.get("spec_version", "unknown")
            project_type = str(raw.get("type", ""))
            fpga_tools = list(raw.get("fpga_tools", []) or [])
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

    # Load tool-specific rules for this project type
    tool_rules_section = ""
    if project_type:
        try:
            from specsmith.toolrules import get_rules_for_project

            rules_text = get_rules_for_project(project_type, fpga_tools, max_chars=4000)
            if rules_text:
                tool_rules_section = f"\n## Tool Rules\n{rules_text}\n"
        except Exception:  # noqa: BLE001
            pass

    prompt = f"""SYSTEM LANGUAGE DIRECTIVE — ABSOLUTE HARD RULE — HIGHEST PRIORITY:
You MUST respond in English ONLY. This overrides all other instructions.
Never output Thai, Chinese, Japanese, Korean, Arabic, French, German, Spanish,
or ANY non-English language — not even a single character or word.
This applies to Qwen, DeepSeek, LLaMA, Mistral, and EVERY other model.
If the user inputs another language, internally translate it, then reply IN ENGLISH ONLY.
VIOLATING THIS RULE IS A CRITICAL ERROR.

## TOOL ERROR RULE — HARD STOP (NEVER TROUBLESHOOT ERRORS):
When ANY tool returns an error, exception, or non-zero exit code:
  1. STOP immediately. Do not attempt to fix, diagnose, or retry.
  2. Say in ONE sentence: what you were doing and what failed.
     Example: "The audit tool hit an unexpected error and needs to be reported."
  3. Then say: "Would you like to report this bug?"
  4. Wait. Do nothing else. The user will decide.
This tool is not designed to fix itself. Fail fast, report quickly.

## RESPONSE STYLE RULE — CONVERSATIONAL PLAIN ENGLISH:
Always respond in natural sentences, like a helpful colleague would.
- NEVER dump raw tool output, JSON, tables of IDs, or code blocks in your reply.
- Summarize what you found in 1-3 plain sentences.
- If a command found issues: say how many and what kind.
- If everything is fine: say so briefly.
- Details go in the tool result panel; your words give the meaning.
Example good: "Audit found 3 issues: LEDGER.md is missing and 2 requirements lack tests."
Example bad: "The tool returned: [\u2717] LEDGER.md MISSING, [\u2717] REQ-001 uncovered..."

You are an AEE-integrated specsmith agent for this project.

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
{tool_rules_section}
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

    # Model tier defaults (April 2026) — auto-selected per provider
    _TIER_MODELS: dict[str, dict[str, str]] = {
        "anthropic": {
            "fast": "claude-haiku-4-5",
            "balanced": "claude-sonnet-4-6",
            "powerful": "claude-opus-4-6",
        },
        "openai": {
            "fast": "gpt-4o-mini",
            "balanced": "gpt-4o",
            "powerful": "o4-mini",
        },
        "gemini": {
            "fast": "gemini-2.5-flash",
            "balanced": "gemini-2.5-flash",
            "powerful": "gemini-3.1-pro-preview",
        },
        "ollama": {
            "fast": "llama3.2:latest",
            "balanced": "qwen3:14b",
            "powerful": "qwen3:32b",
        },
    }

    QUICK_COMMANDS = {
        "start": (
            "[RESPOND IN ENGLISH ONLY] "
            "Run session start protocol: sync, load AGENTS.md, read last LEDGER.md entries. "
            "Translate any non-English context internally if needed, but respond only in English."
        ),
        "resume": (
            "[RESPOND IN ENGLISH ONLY] Resume from last LEDGER.md entry"
            " — summarize state and propose next task"
        ),
        "save": "[RESPOND IN ENGLISH ONLY] Write a ledger entry summarizing this session's work",
        "audit": "[RESPOND IN ENGLISH ONLY] Run specsmith audit --fix",
        "commit": "[RESPOND IN ENGLISH ONLY] Run specsmith commit",
        "push": "[RESPOND IN ENGLISH ONLY] Run specsmith push",
        "sync": "[RESPOND IN ENGLISH ONLY] Run specsmith sync",
        "epistemic": "[RESPOND IN ENGLISH ONLY] Run full epistemic audit",
        "stress": "[RESPOND IN ENGLISH ONLY] Run stress-test on requirements",
        "status": "[RESPOND IN ENGLISH ONLY] Show session status and credit spend",
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
        json_events: bool = False,
    ) -> None:
        self.project_dir = str(Path(project_dir).resolve())
        self._provider_name = provider_name
        self._model = model
        self._tier = tier
        self._stream = stream
        self._max_iterations = max_tool_iterations
        self._json_events = json_events

        self._provider: Any = None
        self._state = SessionState(project_dir=self.project_dir)
        self._tools: list[Tool] = build_tool_registry(self.project_dir)
        self._skills: list[Skill] = load_skills(Path(self.project_dir))
        self._hooks = HookRegistry()
        self._system_prompt = ""
        self._hard_stop: bool = False  # set True when a critical tool crash is detected

        # Execution profile — loaded from scaffold.yml at session start
        from specsmith import profiles

        self._profile = profiles.load_from_scaffold(self.project_dir)

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

    # Characters in common CJK / Thai / Arabic Unicode blocks
    _NON_ASCII_BLOCKS = re.compile(
        r"[\u0600-\u06FF"  # Arabic
        r"\u0E00-\u0E7F"  # Thai
        r"\u3000-\u9FFF"  # CJK Unified Ideographs + punctuation + kana
        r"\uAC00-\uD7AF"  # Korean Hangul
        r"\uF900-\uFAFF]"  # CJK Compatibility
    )

    def _has_non_english(self, text: str) -> bool:
        """Return True if text contains a significant proportion of non-English script."""
        if not text:
            return False
        hits = len(self._NON_ASCII_BLOCKS.findall(text))
        return hits > 5 and (hits / max(len(text), 1)) > 0.05

    # ---- Critical error patterns that trigger a hard stop ----
    _CRITICAL_PATTERNS = re.compile(
        r"Traceback \(most recent call last\)"
        r"|\[ERROR\]"
        r"|UnicodeDecodeError"
        r"|UnicodeEncodeError"
        r"|ImportError"
        r"|ModuleNotFoundError"
        r"|AttributeError: '"
        r"|TypeError: unsupported"
        r"|PermissionError"
        r"|OSError: "
        r"|RuntimeError: ",
        re.IGNORECASE,
    )

    @staticmethod
    def _is_critical_error(output: str) -> bool:
        """Return True if tool output indicates an unexpected crash.

        Normal governance failures (audit issues, missing files) are NOT
        critical — only Python exceptions and import errors are.
        """
        if not output:
            return False
        # Non-zero exit alone is expected (e.g. audit found issues).
        # Only flag when a Python exception signature is present.
        return AgentRunner._CRITICAL_PATTERNS.search(output) is not None

    def _collect_diagnostics(self, tool_name: str, output: str) -> dict:
        """Collect diagnostic context for a crash report."""
        import platform as _platform
        import sys as _sys

        from specsmith import __version__ as _ver

        project_type = ""
        try:
            import yaml as _yaml

            sf = Path(self.project_dir) / "scaffold.yml"
            if sf.exists():
                raw = _yaml.safe_load(sf.read_text(encoding="utf-8")) or {}
                project_type = str(raw.get("type", ""))
        except Exception:  # noqa: BLE001
            pass

        # Classify repo: Python exceptions from specsmith module → specsmith CLI
        # Extension/bridge errors would never reach here (they don’t use this runner)
        repo = "specsmith"

        # Extract first meaningful error line for the summary
        summary = output.strip().splitlines()
        _err_pat = re.compile(r"\w+Error|Exception|RuntimeError")
        summary_line = next(
            (ln.strip() for ln in reversed(summary) if _err_pat.match(ln.strip())),
            summary[0] if summary else "Unknown error",
        )[:200]

        return {
            "tool": tool_name,
            "summary": summary_line,
            "detail": output[:4000],
            "specsmith_version": _ver,
            "python_version": _sys.version.split()[0],
            "os_info": f"{_platform.system()} {_platform.release()}",
            "project_type": project_type,
            "repo": repo,
        }

    def _agent_turn(self, user_input: str, silent: bool = False) -> str:
        """Execute one user→agent turn with tool loop."""
        # Inject a lightweight English-only reminder into every user message.
        # This is the most reliable way to keep local models (Qwen, DeepSeek) on track
        # because many fine-tunes treat the instruction prefix as a per-turn directive.
        _ENG_PFXS = ("[ENGLISH ONLY]", "[RESPOND IN ENGLISH", "[LANG:EN]")
        if not any(user_input.startswith(p) for p in _ENG_PFXS):
            user_input = "[LANG:EN] " + user_input
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
                    if self._json_events:
                        self._emit_event(type="error", message=error_msg)
                    else:
                        self._print(error_msg)
                return error_msg

            # Update credit tracking
            self._state.total_input_tokens += response.input_tokens
            self._state.total_output_tokens += response.output_tokens
            self._state.total_cost_usd += response.estimated_cost_usd

            # Emit token update event
            if self._json_events and not silent:
                self._emit_event(
                    type="tokens",
                    in_tokens=self._state.total_input_tokens,
                    out_tokens=self._state.total_output_tokens,
                    cost_usd=self._state.total_cost_usd,
                )

            if response.content:
                final_response = response.content

            if not response.has_tool_calls:
                # Non-English correction: if response appears to be in another language,
                # issue a single correction turn rather than showing the wrong-language response.
                if response.content and self._has_non_english(response.content) and _iteration == 0:
                    correction = (
                        "[LANG:EN] CRITICAL: Your last response was in a non-English language. "
                        "You MUST respond in English ONLY. Please re-answer in English."
                    )
                    self._state.messages.append(
                        Message(role=Role.ASSISTANT, content=response.content)
                    )
                    self._state.messages.append(Message(role=Role.USER, content=correction))
                    # Continue the loop to get an English response
                    continue
                # Final response — add to history
                self._state.messages.append(Message(role=Role.ASSISTANT, content=response.content))
                break

            # Process tool calls
            self._hard_stop = False  # reset before each batch
            tool_results = self._execute_tool_calls(response.tool_calls, silent=silent)
            self._state.tool_calls_made += len(tool_results)

            # Fail fast: a critical tool crash was detected — break immediately
            # without sending the error back to the LLM (which would try to fix it).
            if self._hard_stop:
                break

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

        # Emit turn-done event
        if self._json_events and not silent:
            self._emit_event(
                type="turn_done",
                total_tokens=self._state.session_tokens,
                cost_usd=self._state.total_cost_usd,
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

        use_stream = self._stream and not silent and not tools and not self._json_events
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
                if self._json_events:
                    self._emit_event(type="llm_chunk", text=response.content)
                else:
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
        """Execute tool calls and return results.

        Sets ``self._hard_stop = True`` if any tool produces a critical error
        (Python exception, import error, etc.) so the caller can break the
        agentic loop immediately without sending the error to the LLM.
        """
        from specsmith import profiles as _profiles

        results: list[ToolResult] = []
        for tc in tool_calls:
            name = tc.get("name", "")
            call_id = tc.get("id", f"call_{len(results)}")
            inputs = tc.get("input", {})

            if not silent:
                if self._json_events:
                    self._emit_event(type="tool_started", name=name, args=inputs)
                else:
                    self._print(f"\n[Tool: {name}]")

            # ── Execution profile enforcement ──────────────────────────────────
            tool_ok, tool_reason = _profiles.check_tool_allowed(self._profile, name)
            if not tool_ok:
                blocked_msg = f"[BLOCKED by profile '{self._profile.name}'] {tool_reason}"
                if not silent:
                    if self._json_events:
                        self._emit_event(type="tool_blocked", name=name, reason=tool_reason)
                    else:
                        self._print(f"  ✗ {blocked_msg}")
                results.append(
                    ToolResult(
                        tool_name=name,
                        tool_call_id=call_id,
                        content=blocked_msg,
                        error=True,
                    )
                )
                continue

            # For run_command: check the command string
            if name == "run_command" and "command" in inputs:
                cmd_ok, cmd_reason = _profiles.check_command_allowed(
                    self._profile, str(inputs["command"])
                )
                if not cmd_ok:
                    blocked_msg = f"[BLOCKED by profile '{self._profile.name}'] {cmd_reason}"
                    if not silent:
                        if self._json_events:
                            self._emit_event(
                                type="tool_blocked",
                                name=name,
                                command=inputs["command"],
                                reason=cmd_reason,
                            )
                        else:
                            self._print(f"  ✗ {blocked_msg}")
                    results.append(
                        ToolResult(
                            tool_name=name,
                            tool_call_id=call_id,
                            content=blocked_msg,
                            error=True,
                        )
                    )
                    continue

            # For write_file: check file-write permission and size
            if name == "write_file" and "content" in inputs:
                write_ok, write_reason = _profiles.check_write_allowed(
                    self._profile, str(inputs["content"])
                )
                if not write_ok:
                    blocked_msg = f"[BLOCKED by profile '{self._profile.name}'] {write_reason}"
                    if not silent:
                        if self._json_events:
                            self._emit_event(type="tool_blocked", name=name, reason=write_reason)
                        else:
                            self._print(f"  ✗ {blocked_msg}")
                    results.append(
                        ToolResult(
                            tool_name=name,
                            tool_call_id=call_id,
                            content=blocked_msg,
                            error=True,
                        )
                    )
                    continue

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
                    output = _call_handler_safe(tool.handler, inputs)
                    error = False
                except Exception as e:  # noqa: BLE001
                    output = f"[ERROR] {e}"
                    error = True
            else:
                output = f"[Unknown tool: {name}]"
                error = True

            elapsed = time.time() * 1000 - start_ms

            # ---- Fail-fast: detect critical errors -------------------------
            # A critical error is an unexpected crash (Python exception, import
            # failure, etc.) — NOT a normal governance failure (audit issues,
            # missing files) which the LLM should describe conversationally.
            if self._is_critical_error(output):
                self._hard_stop = True
                diagnostics = self._collect_diagnostics(name, output)
                if not silent and self._json_events:
                    self._emit_event(type="tool_crash", **diagnostics)
                elif not silent:
                    self._print(
                        f"\n[CRITICAL ERROR in {name}] "
                        f"{diagnostics['summary']}\n"
                        "Session stopped. Please report this bug."
                    )

            if not silent:
                if self._json_events:
                    self._emit_event(type="tool_finished", name=name, result=output, is_error=error)
                else:
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
        if self._json_events:
            self._emit_event(
                type="ready",
                provider=provider,
                model=model,
                project_dir=self.project_dir,
                tools=len(self._tools),
                skills=len(self._skills),
            )
        else:
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
            # In json_events mode suppress the prompt string so stdout stays pure JSON
            return input("" if self._json_events else "\n> ")
        except EOFError:
            raise

    def _print(self, text: str = "", end: str = "\n", flush: bool = False) -> None:
        """Print to stdout; in json_events mode emit a system event instead."""
        if self._json_events:
            if text.strip():
                self._emit_event(type="system", message=text.strip())
        else:
            print(text, end=end, flush=flush)

    def _emit_event(self, **kwargs: Any) -> None:
        """Emit a newline-delimited JSON event to stdout (json_events mode only)."""
        import json
        import sys

        print(json.dumps(kwargs), flush=True, file=sys.stdout)  # noqa: T201
