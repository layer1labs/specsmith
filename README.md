# specsmith

[![CI](https://github.com/BitConcepts/specsmith/actions/workflows/ci.yml/badge.svg)](https://github.com/BitConcepts/specsmith/actions/workflows/ci.yml)
[![Sponsor](https://img.shields.io/badge/sponsor-%E2%9D%A4-ea4aaa?logo=github)](https://github.com/sponsors/BitConcepts)
[![Docs](https://readthedocs.org/projects/specsmith/badge/?version=stable)](https://specsmith.readthedocs.io/en/stable/)
[![PyPI](https://img.shields.io/pypi/v/specsmith?label=stable&style=flat&color=blue&cacheSeconds=60)](https://pypi.org/project/specsmith/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![VS Code Extension](https://img.shields.io/badge/VS%20Code-AEE%20Workbench-4ec9b0?logo=visualstudiocode)](https://github.com/BitConcepts/specsmith-vscode)

**Applied Epistemic Engineering toolkit for AI-assisted development.**

> Intelligence proposes. Constraints decide. The ledger remembers.

specsmith treats belief systems like code: codable, testable, and deployable. It scaffolds
epistemically-governed projects, stress-tests requirements as BeliefArtifacts, runs
cryptographically-sealed trace vaults, and orchestrates AI agents under formal AEE governance.

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

The current phase is persisted in `scaffold.yml` as `aee_phase` and displayed in the VS Code
Governance Panel. Each phase has a checklist of file/command criteria, recommended commands,
and a readiness percentage.

---

## Install

**Recommended — global install via [pipx](https://pipx.pypa.io):**

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

# Check current AEE workflow phase
specsmith phase --project-dir ./my-project
```

---

## VS Code Extension

The **specsmith AEE Workbench** VS Code extension is the flagship client:

```
# Install specsmith first, then:
# VS Code: Ctrl+Shift+P → specsmith: New Agent Session
# Governance Panel: Ctrl+Shift+G
```

**Key features:**
- **6-tab Settings panel** — Project / Tools / Files / Updates / Actions / Execution
- **Execution profiles** — safe (read-only) / standard / open / admin; custom allow/block command lists stored in `scaffold.yml`
- **AEE phase indicator** — shows current phase with readiness %, Next Phase button, and phase selector
- **AI agent sessions** — independent process per project, JSONL bridge, chat with file injection
- **Live model listing** — Anthropic, OpenAI, Gemini, Mistral, local Ollama (GPU-aware)
- **Ollama integration** — browse curated catalog, download models with progress, task-based suggestions
- **FPGA/HDL tool support** — vivado, gtkwave, vsg, ghdl, verilator, yosys, nextpnr, and 15 more
- **Tool installer** — scan installed tools; one-click install via winget/brew/apt for missing tools
- **Tool rules** — curated AI context rules for 20+ tools (VSG, GHDL, Verilator, ruff, mypy, etc.) auto-injected into agent system prompt
- **API key management** — stored in OS credential store (Windows Credential Manager / macOS Keychain)
- **Update checker** — PyPI version check, Install Update button, release channel selector (stable / pre-release)
- **Auto-open** — Settings panel always opens alongside every new session; never a blank pane

**[→ specsmith-vscode on GitHub](https://github.com/BitConcepts/specsmith-vscode)**

---

## Supporting specsmith

If specsmith is saving you time or helping your team ship better software, please consider:

- **[Sponsoring BitConcepts](https://github.com/sponsors/BitConcepts)** — directly funds development
- **Starring** [specsmith](https://github.com/BitConcepts/specsmith) and [specsmith-vscode](https://github.com/BitConcepts/specsmith-vscode) on GitHub
- **Reporting bugs** and **requesting features** via [GitHub Issues](https://github.com/BitConcepts/specsmith/issues)
- **Contributing** — see [CONTRIBUTING.md](CONTRIBUTING.md)

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

GPU-aware context sizing in the VS Code extension: 4K/8K/16K/32K tokens based on detected VRAM.
Override with `specsmith.ollamaContextLength` in VS Code settings.

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

**Agent:** `run` `agent providers/tools/skills`

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

## Documentation

**[specsmith.readthedocs.io](https://specsmith.readthedocs.io)** — Full manual: AEE primer,
command reference, project types, tool registry, governance model, Ollama guide, VS Code extension.

## Links

- [PyPI](https://pypi.org/project/specsmith/)
- [Documentation](https://specsmith.readthedocs.io)
- [Changelog](CHANGELOG.md)
- [VS Code Extension](https://github.com/BitConcepts/specsmith-vscode)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

## License

MIT — Copyright (c) 2026 BitConcepts, LLC.
