# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Multi-provider LLM client with automatic fallback (REQ-275..REQ-277).

Tries a configurable ordered list of providers; first configured one that
returns successfully wins.  Providers raising HTTP 401/403/429/5xx fall
through to the next provider.  Uses ``urllib`` only — no optional packages.

Concrete providers:
* MistralProvider  (mistral-small-latest)
* OpenAIProvider   (gpt-4o-mini)
* GoogleProvider   (gemini-2.0-flash)
* OllamaProvider   (llama3.2:3b — local)
* MockProvider     (test-only; returns whatever a producer callable yields)
"""

from __future__ import annotations

import json
import logging
import math
import re
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

_log = logging.getLogger(__name__)

_USER_AGENT = "specsmith-llm-client/1.0"


# ── Result type ────────────────────────────────────────────────────────────


@dataclass(slots=True)
class LLMResult:
    """Text + metadata from a successful chat call."""

    provider: str
    model: str
    text: str
    raw: dict[str, Any] = field(default_factory=dict)


class LLMError(RuntimeError):
    """Raised when no provider succeeded."""


# ── HTTP helper ─────────────────────────────────────────────────────────────


def _http_post_json(
    url: str,
    *,
    body: dict[str, Any],
    headers: dict[str, str] | None = None,
    timeout: float = 60.0,
) -> tuple[int, dict[str, Any]]:
    """POST JSON body; returns (status, parsed_json)."""
    payload = json.dumps(body).encode("utf-8")
    hdrs: dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": _USER_AGENT,
    }
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=payload, headers=hdrs, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        raw = resp.read()
        status = resp.status
        if not raw:
            return status, {}
        try:
            return status, json.loads(raw)
        except json.JSONDecodeError:
            return status, {"_raw": raw.decode("utf-8", errors="replace")}


def _is_fallback_status(code: int) -> bool:
    return code in (401, 403, 404, 408, 409, 425, 429) or 500 <= code < 600


def _extract_text(data: dict[str, Any]) -> str:
    """Robustly extract reply text from an OpenAI-compatible response."""
    choices = data.get("choices")
    if not choices:
        return ""
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    # Gemini thinking models return answer in 'parts'
    if content is None and "parts" in msg:
        parts = msg["parts"]
        if isinstance(parts, list):
            content = "\n".join(p.get("text", "") for p in parts if isinstance(p, dict))
    return content or ""


def _extract_json_text(text: str) -> str:
    """Robustly extract JSON from a model response."""
    # Fast path
    try:
        json.loads(text)
        return text
    except Exception:  # noqa: BLE001
        pass
    # ```json ... ``` fence
    for pat in (r"```json\s*(\{.*?\})\s*```", r"```\s*(\{.*?\})\s*`"):
        m = re.search(pat, text, re.DOTALL)
        if m:
            cand = m.group(1).strip()
            try:
                json.loads(cand)
                return cand
            except Exception:  # noqa: BLE001
                pass
    # First balanced { } block
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                cand = text[start : i + 1]
                try:
                    json.loads(cand)
                    return cand
                except Exception:  # noqa: BLE001
                    break
    raise ValueError(f"Could not extract JSON from response: {text[:200]!r}")


def _estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


# ── O-series translation ───────────────────────────────────────────────────


def _is_o_series(model: str) -> bool:
    ml = model.lower()
    return any(ml.startswith(p) for p in ("o1", "o3", "o4")) or any(
        t in ml for t in ("-o1-", "-o3-", "-o4-")
    )


def _translate_o_series(
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Translate messages + params for OpenAI o1/o3/o4 reasoning models."""
    adj: list[dict[str, str]] = []
    for m in messages:
        if m.get("role") == "system":
            adj.append({"role": "developer", "content": m.get("content", "")})
        else:
            adj.append(m)
    extra: dict[str, Any] = {"max_completion_tokens": max_tokens, "temperature": 1}
    return adj, extra


# ── Provider ABC ──────────────────────────────────────────────────────────


class LLMProvider(ABC):
    """Provider-specific HTTP shim."""

    name: str = ""
    key_name: str = ""
    default_model: str = ""

    def __init__(self, model: str | None = None) -> None:
        if not self.name:
            raise TypeError(f"{type(self).__name__}.name must be set")
        self.model = model or self.default_model

    def is_configured(self) -> bool:
        """Return True if the provider has a usable API key."""
        import os  # noqa: PLC0415

        return bool(self.key_name) and bool(os.environ.get(self.key_name))

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
        json_schema: dict[str, Any] | None = None,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> LLMResult:
        """Execute one chat call; raise ``urllib.error.HTTPError`` on fallback-worthy errors."""


# ── Concrete providers ─────────────────────────────────────────────────────


