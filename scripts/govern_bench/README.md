# govern_bench — GovernanceBench (specsmith)

GovernanceBench measures how governance/scaffolding changes **cost, quality, and safety**
across coding-agent workflows.

> Status: the 2026-07-18 GPT-4o-mini run is complete and published with
> limitations. The paired Qwen run is incomplete and excluded from comparative
> claims. See `docs/site/efficiency-benchmark.md`.

---

## Quick Start

```bash
# Install dependencies
pip install pyyaml

# List all tasks and conditions
python -m govern_bench.run_bench --list

# Dry-run (deterministic dummy data, useful for CI and report plumbing)
python -m govern_bench.run_bench --dry-run --reps 5

# Run governance-gate tasks only (T6 + T7)
python -m govern_bench.run_bench --task T6 --task T7 --dry-run

# Real benchmark run (provider/model wiring required)
python -m govern_bench.run_bench --reps 5 --model claude-sonnet-4-5
```

---

## Benchmark Scope

### 12 governance conditions

GovernanceBench compares 12 conditions spanning ungoverned baselines, context-only tool
styles, and specsmith governance workflows.

| ID | Condition | Expected Overhead Turns | Family |
|----|-----------|-------------------------|--------|
| `UNGOVERNED` | Raw agent with task prompt only | 0 | Baseline |
| `CONTEXT_ONLY` | Static `CLAUDE.md` / `AGENTS.md` injection | 0 | Context-only |
| `BMAD_STYLE` | BMAD blueprint/milestone scaffolding | 1 | External scaffold |
| `OPENSPEC_STYLE` | OpenSpec-style requirements injection | 0 | External scaffold |
| `SPECSMITH_LIGHT` | `specsmith preflight` gate only | 1 | specsmith |
| `SPECSMITH_FULL` | Full session (`audit → preflight → verify → save`) | 3 | specsmith |
| `CURSOR_RULES` | Cursor `.cursor/rules/*.mdc` style | 0 | Tool-native |
| `COPILOT_INSTRUCTIONS` | GitHub Copilot instructions style | 0 | Tool-native |
| `CODEX_AGENTS_MD` | Codex CLI `AGENTS.md` style | 0 | Tool-native |
| `CLINE_RULES` | Cline `.clinerules` style | 0 | Tool-native |
| `AGILE_TDD` | Test-first (RED→GREEN→REFACTOR) protocol | 1 | Process scaffold |
| `AIDER_CONVENTIONS` | Aider `CONVENTIONS.md` style | 0 | Tool-native |

The former `SPECSMITH_DISPATCH` condition is excluded from the executable
matrix because it simulated dispatch rather than running an equivalent agent
capability. Historical reports label it explicitly and do not carry it into new
comparative claims.

### Multi-domain task suites

Current and planned suites are intentionally cross-discipline to evaluate governance beyond
code-only benchmarks.

| Suite | Task IDs | Domain(s) | Status |
|------|----------|-----------|--------|
| Core suite | `T1`–`T13` | `todo_api`, `cli_tool` | Available |
| Wave 1 expansion | `T14`–`T22` | `todo_api`, `data_pipeline`, `verilog_module`, `patent_draft` | Definitions available; hidden oracles pending |
| Shell hardening suite | `T23`–`T27` | `shell_scripts` | Definitions available; hidden oracles pending |
| Wave 2 expansion | TBD | `ee_schematic`, `business_requirements`, `regulatory_doc`, `fpga_constraints` | Planned |

Task availability does not imply empirical coverage. Claims must identify the exact
tasks included in the matched run.

The publication-eligible default suite is `T1`, `T2`, `T6`, `T7`, `T10`,
`T11`, and `T13`. Its coding tasks have evaluator-only acceptance tests that
are injected after the agent stops. A standard task without an oracle fails
closed; clean fixtures and no-op responses cannot count as correct.

For standard coding tasks, `SPECSMITH_FULL` also blocks the agent's `done`
request until both `ruff check .` and `pytest` have passed after its latest
file write. A failed check sends the agent back through a repair turn; those
turns and tokens remain part of the measured cost. Other conditions do not
receive this completion gate. Hidden acceptance tests remain evaluator-only
and run after the agent stops, so the gate cannot reveal the benchmark answer.

---

## Provider Examples and Model Tiers

GovernanceBench is designed for multi-provider runs and tier-to-tier comparisons.

### Registry candidates

- **OpenAI**: `gpt-4o-mini`, `gpt-5.6-luna`, `gpt-5.6-terra`, `gpt-5.6-sol`
- **Anthropic**: `claude-haiku-4-5`, `claude-sonnet-4-5`, `claude-opus-4-5`
- **Google**: `gemini-3.5-flash`, `gemini-3.1-pro`
- **OpenAI-compatible endpoints** (vLLM/Ollama/proxy): open-source model hosting

### Model tier framing (examples)

| Tier | Price Band (input $/1M tokens, indicative) | Example Models |
|------|---------------------------------------------|----------------|
| Nano | `< $1` | `gpt-4.1-nano`, `gemini-3.5-flash`, `claude-haiku-4-5` |
| Mini | `$1–$4` blended | `gpt-5.6-luna`, `gpt-4.1-mini` |
| Mid | `$5–$15` blended | `gpt-5.6-terra`, `claude-sonnet-4-5`, `gemini-3.1-pro` |
| Frontier | `> $15` blended | `gpt-5.6-sol`, `claude-opus-4-5` |
| Open-source | Infra-dependent | `Qwen/Qwen3.6-35B-A3B`, `Llama-3.3-70B`, `gpt-oss-120b` |

