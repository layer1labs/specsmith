# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""specsmith.agent.token_pricing — static per-token cost lookup.

Provides a single function :func:`cost_for_tokens` that returns the estimated
USD cost for a given (provider, model, input_tokens, output_tokens) tuple.

Design contract
---------------
- ``ollama`` provider (and its aliases ``llamacpp``, ``vllm``, ``lmstudio``)
  always returns **0.0** — local inference is free; this is intentional and
  correct, not a bug or missing data.
- Known cloud models (OpenAI, Anthropic, Google) use a static pricing table
  updated to Q2 2026 list prices.
- Unknown providers/models fall back to a conservative default rate so
  ``cost_of_pass`` analysis degrades gracefully rather than crashing.

Pricing source
--------------
Q2 2026 provider pricing pages.  All figures are in USD per 1 M tokens.
Update this table when provider pricing changes (bump the table version comment).
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Pricing table — (input_usd_per_1M, output_usd_per_1M)
# Table version: 2026-Q2
# ---------------------------------------------------------------------------

#: Providers that are always zero-cost (local inference).
_FREE_PROVIDERS: frozenset[str] = frozenset({"ollama", "llamacpp", "vllm", "lmstudio", "local"})

#: Static pricing table.  Keys are normalised model name substrings matched
#: from longest to shortest so that more-specific keys win over generic ones.
_PRICING_PER_1M: dict[str, tuple[float, float]] = {
    # ── OpenAI GPT-4 family ────────────────────────────────────────────────
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1-nano": (0.10, 0.40),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4-turbo": (10.00, 30.00),
    # ── OpenAI GPT-5 family ────────────────────────────────────────────────
    "gpt-5-nano": (0.50, 2.00),
    "gpt-5-mini": (2.00, 8.00),
    "gpt-5-pro": (50.00, 200.00),
    "gpt-5.4-nano": (0.30, 1.20),
    "gpt-5.4-mini": (1.00, 4.00),
    "gpt-5.4-pro": (20.00, 80.00),
    "gpt-5.4": (5.00, 20.00),
    "gpt-5.5-pro": (15.00, 60.00),
    "gpt-5.5": (3.00, 12.00),
    "gpt-5.2-codex": (10.00, 40.00),
    "gpt-5.2-pro": (40.00, 160.00),
    "gpt-5.2": (10.00, 40.00),
    "gpt-5.3-codex": (8.00, 32.00),
    "gpt-5.1": (12.00, 48.00),
    "gpt-5-codex": (15.00, 60.00),
    "gpt-5": (15.00, 60.00),
    # ── OpenAI reasoning ──────────────────────────────────────────────────
    "o4-mini": (1.10, 4.40),
    "o3-mini": (1.10, 4.40),
    "o3": (10.00, 40.00),
    "o1": (15.00, 60.00),
    # ── Anthropic ─────────────────────────────────────────────────────────
    "claude-haiku-4-5": (0.25, 1.25),
    "claude-haiku": (0.25, 1.25),
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-sonnet": (3.00, 15.00),
    "claude-opus-4-5": (15.00, 75.00),
    "claude-opus-4-6": (15.00, 75.00),
    "claude-opus": (15.00, 75.00),
    # ── Google ────────────────────────────────────────────────────────────
    "gemini-3.5-flash": (0.15, 0.60),
    "gemini-3-flash": (0.35, 1.05),
    "gemini-flash": (0.075, 0.30),
    "gemini-3.1-pro": (1.25, 5.00),
    "gemini-pro": (1.25, 5.00),
    # ── Conservative fallback ─────────────────────────────────────────────
    "unknown": (3.00, 15.00),
}


def _lookup_rates(model: str) -> tuple[float, float]:
    """Return (input_usd_per_1M, output_usd_per_1M) for *model*.

    Tries an exact key match first, then a longest-substring match, and
    finally falls back to the ``"unknown"`` conservative default.
    """
    key = model.strip().lower()
    if key in _PRICING_PER_1M:
        return _PRICING_PER_1M[key]
    # Longest-prefix / substring match so that "gpt-4o-mini-2026-04-09"
    # still resolves to "gpt-4o-mini".
    best_match = ""
    for table_key in _PRICING_PER_1M:
        if table_key in key and len(table_key) > len(best_match):
            best_match = table_key
    if best_match:
        return _PRICING_PER_1M[best_match]
    return _PRICING_PER_1M["unknown"]


def cost_for_tokens(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Return estimated USD cost for a single LLM call.

    Args:
        provider: Provider name (e.g. ``"ollama"``, ``"openai"``, ``"anthropic"``).
        model: Model name or slug (e.g. ``"gpt-4o"``, ``"qwen2.5-coder:14b"``).
        input_tokens: Number of prompt/context tokens consumed.
        output_tokens: Number of generated/completion tokens.

    Returns:
        Estimated cost in USD.  Always ``0.0`` for local/free providers
        (Ollama, llamacpp, vllm, lmstudio, local).  Returns ``0.0`` when
        both token counts are zero regardless of provider.

    Examples::

        >>> cost_for_tokens("ollama", "qwen2.5-coder:14b", 1000, 500)
        0.0
        >>> cost_for_tokens("openai", "gpt-4o-mini", 1_000_000, 0)
        0.15
        >>> cost_for_tokens("anthropic", "claude-haiku-4-5", 0, 1_000_000)
        1.25

    """
    if not provider and not model:
        return 0.0
    if (provider or "").strip().lower() in _FREE_PROVIDERS:
        return 0.0
    if input_tokens == 0 and output_tokens == 0:
        return 0.0
    inp_per_m, out_per_m = _lookup_rates(model)
    return (input_tokens * inp_per_m + output_tokens * out_per_m) / 1_000_000


def cost_for_tokens_breakdown(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> tuple[float, float, float]:
    """Return ``(input_cost_usd, output_cost_usd, total_cost_usd)``."""
    if (provider or "").strip().lower() in _FREE_PROVIDERS:
        return 0.0, 0.0, 0.0
    inp_per_m, out_per_m = _lookup_rates(model)
    inp_cost = input_tokens * inp_per_m / 1_000_000
    out_cost = output_tokens * out_per_m / 1_000_000
    return inp_cost, out_cost, inp_cost + out_cost


def tokens_per_correct_answer(
    records: list[Any],
    *,
    token_attr: str = "tokens_total",
    passed_attr: str = "passed",
) -> float | None:
    """Compute mean tokens consumed per correct (passing) answer.

    Args:
        records: Sequence of record objects (e.g. :class:`MetricsRecord` or
            :class:`RunResult`) with numeric ``token_attr`` and bool
            ``passed_attr`` attributes.
        token_attr: Attribute name for total token count.
        passed_attr: Attribute name for pass/fail boolean.

    Returns:
        Mean total tokens among passing records, or ``None`` if no passing
        records exist.

    """
    passing = [r for r in records if getattr(r, passed_attr, False)]
    if not passing:
        return None
    totals = [getattr(r, token_attr, 0) for r in passing]
    return sum(totals) / len(totals)


__all__ = [
    "cost_for_tokens",
    "cost_for_tokens_breakdown",
    "tokens_per_correct_answer",
]
