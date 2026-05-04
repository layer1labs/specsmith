# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Real LLM-backed runner for `specsmith chat` (REQ-108, REQ-112-118).

This module replaces the deterministic stub that previously lived inside
`chat_cmd`. It selects the first available provider (Ollama → Anthropic →
OpenAI → Gemini) and streams the model's response as `token` events
through the supplied :class:`EventEmitter`. Output is then parsed for
``Files changed:`` and ``Test results:`` sections so the verifier can
emit a real verdict.

The runner is deliberately defensive: any provider error (missing SDK,
unreachable endpoint, network failure) returns ``None`` so the caller
can fall back to the deterministic stub. This keeps the test suite
green on machines that have no LLM configured at all.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from specsmith.agent.events import EventEmitter
from specsmith.agent.verifier import (
    VerifierVerdict,
    report_from_chat_sections,
    score,
)

DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = os.environ.get("SPECSMITH_OLLAMA_MODEL", "qwen2.5:7b")
SYSTEM_PROMPT = (
    "You are Nexus, the local-first agentic developer assistant inside "
    "Specsmith. Always end your response with the canonical contract:\n"
    "Plan:\n"
    "Files changed:\n"
    "Test results:\n"
    "Next action:\n"
)


@dataclass
class ChatRunResult:
    """Return value of :func:`run_chat`."""

    provider: str
    summary: str
    files_changed: list[str] = field(default_factory=list)
    verdict: VerifierVerdict | None = None
    raw_text: str = ""
    # C1: per-turn token + cost accounting. Populated by the provider
    # driver when it can read counters from the response (Ollama and
    # Anthropic both expose them). Falls back to a deterministic char-
    # based heuristic so the TokenMeter chip is never zero on Ollama or
    # OpenAI-compat endpoints that don't surface usage in streaming mode.
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "summary": self.summary,
            "files_changed": list(self.files_changed),
            "confidence": self.verdict.confidence if self.verdict else 0.0,
            "equilibrium": self.verdict.equilibrium if self.verdict else False,
            "tokens_in": int(self.tokens_in),
            "tokens_out": int(self.tokens_out),
            "cost_usd": float(self.cost_usd),
        }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_chat(
    utterance: str,
    *,
    project_dir: Path,
    profile: str,
    session_id: str,
    emitter: EventEmitter,
    msg_block: str,
    history: list[dict[str, Any]] | None = None,
    confidence_target: float = 0.7,
    rules_prefix: str = "",
    endpoint_id: str | None = None,
) -> ChatRunResult | None:
    """Drive a real LLM turn. Return ``None`` if no provider is reachable.

    When ``endpoint_id`` is set, the BYOE store (REQ-142) is consulted and
    the resolved :class:`Endpoint` short-circuits the provider chain via
    the new :func:`_run_openai_compat` driver. Any error during endpoint
    resolution falls back to the legacy auto-detect chain so an offline
    misconfigured endpoint never breaks `specsmith chat`.
    """
    history = history or []
    messages = _build_messages(utterance, history, rules_prefix)

    # REQ-142: explicit endpoint override.
    if endpoint_id:
        try:
            from specsmith.agent.endpoints import EndpointStore

            endpoint = EndpointStore.load().resolve(endpoint_id)
        except Exception:  # noqa: BLE001 - any failure → fall back to auto-detect
            endpoint = None
        if endpoint is not None:
            try:
                full_text, usage = _run_openai_compat(
                    messages, emitter, msg_block, endpoint=endpoint
                )
            except Exception:  # noqa: BLE001 - degrade to auto-detect
                full_text, usage = None, _UsageDelta()
            if full_text is not None:
                return _finalize(
                    full_text,
                    "openai_compat",
                    project_dir,
                    confidence_target,
                    messages=messages,
                    usage=usage,
                )

    # Order matters: Ollama first because it's local-first and free.
    for provider in (_run_ollama, _run_anthropic, _run_openai, _run_gemini):
        try:
            full_text, usage = provider(messages, emitter, msg_block)
        except Exception:  # noqa: BLE001 - any failure → next provider
            continue
        if full_text is None:
            continue
        return _finalize(
            full_text,
            provider.__name__,
            project_dir,
            confidence_target,
            messages=messages,
            usage=usage,
        )
    return None