class MistralProvider(LLMProvider):
    name = "mistral"
    key_name = "MISTRAL_API_KEY"
    default_model = "mistral-small-latest"

    def chat(
        self, messages, *, json_mode=False, json_schema=None, max_tokens=2000, temperature=0.3
    ):
        import os  # noqa: PLC0415

        key = os.environ.get(self.key_name, "")
        if not key:
            raise LLMError("Mistral API key not set (MISTRAL_API_KEY)")
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        _, data = _http_post_json(
            "https://api.mistral.ai/v1/chat/completions",
            body=body,
            headers={"Authorization": f"Bearer {key}"},
        )
        return LLMResult(provider=self.name, model=self.model, text=_extract_text(data), raw=data)


class OpenAIProvider(LLMProvider):
    name = "openai"
    key_name = "OPENAI_API_KEY"
    default_model = "gpt-4o-mini"

    def chat(
        self, messages, *, json_mode=False, json_schema=None, max_tokens=2000, temperature=0.3
    ):
        import os  # noqa: PLC0415

        key = os.environ.get(self.key_name, "")
        if not key:
            raise LLMError("OpenAI API key not set (OPENAI_API_KEY)")
        if _is_o_series(self.model):
            messages, extra = _translate_o_series(messages, max_tokens, temperature)
            body: dict[str, Any] = {"model": self.model, "messages": messages, **extra}
        else:
            body = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        if json_schema:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_output",
                    "strict": False,
                    "schema": json_schema,
                },
            }
        elif json_mode:
            body["response_format"] = {"type": "json_object"}
        _, data = _http_post_json(
            "https://api.openai.com/v1/chat/completions",
            body=body,
            headers={"Authorization": f"Bearer {key}"},
        )
        return LLMResult(provider=self.name, model=self.model, text=_extract_text(data), raw=data)


