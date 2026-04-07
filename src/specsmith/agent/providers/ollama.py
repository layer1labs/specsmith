# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Ollama provider — local LLMs via REST API. Zero SDK needed (stdlib only).

Ollama exposes an OpenAI-compatible /v1/chat/completions endpoint.
We use that directly for tool calling. For plain completion, we use
the native /api/chat endpoint.
"""

from __future__ import annotations

import json
import os
import urllib.request
from collections.abc import Iterator
from typing import Any

from specsmith.agent.core import (
    CompletionResponse,
    Message,
    StreamToken,
    Tool,
)


def _is_tool_fallback_error(exc: BaseException) -> bool:
    """Return True when an exception signals that tool calling is not supported.

    Covers HTTP 400 (Bad Request from the OpenAI-compat endpoint), 405 (Method
    Not Allowed), and error messages that explicitly mention lack of support.
    """
    msg = str(exc).lower()
    return (
        "400" in msg
        or "405" in msg
        or "bad request" in msg
        or "does not support" in msg
        or "tool" in msg and "not supported" in msg
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
        # Use OpenAI-compat endpoint if tools are needed.
        # Falls back to native mode if the model returns 400 (tool calling not supported).
        if tools:
            try:
                return self._complete_openai_compat(messages, tools, max_tokens)
            except Exception as exc:  # noqa: BLE001
                if _is_tool_fallback_error(exc):
                    # Model doesn't support tool calling — retry without tools
                    return self._complete_native(messages, max_tokens)
                raise
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

    # ── Model name resolution ───────────────────────────────────────────────

    def _get_installed_models(self) -> list[str]:
        """Query running Ollama for exact installed model IDs."""
        try:
            with urllib.request.urlopen(  # noqa: S310
                f"{self._base_url}/api/tags", timeout=3
            ) as resp:
                data: dict[str, Any] = json.loads(resp.read())
                return [m["name"] for m in data.get("models", [])]
        except Exception:  # noqa: BLE001
            return []

    def _resolve_model(self, requested: str) -> str:
        """Resolve a requested model name to the exact installed name.

        Handles the common Ollama 404 scenario where the model was pulled
        under a quantization-tagged name (e.g. ``qwen2.5:14b-instruct-q4_K_M``)
        but specsmith was started with the short tag (``qwen2.5:14b``).
        Returns the shortest matching installed name (= the default quant tag)
        or the original name if nothing better is found.
        """
        installed = self._get_installed_models()
        if not installed:
            return requested
        if requested in installed:
            return requested  # exact match — nothing to do
        # Try base name (before first colon): 'qwen2.5' matches 'qwen2.5:14b-*'
        base = requested.split(":")[0]
        # Also try short tag: 'qwen2.5:14b' matches 'qwen2.5:14b-instruct-q4_K_M'
        short_tag = requested if ":" in requested else None
        candidates = [
            m for m in installed
            if m.startswith(base + ":")
            or (short_tag and m.startswith(short_tag))
        ]
        if candidates:
            return min(candidates, key=len)  # shortest = default quantization
        return requested

    # ── HTTP helper ─────────────────────────────────────────────────────────

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        import urllib.error

        # Patch payload model name to current self.model (may change on retry)
        payload = {**payload, "model": self.model}
        req = urllib.request.Request(  # noqa: S310
            f"{self._base_url}{path}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
                result: dict[str, Any] = json.loads(resp.read())
                return result
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Auto-resolve: find exact installed model name and retry once
                resolved = self._resolve_model(self.model)
                if resolved != self.model:
                    self.model = resolved
                    return self._post(path, payload)  # retry with correct name
                installed = self._get_installed_models()
                hint = (
                    "\n  Installed: " + ", ".join(installed[:5])
                    if installed else "\n  (Ollama returned no installed models)"
                )
                raise RuntimeError(
                    f"Ollama model not found: '{self.model}'{hint}\n"
                    f"  Download it: specsmith ollama pull {self.model}"
                ) from e
            raise
        except OSError as e:
            if "Connection refused" in str(e) or "ECONNREFUSED" in str(e):
                raise RuntimeError(
                    f"Ollama not running at {self._base_url}\n"
                    "  Start it: ollama serve   (or open the Ollama desktop app)"
                ) from e
            raise
