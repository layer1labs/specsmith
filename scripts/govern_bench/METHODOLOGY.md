# GovernanceBench Statistical Methodology

This document defines the statistical design, aggregation rules, and reporting guardrails for
GovernanceBench.

> Publication status: the current repeated-run evidence and its limitations are
> published in `docs/site/efficiency-benchmark.md`. New claims remain unpublished
> until their raw artifacts pass the completeness and comparability gates below.

## 1) Objective

Quantify governance/scaffolding impact on:

1. correctness and safety outcomes,
2. token/cost efficiency,
3. reliability/consistency across repeated runs,
4. economic accessibility across model tiers.

## 2) Experimental Design

Each benchmark observation is a run over the Cartesian product:

- task (`T*`),
- governance condition (`12` executable conditions),
- model/provider pair,
- repetition index (`rep`).

Recommended repetitions:

- minimum analytical run: `n_reps = 5` per cell,
- publication-grade run: `n_reps = 10` per cell.

Cells with fewer repetitions should be reported as provisional.

## 3) Core Metrics

### 3.1 Primary metric

`tokens_per_correct_answer = mean_total_tokens / pass_rate`

where:

- `mean_total_tokens` is the average input plus output tokens within a slice,
- `pass_rate` is fraction of passing runs in that slice.

If `pass_rate = 0`, the metric is non-finite and should be represented as null/non-finite
in leaderboard exports.

### 3.2 Secondary metrics

- `pass_rate`
- `cost_of_pass = estimated_mean_api_cost_usd / pass_rate`
- `quality_score`
- `input_tokens`, `output_tokens`, `api_cost_usd`
- `cached_input_tokens`, `cache_write_tokens` (when reported by the provider)
- `rework_turns`, `governance_turns`, `wall_clock_s`
- governance-specific behavior rates for ambiguity/safety tasks

## 4) Interval Estimation and Derived Statistics

### 4.1 Pass-rate confidence interval

Use a 95% Wilson score interval:

- `ci_pass_rate_low`
- `ci_pass_rate_high`

Wilson intervals are preferred over normal approximations for bounded Bernoulli outcomes,
especially for small sample sizes.

### 4.2 Cost-of-pass confidence interval

Use non-parametric bootstrap with 1,000 resamples over runs within each slice:

- recompute `cost_of_pass` per resample,
- report 2.5th and 97.5th percentiles as:
  - `ci_cop_low`
  - `ci_cop_high`

### 4.3 First-pass and consistency

- `first_pass_rate = P(rework_turns == 1)`
- `consistency_score = 1 - stdev(passed_bool)` (or equivalent bounded stability proxy)

Higher values indicate more predictable scaffold behavior.

### 4.4 Scaffold lift

For each `(task, model)`:

`scaffold_lift(condition) = pass_rate(condition) - pass_rate(UNGOVERNED)`

Lift should only be computed when both rates are defined on matched slices.

### 4.5 Democratization score

For a selected nano model and frontier baseline:

`democratization_score = CoP(nano + best_scaffold) / CoP(frontier + UNGOVERNED)`

Interpretation:

- `< 1.0` means nano+scaffold is cheaper per pass than frontier baseline.
- `= 1.0` parity.
- `> 1.0` no democratization advantage.

## 5) Pareto Frontier

To summarize efficiency-quality tradeoffs, compute the Pareto frontier over points:

- x-axis: `cost_of_pass` (lower is better),
- y-axis: `quality_score` (higher is better),
- point key: `(model, condition, task_suite)`.

A point is Pareto-optimal if no other point has both lower/equal CoP and higher/equal quality
with at least one strict improvement.

## 6) Reporting Rules

All benchmark reports should include:

1. model/provider matrix used,
2. repetition count per slice,
3. confidence intervals for key metrics,
4. explicit treatment of non-finite CoP values,
5. raw run artifact references.

Runs below five repetitions per matched slice are diagnostic only and must not
produce superiority claims. Five repetitions support screening observations;
ten support release-quality publication. Comparative claims additionally
require complete identical cell sets and must preserve or improve correctness,
not merely reduce tokens or estimated cost.

Do not publish absolute performance claims without confidence intervals.
Do not publish comparative claims when intervals overlap substantially without caveats.

## 7) Reproducibility Requirements

- Use fixed benchmark definitions from versioned task/condition files.
- Start runs from clean project fixtures/worktrees.
- Inject evaluator-only acceptance tests only after the agent finishes. A
  standard coding task without a hidden oracle is not scoreable and must fail
  closed. Run project lint and project tests before injection, then run the
  independent oracle exactly once in isolation. Passing requires all three.
- For standard coding tasks, require `SPECSMITH_FULL` to pass `ruff check .`
  and `pytest` after its latest write before accepting `done`. Failed checks
  trigger measured repair turns. Do not apply this gate to comparison
  conditions, and never expose the hidden oracle during repair.
- Disable pytest and Ruff caches during grading so generated cache files do not
  contaminate diffs, scope measurements, or subsequent validation.
- Record model identifiers, provider, run timestamp, and benchmark commit SHA.
- Record model-specific compatibility parameters. GPT-5.6 Chat Completions
  runs use `reasoning_effort=none` because that is the function-tool mode
  supported by the provider; every condition for that model uses the same mode.
- Preserve raw benchmark output JSON for auditability.

## 8) Limitations

- Provider pricing and model behavior can drift over time. Dollar cost is a
  secondary estimate based on the versioned pricing table; token efficiency is
  the provider-neutral primary measure.
- LLM judge components can add evaluator variance.
- Cross-domain comparability depends on validator quality per domain.

These limitations must be disclosed in external benchmark communication.
