# Governance Efficiency Model Comparison

## Evidence levels

| Evidence | Model/routes | Repetitions | Treatment |
|---|---|---:|---|
| [29963772623](https://github.com/layer1labs/specsmith/actions/runs/29963772623) + [29963515885](https://github.com/layer1labs/specsmith/actions/runs/29963515885) | GPT-5.6 Sol | 5 per task/condition | Current eight-task matched screen |
| [29966620911](https://github.com/layer1labs/specsmith/actions/runs/29966620911) | Qwen3.6-35B-A3B / DeepInfra | 1 | Adaptive managed-route diagnostic |
| [29962883256](https://github.com/layer1labs/specsmith/actions/runs/29962883256) | Qwen3.6-35B-A3B, Qwen3-Coder-Next, Qwen3-Coder-480B-A35B | 1 | Managed-route diagnostic only |
| `29839696631`, `29942515095` | GPT-5.6 Sol | 5 | Superseded historical screens |
| `29944111036` | Qwen3.6-35B-A3B / Scaleway | 1 | Superseded route diagnostic |

Results are never combined across incompatible commits, task grids, routes, or
repetition sets. GPT-5.6 uses Chat Completions with `reasoning_effort=none` for
function-tool compatibility in every condition.

## Current frontier screen

| Condition | Correct | Tokens/correct | Cost | Mean turns |
|---|---:|---:|---:|---:|
| Cursor rules | 34/40 | 33.8k | $5.1779 | 6.38 |
| Specsmith FULL | 40/40 | 9.0k | $3.3110 | 3.40 |

The matched point estimate favors FULL on correctness, TPCA, measured cost,
turns, and wall time across all eight versioned task types. The result is a
comparison with the repository's Cursor-style rules condition; it is not a
claim about every interactive feature or future version of the commercial
Cursor product.

## Managed Qwen findings

| Route | Cursor correct | FULL correct | FULL TPCA | Serving observation |
|---|---:|---:|---:|---|
| `Qwen/Qwen3.6-35B-A3B:deepinfra` | 2/3 | 1/3 | 186.8k | best managed candidate; T2 benefited strongly, T11/T28 remained serial and slow |
| `Qwen/Qwen3-Coder-Next:novita` | 2/3 | 0/3 | undefined | lower FULL history on T28, but no correct FULL cell |
| `Qwen/Qwen3-Coder-480B-A35B-Instruct:novita` | 0/3 | 0/3 | undefined | larger active capacity did not repair tool-loop behavior |

These n=1 rows diagnose serving/model interaction; they do not rank the models.
Qwen3.6/DeepInfra took 35m23s for six cells, versus about six minutes for each
Novita model job. A low list price is therefore not a low task cost when action
turns and latency multiply.

The strongest positive Qwen receipt was T2: Qwen3.6 FULL passed in 19.3k tokens
and four turns, while Cursor passed in 65.6k tokens and ten turns. T11 exposed
the opposite boundary: Cursor passed, while FULL exhausted 12 turns after
serial reads and an unrelated-defect detour. All T28 cells failed.

The adaptive Qwen3.6 rerun changed that diagnostic from Cursor 2/3 and FULL
1/3 to Cursor 1/3 and FULL 2/3; stochastic n=1 results must not be combined as
replicates. Within the new run, FULL used 201,485 tokens (100.7k TPCA) versus
Cursor's 358,653 tokens (358.7k TPCA). FULL T11 passed in six turns after one
composite two-file write. T28 remained incorrect at the 20-turn boundary despite
all public checks passing, exposing a contract-validator and repair-direction
gap rather than evidence that more turns or a larger model would solve it.

## Which Qwen to test next

The next managed experiment is one T28-only Cursor/FULL diagnostic with
`Qwen/Qwen3.6-35B-A3B:deepinfra` after the visible shared-contract validator and
focused repair boundaries. It tests the observed failure directly at two paid
cells. The two Novita routes do not warrant repeated paid runs until their
serving behavior changes.

For a stronger open-weight tool-serving experiment, prefer one of these lanes:

1. **Qwen-native managed agent:** Qwen Code or Qwen-Agent with a current coder
   endpoint such as `qwen3-coder-plus`, keeping provider and scaffold metadata.
2. **Self-hosted coder:** Qwen3-Coder-Next through vLLM/SGLang with automatic
   tool choice and the `qwen3_coder` parser required by its model card.
3. **Capacity control:** Qwen3-Coder-480B-A35B only after the same native parser
   is proven; the Novita result shows that parameter count alone is not enough.

[Qwen3-Coder-Next](https://huggingface.co/Qwen/Qwen3-Coder-Next) is attractive
because it is an 80B-total/3B-active coding-agent model with a 256K context and
explicit long-horizon/tool recovery training. The larger
[Qwen3-Coder-480B-A35B-Instruct](https://huggingface.co/Qwen/Qwen3-Coder-480B-A35B-Instruct)
is a useful capacity control, not the default recommendation.
[Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B) remains the best
managed-HF candidate measured here.

## FP8 and base variants

The Qwen3.6 FP8 repository was not mapped to a managed Hugging Face Inference
Provider during the probe. Test it only in a separately labelled self-hosted
lane with exact hardware, quantization, runtime, parser, and sampling metadata.
A base model is not the preferred tool agent without post-training or an agent
scaffold; compare it as a scientific control, not as the expected winner.

## Recommended comparison set

- GPT-5.6 Sol: frontier efficacy and current repeated anchor.
- A current smaller OpenAI model: degradation and price sensitivity, never as a
  proxy for frontier behavior.
- Qwen3.6/DeepInfra: managed open-weight portability after adaptive tools.
- Qwen3-Coder-Next/native parser: self-hosted or Qwen-native tool-serving lane.

Promote a route from n=1 to n=5 only after it produces correct cells. Use n=10
before a release-quality statistical claim. Preserve raw token, cost, latency,
sampling, parser, and provider receipts so a serving change is not mistaken for
a model-quality change.

## Failure provenance

Unavailable routing, incompatible function-tool settings, cancelled jobs,
provider errors, and incomplete artifacts remain in provenance but never enter
a leaderboard denominator. This is especially important for open-weight models:
the model checkpoint, chat template, tool parser, quantization, and host can each
change the result.
