# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""AgentWorker — runs agent turns in a background QThread.

GUIAgentRunner subclasses AgentRunner and overrides the three output
methods to emit Qt signals instead of printing to stdout:

  _print()               → text_ready signal (system/info text)
  _call_provider()       → llm_chunk signal (assistant response)
  _execute_tool_calls()  → tool_started / tool_finished signals (structured)

AgentWorker wraps a single GUIAgentRunner and runs _agent_turn() in a
QThread so the UI never blocks.
"""

from __future__ import annotations

import json
import time
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal

from specsmith.agent.core import CompletionResponse, Message, Tool, ToolResult
from specsmith.agent.hooks import HookContext, HookTrigger
from specsmith.agent.runner import AgentRunner
from specsmith.agent.tools import get_tool_by_name


class WorkerSignals(QObject):
    """All signals emitted by the agent worker."""

    llm_chunk = Signal(str)  # assistant text (full response, non-streaming)
    tool_started = Signal(str, str)  # (tool_name, args_json)
    tool_finished = Signal(str, str, bool)  # (tool_name, result, is_error)
    tokens_updated = Signal(int, int, float)  # (in_tokens, out_tokens, cost_usd)
    turn_done = Signal()
    error = Signal(str)


class GUIAgentRunner(AgentRunner):
    """AgentRunner subclass that routes output to Qt signals instead of stdout."""

    def __init__(self, signals: WorkerSignals, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._gui_signals = signals

    # ── Suppress all stdout prints ────────────────────────────────────────────

    def _print(self, text: str = "", end: str = "\n", flush: bool = False) -> None:
        pass  # Output goes through signals only

    # ── Emit assistant text as signal ─────────────────────────────────────────

    def _call_provider(self, messages: list[Message], silent: bool = False) -> CompletionResponse:
        from typing import cast

        provider: Any = self._provider
        # Always use non-streaming for GUI (avoids lost tool_calls)
        response = cast("CompletionResponse", provider.complete(messages, tools=self._tools))

        if response.content and not silent:
            self._gui_signals.llm_chunk.emit(response.content)

        # Update token counts from response
        self._state.total_input_tokens += response.input_tokens
        self._state.total_output_tokens += response.output_tokens
        self._state.total_cost_usd += response.estimated_cost_usd

        self._gui_signals.tokens_updated.emit(
            self._state.total_input_tokens,
            self._state.total_output_tokens,
            self._state.total_cost_usd,
        )

        return response

    # Override _agent_turn to avoid double-counting tokens (provider already counts them)
    def _agent_turn(self, user_input: str, silent: bool = False) -> str:  # noqa: ARG002
        """Token-safe agent loop; accumulation is done inside _call_provider."""
        from specsmith.agent.core import Role

        self._state.messages.append(Message(role=Role.USER, content=user_input))

        final_response = ""
        for _iteration in range(self._max_iterations):
            messages_with_system = [
                Message(role=Role.SYSTEM, content=self._system_prompt),
            ] + self._state.messages

            try:
                response = self._call_provider(messages_with_system, silent=False)
            except Exception as e:  # noqa: BLE001
                self._gui_signals.error.emit(f"Provider error: {e}")
                return str(e)

            if response.content:
                final_response = response.content

            if not response.has_tool_calls:
                self._state.messages.append(Message(role=Role.ASSISTANT, content=response.content))
                break

            tool_results = self._execute_tool_calls(response.tool_calls, silent=False)
            self._state.tool_calls_made += len(tool_results)
            self._state.messages.append(
                Message(
                    role=Role.ASSISTANT,
                    content=response.content or "",
                    tool_calls=response.tool_calls,
                ),
            )
            for tr in tool_results:
                self._state.messages.append(
                    Message(role=Role.TOOL, content=tr.content, tool_call_id=tr.tool_call_id),
                )

        return final_response

    # ── Emit structured tool signals ──────────────────────────────────────────

    def _execute_tool_calls(
        self,
        tool_calls: list[dict[str, Any]],
        silent: bool = False,
    ) -> list[ToolResult]:
        results: list[ToolResult] = []
        for tc in tool_calls:
            name = tc.get("name", "")
            call_id = tc.get("id", f"call_{len(results)}")
            inputs = tc.get("input", {})

            if not silent:
                self._gui_signals.tool_started.emit(name, json.dumps(inputs, default=str)[:400])

            # Pre-tool hooks
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
                result_text = f"[BLOCKED by hook] {block_msg}"
                if not silent:
                    self._gui_signals.tool_finished.emit(name, result_text, True)
                results.append(
                    ToolResult(
                        tool_name=name,
                        tool_call_id=call_id,
                        content=result_text,
                        error=True,
                    ),
                )
                continue

            # Execute
            tool: Tool | None = get_tool_by_name(self._tools, name)
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
                self._gui_signals.tool_finished.emit(name, output, error)

            tr = ToolResult(
                tool_name=name,
                tool_call_id=call_id,
                content=output,
                error=error,
                elapsed_ms=elapsed,
            )
            results.append(tr)

            # Post-tool hooks
            post_ctx = HookContext(
                trigger=HookTrigger.POST_TOOL,
                tool_name=name,
                tool_input=inputs,
                tool_output=output,
                project_dir=self.project_dir,
            )
            self._hooks.fire(HookTrigger.POST_TOOL, post_ctx)

        return results


class AgentWorker(QThread):
    """QThread that runs a single agent turn.

    Create a new AgentWorker per user message. Reuse the same
    GUIAgentRunner across turns to preserve conversation history.
    """

    def __init__(
        self,
        runner: GUIAgentRunner,
        user_input: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._runner = runner
        self._user_input = user_input

    def run(self) -> None:
        try:
            self._runner._ensure_provider()
            if not self._runner._system_prompt:
                from specsmith.agent.runner import build_system_prompt

                self._runner._system_prompt = build_system_prompt(
                    self._runner.project_dir,
                    self._runner._skills,
                )
            self._runner._agent_turn(self._user_input, silent=True)
            self._runner._gui_signals.turn_done.emit()
        except Exception as e:  # noqa: BLE001
            self._runner._gui_signals.error.emit(str(e))
            self._runner._gui_signals.turn_done.emit()
