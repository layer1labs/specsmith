# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for src/specsmith/agent/optimizer.py — REQ-OPT-001 through REQ-OPT-013."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import pytest

from specsmith.agent.optimizer import (
    ComplexityTier,
    ContextManager,
    ModelRouter,
    OptimizationConfig,
    OptimizationEngine,
    OptimizationReport,
    ResponseCache,
    TokenEstimator,
    ToolFilter,
    _get_role,
    estimate_session_savings,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


@dataclass
class _Msg:
    role: str
    content: str


def _msgs(*pairs: tuple[str, str]) -> list[_Msg]:
    return [_Msg(role=r, content=c) for r, c in pairs]


@dataclass
class _Tool:
    name: str
    description: str = ""


# ── TEST-OPT-001: TokenEstimator.estimate() ──────────────────────────────────


class TestTokenEstimator:
    def test_estimate_non_empty(self):
        """Covers REQ-OPT-001: estimate returns positive int for non-empty text."""
        est = TokenEstimator()
        assert est.estimate("Hello world") > 0

    def test_estimate_empty(self):
        est = TokenEstimator()
        assert est.estimate("") == 0

    def test_estimate_gpt4_ratio(self):
        """GPT-4 uses ~0.25 tokens/char (4 chars/token)."""
        est = TokenEstimator()
        text = "a" * 400  # 400 chars → ~100 tokens at 4 chars/token
        result = est.estimate(text, model="gpt-4o")
        assert 80 <= result <= 120, f"Expected ~100 tokens, got {result}"

    def test_estimate_claude_ratio(self):
        """Claude uses ~3.8 chars/token (slightly more compressed)."""
        est = TokenEstimator()
        text = "a" * 380  # 380 chars → ~100 tokens at 3.8 chars/token
        result = est.estimate(text, model="claude-sonnet-4-5")
        assert 80 <= result <= 120, f"Expected ~100 tokens, got {result}"

    def test_estimate_messages(self):
        est = TokenEstimator()
        msgs = _msgs(("system", "You are a helper."), ("user", "What is 2+2?"))
        total = est.estimate_messages(msgs)
        assert total > 0

    def test_estimate_messages_adds_overhead(self):
        """Each message adds 4-token overhead."""
        est = TokenEstimator()
        msgs = _msgs(("user", ""))  # empty content, just overhead
        total = est.estimate_messages(msgs)
        assert total >= 4  # at minimum the overhead


# ── TEST-OPT-002: TokenEstimator.estimate_cost() ─────────────────────────────


class TestTokenEstimatorCost:
    def test_estimate_cost_anthropic(self):
        """Covers REQ-OPT-001: estimate_cost returns expected USD."""
        est = TokenEstimator()
        # claude-sonnet-4-5: $3/M input, $15/M output
        # 1M input + 1M output = $18
        cost = est.estimate_cost(1_000_000, 1_000_000, "anthropic", "claude-sonnet-4-5")
        assert abs(cost - 18.0) < 0.01

    def test_estimate_cost_openai(self):
        est = TokenEstimator()
        # gpt-4o: $2.50/M input, $10/M output
        cost = est.estimate_cost(1_000_000, 0, "openai", "gpt-4o")
        assert abs(cost - 2.5) < 0.01

    def test_estimate_cost_zero(self):
        est = TokenEstimator()
        assert est.estimate_cost(0, 0, "anthropic", "claude-haiku-4-5") == 0.0

    def test_estimate_cost_unknown_model_uses_default(self):
        est = TokenEstimator()
        cost = est.estimate_cost(1_000_000, 0, "anthropic", "unknown-model-xyz")
        assert cost > 0  # falls back to provider default


# ── TEST-OPT-003: ResponseCache cold/warm hit ─────────────────────────────────


class TestResponseCacheColdWarm:
    def test_cold_miss(self):
        """Covers REQ-OPT-002: get() returns None on cold cache."""
        cache = ResponseCache()
        assert cache.get("nonexistent_key") is None

    def test_warm_hit(self):
        """Covers REQ-OPT-002: returns response string on warm hit."""
        cache = ResponseCache()
        cache.set("k1", "The answer is 42", in_tokens=100, out_tokens=20)
        result = cache.get("k1")
        assert result == "The answer is 42"

    def test_hit_increments_counter(self):
        cache = ResponseCache()
        cache.set("k1", "hello")
        cache.get("k1")
        assert cache.hit_rate == pytest.approx(1.0)

    def test_miss_increments_counter(self):
        cache = ResponseCache()
        cache.get("no_such_key")
        assert cache.hit_rate == pytest.approx(0.0)

    def test_cache_key_stable(self):
        """Same inputs produce the same key."""
        cache = ResponseCache()
        msgs = _msgs(("user", "hello"))
        k1 = cache.cache_key("anthropic", "claude-haiku-4-5", msgs)
        k2 = cache.cache_key("anthropic", "claude-haiku-4-5", msgs)
        assert k1 == k2

    def test_cache_key_differs_by_model(self):
        cache = ResponseCache()
        msgs = _msgs(("user", "hello"))
        k1 = cache.cache_key("anthropic", "claude-haiku-4-5", msgs)
        k2 = cache.cache_key("anthropic", "claude-sonnet-4-5", msgs)
        assert k1 != k2


# ── TEST-OPT-004: ResponseCache records savings ───────────────────────────────


class TestResponseCacheSavings:
    def test_tokens_saved_on_hit(self):
        """Covers REQ-OPT-002: records tokens_saved on cache hit."""
        cache = ResponseCache()
        cache.set("k1", "response", in_tokens=500, out_tokens=100)
        cache.get("k1")  # hit
        assert cache.tokens_saved == 600

    def test_cost_saved_on_hit(self):
        """Covers REQ-OPT-002: records cost_saved on cache hit."""
        cache = ResponseCache()
        cache.set("k1", "response", cost_usd=0.0015)
        cache.get("k1")
        assert cache.cost_saved == pytest.approx(0.0015, abs=1e-6)


# ── TEST-OPT-005: ResponseCache TTL expiry ────────────────────────────────────


class TestResponseCacheTTL:
    def test_entry_expires(self):
        """Covers REQ-OPT-003: expires entries after TTL seconds."""
        cache = ResponseCache(ttl_seconds=1)
        cache.set("k1", "value")
        assert cache.get("k1") == "value"  # immediate hit
        # Manually expire by patching the internal entry
        cache._cache["k1"]["expires"] = time.time() - 1
        assert cache.get("k1") is None  # expired

    def test_evict_expired_returns_count(self):
        cache = ResponseCache(ttl_seconds=1)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache._cache["k1"]["expires"] = time.time() - 1  # expire k1
        removed = cache.evict_expired()
        assert removed == 1
        assert cache.get("k2") == "v2"


# ── TEST-OPT-006 / OPT-007: ContextManager.trim() ────────────────────────────


class TestContextManagerTrim:
    def test_trim_reduces_messages_when_over_limit(self):
        """Covers REQ-OPT-004: trim returns fewer messages when over max_tokens."""
        cm = ContextManager(max_tokens=20)  # very tight budget
        # Build messages whose total exceeds 20 tokens
        msgs = _msgs(
            ("system", "You are a helper."),
            ("user", "message 1"),
            ("assistant", "response 1"),
            ("user", "message 2"),
            ("assistant", "response 2"),
        )
        trimmed, removed = cm.trim(msgs)
        assert len(trimmed) < len(msgs)
        assert removed > 0

    def test_trim_preserves_system_message(self):
        """Covers REQ-OPT-004: always preserves system message."""
        cm = ContextManager(max_tokens=10)  # extremely tight
        msgs = _msgs(
            ("system", "System prompt that must always be kept."),
            ("user", "user 1"),
            ("assistant", "assistant 1"),
        )
        trimmed, _ = cm.trim(msgs)
        roles = [_get_role(m) for m in trimmed]
        assert "system" in roles

    def test_no_trim_when_under_limit(self):
        """No trimming when within budget."""
        cm = ContextManager(max_tokens=100_000)
        msgs = _msgs(("user", "hi"), ("assistant", "hello"))
        trimmed, removed = cm.trim(msgs)
        assert removed == 0
        assert len(trimmed) == len(msgs)


# ── TEST-OPT-008: ContextManager.needs_summarization() ───────────────────────


class TestContextManagerSummarize:
    def test_needs_summarization_true_when_over_threshold(self):
        """Covers REQ-OPT-005: returns True when over threshold."""
        cm = ContextManager(summarize_threshold=5)  # tiny threshold
        # Build messages that exceed 5 tokens
        msgs = _msgs(
            ("user", "This is a fairly long message that should exceed the threshold"),
            ("assistant", "A fairly long response that pushes over the token limit"),
        )
        assert cm.needs_summarization(msgs) is True

    def test_needs_summarization_false_when_under_threshold(self):
        cm = ContextManager(summarize_threshold=100_000)
        msgs = _msgs(("user", "hi"))
        assert cm.needs_summarization(msgs) is False

    def test_summarization_prompt_format(self):
        cm = ContextManager()
        msgs = _msgs(("user", "hello"), ("assistant", "hi"))
        prompt = cm.summarization_prompt(msgs)
        assert "Summarise" in prompt or "summarise" in prompt.lower()
        assert "[user]" in prompt.lower() or "user" in prompt


# ── TEST-OPT-009: ModelRouter.classify() ─────────────────────────────────────


class TestModelRouterClassify:
    def test_fast_for_short_input(self):
        """Covers REQ-OPT-006: FAST for short/simple inputs."""
        router = ModelRouter(min_input_length=20)
        result = router.classify("hi")
        assert result == ComplexityTier.FAST

    def test_fast_for_simple_audit_query(self):
        router = ModelRouter()
        result = router.classify("run audit and validate")
        assert result in (ComplexityTier.FAST, ComplexityTier.BALANCED)

    def test_powerful_for_architecture_keyword(self):
        """Covers REQ-OPT-006: POWERFUL for architecture keywords."""
        router = ModelRouter()
        result = router.classify("design the overall system architecture for this project")
        assert result == ComplexityTier.POWERFUL

    def test_powerful_for_long_input(self):
        router = ModelRouter()
        long_input = "word " * 200  # 200 words
        result = router.classify(long_input)
        assert result == ComplexityTier.POWERFUL

    def test_balanced_for_medium_input(self):
        router = ModelRouter()
        result = router.classify(
            "Please write a function that reads a file and counts lines in Python"
        )
        assert result in (ComplexityTier.BALANCED, ComplexityTier.POWERFUL)


# ── TEST-OPT-010: ModelRouter.suggest_model() ────────────────────────────────


class TestModelRouterSuggestModel:
    def test_anthropic_fast_is_haiku(self):
        """Covers REQ-OPT-007: haiku/mini/flash for FAST tier per provider."""
        router = ModelRouter()
        model = router.suggest_model("anthropic", ComplexityTier.FAST)
        assert "haiku" in model.lower()

    def test_openai_fast_is_mini(self):
        router = ModelRouter()
        model = router.suggest_model("openai", ComplexityTier.FAST)
        assert "mini" in model.lower()

    def test_gemini_fast_is_flash(self):
        router = ModelRouter()
        model = router.suggest_model("gemini", ComplexityTier.FAST)
        assert "flash" in model.lower()

    def test_powerful_tier_returns_flagship(self):
        router = ModelRouter()
        model = router.suggest_model("anthropic", ComplexityTier.POWERFUL)
        assert "opus" in model.lower()


# ── TEST-OPT-011: ToolFilter.select() ────────────────────────────────────────


class TestToolFilter:
    def test_returns_subset_when_many_tools(self):
        """Covers REQ-OPT-008: returns subset."""
        tf = ToolFilter(max_tools=3)
        tools = [_Tool(name=f"tool_{i}") for i in range(10)]
        result = tf.select(tools, "audit the project")
        assert len(result) <= 3

    def test_returns_all_when_few_tools(self):
        """Returns all tools when count ≤ max_tools."""
        tf = ToolFilter(max_tools=10)
        tools = [_Tool(name="audit"), _Tool(name="validate")]
        result = tf.select(tools, "any task")
        assert len(result) == 2

    def test_governance_tools_ranked_higher_for_audit_task(self):
        """Covers REQ-OPT-008: governance tools ranked higher for audit tasks."""
        tf = ToolFilter(max_tools=3)
        tools = [
            _Tool(name="audit", description="run governance audit"),
            _Tool(name="validate", description="check governance consistency"),
            _Tool(name="doctor", description="check tools installed"),
            _Tool(name="run_command", description="execute shell command"),
            _Tool(name="write_file", description="write a file"),
            _Tool(name="unrelated_tool", description="does something unrelated"),
        ]
        result = tf.select(tools, "run audit and check governance health")
        result_names = {t.name for t in result}
        assert "audit" in result_names or "validate" in result_names

    def test_filesystem_tools_always_included(self):
        """run_command and write_file get base boost."""
        tf = ToolFilter(max_tools=5)
        tools = [
            _Tool(name="run_command"),
            _Tool(name="write_file"),
            _Tool(name="read_file"),
            _Tool(name="list_dir"),
            _Tool(name="grep_files"),
            _Tool(name="obscure_tool_a"),
            _Tool(name="obscure_tool_b"),
        ]
        result = tf.select(tools, "help me with the project")
        result_names = {t.name for t in result}
        # At least 3 filesystem tools should be included
        fs_tools = {"run_command", "write_file", "read_file", "list_dir", "grep_files"}
        assert len(result_names & fs_tools) >= 3


# ── TEST-OPT-012: OptimizationEngine.pre_call() cache hit ────────────────────


class TestOptimizationEngineCacheHit:
    def test_cache_hit_on_repeated_call(self):
        """Covers REQ-OPT-009: cache hit skips model call."""
        engine = OptimizationEngine(OptimizationConfig(routing_enabled=False))
        msgs = _msgs(("user", "What is 2+2?"))
        tools: list[Any] = []

        # First call — cache miss, populate cache manually
        hint1 = engine.pre_call(msgs, tools, "claude-haiku-4-5", "anthropic")
        assert not hint1.cache_hit
        engine.post_call(
            hint1,
            response="The answer is 4.",
            in_tokens=20,
            out_tokens=5,
            cost_usd=0.00002,
            provider="anthropic",
            model="claude-haiku-4-5",
        )

        # Second call with identical messages — should hit cache
        hint2 = engine.pre_call(msgs, tools, "claude-haiku-4-5", "anthropic")
        assert hint2.cache_hit
        assert hint2.cached_response == "The answer is 4."

    def test_no_cache_hit_when_messages_differ(self):
        engine = OptimizationEngine(OptimizationConfig())
        msgs1 = _msgs(("user", "What is 2+2?"))
        msgs2 = _msgs(("user", "What is 3+3?"))
        tools: list[Any] = []

        hint1 = engine.pre_call(msgs1, tools, "gpt-4o", "openai")
        engine.post_call(
            hint1, response="4", in_tokens=10, out_tokens=2, provider="openai", model="gpt-4o"
        )

        hint2 = engine.pre_call(msgs2, tools, "gpt-4o", "openai")
        assert not hint2.cache_hit


# ── TEST-OPT-013: OptimizationReport accumulates correctly ────────────────────


class TestOptimizationReport:
    def test_cache_hits_accumulate(self):
        """Covers REQ-OPT-010: accumulates cache_hits across calls."""
        engine = OptimizationEngine(OptimizationConfig(routing_enabled=False))
        msgs = _msgs(("user", "hello"))
        tools: list[Any] = []

        # Populate cache
        hint = engine.pre_call(msgs, tools, "gpt-4o", "openai")
        engine.post_call(
            hint, response="hi", in_tokens=5, out_tokens=2, provider="openai", model="gpt-4o"
        )

        # Two more calls → both should be cache hits
        for _ in range(2):
            h = engine.pre_call(msgs, tools, "gpt-4o", "openai")
            assert h.cache_hit

        report = engine.report()
        assert report.cache_hits == 2

    def test_tokens_saved_by_trim_accumulates(self):
        """Covers REQ-OPT-010: accumulates tokens_saved_by_trim."""
        cfg = OptimizationConfig(context_max_tokens=10, cache_enabled=False, routing_enabled=False)
        engine = OptimizationEngine(cfg)
        msgs = _msgs(
            ("system", "sys"),
            ("user", "message that is longer than the trim budget"),
            ("assistant", "a response"),
        )
        engine.pre_call(msgs, [], "gpt-4o", "openai")
        report = engine.report()
        assert report.tokens_saved_by_trim > 0

    def test_report_summary_contains_key_fields(self):
        report = OptimizationReport(
            cache_hits=5, cache_misses=10, tokens_saved_by_cache=5000, cost_saved_usd=0.05
        )
        summary = report.summary()
        assert "33.3%" in summary  # 5/(5+10)
        assert "5,000" in summary
        assert "$0.0500" in summary

    def test_cache_hit_rate_zero_when_no_calls(self):
        report = OptimizationReport()
        assert report.cache_hit_rate == 0.0


# ── Extra: estimate_session_savings ──────────────────────────────────────────


class TestEstimateSessionSavings:
    def test_baseline_positive(self):
        result = estimate_session_savings("anthropic", "claude-sonnet-4-5", 10, 1000, 300)
        assert result["baseline_usd"] > 0

    def test_total_savings_less_than_baseline(self):
        result = estimate_session_savings("openai", "gpt-4o", 20, 2000, 500)
        assert result["total_savings_usd"] <= result["baseline_usd"]

    def test_savings_pct_between_0_and_95(self):
        result = estimate_session_savings("anthropic", "claude-opus-4-5", 5, 10000, 2000)
        assert 0 <= result["savings_pct"] <= 95


# ── Extra: OptimizationConfig serialisation ──────────────────────────────────


class TestOptimizationConfig:
    def test_round_trip_serialisation(self):
        """Covers REQ-OPT-013: config is serialisable."""
        cfg = OptimizationConfig(
            cache_enabled=False,
            context_max_tokens=50_000,
            routing_enabled=True,
        )
        d = cfg.to_dict()
        restored = OptimizationConfig.from_dict(d)
        assert restored.cache_enabled is False
        assert restored.context_max_tokens == 50_000
        assert restored.routing_enabled is True

    def test_from_dict_ignores_unknown_keys(self):
        """Extra keys in YAML don't crash from_dict."""
        cfg = OptimizationConfig.from_dict({"unknown_key": 42, "cache_enabled": True})
        assert cfg.cache_enabled is True
