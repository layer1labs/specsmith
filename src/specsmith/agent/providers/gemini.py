# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Google Gemini provider for the specsmith agentic client.

SDK support (prefers new over legacy):
  - google-genai  (GA May 2025)  — preferred: pip install specsmith[gemini]
  - google-generativeai (deprecated Nov 30, 2025) — legacy fallback

Current models (April 2026):
  gemini-2.5-flash         — fast, 1M ctx (default)
  gemini-2.5-pro           — most capable 2.5
  gemini-3-flash-preview   — newest fast frontier model
  gemini-3.1-pro-preview   — latest pro frontier model

Note: gemini-2.0-flash is being shut down June 1, 2026.
Free API key: https://aistudio.google.com/apikey

Requires: pip install specsmith[gemini]
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
)


class GeminiProvider:
    """Google Gemini provider.

    Supports gemini-2.5-flash, gemini-2.5-pro, gemini-3-flash-preview, etc.
    Tries the new ``google-genai`` SDK first; falls back to the legacy
    ``google-generativeai`` SDK if not installed.
    """

    provider_name = "gemini"

    # Current recommended model (free tier available, fast)
    _DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(self, model: str = _DEFAULT_MODEL, api_key: str = "") -> None:
        self.model   = model
        self._api_key = api_key
        self._sdk: str = ""          # "genai" or "legacy"
        self._client: Any = None
        self._genai:  Any = None     # new SDK client or legacy module
        self._ensure_client()

    def _ensure_client(self) -> None:
        # ── Try new google-genai SDK first ────────────────────────────────
        try:
            from google import genai  # type: ignore[import-untyped]

            self._client = genai.Client(api_key=self._api_key or None)
            self._sdk = "genai"
            return
        except (ImportError, Exception):  # noqa: BLE001
            pass

        # ── Fall back to legacy google-generativeai ───────────────────────
        try:
            import google.generativeai as _legacy_genai  # type: ignore[import-untyped]

            _legacy_genai.configure(api_key=self._api_key)
            self._genai = _legacy_genai
            self._sdk = "legacy"
        except ImportError as e:
            from specsmith.agent.core import ProviderNotAvailable
            raise ProviderNotAvailable("gemini", "gemini") from e

    def is_available(self) -> bool:
        try:
            # Check whichever SDK is available
            if self._sdk == "genai":
                from google import genai  # noqa: F401  # type: ignore[import-untyped]
            else:
                import google.generativeai  # noqa: F401  # type: ignore[import-untyped]
            return bool(self._api_key)
        except ImportError:
            return False

    # ── Complete ──────────────────────────────────────────────────────────────

    def complete(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        max_tokens: int = 4096,
    ) -> CompletionResponse:
        if self._sdk == "genai":
            return self._complete_new_sdk(messages, max_tokens)
        return self._complete_legacy_sdk(messages, max_tokens)

    def _complete_new_sdk(
        self, messages: list[Message], max_tokens: int
    ) -> CompletionResponse:
        """Complete using google-genai (new SDK, GA May 2025)."""
        from google.genai.types import GenerateContentConfig  # type: ignore[import-untyped]

        system_text, history = self._split_messages(messages)

        config_kwargs: dict[str, Any] = {"max_output_tokens": max_tokens}
        if system_text:
            config_kwargs["system_instruction"] = system_text

        response = self._client.models.generate_content(
            model=self.model,
            contents=history,
            config=GenerateContentConfig(**config_kwargs),
        )

        content = response.text or ""
        usage   = getattr(response, "usage_metadata", None)
        in_tok  = getattr(usage, "prompt_token_count", 0) if usage else 0
        out_tok = getattr(usage, "candidates_token_count", 0) if usage else 0

        return CompletionResponse(
            content=content,
            model=self.model,
            input_tokens=in_tok,
            output_tokens=out_tok,
            stop_reason="stop",
        )

    def _complete_legacy_sdk(
        self, messages: list[Message], max_tokens: int
    ) -> CompletionResponse:
        """Complete using legacy google-generativeai SDK.

        Uses the ``system_instruction`` constructor parameter (available
        since google-generativeai 0.4.0, not the old prepend-to-user hack).
        """
        system_text, history = self._split_messages(messages)

        kwargs: dict[str, Any] = {
            "model_name": self.model,
            "generation_config": {"max_output_tokens": max_tokens},
        }
        if system_text:
            kwargs["system_instruction"] = system_text

        gemini_model = self._genai.GenerativeModel(**kwargs)

        if not history:
            return CompletionResponse(content="", model=self.model)

        last_msg = history.pop()
        chat     = gemini_model.start_chat(history=history)
        response = chat.send_message(last_msg["parts"][0])
        content  = response.text or ""

        # Token counts from usage_metadata (available in 0.8+)
        usage   = getattr(response, "usage_metadata", None)
        in_tok  = getattr(usage, "prompt_token_count", 0) if usage else 0
        out_tok = getattr(usage, "candidates_token_count", 0) if usage else 0

        return CompletionResponse(
            content=content,
            model=self.model,
            input_tokens=in_tok,
            output_tokens=out_tok,
            stop_reason="stop",
        )

    # ── Streaming ─────────────────────────────────────────────────────────────

    def stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        max_tokens: int = 4096,
    ) -> Iterator[StreamToken]:
        if self._sdk == "genai":
            yield from self._stream_new_sdk(messages, max_tokens)
        else:
            yield from self._stream_legacy_sdk(messages, max_tokens)

    def _stream_new_sdk(
        self, messages: list[Message], max_tokens: int
    ) -> Iterator[StreamToken]:
        from google.genai.types import GenerateContentConfig  # type: ignore[import-untyped]

        system_text, history = self._split_messages(messages)
        config_kwargs: dict[str, Any] = {"max_output_tokens": max_tokens}
        if system_text:
            config_kwargs["system_instruction"] = system_text

        for chunk in self._client.models.generate_content_stream(
            model=self.model,
            contents=history,
            config=GenerateContentConfig(**config_kwargs),
        ):
            if chunk.text:
                yield StreamToken(text=chunk.text)
        yield StreamToken(text="", is_final=True)

    def _stream_legacy_sdk(
        self, messages: list[Message], max_tokens: int
    ) -> Iterator[StreamToken]:
        system_text, history = self._split_messages(messages)

        kwargs: dict[str, Any] = {
            "model_name": self.model,
            "generation_config": {"max_output_tokens": max_tokens},
        }
        if system_text:
            kwargs["system_instruction"] = system_text

        gemini_model = self._genai.GenerativeModel(**kwargs)

        if not history:
            yield StreamToken(text="", is_final=True)
            return

        last_msg = history.pop()
        chat     = gemini_model.start_chat(history=history)
        for chunk in chat.send_message(last_msg["parts"][0], stream=True):
            if chunk.text:
                yield StreamToken(text=chunk.text)
        yield StreamToken(text="", is_final=True)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _split_messages(
        self, messages: list[Message]
    ) -> tuple[str, list[dict[str, Any]]]:
        """Split messages into (system_instruction_text, conversation_history).

        System messages are extracted as a system instruction (not injected
        into the conversation history).
        """
        system_parts: list[str] = []
        history: list[dict[str, Any]] = []

        for m in messages:
            if m.role == Role.SYSTEM:
                system_parts.append(m.content)
            elif m.role == Role.USER:
                history.append({"role": "user", "parts": [m.content]})
            elif m.role == Role.ASSISTANT:
                history.append({"role": "model", "parts": [m.content]})

        system_text = "\n\n".join(system_parts)
        return system_text, history