@dataclass
class _UsageDelta:
    """Per-turn token + cost counters reported by a provider driver.

    All fields default to ``0`` so callers can construct a zero-value
    instance without caring whether the provider supports usage tracking.
    """

    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0


def _finalize(
    full_text: str,
    provider_fn_name: str,
    project_dir: Path,
    confidence_target: float,
    *,
    messages: list[dict[str, str]] | None = None,
    usage: _UsageDelta | None = None,
) -> ChatRunResult:
    sections = _parse_output_contract(full_text)
    files_changed = _split_files_list(sections.get("files_changed", ""))
    report = report_from_chat_sections(sections, files_changed=files_changed)
    verdict = score(report, confidence_target=confidence_target)
    summary = (sections.get("plan") or full_text.strip()[:200]).strip() or verdict.summary

    # C1: when the provider didn't report exact counts, estimate from text.
    # The four-chars-per-token rule of thumb is OpenAI's published guidance
    # and matches Ollama / Anthropic / Gemini within ~10% across the model
    # families we ship today — close enough for the TokenMeter chip and
    # the ``credits record`` ledger event.
    if usage is None:
        usage = _UsageDelta()
    if usage.tokens_in == 0 and messages is not None:
        usage.tokens_in = _estimate_tokens("\n".join(m.get("content", "") for m in messages))
    if usage.tokens_out == 0:
        usage.tokens_out = _estimate_tokens(full_text)

    return ChatRunResult(
        provider=provider_fn_name.removeprefix("_run_"),
        summary=summary,
        files_changed=files_changed,
        verdict=verdict,
        raw_text=full_text,
        tokens_in=int(usage.tokens_in),
        tokens_out=int(usage.tokens_out),
        cost_usd=float(usage.cost_usd),
    )


