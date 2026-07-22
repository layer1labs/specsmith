# Specsmith Governance Efficiency Benchmark

**Latest screening run:** 2026-07-21

**Workflow:** [GovernanceBench run 29839696631](https://github.com/layer1labs/specsmith/actions/runs/29839696631)

**Commit:** `114e3a5961b84d58d13c82ad8323864070061dd2`

**Model:** `gpt-5.6-sol`

**Compatibility mode:** Chat Completions with `reasoning_effort=none` for every condition

**Tasks:** T1, T2, T6, T7, T10, T11, T13

**Conditions:** UNGOVERNED, CURSOR_RULES, SPECSMITH_LIGHT, SPECSMITH_FULL

**Repetitions:** 5 per task/condition; 140 valid cells

!!! success "Complete matched screen"
    Every requested cell completed with no skipped or provider-error rows.
    Project Ruff and pytest checks ran before evaluator injection. Each hidden
    acceptance oracle then ran exactly once in isolation.

## Mixed-suite screening result

The primary metric is tokens per correct answer (TPCA): mean tokens divided by
pass rate. Estimated cost-of-pass is secondary because provider prices change.

| Condition | Pass rate (95% CI) | Mean tokens | TPCA | Conservative list cost | List cost/pass (95% CI) |
|---|---:|---:|---:|---:|---:|
| Ungoverned | 86% (71%–94%) | 21.8k | 25.4k | $0.1478 | $0.1724 ($0.1466–$0.1977) |
| Cursor rules | 83% (67%–92%) | 26.8k | 32.3k | $0.1760 | $0.2124 ($0.1728–$0.2615) |
| Specsmith LIGHT | 94% (81%–98%) | 20.6k | 21.8k | $0.1417 | $0.1502 ($0.1123–$0.1947) |
| Specsmith FULL | 91% (78%–97%) | 19.9k | 21.7k | $0.1379 | $0.1508 ($0.1155–$0.1931) |

Point estimates favor both Specsmith conditions on the mixed suite. FULL used
14.6% fewer tokens per correct answer than ungoverned and 32.9% fewer than
Cursor rules. LIGHT had the highest observed pass rate. The confidence
intervals overlap, so this is a screening observation, not proof of a universal
or statistically separated advantage.

The dollar values above are conservative historical estimates that price every
input token at the normal list rate. The artifact contains `cached_input_tokens`
but not GPT-5.6 `cache_write_tokens`, so exact cached billing cannot be
reconstructed after the fact. This does not change raw token counts, pass rates,
or TPCA. The corrected harness records cache reads and writes independently and
uses the model's cached-input and cache-write rates for future reports.

## Long-horizon screen

The separate T28 polyglot slice now has matched five-repetition screening
evidence. In
[run 29942515095](https://github.com/layer1labs/specsmith/actions/runs/29942515095),
GPT-5.6 Sol passed all five hidden oracles under both Cursor rules and Specsmith
FULL. Cursor used 56.3k tokens/correct and $0.3187/pass; FULL used 71.4k and
$0.3813. FULL therefore did not demonstrate a token-efficiency advantage on
this slice.

FULL nevertheless improved 15.6% from the prior 84.6k-token matched screen
after internal governance files were removed from model context, missing
validators moved into the deterministic completion gate, and obsolete
full-file reads were compacted from protocol-valid history after replacement.
The current audit found no weaknesses. One FULL repetition incurred 127.0k
tokens when independent verification caught a real acceptance gap and forced a
successful repair; it is retained in TPCA and cost/pass. See the
[long-horizon benchmark and weakness audit](benchmark-audit.md) for rep-level
evidence and limitations.

The same corrected harness was probed through the managed Hugging Face
Qwen3.6-35B-A3B route in
[run 29944111036](https://github.com/layer1labs/specsmith/actions/runs/29944111036).
Both Cursor and FULL failed at the 20-turn ceiling (230.8k and 236.9k tokens),
so neither has finite TPCA. The valid but incorrect diagnostic was not repeated.

## Where the tokens went

Output was nearly flat across conditions; accumulated input history explains
almost all of the spread. Each row averages 35 task repetitions, and cached
input is a subset of input rather than an additional token count.

| Condition | Mean input | Mean output | Mean cached input | Mean LLM turns |
|---|---:|---:|---:|---:|
| Ungoverned | 20.2k | 1.55k | 18.2k | 4.97 |
| Cursor rules | 25.1k | 1.68k | 22.8k | 5.40 |
| Specsmith LIGHT | 19.0k | 1.56k | 17.2k | 4.17 |
| Specsmith FULL | 18.3k | 1.55k | 16.6k | 3.97 |

Traces in all four conditions also showed agents reading files whose bodies the
harness had already preloaded. Because prior messages remain in later requests,
that duplication was paid repeatedly. This is why the first implementation
change is just-in-time file retrieval, not shorter model answers: mean output
varied by only 0.13k tokens while mean input varied by 6.8k.

## Coding-only result

T6 is an ambiguous request and T7 is destructive; deterministic preflight can
correctly stop them before an LLM call. Removing those two governance tasks
shows the coding result separately.

| Condition | Coding passes | Pass rate | Mean tokens | TPCA | Cost/pass |
|---|---:|---:|---:|---:|---:|
| Ungoverned | 25/25 | 100% | 28.3k | 28.3k | $0.1944 |
| Cursor rules | 24/25 | 96% | 34.1k | 35.6k | $0.2370 |
| Specsmith LIGHT | 23/25 | 92% | 28.8k | 31.3k | $0.2156 |
| Specsmith FULL | 22/25 | 88% | 27.8k | 31.6k | $0.2194 |

The current evidence does **not** show a coding-correctness advantage. Raw
GPT-5.6 Sol passed every coding cell. Specsmith used fewer tokens per correct
answer than Cursor rules, but with lower coding pass rates. The aggregate win
comes from avoiding unnecessary model calls and unsafe action on governance
tasks.

## Task-level findings

- T6: raw and Cursor failed all five ambiguity checks; LIGHT and FULL stopped
  correctly with zero model tokens.
- T7: all conditions behaved safely, but LIGHT and FULL used zero model tokens
  versus 6.6k for raw and 12.3k for Cursor.
- T2 and T11: all conditions passed. FULL used 32.2k and 29.3k mean tokens,
  respectively, versus Cursor's 48.8k and 38.0k.
- T1 and T13: all conditions passed; raw was cheapest on T1 and Cursor was
  cheapest on T13.
- T10: raw passed 5/5, Cursor 4/5, LIGHT 3/5, and FULL 2/5. The failed governed
  implementations counted priorities correctly in the new endpoint but did
  not repair the existing POST data path that discarded submitted priority.
  Their self-authored public tests missed that boundary; the hidden oracle
  caught it.

T10 is the most important improvement signal. More prompt scaffolding is not
the answer. Specsmith needs stronger linked acceptance-test enforcement across
existing data-flow boundaries while keeping the context contract compact.

## Model diagnostics

[Run 29834732303](https://github.com/layer1labs/specsmith/actions/runs/29834732303)
executed one repetition per cell on three models. These rows validate routes and
reveal model dependence; n=1 does not support superiority claims.

| Model / condition | Raw | Cursor | LIGHT | FULL |
|---|---:|---:|---:|---:|
| GPT-5.6 Sol pass / TPCA | 6/7 / 27.0k | 5/7 / 31.1k | 6/7 / 21.4k | 7/7 / 23.9k |
| GPT-4o-mini pass / TPCA | 3/7 / 59.9k | 4/7 / 34.1k | 3/7 / 67.2k | 5/7 / 38.5k |
| Qwen3.6-35B-A3B pass / TPCA | 2/7 / 175.9k | 1/7 / 442.9k | 2/7 / 157.7k | 2/7 / 170.3k |

The managed Qwen Scaleway route produced complete, billable results but was not
competitive on this tool-driven suite: most coding cells failed lint or tests,
and the 28-cell job took about one hour (128 seconds mean wall time per cell).
The FP8 repository has no managed Hugging Face provider mapping and should be
evaluated separately in a controlled self-hosted lane.

## Product and benchmark recommendations

1. Keep LIGHT as the default low-overhead path. Use FULL when a project has
   trustworthy linked acceptance tests that can drive repair.
2. Invest in requirement-to-independent-test enforcement and boundary-aware
   context, not a larger generic skill catalog or longer prompts.
3. Keep GPT-5.6 Sol as the frontier anchor. Retain a small model for degradation
   testing and Qwen as a separate open-weight lane with explicit time budgets.
4. Run ten repetitions before a release-quality claim. Expand to all twelve
   scaffolding conditions only after the core four-condition signal is stable.

## Benchmark-driven optimization loop

GovernanceBench is now a product feedback loop, not a marketing snapshot:

1. Run the core matched screen and fail closed if any cell is missing or has a
   provider error.
2. Separate deterministic governance tasks from coding tasks. Optimize mixed
   TPCA without hiding coding-correctness regressions.
3. Inspect task-level failures, token components, repair turns, and wall time.
   Convert a reproducible product failure into a linked requirement and an
   independent regression test.
4. Prefer the smallest deterministic intervention that improves the failed
   task: reject ambiguity before an LLM call, retrieve only relevant evidence,
   or run the linked acceptance test. Do not lengthen every prompt to fix one
   task.
5. Re-run the affected cells first, then the complete matched screen. Publish a
   new result only when correctness is preserved or improved and TPCA falls.

The immediate optimization target is T10. Specsmith should expose a compact
requirement-to-boundary context and enforce an independent test covering the
existing write path before accepting completion. LIGHT remains the default
until FULL demonstrates that its extra repair loop earns its token cost.

## Research-backed implementation priorities

The trace data and primary research converge on a small set of changes:

- **Retrieve code just in time.** Every condition re-read files that the old
  harness eagerly injected, so repeated input history dominated spend. The
  harness now sends the file index by default and lets the agent retrieve only
  relevant bodies. This follows Anthropic's
  [progressive-disclosure guidance](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
  and the localization-first result in
  [Agentless](https://arxiv.org/abs/2407.01489).
- **Make the independent test legible and immutable.** Preflight now emits a
  bounded AEE context contract with linked test commands and instructs the host
  agent not to edit those tests. This directly addresses T10's public-boundary
  miss and the low-coverage-test risk identified in OpenAI's
  [coding-evaluation audit](https://openai.com/index/separating-signal-from-noise-coding-evaluations/).
- **Preserve active evidence, not bulk history.** Grace now prioritizes active
  preflight/verification evidence, caps resumed chat at six turns, and uses a
  6,000-character seed. Longer sessions can use state-preserving compaction;
  both [OpenAI](https://developers.openai.com/api/docs/guides/compaction) and
  Anthropic recommend compacting redundant tool output while retaining
  unresolved state.
- **Measure caching instead of assuming it.** GPT-5.6 requests now use a stable
  prompt cache key and record cache reads/writes. OpenAI requires exact reusable
  prefixes for cache hits and recommends placing stable content first in its
  [prompt-caching guide](https://developers.openai.com/api/docs/guides/prompt-caching).
- **Route models only from local evidence.** The diagnostic showed that neither
  the small OpenAI model nor managed Qwen was a safe default for coding. A
  learned cascade remains promising—see
  [RouteLLM](https://arxiv.org/abs/2406.18665) and
  [FrugalGPT](https://arxiv.org/abs/2305.05176)—but Specsmith should enable it
  only after enough per-task outcomes exist to bound regression risk.

Prompt compression such as
[LLMLingua-2](https://arxiv.org/abs/2403.12968) is a candidate for long prose
and tool output, not source code, JSON, test commands, or provenance IDs. It
must earn adoption in an ablation because semantic-looking compression can
still discard a boundary-critical fact. The same caution follows the
[lost-in-the-middle](https://arxiv.org/abs/2307.03172) result: more context is
not automatically more usable context.

## Coverage priorities

The post-change Windows validation collected 2,328 tests: 2,314 passed, nine
were skipped, and five expected failures remained expected. Application line
coverage was 52%. A separate GovernanceBench measurement was 38% overall;
its pricing module reached 86%, but the orchestration harness was 33%.

The new regressions cover the paths implicated by this run: bounded preflight
contracts, trace-ID retention under compression, active-evidence priority,
resumed-history caps, just-in-time file retrieval, cached-read/write pricing,
and OpenAI cache telemetry. The CI coverage command now includes
`govern_bench`, so harness coverage cannot remain invisible behind the
application-only number.

Next coverage work should follow risk, not inflate a repository-wide number:

1. Add provider-response fixtures and failure injection around benchmark
   orchestration, artifact completeness, retries, and resume behavior.
2. Exercise the requirement/retrieval boundary and verification failure paths;
   those modules currently have materially less coverage than the pricing and
   condition registries.
3. Split optional GUI, one-time migrations, and legacy compatibility code from
   the mission-core coverage view. Either test those surfaces intentionally or
   remove them; uncovered dormant code should not dilute the signal used to
   release the governance core.

## Excluded and diagnostic attempts

Failed attempts are evidence about the harness, but not benchmark results:

| Workflow run | Outcome | Publication treatment |
|---|---|---|
| `29826896259` | Requested Hugging Face route was not offered by the provider. | Excluded; no model comparison. |
| `29827597006`, `29827805536` | GPT-5.6 Sol rejected function tools with the requested reasoning setting. | Excluded; compatibility fixed by applying `reasoning_effort=none` uniformly. |
| `29829542051` | Artifact handling raised `[Errno 21] Is a directory`, leaving incomplete cells. | Excluded; fail-closed comparison correctly refused. |
| `29832926861` | Run was cancelled while the slow Qwen lane was still executing. | Excluded; partial model outputs are not combined. |

This provenance prevents an incomplete or selectively successful run from being
mistaken for the complete 140-cell screen.

## Integrity protocol

The harness fails closed on missing or errored cells, enforces identical matched
cell sets, isolates every project fixture, disables pytest/Ruff caches, excludes
evaluator files from diffs, and requires hidden outcome oracles for standard
coding tasks. `SPECSMITH_FULL` must pass Ruff and project pytest after its latest
write before `done` is accepted; repair turns and tokens remain charged to FULL.

See the versioned
[`METHODOLOGY.md`](https://github.com/layer1labs/specsmith/blob/develop/scripts/govern_bench/METHODOLOGY.md)
for statistical definitions and publication rules.
