# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for specsmith.agent.token_pricing and related cost metrics.

Covers:
  - cost_for_tokens() with known OpenAI / Anthropic / Google models
  - Ollama (and local aliases) always returns 0.0
  - Unknown provider safe fallback (conservative default)
  - Unknown model safe fallback
  - cost_for_tokens_breakdown() tuple decomposition
  - tokens_per_correct_answer() helper
  - MetricsStore.cost_of_pass() with mixed Ollama/OpenAI records:
      Ollama records (cost_usd=0.0) are excluded from the costed denominator,
      so cost_of_pass reflects only cloud-API sessions.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from specsmith.agent.token_pricing import (
    _FREE_PROVIDERS,
    _PRICING_PER_1M,
    cost_for_tokens,
    cost_for_tokens_breakdown,
    tokens_per_correct_answer,
)
from specsmith.project_metrics import MetricsRecord, MetricsStore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_1M = 1_000_000


def _usd(model: str, inp: int, out: int) -> float:
    """Expected USD from _PRICING_PER_1M for testing arithmetic."""
    inp_r, out_r = _PRICING_PER_1M.get(model, _PRICING_PER_1M["unknown"])
    return (inp * inp_r + out * out_r) / _1M


# ---------------------------------------------------------------------------
# Free providers (Ollama and local aliases)
# ---------------------------------------------------------------------------


class TestFreeProviders:
    def test_ollama_is_in_free_set(self) -> None:
        assert "ollama" in _FREE_PROVIDERS

    def test_local_aliases_in_free_set(self) -> None:
        for alias in ("llamacpp", "vllm", "lmstudio", "local"):
            assert alias in _FREE_PROVIDERS, f"{alias!r} must be a free provider"

    @pytest.mark.parametrize("provider", ["ollama", "llamacpp", "vllm", "lmstudio", "local"])
    def test_free_provider_always_zero(self, provider: str) -> None:
        cost = cost_for_tokens(provider, "qwen2.5-coder:14b", 10_000, 5_000)
        assert cost == 0.0, f"Expected 0.0 for {provider!r}"

    def test_ollama_zero_regardless_of_model(self) -> None:
        """Any model string paired with ollama must return 0.0."""
        for model in ("gpt-4o", "claude-opus", "qwen3:30b-a3b", ""):
            assert cost_for_tokens("ollama", model, 1_000, 500) == 0.0

    def test_ollama_case_insensitive(self) -> None:
        assert cost_for_tokens("OLLAMA", "qwen:7b", 1_000, 500) == 0.0

    def test_free_provider_breakdown_all_zeros(self) -> None:
        inp, out, total = cost_for_tokens_breakdown("ollama", "qwen:7b", 5_000, 2_000)
        assert inp == 0.0 and out == 0.0 and total == 0.0


# ---------------------------------------------------------------------------
# Known cloud models — OpenAI
# ---------------------------------------------------------------------------


class TestOpenAIPricing:
    def test_gpt4o_mini_input_only(self) -> None:
        expected = 0.15 / _1M * _1M  # 0.15 per 1M → $0.15 for exactly 1M tokens
        cost = cost_for_tokens("openai", "gpt-4o-mini", _1M, 0)
        assert abs(cost - expected) < 1e-10

    def test_gpt4o_output_only(self) -> None:
        expected = 10.00 / _1M * _1M
        cost = cost_for_tokens("openai", "gpt-4o", 0, _1M)
        assert abs(cost - expected) < 1e-10

    def test_gpt4o_combined(self) -> None:
        inp_tokens = 500_000
        out_tokens = 200_000
        expected = _usd("gpt-4o", inp_tokens, out_tokens)
        cost = cost_for_tokens("openai", "gpt-4o", inp_tokens, out_tokens)
        assert abs(cost - expected) < 1e-10

    def test_gpt41_mini(self) -> None:
        expected = _usd("gpt-4.1-mini", 1_000_000, 500_000)
        cost = cost_for_tokens("openai", "gpt-4.1-mini", 1_000_000, 500_000)
        assert abs(cost - expected) < 1e-10

    def test_gpt5_model(self) -> None:
        expected = _usd("gpt-5", 100_000, 50_000)
        cost = cost_for_tokens("openai", "gpt-5", 100_000, 50_000)
        assert abs(cost - expected) < 1e-10

    def test_versioned_suffix_resolves(self) -> None:
        """'gpt-4o-mini-2026-04-09' should match 'gpt-4o-mini' via substring."""
        expected = _usd("gpt-4o-mini", 100_000, 50_000)
        cost = cost_for_tokens("openai", "gpt-4o-mini-2026-04-09", 100_000, 50_000)
        assert abs(cost - expected) < 1e-10


