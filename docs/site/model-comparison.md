# Governance Efficiency Model Comparison

## Evidence levels

| Evidence | Model/routes | Repetitions | Treatment |
|---|---|---:|---|
| [30093712102](https://github.com/layer1labs/specsmith/actions/runs/30093712102) | GPT-5.6 Sol | 5 T28 FULL | Final learning commit: 5/5, 26.5k TPCA, no audit weakness |
| [30093614453](https://github.com/layer1labs/specsmith/actions/runs/30093614453) | DeepSeek-V4 Pro + GLM-5.2 | 1 T28 FULL each | Both correct after targeted repairs; 84.4k and 73.6k TPCA, not promoted |
| [30091184259](https://github.com/layer1labs/specsmith/actions/runs/30091184259) | Seven managed frontier routes | 1 per T28 condition | Admission/trace screen; only Kimi and Qwen FULL passed |
| [30092473534](https://github.com/layer1labs/specsmith/actions/runs/30092473534) | Kimi K2.7 Code / DeepInfra | requested 5 per condition | Rejected incomplete artifact; eight router 504 cells |
| [30096516180](https://github.com/layer1labs/specsmith/actions/runs/30096516180) | Kimi K2.7 Code / Together | live probe | Account-level HTTP 403; no benchmark cell |
| [30096796977](https://github.com/layer1labs/specsmith/actions/runs/30096796977) | Kimi K2.7 Code / Novita | 1 per T28 condition | Cursor failed at 108.1k; FULL passed at 43.0k |
| [30077217017](https://github.com/layer1labs/specsmith/actions/runs/30077217017) | GPT-5.6 Sol | 5 T28 FULL | Superseded optimized envelope: 5/5, 28.3k TPCA |
| [30045327768](https://github.com/layer1labs/specsmith/actions/runs/30045327768) | GPT-5.6 Sol | 5 per T28 condition | Current matched Cursor/FULL comparator |
| [30076208564](https://github.com/layer1labs/specsmith/actions/runs/30076208564) | DeepSeek-V4 Pro / Novita | 1 FULL | Correct diagnostic; 47.9k TPCA, not promoted |
| [30074528288](https://github.com/layer1labs/specsmith/actions/runs/30074528288) | Kimi K2.7 Code / DeepInfra | 1 FULL | Correct diagnostic; 101.7k TPCA, not promoted |
| [30045980234](https://github.com/layer1labs/specsmith/actions/runs/30045980234) | GLM-5.2 / DeepInfra | 1 FULL | Correct diagnostic; 72.2k TPCA, not promoted |
| [30075176235](https://github.com/layer1labs/specsmith/actions/runs/30075176235), [30075720489](https://github.com/layer1labs/specsmith/actions/runs/30075720489) | MiniMax-M3 / Novita | 1 each | Two failed diagnostics; text-only then empty-response stops |
| [30077072490](https://github.com/layer1labs/specsmith/actions/runs/30077072490), [30077459159](https://github.com/layer1labs/specsmith/actions/runs/30077459159), [30077929145](https://github.com/layer1labs/specsmith/actions/runs/30077929145), [30078601832](https://github.com/layer1labs/specsmith/actions/runs/30078601832) | GPT-OSS-120B / DeepInfra then Novita | 1 each | Four failed provider, serialization, and completion-protocol diagnostics; rejected |
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

## July 24 open-frontier replay

All seven exact routes passed metadata and paid tool-call probes in
[workflow 30091129732](https://github.com/layer1labs/specsmith/actions/runs/30091129732).
The matched n=1 results in workflow `30091184259` are diagnostic:

| Candidate | Cursor result | FULL result | Audit decision |
|---|---:|---:|---|
| Kimi K2.7 Code / DeepInfra | fail, 42,319 | pass, 24,021 | confirm route before repetition |
| Qwen3.6-35B-A3B / DeepInfra | fail, 163,904 | pass, 62,060 | advance candidate; above envelope |
| DeepSeek-V4 Pro / Novita | fail, 21,095 | fail, 74,923 | repair explicit completion narration |
| GLM-5.2 / DeepInfra | fail, 196,733 | fail, 24,619 | repair explicit milestone narration |
| MiniMax-M3 / Novita | fail, 26,275 | fail, 56,054 | repair provider/tool continuation |
| DeepSeek-V4 Flash / DeepInfra | fail, 87,207 | fail, 130,057 | rejected at turn ceiling |
| Nemotron 3 Ultra / DeepInfra | fail, 141,608 | fail, 119,407 | rejected repeated-tool loop |

Specsmith materially improved the Qwen3.6 outcome, but 62.1k TPCA was still
2.19× the old Sol envelope and therefore did not earn n=5. The final targeted
repair run made GLM and DeepSeek Pro correct, but their 73.6k and 84.4k TPCA
also failed the efficiency envelope. MiniMax's post-repair trace wrote no files
and ended after two empty continuations; further repetition requires a new
native tool protocol or serving route.

DeepSeek V4 Flash and Nemotron completed the previous next-candidate queue and
are rejected on their measured routes. The remaining infrastructure experiment
is Qwen3-Coder-Next with the native `qwen3_coder` parser. The local 12 GB RTX
4070 cannot host the 80B checkpoint, and this repository has no configured
OpenAI-compatible endpoint secret/URL for an external native deployment, so a
managed Novita rerun would not test the requested parser.

Kimi route confirmation also completed. DeepInfra returned router HTML 504
responses in eight requested n=5 cells, Together failed its live probe with
HTTP 403, and Novita completed a matched n=1 screen. On Novita, Cursor Rules
failed after 108,137 tokens and 20 turns; FULL passed after 43,015 tokens and
10 turns. That is a substantial within-route governance improvement, but the
correct FULL cell still costs 1.62× the latest 26,499-token Sol envelope. The
audit therefore blocks n=5 rather than treating provider fallback as a reason
to waive the efficiency gate.

## Historical open-frontier admissions

Four current checkpoints were admitted through live route probes and one T28
FULL diagnostic each:

| Candidate | Pinned route | Router price / 1M input-output | Why it is useful |
|---|---|---:|---|
| [Kimi K2.7 Code](https://huggingface.co/moonshotai/Kimi-K2.7-Code) | DeepInfra | $0.74 / $3.50 | code-specialized 262K agent with explicit tool-oriented evaluation settings |
| [GLM-5.2](https://huggingface.co/zai-org/GLM-5.2) | DeepInfra | $0.93 / $3.00 | one-million-token long-horizon coding control |
| [DeepSeek-V4 Pro](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro) | Novita | $1.60 / $3.20 | 49B-active million-token reasoning/coding control |
| [MiniMax-M3](https://huggingface.co/MiniMaxAI/MiniMax-M3) | Novita | $0.30 / $1.20 | inexpensive one-million-token long-horizon challenger |

All four initial routes passed live tool-call probes in
[workflow 30045915766](https://github.com/layer1labs/specsmith/actions/runs/30045915766).

| Candidate | Correct | Tokens | Turns | Cost | Wall time | Decision |
|---|---:|---:|---:|---:|---:|---|
| DeepSeek-V4 Pro | yes | 47,855 | 7 | $0.1013 | 286.9s | strongest open challenger; above Sol envelope |
| GLM-5.2 | yes | 72,187 | 11 | $0.1015 | 376.6s | above Sol envelope |
| Kimi K2.7 Code | yes | 101,713 | 15 | $0.1326 | 552.8s | above Sol envelope |
| MiniMax-M3 | no | 53,196 | 8 | $0.0301 | 235.6s | text-only stop |
| MiniMax-M3 retry | no | 24,093 | 4 | $0.0151 | 128.1s | empty-response stop |

The three correct diagnostics passed the independent oracle, but even DeepSeek
used 69% more tokens than the then-current 28,314-token Sol+FULL envelope. The MiniMax
failures led to bounded narration recovery and fail-closed `governed_failure`
admission logic; they are not low-cost successes.

GPT-OSS-120B provided a useful provider control. DeepInfra called one file tool,
then emitted two empty continuations in
[run 30077072490](https://github.com/layer1labs/specsmith/actions/runs/30077072490).
The audit now labels this `tool_continuation_failure`. Novita resumed correctly
in [run 30077459159](https://github.com/layer1labs/specsmith/actions/runs/30077459159),
but emitted one action per turn, exhausted all 20 turns at 55,023 tokens, and
failed correctness. That trace exposed an adaptive-controller defect:
pre-enabled composite writes suppressed the later composite-read upgrade.
Composite read and write state are now independent, so a serialized route gains
bounded `read_files` after two scalar turns without enlarging Sol's initial tool
surface. The resulting
[run 30077929145](https://github.com/layer1labs/specsmith/actions/runs/30077929145)
fell to 44,692 tokens and 17 turns—18.8% fewer tokens and three fewer turns—but
the provider serialized exact `done` arguments as plain JSON after all declared
files were written. Exact-schema recovery is now permitted only after complete
write-scope evidence; deterministic public and independent checks still decide
correctness. The confirmation
[run 30078601832](https://github.com/layer1labs/specsmith/actions/runs/30078601832)
did not reach complete write scope, so recovery correctly did not activate; it
exhausted 20 turns at 49,339 tokens. The managed GPT-OSS model/route pair is
rejected.

## Next infrastructure queue

The next managed admissions should remain one-cell diagnostics:

1. **Qwen3-Coder-Next with its native `qwen3_coder` parser** — provision a
   multi-GPU or hosted OpenAI-compatible endpoint and begin with one T28 FULL
   cell; do not substitute the managed Novita route.
2. **Release-quality confirmation** — expand the winning unchanged Sol grid to
   n=10 only after the n=5 comparison is complete.

Kimi, GPT-OSS, GLM, DeepSeek, MiniMax, Flash, and Nemotron receive no further
managed-route repetitions on the measured configurations. A new attempt must
change a demonstrated serving or controller boundary and starts again at n=1.
Every candidate must beat the current Sol FULL T28 token envelope before
earning a matched n=5 screen.

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
