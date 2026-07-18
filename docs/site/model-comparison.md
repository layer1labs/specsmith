# specsmith Governance Efficiency — Model Comparison

**Run:** [29650915022](https://github.com/layer1labs/specsmith/actions/runs/29650915022)

**Date:** 2026-07-18

!!! danger "Cross-model ranking withheld"
    GPT-4o-mini completed all 182 requested cells. Qwen3-Coder completed only
    74; 108 cells were unavailable because the Hugging Face provider stopped
    serving requests. A partial provider run cannot support model rankings,
    relative cost-of-pass claims, or governance-lift comparisons.

## Artifact completeness

| Model | Requested | Valid | Provider errors | Passes among valid | Comparative status |
|---|---:|---:|---:|---:|---|
| `gpt-4o-mini` | 182 | 182 | 0 | 111 (61.0%) | Valid single-model evidence |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | 182 | 74 | 108 | 36 (48.6%) | Invalid for comparison |

Qwen failures consisted of 107 HTTP 402 credit-depletion responses and one
HTTP 429 token-per-minute response. They are infrastructure failures, not
failed task solutions.

## Complete-model findings

For GPT-4o-mini, ungoverned achieved 64% aggregate pass rate. specsmith LIGHT,
FULL, and DISPATCH each achieved 57%. The results are task-dependent: LIGHT and
FULL improved T10 from 0% to 100%, while governed conditions underperformed on
T1 and T13. T6 and T7 were non-discriminating because nearly every condition
passed.

See [Governance Efficiency Benchmark](efficiency-benchmark.md) for complete
condition and task tables.

## Next comparison matrix

| Role | Model | Rationale |
|---|---|---|
| Historical baseline | `gpt-4o-mini` | Preserves continuity with prior runs |
| Open-weight managed route | `Qwen/Qwen3.6-35B-A3B:deepinfra` | Current Qwen coding/repository model with a live tool-capable HF route |
| Cost-conscious current model | `gpt-5.6-luna` | Modern closed-model screening baseline |
| Frontier anchor | `gpt-5.6-sol` | Upper-bound comparison for complex coding and reasoning |

The FP8 repository `Qwen/Qwen3.6-35B-A3B-FP8` is suitable for a separate
self-hosted experiment. It currently has no managed Hugging Face Inference
Provider mapping, so combining it with managed API models would also combine
model-quality and serving-infrastructure effects.

## Publication rule

Future reports are generated only when every selected model has the identical
task/condition/repetition cell set and every cell is valid. Incomplete artifacts
remain downloadable for diagnosis but cannot produce a successful comparison.
