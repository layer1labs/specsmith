# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Ollama provider — local LLMs via REST API. Zero SDK needed (stdlib only).

API compatibility: Ollama v0.3+ (tool calling via /api/chat), v0.20+ verified.

Endpoint strategy:
  /api/chat     — Used for ALL completions, including tool calling (v0.3+).
                  Arguments in tool_calls responses are already dicts (not JSON strings).
  /api/version  — Server version check.
  /api/tags     — List installed models.
  /api/delete   — Delete a model (body: {"model": "<name>"}).

We no longer use /v1/chat/completions (OpenAI-compat endpoint) because:
  - It returns HTTP 400 for many Ollama local models.
  - The native /api/chat endpoint is the correct and preferred path.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from collections.abc import Iterator
from typing import Any

from specsmith.agent.core import (
    CompletionResponse,
    Message,
    StreamToken,
    Tool,
)

# Models whose names suggest they support "think" (extended reasoning)
_THINK_MODEL_PATTERNS = re.compile(
    r"qwq|deepseek-r1|qwen3.*:.*think|o1|o3|phi-4-reasoning",
    re.IGNORECASE,
)


def _is_tool_fallback_error(exc: BaseException) -> bool:
    """Return True when an exception signals that tool calling is not supported.

    Used to fall back to text-only completion when the model doesn't
    support structured tool calling.
    """
    msg = str(exc).lower()
    return (
        "400" in msg
        or "405" in msg
        or "bad request" in msg
        or ("tool" in msg and "not supported" in msg)
        or "does not support" in msg
    )


class OllamaProvider:
    """Ollama local LLM provider. Compatible with Ollama v0.3+.

    Uses the native ``/api/chat`` endpoint for all completions, including
    tool calling.  Context length (num_ctx) is controlled via the
    ``SPECSMITH_OLLAMA_NUM_CTX`` environment variable (default 4096).
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
        self._num_ctx: int = int(os.environ.get("SPECSMITH_OLLAMA_NUM_CTX", "4096"))
        # Whether to pass "think" parameter for reasoning models
        self._think: bool | None = (
            True if _THINK_MODEL_PATTERNS.search(model) else None
        )

    def is_available(self) -> bool:
        try:
            urllib.request.urlopen(  # noqa: S310
                f"{self._base_url}/api/version", timeout=2
            )
            return True
        except Exception:  # noqa: BLE001
            return False

    # ── Completion ────────────────────────────────────────────────────────────

    def complete(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        max_tokens: int = 4096,
    ) -> CompletionResponse:
        """Complete using the native /api/chat endpoint.

        Tool calling is attempted first; if the model returns an error
        indicating no tool support (HTTP 400 etc.) we retry without tools.
        """
        if tools:
            try:
                return self._complete_with_tools(messages, tools, max_tokens)
            except Exception as exc:  # noqa: BLE001
                if _is_tool_fallback_error(exc):
                    # Model doesn't support tool calling — degrade gracefully
                    return self._complete_native(messages, max_tokens)
                raise
        return self._complete_native(messages, max_tokens)

    def _complete_native(
        self, messages: list[Message], max_tokens: int
    ) -> CompletionResponse:
        """Plain chat completion without tools."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "stream": False,
            "options": {"num_predict": max_tokens, "num_ctx": self._num_ctx},
        }
        if self._think is not None:
            payload["think"] = self._think

        data = self._post("/api/chat", payload)
        content = data.get("message", {}).get("content", "") or ""
        return CompletionResponse(
            content=content,
            model=self.model,
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            stop_reason="stop",
        )

    def _complete_with_tools(
        self, messages: list[Message], tools: list[Tool], max_tokens: int
    ) -> CompletionResponse:
        """Chat completion with tool calling via native /api/chat endpoint.

        Ollama v0.3+ supports tools directly on /api/chat using the same
        schema as OpenAI.  Key differences from the OpenAI-compat response:

        - ``message.tool_calls[].function.arguments`` is already a **dict**
          (not a JSON string).
        - ``message.tool_calls[].id`` may be absent; we synthesise one.
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "stream": False,
            "tools": [t.to_openai_schema() for t in tools],
            "options": {"num_predict": max_tokens, "num_ctx": self._num_ctx},
        }
        data = self._post("/api/chat", payload)
        msg = data.get("message", {})
        content = msg.get("content", "") or ""

        tool_calls: list[dict[str, Any]] = []
        for idx, tc in enumerate(msg.get("tool_calls", [])):
            fn   = tc.get("function", {})
            name = fn.get("name", "")
            args = fn.get("arguments", {})
            # Native: arguments is already a dict; compat: it's a JSON string
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except (json.JSONDecodeError, ValueError):
                    args = {}
            # Ollama native may omit id; generate a stable synthetic one
            call_id = tc.get("id") or f"ollama_call_{idx}_{name}"
            tool_calls.append({"id": call_id, "name": name, "input": args})

        return CompletionResponse(
            content=content,
            model=self.model,
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            tool_calls=tool_calls,
            stop_reason="tool_use" if tool_calls else "stop",
        )

    # ── Streaming ─────────────────────────────────────────────────────────────

    def stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        max_tokens: int = 4096,
    ) -> Iterator[StreamToken]:
        """Streaming completion via native /api/chat.

        Note: Ollama native streaming emits NDJSON; tool calls appear in the
        final ``done=true`` chunk.  We yield text tokens as they arrive.
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "stream": True,
            "options": {"num_predict": max_tokens, "num_ctx": self._num_ctx},
        }
        if tools:
            payload["tools"] = [t.to_openai_schema() for t in tools]
        if self._think is not None:
            payload["think"] = self._think

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
                    # Skip "thinking" blocks in reasoning models
                    thinking = chunk.get("message", {}).get("thinking", "")
                    if text and not thinking:
                        yield StreamToken(text=text)
                    if done:
                        yield StreamToken(text="", is_final=True)
                        return
                except json.JSONDecodeError:
                    continue

    # ── Model name resolution ─────────────────────────────────────────────────

    def _get_installed_models(self) -> list[str]:
        """Query running Ollama for exact installed model IDs (via /api/tags)."""
        try:
            with urllib.request.urlopen(  # noqa: S310
                f"{self._base_url}/api/tags", timeout=3
            ) as resp:
                data: dict[str, Any] = json.loads(resp.read())
                return [m["name"] for m in data.get("models", [])]
        except Exception:  # noqa: BLE001
            return []

    def _resolve_model(self, requested: str) -> str:
        """Resolve a requested model tag to the exact installed name.

        Handles the common case where the model was pulled under a
        quantization-tagged name (e.g. ``qwen2.5:14b-instruct-q4_K_M``)
        but specsmith was started with the short tag (``qwen2.5:14b``).
        Returns the shortest matching installed name (= default quant tag)
        or the original name if nothing better is found.
        """
        installed = self._get_installed_models()
        if not installed:
            return requested
        if requested in installed:
            return requested
        base      = requested.split(":")[0]
        short_tag = requested if ":" in requested else None
        candidates = [
            m for m in installed
            if m.startswith(base + ":")
            or (short_tag and m.startswith(short_tag))
        ]
        return min(candidates, key=len) if candidates else requested

    # ── HTTP helper ───────────────────────────────────────────────────────────

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST JSON to the Ollama server; auto-resolve model on 404."""
        import urllib.error

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
                    return self._post(path, payload)
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
