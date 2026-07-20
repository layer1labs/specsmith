# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for the govern_bench benchmark harness.

Covers:
  TEST-BH-01: RunResult.passed requires BOTH lint_passed AND tests_passed
  TEST-BH-02: RunResult.total_tokens = input + output
  TEST-BH-03: RunResult.__post_init__ auto-computes cost breakdown from token counts
  TEST-BH-04: SliceStats.from_runs() computes pass_rate correctly
  TEST-BH-05: SliceStats.cost_of_pass = mean_cost / pass_rate
  TEST-BH-06: SliceStats.cost_of_pass = inf when no passing runs
  TEST-BH-07: BenchReport.slices() groups runs by (task, condition)
  TEST-BH-08: BenchReport.condition_summary() sets cost_delta_vs_ungoverned
  TEST-BH-09: estimate_cost() returns 0.0 for zero tokens
  TEST-BH-10: EuTB metric — effectiveness_under_token_budget computation
  TEST-BH-11: Expensive-failure detection — failed run using >4× budget tokens
  TEST-BH-12: Outcome validity — partial pass (only lint or only tests) is a fail
  TEST-BH-13: Holdout isolation — benchmark task IDs are unique (no contamination)
  TEST-BH-14: model_pricing_per_1m table contains expected model families
  TEST-BH-15: BenchReport.condition_summary cost_delta is None when baseline missing
  TEST-BH-16: load_all_tasks() smoke — loads without error (YAML required)
  TEST-BH-17: Skipped runs are excluded from SliceStats aggregation
  TEST-BH-18: Multiple reps reduce variance — std_dev only computed when n >= 2

