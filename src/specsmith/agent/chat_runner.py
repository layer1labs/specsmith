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

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "summary": self.summary,
            "files_changed": list(self.files_changed),
            "confidence": self.verdict.confidence if self.verdict else 0.0,
            "equilibrium": self.verdict.equilibrium if self.verdict else False,
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
) -> ChatRunResult | None:
    """Drive a real LLM turn. Return ``None`` if no provider is reachable."""
    history = history or []
    messages = _build_messages(utterance, history, rules_prefix)

    # Order matters: Ollama first because it's local-first and free.
    for provider in (_run_ollama, _run_anthropic, _run_openai, _run_gemini):
        try:
            full_text = provider(messages, emitter, msg_block)
        except Exception:  # noqa: BLE001 - any failure → next provider
            continue
        if full_text is None:
            continue
        return _finalize(full_text, provider.__name__, project_dir, confidence_target)
    return None


def _finalize(
    full_text: str,
    provider_fn_name: str,
    project_dir: Path,
    confidence_target: float,
) -> ChatRunResult:
    sections = _parse_output_contract(full_text)
    files_changed = _split_files_list(sections.get("files_changed", ""))
    report = report_from_chat_sections(sections, files_changed=files_changed)
    verdict = score(report, confidence_target=confidence_target)
    summary = (sections.get("plan") or full_text.strip()[:200]).strip() or verdict.summary
    return ChatRunResult(
        provider=provider_fn_name.removeprefix("_run_"),
        summary=summary,
        files_changed=files_changed,
        verdict=verdict,
        raw_text=full_text,
    )


# ---------------------------------------------------------------------------
# Provider drivers — each returns the full assembled text or None
# ---------------------------------------------------------------------------


def _run_ollama(
    messages: list[dict[str, str]],
    emitter: EventEmitter,
    block_id: str,
) -> str | None:
    """Stream from a local Ollama daemon using only stdlib."""
    host = os.environ.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST).rstrip("/")
    model = os.environ.get("SPECSMITH_OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)

    if not _ollama_alive(host):
        return None

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
                break
    return "".join(pieces) if pieces else None


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
) -> str | None:
    """Use the anthropic SDK if installed and a key is configured."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None

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
    return "".join(pieces) if pieces else None


def _run_openai(
    messages: list[dict[str, str]],
    emitter: EventEmitter,
    block_id: str,
) -> str | None:
    """Use the openai SDK if installed and a key is configured."""
    if not os.environ.get("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None

    client = OpenAI()
    stream = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        messages=messages,
        stream=True,
    )
    pieces: list[str] = []
    for chunk in stream:
        text = (chunk.choices[0].delta.content or "") if chunk.choices else ""
        if text:
            emitter.token(block_id, text)
            pieces.append(text)
    return "".join(pieces) if pieces else None


def _run_gemini(
    messages: list[dict[str, str]],
    emitter: EventEmitter,
    block_id: str,
) -> str | None:
    """Use google-genai SDK if installed and a key is configured."""
    if not os.environ.get("GOOGLE_API_KEY"):
        return None
    try:
        from google import genai
    except ImportError:
        return None

    client = genai.Client()
    prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    pieces: list[str] = []
    for chunk in client.models.generate_content_stream(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=prompt,
    ):
        text = getattr(chunk, "text", "") or ""
        if text:
            emitter.token(block_id, text)
            pieces.append(text)
    return "".join(pieces) if pieces else None


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
