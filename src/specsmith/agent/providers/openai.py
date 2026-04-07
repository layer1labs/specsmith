# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""OpenAI provider (also works for any OpenAI-compatible API, including Ollama).

Requires: pip install specsmith[openai]

For Ollama: set base_url="http://localhost:11434/v1" and api_key="ollama"
For other OpenAI-compatible servers: set OPENAI_BASE_URL environment variable
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from specsmith.agent.core import (
    CompletionResponse,
    Message,
    StreamToken,
    Tool,
)


def _is_o_series(model: str) -> bool:
    """Return True for OpenAI o-series reasoning models (o1, o3, o4, o3-mini, o4-mini …).

    These models:
    - Use the ``developer`` role instead of ``system`` for instructions.
    - Accept ``max_completion_tokens`` (preferred over the deprecated ``max_tokens``).
    """
    import re
    return bool(re.match(r"o[0-9]", model.lower()))


class OpenAIProvider:
    """OpenAI-compatible provider. Supports GPT-4o, o-series, and any compatible API."""

    provider_name = "openai"

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str = "",
        base_url: str = "",
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._base_url = base_url
        self._client: Any = None
        self._ensure_client()

    def _ensure_client(self) -> None:
        try:
            import openai

            kwargs: dict[str, Any] = {"api_key": self._api_key or "placeholder"}
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._client = openai.OpenAI(**kwargs)
        except ImportError as e:
            from specsmith.agent.core import ProviderNotAvailable

            raise ProviderNotAvailable("openai", "openai") from e

    def is_available(self) -> bool:
        try:
            import openai  # noqa: F401

            return bool(self._api_key or self._base_url)
        except ImportError:
            return False

    def _adapt_messages(
        self, messages: list[Message]
    ) -> list[dict[str, Any]]:
        """Convert messages to API format, mapping system→developer for o-series."""
        from specsmith.agent.core import Role
        adapted: list[dict[str, Any]] = []
        for m in messages:
            d = m.to_dict()
            # o1+ models use 'developer' role for system instructions
            if m.role == Role.SYSTEM and _is_o_series(self.model):
                d = {**d, "role": "developer"}
            adapted.append(d)
        return adapted

    def complete(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        max_tokens: int = 4096,
    ) -> CompletionResponse:
        msgs = self._adapt_messages(messages)
        # o-series: use max_completion_tokens (includes reasoning tokens)
        token_key = "max_completion_tokens" if _is_o_series(self.model) else "max_tokens"
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": msgs,
            token_key: max_tokens,
        }
        if tools:
            kwargs["tools"] = [t.to_openai_schema() for t in tools]
            kwargs["tool_choice"] = "auto"

        response = self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        content = choice.message.content or ""

        tool_calls: list[dict[str, Any]] = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                import json

                tool_calls.append(
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "input": json.loads(tc.function.arguments or "{}"),
                    }
                )

        usage = response.usage
        return CompletionResponse(
            content=content,
            model=response.model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            tool_calls=tool_calls,
            stop_reason=choice.finish_reason or "stop",
        )

    def stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        max_tokens: int = 4096,
    ) -> Iterator[StreamToken]:
        msgs = self._adapt_messages(messages)
        token_key = "max_completion_tokens" if _is_o_series(self.model) else "max_tokens"
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": msgs,
            token_key: max_tokens,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = [t.to_openai_schema() for t in tools]

        stream = self._client.chat.completions.create(**kwargs)
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield StreamToken(text=delta.content)
        yield StreamToken(text="", is_final=True)
