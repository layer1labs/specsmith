"""Per-run metrics collection for the governance efficiency benchmark.

A RunResult captures everything recorded during a single task x condition run.
BenchReport aggregates multiple RunResults into comparison tables.

Primary metric: tokens_per_correct_answer = mean_total_tokens / pass_rate
  where pass_rate = fraction of runs for this (task, condition) that pass.

Cost concepts:
  token credits     – raw token count (the unit providers bill in)
  input_cost_usd    – USD cost of prompt/context tokens
  output_cost_usd   – USD cost of generated tokens
  api_cost_usd      – total USD = input + output
  tokens_per_correct_answer – provider-neutral tokens consumed per correct answer
  cost_of_pass      – api_cost_usd / pass_rate (expected cost per correct answer)
  cost_delta        – ratio vs UNGOVERNED baseline (1.0 = same cost; <1 = cheaper)

Dollar prices are versioned benchmark estimates, not billing records. Provider
routes and prices can drift, which is why token efficiency is the primary metric.
Per-million-token pricing is the industry standard unit — convert to $/token
for calculations: price_per_token = price_per_million / 1_000_000.
"""

from __future__ import annotations

import math
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Pricing table: (input_usd_per_1m, output_usd_per_1m)
# Versioned estimates; verify against provider pricing before publication.
# ---------------------------------------------------------------------------

MODEL_PRICING_PER_1M: dict[str, tuple[float, float]] = {
    # ── OpenAI GPT-4 family ──────────────────────────────────────────────
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    # ── OpenAI GPT-5 family registry estimates ──────────────────────────
    "gpt-5": (15.00, 60.00),
    "gpt-5-mini": (2.00, 8.00),
    "gpt-5-nano": (0.50, 2.00),
    "gpt-5-pro": (50.00, 200.00),
    "gpt-5-codex": (15.00, 60.00),
    "gpt-5.1": (12.00, 48.00),
    "gpt-5.2": (10.00, 40.00),
    "gpt-5.2-pro": (40.00, 160.00),
    "gpt-5.2-codex": (10.00, 40.00),
    "gpt-5.3-codex": (8.00, 32.00),
    "gpt-5.4": (5.00, 20.00),
    "gpt-5.4-mini": (1.00, 4.00),
    "gpt-5.4-nano": (0.30, 1.20),
    "gpt-5.4-pro": (20.00, 80.00),
    "gpt-5.5": (3.00, 12.00),  # mid-tier coding model
    "gpt-5.5-pro": (15.00, 60.00),
    "gpt-5.6-luna": (1.00, 6.00),
    "gpt-5.6-terra": (2.50, 15.00),
    "gpt-5.6-sol": (5.00, 30.00),
    "gpt-5.6": (5.00, 30.00),
    # ── OpenAI reasoning models ──────────────────────────────────────────
    "o1": (15.0, 60.00),
    "o3": (10.0, 40.00),
    "o3-mini": (1.1, 4.40),
    "o4-mini": (1.1, 4.40),
    # ── Anthropic ────────────────────────────────────────────────────────
    "claude-haiku-4-5": (0.25, 1.25),
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-opus-4-5": (15.00, 75.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    # ── Google ───────────────────────────────────────────────────────────
    "gemini-3-flash": (0.35, 1.05),
    "gemini-3.5-flash": (0.15, 0.60),
    "gemini-3.1-pro": (1.25, 5.00),
    # ── OpenAI-compatible / open-source endpoints (hosted estimates) ────
    "Llama-3.1-70B": (0.88, 0.88),
    "llama-3.1-70b": (0.88, 0.88),
    "Qwen2.5-Coder-72B": (0.90, 0.90),
    "qwen2.5-coder-72b": (0.90, 0.90),
    "DeepSeek-Coder-V3": (0.70, 0.70),
    "deepseek-coder-v3": (0.70, 0.70),
    # ── HuggingFace Inference Providers — open-model tier spread ──────
    # Seed estimates from the HF Inference Providers router. probe_models.py
    # displays live route pricing for review but does not mutate these values.
    # Keyed by exact repo id AND lowercased alias (estimate_cost is
    # case-sensitive; model ids passed via --model are full HF repo ids).
    "meta-llama/Llama-3.1-8B-Instruct": (0.05, 0.08),
    "meta-llama/llama-3.1-8b-instruct": (0.05, 0.08),
    "Qwen/Qwen3-Coder-30B-A3B-Instruct": (0.10, 0.30),
    "qwen/qwen3-coder-30b-a3b-instruct": (0.10, 0.30),
    "Qwen/Qwen3.6-35B-A3B": (0.285, 1.71),
    "qwen/qwen3.6-35b-a3b": (0.285, 1.71),
    "Qwen/Qwen3-Coder-Next": (0.20, 1.50),
    "qwen/qwen3-coder-next": (0.20, 1.50),
    "Qwen/Qwen3-Coder-480B-A35B-Instruct": (0.38, 1.55),
    "qwen/qwen3-coder-480b-a35b-instruct": (0.38, 1.55),
    "moonshotai/Kimi-K2.7-Code": (0.74, 3.50),
    "moonshotai/kimi-k2.7-code": (0.74, 3.50),
    "zai-org/GLM-5.2": (0.93, 3.00),
    "zai-org/glm-5.2": (0.93, 3.00),
    "deepseek-ai/DeepSeek-V4-Pro": (1.60, 3.20),
    "deepseek-ai/deepseek-v4-pro": (1.60, 3.20),
    "MiniMaxAI/MiniMax-M3": (0.30, 1.20),
    "minimaxai/minimax-m3": (0.30, 1.20),
    "meta-llama/Llama-3.3-70B-Instruct": (0.60, 0.70),
    "meta-llama/llama-3.3-70b-instruct": (0.60, 0.70),
    "openai/gpt-oss-120b": (0.15, 0.60),
    # ── Fallback ──────────────────────────────────────────
    "unknown": (3.00, 15.00),
}

