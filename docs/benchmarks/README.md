# Benchmark Suites

The executable GovernanceBench harness lives in `scripts/govern_bench/`. It
compares governed and non-governed agent workflows with isolated fixtures,
hidden acceptance oracles, complete-cell enforcement, token accounting, and
versioned task/condition definitions.

This directory contains complementary process scenarios for traceability,
audit, recovery, and multi-agent governance. They are specifications, not
executable GovernanceBench cells.

## Core metrics to capture

- tokens per correct answer (primary for executable model runs);
- estimated cost-of-pass and wall time (secondary);
- requirement/test trace coverage and audit completeness;
- interrupted-session recovery fidelity.

## Comparison axes
- no governance
- Spec Kit
- OpenSpec
- BMAD
- direct agent (ungoverned)
- specsmith governed workflow

## Scenarios

See `docs/benchmarks/scenarios/` for all scenario definitions.

See the [current executable results](../site/efficiency-benchmark.md) and the
[model comparison](../site/model-comparison.md).

## Current validated evidence

- Current frontier screen: GPT-5.6 Sol runs `29963772623` and `29963515885`,
  eight exact task types, Cursor rules/FULL, and five repetitions per cell.
  FULL passed 40/40 at 9.0k TPCA; Cursor rules passed 34/40 at 33.8k TPCA.
- Model/route diagnostic: run `29834732303`, the same matched task/condition
  grid, one repetition for GPT-5.6 Sol, GPT-4o-mini, and
  Qwen3.6-35B-A3B.
- Corrected long-horizon diagnostic: run `29930247611`, T28 raw/LIGHT/FULL,
  one repetition for GPT-5.6 Sol and Qwen3.6-35B-A3B. GPT passed all three;
  Qwen reached the bounded turn ceiling in all three. This is diagnostic only.
- Current long-horizon screen: run `29963515885`, T28 Cursor/FULL, five
  repetitions for GPT-5.6 Sol. Both passed 5/5; Cursor used 57.3k TPCA and
  FULL 20.6k.
- Corrected managed Qwen diagnostic: run `29944111036`, T28 Cursor/FULL, one
  repetition. Both reached 20 turns without passing; TPCA is infinite and the
  audit reports turn exhaustion, acceptance gaps, and context dominance.
- July 23 Qwen admission diagnostics: Qwen3.6/DeepInfra T28 FULL runs
  `30010219286`, `30011743699`, and `30013020354` were respectively correct at
  180.9k tokens, oracle-failing at 136.4k, and public-test-failing at 151.7k.
  All used 20 turns and remain separate n=1 cells. Qwen3-Coder-Next/Novita runs
  `30007255204` and `30007554143` failed provider/tool admission and are not
  native-parser evidence.
- Incomplete, cancelled, provider-error, and artifact-error attempts are
  diagnostic provenance only. They must not populate a comparison table.

## Continuous efficiency discipline

For each complete run, compare mixed-suite and coding-only correctness, TPCA,
cost/pass, repair turns, and wall time at task level. A reproducible regression
becomes a linked requirement and independent test. Validate the narrow fix on
affected cells, then rerun the identical complete grid before publishing an
improvement. This keeps benchmark learning tied to implementation rather than
prompt expansion or selective reporting.

## Long-horizon product slice

`T28` is intentionally reported as its own slice. It requires one coherent
incident-command product across Python/FastAPI, Go, TypeScript/React,
Playwright, JSON Schema, CSS, tests, and architecture documentation. Its
20-turn ceiling is task metadata, not a global expansion of every benchmark
cell. The evaluator-only oracle verifies API behavior, contract parity, Go
normalization, UI states and accessibility, the browser journey, public tests,
and the architecture record.

Each run writes an adjacent `*.audit.json` artifact. The audit is deterministic
and flags incomplete evidence, undersampling, acceptance gaps, correctness
regressions, token amplification, and context-dominated spend.