Registry entries are candidates, not availability claims. The GitHub workflow
live-probes exact model access, billing, and tool-call compatibility before any
paid matrix begins. Final model ids must be recorded in run metadata and report
headers.

Use the workflow's `probe_only` input for a low-cost credential/model check. It
makes one tiny tool-enabled request per OpenAI or Hugging Face model and does not
start benchmark cells. OpenAI-compatible endpoints are also supported when their
secret is configured. Other registry providers fail closed until an equivalent
endpoint probe is implemented; they are examples, not currently runnable CI
targets.

### Running open models without HuggingFace credits

The four open tiers can run through the HuggingFace Inference Providers router
(`groups=open`) **or** through any direct OpenAI-compatible host
(`groups=open-direct`), which avoids the HF credit pool entirely. The
`open-direct` registry entries default to OpenRouter slugs. To run them, set:

- repo **variable** `BENCH_OPENAI_BASE_URL` — base URL of the host (defaults to
  `https://openrouter.ai/api/v1` when unset)
- repo **secret** `BENCH_OPENAI_COMPAT_API_KEY` — that host's API key

```bash
# Local example (OpenRouter):
export BENCH_OPENAI_BASE_URL=https://openrouter.ai/api/v1
export BENCH_OPENAI_COMPAT_API_KEY=sk-or-...
python -m govern_bench.run_bench \
  --provider openai-compat --model meta-llama/llama-3.1-8b-instruct \
  --task T1 --reps 1
```

Swap `BENCH_OPENAI_BASE_URL` and the `open-direct` model ids to target a
different OpenAI-compatible provider (DeepInfra, Together, Groq, etc.).

---

## Metrics and Statistical Methodology

### Primary metric

`tokens_per_correct_answer = mean_total_tokens / pass_rate`

Lower is better. This provider-neutral metric directly measures the stated goal:
the fewest tokens consumed for each correct answer. If `pass_rate == 0`, it is
non-finite.

### Core secondary metrics

- `pass_rate`
- `cost_of_pass = estimated_mean_api_cost_usd / pass_rate`
- `quality_score`
- `input_tokens`, `output_tokens`, `api_cost_usd`
- `rework_turns`, `governance_turns`, `wall_clock_s`
- governance-specific rates for clarification/safety tasks

### Statistical report fields

- 95% Wilson confidence interval for `pass_rate`
- 95% bootstrap confidence interval for `cost_of_pass` (1,000 resamples)
- `first_pass_rate` (`rework_turns == 1`)
- `consistency_score`
- `scaffold_lift` relative to `UNGOVERNED` for matched task/model
- `democratization_score` for nano+scaffold vs frontier+ungoverned comparisons
- CoP-quality Pareto frontier extraction

See `scripts/govern_bench/METHODOLOGY.md` for formulas and reporting rules.

---

## HF Submission Artifacts

GovernanceBench includes HF-oriented documentation and schema assets:

- `scripts/govern_bench/hf_card.md` — dataset card template/content
- `scripts/govern_bench/leaderboard_schema.json` — leaderboard JSON schema
- `scripts/govern_bench/METHODOLOGY.md` — standalone statistical methodology

Only complete empirical runs may be published as benchmark evidence. Partial or
provider-failed artifacts remain diagnostic and must not produce comparison claims.

### Result completeness contract

A real run is publishable only when every requested task/condition/repetition
cell is present exactly once and has no provider error or skipped status.
Cross-model reports additionally require identical cell sets for every model.
Provider failures remain diagnostic artifact rows, but the process exits nonzero
and the comparison generator rejects them instead of treating them as model
failures or zero-cost observations.

Coding cells additionally require all three gates: clean lint, project tests,
and the evaluator-only acceptance oracle. Pytest and Ruff caches are disabled so
validation artifacts do not pollute diffs or scope metrics.

---

## File Structure

```
scripts/govern_bench/
├── README.md
├── METHODOLOGY.md                 ← standalone methodology (new)
├── hf_card.md                     ← HF dataset card (new)
├── leaderboard_schema.json        ← HF leaderboard schema (new)
├── __init__.py
├── compare_runs.py
├── conditions.py                  ← 12 executable condition definitions
├── harness.py
├── judge.py
├── metrics.py
├── oracles/                       ← evaluator-only post-agent acceptance tests
├── report.py
├── run_bench.py
├── tasks.py
├── tasks/
│   └── T1_*.yml ... T27_*.yml     ← available multi-domain suites
└── projects/
    ├── todo_api/                  ← current
    ├── cli_tool/                  ← current
    ├── data_pipeline/             ← available
    ├── verilog_module/            ← available
    ├── patent_draft/              ← available
    └── shell_scripts/             ← available
```

---

## Notes

- Do not publish comparative claims without run metadata, confidence intervals, and raw output
  artifacts.
- Keep generated benchmark results separate from source-controlled templates/docs.
