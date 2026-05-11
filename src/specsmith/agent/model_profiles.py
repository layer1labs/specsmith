# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Model capability profiles for specsmith AEE agents (REQ-270..REQ-271).

Each profile controls how the LLM is called and how the system prompt is
structured. Profiles are matched by model name prefix (longest match wins).

Fields
------
max_tokens       Maximum tokens to generate in a single response.
temperature      Sampling temperature. Low for structured tasks (0.1-0.2).
ctx_budget       Approx. chars of conversation history to keep (messages
                 trimmed oldest-first if over budget). 1 token ≈ 4 chars.
action_capable   Whether the model reliably produces structured JSON actions.
                 False = action addendum stripped from system prompt.
prompt_style     How to format the system prompt:
                   "plain"    – single paragraph
                   "sections" – ### headings + ---- separators (Mistral-style)
                   "xml"      – <context>/<instructions> tags (Claude-style)
"""

from __future__ import annotations

from typing import TypedDict


class ModelProfile(TypedDict):
    max_tokens: int
    temperature: float
    ctx_budget: int
    action_capable: bool
    prompt_style: str


# ── Per-model profiles (prefix matched, longest key wins) ─────────────────

_PROFILES: dict[str, ModelProfile] = {
    # ── Mistral (Ollama) ──────────────────────────────────────────────────
    "mistral-nemo": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 24000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "mistral:7b": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 6000,
        "action_capable": False,
        "prompt_style": "sections",
    },
    "mistral:latest": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 6000,
        "action_capable": False,
        "prompt_style": "sections",
    },
    # ── Qwen 2.5 (Ollama) ─────────────────────────────────────────────────
    "qwen2.5:72b": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 20000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "qwen2.5:32b": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 16000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "qwen2.5:14b": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 12000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "qwen2.5:7b": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 6000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "qwen2.5:3b": {
        "max_tokens": 1024,
        "temperature": 0.25,
        "ctx_budget": 3000,
        "action_capable": False,
        "prompt_style": "plain",
    },
    "qwen2.5-coder:32b": {
        "max_tokens": 4096,
        "temperature": 0.10,
        "ctx_budget": 16000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "qwen2.5": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 8000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    # ── Qwen 3 (Ollama) ───────────────────────────────────────────────────
    "qwen3:30b-a3b": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 20000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "qwen3:8b": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 8000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "qwen3:4b": {
        "max_tokens": 1024,
        "temperature": 0.25,
        "ctx_budget": 4000,
        "action_capable": False,
        "prompt_style": "plain",
    },
    "qwen3": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 8000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    # ── Llama 3 (Ollama) ──────────────────────────────────────────────────
    "llama3.3": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 16000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "llama3.2:3b": {
        "max_tokens": 1024,
        "temperature": 0.25,
        "ctx_budget": 3000,
        "action_capable": False,
        "prompt_style": "plain",
    },
    "llama3.2:1b": {
        "max_tokens": 768,
        "temperature": 0.30,
        "ctx_budget": 2000,
        "action_capable": False,
        "prompt_style": "plain",
    },
    "llama3.2": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 8000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "llama3.1": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 8000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "llama3": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 8000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    # ── Gemma (Ollama) ────────────────────────────────────────────────────
    "gemma3:27b": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 16000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "gemma3:12b": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 8000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "gemma3": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 8000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    # ── Phi (Ollama) ──────────────────────────────────────────────────────
    "phi4": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 12000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "phi3.5": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 6000,
        "action_capable": False,
        "prompt_style": "plain",
    },
    # ── DeepSeek (Ollama) ─────────────────────────────────────────────────
    "deepseek-r1:70b": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 20000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "deepseek-r1:32b": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 16000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "deepseek-r1:14b": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 12000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "deepseek-r1:7b": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 6000,
        "action_capable": False,
        "prompt_style": "sections",
    },
    # ── Mistral API ───────────────────────────────────────────────────────
    "mistral-large": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 24000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "mistral-medium": {
        "max_tokens": 4096,
        "temperature": 0.18,
        "ctx_budget": 16000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "mistral-small": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 8000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "codestral": {
        "max_tokens": 4096,
        "temperature": 0.10,
        "ctx_budget": 16000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    # ── OpenAI ────────────────────────────────────────────────────────────
    "gpt-4o": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 32000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "gpt-4.1": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 32000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "gpt-4-turbo": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 32000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "gpt-4": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 16000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "gpt-3.5": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 8000,
        "action_capable": False,
        "prompt_style": "plain",
    },
    # o-series: temperature is effectively ignored (always 1), large reasoning ctx
    "o1": {
        "max_tokens": 4096,
        "temperature": 1.0,
        "ctx_budget": 32000,
        "action_capable": True,
        "prompt_style": "plain",
    },
    "o3": {
        "max_tokens": 4096,
        "temperature": 1.0,
        "ctx_budget": 32000,
        "action_capable": True,
        "prompt_style": "plain",
    },
    "o4": {
        "max_tokens": 4096,
        "temperature": 1.0,
        "ctx_budget": 32000,
        "action_capable": True,
        "prompt_style": "plain",
    },
    # ── Anthropic ─────────────────────────────────────────────────────────
    "claude-sonnet-4": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 32000,
        "action_capable": True,
        "prompt_style": "xml",
    },
    "claude-opus-4": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 32000,
        "action_capable": True,
        "prompt_style": "xml",
    },
    "claude-haiku-4": {
        "max_tokens": 4096,
        "temperature": 0.18,
        "ctx_budget": 16000,
        "action_capable": True,
        "prompt_style": "xml",
    },
    "claude-3-5-sonnet": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 32000,
        "action_capable": True,
        "prompt_style": "xml",
    },
    "claude-3-5-haiku": {
        "max_tokens": 4096,
        "temperature": 0.18,
        "ctx_budget": 16000,
        "action_capable": True,
        "prompt_style": "xml",
    },
    "claude-3-opus": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 32000,
        "action_capable": True,
        "prompt_style": "xml",
    },
    "claude-3-haiku": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 8000,
        "action_capable": True,
        "prompt_style": "xml",
    },
    "claude-3": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 16000,
        "action_capable": True,
        "prompt_style": "xml",
    },
    # ── Google Gemini ─────────────────────────────────────────────────────
    "gemini-2.5-pro": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 48000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "gemini-2.5-flash": {
        "max_tokens": 4096,
        "temperature": 0.18,
        "ctx_budget": 32000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "gemini-2.0-flash": {
        "max_tokens": 4096,
        "temperature": 0.18,
        "ctx_budget": 24000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "gemini-1.5-pro": {
        "max_tokens": 4096,
        "temperature": 0.15,
        "ctx_budget": 48000,
        "action_capable": True,
        "prompt_style": "sections",
    },
    "gemini-1.5-flash": {
        "max_tokens": 2048,
        "temperature": 0.20,
        "ctx_budget": 24000,
        "action_capable": True,
        "prompt_style": "sections",
    },
}

# Sensible fallback for unknown models
_DEFAULT: ModelProfile = {
    "max_tokens": 2500,
    "temperature": 0.25,
    "ctx_budget": 6000,
    "action_capable": True,
    "prompt_style": "sections",
}


def get_profile(model: str | None) -> ModelProfile:
    """Return the capability profile for *model*, matching by prefix (longest key first)."""
    if not model:
        return _DEFAULT
    for key in sorted(_PROFILES, key=len, reverse=True):
        if model.lower().startswith(key.lower()):
            return _PROFILES[key]
    return _DEFAULT


def trim_history(
    messages: list[dict[str, str]],
    budget_chars: int,
) -> list[dict[str, str]]:
    """Trim conversation history to fit within budget_chars (approx. tokens × 4).

    When the conversation exceeds the budget the oldest turns are collapsed
    into a compact summary note rather than silently dropped.  The system
    message (role=="system") is always kept intact.

    budget_chars approximates token count at 4 chars/token.
    """
    system = [m for m in messages if m.get("role") == "system"]
    convo = [m for m in messages if m.get("role") != "system"]

    total = sum(len(m.get("content", "")) for m in convo)
    if total <= budget_chars:
        return system + convo

    # Collect oldest messages to summarise
    summarised: list[str] = []
    while total > budget_chars * 0.9 and len(convo) > 2:
        removed = convo.pop(0)
        role_label = "User" if removed.get("role") == "user" else "Assistant"
        snippet = removed.get("content", "")[:120].replace("\n", " ")
        summarised.append(f"{role_label}: {snippet}...")
        total -= len(removed.get("content", ""))

    if summarised:
        summary_note = (
            f"[Earlier conversation summary — {len(summarised)} turns condensed]\n"
            + "\n".join(summarised)
        )
        convo.insert(0, {"role": "assistant", "content": summary_note})

    return system + convo


__all__ = [
    "ModelProfile",
    "_DEFAULT",
    "_PROFILES",
    "get_profile",
    "trim_history",
]
