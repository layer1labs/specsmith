# Long-Horizon Benchmark and Weakness Audit

GovernanceBench `T28` measures whether an agent can keep one product contract
coherent across a Python/FastAPI API, Go alert worker, TypeScript/React UI,
Playwright browser journey, JSON Schema, CSS, public tests, and architecture
documentation. It is a separate long-horizon slice, not another cheap task in
the mixed-suite average.

## Why a separate long-horizon slice

Short repair tasks reveal scope discipline and boundary mistakes, but they do
not measure planning across components or whether early decisions remain
consistent later. T28 therefore declares a 20-turn ceiling while ordinary tasks
retain the normal bounded budget. Report its correctness, tokens, cost, turns,
and weaknesses separately before combining it with any suite.

For `SPECSMITH_FULL`, completion is blocked until Python lint/tests, Go tests,
and the deterministic UI validator all pass after the final file write.

The clean starter passes only its health check. It cannot pass the hidden
oracle without implementing all of these boundaries:

- shared incident fields and enums in JSON Schema;
- create, list/filter, and acknowledge API behavior;
- Go `NormalizeAlert` validation and normalization;
- loading, empty, error, filtering, and acknowledge UI states;
- accessible controls and a non-skipped Playwright journey;
- meaningful public boundary tests; and
- an architecture record covering the end-to-end data flow.

The oracle evaluates behavior rather than one spelling or schema idiom. For
example, nullable fields may use JSON Schema `type`, `anyOf`, or `oneOf`; a UI
may express the no-incidents state semantically; and architecture prose may use
either “in-memory” or “in memory.” This keeps equivalent correct solutions from
being counted as failures.

## Run it

Start with one matched diagnostic repetition because a long-horizon cell is
substantially more expensive than a short repair:

```bash
python scripts/govern_bench/run_bench.py \
  --task T28 \
  --condition UNGOVERNED \
  --condition SPECSMITH_LIGHT \
  --condition SPECSMITH_FULL \
  --provider openai \
  --model gpt-5.6-sol \
  --reps 1 \
  --json-output bench-results-t28.json \
  --output bench-report-t28.md
```

The runner automatically writes `bench-results-t28.audit.json`. Increase to
five repetitions only after the diagnostic proves the fixture, provider route,
turn budget, and hidden oracle are stable.

## Audit what happened

The normal `specsmith audit` remains the project governance-health command. Add
a benchmark artifact to correlate that health with measured agent outcomes:

```bash
specsmith audit \
  --project-dir . \
  --benchmark-results bench-results-t28.json \
  --report benchmark-project-audit.json
```

The combined JSON retains every ordinary audit check and adds condition metrics,
evidence completeness, and structured weaknesses. High or critical benchmark
weaknesses make the audit exit non-zero.

| Weakness | Meaning | First response |
|---|---|---|
| `incomplete_evidence` | A provider cell skipped or errored. | Repair infrastructure and rerun the identical grid. |
| `missing_cells` | A model/task/condition combination is absent. | Rerun every missing cell with the same repetition set. |
| `duplicate_cells` | A repetition key appears more than once. | Reject the artifact and regenerate the requested cells. |
| `uneven_repetitions` | Compared cells do not share one repetition count. | Rerun or filter to an identical matched grid. |
| `unreplayable_diff` | A stored final patch is malformed or was compacted. | Reject the artifact, repair serialization, and rerun the same cells. |
| `undersampled` | Fewer than five repetitions exist in a cell. | Treat as diagnostic; do not publish superiority claims. |
| `acceptance_gap` | Public tests passed but the independent oracle failed. | Link the missed boundary to an immutable acceptance test. |
| `correctness_regression` | A Specsmith condition passed less often than raw on a task. | Keep the lighter path and repair that task before expanding governance. |
| `token_amplification` | TPCA is over 10% worse than raw. | Remove repeated context or calls before adding instructions. |
| `context_dominance` | Mean input is at least ten times mean output. | Use just-in-time retrieval, stable cached prefixes, and compaction. |

The report is deterministic. It does not spend tokens on an LLM judge and does
not infer root causes beyond the evidence present in raw rows. Transcripts,
diffs, validator output, controller decisions, and task requirements remain the
sources for the subsequent engineering diagnosis.

## Improvement loop

1. Run one matched T28 diagnostic across raw, LIGHT, and FULL.
2. Audit the raw artifact and inspect every high/critical weakness.
3. Convert reproducible misses into linked requirements and independent tests.
4. Fix the smallest implicated governance or retrieval boundary.
5. Rerun the affected cells, then the complete matched T28 slice.
6. Publish only complete five-repetition screening evidence; require ten for a
   release-quality claim.
