# Long-Horizon Benchmark and Weakness Audit

GovernanceBench `T28` is a 20-turn product task spanning a Python/FastAPI API,
Go worker, TypeScript/React UI, Playwright journey, JSON Schema, CSS, public
tests, and architecture documentation. Its result is reported separately as
well as in the eight-task suite so cheap governance gates cannot hide
long-horizon cost.

## Matched five-repetition screen

[Workflow 30045327768](https://github.com/layer1labs/specsmith/actions/runs/30045327768)
ran commit `5790d41971e027d2abd34973169c10a57e277eaa` with GPT-5.6 Sol,
Cursor rules, Specsmith FULL, and five matched repetitions. Every T28 cell
passed project checks and the evaluator-isolated oracle.

| Condition | Correct | Mean tokens | Tokens/correct | Mean turns | Mean wall time |
|---|---:|---:|---:|---:|---:|
| Cursor rules | 5/5 | 69.1k | 69.1k | 10.8 | 88.9s |
| Specsmith FULL | 5/5 | 32.0k | 32.0k | 11.4 | 86.6s |

With equal observed correctness, FULL used 53.6% fewer tokens per correct
answer, 26.0% lower measured provider cost, and 2.6% less wall time. The audit
found one medium Cursor-only scope-expansion finding and no FULL weakness; its
next action is `expand_release_sample`. The earlier `29963515885` screen remains
part of the versioned eight-task aggregate but is not combined with this newer
commit.

Four FULL repetitions needed the same deterministic backend repair and spent
one turn rereading the single failed file after its prior write body had been
compacted to a digest. That cost remains charged to this screen. The resulting
controller improvement now returns bounded current content when exactly one
requirement-linked file fails and removes read tools for the next turn, enabling
an immediate repair write. Ambiguous multi-file failures retain the safer
read-capable path.

## Current optimized Sol envelope

[Workflow 30077217017](https://github.com/layer1labs/specsmith/actions/runs/30077217017)
verified that change at n=5 on commit `3d86308`. Every FULL cell passed public
checks and the isolated oracle.

| FULL screen | Correct | TPCA | Mean input | Mean turns | Mean cost |
|---|---:|---:|---:|---:|---:|
| Before focused handoff | 5/5 | 32,020 | 25,356 | 11.4 | $0.2640 |
| Focused handoff | 5/5 | 28,314 | 21,725 | 10.2 | $0.2519 |

The same-model reduction is 11.6% TPCA, 14.3% input tokens, 10.5% turns, and
4.6% measured cost. All three new repair traces skipped the former reread and
wrote the focused file immediately. The audit found no weakness and selected
`expand_release_sample`; 28,314 TPCA is now the versioned T28 frontier envelope.

## Feedback-loop example

Four GPT-OSS-120B diagnostics show how the audit drives bounded changes without
turning failures into a leaderboard win:

| Workflow | Smallest changed boundary | Result |
|---|---|---|
| [30077072490](https://github.com/layer1labs/specsmith/actions/runs/30077072490) | DeepInfra provider route | one valid tool call, then two empty continuations |
| [30077459159](https://github.com/layer1labs/specsmith/actions/runs/30077459159) | Novita provider route only | continuation worked; 20 serialized actions exposed an adaptive-state bug |
| [30077929145](https://github.com/layer1labs/specsmith/actions/runs/30077929145) | composite-read state separated from writes | 44,692 tokens and 17 turns, but `done` arguments arrived as text |
| [30078601832](https://github.com/layer1labs/specsmith/actions/runs/30078601832) | exact-schema completion recovery | stochastic trace never completed scope; 49,339 tokens, 20 turns, failed |

The first trace created `tool_continuation_failure`; the second led to
independent read/write adaptation; the third led to a narrow completion guard
that still requires complete write evidence and unchanged validators. The
fourth did not reproduce the prerequisite and was rejected. No further managed
GPT-OSS repetition or larger turn budget is justified.

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
confirmed that contract visibility worked but the managed route remained
inefficient. Later runs separated scaffold defects from route reliability:

- `30010219286` was correct at 180,895 tokens, but exhausted 20 turns and
  repeated 26 of 48 reads.
- `30011743699` reduced tokens to 136,360 after digest and repair controls, but
  failed the independent oracle.
- `30013020354` passed the oracle 5/5, yet its own tests coupled to a nonexistent
  private `_data` attribute and still failed after 151,666 tokens and 20 turns.

The resulting controller records model-owned writes and known absence as
epistemic evidence, withholds already-known reads at the next milestone, and
returns repair writes directly to deterministic validation. The public T28
contract now also enforces the starter Go package and safely composed UI query
parameters. These changes close observed governance gaps without changing the
turn cap or hidden oracle. The remaining finding is route/model reliability:
managed Qwen3.6 is not promoted, and the next Qwen test must change the native
tool-serving protocol.

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
The JSON audit also includes `next_experiment`: a deterministic action,
readiness flag, rationale, evidence codes, and the exact task/condition slice.
It rejects incomplete artifacts, repairs correctness before cost, optimizes a
measured efficiency regression, advances a clean diagnostic to five
repetitions, and advances a clean screen to ten. A versioned, source-linked
frontier envelope prevents a correct but materially more expensive challenger
from earning five paid repetitions. Non-row JSON documents fail closed as
`reject_artifact`. This closes the feedback loop without asking another model
to judge its own work.

| Weakness | Meaning | First response |
|---|---|---|
| `incomplete_evidence` / `missing_cells` | A requested result is absent or errored. | Repair infrastructure and rerun the identical grid. |
| `uneven_repetitions` / `duplicate_cells` | Compared evidence is not one matched grid. | Reject and regenerate the artifact. |
| `turn_budget_exhausted` | Work reached the bounded cap. | Inspect action targets; do not raise the cap blindly. |
| `tool_call_serialization` | The route repeatedly emits one action per turn. | Use a compatible parser or bounded composite tools. |
| `broad_reread_churn` | Unchanged files dominate reads. | Replace bodies with version receipts and active evidence. |
| `milestone_fragmentation` | Several components changed without a completed boundary. | Stage the active milestone and batch independent files. |
| `premature_text_stop` | Narration stopped before a terminal action. | Permit one bounded continuation, then fail closed. |
| `tool_continuation_failure` | A route calls a tool, then emits two empty continuations. | Verify the native protocol, change only the serving route, and rerun once. |
| `acceptance_gap` | Public checks pass but the hidden oracle fails. | Add an immutable independent boundary test. |
| `governed_failure` | A Specsmith cell failed, even without a baseline row. | Repair the measured stop reason before repetition. |
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