# Cached-input prices are versioned separately so the long-standing two-value
# pricing registry stays backwards compatible. Unknown models conservatively
# use their normal input rate. GPT-5.6 values are from the official model card.
MODEL_CACHED_INPUT_PER_1M: dict[str, float] = {
    "gpt-5.6-sol": 0.50,
    "gpt-5.6": 0.50,
}

MODEL_CACHE_WRITE_MULTIPLIER: dict[str, float] = {
    "gpt-5.6-sol": 1.25,
    "gpt-5.6": 1.25,
}

# HF router prices can differ by explicitly pinned serving provider. Exact
# route keys take precedence over the repo-level fallback above.
MODEL_ROUTE_PRICING_PER_1M: dict[str, tuple[float, float]] = {
    "Qwen/Qwen3.6-35B-A3B:deepinfra": (0.15, 0.95),
    "Qwen/Qwen3.6-35B-A3B:scaleway": (0.285, 1.71),
    "moonshotai/Kimi-K2.7-Code:deepinfra": (0.74, 3.50),
    "zai-org/GLM-5.2:deepinfra": (0.93, 3.00),
    "deepseek-ai/DeepSeek-V4-Pro:novita": (1.60, 3.20),
    "MiniMaxAI/MiniMax-M3:novita": (0.30, 1.20),
    "openai/gpt-oss-120b:deepinfra": (0.037, 0.17),
    "openai/gpt-oss-120b:novita": (0.05, 0.25),
}

# Backwards-compatible alias — keep old key format working
MODEL_PRICING: dict[str, tuple[float, float]] = {
    k: (v[0] / 1000, v[1] / 1000)  # convert $/1M → $/1K
    for k, v in MODEL_PRICING_PER_1M.items()
}