class GoogleProvider(LLMProvider):
    name = "google"
    key_name = "GOOGLE_API_KEY"
    default_model = "gemini-2.0-flash"

    def chat(
        self, messages, *, json_mode=False, json_schema=None, max_tokens=2000, temperature=0.3
    ):
        import os  # noqa: PLC0415

        key = os.environ.get(self.key_name, "")
        if not key:
            raise LLMError("Google API key not set (GOOGLE_API_KEY)")
        contents = [
            {
                "role": ("user" if m.get("role") != "model" else "model"),
                "parts": [{"text": m.get("content", "")}],
            }
            for m in messages
            if m.get("role") in ("system", "user", "assistant", "model")
        ]
        body: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature},
        }
        if json_mode:
            body["generationConfig"]["responseMimeType"] = "application/json"
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{urllib.parse.quote(self.model)}:generateContent?key={key}"
        )
        _, data = _http_post_json(url, body=body)
        candidates = (data or {}).get("candidates") or []
        text = ""
        if candidates:
            parts = (candidates[0].get("content") or {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts)
        return LLMResult(provider=self.name, model=self.model, text=text, raw=data)


class OllamaProvider(LLMProvider):
    """Local Ollama provider (no API key required)."""

    name = "ollama"
    key_name = ""
    default_model = "llama3.2:3b"

    def __init__(self, model: str | None = None, base_url: str = "http://localhost:11434") -> None:
        super().__init__(model)
        self.base_url = base_url.rstrip("/")

    def is_configured(self) -> bool:
        """Check if Ollama is running."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:  # noqa: S310
                return resp.status == 200
        except Exception:  # noqa: BLE001
            return False

    def chat(
        self, messages, *, json_mode=False, json_schema=None, max_tokens=2000, temperature=0.3
    ):
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if json_mode:
            body["format"] = "json"
        data_bytes = json.dumps(body).encode()
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:  # noqa: S310
                data = json.loads(resp.read().decode())
            text = data.get("message", {}).get("content", "")
            return LLMResult(provider=self.name, model=self.model, text=text, raw=data)
        except urllib.error.URLError as exc:
            raise LLMError(f"Ollama not reachable at {self.base_url}: {exc}") from exc


class MockProvider(LLMProvider):
    """Test-only provider: returns whatever ``producer`` yields."""

    name = "mock"
    key_name = ""
    default_model = "mock-1"

    def __init__(self, producer: Callable[[list[dict[str, str]]], str] | str) -> None:
        super().__init__(model=self.default_model)
        if isinstance(producer, str):
            _text = producer
            self._producer: Callable[[list[dict[str, str]]], str] = lambda _msgs: _text
        else:
            self._producer = producer

    def is_configured(self) -> bool:
        return True

    def chat(
        self, messages, *, json_mode=False, json_schema=None, max_tokens=2000, temperature=0.3
    ):
        text = self._producer(messages)
        return LLMResult(provider=self.name, model=self.model, text=text, raw={})


# ── Client with provider fallback ─────────────────────────────────────────


def _default_providers() -> list[LLMProvider]:
    return [MistralProvider(), OpenAIProvider(), GoogleProvider(), OllamaProvider()]


class LLMClient:
    """Try a list of providers in order; first configured one that succeeds wins.

    Providers raising ``urllib.error.HTTPError`` with a fallback status code
    (401/403/429/5xx) move the client to the next provider.
    """

    def __init__(self, providers: list[LLMProvider] | None = None) -> None:
        self._providers = providers or _default_providers()

    def configured_providers(self) -> list[str]:
        return [p.name for p in self._providers if p.is_configured()]

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
        json_schema: dict[str, Any] | None = None,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> LLMResult:
        """Try each configured provider in order. Fallback on HTTP errors."""
        errors: list[str] = []
        for p in self._providers:
            if not p.is_configured():
                continue
            try:
                return p.chat(
                    messages,
                    json_mode=json_mode,
                    json_schema=json_schema,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            except urllib.error.HTTPError as exc:
                if _is_fallback_status(exc.code):
                    _log.info("provider %s returned HTTP %s, trying next", p.name, exc.code)
                    errors.append(f"{p.name}: HTTP {exc.code}")
                    continue
                raise LLMError(f"{p.name} HTTP {exc.code}: {exc.reason}") from exc
            except urllib.error.URLError as exc:
                _log.info("provider %s URLError: %s, trying next", p.name, exc.reason)
                errors.append(f"{p.name}: URLError {exc.reason}")
                continue
            except LLMError:
                raise
            except Exception as exc:  # noqa: BLE001
                _log.warning("provider %s raised %s: %s", p.name, type(exc).__name__, exc)
                errors.append(f"{p.name}: {type(exc).__name__}: {exc}")
                continue
        configured = self.configured_providers()
        summary = "; ".join(errors) if errors else "no configured providers"
        raise LLMError(f"No LLM provider succeeded ({summary}). Configured: {configured}")

    def chat_json(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 2000,
        temperature: float = 0.0,
    ) -> tuple[dict[str, Any], LLMResult]:
        """Like ``chat`` but returns ``(parsed_json, result)``."""
        result = self.chat(messages, json_mode=True, max_tokens=max_tokens, temperature=temperature)
        text = (result.text or "").strip()
        try:
            return json.loads(text), result
        except json.JSONDecodeError:
            pass
        start = text.find("{")
        end = text.rfind("}")
        if 0 <= start < end:
            try:
                return json.loads(text[start : end + 1]), result
            except json.JSONDecodeError as exc:
                raise LLMError(f"Could not parse JSON from {result.provider}: {exc}") from exc
        raise LLMError(f"Empty / non-JSON response from {result.provider}: {text[:200]!r}")


# ── vLLM / BYOE guided-JSON dispatch helper ─────────────────────────────────


def dispatch_byoe(
    *,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    api_key: str = "",
    headers: dict[str, str] | None = None,
    json_mode: bool = False,
    json_schema: dict[str, Any] | None = None,
    max_tokens: int = 2000,
    temperature: float = 0.3,
    timeout: float = 120.0,
) -> LLMResult:
    """Dispatch a chat request to any OpenAI-compatible BYOE endpoint.

    Supports vLLM ``guided_json`` + ``chat_template_kwargs`` for structured
    output (REQ-277).  Also handles O-series model translation (REQ-276).
    """
    base = base_url.rstrip("/")
    if base.endswith("/v1") or "/v1beta" in base or base.endswith("/openai"):
        url = f"{base}/chat/completions"
    else:
        url = f"{base}/v1/chat/completions"

    if _is_o_series(model):
        messages, extra = _translate_o_series(messages, max_tokens, temperature)
        body: dict[str, Any] = {"model": model, "messages": messages, **extra}
    else:
        body = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

    if json_schema:
        # vLLM guided JSON mode
        body["guided_json"] = json_schema
        body["chat_template_kwargs"] = {"enable_thinking": False}
    elif json_mode:
        body["response_format"] = {"type": "json_object"}
        body["chat_template_kwargs"] = {"enable_thinking": False}

    req_headers: dict[str, str] = {}
    if api_key:
        req_headers["Authorization"] = f"Bearer {api_key}"
    if headers:
        req_headers.update(headers)

    try:
        _, data = _http_post_json(url, body=body, headers=req_headers or None, timeout=timeout)
        return LLMResult(provider="byoe", model=model, text=_extract_text(data), raw=data)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")[:500]
        raise LLMError(f"BYOE endpoint HTTP {exc.code}: {raw}") from exc
    except Exception as exc:  # noqa: BLE001
        raise LLMError(f"BYOE request failed: {exc}") from exc


__all__ = [
    "LLMClient",
    "LLMError",
    "LLMProvider",
    "LLMResult",
    "MistralProvider",
    "MockProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "GoogleProvider",
    "dispatch_byoe",
]
