"""Per-run metrics collection for the governance efficiency benchmark.

A RunResult captures everything recorded during a single task x condition run.
BenchReport aggregates multiple RunResults into comparison tables.

Primary metric: cost_of_pass = total_cost_usd / pass_rate
  where pass_rate = fraction of runs for this (task, condition) that pass.

Cost concepts:
  token credits     – raw token count (the unit providers bill in)
  input_cost_usd    – USD cost of prompt/context tokens
  output_cost_usd   – USD cost of generated tokens
  api_cost_usd      – total USD = input + output
  cost_of_pass      – api_cost_usd / pass_rate (expected cost per correct answer)
  cost_delta        – ratio vs UNGOVERNED baseline (1.0 = same cost; <1 = cheaper)

All prices are list prices from provider pricing pages, Q2 2026.
Per-million-token pricing is the industry standard unit — convert to $/token
for calculations: price_per_token = price_per_million / 1_000_000.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Pricing table: (input_usd_per_1m, output_usd_per_1m)
# Source: provider pricing pages, Q2 2026.
# ---------------------------------------------------------------------------

MODEL_PRICING_PER_1M: dict[str, tuple[float, float]] = {
    # ── OpenAI GPT-4 family ──────────────────────────────────────────────
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    # ── OpenAI GPT-5 family (prices verified Q3–Q4 2025 / Q1–Q2 2026) ───
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
    # ── Fallback ─────────────────────────────────────────────────────────
    "unknown": (3.00, 15.00),
}

# Backwards-compatible alias — keep old key format working
MODEL_PRICING: dict[str, tuple[float, float]] = {
    k: (v[0] / 1000, v[1] / 1000)  # convert $/1M → $/1K
    for k, v in MODEL_PRICING_PER_1M.items()
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return estimated API cost in USD."""
    inp_per_m, out_per_m = MODEL_PRICING_PER_1M.get(model, MODEL_PRICING_PER_1M["unknown"])
    return (input_tokens / 1_000_000 * inp_per_m) + (output_tokens / 1_000_000 * out_per_m)


def estimate_cost_breakdown(
    model: str, input_tokens: int, output_tokens: int
) -> tuple[float, float, float]:
    """Return (input_cost_usd, output_cost_usd, total_cost_usd)."""
    inp_per_m, out_per_m = MODEL_PRICING_PER_1M.get(model, MODEL_PRICING_PER_1M["unknown"])
    inp_cost = input_tokens / 1_000_000 * inp_per_m
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
    model: str = "unknown"

    # Monetary cost breakdown (USD)
    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0
    api_cost_usd: float = 0.0  # total = input + output

    # Quality
    lint_passed: bool = False
    tests_passed: bool = False
    quality_score: float = 0.0  # 0.0-1.0 from LLM judge
    judge_rationale: str = ""

    # Efficiency
    rework_turns: int = 1  # >=1 (1 = first-pass success)
    governance_turns: int = 0  # turns consumed by governance overhead
    wall_clock_s: float = 0.0

    # Error tracking
    error: str | None = None
    skipped: bool = False

    # Raw outputs for post-hoc analysis
    agent_transcript: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.api_cost_usd == 0.0 and self.input_tokens > 0:
            inp, out, total = estimate_cost_breakdown(
                self.model, self.input_tokens, self.output_tokens
            )
            self.input_cost_usd = inp
            self.output_cost_usd = out
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
        return self.rework_turns + self.governance_turns


# ---------------------------------------------------------------------------
# Aggregate statistics for (task, condition) slice
# ---------------------------------------------------------------------------