_MODEL_TIER_OVERRIDES: dict[str, str] = {
    "gpt-4.1-nano": "nano",
    "gemini-3.5-flash": "nano",
    "claude-haiku-4-5": "nano",
    "gpt-4o-mini": "mini",
    "gpt-5.5": "mini",
    "gpt-5.6-luna": "mini",
    "gpt-4.1-mini": "mini",
    "gpt-5.4": "mid",
    "gpt-5.6-terra": "mid",
    "claude-sonnet-4-5": "mid",
    "gemini-3.1-pro": "mid",
    "gpt-5": "frontier",
    "gpt-5.6-sol": "frontier",
    "gpt-5.6": "frontier",
    "claude-opus-4-5": "frontier",
    "llama-3.1-70b": "open-source",
    "qwen2.5-coder-72b": "open-source",
    "deepseek-coder-v3": "open-source",
    # Open-model tier spread (smallest → largest) for the open-only benchmark.
    # Keys are lowercased repo ids; model_tier() lowercases before lookup.
    "meta-llama/llama-3.1-8b-instruct": "open-small",
    "qwen/qwen3-coder-30b-a3b-instruct": "open-mid",
    "qwen/qwen3.6-35b-a3b": "open-mid",
    "qwen/qwen3-coder-next": "open-large",
    "qwen/qwen3-coder-480b-a35b-instruct": "open-xl",
    "moonshotai/kimi-k2.7-code": "open-xl",
    "zai-org/glm-5.2": "open-xl",
    "deepseek-ai/deepseek-v4-pro": "open-xl",
    "minimaxai/minimax-m3": "open-xl",
    "meta-llama/llama-3.3-70b-instruct": "open-large",
    "openai/gpt-oss-120b": "open-xl",
}

_OPEN_SOURCE_MARKERS = (
    "llama",
    "qwen",
    "deepseek",
    "kimi",
    "minimax",
    "mistral",
    "glm",
    "gpt-oss",
)


def strip_provider_route(model: str) -> str:
    """Drop an HF Inference Providers ``:<provider>`` route suffix.

    The HF router accepts ``org/repo:provider`` to pin one inference provider
    (e.g. ``meta-llama/Llama-3.1-8B-Instruct:deepinfra``). Pricing and tier
    tables are keyed by the bare repo id, so normalise before lookup. Repo ids
    contain ``/`` and never ``:``; a provider slug never contains ``/``.
    """
    base, sep, route = model.rpartition(":")
    if sep and route and "/" not in route:
        return base
    return model


def _tier_from_price(input_usd_per_1m: float, output_usd_per_1m: float) -> str:
    blended_price = (input_usd_per_1m + output_usd_per_1m) / 2.0
    if blended_price < 1.0:
        return "nano"
    if blended_price <= 4.0:
        return "mini"
    if blended_price <= 15.0:
        return "mid"
    return "frontier"


def model_tier(model: str) -> str:
    """Return the benchmark tier label for a model."""
    base = strip_provider_route(model)
    key = base.strip().lower()
    if key in _MODEL_TIER_OVERRIDES:
        return _MODEL_TIER_OVERRIDES[key]
    if any(marker in key for marker in _OPEN_SOURCE_MARKERS):
        return "open-source"

    prices = MODEL_PRICING_PER_1M.get(base)
    if prices is None:
        return "unknown"
    return _tier_from_price(*prices)


MODEL_TIER: dict[str, str] = {model: model_tier(model) for model in MODEL_PRICING_PER_1M}
MODEL_TIER.update(
    {
        "Llama-3.1-70B": "open-source",
        "Qwen2.5-Coder-72B": "open-source",
        "DeepSeek-Coder-V3": "open-source",
    }
)


def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> float:
    """Return estimated API cost in USD."""
    _, _, total = estimate_cost_breakdown(
        model,
        input_tokens,
        output_tokens,
        cached_input_tokens,
        cache_write_tokens,
    )
    return total


