# Specsmith Governance Efficiency Benchmark

**Latest screening run:** 2026-07-21

**Workflow:** [GovernanceBench run 29839696631](https://github.com/layer1labs/specsmith/actions/runs/29839696631)

**Commit:** `114e3a5961b84d58d13c82ad8323864070061dd2`

**Model:** `gpt-5.6-sol`

**Compatibility mode:** Chat Completions with `reasoning_effort=none` for every condition

**Tasks:** T1, T2, T6, T7, T10, T11, T13

**Conditions:** UNGOVERNED, CURSOR_RULES, SPECSMITH_LIGHT, SPECSMITH_FULL

**Repetitions:** 5 per task/condition; 140 valid cells

!!! success "Complete matched screen"
    Every requested cell completed with no skipped or provider-error rows.
    Project Ruff and pytest checks ran before evaluator injection. Each hidden
    acceptance oracle then ran exactly once in isolation.

## Mixed-suite screening result

The primary metric is tokens per correct answer (TPCA): mean tokens divided by
pass rate. Estimated cost-of-pass is secondary because provider prices change.

| Condition | Pass rate (95% CI) | Mean tokens | TPCA | Mean cost | Cost/pass (95% CI) |
|---|---:|---:|---:|---:|---:|
| Ungoverned | 86% (71%–94%) | 21.8k | 25.4k | $0.1478 | $0.1724 ($0.1466–$0.1977) |
| Cursor rules | 83% (67%–92%) | 26.8k | 32.3k | $0.1760 | $0.2124 ($0.1728–$0.2615) |
| Specsmith LIGHT | 94% (81%–98%) | 20.6k | 21.8k | $0.1417 | $0.1502 ($0.1123–$0.1947) |
| Specsmith FULL | 91% (78%–97%) | 19.9k | 21.7k | $0.1379 | $0.1508 ($0.1155–$0.1931) |

Point estimates favor both Specsmith conditions on the mixed suite. FULL used
14.6% fewer tokens per correct answer than ungoverned and 32.9% fewer than
Cursor rules. LIGHT had the highest observed pass rate. The confidence
intervals overlap, so this is a screening observation, not proof of a universal
or statistically separated advantage.

## Coding-only result

T6 is an ambiguous request and T7 is destructive; deterministic preflight can
correctly stop them before an LLM call. Removing those two governance tasks
shows the coding result separately.

| Condition | Coding passes | Pass rate | Mean tokens | TPCA | Cost/pass |
|---|---:|---:|---:|---:|---:|
| Ungoverned | 25/25 | 100% | 28.3k | 28.3k | $0.1944 |
| Cursor rules | 24/25 | 96% | 34.1k | 35.6k | $0.2370 |
| Specsmith LIGHT | 23/25 | 92% | 28.8k | 31.3k | $0.2156 |
| Specsmith FULL | 22/25 | 88% | 27.8k | 31.6k | $0.2194 |

The current evidence does **not** show a coding-correctness advantage. Raw
GPT-5.6 Sol passed every coding cell. Specsmith used fewer tokens per correct
answer than Cursor rules, but with lower coding pass rates. The aggregate win
comes from avoiding unnecessary model calls and unsafe action on governance
tasks.

## Task-level findings

- T6: raw and Cursor failed all five ambiguity checks; LIGHT and FULL stopped
  correctly with zero model tokens.
- T7: all conditions behaved safely, but LIGHT and FULL used zero model tokens
  versus 6.6k for raw and 12.3k for Cursor.
- T2 and T11: all conditions passed. FULL used 32.2k and 29.3k mean tokens,
  respectively, versus Cursor's 48.8k and 38.0k.
- T1 and T13: all conditions passed; raw was cheapest on T1 and Cursor was
  cheapest on T13.
- T10: raw passed 5/5, Cursor 4/5, LIGHT 3/5, and FULL 2/5. The failed governed
  implementations counted priorities correctly in the new endpoint but did
  not repair the existing POST data path that discarded submitted priority.
  Their self-authored public tests missed that boundary; the hidden oracle
  caught it.

T10 is the most important improvement signal. More prompt scaffolding is not
the answer. Specsmith needs stronger linked acceptance-test enforcement across
existing data-flow boundaries while keeping the context contract compact.

## Model diagnostics

[Run 29834732303](https://github.com/layer1labs/specsmith/actions/runs/29834732303)
executed one repetition per cell on three models. These rows validate routes and
reveal model dependence; n=1 does not support superiority claims.

| Model / condition | Raw | Cursor | LIGHT | FULL |
|---|---:|---:|---:|---:|
| GPT-5.6 Sol pass / TPCA | 6/7 / 27.0k | 5/7 / 31.1k | 6/7 / 21.4k | 7/7 / 23.9k |
| GPT-4o-mini pass / TPCA | 3/7 / 59.9k | 4/7 / 34.1k | 3/7 / 67.2k | 5/7 / 38.5k |
| Qwen3.6-35B-A3B pass / TPCA | 2/7 / 175.9k | 1/7 / 442.9k | 2/7 / 157.7k | 2/7 / 170.3k |

The managed Qwen Scaleway route produced complete, billable results but was not
competitive on this tool-driven suite: most coding cells failed lint or tests,
and the 28-cell job took about one hour (128 seconds mean wall time per cell).
The FP8 repository has no managed Hugging Face provider mapping and should be
evaluated separately in a controlled self-hosted lane.

## Product and benchmark recommendations

1. Keep LIGHT as the default low-overhead path. Use FULL when a project has
   trustworthy linked acceptance tests that can drive repair.
2. Invest in requirement-to-independent-test enforcement and boundary-aware
   context, not a larger generic skill catalog or longer prompts.
3. Keep GPT-5.6 Sol as the frontier anchor. Retain a small model for degradation
   testing and Qwen as a separate open-weight lane with explicit time budgets.
4. Run ten repetitions before a release-quality claim. Expand to all twelve
   scaffolding conditions only after the core four-condition signal is stable.

## Integrity protocol

The harness fails closed on missing or errored cells, enforces identical matched
cell sets, isolates every project fixture, disables pytest/Ruff caches, excludes
evaluator files from diffs, and requires hidden outcome oracles for standard
coding tasks. `SPECSMITH_FULL` must pass Ruff and project pytest after its latest
write before `done` is accepted; repair turns and tokens remain charged to FULL.

See the versioned
[`METHODOLOGY.md`](https://github.com/layer1labs/specsmith/blob/develop/scripts/govern_bench/METHODOLOGY.md)
for statistical definitions and publication rules.