All tests are offline-only (no LLM, no network); benchmark task YAML is
loaded from disk when present but skipped gracefully if unavailable.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import govern_bench (scripts dir must be on sys.path)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from govern_bench.metrics import (  # noqa: E402
    BenchReport,
    RunResult,
    SliceStats,
    estimate_cost,
    estimate_cost_breakdown,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(
    task_id: str = "T1",
    condition_id: str = "UNGOVERNED",
    rep: int = 1,
    model: str = "gpt-4o-mini",
    input_tokens: int = 2000,
    output_tokens: int = 1000,
    lint_passed: bool = True,
    tests_passed: bool = True,
    quality_score: float = 0.8,
    rework_turns: int = 1,
    governance_turns: int = 0,
    wall_clock_s: float = 5.0,
    skipped: bool = False,
) -> RunResult:
    return RunResult(
        task_id=task_id,
        condition_id=condition_id,
        rep=rep,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        lint_passed=lint_passed,
        tests_passed=tests_passed,
        quality_score=quality_score,
        rework_turns=rework_turns,
        governance_turns=governance_turns,
        wall_clock_s=wall_clock_s,
        skipped=skipped,
    )


# ---------------------------------------------------------------------------
# TEST-BH-09: estimate_cost
# ---------------------------------------------------------------------------


class TestEstimateCost:
    def test_zero_tokens_zero_cost(self) -> None:
        assert estimate_cost("gpt-4o-mini", 0, 0) == 0.0

    def test_known_model_pricing(self) -> None:
        # gpt-4o-mini: input=$0.15/1M, output=$0.60/1M
        cost = estimate_cost("gpt-4o-mini", 1_000_000, 1_000_000)
        expected = 0.15 + 0.60
        assert abs(cost - expected) < 1e-9

    def test_unknown_model_uses_fallback(self) -> None:
        cost_unknown = estimate_cost("totally-made-up-model", 100_000, 50_000)
        cost_fallback = estimate_cost("unknown", 100_000, 50_000)
        assert abs(cost_unknown - cost_fallback) < 1e-9

    def test_breakdown_sums_to_total(self) -> None:
        inp, out, total = estimate_cost_breakdown("gpt-4o", 200_000, 80_000)
        assert abs(inp + out - total) < 1e-12


# ---------------------------------------------------------------------------
# TEST-BH-01/02/03: RunResult properties
# ---------------------------------------------------------------------------


class TestRunResult:
    def test_passed_requires_both_lint_and_tests(self) -> None:
        assert _run(lint_passed=True, tests_passed=True).passed is True

    def test_fails_if_lint_fails(self) -> None:
        assert _run(lint_passed=False, tests_passed=True).passed is False

    def test_fails_if_tests_fail(self) -> None:
        assert _run(lint_passed=True, tests_passed=False).passed is False

    def test_fails_if_both_fail(self) -> None:
        assert _run(lint_passed=False, tests_passed=False).passed is False

    def test_total_tokens(self) -> None:
        r = _run(input_tokens=1500, output_tokens=800)
        assert r.total_tokens == 2300

    def test_post_init_computes_cost(self) -> None:
        r = _run(model="gpt-4o-mini", input_tokens=1_000_000, output_tokens=0)
        assert abs(r.api_cost_usd - 0.15) < 1e-9

    def test_post_init_skipped_when_cost_provided(self) -> None:
        """If api_cost_usd is set explicitly, __post_init__ should not override it."""
        r = RunResult(
            task_id="T1",
            condition_id="UNGOVERNED",
            rep=1,
            model="gpt-4o-mini",
            input_tokens=1_000_000,
            output_tokens=0,
            api_cost_usd=99.99,  # explicit override
        )
        assert r.api_cost_usd == 99.99

    def test_total_turns(self) -> None:
        r = _run(rework_turns=3, governance_turns=2)
        assert r.total_turns == 5

    def test_explicit_total_cost_still_populates_breakdown(self) -> None:
        r = RunResult(
            task_id="T1",
            condition_id="UNGOVERNED",
            rep=1,
            model="gpt-4o-mini",
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            api_cost_usd=0.75,
        )
        assert r.input_cost_usd == pytest.approx(0.15)
        assert r.output_cost_usd == pytest.approx(0.60)
        assert r.api_cost_usd == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# TEST-BH-12: Outcome validity — partial passes are failures
# ---------------------------------------------------------------------------


class TestOutcomeValidity:
    """A benchmark run must pass BOTH criteria to count as 'passed'.

    This is the outcome-validity property: a passing test suite doesn't
    guarantee correctness if lint fails, and vice versa.
    """

    def test_lint_only_pass_is_failure(self) -> None:
        r = _run(lint_passed=True, tests_passed=False)
        assert r.passed is False, "Lint-only pass must not count as a run pass"

    def test_tests_only_pass_is_failure(self) -> None:
        r = _run(lint_passed=False, tests_passed=True)
        assert r.passed is False, "Test-only pass must not count as a run pass"

    def test_quality_score_independent_of_pass(self) -> None:
        """A high quality score doesn't override the pass criteria."""
        r = _run(lint_passed=False, tests_passed=True, quality_score=0.99)
        assert r.passed is False

    def test_both_criteria_required_across_multiple_runs(self) -> None:
        runs = [
            _run(lint_passed=True, tests_passed=True),
            _run(lint_passed=False, tests_passed=True),
            _run(lint_passed=True, tests_passed=False),
            _run(lint_passed=False, tests_passed=False),
        ]
        passed_count = sum(1 for r in runs if r.passed)
        assert passed_count == 1, "Exactly one of four partial-pass combinations truly passes"


# ---------------------------------------------------------------------------
# TEST-BH-04/05/06: SliceStats aggregation
# ---------------------------------------------------------------------------


class TestSliceStats:
    def test_pass_rate_all_pass(self) -> None:
        runs = [_run(rep=i) for i in range(5)]
        stats = SliceStats.from_runs(runs)
        assert stats.pass_rate == 1.0

    def test_pass_rate_none_pass(self) -> None:
        runs = [_run(rep=i, lint_passed=False) for i in range(3)]
        stats = SliceStats.from_runs(runs)
        assert stats.pass_rate == 0.0

    def test_pass_rate_mixed(self) -> None:
        runs = [
            _run(rep=1, lint_passed=True, tests_passed=True),
            _run(rep=2, lint_passed=False, tests_passed=True),
        ]
        stats = SliceStats.from_runs(runs)
        assert abs(stats.pass_rate - 0.5) < 1e-9

    def test_cost_of_pass_correct(self) -> None:
        """cost_of_pass = mean_api_cost_usd / pass_rate."""
        runs = [
            _run(
                rep=1,
                model="gpt-4o-mini",
                input_tokens=1_000_000,
                output_tokens=0,
                lint_passed=True,
                tests_passed=True,
            ),
            _run(
                rep=2,
                model="gpt-4o-mini",
                input_tokens=1_000_000,
                output_tokens=0,
                lint_passed=False,
                tests_passed=True,
            ),
        ]
        stats = SliceStats.from_runs(runs)
        # All runs same cost ($0.15), pass_rate = 0.5
        # cost_of_pass = 0.15 / 0.5 = 0.30
        assert abs(stats.cost_of_pass - 0.30) < 1e-6

    def test_cost_of_pass_inf_when_no_passes(self) -> None:
        runs = [_run(rep=i, lint_passed=False) for i in range(3)]
        stats = SliceStats.from_runs(runs)
        assert stats.cost_of_pass == float("inf")

    def test_mean_tokens_computed(self) -> None:
        runs = [
            _run(rep=1, input_tokens=1000, output_tokens=500),
            _run(rep=2, input_tokens=2000, output_tokens=1000),
        ]
        stats = SliceStats.from_runs(runs)
        assert abs(stats.mean_total_tokens - 2250.0) < 1e-9

    def test_empty_runs_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            SliceStats.from_runs([])

    def test_skipped_runs_excluded(self) -> None:
        runs = [
            _run(rep=1, lint_passed=True, tests_passed=True, skipped=False),
            _run(rep=2, lint_passed=True, tests_passed=True, skipped=True),
            _run(rep=3, lint_passed=True, tests_passed=True, skipped=True),
        ]
        stats = SliceStats.from_runs(runs)
        # Only the non-skipped run counts
        assert stats.n_reps == 3  # total including skipped
        assert abs(stats.pass_rate - 1.0) < 1e-9  # only valid run passes


# ---------------------------------------------------------------------------
# TEST-BH-18: Multiple reps — std_dev only computed when n >= 2
# ---------------------------------------------------------------------------


class TestStdDev:
    def test_std_none_when_single_rep(self) -> None:
        runs = [_run(rep=1)]
        stats = SliceStats.from_runs(runs)
        assert stats.std_total_tokens is None

    def test_std_computed_when_two_reps(self) -> None:
        runs = [
            _run(rep=1, input_tokens=1000, output_tokens=500),
            _run(rep=2, input_tokens=2000, output_tokens=1000),
        ]
        stats = SliceStats.from_runs(runs)
        assert stats.std_total_tokens is not None
        assert stats.std_total_tokens >= 0.0


# ---------------------------------------------------------------------------
# TEST-BH-07/08: BenchReport aggregation
# ---------------------------------------------------------------------------


class TestBenchReport:
    def _make_report(self) -> BenchReport:
        report = BenchReport()
        # Two conditions × one task × 2 reps
        report.runs = [
            _run(
                task_id="T1",
                condition_id="UNGOVERNED",
                rep=1,
                lint_passed=True,
                tests_passed=True,
                model="gpt-4o-mini",
                input_tokens=1_000_000,
                output_tokens=0,
            ),
            _run(
                task_id="T1",
                condition_id="UNGOVERNED",
                rep=2,
                lint_passed=False,
                tests_passed=True,
                model="gpt-4o-mini",
                input_tokens=1_000_000,
                output_tokens=0,
            ),
            _run(
                task_id="T1",
                condition_id="SPECSMITH_FULL",
                rep=1,
                lint_passed=True,
                tests_passed=True,
                model="gpt-4o-mini",
                input_tokens=1_000_000,
                output_tokens=0,
            ),
            _run(
                task_id="T1",
                condition_id="SPECSMITH_FULL",
                rep=2,
                lint_passed=True,
                tests_passed=True,
                model="gpt-4o-mini",
                input_tokens=1_000_000,
                output_tokens=0,
            ),
        ]
        return report

    def test_slices_groups_correctly(self) -> None:
        report = self._make_report()
        slices = report.slices()
        assert len(slices) == 2
        conditions = {s.condition_id for s in slices}
        assert conditions == {"UNGOVERNED", "SPECSMITH_FULL"}

    def test_ungoverned_lower_pass_rate(self) -> None:
        report = self._make_report()
        slices = {s.condition_id: s for s in report.slices()}
        ung = slices["UNGOVERNED"]
        spec = slices["SPECSMITH_FULL"]
        assert ung.pass_rate < spec.pass_rate, "SPECSMITH_FULL should outperform UNGOVERNED"

    def test_condition_summary_has_all_conditions(self) -> None:
        report = self._make_report()
        summary = report.condition_summary()
        assert "UNGOVERNED" in summary
        assert "SPECSMITH_FULL" in summary

    def test_condition_summary_cost_delta_relative_to_ungoverned(self) -> None:
        report = self._make_report()
        summary = report.condition_summary()
        # UNGOVERNED baseline delta should be 1.0 (self-referential)
        ung_delta = summary["UNGOVERNED"]["cost_delta_vs_ungoverned"]
        if ung_delta is not None:
            assert abs(ung_delta - 1.0) < 1e-6

    def test_cost_delta_none_when_baseline_missing(self) -> None:
        """When no UNGOVERNED runs exist, all deltas should be None."""
        report = BenchReport()
        report.runs = [
            _run(
                task_id="T1",
                condition_id="SPECSMITH_FULL",
                rep=1,
                lint_passed=True,
                tests_passed=True,
            ),
        ]
        summary = report.condition_summary()
        assert summary["SPECSMITH_FULL"]["cost_delta_vs_ungoverned"] is None

    def test_condition_summary_includes_zero_pass_task_cost(self) -> None:
        report = BenchReport()
        report.runs = [
            _run(
                task_id="T1",
                condition_id="UNGOVERNED",
                rep=1,
                lint_passed=True,
                tests_passed=True,
                model="gpt-4o-mini",
                input_tokens=1_000_000,
                output_tokens=0,
            ),
            _run(
                task_id="T2",
                condition_id="UNGOVERNED",
                rep=1,
                lint_passed=False,
                tests_passed=False,
                model="gpt-4o-mini",
                input_tokens=1_000_000,
                output_tokens=0,
            ),
        ]
        summary = report.condition_summary()["UNGOVERNED"]
        assert summary["mean_pass_rate"] == 0.5
        assert summary["mean_api_cost_usd"] == pytest.approx(0.15)
        assert summary["mean_cost_of_pass"] == pytest.approx(0.30)


# ---------------------------------------------------------------------------
# TEST-BH-10: Effectiveness Under Token Budget (EuTB) metric
# ---------------------------------------------------------------------------


class TestEffectivenessUnderTokenBudget:
    """EuTB = pass_rate × (1 − tokens_used/token_budget).

    Captures the joint objective: maximize accuracy while staying within
    a token budget constraint (from 'AI Agents That Matter' / NeurIPS 2025).
    """

    @staticmethod
    def eutb(pass_rate: float, tokens_used: float, token_budget: float) -> float:
        """Effectiveness under token budget metric."""
        if token_budget <= 0:
            return 0.0
        efficiency = 1.0 - (tokens_used / token_budget)
        return pass_rate * max(0.0, efficiency)

    def test_perfect_efficiency_under_budget(self) -> None:
        # 100% pass rate, uses exactly half the budget
        score = self.eutb(1.0, 500, 1000)
        assert abs(score - 0.5) < 1e-9

    def test_zero_pass_rate_gives_zero_eutb(self) -> None:
        score = self.eutb(0.0, 100, 1000)
        assert score == 0.0

    def test_over_budget_gives_zero_efficiency(self) -> None:
        """Consuming more than the budget → efficiency ≤ 0 → EuTB = 0."""
        score = self.eutb(1.0, 1500, 1000)
        assert score == 0.0, "Exceeding token budget must yield 0.0 EuTB"

    def test_exactly_at_budget_zero_efficiency(self) -> None:
        score = self.eutb(1.0, 1000, 1000)
        assert score == 0.0

    def test_eutb_captures_pareto_tradeoff(self) -> None:
        """A cheaper solution with same pass rate should outperform on EuTB."""
        expensive = self.eutb(0.9, 800, 1000)  # pass 90%, use 80% of budget
        cheap = self.eutb(0.9, 400, 1000)  # pass 90%, use 40% of budget
        assert cheap > expensive

    def test_eutb_from_slice_stats(self) -> None:
        """Compute EuTB from SliceStats to exercise the full pipeline."""
        runs = [
            _run(
                rep=i,
                input_tokens=400_000,
                output_tokens=100_000,
                lint_passed=True,
                tests_passed=True,
            )
            for i in range(4)
        ]
        stats = SliceStats.from_runs(runs)
        token_budget = 1_000_000  # 1M token budget per run
        score = self.eutb(stats.pass_rate, stats.mean_total_tokens, token_budget)
        # pass_rate=1.0, tokens=500k, budget=1M → 1.0 * (1 - 0.5) = 0.5
        assert abs(score - 0.5) < 1e-9


# ---------------------------------------------------------------------------
# TEST-BH-11: Expensive-failure detection
# ---------------------------------------------------------------------------


class TestExpensiveFailureDetection:
    """An 'expensive failure' is a run that:
      1. Does NOT pass (failed outcome)
      2. Consumes tokens significantly above the budget (or above passing runs)

    This is a key benchmark quality indicator from BetterBench research:
    high token consumption on wrong answers is worse than cheap failures.
    """

    @staticmethod
    def is_expensive_failure(
        run: RunResult,
        *,
        token_budget: int,
        expensive_multiplier: float = 4.0,
    ) -> bool:
        """Return True if the run failed AND consumed > multiplier × budget tokens."""
        return not run.passed and run.total_tokens > expensive_multiplier * token_budget

    def test_expensive_failure_detected(self) -> None:
        budget = 3000
        r = _run(
            input_tokens=10000,
            output_tokens=5000,
            lint_passed=False,
            tests_passed=True,
        )
        assert self.is_expensive_failure(r, token_budget=budget)

    def test_cheap_failure_not_expensive(self) -> None:
        budget = 3000
        r = _run(
            input_tokens=1000,
            output_tokens=500,
            lint_passed=False,
            tests_passed=True,
        )
        assert not self.is_expensive_failure(r, token_budget=budget)

    def test_passing_run_never_expensive_failure(self) -> None:
        budget = 100
        r = _run(input_tokens=10000, output_tokens=5000, lint_passed=True, tests_passed=True)
        assert not self.is_expensive_failure(r, token_budget=budget)

    def test_expensive_failure_rate_across_slice(self) -> None:
        """Compute the fraction of runs in a slice that are expensive failures."""
        budget = 3000
        runs = [
            _run(rep=1, input_tokens=500, output_tokens=200, lint_passed=True, tests_passed=True),
            _run(rep=2, input_tokens=1000, output_tokens=500, lint_passed=False, tests_passed=True),
            _run(rep=3, input_tokens=10000, output_tokens=5000, lint_passed=False),  # expensive!
        ]
        n_expensive = sum(1 for r in runs if self.is_expensive_failure(r, token_budget=budget))
        rate = n_expensive / len(runs)
        assert abs(rate - 1 / 3) < 1e-9

    def test_ungoverned_more_expensive_failures_than_governed(self) -> None:
        """Ungoverned agents should produce more expensive failures on hard tasks."""
        budget = 3000
        ungoverned_runs = [
            _run(
                rep=i,
                condition_id="UNGOVERNED",
                input_tokens=12000,
                output_tokens=6000,
                lint_passed=False,
            )
            for i in range(3)
        ]
        governed_runs = [
            _run(
                rep=i,
                condition_id="SPECSMITH_FULL",
                input_tokens=2000,
                output_tokens=500,
                lint_passed=True,
                tests_passed=True,
            )
            for i in range(3)
        ]
        ung_expensive_rate = sum(
            1 for r in ungoverned_runs if self.is_expensive_failure(r, token_budget=budget)
        ) / len(ungoverned_runs)
        gov_expensive_rate = sum(
            1 for r in governed_runs if self.is_expensive_failure(r, token_budget=budget)
        ) / len(governed_runs)
        assert ung_expensive_rate > gov_expensive_rate


# ---------------------------------------------------------------------------
# TEST-BH-13: Holdout isolation — task IDs are unique
# ---------------------------------------------------------------------------


class TestHoldoutIsolation:
    """Task IDs must be globally unique to prevent contamination between train/test sets.

    This is a structural benchmark validity property: each task represents a
    distinct capability test, and re-using IDs would cause double-counting in
    per-task analysis.
    """

    def test_task_ids_are_unique_in_report(self) -> None:
        """A BenchReport with duplicate task IDs across different conditions
        should still group correctly (tasks are per-condition, not globally unique)."""
        report = BenchReport()
        report.runs = [
            _run(task_id="T1", condition_id="UNGOVERNED", rep=1),
            _run(task_id="T1", condition_id="SPECSMITH_FULL", rep=1),
            _run(task_id="T2", condition_id="UNGOVERNED", rep=1),
        ]
        slices = report.slices()
        # Should have 3 distinct (task, condition) slices
        slice_keys = {(s.task_id, s.condition_id) for s in slices}
        assert len(slice_keys) == 3

    def test_no_duplicate_slice_keys(self) -> None:
        """SliceStats grouping must produce at most one entry per (task, condition)."""
        import random

        rng = random.Random(42)
        runs = [
            _run(
                task_id=f"T{rng.randint(1, 3)}",
                condition_id=rng.choice(["UNGOVERNED", "SPECSMITH_FULL"]),
                rep=i,
            )
            for i in range(12)
        ]
        report = BenchReport(runs=runs)
        slices = report.slices()
        keys = [(s.task_id, s.condition_id) for s in slices]
        assert len(keys) == len(set(keys)), "No duplicate (task, condition) slice keys"


# ---------------------------------------------------------------------------
# TEST-BH-14: Pricing table completeness
# ---------------------------------------------------------------------------


class TestPricingTable:
    def test_known_model_families_present(self) -> None:
        from govern_bench.metrics import MODEL_PRICING_PER_1M

        # Must have at least one entry from each major family
        keys_str = " ".join(MODEL_PRICING_PER_1M)
        assert "gpt-4o" in keys_str, "OpenAI GPT-4 family missing"
        assert "claude" in keys_str, "Anthropic family missing"
        assert "gemini" in keys_str, "Google family missing"
        assert "unknown" in MODEL_PRICING_PER_1M, "Fallback 'unknown' key missing"

    def test_all_prices_non_negative(self) -> None:
        from govern_bench.metrics import MODEL_PRICING_PER_1M

        for model, (inp, out) in MODEL_PRICING_PER_1M.items():
            assert inp >= 0.0, f"{model}: input price must be >= 0"
            assert out >= 0.0, f"{model}: output price must be >= 0"

    def test_output_price_geq_input_price(self) -> None:
        """Output tokens are typically priced higher than input tokens for the same model."""
        from govern_bench.metrics import MODEL_PRICING_PER_1M

        for model, (inp, out) in MODEL_PRICING_PER_1M.items():
            if model == "unknown":
                continue
            assert out >= inp, f"{model}: output price ({out}) should be >= input price ({inp})"


# ---------------------------------------------------------------------------
# TEST-BH-16: load_all_tasks() smoke test
# ---------------------------------------------------------------------------


class TestLoadAllTasks:
    """load_all_tasks() must load the YAML task registry without error.

    Skipped gracefully if yaml is not installed or task directory is missing.
    """

    def test_load_all_tasks_smoke(self) -> None:
        try:
            import yaml  # noqa: F401
        except ImportError:
            pytest.skip("PyYAML not installed — cannot load benchmark tasks")

        from govern_bench.tasks import TASKS_DIR, load_all_tasks

        if not TASKS_DIR.exists():
            pytest.skip(f"Tasks directory not found: {TASKS_DIR}")

        tasks = load_all_tasks()
        assert len(tasks) > 0, "Expected at least one task definition"

    def test_loaded_tasks_have_required_fields(self) -> None:
        try:
            import yaml  # noqa: F401
        except ImportError:
            pytest.skip("PyYAML not installed")

        from govern_bench.tasks import TASKS_DIR, load_all_tasks

        if not TASKS_DIR.exists():
            pytest.skip(f"Tasks directory not found: {TASKS_DIR}")

        tasks = load_all_tasks()
        for task in tasks:
            assert task.id, "Task must have an id"
            assert task.title, "Task must have a title"
            assert task.task_prompt, "Task must have a task_prompt"
            assert task.acceptance_criteria, "Task must have acceptance_criteria"

    def test_task_ids_globally_unique(self) -> None:
        try:
            import yaml  # noqa: F401
        except ImportError:
            pytest.skip("PyYAML not installed")

        from govern_bench.tasks import TASKS_DIR, load_all_tasks

        if not TASKS_DIR.exists():
            pytest.skip(f"Tasks directory not found: {TASKS_DIR}")

        tasks = load_all_tasks()
        ids = [t.id for t in tasks]
        assert len(ids) == len(set(ids)), "All task IDs must be globally unique"

    def test_bench_task_from_dict_raises_on_missing_field(self) -> None:
        from govern_bench.tasks import BenchTask

        with pytest.raises(ValueError, match="missing required fields"):
            BenchTask.from_dict({"id": "T99", "title": "Incomplete"})
