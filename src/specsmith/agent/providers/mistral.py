# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Mistral AI provider for the specsmith agentic client.

Mistral's API is OpenAI-compatible, so we use the openai SDK pointed at
Mistral's endpoint.  Pixtral models support vision/OCR.

Requires: pip install specsmith[mistral]

Environment:
    MISTRAL_API_KEY — your Mistral API key (https://console.mistral.ai/)

Models:
    mistral-large-latest       — most capable text model
    mistral-small-latest       — fast, cheap
    codestral-latest           — code-optimised (FIM support)
    pixtral-large-latest       — vision + OCR (multimodal)
    pixtral-12b-2409           — smaller vision model
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

_MISTRAL_BASE_URL = "https://api.mistral.ai/v1"

# Pixtral models that support image/document input (OCR use-cases)
_VISION_MODELS = {"pixtral-large-latest", "pixtral-12b-2409", "pixtral-large-2411"}


class MistralProvider:
    """Mistral AI provider.  Uses the OpenAI-compatible chat completions API."""

    provider_name = "mistral"

    def __init__(self, model: str = "mistral-large-latest", api_key: str = "") -> None:
        self.model = model
        self._api_key = api_key
        self._client: Any = None
        self._ensure_client()

    def _ensure_client(self) -> None:
        try:
            import openai

            self._client = openai.OpenAI(
                api_key=self._api_key or "placeholder",
                base_url=_MISTRAL_BASE_URL,
            )
        except ImportError as e:
            from specsmith.agent.core import ProviderNotAvailable

            raise ProviderNotAvailable("mistral", "openai") from e

    def is_available(self) -> bool:
        try:
            import openai  # noqa: F401

            return bool(self._api_key)
        except ImportError:
            return False

    @property
    def supports_vision(self) -> bool:
        return self.model in _VISION_MODELS

    def complete(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        max_tokens: int = 4096,
    ) -> CompletionResponse:
        msgs = [m.to_dict() for m in messages]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": msgs,
            "max_tokens": max_tokens,
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
        msgs = [m.to_dict() for m in messages]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": msgs,
            "max_tokens": max_tokens,
            "stream": True,
        }
        stream = self._client.chat.completions.create(**kwargs)
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield StreamToken(text=delta.content)
        yield StreamToken(text="", is_final=True)

    def ocr_image(self, image_path: str, prompt: str = "Extract all text from this image.") -> str:
        """Extract text from an image using a Pixtral vision model.

        Automatically switches to pixtral-large-latest if current model is text-only.
        """
        import base64
        from pathlib import Path

        model = self.model if self.supports_vision else "pixtral-large-latest"
        img_bytes = Path(image_path).read_bytes()
        b64 = base64.b64encode(img_bytes).decode()

        # Detect MIME type from extension
        ext = Path(image_path).suffix.lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
        }
        mime = mime_map.get(ext, "image/png")

        response = self._client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""