# ---------------------------------------------------------------------------
# Known cloud models — Anthropic
# ---------------------------------------------------------------------------


class TestAnthropicPricing:
    def test_claude_haiku_45(self) -> None:
        expected = _usd("claude-haiku-4-5", 0, _1M)  # $1.25 per 1M output
        cost = cost_for_tokens("anthropic", "claude-haiku-4-5", 0, _1M)
        assert abs(cost - expected) < 1e-10

    def test_claude_sonnet_45(self) -> None:
        expected = _usd("claude-sonnet-4-5", 200_000, 100_000)
        cost = cost_for_tokens("anthropic", "claude-sonnet-4-5", 200_000, 100_000)
        assert abs(cost - expected) < 1e-10

    def test_claude_opus(self) -> None:
        expected = _usd("claude-opus", 50_000, 25_000)
        cost = cost_for_tokens("anthropic", "claude-opus", 50_000, 25_000)
        assert abs(cost - expected) < 1e-10

    def test_provider_does_not_affect_model_lookup(self) -> None:
        """Provider string only gates free-provider check; model lookup is independent."""
        # Passing "anthropic" vs "openai" with the same model name should give same result.
        cost_a = cost_for_tokens("anthropic", "claude-haiku-4-5", 100_000, 50_000)
        cost_b = cost_for_tokens("openai", "claude-haiku-4-5", 100_000, 50_000)
        assert abs(cost_a - cost_b) < 1e-12


# ---------------------------------------------------------------------------
# Known cloud models — Google
# ---------------------------------------------------------------------------


class TestGooglePricing:
    def test_gemini_3_flash(self) -> None:
        expected = _usd("gemini-3-flash", 500_000, 200_000)
        cost = cost_for_tokens("google", "gemini-3-flash", 500_000, 200_000)
        assert abs(cost - expected) < 1e-10

    def test_gemini_35_flash(self) -> None:
        cost = cost_for_tokens("google", "gemini-3.5-flash", _1M, _1M)
        expected = (0.15 + 0.60) / _1M * _1M
        assert abs(cost - expected) < 1e-10


# ---------------------------------------------------------------------------
# Unknown / fallback
# ---------------------------------------------------------------------------


class TestUnknownFallback:
    def test_unknown_provider_uses_conservative_default(self) -> None:
        """Unknown provider with unknown model falls back to conservative rate."""
        cost = cost_for_tokens("acme-ai", "totally-made-up-model", _1M, 0)
        expected = _usd("unknown", _1M, 0)
        assert abs(cost - expected) < 1e-10

    def test_empty_provider_empty_model_is_zero(self) -> None:
        assert cost_for_tokens("", "", 1_000, 500) == 0.0

    def test_zero_tokens_always_zero(self) -> None:
        for provider, model in [("openai", "gpt-4o"), ("anthropic", "claude-opus")]:
            assert cost_for_tokens(provider, model, 0, 0) == 0.0

    def test_unknown_model_known_provider_uses_fallback_rate(self) -> None:
        """Provider 'openai' but model not in table → conservative default."""
        cost = cost_for_tokens("openai", "gpt-99-ultra-fictional", 100_000, 50_000)
        expected = _usd("unknown", 100_000, 50_000)
        assert abs(cost - expected) < 1e-10


# ---------------------------------------------------------------------------
# Breakdown
# ---------------------------------------------------------------------------


class TestBreakdown:
    def test_breakdown_sums_to_total(self) -> None:
        inp, out, total = cost_for_tokens_breakdown("openai", "gpt-4o", 300_000, 100_000)
        assert abs(inp + out - total) < 1e-12

    def test_breakdown_input_output_correct(self) -> None:
        inp_r, out_r = _PRICING_PER_1M["gpt-4o"]
        inp, out, total = cost_for_tokens_breakdown("openai", "gpt-4o", 200_000, 80_000)
        assert abs(inp - 200_000 * inp_r / _1M) < 1e-12
        assert abs(out - 80_000 * out_r / _1M) < 1e-12

    def test_breakdown_zero_for_ollama(self) -> None:
        inp, out, total = cost_for_tokens_breakdown("ollama", "qwen:7b", 10_000, 5_000)
        assert inp == out == total == 0.0


# ---------------------------------------------------------------------------
# tokens_per_correct_answer helper
# ---------------------------------------------------------------------------