def estimate_cost_breakdown(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> tuple[float, float, float]:
    """Return (input_cost_usd, output_cost_usd, total_cost_usd)."""
    base = strip_provider_route(model)
    inp_per_m, out_per_m = MODEL_ROUTE_PRICING_PER_1M.get(
        model,
        MODEL_PRICING_PER_1M.get(base, MODEL_PRICING_PER_1M["unknown"]),
    )
    cached = min(max(0, cached_input_tokens), max(0, input_tokens))
    writes = min(max(0, cache_write_tokens), max(0, input_tokens - cached))
    uncached = max(0, input_tokens - cached - writes)
    cached_per_m = MODEL_CACHED_INPUT_PER_1M.get(base, inp_per_m)
    write_per_m = inp_per_m * MODEL_CACHE_WRITE_MULTIPLIER.get(base, 1.0)
    inp_cost = (
        uncached / 1_000_000 * inp_per_m
        + cached / 1_000_000 * cached_per_m
        + writes / 1_000_000 * write_per_m
    )
    out_cost = output_tokens / 1_000_000 * out_per_m
    return inp_cost, out_cost, inp_cost + out_cost


def monthly_cost_projection(
    cost_per_task_usd: float,
    tasks_per_day: int = 20,
    working_days: int = 22,
) -> float:
    """Project monthly API cost based on daily task volume."""
    return cost_per_task_usd * tasks_per_day * working_days


# ---------------------------------------------------------------------------
# RunResult
# ---------------------------------------------------------------------------


@dataclass
class RunResult:
    """Metrics for a single task x condition x repetition run."""

    task_id: str
    condition_id: str
    rep: int  # 1-based repetition index

    # Token usage (credit cost = raw token counts)
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    cache_write_tokens: int = 0
    model: str = "unknown"

    # Monetary cost breakdown (USD)
    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0
    api_cost_usd: float = 0.0  # total = input + output

    # Quality
    lint_passed: bool = False
    tests_passed: bool = False
    project_tests_passed: bool | None = None
    acceptance_oracle_passed: bool | None = None
    quality_score: float = 0.0  # 0.0-1.0 from LLM judge
    judge_rationale: str = ""

    # Efficiency
    rework_turns: int = 1  # >=1 (1 = first-pass success)
    governance_turns: int = 0  # turns consumed by governance overhead
    llm_turns: int = 0
    wall_clock_s: float = 0.0
    stop_reason: str = ""

    # Error tracking
    error: str | None = None
    skipped: bool = False

    # Raw outputs for post-hoc analysis
    agent_transcript: list[dict] = field(default_factory=list)
    call_usage: list[dict] = field(default_factory=list)
    files_written: list[str] = field(default_factory=list)
    final_diff: str = ""
    lint_output: str = ""
    test_output: str = ""
    governance_decision: dict = field(default_factory=dict)
    verify_result: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.input_tokens > 0 and self.input_cost_usd == 0.0 and self.output_cost_usd == 0.0:
            inp, out, total = estimate_cost_breakdown(
                self.model,
                self.input_tokens,
                self.output_tokens,
                self.cached_input_tokens,
                self.cache_write_tokens,
            )
            self.input_cost_usd = inp
            self.output_cost_usd = out
            if self.api_cost_usd == 0.0:
                self.api_cost_usd = total

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def passed(self) -> bool:
        """A run passes if lint and tests both pass."""
        return self.lint_passed and self.tests_passed

    @property
    def total_turns(self) -> int:
        # Older artifacts used rework_turns as their only model-turn proxy.
        return (self.llm_turns or self.rework_turns) + self.governance_turns


_WILSON_Z_95 = 1.959963984540054


def wilson_pass_rate_ci(successes: int, trials: int) -> tuple[float, float]:
    """Wilson score interval for a Bernoulli success rate at 95% confidence."""
    if trials <= 0:
        return (0.0, 0.0)

    p = successes / trials
    z2 = _WILSON_Z_95**2
    denom = 1.0 + z2 / trials
    center = (p + z2 / (2.0 * trials)) / denom
    margin = _WILSON_Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * trials)) / trials) / denom
    low = max(0.0, center - margin)
    high = min(1.0, center + margin)
    return (low, high)


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return float("inf")
    if len(values) == 1:
        return values[0]

    sorted_values = sorted(values)
    pos = (len(sorted_values) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_values[lo]

    low = sorted_values[lo]
    high = sorted_values[hi]
    if math.isinf(low) or math.isinf(high):
        return float("inf")
    frac = pos - lo
    return low + (high - low) * frac


def bootstrap_cost_of_pass_ci(
    runs: list[RunResult],
    bootstrap_samples: int = 1000,
) -> tuple[float, float]:
    """Bootstrap 95% confidence interval for cost-of-pass."""
    valid = [r for r in runs if not r.skipped]
    if not valid:
        return (float("inf"), float("inf"))

    seed = "|".join(
        f"{r.task_id}:{r.condition_id}:{r.model}:{r.rep}"
        for r in sorted(valid, key=lambda run: run.rep)
    )
    rng = random.Random(seed)
    sample_size = len(valid)
    cop_samples: list[float] = []

    for _ in range(bootstrap_samples):
        resampled = [valid[rng.randrange(sample_size)] for _ in range(sample_size)]
        pass_rate = sum(1 for r in resampled if r.passed) / sample_size
        mean_cost = statistics.mean(r.api_cost_usd for r in resampled)
        cop = mean_cost / pass_rate if pass_rate > 0 else float("inf")
        cop_samples.append(cop)

    return (_quantile(cop_samples, 0.025), _quantile(cop_samples, 0.975))


# ---------------------------------------------------------------------------
# Aggregate statistics for (task, condition) slice
# ---------------------------------------------------------------------------


@dataclass
class SliceStats:
    """Aggregate statistics over N repetitions of a (task, condition) slice."""

    task_id: str
    condition_id: str
    model: str
    n_reps: int

    pass_rate: float = 0.0
    ci_pass_rate_low: float = 0.0
    ci_pass_rate_high: float = 0.0
    mean_input_tokens: float = 0.0
    mean_output_tokens: float = 0.0
    mean_total_tokens: float = 0.0
    mean_input_cost_usd: float = 0.0
    mean_output_cost_usd: float = 0.0
    mean_api_cost_usd: float = 0.0
    mean_quality_score: float = 0.0
    first_pass_rate: float = 0.0
    consistency_score: float = 0.0
    scaffold_lift: float | None = None
    mean_rework_turns: float = 0.0
    mean_governance_turns: float = 0.0
    mean_wall_clock_s: float = 0.0

    # Std-devs (None when n_reps < 2)
    std_total_tokens: float | None = None
    std_api_cost_usd: float | None = None
    std_quality_score: float | None = None

    # Primary metric: expected USD to get one correct answer
    tokens_per_correct_answer: float = float("inf")
    cost_of_pass: float = float("inf")
    ci_cop_low: float = float("inf")
    ci_cop_high: float = float("inf")
    # Cost delta vs UNGOVERNED baseline (set externally by BenchReport)
    # <1.0 = cheaper per pass; >1.0 = more expensive per pass
    cost_delta_vs_baseline: float | None = None

    @classmethod
    def from_runs(cls, runs: list[RunResult]) -> SliceStats:
        """Compute aggregate stats from a list of RunResults."""
        if not runs:
            raise ValueError("Cannot compute stats from empty run list")

        task_id = runs[0].task_id
        condition_id = runs[0].condition_id
        n = len(runs)

        valid = [r for r in runs if not r.skipped]
        models = {r.model for r in valid if r.model}
        model = models.pop() if len(models) == 1 else ("mixed" if models else runs[0].model)
        if not valid:
            return cls(
                task_id=task_id,
                condition_id=condition_id,
                model=model,
                n_reps=n,
            )

        pass_count = sum(1 for r in valid if r.passed)
        pass_rate = pass_count / len(valid)
        ci_pass_low, ci_pass_high = wilson_pass_rate_ci(pass_count, len(valid))
        mean_cost = statistics.mean(r.api_cost_usd for r in valid)
        mean_tokens = statistics.mean(r.total_tokens for r in valid)
        ci_cop_low, ci_cop_high = bootstrap_cost_of_pass_ci(valid)
        first_pass_rate = sum(1 for r in valid if r.passed and r.rework_turns <= 1) / len(valid)
        pass_values = [1.0 if r.passed else 0.0 for r in valid]
        consistency_score = (
            1.0 if len(pass_values) < 2 else max(0.0, 1.0 - statistics.pstdev(pass_values))
        )

        tokens_per_correct_answer = mean_tokens / pass_rate if pass_rate > 0 else float("inf")
        cost_of_pass = (mean_cost / pass_rate) if pass_rate > 0 else float("inf")

        stats = cls(
            task_id=task_id,
            condition_id=condition_id,
            model=model,
            n_reps=n,
            pass_rate=pass_rate,
            ci_pass_rate_low=ci_pass_low,
            ci_pass_rate_high=ci_pass_high,
            mean_input_tokens=statistics.mean(r.input_tokens for r in valid),
            mean_output_tokens=statistics.mean(r.output_tokens for r in valid),
            mean_total_tokens=mean_tokens,
            mean_input_cost_usd=statistics.mean(r.input_cost_usd for r in valid),
            mean_output_cost_usd=statistics.mean(r.output_cost_usd for r in valid),
            mean_api_cost_usd=mean_cost,
            mean_quality_score=statistics.mean(r.quality_score for r in valid),
            first_pass_rate=first_pass_rate,
            consistency_score=consistency_score,
            mean_rework_turns=statistics.mean(r.rework_turns for r in valid),
            mean_governance_turns=statistics.mean(r.governance_turns for r in valid),
            mean_wall_clock_s=statistics.mean(r.wall_clock_s for r in valid),
            tokens_per_correct_answer=tokens_per_correct_answer,
            cost_of_pass=cost_of_pass,
            ci_cop_low=ci_cop_low,
            ci_cop_high=ci_cop_high,
        )

        if len(valid) >= 2:
            stats.std_total_tokens = statistics.stdev(r.total_tokens for r in valid)
            stats.std_api_cost_usd = statistics.stdev(r.api_cost_usd for r in valid)
            stats.std_quality_score = statistics.stdev(r.quality_score for r in valid)

        return stats


# ---------------------------------------------------------------------------
# Full benchmark report container
# ---------------------------------------------------------------------------


@dataclass
class BenchReport:
    """Aggregated results across all tasks × conditions."""

    runs: list[RunResult] = field(default_factory=list)

    def slices(self) -> list[SliceStats]:
        """Return SliceStats for every (task, condition) combination."""
        from itertools import groupby

        def _run_key(r: RunResult) -> tuple[str, str]:
            return (r.task_id, r.condition_id)

        sorted_runs = sorted(self.runs, key=_run_key)
        slices = [
            SliceStats.from_runs(list(group)) for _, group in groupby(sorted_runs, key=_run_key)
        ]
        baseline_by_task_model: dict[tuple[str, str], float] = {
            (s.task_id, s.model): s.pass_rate for s in slices if s.condition_id == "UNGOVERNED"
        }
        for s in slices:
            baseline = baseline_by_task_model.get((s.task_id, s.model))
            if baseline is None:
                s.scaffold_lift = None
            elif s.condition_id == "UNGOVERNED":
                s.scaffold_lift = 0.0
            else:
                s.scaffold_lift = s.pass_rate - baseline
        return slices

    def model_condition_summary(self) -> list[dict[str, float | str | None]]:
        """Return aggregate metrics grouped by (model, condition) across tasks."""
        grouped: dict[tuple[str, str], list[RunResult]] = defaultdict(list)
        for run in self.runs:
            if not run.skipped:
                grouped[(run.model, run.condition_id)].append(run)

        lifts_by_model_condition: dict[tuple[str, str], list[float]] = defaultdict(list)
        tasks_by_model_condition: dict[tuple[str, str], set[str]] = defaultdict(set)
        for stats in self.slices():
            tasks_by_model_condition[(stats.model, stats.condition_id)].add(stats.task_id)
            if stats.scaffold_lift is not None:
                lifts_by_model_condition[(stats.model, stats.condition_id)].append(
                    stats.scaffold_lift
                )

        rows: list[dict[str, float | str | None]] = []
        for (model, condition), grouped_runs in grouped.items():
            pass_rate = sum(1 for run in grouped_runs if run.passed) / len(grouped_runs)
            mean_cost = statistics.mean(run.api_cost_usd for run in grouped_runs)
            mean_tokens = statistics.mean(run.total_tokens for run in grouped_runs)
            mean_cop = mean_cost / pass_rate if pass_rate > 0 else float("inf")
            mean_tpca = mean_tokens / pass_rate if pass_rate > 0 else float("inf")
            lifts = lifts_by_model_condition[(model, condition)]
            rows.append(
                {
                    "model": model,
                    "condition": condition,
                    "model_tier": model_tier(model),
                    "mean_pass_rate": pass_rate,
                    "mean_quality_score": statistics.mean(
                        run.quality_score for run in grouped_runs
                    ),
                    "mean_cost_of_pass": mean_cop,
                    "mean_tokens_per_correct_answer": mean_tpca,
                    "mean_scaffold_lift": statistics.mean(lifts) if lifts else None,
                    "n_tasks": len(tasks_by_model_condition[(model, condition)]),
                }
            )
        return rows

    def democratization_table(self) -> list[dict[str, float | str | None]]:
        """Return cheapest model-tier wins vs frontier+UNGOVERNED CoP per scaffold."""
        rows = self.model_condition_summary()
        frontier_baselines = [
            r
            for r in rows
            if (
                r["condition"] == "UNGOVERNED"
                and r["model_tier"] == "frontier"
                and isinstance(r["mean_cost_of_pass"], float)
                and r["mean_cost_of_pass"] < float("inf")
            )
        ]
        if not frontier_baselines:
            return []

        frontier_best = min(
            frontier_baselines,
            key=lambda row: float(row["mean_cost_of_pass"]),
        )
        frontier_cop = float(frontier_best["mean_cost_of_pass"])
        frontier_model = str(frontier_best["model"])
        conditions = sorted(
            {str(r["condition"]) for r in rows if str(r["condition"]) != "UNGOVERNED"}
        )

        table: list[dict[str, float | str | None]] = []
        for condition in conditions:
            candidates = [
                r
                for r in rows
                if (
                    r["condition"] == condition
                    and isinstance(r["mean_cost_of_pass"], float)
                    and r["mean_cost_of_pass"] < frontier_cop
                )
            ]
            if not candidates:
                table.append(
                    {
                        "scaffold": condition,
                        "frontier_model": frontier_model,
                        "frontier_cop_usd": frontier_cop,
                        "cheapest_model": None,
                        "cheapest_model_tier": None,
                        "cheapest_cop_usd": None,
                        "cost_multiplier_vs_frontier": None,
                        "democratization_score": None,
                    }
                )
                continue

            winner = min(candidates, key=lambda row: float(row["mean_cost_of_pass"]))
            winner_cop = float(winner["mean_cost_of_pass"])
            table.append(
                {
                    "scaffold": condition,
                    "frontier_model": frontier_model,
                    "frontier_cop_usd": frontier_cop,
                    "cheapest_model": str(winner["model"]),
                    "cheapest_model_tier": str(winner["model_tier"]),
                    "cheapest_cop_usd": winner_cop,
                    "cost_multiplier_vs_frontier": (
                        frontier_cop / winner_cop if winner_cop > 0 else None
                    ),
                    "democratization_score": (
                        winner_cop / frontier_cop if frontier_cop > 0 else None
                    ),
                }
            )
        return table

    def pareto_frontier_data(self) -> list[dict[str, float | str | None]]:
        """Return non-dominated model/condition points in CoP-vs-pass space."""
        points = [
            row
            for row in self.model_condition_summary()
            if (
                isinstance(row["mean_cost_of_pass"], float)
                and row["mean_cost_of_pass"] < float("inf")
            )
        ]
        frontier: list[dict[str, float | str | None]] = []
        for point in points:
            point_cost = float(point["mean_cost_of_pass"])
            point_quality = float(point["mean_pass_rate"])
            dominated = False
            for candidate in points:
                if candidate is point:
                    continue
                candidate_cost = float(candidate["mean_cost_of_pass"])
                candidate_quality = float(candidate["mean_pass_rate"])
                if (
                    candidate_cost <= point_cost
                    and candidate_quality >= point_quality
                    and (candidate_cost < point_cost or candidate_quality > point_quality)
                ):
                    dominated = True
                    break
            if not dominated:
                frontier.append(
                    {
                        "model": point["model"],
                        "condition": point["condition"],
                        "model_tier": point["model_tier"],
                        "pass_rate": point["mean_pass_rate"],
                        "quality_score": point["mean_quality_score"],
                        "cost_of_pass_usd": point["mean_cost_of_pass"],
                        "scaffold_lift": point["mean_scaffold_lift"],
                    }
                )
        frontier.sort(
            key=lambda row: (
                float(row["cost_of_pass_usd"]),
                -float(row["pass_rate"]),
            )
        )
        return frontier

    def hf_leaderboard_json(
        self,
        task_suite: str = "governancebench-v1",
    ) -> list[dict[str, float | str | int | None]]:
        """Return HuggingFace-friendly leaderboard rows sorted by CoP."""
        rows = self.model_condition_summary()
        rows.sort(
            key=lambda row: (
                float(row["mean_cost_of_pass"])
                if isinstance(row["mean_cost_of_pass"], float)
                else float("inf"),
                -float(row["mean_pass_rate"]),
            )
        )

        leaderboard: list[dict[str, float | str | int | None]] = []
        for rank, row in enumerate(rows, start=1):
            cop = float(row["mean_cost_of_pass"])
            leaderboard.append(
                {
                    "rank": rank,
                    "model": str(row["model"]),
                    "scaffold": str(row["condition"]),
                    "task_suite": task_suite,
                    "pass_rate": round(float(row["mean_pass_rate"]), 6),
                    "cop_usd": None if cop == float("inf") else round(cop, 6),
                    "tokens_per_correct_answer": (
                        None
                        if float(row["mean_tokens_per_correct_answer"]) == float("inf")
                        else round(float(row["mean_tokens_per_correct_answer"]), 3)
                    ),
                    "scaffold_lift": (
                        round(float(row["mean_scaffold_lift"]), 6)
                        if row["mean_scaffold_lift"] is not None
                        else None
                    ),
                    "model_tier": str(row["model_tier"]),
                }
            )
        return leaderboard

    def condition_summary(self) -> dict[str, dict]:
        """Roll up per-condition means across all tasks, including cost deltas.

        cost_delta_vs_ungoverned: ratio of mean_cost_of_pass vs UNGOVERNED.
          <1.0 = cheaper per passing run; >1.0 = more expensive.
          None when UNGOVERNED has no data.
        """
        per_condition: dict[str, list[RunResult]] = defaultdict(list)
        for run in self.runs:
            if not run.skipped:
                per_condition[run.condition_id].append(run)

        slices_by_condition: dict[str, list[SliceStats]] = defaultdict(list)
        for stats in self.slices():
            slices_by_condition[stats.condition_id].append(stats)

        summary: dict[str, dict] = {}
        for cid, runs in per_condition.items():
            slices = slices_by_condition[cid]
            pass_count = sum(1 for run in runs if run.passed)
            pass_rate = pass_count / len(runs)
            ci_pass_low, ci_pass_high = wilson_pass_rate_ci(pass_count, len(runs))
            mean_cost = statistics.mean(run.api_cost_usd for run in runs)
            mean_tokens = statistics.mean(run.total_tokens for run in runs)
            mean_cop = mean_cost / pass_rate if pass_rate > 0 else float("inf")
            mean_tpca = mean_tokens / pass_rate if pass_rate > 0 else float("inf")
            ci_cop_low, ci_cop_high = bootstrap_cost_of_pass_ci(runs)
            scaffold_lifts = [s.scaffold_lift for s in slices if s.scaffold_lift is not None]
            summary[cid] = {
                "mean_pass_rate": pass_rate,
                "ci_pass_rate_low": ci_pass_low,
                "ci_pass_rate_high": ci_pass_high,
                "mean_input_tokens": statistics.mean(run.input_tokens for run in runs),
                "mean_output_tokens": statistics.mean(run.output_tokens for run in runs),
                "mean_total_tokens": mean_tokens,
                "mean_tokens_per_correct_answer": mean_tpca,
                "mean_input_cost_usd": statistics.mean(run.input_cost_usd for run in runs),
                "mean_output_cost_usd": statistics.mean(run.output_cost_usd for run in runs),
                "mean_api_cost_usd": mean_cost,
                "mean_quality_score": statistics.mean(run.quality_score for run in runs),
                "mean_first_pass_rate": statistics.mean(s.first_pass_rate for s in slices),
                "mean_consistency_score": statistics.mean(s.consistency_score for s in slices),
                "mean_scaffold_lift": (statistics.mean(scaffold_lifts) if scaffold_lifts else None),
                "mean_cost_of_pass": mean_cop,
                "ci_cop_low": ci_cop_low,
                "ci_cop_high": ci_cop_high,
                # will be filled below once baseline is known
                "cost_delta_vs_ungoverned": None,
                "monthly_cost_20tasks": monthly_cost_projection(
                    mean_cost,
                    tasks_per_day=20,
                ),
                "n_tasks": len({run.task_id for run in runs}),
            }

        # Fill in cost deltas relative to UNGOVERNED
        baseline_cop = summary.get("UNGOVERNED", {}).get("mean_cost_of_pass")
        if baseline_cop and baseline_cop < float("inf"):
            for _cid, s in summary.items():
                cop = s["mean_cost_of_pass"]
                if cop < float("inf"):
                    s["cost_delta_vs_ungoverned"] = cop / baseline_cop

        return summary
