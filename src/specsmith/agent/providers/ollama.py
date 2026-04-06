# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Ollama provider — local LLMs via REST API. Zero SDK needed (stdlib only).

Ollama exposes an OpenAI-compatible /v1/chat/completions endpoint.
We use that directly for tool calling. For plain completion, we use
the native /api/chat endpoint.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Iterator
from typing import Any

import os

from specsmith.agent.core import (
    CompletionResponse,
    Message,
    StreamToken,
    Tool,
)


class OllamaProvider:
    """Ollama local LLM provider. Works with llama3.3, qwen2.5, phi4, etc.

    Context length (num_ctx) is controlled by the SPECSMITH_OLLAMA_NUM_CTX
    environment variable. Default 4096; set higher for larger context windows.
    The VS Code extension auto-detects GPU VRAM and sets this appropriately.
    """

    provider_name = "ollama"

    def __init__(
        self,
        model: str = "qwen2.5:14b",
        base_url: str = "http://localhost:11434",
    ) -> None:
        self.model = model
        self._base_url = base_url.rstrip("/")
        # Context window size: env var, default 4096
        self._num_ctx: int = int(os.environ.get("SPECSMITH_OLLAMA_NUM_CTX", "4096"))

    def is_available(self) -> bool:
        try:
            urllib.request.urlopen(  # noqa: S310
                f"{self._base_url}/api/version", timeout=2
            )
            return True
        except Exception:  # noqa: BLE001
            return False

    def complete(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        max_tokens: int = 4096,
    ) -> CompletionResponse:
        # Use OpenAI-compat endpoint if tools are needed
        if tools:
            return self._complete_openai_compat(messages, tools, max_tokens)
        return self._complete_native(messages, max_tokens)

    def _complete_native(self, messages: list[Message], max_tokens: int) -> CompletionResponse:
        payload = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "stream": False,
            "options": {"num_predict": max_tokens, "num_ctx": self._num_ctx},
        }
        data = self._post("/api/chat", payload)
        content = data.get("message", {}).get("content", "")
        return CompletionResponse(
            content=content,
            model=self.model,
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            stop_reason="stop",
        )

    def _complete_openai_compat(
        self, messages: list[Message], tools: list[Tool], max_tokens: int
    ) -> CompletionResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "max_tokens": max_tokens,
            "tools": [t.to_openai_schema() for t in tools],
        }
        data = self._post("/v1/chat/completions", payload)
        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "") or ""
        tool_calls: list[dict[str, Any]] = []
        for tc in choice.get("message", {}).get("tool_calls", []):
            tool_calls.append(
                {
                    "id": tc.get("id", ""),
                    "name": tc.get("function", {}).get("name", ""),
                    "input": json.loads(tc.get("function", {}).get("arguments", "{}")),
                }
            )
        usage = data.get("usage", {})
        return CompletionResponse(
            content=content,
            model=self.model,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            tool_calls=tool_calls,
            stop_reason=choice.get("finish_reason", "stop"),
        )

    def stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        max_tokens: int = 4096,
    ) -> Iterator[StreamToken]:
        payload = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "stream": True,
            "options": {"num_predict": max_tokens},
        }
        req = urllib.request.Request(  # noqa: S310
            f"{self._base_url}/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
            for line in resp:
                line = line.strip()
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    text = chunk.get("message", {}).get("content", "")
                    done = chunk.get("done", False)
                    if text:
                        yield StreamToken(text=text)
                    if done:
                        yield StreamToken(text="", is_final=True)
                        return
                except json.JSONDecodeError:
                    continue

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        req = urllib.request.Request(  # noqa: S310
            f"{self._base_url}{path}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
            result: dict[str, Any] = json.loads(resp.read())
            return result
