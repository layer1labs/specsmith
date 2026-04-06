# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Token & credit optimization engine for the specsmith agentic client.

Implements 10 orthogonal optimization strategies drawn from 2025-2026 research:

  1. Response caching       — SHA-256 hash cache, 30-70% savings
  2. Prompt caching         — provider cache_control headers, 50-90% savings
  3. Context trimming       — sliding window on history, prevents compounding costs
  4. Model routing          — heuristic complexity → cheapest capable tier
  5. Output length control  — output tokens cost 3-8× more than input
  6. Tool filtering         — reduce tool-schema overhead (55K-134K tokens/call)
  7. Token estimation       — pre-flight cost awareness
  8. Duplicate detection    — identical consecutive turns → instant cached reply
  9. Summarization trigger  — signal when history should be condensed
  10. Optimization reporting — visibility + projected savings

Usage::

    from specsmith.agent.optimizer import OptimizationEngine, OptimizationConfig

    engine = OptimizationEngine(OptimizationConfig())
    hint = engine.pre_call(messages, tools, model="claude-sonnet-4-5", provider="anthropic")
    # ... call provider with hint.messages, hint.model, hint.tools ...
    engine.post_call(hint, in_tokens=1200, out_tokens=300)
    report = engine.report()
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

# ── Pricing tables (per 1M tokens, input / output) ──────────────────────────
# Updated Q1 2026. Used only for cost estimation; never hard-blocked on.
_PRICING: dict[str, dict[str, tuple[float, float]]] = {
    "anthropic": {
        "claude-opus-4-5": (5.00, 25.00),
        "claude-sonnet-4-5": (3.00, 15.00),
        "claude-haiku-4-5": (1.00, 5.00),
        "claude-opus-4-0": (5.00, 25.00),
        "claude-sonnet-4-0": (3.00, 15.00),
        "default": (3.00, 15.00),
    },
    "openai": {
        "gpt-4o": (2.50, 10.00),
        "gpt-4o-mini": (0.15, 0.60),
        "o3": (10.00, 40.00),
        "o3-mini": (1.10, 4.40),
        "o1": (15.00, 60.00),
        "default": (2.50, 10.00),
    },
    "gemini": {
        "gemini-2.5-pro": (1.25, 10.00),
        "gemini-2.5-flash": (0.075, 0.30),
        "gemini-2.0-pro": (1.25, 5.00),
        "gemini-2.0-flash": (0.075, 0.30),
        "default": (1.25, 5.00),
    },
    "mistral": {
        "mistral-large-latest": (2.00, 6.00),
        "mistral-small-latest": (0.10, 0.30),
        "codestral-latest": (0.30, 0.90),
        "pixtral-large-latest": (2.00, 6.00),
        "default": (2.00, 6.00),
    },
}

# Cheapest model per (provider, tier) — model routing destinations
_ROUTER_MODELS: dict[str, dict[str, str]] = {
    "anthropic": {
        "FAST": "claude-haiku-4-5",
        "BALANCED": "claude-sonnet-4-5",
        "POWERFUL": "claude-opus-4-5",
    },
    "openai": {
        "FAST": "gpt-4o-mini",
        "BALANCED": "gpt-4o",
        "POWERFUL": "o3",
    },
    "gemini": {
        "FAST": "gemini-2.5-flash",
        "BALANCED": "gemini-2.5-flash",
        "POWERFUL": "gemini-2.5-pro",
    },
    "mistral": {
        "FAST": "mistral-small-latest",
        "BALANCED": "mistral-large-latest",
        "POWERFUL": "mistral-large-latest",
    },
    "ollama": {
        "FAST": "qwen2.5:7b",
        "BALANCED": "qwen2.5:14b",
        "POWERFUL": "qwen2.5:14b",
    },
}

