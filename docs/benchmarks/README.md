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