def _estimate_tokens(text: str) -> int:
    """Rough char→token heuristic (4 chars/token, floor at 1 if non-empty)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Provider drivers — each returns the full assembled text or None
# ---------------------------------------------------------------------------


def _run_ollama(
    messages: list[dict[str, str]],
    emitter: EventEmitter,
    block_id: str,
) -> tuple[str | None, _UsageDelta]:
    """Stream from a local Ollama daemon using only stdlib."""
    host = os.environ.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST).rstrip("/")
    model = os.environ.get("SPECSMITH_OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    usage = _UsageDelta()

    if not _ollama_alive(host):
        return None, usage

    payload = json.dumps({"model": model, "messages": messages, "stream": True}).encode("utf-8")
    req = Request(  # noqa: S310 - URL is a hardcoded localhost default
        f"{host}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    pieces: list[str] = []
    with urlopen(req, timeout=120) as resp:  # noqa: S310
        for raw_line in resp:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            chunk = ((obj.get("message") or {}).get("content")) or ""
            if chunk:
                emitter.token(block_id, chunk)
                pieces.append(chunk)
            if obj.get("done"):
                # C1: Ollama exposes prompt_eval_count + eval_count on the
                # final ``done`` message. Cost is zero for local models.
                usage.tokens_in = int(obj.get("prompt_eval_count") or 0)
                usage.tokens_out = int(obj.get("eval_count") or 0)
                usage.cost_usd = 0.0
                break
    return ("".join(pieces) if pieces else None), usage


def _ollama_alive(host: str) -> bool:
    try:
        with urlopen(f"{host}/api/tags", timeout=2):  # noqa: S310
            return True
    except (URLError, TimeoutError, OSError):
        return False


def _run_anthropic(
    messages: list[dict[str, str]],
    emitter: EventEmitter,
    block_id: str,
) -> tuple[str | None, _UsageDelta]:
    """Use the anthropic SDK if installed and a key is configured."""
    usage = _UsageDelta()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None, usage
    try:
        import anthropic
    except ImportError:
        return None, usage

    system = "\n".join(m["content"] for m in messages if m["role"] == "system")
    user_msgs = [m for m in messages if m["role"] != "system"]
    client = anthropic.Anthropic()
    pieces: list[str] = []
    with client.messages.stream(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5"),
        max_tokens=2048,
        system=system,
        messages=[{"role": m["role"], "content": m["content"]} for m in user_msgs],
    ) as stream:
        for event in stream:
            text = getattr(getattr(event, "delta", None), "text", None)
            if text:
                emitter.token(block_id, text)
                pieces.append(text)
        # C1: pull final usage off the SDK's `final_message`. Cost is the
        # caller's problem (rate-limit module knows the model price); we
        # report tokens here and let the credits ledger compute USD.
        try:
            final = stream.get_final_message()
            usage.tokens_in = int(getattr(final.usage, "input_tokens", 0) or 0)
            usage.tokens_out = int(getattr(final.usage, "output_tokens", 0) or 0)
        except Exception:  # noqa: BLE001 - usage is best-effort
            pass
    return ("".join(pieces) if pieces else None), usage


def _run_openai(
    messages: list[dict[str, str]],
    emitter: EventEmitter,
    block_id: str,
) -> tuple[str | None, _UsageDelta]:
    """Use the openai SDK if installed and a key is configured."""
    usage = _UsageDelta()
    if not os.environ.get("OPENAI_API_KEY"):
        return None, usage
    try:
        from openai import OpenAI
    except ImportError:
        return None, usage

    client = OpenAI()
    # ``stream_options.include_usage`` makes the final SSE chunk carry a
    # populated ``usage`` block (otherwise streaming responses emit it as
    # ``None``). Older SDK versions silently ignore unknown kwargs.
    stream = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        messages=messages,
        stream=True,
        stream_options={"include_usage": True},
    )
    pieces: list[str] = []
    for chunk in stream:
        if chunk.choices:
            text = chunk.choices[0].delta.content or ""
            if text:
                emitter.token(block_id, text)
                pieces.append(text)
        usage_obj = getattr(chunk, "usage", None)
        if usage_obj is not None:
            usage.tokens_in = int(getattr(usage_obj, "prompt_tokens", 0) or 0)
            usage.tokens_out = int(getattr(usage_obj, "completion_tokens", 0) or 0)
    return ("".join(pieces) if pieces else None), usage


def _run_openai_compat(
    messages: list[dict[str, str]],
    emitter: EventEmitter,
    block_id: str,
    *,
    endpoint: Any,
) -> tuple[str | None, _UsageDelta]:
    """Stream from a user-registered OpenAI-v1-compatible endpoint (REQ-142).

    Uses raw stdlib HTTP so the openai SDK is not a hard dependency for
    BYOE. Sends a streaming ``/chat/completions`` request, decodes the
    Server-Sent-Events ``data:`` lines, and forwards each ``content``
    delta as a ``token`` event on ``block_id``.
    """
    usage = _UsageDelta()
    base_url = endpoint.base_url.rstrip("/")
    url = f"{base_url}/chat/completions"
    model = endpoint.default_model or os.environ.get("SPECSMITH_OPENAI_COMPAT_MODEL", "")
    if not model:
        # The endpoint did not pin a default model and the env override is
        # absent. We cannot fabricate one; fall back to the auto-detect chain.
        return None, usage

    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    try:
        token = endpoint.resolve_token()
    except Exception:  # noqa: BLE001 - fall back to auto-detect chain
        return None, usage
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(
        {
            "model": model,
            "messages": messages,
            "stream": True,
            # Many vLLM/llama.cpp builds honour OpenAI's stream_options;
            # the request is harmless if they don't.
            "stream_options": {"include_usage": True},
        }
    ).encode("utf-8")
    req = Request(url, data=body, headers=headers, method="POST")  # noqa: S310 - user-supplied

    ctx = None
    if not endpoint.verify_tls and url.startswith("https://"):
        import ssl

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    pieces: list[str] = []
    try:
        with urlopen(req, timeout=120, context=ctx) as resp:  # noqa: S310 - user-supplied
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").rstrip("\n\r")
                if not line.startswith("data:"):
                    continue
                payload = line[len("data:") :].strip()
                if not payload or payload == "[DONE]":
                    if payload == "[DONE]":
                        break
                    continue
                try:
                    obj = json.loads(payload)
                except ValueError:
                    continue
                choices = obj.get("choices") or []
                usage_obj = obj.get("usage")
                if usage_obj:
                    usage.tokens_in = int(usage_obj.get("prompt_tokens") or 0)
                    usage.tokens_out = int(usage_obj.get("completion_tokens") or 0)
                if not choices:
                    continue
                delta = (choices[0] or {}).get("delta") or {}
                chunk = str(delta.get("content") or "")
                if chunk:
                    emitter.token(block_id, chunk)
                    pieces.append(chunk)
    except (URLError, TimeoutError, OSError):
        return None, usage
    return ("".join(pieces) if pieces else None), usage


def _run_gemini(
    messages: list[dict[str, str]],
    emitter: EventEmitter,
    block_id: str,
) -> tuple[str | None, _UsageDelta]:
    """Use google-genai SDK if installed and a key is configured."""
    usage = _UsageDelta()
    if not os.environ.get("GOOGLE_API_KEY"):
        return None, usage
    try:
        from google import genai
    except ImportError:
        return None, usage

    client = genai.Client()
    prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    pieces: list[str] = []
    last_chunk: Any = None
    for chunk in client.models.generate_content_stream(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=prompt,
    ):
        last_chunk = chunk
        text = getattr(chunk, "text", "") or ""
        if text:
            emitter.token(block_id, text)
            pieces.append(text)
    # Gemini exposes ``usage_metadata`` on the final chunk. Field names
    # vary across SDK versions; we accept the union.
    meta = getattr(last_chunk, "usage_metadata", None) if last_chunk else None
    if meta is not None:
        usage.tokens_in = int(
            getattr(meta, "prompt_token_count", 0) or getattr(meta, "input_token_count", 0) or 0
        )
        usage.tokens_out = int(
            getattr(meta, "candidates_token_count", 0)
            or getattr(meta, "output_token_count", 0)
            or 0
        )
    return ("".join(pieces) if pieces else None), usage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_messages(
    utterance: str,
    history: list[dict[str, Any]],
    rules_prefix: str,
) -> list[dict[str, str]]:
    system = SYSTEM_PROMPT
    if rules_prefix:
        system = f"{system}\n\nProject rules:\n{rules_prefix}"
    msgs: list[dict[str, str]] = [{"role": "system", "content": system}]
    for turn in history[-10:]:
        text = str(turn.get("utterance") or turn.get("text") or "").strip()
        if text:
            msgs.append({"role": "user", "content": text})
    msgs.append({"role": "user", "content": utterance})
    return msgs


def _parse_output_contract(text: str) -> dict[str, str]:
    """Extract canonical Nexus output sections from free-form text.

    The contract is `Plan:`, `Commands to run:`, `Files changed:`,
    `Diff:`, `Test results:`, `Next action:`. Sections that don't
    appear are returned as empty strings.
    """
    keys = [
        ("plan", "Plan:"),
        ("commands_to_run", "Commands to run:"),
        ("files_changed", "Files changed:"),
        ("diff", "Diff:"),
        ("test_results", "Test results:"),
        ("next_action", "Next action:"),
    ]
    out: dict[str, str] = {key: "" for key, _ in keys}
    lower = text.lower()
    bounds: list[tuple[str, int]] = []
    for key, header in keys:
        idx = lower.find(header.lower())
        if idx >= 0:
            bounds.append((key, idx + len(header)))
    bounds.sort(key=lambda b: b[1])
    for i, (key, start) in enumerate(bounds):
        if i + 1 < len(bounds):
            next_key, next_pos = bounds[i + 1]
            end = next_pos - len(_section_header(next_key))
        else:
            end = len(text)
        out[key] = text[start:end].strip()
    return out


def _section_header(key: str) -> str:
    return {
        "plan": "Plan:",
        "commands_to_run": "Commands to run:",
        "files_changed": "Files changed:",
        "diff": "Diff:",
        "test_results": "Test results:",
        "next_action": "Next action:",
    }[key]


def _split_files_list(text: str) -> list[str]:
    items: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("-", "*", "+")):
            line = line[1:].strip()
        if line:
            items.append(line)
    return items


__all__ = ["ChatRunResult", "run_chat"]