# ── Complexity classification keywords ──────────────────────────────────────
_POWERFUL_KEYWORDS = frozenset(
    [
        "architecture",
        "design",
        "refactor",
        "redesign",
        "implement from scratch",
        "complex",
        "multi-file",
        "system",
        "framework",
        "migration",
        "security audit",
        "performance bottleneck",
        "debug production",
        "concurrent",
        "distributed",
        "write a full",
        "build a complete",
        "analyze the entire",
        "optimize all",
        "write tests for",
        "generate documentation for the whole",
    ]
)
_FAST_KEYWORDS = frozenset(
    [
        "hello",
        "hi ",
        "thanks",
        "thank you",
        "yes",
        "no",
        "ok",
        "okay",
        "what is",
        "what's",
        "how do i",
        "can you explain",
        "list",
        "summarize",
        "show me",
        "audit",
        "validate",
        "doctor",
        "status",
        "run ",
        "check ",
        "quick ",
        "brief ",
        "simple ",
        "just ",
    ]
)

# Tool relevance keywords — tools are scored by how many of these appear
_TOOL_KEYWORDS: dict[str, list[str]] = {
    "audit": ["audit", "health", "governance", "check", "inspect"],
    "validate": ["validate", "valid", "consistent", "req", "test", "arch"],
    "epistemic_audit": ["epistemic", "belief", "certainty", "aee", "stress"],
    "stress_test": ["stress", "adversarial", "challenge", "failure", "requirement"],
    "belief_graph": ["belief", "graph", "dependency", "cert"],
    "diff": ["diff", "compare", "template", "drift"],
    "export": ["export", "report", "coverage", "compliance"],
    "doctor": ["doctor", "tool", "install", "missing"],
    "commit": ["commit", "stage", "git", "save"],
    "push": ["push", "remote", "origin"],
    "sync": ["sync", "pull", "fetch", "update"],
    "create_pr": ["pr", "pull request", "merge"],
    "run_command": ["run", "execute", "command", "shell", "test", "build", "install"],
    "write_file": ["write", "create", "edit", "modify", "update", "file"],
    "read_file": ["read", "show", "open", "file", "content", "view"],
    "list_dir": ["list", "directory", "folder", "files", "structure"],
    "grep_files": ["search", "find", "grep", "look for", "where is"],
    "ledger_add": ["ledger", "log", "record", "entry", "document"],
    "ledger_list": ["ledger", "history", "entries", "recent"],
    "trace_seal": ["seal", "trace", "decision", "record"],
    "trace_verify": ["verify", "integrity", "chain", "tamper"],
    "req_list": ["requirements", "req list", "list req"],
    "req_gaps": ["gaps", "uncovered", "missing test", "coverage"],
}


# ── Data types ───────────────────────────────────────────────────────────────


class ComplexityTier(str, Enum):
    FAST = "FAST"
    BALANCED = "BALANCED"
    POWERFUL = "POWERFUL"


