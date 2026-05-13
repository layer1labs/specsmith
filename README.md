# specsmith

[![CI](https://github.com/layer1labs/specsmith/actions/workflows/ci.yml/badge.svg)](https://github.com/layer1labs/specsmith/actions/workflows/ci.yml)
[![Sponsor](https://img.shields.io/badge/sponsor-%E2%9D%A4-ea4aaa?logo=github)](https://github.com/sponsors/layer1labs)
[![Docs](https://readthedocs.org/projects/specsmith/badge/?version=stable)](https://specsmith.readthedocs.io/en/stable/)
[![PyPI](https://img.shields.io/pypi/v/specsmith?label=stable&style=flat&color=blue&cacheSeconds=60)](https://pypi.org/project/specsmith/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Applied Epistemic Engineering toolkit for AI-assisted development.**

> Intelligence proposes. Constraints decide. The ledger remembers.

specsmith treats belief systems like code: codable, testable, and deployable. It scaffolds
epistemically-governed projects, stress-tests requirements as BeliefArtifacts, runs
cryptographically-sealed trace vaults, and orchestrates AI agents under formal AEE governance.

**0.11.0 — EU AI Act / NIST AI RMF compliance, context window management, and governance tools panel.**
Specsmith now ships a full compliance and auditability layer aligned to the EU AI Act (2024/1689)
and the NIST AI Risk Management Framework 1.0. Every agent action is cryptographically sealed,
every AI-generated output is disclosed, context windows are GPU-aware and protected against
overflow, and a dedicated governance tools panel in Kairos surfaces compliance settings
per-session and per-project.

```bash
specsmith governance-serve --port 7700     # Kairos governance REST API
specsmith sync                              # sync .specsmith/ from docs/ markdown
specsmith agent permissions-check git_push # check tool permission (REQ-012)
specsmith ollama gpu                        # detect GPU VRAM, recommend context size
specsmith export                            # generate full compliance report

# Update channel management (REQ-248)
specsmith channel set stable               # pin to stable releases
specsmith channel set dev                  # opt in to dev/pre-release builds
specsmith channel get --json               # show current channel + source

# ESDB extended lifecycle (REQ-249..253)
specsmith esdb export --json               # dump all records to JSON snapshot
specsmith esdb import backup.json          # validate + stage an import
specsmith esdb backup                      # create timestamped snapshot
specsmith esdb rollback --steps 2          # report WAL rollback (stub)
specsmith esdb compact                     # request WAL compaction

# Skills lifecycle (REQ-254..255)
specsmith skills deactivate <skill-id>     # set active=false in skill.json
specsmith skills delete <skill-id> --yes   # permanently remove skill

# MCP config generation (REQ-256)
specsmith mcp generate "Search USPTO patents" --json  # JSON config stub

# Agent ask dispatcher — no LLM required (REQ-257)
specsmith agent ask "show esdb status" --json-output
specsmith agent ask "build skill for summarizing"
```

It also co-installs the standalone `epistemic` Python library for direct use in any project:

```python
from epistemic import AEESession         # works in any Python 3.10+ project
from epistemic import BeliefArtifact, StressTester, CertaintyEngine
```

---

## What is Applied Epistemic Engineering?

AEE treats requirements, decisions, and assumptions — the beliefs your project depends on — as
engineering artifacts subject to the same discipline as code: version control, testing, and refactoring.

**The 4-step core method: Frame → Disassemble → Stress-Test → Reconstruct**

**The 5 foundational axioms:**
1. **Observability** — every belief must be inspectable
2. **Falsifiability** — every belief must be challengeable
3. **Irreducibility** — beliefs decompose to atomic primitives
4. **Reconstructability** — every failed belief can be rebuilt
5. **Convergence** — stress-test + recovery always reaches Equilibrium

---

## The AEE Workflow — 7 Phases

specsmith tracks your project through the full AEE development cycle:

```
🌱 Inception → 🏗 Architecture → 📋 Requirements → ✅ Test Spec
    → ⚙ Implementation → 🔬 Verification → 🚀 Release
```

```bash
specsmith phase          # show current phase + readiness checklist
specsmith phase next     # advance to the next phase (runs checks first)
specsmith phase set requirements  # jump to a specific phase
specsmith phase list     # list all phases
```

The current phase is persisted in `scaffold.yml` as `aee_phase` and displayed in the
Kairos Governance page. Each phase has a checklist of file/command criteria, recommended
commands, and a readiness percentage.

---

## Install

**Recommended — via pipx (works with Kairos, any terminal, and CI):**

```bash
pipx install specsmith                    # core CLI + epistemic library
pipx inject specsmith anthropic           # + Claude support
pipx inject specsmith openai              # + GPT / O-series support
pipx inject specsmith google-generativeai # + Gemini support
```

**Or with pip:**

```bash
pip install specsmith                     # core
pip install "specsmith[anthropic]"       # + Claude
pip install "specsmith[openai]"          # + GPT/O-series
pip install "specsmith[gemini]"          # + Gemini
```

**Update:**

```bash
pipx upgrade specsmith
specsmith self-update
```

---

## Quick Start

```bash
# New project (interactive)
specsmith init

# Adopt an existing project
specsmith import --project-dir ./my-project

# Check governance health
specsmith audit --project-dir ./my-project

# Run AEE stress-test on requirements
specsmith stress-test --project-dir ./my-project

# Full epistemic audit (certainty + logic knots + recovery proposals)
specsmith epistemic-audit --project-dir ./my-project

# Start the agentic REPL
specsmith run --project-dir ./my-project

# AG2 agent shell — Planner/Builder/Verifier over Ollama
specsmith agent status                    # check agent config + Ollama
specsmith agent plan "add logging"        # plan only (no execution)
specsmith agent run "fix lint errors"     # full Plan → Build → Verify
specsmith agent improve "add tests"       # self-improvement with reports
specsmith agent verify                    # run Verifier on current state
specsmith agent reports                   # list improvement reports

# Check current AEE workflow phase
specsmith phase --project-dir ./my-project
```

---

## Machine State Sync

`.specsmith/` always mirrors the human-readable `docs/` governance files.
Run `specsmith sync` after any change to `docs/REQUIREMENTS.md` or `docs/TESTS.md`:

```bash
specsmith sync                     # regenerate .specsmith/requirements.json + testcases.json
specsmith sync --check             # CI mode: exits 1 if out of sync without writing
specsmith sync --json              # emit sync result as JSON
```

## Least-Privilege Agent Permissions (REG-012)

```bash
specsmith agent permissions                      # show active permission profile
specsmith agent permissions-check git_push       # check if git_push is allowed
specsmith agent permissions-check git_push --no-log  # dry-run (no ledger write)
```

Configure in `docs/SPECSMITH.yml`:
```yaml
agent:
  permissions:
    preset: standard       # read_only | standard | extended | admin
    # Or custom:
    allow: [read_file, write_file, run_shell, git_status]
    deny:  [git_push, git_create_pr]
```

---

## AI Compliance & Governance

specsmith is designed from the ground up for **auditable, explainable, and human-overseen AI**.
It implements concrete compliance mechanisms mapped to the two major regulatory frameworks
that govern AI systems in production today.

### Standards Coverage

**EU AI Act (Regulation 2024/1689)** — The world's first comprehensive legal framework for AI,
enforced across the European Union. High-risk AI systems must provide transparency, auditability,
human oversight, and robustness. specsmith implements:

| EU AI Act Requirement | specsmith Mechanism |
|---|---|
| Art. 9 — Risk Management System | AEE verification loop with confidence scoring and equilibrium checks |
| Art. 12 — Logging & Record-Keeping | `TraceVault` SHA-256 chained ledger (tamper-evident, append-only) |
| Art. 13 — Transparency & Explainability | `ai_disclosure` block in every preflight response; `/why` in Nexus REPL |
| Art. 14 — Human Oversight | Human escalation threshold (`--escalate-threshold`); kill-switch CLI |
| Art. 15 — Accuracy & Robustness | Bounded retry (max 3×), confidence gates, hard context ceiling (REQ-247) |
| Art. 53 — GPAI Model Transparency | Provider + model name emitted in every `ai_disclosure` block |

**NIST AI Risk Management Framework 1.0 (AI RMF)** — The US standard for managing AI risk
across the AI lifecycle. specsmith addresses all four core functions:

| NIST AI RMF Function | specsmith Mechanism |
|---|---|
| **GOVERN** — Policies & accountability | Governance rules (H1–H13), permissions profile, `scaffold.yml` policy |
| **MAP** — Risk identification | AEE stress-test, belief graph, contradictions and uncertainty metrics |
| **MEASURE** — Risk analysis | Confidence scoring, epistemic equilibrium, `specsmith epistemic-audit` |
| **MANAGE** — Risk treatment | Kill-switch, escalation, bounded retry, safe-write backup, permissions deny-list |

### How Each Compliance Mechanism Works

#### 1. Tamper-Evident Audit Log — `TraceVault` (REQ-206)

Every agent action, decision, milestone, and audit gate is recorded as a JSONL entry in
`.specsmith/trace.jsonl`. Each entry contains a SHA-256 hash of its own content plus the
hash of the previous entry, forming a cryptographic chain:

```jsonl
{"seq":1, "type":"DECISION", "description":"...", "hash":"a3f9...", "prev":"genesis"}
{"seq":2, "type":"MILESTONE", "description":"...", "hash":"7c2b...", "prev":"a3f9..."}
```

Any modification to a past entry breaks every subsequent hash. `specsmith trace verify`
detects and reports the first corrupted entry. The file is append-only — overwrites are
blocked by `safe_write`. This satisfies **EU AI Act Art. 12** (logging and record-keeping)
and **NIST AI RMF GOVERN** (accountability trail).

#### 2. AI Disclosure — Every Response (REQ-207)

Every preflight response includes a mandatory `ai_disclosure` block:

```json
{
  "ai_disclosure": {
    "governed_by": "specsmith",
    "governance_gated": true,
    "provider": "ollama",
    "model": "qwen2.5:14b",
    "spec_version": "0.11.0"
  }
}
```

This ensures every AI-generated output is traceable to its source model and version,
meeting **EU AI Act Art. 13** (transparency) and **Art. 53** (GPAI transparency).
It is impossible to suppress — the field is injected at the governance layer before
any response is returned to the client.

#### 3. Human Escalation — Configurable Threshold (REQ-209)

When an action's confidence is below the escalation threshold, specsmith sets
`escalation_required: true` and includes an `escalation_reason` in the preflight payload.
Kairos surfaces this as a confirmation dialog before execution proceeds.

```bash
specsmith preflight "deploy to production" --escalate-threshold 0.85 --json
# → escalation_required: true, escalation_reason: "confidence 0.71 < threshold 0.85"
```

This implements **EU AI Act Art. 14** (human oversight) and **NIST AI RMF MANAGE**.

#### 4. Kill-Switch — Immediate Session Termination (REQ-210)

A `kill-session` CLI command and keyboard shortcut (surfaced in Kairos) immediately
terminates all active agent sessions and records a timestamped kill event in `LEDGER.md`:

```bash
specsmith kill-session                   # terminate all sessions, log kill event
specsmith kill-session --session abc123  # terminate a specific session
```

This satisfies **EU AI Act Art. 14 §4** (ability to intervene and stop the AI system)
and is required for certification of high-risk AI systems.

#### 5. Append-Only Safe Write — `safe_write` (REQ-213)

All governance file writes go through `safe_write`, which:
- **Appends** to `LEDGER.md` and `.specsmith/ledger.jsonl` — never truncates
- **Backs up** any file before overwriting it (timestamped `.bak` copy)
- **Prevents** accidental destruction of audit history

This satisfies **EU AI Act Art. 12** (records must be kept for the lifetime of the system)
and provides recovery capability per **NIST AI RMF MANAGE**.

#### 6. Least-Privilege Permissions (REQ-217, REQ-012)

Every agent tool call is gated through a permission profile. Tools outside the active
profile are denied with exit code 3 and a ledger entry:

```bash
specsmith agent permissions-check git_push   # exit 0 = allowed, exit 3 = denied
specsmith agent permissions                  # show active profile
```

Four built-in presets (`read_only`, `standard`, `extended`, `admin`) plus full
custom allow/deny lists in `.specsmith/config.yml`. This implements **NIST AI RMF GOVERN**
(policy enforcement) and principle of least privilege per standard security practice.

#### 7. Policy Guardrails — `is_safe_command` (REQ-220)

Before any shell command is executed, `agent.safety.is_safe_command()` classifies it
against a deny list of destructive patterns (`rm -rf`, `git push origin main`,
`kubectl apply`, `cat .env`, etc.). Denied commands are blocked and logged.
This implements **NIST AI RMF MANAGE** (risk treatment at the action level).

#### 8. Compliance Export Report (REQ-208, REQ-215)

`specsmith export` generates a full compliance report containing:
- **AI System Inventory** — all providers, models, and versions used
- **Risk Classification** — AEE phase, confidence scores, open work items
- **Human Oversight Controls** — active permission profile, escalation settings, kill-switch state
- **Audit Trail Summary** — TraceVault chain length, last verification, any tampering

```bash
specsmith export --format markdown > compliance-report.md
specsmith export --format json > compliance-report.json
```

This report is suitable for submission to regulators, internal audit teams, or
SOC-2 / ISO-42001 reviewers.

### Compliance per Session and per Project

Compliance settings are layered:

1. **Global defaults** — `~/.specsmith/config.yml` (user-level defaults)
2. **Per-project policy** — `.specsmith/config.yml` (committed to the repo)
3. **Per-session overrides** — Kairos Governance panel or CLI flags

The Kairos **Governance Tools Panel** (Settings → Governance) exposes all compliance
controls in a live UI: escalation threshold, permission profile, kill-switch, audit log
viewer, and context window settings. Changes take effect immediately for the active
session and can optionally be written back to the per-project `.specsmith/config.yml`.

---

## Context Window Management

specsmith enforces safe, efficient use of LLM context windows — especially critical
when running local models via Ollama where the context limit directly affects GPU VRAM.

### GPU-Aware Context Sizing (REQ-244)

```bash
specsmith ollama gpu                    # detect GPU VRAM (NVIDIA + AMD supported)
specsmith ollama available              # show models within your VRAM budget
```

VRAM tiers and recommended context sizes:

| VRAM | Recommended Context |
|---|---|
| < 6 GB (CPU or low-end GPU) | 4,096 tokens |
| 6–11 GB | 8,192 tokens |
| 12–19 GB | 16,384 tokens |
| 20 GB+ | 32,768 tokens |

Override via `SPECSMITH_OLLAMA_CONTEXT_LENGTH` or `ollama.context_length` in `.specsmith/config.yml`.

### Live Context Fill Indicator (REQ-245)

The context fill tracker emits real-time JSONL events consumed by Kairos:

```jsonl
{"type": "context_fill", "used": 27500, "limit": 32768, "pct": 83.9}
```

Kairos displays a compact fill bar in the agent footer. When fill reaches the
compression threshold (default 80%), specsmith signals that context summarization
should run before the next turn.

### Auto Context Compression (REQ-246)

When fill reaches the compression threshold, specsmith automatically triggers
conversation summarization — the current context is condensed to a compact summary
that preserves key decisions and facts while freeing window space. This happens
transparently before the next agent turn.

Configure in `.specsmith/config.yml`:

```yaml
context:
  compression_threshold_pct: 80   # trigger summarization at 80% fill
  auto_compress: true             # enable automatic compression
```

### Hard Context Ceiling — Never 100% Full (REQ-247)

A hard reservation of **15% of the context window** (minimum 2,048 tokens) is always
held back for the governance layer. Attempts to fill beyond the effective ceiling raise
`ContextFullError` — making it impossible to reach a state where even a compression
request cannot be processed. This is a safety invariant, not a configuration option.

---

## Kairos + Governance REST API

**Kairos** is the companion Rust terminal runtime (`BitConcepts/kairos`). specsmith
acts as the governance backend: Kairos spawns `specsmith governance-serve` at startup
and routes all preflight and verify calls through it.

```bash
# Start the governance REST API (Kairos calls this automatically)
specsmith governance-serve --port 7700 --project-dir .

# Classify a natural-language utterance under Specsmith governance
specsmith preflight "fix the cleanup dry-run regression" --json

# Start the agentic REPL
specsmith run
> what does the cleanup module do?           # read-only ask -> answered
> fix the cleanup dry-run regression          # change -> Specsmith approves, runs
> delete the entire dist directory            # destructive -> needs clarification
```

---

## Nexus

The Nexus runtime is specsmith's local-first agentic REPL — a
governance-gated broker that sits between you and the LLM.

Every utterance passes through `specsmith preflight` before execution.
The broker classifies intent, matches requirements, and gates the action.
After execution, `specsmith verify` checks equilibrium. The `/why` command
shows the full governance trace.

```bash
# Interactive REPL with governance
specsmith run
nexus> fix the cleanup bug         # broker classifies → accepts → executes → verifies
nexus> /why                         # show governance trace for last action
nexus> /exit
```

The Nexus broker:
- **Preflight gate**: every change goes through `specsmith preflight`
- **Bounded retry**: failed actions retry up to 3× with strategy classification
- **Execution trace**: every action is sealed in the cryptographic trace vault
- **`/why` toggle**: shows governance rationale in human-readable form
```

**How it works.** A natural-language **broker** classifies intent, infers scope from
your requirements, and asks Specsmith to **preflight** the request. Only when the
preflight decision is `accepted` does Nexus drive the AG2 orchestrator — and it does so
through a **bounded-retry harness** so you can never accidentally run away. By default,
Nexus speaks plain English; toggle `/why` in the REPL to surface the underlying
requirement, test, and work-item identifiers Specsmith assigned.

**Pieces in this repo.**
- `specsmith preflight` — CLI subcommand emitting a deterministic governance JSON payload
  (`decision`, `requirement_ids`, `test_case_ids`, `confidence_target`, `instruction`).
- `src/specsmith/agent/broker.py` — natural-language broker (intent + scope + narration).
- `src/specsmith/agent/repl.py` — Nexus REPL with the `/why` toggle and execution gate.
- `docker-compose.yml` — pinned vLLM `l1-nexus` model server with the Hermes tool-call parser.
- `scripts/nexus_smoke.py` — opt-in live smoke test (`NEXUS_LIVE=1` to run against
  a running container).

---

## AI Model Intelligence

specsmith ships a complete AI model intelligence layer for tracking, scoring, and routing
to the best available LLM for each task type.

### HF Open LLM Leaderboard Sync (REQ-263..REQ-269)

Syncs benchmark data from the HuggingFace Open LLM Leaderboard and computes three
task-specific bucket scores — **reasoning**, **conversational**, and **longform** — for
every model. A 40+ model static fallback ensures scores are always available even without
network access.

```bash
specsmith model-intel sync                  # sync from HF leaderboard (static fallback if offline)
specsmith model-intel scores                # list all cached bucket scores
specsmith model-intel scores --model gpt-4o # show scores for a specific model
specsmith model-intel recommendations       # top-10 models for reasoning bucket
specsmith model-intel recommendations --bucket conversational  # or longform
specsmith model-intel connection            # test HF API connectivity + token status
```

Set `SPECSMITH_HF_TOKEN` for authenticated access (1000 req/5min instead of 500).
Scores persist to `~/.specsmith/model_scores.json`. Background sync runs 15s after startup
then daily.

**Bucket formulas (normalised 0-100):**
- Reasoning = 0.35×MATH + 0.30×GPQA + 0.25×BBH + 0.10×IFEval
- Conversational = 0.40×IFEval + 0.35×MMLU-PRO + 0.25×BBH
- Longform = 0.35×MUSR + 0.35×IFEval + 0.30×MMLU-PRO

### Model Capability Profiles (REQ-270..REQ-271)

40+ pre-built model profiles cover all major providers (OpenAI, Anthropic, Google, Mistral,
Meta Llama, Qwen, DeepSeek, and local Ollama variants). Each profile specifies:
`max_tokens`, `prompt_style` (sections/xml/markdown), `supports_vision`,
`supports_tool_calls`, `reasoning_mode`, and `context_window`.

Context-aware history trimming preserves system messages while summarising older turns when
the token budget is exceeded:

```python
from specsmith.agent.model_profiles import get_profile, trim_history

profile = get_profile("qwen2.5:14b")   # exact or prefix match; returns default if unknown
messages = trim_history(messages, budget_chars=12000)
```

### LLM Client with Provider Fallback (REQ-275..REQ-277)

`LLMClient` wraps multiple providers with automatic fallback on 429 / 401 errors,
O-series parameter translation (`max_completion_tokens`, temperature=1, developer role),
and vLLM guided-JSON payload injection:

```python
from specsmith.agent.llm_client import LLMClient

client = LLMClient([
    {"provider_type": "cloud", "model": "gpt-4o", ...},
    {"provider_type": "ollama", "model": "qwen2.5:14b", ...},  # local fallback
])
result = client.chat([{"role": "user", "content": "hello"}])
```

### Endpoint Presets + Suggest Profiles (REQ-278..REQ-280)

A registry of 10+ pre-configured endpoint presets for common cloud and local LLM providers:

```bash
specsmith agent endpoint-presets            # list all presets (vllm, lm_studio, openrouter, etc.)
specsmith agent endpoint-presets --json     # machine-readable output
specsmith agent suggest-profiles            # suggest optimal profiles based on env (API keys, hardware)
specsmith agent suggest-profiles --json     # structured suggestions with bucket/role annotations
```

Suggestions are read-only (never persisted) and inspect `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`,
`GOOGLE_API_KEY`, and local Ollama availability.

### Kairos AI Providers — Bucket Score Columns (REQ-281)

The Kairos **Agents > AI Providers** table gained three new columns — **R** (reasoning),
**C** (conversational), **L** (longform) — showing each provider's HF bucket scores inline.
A **Sync Scores** button triggers a background sync from the HF leaderboard without
interrupting the active session.

---

## Kairos — Flagship Terminal Client

**[Kairos](https://github.com/BitConcepts/kairos)** is the recommended terminal client for specsmith.
Kairos spawns specsmith as a managed governance child process at startup and routes all
preflight, verify, and BYOE proxy calls through it. The Governance settings page shows live
specsmith status, version, and one-click update.

```bash
# Kairos starts specsmith automatically; or run manually:
specsmith governance-serve --port 7700 --project-dir .
```

The VS Code extension (`specsmith-vscode`) has been **deprecated** in favour of Kairos.
Use `pipx install specsmith` for standalone CLI usage from any terminal.

---

## Supporting specsmith

specsmith is open source and built by a small team. Every bit of support helps:

- ⭐ **Star** [specsmith](https://github.com/BitConcepts/specsmith) and [kairos](https://github.com/BitConcepts/kairos) on GitHub
- 📣 **Tell your friends and colleagues** — word of mouth is our best marketing
- 🐛 **Report bugs** via [GitHub Issues](https://github.com/BitConcepts/specsmith/issues) — even small ones help
- 💡 **Suggest features** via [GitHub Discussions](https://github.com/BitConcepts/specsmith/discussions) — we read every suggestion
- 🔧 **Fix bugs and contribute** — see [CONTRIBUTING.md](CONTRIBUTING.md); PRs welcome
- 📝 **Write about specsmith** — blog posts, tutorials, and talks help the community grow
- ❤️ **[Sponsor BitConcepts](https://github.com/sponsors/BitConcepts)** — directly funds development

---

## Ollama — Local LLMs (Zero API Cost)

specsmith has first-class Ollama support, including:

```bash
specsmith ollama gpu                    # detect GPU and VRAM tier
specsmith ollama available              # show catalog filtered by VRAM budget
specsmith ollama available --task code  # filter by task type
specsmith ollama pull qwen2.5:14b      # download a model
specsmith ollama suggest requirements  # task-based recommendations
specsmith ollama list                  # show installed models
```

GPU-aware context sizing: 4K/8K/16K/32K tokens based on detected VRAM.
Override via `SPECSMITH_OLLAMA_CONTEXT_LENGTH` env var or `ollama.context_length` in `.specsmith/config.yml`.

---

## FPGA / HDL Projects

specsmith supports FPGA-specific project types with full governance:

```yaml
# scaffold.yml
type: fpga-rtl-amd          # or fpga-rtl-intel / fpga-rtl-lattice / fpga-rtl
fpga_tools:
  - vivado
  - gtkwave
  - vsg
  - ghdl
  - verilator
```

Supported tools: **Synthesis:** vivado, quartus, radiant, diamond, gowin.
**Simulation:** ghdl, iverilog, verilator, modelsim, questasim, xsim.
**Waveform:** gtkwave, surfer. **Linting:** vsg, verible, svlint.
**Formal:** symbiyosys. **OSS flow:** yosys, nextpnr, openFPGALoader.

---

## 50+ CLI Commands

**Governance:** `init` `import` `audit` `validate` `diff` `upgrade` `compress` `doctor` `export` `architect`

**AEE Epistemic:** `stress-test` `epistemic-audit` `belief-graph` `trace seal/verify/log` `integrate`

**Workflow:** `phase show/set/next/list` `ledger add/list` `req list/add/gaps/trace`

**Agent:** `run` `agent run/plan/status/verify/improve/reports` `agent providers/tools/skills` `agent suggest-profiles` `agent endpoint-presets`

**Model Intel:** `model-intel sync` `model-intel scores` `model-intel recommendations` `model-intel connection`

**Ollama:** `ollama list/available/gpu/pull/suggest`

**Workspace:** `workspace init/audit/export`

**VCS:** `commit` `push` `sync` `branch` `pr` `status`

**Tools:** `tools scan [--fpga]` `tools install <tool>` `tools rules [--tool] [--list]`

**Tools:** `exec` `ps` `abort` `watch` `optimize` `credits` `self-update`

**Auth:** `auth set/list/remove/check`

**Patent:** `patent search/prior-art`

---

## 35 Project Types

**Software:** Python CLI/lib/web, Rust, Go, C/C++, .NET, Node.js/TypeScript, mobile, microservices, data/ML.

**Hardware/Embedded:** FPGA/RTL (Xilinx, Intel, Lattice, generic), Yocto BSP, embedded C/C++.

**Documents:** Technical specs, research papers, API specs, requirements management.

**Business/Legal:** Business plans, patent applications, compliance frameworks.

---

## epistemic Library

The standalone `epistemic` Python library works in any Python 3.10+ project — no specsmith coupling:

```python
from epistemic import AEESession, BeliefArtifact, StressTester

session = AEESession("my-project", threshold=0.70)
session.add_belief(
    artifact_id="HYP-001",
    propositions=["The API always returns valid JSON"],
    epistemic_boundary=["Valid auth token required"],
)
session.accept("HYP-001")
result = session.run()
print(result.summary())
# certainty=0.55, failures=2, equilibrium=False
```

Use cases: linguistics research, compliance pipelines, AI alignment, patent prosecution.

---

## Governance Rules (H1–H13)

13 hard rules enforced by `specsmith validate`:

- **H11** — Every loop or blocking wait must have a timeout, fallback exit, and diagnostic message.
- **H12** — Windows multi-step automation goes into `.cmd` files, not inline shell invocations.
- **H13** — Agent tools must declare epistemic contracts (what they claim and what they cannot detect).

---

## The specsmith Bootstrap

specsmith governs itself — the specsmith repo is a specsmith-managed project. Run `specsmith audit`
in this repo to check its governance health. This means every feature we add to specsmith is
immediately dogfooded on specsmith itself. [Kairos](https://github.com/BitConcepts/kairos)
is the companion terminal and flagship client.

## Documentation

**[specsmith.readthedocs.io](https://specsmith.readthedocs.io)** — Full manual: AEE primer,
command reference, project types, tool registry, governance model, Ollama guide, Kairos integration.

## Links

- [PyPI](https://pypi.org/project/specsmith/)
- [Documentation](https://specsmith.readthedocs.io)
- [Changelog](CHANGELOG.md)
- [Kairos terminal client](https://github.com/BitConcepts/kairos)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

## License

MIT — Copyright (c) 2026 BitConcepts, LLC.
