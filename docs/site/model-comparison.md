# Governance Efficiency Model Comparison

## Evidence levels

| Evidence | Model/routes | Repetitions | Treatment |
|---|---|---:|---|
| [29963772623](https://github.com/layer1labs/specsmith/actions/runs/29963772623) + [29963515885](https://github.com/layer1labs/specsmith/actions/runs/29963515885) | GPT-5.6 Sol | 5 per task/condition | Current eight-task matched screen |
| [30010219286](https://github.com/layer1labs/specsmith/actions/runs/30010219286), [30011743699](https://github.com/layer1labs/specsmith/actions/runs/30011743699), [30013020354](https://github.com/layer1labs/specsmith/actions/runs/30013020354) | Qwen3.6-35B-A3B / DeepInfra | 1 each | Trace-driven T28 diagnostics; never combined |
| [30007255204](https://github.com/layer1labs/specsmith/actions/runs/30007255204), [30007554143](https://github.com/layer1labs/specsmith/actions/runs/30007554143) | Qwen3-Coder-Next / Novita | 1 each | Provider/tool-route admission failures |
| [29969671380](https://github.com/layer1labs/specsmith/actions/runs/29969671380) | Qwen3.6-35B-A3B / DeepInfra | 1 | T28 contract-repair diagnostic |
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

The contract-repair T28 run then failed both conditions. Cursor used 183.1k
tokens and passed 4/5 hidden checks. FULL used 203.2k tokens over 891.3 seconds,
implemented every declared file, and passed the hidden oracle 5/5, but one Ruff
`I001` remained after the last write. Turns 15–20 were unchanged rereads. The
visible contract and milestone decomposition therefore improved substantive
coverage but did not make this serving route efficient or reliable.

## July 23 admission decision

| Workflow | Correct | Tokens | Public evidence | Independent evidence |
|---|---:|---:|---|---|
| [30010219286](https://github.com/layer1labs/specsmith/actions/runs/30010219286) | yes | 180,895 | passed | hidden oracle 5/5 |
| [30011743699](https://github.com/layer1labs/specsmith/actions/runs/30011743699) | no | 136,360 | passed | hidden oracle failed |
| [30013020354](https://github.com/layer1labs/specsmith/actions/runs/30013020354) | no | 151,666 | self-authored tests and Ruff failed | hidden oracle 5/5 |

The token controls materially reduced some traces but did not produce repeatable
correctness. All three used 20 turns. The one correct cell was 8.8× GPT-5.6 Sol
FULL's current 20.6k T28 TPCA, so managed Qwen3.6 is rejected for an n=5 screen.
The Qwen3-Coder-Next/Novita experiments also failed admission: `30007255204`
returned HTTP 400 before the first action, while `30007554143` wrote no files in
58,149 tokens. Neither demonstrates the native parser.

## Which Qwen to test next

No further managed Qwen repetition is earned. The next experiment must change
the serving/tool protocol: Qwen3-Coder-Next behind the native `qwen3_coder`
parser, with one T28 FULL cell as the admission test. It advances to a matched
Cursor/FULL n=5 screen only after that cell is correct and materially better on
tokens and wall time. The Novita OpenAI-compatible route is not a substitute for
this experiment because its trace did not demonstrate native multi-tool
semantics.

For a stronger open-weight tool-serving experiment, prefer one of these lanes:

1. **Qwen-native managed agent:** Qwen Code or Qwen-Agent with a current coder
   endpoint such as `qwen3-coder-plus`, keeping provider and scaffold metadata.
2. **Self-hosted coder:** Qwen3-Coder-Next through vLLM/SGLang with automatic
   tool choice and the `qwen3_coder` parser required by its model card.
3. **Capacity control:** Qwen3-Coder-480B-A35B only after the same native parser
   is proven; the Novita result shows that parameter count alone is not enough.

The self-hosted admission experiment is intentionally one cell:

```bash
vllm serve Qwen/Qwen3-Coder-Next \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder

export BENCH_OPENAI_BASE_URL=http://127.0.0.1:8000/v1
export BENCH_OPENAI_COMPAT_API_KEY=local
export PYTHONPATH=scripts
python -m govern_bench.run_bench \
  --provider openai-compat \
  --model Qwen/Qwen3-Coder-Next \
  --task T28 \
  --condition SPECSMITH_FULL \
  --reps 1 \
  --json-output qwen-coder-next-native-t28.json
```

Record the runtime, parser, model revision, quantization, hardware, sampling,
and endpoint metadata with the artifact. Without those fields, the result is a
generic OpenAI-compatible route test rather than evidence about native Qwen tool
serving.

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

## Open-frontier admission queue

Four additional current checkpoints are registered in the `open-frontier`
group. Their routes were selected from live Hugging Face router metadata on
2026-07-23; the workflow still requires a paid tool-call probe before any
benchmark cell:

| Candidate | Pinned route | Router price / 1M input-output | Why it is useful |
|---|---|---:|---|
| [Kimi K2.7 Code](https://huggingface.co/moonshotai/Kimi-K2.7-Code) | DeepInfra | $0.74 / $3.50 | code-specialized 262K agent with explicit tool-oriented evaluation settings |
| [GLM-5.2](https://huggingface.co/zai-org/GLM-5.2) | DeepInfra | $0.93 / $3.00 | one-million-token long-horizon coding control |
| [DeepSeek-V4 Pro](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro) | Novita | $1.60 / $3.20 | 49B-active million-token reasoning/coding control |
| [MiniMax-M3](https://huggingface.co/MiniMaxAI/MiniMax-M3) | Novita | $0.30 / $1.20 | inexpensive one-million-token long-horizon challenger |

The next paid open-model experiment is GLM-5.2 on T28 FULL at n=1, because it
changes both model family and tool-serving implementation while directly
targeting the serial long-horizon failure seen with managed Qwen. Kimi K2.7
Code is the code-specialized follow-up; MiniMax-M3 is the cost challenger; and
DeepSeek-V4 Pro is the higher-active-capacity control. Probe failure rejects a
route before the matrix. A correct diagnostic must also beat the current Sol
FULL T28 token envelope before earning a matched n=5 screen.

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