@dataclass
class SliceStats:
    """Aggregate statistics over N repetitions of a (task, condition) slice."""

    task_id: str
    condition_id: str
    n_reps: int

    pass_rate: float = 0.0
    mean_input_tokens: float = 0.0
    mean_output_tokens: float = 0.0
    mean_total_tokens: float = 0.0
    mean_input_cost_usd: float = 0.0
    mean_output_cost_usd: float = 0.0
    mean_api_cost_usd: float = 0.0
    mean_quality_score: float = 0.0
    mean_rework_turns: float = 0.0
    mean_governance_turns: float = 0.0
    mean_wall_clock_s: float = 0.0

    # Std-devs (None when n_reps < 2)
    std_total_tokens: float | None = None
    std_api_cost_usd: float | None = None
    std_quality_score: float | None = None

    # Primary metric: expected USD to get one correct answer
    cost_of_pass: float = float("inf")
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
        if not valid:
            return cls(task_id=task_id, condition_id=condition_id, n_reps=n)

        pass_rate = sum(1 for r in valid if r.passed) / len(valid)
        mean_cost = statistics.mean(r.api_cost_usd for r in valid)

        cost_of_pass = (mean_cost / pass_rate) if pass_rate > 0 else float("inf")

        stats = cls(
            task_id=task_id,
            condition_id=condition_id,
            n_reps=n,
            pass_rate=pass_rate,
            mean_input_tokens=statistics.mean(r.input_tokens for r in valid),
            mean_output_tokens=statistics.mean(r.output_tokens for r in valid),
            mean_total_tokens=statistics.mean(r.total_tokens for r in valid),
            mean_input_cost_usd=statistics.mean(r.input_cost_usd for r in valid),
            mean_output_cost_usd=statistics.mean(r.output_cost_usd for r in valid),
            mean_api_cost_usd=mean_cost,
            mean_quality_score=statistics.mean(r.quality_score for r in valid),
            mean_rework_turns=statistics.mean(r.rework_turns for r in valid),
            mean_governance_turns=statistics.mean(r.governance_turns for r in valid),
            mean_wall_clock_s=statistics.mean(r.wall_clock_s for r in valid),
            cost_of_pass=cost_of_pass,
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
        return [
            SliceStats.from_runs(list(group)) for _, group in groupby(sorted_runs, key=_run_key)
        ]

    def condition_summary(self) -> dict[str, dict]:
        """Roll up per-condition means across all tasks, including cost deltas.

        cost_delta_vs_ungoverned: ratio of mean_cost_of_pass vs UNGOVERNED.
          <1.0 = cheaper per passing run; >1.0 = more expensive.
          None when UNGOVERNED has no data.
        """
        per_condition: dict[str, list[SliceStats]] = {}
        for s in self.slices():
            per_condition.setdefault(s.condition_id, []).append(s)

        summary: dict[str, dict] = {}
        for cid, slices in per_condition.items():
            finite_cop = [s.cost_of_pass for s in slices if s.cost_of_pass < float("inf")]
            mean_cop = statistics.mean(finite_cop) if finite_cop else float("inf")
            summary[cid] = {
                "mean_pass_rate": statistics.mean(s.pass_rate for s in slices),
                "mean_input_tokens": statistics.mean(s.mean_input_tokens for s in slices),
                "mean_output_tokens": statistics.mean(s.mean_output_tokens for s in slices),
                "mean_total_tokens": statistics.mean(s.mean_total_tokens for s in slices),
                "mean_input_cost_usd": statistics.mean(s.mean_input_cost_usd for s in slices),
                "mean_output_cost_usd": statistics.mean(s.mean_output_cost_usd for s in slices),
                "mean_api_cost_usd": statistics.mean(s.mean_api_cost_usd for s in slices),
                "mean_quality_score": statistics.mean(s.mean_quality_score for s in slices),
                "mean_cost_of_pass": mean_cop,
                # will be filled below once baseline is known
                "cost_delta_vs_ungoverned": None,
                "monthly_cost_20tasks": monthly_cost_projection(
                    statistics.mean(s.mean_api_cost_usd for s in slices),
                    tasks_per_day=20,
                ),
                "n_tasks": len(slices),
            }

        # Fill in cost deltas relative to UNGOVERNED
        baseline_cop = summary.get("UNGOVERNED", {}).get("mean_cost_of_pass")
        if baseline_cop and baseline_cop < float("inf"):
            for _cid, s in summary.items():
                cop = s["mean_cost_of_pass"]
                if cop < float("inf"):
                    s["cost_delta_vs_ungoverned"] = cop / baseline_cop

        return summary
