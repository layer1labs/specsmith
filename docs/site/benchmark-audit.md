# Long-Horizon Benchmark and Weakness Audit

GovernanceBench `T28` is a 20-turn product task spanning a Python/FastAPI API,
Go worker, TypeScript/React UI, Playwright journey, JSON Schema, CSS, public
tests, and architecture documentation. Its result is reported separately as
well as in the eight-task suite so cheap governance gates cannot hide
long-horizon cost.

## Current five-repetition screen

[Workflow 29963515885](https://github.com/layer1labs/specsmith/actions/runs/29963515885)
ran commit `f474bb6b772fe71fd7f1b20d585e23b15fec746a` with GPT-5.6 Sol,
Cursor rules, Specsmith FULL, and five matched repetitions. Every T28 cell
passed project checks and the evaluator-isolated oracle.

| Condition | Correct | Mean tokens | Tokens/correct | Mean turns | Mean wall time |
|---|---:|---:|---:|---:|---:|
| Cursor rules | 5/5 | 57.3k | 57.3k | 9.2 | 81.0s |
| Specsmith FULL | 5/5 | 20.6k | 20.6k | 6.6 | 65.9s |

With equal observed correctness, FULL used 64.1% fewer tokens per correct
answer and 18.6% less wall time. This supersedes the earlier `29942515095`
screen, where FULL used 71.4k tokens/correct. The measured improvement came
from a requirement-linked change map, milestone progress, a minimal initial
tool surface, just-in-time reads, and compact replacement of stale context.

The current audit found one medium FULL finding and no high/critical FULL
finding. A successful repetition used 12 turns versus a six-turn median because
deterministic validation rejected the first backend implementation and forced
repair. Its 30.1k tokens remain charged to FULL. This is the intended behavior:
correctness evidence can spend a bounded repair turn, but the benchmark never
deletes that cost as an outlier.

## Qwen long-horizon diagnostic

[Workflow 29962883256](https://github.com/layer1labs/specsmith/actions/runs/29962883256)
tested three managed Hugging Face routes at one repetition. All six T28 cells
failed, so none has finite TPCA and none was promoted to a repeated screen.

| Route | Cursor T28 | FULL T28 | FULL tokens | Diagnostic |
|---|---:|---:|---:|---|
| Qwen3.6-35B-A3B / DeepInfra | fail | fail | 116.5k | all ten boundaries written, but repair remained serial and exhausted 20 turns |
| Qwen3-Coder-Next / Novita | fail | fail | 68.1k | lower input history, incomplete cross-boundary validation |
| Qwen3-Coder-480B-A35B / Novita | fail | fail | 55.4k | model size did not prevent milestone fragmentation |

The follow-up changed action shape, not the turn cap. In
[workflow 29966620911](https://github.com/layer1labs/specsmith/actions/runs/29966620911),
Qwen3.6/DeepInfra FULL passed T2 and T11 (2/3) at 100.7k TPCA versus Cursor's
T11-only 1/3 at 358.7k TPCA. FULL T28 still failed after 133.7k tokens and 20
turns. Its public validators passed, but the hidden oracle scored 3/5 because
the shared schema did not require `acknowledged_at` and the browser test did not
use semantic role locators. The trace also showed repeated reads of the public
UI validator after its failure instead of an edit.

The controller now keeps scalar tools valid while adding composite operations,
adds a visible deterministic shared-contract validator, and maps each failed
public validator to versioned requirement-linked files. The repair instruction
explicitly makes failure output authoritative and suppresses unchanged validator
rereads. The hidden oracle remains isolated. A native Qwen serving lane should
still use the model's `qwen3_coder` tool parser or Qwen's agent scaffold before
comparing model sizes again.

The targeted [T28 follow-up 29969671380](https://github.com/layer1labs/specsmith/actions/runs/29969671380)
confirmed that the contract visibility worked but the managed route remained
inefficient. FULL passed the hidden oracle 5/5 after implementing all ten declared
files, versus Cursor's 4/5, but neither cell was correct. FULL consumed 203.2k
tokens and 891.3 seconds, then exhausted turns with one Ruff `I001` after its
last write. Turns 15–20 repeatedly requested unchanged Go/UI files despite the
focused repair instruction. The benchmark audit therefore classifies the next
move as a serving/tool-policy experiment, not more milestones or a larger cap.

The final scorer now reruns public task validators before installing the hidden
oracle, applies at most one FULL default-safe Ruff repair, and executes the
oracle exactly once after the model loop. Agent-loop equilibrium uses public
evidence only, so hidden results cannot cause another model repair turn.

## Completion and oracle boundaries

The clean starter cannot pass the hidden oracle without implementing:

- one shared incident field/enumeration contract;
- create, list/filter, and acknowledge API behavior;
- Go `NormalizeAlert` validation and normalization;
- loading, empty, error, filtering, and acknowledge UI states;
- accessible controls and a non-skipped Playwright journey;
- meaningful public boundary tests; and
- an architecture record covering end-to-end data flow.

For FULL, controller-owned Ruff, pytest, Go, and UI validators must pass after
the latest write. The evaluator then returns only an equilibrium decision, not
hidden test content, to a bounded repair loop. One Ruff default-safe-fix pass is
permitted before a lint-only failure is returned; unsafe fixes are never
enabled.

## Run and audit it

Start with one repetition:

```bash
python scripts/govern_bench/run_bench.py \
  --task T28 \
  --condition CURSOR_RULES \
  --condition SPECSMITH_FULL \
  --provider openai \
  --model gpt-5.6-sol \
  --reps 1 \
  --json-output bench-results-t28.json \
  --output bench-report-t28.md
```

The runner writes `bench-results-t28.audit.json`. Combine outcome findings with
repository health through Specsmith:

```bash
specsmith audit \
  --project-dir . \
  --benchmark-results bench-results-t28.json \
  --report benchmark-project-audit.json
```

High or critical benchmark weaknesses make the combined audit exit non-zero.

| Weakness | Meaning | First response |
|---|---|---|
| `incomplete_evidence` / `missing_cells` | A requested result is absent or errored. | Repair infrastructure and rerun the identical grid. |
| `uneven_repetitions` / `duplicate_cells` | Compared evidence is not one matched grid. | Reject and regenerate the artifact. |
| `turn_budget_exhausted` | Work reached the bounded cap. | Inspect action targets; do not raise the cap blindly. |
| `tool_call_serialization` | The route repeatedly emits one action per turn. | Use a compatible parser or bounded composite tools. |
| `broad_reread_churn` | Unchanged files dominate reads. | Replace bodies with version receipts and active evidence. |
| `milestone_fragmentation` | Several components changed without a completed boundary. | Stage the active milestone and batch independent files. |
| `premature_text_stop` | Narration stopped before a terminal action. | Permit one bounded continuation, then fail closed. |
| `acceptance_gap` | Public checks pass but the hidden oracle fails. | Add an immutable independent boundary test. |
| `scope_expansion` | Writes exceed declared requirement boundaries. | Verify necessity or constrain retrieval/edits. |
| `cursor_correctness_regression` | FULL passes less often on a task. | Repair correctness before claiming efficiency. |
| `cursor_efficiency_regression` | FULL TPCA exceeds Cursor by more than 10%. | Remove rereads, planning, or validator churn. |
| `verification_repair_outlier` | A row materially exceeds its cell's turn median. | Return only focused failure evidence and keep the repair bounded. |
| `context_dominance` | Input is at least ten times output. | Use stable prefixes, JIT retrieval, and compaction. |

## Improvement loop

1. Run a matched n=1 diagnostic.
2. Audit every correctness, efficiency, and completeness weakness.
3. Link a reproducible miss to a requirement and independent regression test.
4. Change the smallest controller, context, or serving boundary implicated by
   the trace.
5. Rerun the affected cells; promote only correct diagnostics to n=5.
6. Require n=10 before a release-quality statistical claim.

The audit is deterministic and spends no judge-model tokens. Raw transcripts,
content-free tool targets and argument hashes, diffs, validator output,
controller decisions, task metadata, and exact provider receipts remain the
engineering evidence.
