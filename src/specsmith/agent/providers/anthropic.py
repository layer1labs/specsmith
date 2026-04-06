# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Anthropic (Claude) provider for the specsmith agentic client.

Requires: pip install specsmith[anthropic]
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from specsmith.agent.core import (
    CompletionResponse,
    Message,
    Role,
    StreamToken,
    Tool,
    ToolResult,
)


class AnthropicProvider:
    """Anthropic Claude provider. Supports claude-opus-4-5, claude-sonnet-4-5, claude-haiku-4-5.

    Set ``prompt_caching=True`` (default) to add ``cache_control: {"type": "ephemeral"}``
    to the system message, enabling Anthropic\'s 50-90% cached-read discount on
    repeated system-prompt tokens.
    """

    provider_name = "anthropic"

    def __init__(
        self,
        model: str = "claude-sonnet-4-5",
        api_key: str = "",
        prompt_caching: bool = True,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._prompt_caching = prompt_caching
        self._client: Any = None
        self._ensure_client()

    def _ensure_client(self) -> None:
        try:
            import anthropic

            self._client = anthropic.Anthropic(api_key=self._api_key or None)
        except ImportError as e:
            from specsmith.agent.core import ProviderNotAvailable

            raise ProviderNotAvailable("anthropic", "anthropic") from e

    def is_available(self) -> bool:
        try:
            import anthropic  # noqa: F401

            return bool(self._api_key)
        except ImportError:
            return False

    def complete(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        max_tokens: int = 4096,
    ) -> CompletionResponse:
        system_msg = ""
        filtered: list[dict[str, Any]] = []
        for m in messages:
            if m.role == Role.SYSTEM:
                system_msg = m.content
            else:
                filtered.append(m.to_dict())

        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": filtered,
        }
        if system_msg:
            # Prompt caching: mark system prompt as cacheable.
            # Anthropic charges only 0.1x the base input price for cache reads
            # (90% discount), making this the single highest-ROI optimisation.
            if self._prompt_caching:
                kwargs["system"] = [
                    {
                        "type": "text",
                        "text": system_msg,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
            else:
                kwargs["system"] = system_msg
        if tools:
            kwargs["tools"] = [t.to_anthropic_schema() for t in tools]

        response = self._client.messages.create(**kwargs)

        content = ""
        tool_calls: list[dict[str, Any]] = []
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text
            elif hasattr(block, "type") and block.type == "tool_use":
                tool_calls.append(
                    {
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )

        return CompletionResponse(
            content=content,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            tool_calls=tool_calls,
            stop_reason=response.stop_reason or "end_turn",
        )

    def stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        max_tokens: int = 4096,
    ) -> Iterator[StreamToken]:
        system_msg = ""
        filtered: list[dict[str, Any]] = []
        for m in messages:
            if m.role == Role.SYSTEM:
                system_msg = m.content
            else:
                filtered.append(m.to_dict())

        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": filtered,
        }
        if system_msg:
            if self._prompt_caching:
                kwargs["system"] = [
                    {
                        "type": "text",
                        "text": system_msg,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
            else:
                kwargs["system"] = system_msg
        if tools:
            kwargs["tools"] = [t.to_anthropic_schema() for t in tools]

        with self._client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield StreamToken(text=text)
        yield StreamToken(text="", is_final=True)

    def build_tool_result_message(self, results: list[ToolResult]) -> Message:
        """Build a message containing tool results for Anthropic's format."""
        content: list[dict[str, Any]] = []
        for r in results:
            content.append(
                {
                    "type": "tool_result",
                    "tool_use_id": r.tool_call_id,
                    "content": r.content,
                    "is_error": r.error,
                }
            )
        return Message(role=Role.USER, content=str(content))
