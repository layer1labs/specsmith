# Governance Efficiency Model Comparison

## Current evidence levels

| Evidence | Models | Repetitions | Status |
|---|---|---:|---|
| [Frontier screen 29839696631](https://github.com/layer1labs/specsmith/actions/runs/29839696631) | `gpt-5.6-sol` | 5 | Complete screening evidence |
| [Route/model diagnostic 29834732303](https://github.com/layer1labs/specsmith/actions/runs/29834732303) | GPT-5.6 Sol, GPT-4o-mini, Qwen3.6-35B-A3B | 1 | Complete diagnostic evidence only |

All runs used the same seven tasks and the same four conditions: raw,
Cursor rules, Specsmith LIGHT, and Specsmith FULL. GPT-5.6 Sol used Chat
Completions with `reasoning_effort=none` for function-tool compatibility,
uniformly across conditions.

## Five-repetition frontier result

| Condition | Pass rate | TPCA | Conservative list cost/pass |
|---|---:|---:|---:|
| Specsmith FULL | 91% | 21.7k | $0.1508 |
| Specsmith LIGHT | 94% | 21.8k | $0.1502 |
| Ungoverned | 86% | 25.4k | $0.1724 |
| Cursor rules | 83% | 32.3k | $0.2124 |

These mixed-suite point estimates favor Specsmith, but confidence intervals
overlap. Coding-only correctness favored raw GPT-5.6 Sol: raw passed 25/25,
Cursor 24/25, LIGHT 23/25, and FULL 22/25. See the
[full benchmark report](efficiency-benchmark.md) for the task-level explanation.

The historical dollar estimates omit cached-input discounts because the run did
not capture GPT-5.6 cache-write tokens. They are retained for provenance, not as
billing records; TPCA is the primary cross-provider comparison.

## Diagnostic model behavior

| Model | Main observation |
|---|---|
| `gpt-5.6-sol` | Strongest overall correctness and the only model advanced to n=5 screening. |
| `gpt-4o-mini` | FULL improved n=1 correctness over raw, but Cursor had lower TPCA; useful as a degradation test, not a frontier proxy. |
| `Qwen/Qwen3.6-35B-A3B:scaleway` | Complete but slow and weak on coding cells; retain as a separate open-weight lane. |

The diagnostics demonstrate that governance lift is model-dependent. They do
not justify combining n=1 model rows into a cross-model ranking.

## Qwen FP8 and base variants

`Qwen/Qwen3.6-35B-A3B:scaleway` is the current managed, tool-capable Hugging
Face route. `Qwen/Qwen3.6-35B-A3B-FP8` has no managed Inference Provider mapping
at the time of this run. FP8 or base-model testing therefore belongs in a
self-hosted vLLM/compatible lane with its own hardware, quantization, and
serving metadata; mixing it into the managed API table would confound model and
infrastructure effects.

## Recommended comparison set

- Frontier efficacy: GPT-5.6 Sol.
- Cost/degradation: a current smaller OpenAI model, with no assumption that it
  represents frontier behavior.
- Open-weight portability: Qwen3.6 in a separately timed managed or self-hosted
  lane.
- Framework breadth: run all twelve scaffolding conditions only after the core
  raw/Cursor/LIGHT/FULL screen is stable at ten repetitions.

Future reports must use complete identical cell sets and state their evidence
level. Five repetitions support screening observations; ten are required for a
release-quality claim.

## Route and failure provenance

Provider and harness failures are reported separately from model quality. Runs
`29826896259`, `29827597006`, `29827805536`, and `29829542051` were invalidated
by unavailable routing, request compatibility, or artifact errors. Run
`29832926861` was cancelled before the Qwen lane completed. None contributes a
leaderboard row or denominator. This distinction matters especially for hosted
open-weight models, where routing and serving latency can otherwise be mistaken
for model capability.
