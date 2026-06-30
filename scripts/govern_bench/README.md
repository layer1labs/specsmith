# govern_bench — GovernanceBench (specsmith)

GovernanceBench measures how governance/scaffolding changes **cost, quality, and safety**
across coding-agent workflows.

> Status: expansion in progress. Published benchmark results are **TBD**.

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

### 13 governance conditions

GovernanceBench compares 13 conditions spanning ungoverned baselines, context-only tool
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
| `SPECSMITH_DISPATCH` | specsmith multi-agent DAG dispatch | 5 | specsmith |

### Multi-domain task suites

Current and planned suites are intentionally cross-discipline to evaluate governance beyond
code-only benchmarks.

| Suite | Task IDs | Domain(s) | Status |
|------|----------|-----------|--------|
| Core suite | `T1`–`T13` | `todo_api`, `cli_tool` | Available |
| Wave 1 expansion | `T14`–`T22` | `todo_api`, `data_pipeline`, `verilog_module`, `patent_draft` | Planned |
| Shell hardening suite | `T23`–`T27` | `shell_scripts` | Planned |
| Wave 2 expansion | TBD | `ee_schematic`, `business_requirements`, `regulatory_doc`, `fpga_constraints` | Planned |

No benchmark claims should be made from planned suites until task artifacts and run data exist.

---

## Provider Examples and Model Tiers

GovernanceBench is designed for multi-provider runs and tier-to-tier comparisons.

### Provider examples

- **OpenAI**: `gpt-4.1-nano`, `gpt-4o-mini`, `gpt-5.4`, `gpt-5`
- **Anthropic**: `claude-haiku-4-5`, `claude-sonnet-4-5`, `claude-opus-4-5`
- **Google**: `gemini-3.5-flash`, `gemini-3.1-pro`
- **OpenAI-compatible endpoints** (vLLM/Ollama/proxy): open-source model hosting

### Model tier framing (examples)

| Tier | Price Band (input $/1M tokens, indicative) | Example Models |
|------|---------------------------------------------|----------------|
| Nano | `< $1` | `gpt-4.1-nano`, `gemini-3.5-flash`, `claude-haiku-4-5` |
| Mini | `$1–$4` | `gpt-4o-mini`, `gpt-5.5`, `gpt-4.1-mini` |
| Mid | `$5–$15` | `gpt-5.4`, `claude-sonnet-4-5`, `gemini-3.1-pro` |
| Frontier | `> $15` | `gpt-5`, `claude-opus-4-5` |
| Open-source | Infra-dependent | `Llama-3.1-70B`, `Qwen2.5-Coder-72B`, `DeepSeek-Coder-V3` |

Use these as comparison tiers, not fixed coverage requirements. Final model lists should be
recorded in run metadata and report headers.

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

`cost_of_pass = mean_api_cost_usd / pass_rate`

Lower is better. If `pass_rate == 0`, cost-of-pass is treated as non-finite.

### Core secondary metrics

- `pass_rate`
- `quality_score`
- `input_tokens`, `output_tokens`, `api_cost_usd`
- `rework_turns`, `governance_turns`, `wall_clock_s`
- governance-specific rates for clarification/safety tasks

### Expansion statistics (planned report fields)

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

Benchmark result values should remain `TBD` in docs until empirical runs are completed.

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
├── conditions.py                  ← 13 condition definitions
├── harness.py
├── judge.py
├── metrics.py
├── report.py
├── run_bench.py
├── tasks.py
├── tasks/
│   ├── T1_*.yml ... T13_*.yml     ← current core suite
│   └── T14+                        ← planned multi-domain expansion
└── projects/
    ├── todo_api/                  ← current
    ├── cli_tool/                  ← current
    ├── data_pipeline/             ← planned
    ├── verilog_module/            ← planned
    ├── patent_draft/              ← planned
    └── shell_scripts/             ← planned
```

---

## Notes

- Do not publish comparative claims without run metadata, confidence intervals, and raw output
  artifacts.
- Keep generated benchmark results separate from source-controlled templates/docs.
