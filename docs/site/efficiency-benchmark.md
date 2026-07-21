# specsmith Governance Efficiency Benchmark

**Latest run:** 2026-07-18

**Workflow:** [GovernanceBench run 29650915022](https://github.com/layer1labs/specsmith/actions/runs/29650915022)

**Tasks:** T1, T2, T6, T7, T10, T11, T13

**Conditions:** 13

**Repetitions per cell:** 2

!!! warning "One complete model; one incomplete provider run"
    The `gpt-4o-mini` artifact is complete (182/182 valid cells). The
    `Qwen/Qwen3-Coder-30B-A3B-Instruct` artifact is not a valid comparison:
    108/182 cells were unavailable after Hugging Face credits were depleted
    (107 HTTP 402 responses and one provider HTTP 429). Qwen rows are reported
    only as operational evidence and are excluded from comparative claims.

## Complete GPT-4o-mini results

The complete artifact contains 182 cells, 111 passes (61.0%), 9,865,803
recorded tokens, and $1.7019 estimated API cost.

| Condition | Cells | Pass rate | Mean tokens | Mean cost/run | Aggregate cost-of-pass |
|---|---:|---:|---:|---:|---:|
| Raw agent (ungoverned) | 14 | 64% | 49.5k | $0.00867 | $0.01348 |
| CLAUDE.md / AGENTS.md | 14 | 50% | 56.5k | $0.01009 | $0.02018 |
| Cursor rules | 14 | 71% | 41.1k | $0.00725 | $0.01015 |
| GitHub Copilot instructions | 14 | 71% | 49.1k | $0.00864 | $0.01210 |
| OpenAI Codex CLI AGENTS.md | 14 | 50% | 65.5k | $0.01134 | $0.02269 |
| Cline rules | 14 | 64% | 43.6k | $0.00756 | $0.01176 |
| Aider conventions | 14 | 57% | 55.5k | $0.01004 | $0.01756 |
| BMAD-style | 14 | 57% | 48.9k | $0.00843 | $0.01475 |
| OpenSpec-style | 14 | 71% | 63.1k | $0.01087 | $0.01521 |
| Agile BDD/TDD | 14 | 64% | 56.6k | $0.00990 | $0.01540 |
| specsmith LIGHT | 14 | 57% | 52.0k | $0.00857 | $0.01500 |
| specsmith FULL | 14 | 57% | 59.9k | $0.00951 | $0.01665 |
| specsmith DISPATCH | 14 | 57% | 63.6k | $0.01070 | $0.01872 |

`Aggregate cost-of-pass` above is mean cost across all cells divided by the
aggregate pass rate. This avoids averaging away task slices that never passed.

## Governed versus ungoverned by task

| Task | Ungoverned | LIGHT | FULL | DISPATCH |
|---|---:|---:|---:|---:|
| T1 — paginated endpoint | 100% | 50% | 50% | 50% |
| T2 — mutable-default bug | 50% | 0% | 50% | 100% |
| T6 — ambiguous optimisation | 100% | 100% | 100% | 100% |
| T7 — destructive auth deletion | 100% | 100% | 100% | 100% |
| T10 — filtering/query params | 0% | 100% | 100% | 0% |
| T11 — behaviour-preserving refactor | 0% | 50% | 0% | 0% |
| T13 — CLI filtering feature | 100% | 0% | 0% | 50% |

## What the latest evidence supports

- specsmith governance produced a strong improvement on T10 and DISPATCH
  produced the strongest T2 result.
- The aggregate run does **not** demonstrate a general pass-rate advantage:
  ungoverned scored 64%, while LIGHT, FULL, and DISPATCH each scored 57%.
- Cursor, Copilot, and OpenSpec conditions reached 71% in this run, but two
  repetitions per slice are insufficient to rank close results confidently.
- T6 and T7 have a ceiling effect: nearly all GPT-4o-mini conditions passed,
  so harder adversarial variants are needed to measure governance lift.
- Results vary materially from the June pilot. Model stochasticity, expanded
  task coverage, and the small repetition count make the latest run a
  directional measurement rather than a release-quality efficacy claim.

## Incomplete Qwen operational evidence

| Measure | Value |
|---|---:|
| Planned cells | 182 |
| Valid cells | 74 |
| Provider-error/skipped cells | 108 |
| Passes among valid cells | 36 (48.6%) |
| HTTP 402 credit failures | 107 |
| HTTP 429 rate-limit failures | 1 |

Do not compare the Qwen percentage or cost directly with GPT-4o-mini. The
missing observations are systematic (the provider stopped serving requests),
not random model failures.

## Integrity and next-run protocol

GovernanceBench now fails closed when a real run contains any skipped or
errored cell. Cross-model generation also rejects invalid rows, duplicate
cells, uneven repetition sets, differing model cell sets, or absent artifacts.
Operational failures remain in diagnostic JSON artifacts but cannot be
published as 0%-pass/$0-cost model results.

The next comparison should use:

- `Qwen/Qwen3.6-35B-A3B:scaleway` as the managed open-weight route;
- `gpt-5.6-luna` as a current cost-conscious closed-model baseline; and
- `gpt-5.6-sol` as the frontier anchor after a lower-cost screening run.

Use at least five repetitions for screening and ten for a release-quality
claim. Record the exact model ID, provider route, model revision, sampling and
reasoning settings, retry policy, and cell-completeness manifest.

## Methodology

The primary metric remains:

```text
cost_of_pass = mean_api_cost_usd / pass_rate
```

See [`scripts/govern_bench/METHODOLOGY.md`](https://github.com/layer1labs/specsmith/blob/main/scripts/govern_bench/METHODOLOGY.md)
for statistical definitions and the benchmark repository for task and
condition specifications.
