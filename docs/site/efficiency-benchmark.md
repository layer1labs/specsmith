# Specsmith Governance Efficiency Benchmark

## Current matched screen

The current screening evidence uses `gpt-5.6-sol`, Chat Completions with
`reasoning_effort=none`, and commit `f474bb6b772fe71fd7f1b20d585e23b15fec746a`.
It compares Cursor-style rules with Specsmith FULL across eight task types and
five repetitions per cell.

- [T1, T6, T7, T13 workflow 29963772623](https://github.com/layer1labs/specsmith/actions/runs/29963772623)
- [T2, T10, T11, T28 workflow 29963515885](https://github.com/layer1labs/specsmith/actions/runs/29963515885)

The workflows are complete, non-overlapping slices of the same model, commit,
conditions, compatibility settings, and repetition count. Together they contain
80 valid rows and no provider-error or skipped cells.

| Condition | Correct | Pass rate | Total tokens | Mean tokens | Tokens/correct | Cost | Mean turns | Wall time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Cursor rules | 34/40 | 85% | 1,148,565 | 28,714 | 33,781 | $5.1779 | 6.38 | 1,217.8s |
| Specsmith FULL | 40/40 | 100% | 360,662 | 9,017 | 9,017 | $3.3110 | 3.40 | 1,005.7s |

On this versioned suite, FULL produced six more correct answers, reduced tokens
per correct answer by 73.3%, reduced measured provider cost by 36.1%, and
reduced wall time by 17.4%. This is a strong matched screening result, not a
universal claim about every model, repository, or Cursor configuration.

## Task-level results

Tokens per correct answer (TPCA) retains the cost of failed attempts. A zero-pass
cell has no finite TPCA and is never silently excluded.

| Task | Task type | Cursor correct / TPCA | FULL correct / TPCA | FULL change |
|---|---|---:|---:|---:|
| T1 | Feature addition | 5/5 / 24.5k | 5/5 / 11.1k | 54.6% lower |
| T2 | Bug repair | 4/5 / 57.8k | 5/5 / 6.5k | 88.8% lower, +1 correct |
| T6 | Ambiguity gate | 0/5 / undefined | 5/5 / 0 | safe deterministic stop |
| T7 | Destructive kill switch | 5/5 / 9.4k | 5/5 / 0 | safe deterministic stop |
| T10 | API/data-flow extension | 5/5 / 36.3k | 5/5 / 13.0k | 64.1% lower |
| T11 | Schema propagation | 5/5 / 32.1k | 5/5 / 8.2k | 74.3% lower |
| T13 | CLI extension | 5/5 / 22.3k | 5/5 / 12.7k | 43.1% lower |
| T28 | Polyglot long horizon | 5/5 / 57.3k | 5/5 / 20.6k | 64.1% lower |

The post-run audit found no high or critical FULL weakness. One successful T28
FULL row used 12 turns versus a six-turn median because deterministic validation
caught a backend boundary and forced repair; its full 30.1k-token cost remains
in the aggregate. Cursor findings included one T2 turn-budget exhaustion,
unchanged reread churn, context dominance, and edits outside declared boundaries.

## Latest T28 replication

[Workflow 30045327768](https://github.com/layer1labs/specsmith/actions/runs/30045327768)
is a newer, non-combined T28-only screen at commit `5790d419`. Both conditions
passed 5/5 and passed the evaluator-isolated oracle.

| Condition | Correct | Tokens/correct | Mean cost | Mean turns | Mean wall time |
|---|---:|---:|---:|---:|---:|
| Cursor rules | 5/5 | 69.1k | $0.3568 | 10.8 | 88.9s |
| Specsmith FULL | 5/5 | 32.0k | $0.2640 | 11.4 | 86.6s |

FULL used 53.6% fewer tokens per correct answer and 26.0% lower measured cost.
This screen supplies the versioned T28 frontier envelope used to decide whether
a correct challenger deserves repeated paid runs.

## What changed the result

The improvement came from making governance smaller and more deterministic:

- accepted work starts with only read, write, and done tools;
- requirement-linked change boundaries replace broad repository exploration;
- file bodies are retrieved just in time and unchanged rereads become digest
  receipts;
- completed write bodies and superseded reads leave active provider history;
- validators run outside the model token path and return focused failures;
- long-horizon work receives controller-owned milestone progress without a
  separate planning turn; and
- tool surfaces expand only after a validation failure.

The next adaptive layer observes serving behavior rather than model branding.
After two one-action turns, FULL adds bounded `read_files`/`write_files`
operations (maximum 12 paths) and asks the route to batch the active boundary.
Scalar definitions remain available because some OpenAI-compatible routes keep
selecting a tool advertised earlier in the conversation. Completion may also
run one Ruff default-safe-fix pass before completion or final scoring. Public
task validators run before the hidden oracle, which is executed exactly once
after the agent stops and never supplies repair content.

## Qwen route diagnostic

[Workflow 29962883256](https://github.com/layer1labs/specsmith/actions/runs/29962883256)
ran T2, T11, and T28 once under Cursor rules and FULL. These are diagnostic
receipts only; none was advanced to n=5.

| Managed route | Cursor correct | FULL correct | Main finding |
|---|---:|---:|---|
| `Qwen/Qwen3.6-35B-A3B:deepinfra` | 2/3 | 1/3 | FULL T2: 19.3k vs Cursor 65.6k; T11/T28 exhausted turns; six cells took 35m23s |
| `Qwen/Qwen3-Coder-Next:novita` | 2/3 | 0/3 | Lower FULL tokens on T28, but serial repair and an acceptance gap prevented correctness |
| `Qwen/Qwen3-Coder-480B-A35B-Instruct:novita` | 0/3 | 0/3 | Larger active capacity did not overcome serial actions or incomplete T28 boundaries |

The evidence rejects “use the largest Qwen” as the next move. A focused
[Qwen3.6/DeepInfra adaptive rerun 29966620911](https://github.com/layer1labs/specsmith/actions/runs/29966620911)
then produced these n=1 results on the same T2/T11/T28 task set:

| Condition | Correct | Total tokens | Tokens/correct | Main finding |
|---|---:|---:|---:|---|
| Cursor rules | 1/3 | 358,653 | 358,653 | T11 passed; T2 and T28 failed |
| Specsmith FULL | 2/3 | 201,485 | 100,743 | T2/T11 passed; T28 failed |

Relative to the first Qwen3.6 diagnostic, adaptive FULL improved from 1/3 to
2/3 and reduced TPCA by 46.1%. T11 is the clearest causal trace: after two
scalar turns, the route used one composite write for the implementation and
test and passed in six turns. T28 wrote every declared file and passed its
public project checks, but the hidden oracle rejected an omitted required schema
field and generic Playwright locators. This public-test/oracle disagreement
motivated a visible contract validator and validator-to-file repair boundaries;
it did not justify a larger turn cap or n=5 promotion.

The focused [T28 contract-repair run 29969671380](https://github.com/layer1labs/specsmith/actions/runs/29969671380)
did not produce a correct cell:

| Condition | Correct | Tokens | Wall time | Final evidence |
|---|---:|---:|---:|---|
| Cursor rules | 0/1 | 183,061 | 354.5s | project tests passed; hidden oracle 4/5 |
| Specsmith FULL | 0/1 | 203,217 | 891.3s | project tests 10/10 and hidden oracle 5/5; final Ruff `I001` remained |

The visible contract validator repaired the former acceptance gap, but the
route's action policy remained inefficient. July 23 trace-driven experiments
then tested progressively stricter controller behavior:

| Workflow | Route / cell | Correct | Tokens | Turns | Evidence |
|---|---|---:|---:|---:|---|
| [30007255204](https://github.com/layer1labs/specsmith/actions/runs/30007255204) | Coder-Next/Novita, T28 FULL | no result | — | 0 | provider HTTP 400 before a model action |
| [30007554143](https://github.com/layer1labs/specsmith/actions/runs/30007554143) | Coder-Next/Novita, T2 FULL | no | 58,149 | 12 | no files written; route did not follow the advertised tool surface |
| [30009178814](https://github.com/layer1labs/specsmith/actions/runs/30009178814) | Qwen3.6/DeepInfra, T28 FULL | no | 107,749 | 20 | only five boundaries written; broad reread churn |
| [30010219286](https://github.com/layer1labs/specsmith/actions/runs/30010219286) | Qwen3.6/DeepInfra, T28 FULL | yes | 180,895 | 20 | all ten files, clean public checks, hidden oracle 5/5 |
| [30011743699](https://github.com/layer1labs/specsmith/actions/runs/30011743699) | Qwen3.6/DeepInfra, T28 FULL | no | 136,360 | 20 | 24.6% fewer tokens than the correct cell, but independent oracle failed |
| [30013020354](https://github.com/layer1labs/specsmith/actions/runs/30013020354) | Qwen3.6/DeepInfra, T28 FULL | no | 151,666 | 20 | hidden oracle 5/5; self-authored public tests and Ruff failed |

The sequence isolated and fixed real scaffold weaknesses: completed writes now
become digest evidence, known file absence is versioned, reads are suspended
when the next declared boundary is already known, repair writes return directly
to controller validation, and public T28 validators cover Go package and query
composition boundaries. Those changes reduced redundant context without
weakening the hidden oracle. They did not make the managed model reliable: only
one of three recent Qwen3.6 cells was correct, all reached the turn ceiling, and
the correct cell used 8.8× GPT-5.6 Sol FULL's 20.6k T28 TPCA.

No managed Qwen result is promoted to n=5. A stronger infrastructure experiment
is Qwen3-Coder-Next behind its native `qwen3_coder` parser in vLLM/SGLang or
Qwen Code/Qwen-Agent, where multi-step tool semantics are part of the serving
stack. The Novita runs are managed OpenAI-compatible route evidence, not native
parser evidence. The official model cards are
[Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B),
[Qwen3-Coder-Next](https://huggingface.co/Qwen/Qwen3-Coder-Next), and
[Qwen3-Coder-480B-A35B-Instruct](https://huggingface.co/Qwen/Qwen3-Coder-480B-A35B-Instruct).

The `Qwen3.6-35B-A3B-FP8` repository was not offered by a managed Hugging Face
Inference Provider during these probes. FP8 or a base model therefore belongs
in a separately labelled self-hosted lane; combining it with managed routes
would confound model quality, quantization, parser, and serving hardware.

## Benchmark-driven optimization loop

1. Run one matched diagnostic and fail closed on provider errors or missing
   cells.
2. Audit correctness, TPCA, turns, rereads, scope expansion, milestone progress,
   and public-test/oracle disagreement.
3. Convert a reproducible weakness into a linked requirement and independent
   regression test.
4. Change the smallest implicated controller or context boundary; do not raise
   turn caps or weaken the oracle.
5. Rerun affected cells, then the complete matched slice. Advance to n=5 only
   after diagnostic correctness; use n=10 for release-quality statistical claims.

## Integrity and limitations

Every cell uses a disposable project and isolated governance state. Project
Ruff and pytest run before evaluator injection; the hidden acceptance oracle
runs once in isolation. Raw rows retain call-level token/cache usage, costs,
turns, stop reason, content-free tool targets, diffs, validator output, and
controller decisions. Comparisons reject missing, duplicate, uneven, errored,
or incompatible cells.

The current screen compares the repository's versioned Cursor-style condition,
not every feature of the commercial Cursor product. Prices and hosted latency
can change; raw correctness and token receipts are the more portable evidence.
See the [statistical methodology](https://github.com/layer1labs/specsmith/blob/develop/scripts/govern_bench/METHODOLOGY.md),
[model comparison](model-comparison.md), and
[long-horizon weakness audit](benchmark-audit.md).

## Historical provenance

Earlier screens remain available for regression history, but their headline
numbers are superseded by the current commit. Runs with unavailable routes,
tool incompatibility, incomplete artifacts, or cancelled model lanes never
enter a published denominator. In particular, workflow `29942515095` measured
T28 before adaptive change maps and milestone compression; workflow
`29944111036` measured an earlier Qwen3.6 serving configuration. They are not
combined with the current 80-row screen.
