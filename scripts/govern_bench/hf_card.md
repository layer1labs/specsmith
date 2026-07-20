---
pretty_name: GovernanceBench
license: mit
language:
  - en
task_categories:
  - text-generation
  - text-classification
tags:
  - benchmarking
  - llm-evaluation
  - governance
  - software-engineering
---

# GovernanceBench Dataset Card

## Dataset Summary

GovernanceBench is a benchmark suite for measuring how governance and scaffolding affect
agentic software-development outcomes. It evaluates task completion quality, safety behavior,
and cost efficiency across multiple governance conditions, model tiers, and task domains.

Benchmark publication status: **TBD** (no final leaderboard claims in this card yet).

## Supported Tasks and Leaderboards

- Primary benchmark task type: agentic implementation/editing tasks with deterministic
  validators and optional LLM judging.
- Governance-specific task types include ambiguity-handling and safety/refusal behavior.
- Leaderboard format is defined in `scripts/govern_bench/leaderboard_schema.json`.

Task suites:

- Core suite: `T1`–`T13` (currently available)
- Multi-domain suites: `T14`–`T27` (available; empirical coverage depends on the run)

## Metrics

Primary metric:

- `tokens_per_correct_answer = mean_total_tokens / pass_rate`

Secondary metrics:

- `pass_rate`
- `cost_of_pass = estimated_mean_api_cost_usd / pass_rate`
- `quality_score`
- `input_tokens`, `output_tokens`, `api_cost_usd`
- `rework_turns`, `governance_turns`, `wall_clock_s`
- `first_pass_rate`, `consistency_score`
- `scaffold_lift` vs `UNGOVERNED`
- `democratization_score`

Confidence and inference methodology is documented in `scripts/govern_bench/METHODOLOGY.md`.

## Dataset Sources

GovernanceBench combines:

1. **Task definitions**: curated benchmark prompts and acceptance criteria from
   `scripts/govern_bench/tasks/*.yml`
2. **Project fixtures**: starter code/artifacts under `scripts/govern_bench/projects/`
3. **Condition templates**: governance/system-prompt variants from `scripts/govern_bench/conditions.py`
4. **Run outputs**: per-run execution telemetry and aggregate benchmark artifacts

Sources are benchmark-internal and generated from the repository artifacts above.

## Dataset Structure

Planned HF export structure:

- `leaderboard.json`: aggregate leaderboard rows (schema-validated)
- `bench-results-*.json`: per-run detailed results
- `report.md`: human-readable benchmark report

Each leaderboard row corresponds to one `(model, scaffold, task_suite)` slice.

## Data Fields (leaderboard rows)

Required fields:

- `model`
- `provider`
- `tier`
- `scaffold`
- `task_suite`
- `pass_rate`
- `cop_usd`
- `scaffold_lift`
- `is_open_source`

Optional fields may include rank, confidence bounds, repetition count, and run metadata.

## License

This benchmark repository is distributed under the project license (`MIT`).
Third-party model outputs may have additional usage terms from their providers.

## Limitations and Biases

- Metric outcomes are sensitive to model snapshots, provider behavior, and pricing updates.
- LLM judging can introduce evaluator variance; deterministic validators are preferred where possible.
- Planned suites and metrics should not be treated as empirical findings until benchmark runs are executed.

## Citation

Citation metadata: **TBD**