class TestTokensPerCorrectAnswer:
    def _rec(self, tokens: int, passed: bool) -> SimpleNamespace:
        return SimpleNamespace(tokens_total=tokens, passed=passed)

    def test_returns_none_when_no_passing(self) -> None:
        records = [self._rec(1000, False), self._rec(2000, False)]
        assert tokens_per_correct_answer(records) is None

    def test_mean_over_passing_records(self) -> None:
        records = [
            self._rec(1000, True),
            self._rec(3000, True),
            self._rec(9999, False),  # should be excluded
        ]
        result = tokens_per_correct_answer(records)
        assert result is not None
        assert abs(result - 2000.0) < 1e-9

    def test_single_passing_record(self) -> None:
        records = [self._rec(500, True)]
        assert tokens_per_correct_answer(records) == 500.0

    def test_empty_records(self) -> None:
        assert tokens_per_correct_answer([]) is None

    def test_custom_attribute_names(self) -> None:
        rec = SimpleNamespace(tok=800, ok=True)
        result = tokens_per_correct_answer([rec], token_attr="tok", passed_attr="ok")
        assert result == 800.0


# ---------------------------------------------------------------------------
# MetricsStore.cost_of_pass() with mixed Ollama/OpenAI records
# ---------------------------------------------------------------------------


class TestCostOfPassMixedProviders:
    """Verify that Ollama records (cost_usd=0.0) are correctly excluded from
    the costed denominator so cost_of_pass reflects only cloud-API runs."""

    def _store(self, tmp_path: Path, records: list[MetricsRecord]) -> MetricsStore:
        store = MetricsStore(tmp_path)
        for r in records:
            store.append(r)
        return store

    def test_ollama_records_excluded_from_costed(self, tmp_path: Path) -> None:
        """Ollama sessions (cost_usd=0.0) must not inflate the denominator."""
        records = [
            # Ollama sessions — free, should be excluded from cost_of_pass denominator
            MetricsRecord.new(cost_usd=0.0, passed=True, model="qwen2.5-coder:14b"),
            MetricsRecord.new(cost_usd=0.0, passed=True, model="qwen3:30b-a3b"),
            MetricsRecord.new(cost_usd=0.0, passed=False, model="qwen2.5-coder:14b"),
            # OpenAI sessions — priced, included in cost_of_pass
            MetricsRecord.new(cost_usd=0.05, passed=True, model="gpt-4o-mini"),
            MetricsRecord.new(cost_usd=0.08, passed=False, model="gpt-4o-mini"),
        ]
        store = self._store(tmp_path, records)
        # Costed records: only the two with cost_usd > 0
        # pass_rate among costed = 1/2 = 0.5
        # mean_cost among costed = (0.05 + 0.08) / 2 = 0.065
        # cost_of_pass = 0.065 / 0.5 = 0.13
        cop = store.cost_of_pass()
        assert abs(cop - 0.13) < 1e-9

    def test_all_ollama_records_returns_inf(self, tmp_path: Path) -> None:
        """When all sessions are zero-cost (Ollama), cost_of_pass is inf."""
        records = [
            MetricsRecord.new(cost_usd=0.0, passed=True),
            MetricsRecord.new(cost_usd=0.0, passed=True),
            MetricsRecord.new(cost_usd=0.0, passed=False),
        ]
        store = self._store(tmp_path, records)
        assert store.cost_of_pass() == float("inf")

    def test_zero_pass_rate_in_costed_returns_inf(self, tmp_path: Path) -> None:
        """Cloud sessions that all fail → cost_of_pass = inf."""
        records = [
            MetricsRecord.new(cost_usd=0.05, passed=False),
            MetricsRecord.new(cost_usd=0.10, passed=False),
        ]
        store = self._store(tmp_path, records)
        assert store.cost_of_pass() == float("inf")

    def test_cost_of_pass_pure_openai_sessions(self, tmp_path: Path) -> None:
        """Sanity check: 100% pass rate on costed records → cost_of_pass = mean_cost."""
        records = [
            MetricsRecord.new(cost_usd=0.10, passed=True),
            MetricsRecord.new(cost_usd=0.20, passed=True),
        ]
        store = self._store(tmp_path, records)
        # mean_cost = 0.15, pass_rate = 1.0 → cost_of_pass = 0.15
        assert abs(store.cost_of_pass() - 0.15) < 1e-10

    def test_tokens_per_correct_answer_uses_all_records(self, tmp_path: Path) -> None:
        """tokens_per_correct_answer counts across ALL models (Ollama + cloud)."""
        records = [
            MetricsRecord.new(input_tokens=1000, output_tokens=500, passed=True),
            MetricsRecord.new(input_tokens=2000, output_tokens=1000, passed=True),
            MetricsRecord.new(input_tokens=9999, output_tokens=9999, passed=False),
        ]
        result = tokens_per_correct_answer(records)
        assert result is not None
        # mean tokens_total for passing: (1500 + 3000) / 2 = 2250.0
        assert abs(result - 2250.0) < 1e-9