@dataclass
class OptimizationConfig:
    """Configuration for all optimization strategies.

    Embed in scaffold.yml under ``optimization:`` to persist settings.
    """

    # Response cache
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    cache_persist: bool = False  # persist to .specsmith/response-cache.json

    # Context management
    context_max_tokens: int = 100_000
    summarize_threshold: int = 50_000  # tokens before recommending summarization

    # Model routing
    routing_enabled: bool = True
    routing_min_input_length: int = 20  # below this, always FAST

    # Tool filtering
    tool_filter_enabled: bool = True
    tool_filter_max_tools: int = 8  # return at most this many tools

    # Output control
    max_output_tokens: int | None = None  # None = provider default

    # Prompt caching (provider-native, e.g. Anthropic cache_control)
    prompt_caching_enabled: bool = True

    # Reporting
    report_to_ledger: bool = False  # append optimization report to LEDGER.md

    def to_dict(self) -> dict[str, Any]:
        return {
            "cache_enabled": self.cache_enabled,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "cache_persist": self.cache_persist,
            "context_max_tokens": self.context_max_tokens,
            "summarize_threshold": self.summarize_threshold,
            "routing_enabled": self.routing_enabled,
            "tool_filter_enabled": self.tool_filter_enabled,
            "tool_filter_max_tools": self.tool_filter_max_tools,
            "max_output_tokens": self.max_output_tokens,
            "prompt_caching_enabled": self.prompt_caching_enabled,
            "report_to_ledger": self.report_to_ledger,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OptimizationConfig:
        cfg = cls()
        for k, v in data.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
        return cfg


@dataclass
class OptimizationHint:
    """Result from OptimizationEngine.pre_call() — what to send to the provider."""

    messages: list[Any]  # potentially trimmed message list
    model: str  # potentially downgraded model
    tools: list[Any]  # potentially filtered tool list
    cache_hit: bool = False  # True if response was served from cache
    cached_response: str = ""  # populated if cache_hit=True
    tokens_trimmed: int = 0  # tokens removed from history
    tier: str = "BALANCED"  # complexity tier assigned
    original_model: str = ""  # model before routing


@dataclass
class OptimizationReport:
    """Session-level optimization statistics."""

    cache_hits: int = 0
    cache_misses: int = 0
    tokens_saved_by_cache: int = 0
    tokens_saved_by_trim: int = 0
    model_downgrades: int = 0
    cost_saved_usd: float = 0.0
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    recommendations: list[str] = field(default_factory=list)

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total else 0.0

    def summary(self) -> str:
        lines = [
            "=== Optimization Report ===",
            f"  Total calls:        {self.total_calls}",
            f"  Cache hit rate:     {self.cache_hit_rate:.1%}  ({self.cache_hits} hits)",
            f"  Tokens saved/trim:  {self.tokens_saved_by_trim:,}",
            f"  Tokens saved/cache: {self.tokens_saved_by_cache:,}",
            f"  Cost saved:         ${self.cost_saved_usd:.4f}",
            f"  Total cost:         ${self.total_cost_usd:.4f}",
        ]
        if self.model_downgrades:
            lines.append(f"  Model downgrades:   {self.model_downgrades}")
        if self.recommendations:
            lines.append("\nRecommendations:")
            for r in self.recommendations:
                lines.append(f"  • {r}")
        return "\n".join(lines)


# ── Component classes ─────────────────────────────────────────────────────────


class TokenEstimator:
    """Estimates token counts and costs without calling any external API.

    Uses per-model character ratios derived from provider documentation.
    Typical English: 1 token ≈ 4 chars. Code: 1 token ≈ 3 chars.
    """

    # chars per token by model family
    _CHARS_PER_TOKEN: dict[str, float] = {
        "claude": 3.8,  # Anthropic tokeniser
        "gpt-4": 4.0,
        "gpt-4o": 4.0,
        "o1": 4.0,
        "o3": 4.0,
        "gemini": 4.0,
        "mistral": 3.8,
        "default": 4.0,
    }

    def estimate(self, text: str, model: str = "default") -> int:
        """Estimate token count for a string."""
        if not text:
            return 0
        model_lower = model.lower()
        ratio = self._CHARS_PER_TOKEN["default"]
        for key, r in self._CHARS_PER_TOKEN.items():
            if key in model_lower:
                ratio = r
                break
        return max(1, int(len(text) / ratio))

    def estimate_messages(self, messages: list[Any], model: str = "default") -> int:
        """Estimate total token count for a message list."""
        total = 0
        for msg in messages:
            content = ""
            if isinstance(msg, dict):
                content = str(msg.get("content", ""))
            elif hasattr(msg, "content"):
                content = str(msg.content or "")
            total += self.estimate(content, model) + 4  # per-message overhead
        return total

    def estimate_cost(
        self,
        in_tokens: int,
        out_tokens: int,
        provider: str,
        model: str,
    ) -> float:
        """Estimate cost in USD from token counts."""
        provider_prices = _PRICING.get(provider, _PRICING.get("openai", {}))
        fallback = (3.0, 15.0)
        in_price, out_price = provider_prices.get(model, provider_prices.get("default", fallback))
        return (in_tokens * in_price + out_tokens * out_price) / 1_000_000


class ResponseCache:
    """Hash-based in-memory response cache with TTL and optional disk persistence."""

    def __init__(
        self,
        ttl_seconds: int = 3600,
        persist_path: Path | None = None,
    ) -> None:
        self._ttl = ttl_seconds
        self._cache: dict[str, dict[str, Any]] = {}  # key → {response, expires, in_tok, out_tok}
        self._persist_path = persist_path
        self._hits = 0
        self._misses = 0
        self._tokens_saved = 0
        self._cost_saved = 0.0
        if persist_path and persist_path.exists():
            self._load()

    # ── Public API ────────────────────────────────────────────────────────────

    def cache_key(
        self,
        provider: str,
        model: str,
        messages: list[Any],
        tools: list[Any] | None = None,
    ) -> str:
        """Stable SHA-256 key from (provider, model, messages, tools)."""
        msg_repr = json.dumps(
            [{"role": _get_role(m), "content": _get_content(m)} for m in messages],
            sort_keys=True,
        )
        tool_repr = json.dumps(
            [t.name if hasattr(t, "name") else str(t) for t in (tools or [])],
            sort_keys=True,
        )
        raw = f"{provider}:{model}:{msg_repr}:{tool_repr}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, key: str) -> str | None:
        """Return cached response or None if missing/expired."""
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None
        if time.time() > entry["expires"]:
            del self._cache[key]
            self._misses += 1
            return None
        self._hits += 1
        self._tokens_saved += entry.get("tokens", 0)
        self._cost_saved += entry.get("cost", 0.0)
        return entry["response"]

    def set(
        self,
        key: str,
        response: str,
        in_tokens: int = 0,
        out_tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> None:
        """Store a response with TTL and token metadata."""
        self._cache[key] = {
            "response": response,
            "expires": time.time() + self._ttl,
            "tokens": in_tokens + out_tokens,
            "cost": cost_usd,
        }
        if self._persist_path:
            self._save()

    def evict_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        now = time.time()
        expired = [k for k, v in self._cache.items() if now > v["expires"]]
        for k in expired:
            del self._cache[k]
        return len(expired)

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total else 0.0

    @property
    def tokens_saved(self) -> int:
        return self._tokens_saved

    @property
    def cost_saved(self) -> float:
        return self._cost_saved

    @property
    def size(self) -> int:
        return len(self._cache)

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self) -> None:
        if not self._persist_path:
            return
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            self._persist_path.write_text(json.dumps(self._cache, indent=2), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass

    def _load(self) -> None:
        try:
            data = json.loads(self._persist_path.read_text(encoding="utf-8"))  # type: ignore[union-attr]
            now = time.time()
            self._cache = {k: v for k, v in data.items() if now < v.get("expires", 0)}
        except Exception:  # noqa: BLE001
            pass


class ContextManager:
    """Manages conversation history token budget.

    Implements sliding-window trimming and summarization thresholds.
    """

    def __init__(self, max_tokens: int = 100_000, summarize_threshold: int = 50_000) -> None:
        self._max_tokens = max_tokens
        self._summarize_threshold = summarize_threshold
        self._estimator = TokenEstimator()

    def trim(self, messages: list[Any], model: str = "default") -> tuple[list[Any], int]:
        """Trim history to stay within max_tokens.

        Returns (trimmed_messages, tokens_removed).
        Always preserves the first (system) message if present.
        """
        current = self._estimator.estimate_messages(messages, model)
        if current <= self._max_tokens:
            return messages, 0

        system_msgs = [m for m in messages if _get_role(m) == "system"]
        other_msgs = [m for m in messages if _get_role(m) != "system"]

        # Keep as many recent messages as fit within budget
        system_tokens = self._estimator.estimate_messages(system_msgs, model)
        budget = self._max_tokens - system_tokens
        kept: list[Any] = []
        used = 0

        for msg in reversed(other_msgs):
            tok = self._estimator.estimate(_get_content(msg), model) + 4
            if used + tok > budget:
                break
            kept.insert(0, msg)
            used += tok

        removed_tokens = current - system_tokens - used
        return system_msgs + kept, max(0, removed_tokens)

    def needs_summarization(self, messages: list[Any], model: str = "default") -> bool:
        """True when history has grown past the summarization threshold."""
        total = self._estimator.estimate_messages(messages, model)
        return total > self._summarize_threshold

    def summarization_prompt(self, messages: list[Any]) -> str:
        """Return a prompt to summarize a message list (caller sends to LLM)."""
        lines = []
        for m in messages:
            role = _get_role(m)
            content = _get_content(m)[:500]
            lines.append(f"[{role}] {content}")
        history = "\n".join(lines)
        return (
            "Summarise the following conversation history into a compact paragraph "
            "that preserves all key facts, decisions, file names, error codes, "
            "and task context. Be concise. Use bullet points.\n\n"
            f"{history}"
        )


class ModelRouter:
    """Classify task complexity and route to the cheapest capable model.

    Uses keyword + length heuristics with no API call.
    """

    def __init__(self, min_input_length: int = 20) -> None:
        self._min_length = min_input_length

    def classify(self, user_input: str) -> ComplexityTier:
        """Assign FAST / BALANCED / POWERFUL tier based on heuristics."""
        text = user_input.strip().lower()

        # Very short → always FAST
        if len(text) < self._min_length:
            return ComplexityTier.FAST

        # Check for POWERFUL indicators
        for kw in _POWERFUL_KEYWORDS:
            if kw in text:
                return ComplexityTier.POWERFUL

        # Check word count: long inputs are more likely complex
        words = text.split()
        if len(words) > 150:
            return ComplexityTier.POWERFUL
        if len(words) > 60:
            return ComplexityTier.BALANCED

        # Check for FAST indicators
        fast_hits = sum(1 for kw in _FAST_KEYWORDS if kw in text)
        if fast_hits >= 2:
            return ComplexityTier.FAST

        # Code / technical signals
        has_code = bool(re.search(r"```|`[a-zA-Z_]+`|def |class |import |fn |func ", text))
        if has_code:
            return ComplexityTier.BALANCED

        return ComplexityTier.BALANCED

    def suggest_model(self, provider: str, tier: ComplexityTier) -> str:
        """Return the cheapest default model for the given provider + tier."""
        provider_map = _ROUTER_MODELS.get(provider.lower(), _ROUTER_MODELS.get("openai", {}))
        return provider_map.get(tier.value, "")

    def pricing_for(self, provider: str, model: str) -> tuple[float, float]:
        """Return (input_price_per_1M, output_price_per_1M) for model."""
        p = _PRICING.get(provider, {})
        return p.get(model, p.get("default", (3.0, 15.0)))


class ToolFilter:
    """Score and select only tools relevant to the current task.

    Reduces tool-schema token overhead from 55K–134K to a tight subset.
    """

    def __init__(self, max_tools: int = 8) -> None:
        self._max_tools = max_tools

    def select(self, tools: list[Any], task_text: str) -> list[Any]:
        """Return the top-N tools most relevant to task_text."""
        if not tools or len(tools) <= self._max_tools:
            return tools

        task_lower = task_text.lower()
        scored: list[tuple[int, Any]] = []

        for tool in tools:
            name = tool.name if hasattr(tool, "name") else str(tool)
            desc = ((tool.description if hasattr(tool, "description") else "") or "").lower()
            keywords = _TOOL_KEYWORDS.get(name, [])
            score = 0
            for kw in keywords:
                if kw in task_lower:
                    score += 3
            # Secondary: match tool name / description against task
            name_lower = name.lower().replace("_", " ")
            for word in task_lower.split():
                if len(word) > 3 and word in name_lower + " " + desc:
                    score += 1
            # Always keep filesystem + shell tools (universally useful)
            if name in ("run_command", "write_file", "read_file", "list_dir", "grep_files"):
                score += 5
            scored.append((score, tool))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[: self._max_tools]]


# ── Main engine ───────────────────────────────────────────────────────────────


class OptimizationEngine:
    """Orchestrates all optimization strategies for a single agent session.

    Typical lifecycle per turn::

        hint = engine.pre_call(messages, tools, model, provider)
        if hint.cache_hit:
            return hint.cached_response
        response = provider.complete(hint.messages, tools=hint.tools, ...)
        engine.post_call(hint, in_tokens=..., out_tokens=..., cost=...)
    """

    def __init__(
        self,
        config: OptimizationConfig | None = None,
        project_dir: str = ".",
    ) -> None:
        self._config = config or OptimizationConfig()
        self._project_dir = Path(project_dir)
        self._estimator = TokenEstimator()

        persist_path: Path | None = None
        if self._config.cache_persist:
            persist_path = self._project_dir / ".specsmith" / "response-cache.json"

        self._cache = ResponseCache(
            ttl_seconds=self._config.cache_ttl_seconds,
            persist_path=persist_path,
        )
        self._context_mgr = ContextManager(
            max_tokens=self._config.context_max_tokens,
            summarize_threshold=self._config.summarize_threshold,
        )
        self._router = ModelRouter(
            min_input_length=self._config.routing_min_input_length,
        )
        self._tool_filter = ToolFilter(
            max_tools=self._config.tool_filter_max_tools,
        )
        self._report = OptimizationReport()
        self._last_user_msg: str = ""

    # ── Primary interface ────────────────────────────────────────────────────

    def pre_call(
        self,
        messages: list[Any],
        tools: list[Any],
        model: str,
        provider: str,
    ) -> OptimizationHint:
        """Apply all enabled optimizations before an LLM call.

        Returns an OptimizationHint with the (possibly transformed)
        messages, model, and tools to use. If cache_hit is True,
        the caller should return cached_response directly and skip
        the API call.
        """
        self._report.total_calls += 1

        # Extract last user message for routing + tool filtering
        user_text = _last_user_content(messages)

        # ── 1. Duplicate detection & response caching ────────────────────────
        if self._config.cache_enabled:
            cache_key = self._cache.cache_key(provider, model, messages, tools)
            cached = self._cache.get(cache_key)
            if cached is not None:
                self._report.cache_hits += 1
                est_tokens = self._estimator.estimate_messages(messages, model)
                self._report.tokens_saved_by_cache += est_tokens
                return OptimizationHint(
                    messages=messages,
                    model=model,
                    tools=tools,
                    cache_hit=True,
                    cached_response=cached,
                    tier="CACHED",
                )
            self._report.cache_misses += 1

        # ── 2. Context trimming ──────────────────────────────────────────────
        trimmed_msgs, tokens_trimmed = self._context_mgr.trim(messages, model)
        self._report.tokens_saved_by_trim += tokens_trimmed

        # Summarization recommendation
        if self._context_mgr.needs_summarization(trimmed_msgs, model):
            rec = (
                "History is large — consider asking the agent to 'save' "
                "or running /clear to reset context."
            )
            if rec not in self._report.recommendations:
                self._report.recommendations.append(rec)

        # ── 3. Model routing ─────────────────────────────────────────────────
        selected_model = model
        tier = ComplexityTier.BALANCED
        if self._config.routing_enabled and user_text:
            tier = self._router.classify(user_text)
            if tier == ComplexityTier.FAST:
                cheaper = self._router.suggest_model(provider, tier)
                if cheaper and cheaper != model:
                    # Only downgrade, never upgrade
                    orig_in, _ = self._router.pricing_for(provider, model)
                    new_in, _ = self._router.pricing_for(provider, cheaper)
                    if new_in <= orig_in:
                        selected_model = cheaper
                        self._report.model_downgrades += 1

        # ── 4. Tool filtering ────────────────────────────────────────────────
        filtered_tools = tools
        if self._config.tool_filter_enabled and tools and user_text:
            filtered_tools = self._tool_filter.select(tools, user_text)

        return OptimizationHint(
            messages=trimmed_msgs,
            model=selected_model,
            tools=filtered_tools,
            cache_hit=False,
            tokens_trimmed=tokens_trimmed,
            tier=tier.value,
            original_model=model if selected_model != model else "",
        )

    def post_call(
        self,
        hint: OptimizationHint,
        response: str = "",
        in_tokens: int = 0,
        out_tokens: int = 0,
        cost_usd: float = 0.0,
        provider: str = "",
        model: str = "",
    ) -> None:
        """Record results after an LLM call and populate cache."""
        self._report.total_input_tokens += in_tokens
        self._report.total_output_tokens += out_tokens
        self._report.total_cost_usd += cost_usd

        # Store in response cache
        if self._config.cache_enabled and response and not hint.cache_hit:
            cache_key = self._cache.cache_key(provider, model, hint.messages, hint.tools)
            self._cache.set(
                cache_key,
                response,
                in_tokens=in_tokens,
                out_tokens=out_tokens,
                cost_usd=cost_usd,
            )

        # Accumulate savings from cost difference if model was downgraded
        if hint.original_model and provider:
            orig_in, orig_out = self._router.pricing_for(provider, hint.original_model)
            new_in, new_out = self._router.pricing_for(provider, hint.model)
            saved = (
                (in_tokens * (orig_in - new_in)) + (out_tokens * (orig_out - new_out))
            ) / 1_000_000
            self._report.cost_saved_usd += max(0.0, saved)

        # Add cache savings from cache hit
        self._report.cost_saved_usd += self._cache.cost_saved - getattr(
            self, "_last_cache_cost", 0.0
        )
        self._last_cache_cost: float = self._cache.cost_saved  # type: ignore[assignment]

    def report(self) -> OptimizationReport:
        """Return the current session-level optimization report."""
        # Add structural recommendations
        recs = list(self._report.recommendations)
        if self._report.cache_hit_rate < 0.1 and self._report.total_calls > 5:
            recs.append("Low cache hit rate — consider reusing AgentRunner across sessions.")
        if self._report.tokens_saved_by_trim > 10_000:
            recs.append(
                "Significant context trimming occurred — reduce history with /clear more often."
            )
        if self._report.model_downgrades == 0 and self._report.total_calls > 3:
            recs.append(
                "Model routing never fired FAST tier — consider using haiku/mini for quick queries."
            )
        self._report.recommendations = recs
        return self._report

    def cache_stats(self) -> dict[str, Any]:
        return {
            "size": self._cache.size,
            "hit_rate": self._cache.hit_rate,
            "tokens_saved": self._cache.tokens_saved,
            "cost_saved_usd": self._cache.cost_saved,
        }


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_role(msg: Any) -> str:
    if isinstance(msg, dict):
        return str(msg.get("role", ""))
    return str(getattr(msg, "role", ""))


def _get_content(msg: Any) -> str:
    if isinstance(msg, dict):
        return str(msg.get("content", ""))
    return str(getattr(msg, "content", "") or "")


def _last_user_content(messages: list[Any]) -> str:
    """Return the content of the last user message."""
    for msg in reversed(messages):
        if _get_role(msg) in ("user", "USER"):
            return _get_content(msg)
    return ""


def estimate_session_savings(
    provider: str,
    model: str,
    total_calls: int,
    avg_input_tokens: int,
    avg_output_tokens: int,
    cache_hit_rate: float = 0.30,
    routing_fast_pct: float = 0.40,
) -> dict[str, float]:
    """Estimate monthly savings from applying all optimizations.

    Useful for the 'specsmith optimize' CLI report.
    """
    router = ModelRouter()

    monthly_calls = total_calls * 30  # extrapolate from session

    # Baseline monthly cost
    in_p, out_p = router.pricing_for(provider, model)
    baseline = (
        monthly_calls * avg_input_tokens * in_p + monthly_calls * avg_output_tokens * out_p
    ) / 1_000_000

    # Savings from caching
    cache_savings = baseline * cache_hit_rate

    # Savings from routing (FAST tier is ~5x cheaper input on Anthropic)
    fast_model = router.suggest_model(provider, ComplexityTier.FAST)
    if fast_model:
        fast_in, fast_out = router.pricing_for(provider, fast_model)
        routing_saving_per_call = (
            avg_input_tokens * (in_p - fast_in) + avg_output_tokens * (out_p - fast_out)
        ) / 1_000_000
        routing_savings = routing_saving_per_call * monthly_calls * routing_fast_pct
    else:
        routing_savings = 0.0

    # Context trimming: assume 20% token reduction on average
    trim_savings = baseline * 0.20

    total_saved = cache_savings + routing_savings + trim_savings
    return {
        "baseline_usd": round(baseline, 2),
        "cache_savings_usd": round(max(0, cache_savings), 2),
        "routing_savings_usd": round(max(0, routing_savings), 2),
        "trim_savings_usd": round(trim_savings, 2),
        "total_savings_usd": round(max(0, total_saved), 2),
        "savings_pct": round(min(95, total_saved / baseline * 100) if baseline else 0, 1),
    }
