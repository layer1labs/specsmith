# specsmith

[![CI](https://github.com/BitConcepts/specsmith/actions/workflows/ci.yml/badge.svg)](https://github.com/BitConcepts/specsmith/actions/workflows/ci.yml)
[![Sponsor](https://img.shields.io/badge/sponsor-%E2%9D%A4-ea4aaa?logo=github)](https://github.com/sponsors/BitConcepts)
[![Docs](https://readthedocs.org/projects/specsmith/badge/?version=stable)](https://specsmith.readthedocs.io/en/stable/)
[![PyPI](https://img.shields.io/pypi/v/specsmith?label=stable&style=flat&color=blue&cacheSeconds=60)](https://pypi.org/project/specsmith/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
**Applied Epistemic Engineering toolkit for AI-assisted development.**

> Intelligence proposes. Constraints decide. The ledger remembers.

specsmith treats belief systems like code: codable, testable, and deployable. It scaffolds
epistemically-governed projects, stress-tests requirements as BeliefArtifacts, runs
cryptographically-sealed trace vaults, and orchestrates AI agents under formal AEE governance.

**0.10.1 — Governance REST API, machine-state sync, and least-privilege permissions.**
Specsmith now serves as the governance backend for Kairos (the epistemically-governed
Rust terminal) via `specsmith governance-serve`, keeps `.specsmith/` JSON in sync
with `docs/` Markdown via `specsmith sync`, and gates every agent tool call via
`specsmith agent permissions-check`. Multi-agent profiles, BYOE endpoints, and the
AEE phase lifecycle are all fully wired.

```bash
specsmith governance-serve --port 7700     # Kairos governance REST API
specsmith sync                              # sync .specsmith/ from docs/ markdown
specsmith agent permissions-check git_push # check tool permission (REG-012)
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

**Agent:** `run` `agent run/plan/status/verify/improve/reports` `agent providers/tools/skills`

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
