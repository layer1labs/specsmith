# specsmith

[![CI](https://github.com/BitConcepts/specsmith/actions/workflows/ci.yml/badge.svg)](https://github.com/BitConcepts/specsmith/actions/workflows/ci.yml)
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

AEE treats beliefs — requirements, hypotheses, decisions, constraints — like code:

- **Codable**: every claim is a `BeliefArtifact` with propositions and boundaries
- **Testable**: the `StressTester` applies adversarial challenges to surface failure modes
- **Deployable**: beliefs that survive stress-testing can be sealed with cryptographic proof

The 4-step AEE core method: **Frame → Disassemble → Stress-Test → Reconstruct**

The 5 foundational axioms:
1. **Observability** — every belief must be inspectable (hidden assumptions = stop condition)
2. **Falsifiability** — every belief must be challengeable (unchallenged claims = dogma)
3. **Irreducibility** — beliefs decompose to atomic primitives (compound claims hide Logic Knots)
4. **Reconstructability** — every failed belief can be reconstructed (scope may narrow)
5. **Convergence** — S+R iteration always converges to Equilibrium E

---

## The Problem

AI coding agents produce knowledge claims (requirements, code, decisions) but have no
mechanism to assess their epistemic quality. Without governance:
- Requirements are vague, compound, or untestable
- Conflicting claims (Logic Knots) silently accumulate
- Confidence in critical requirements is never measured
- Decisions lack tamper-evident audit trails

specsmith solves this by making the governance layer epistemically aware: requirements
become BeliefArtifacts, audits run stress-tests, decisions seal to the trace vault.

## What specsmith Does

**For new projects:** `specsmith init` generates a complete epistemically-governed scaffold
with governance files, CI/CD, AEE belief registry, and agent integration files.

**For existing projects:** `specsmith import` generates governance overlay files without
modifying source code. Existing files are preserved.

**For AEE workflows:** `specsmith stress-test` runs adversarial challenges against
requirements. `specsmith epistemic-audit` runs the full AEE pipeline. `specsmith trace
seal` creates tamper-evident decision records.

**As a Python library:** `from epistemic import AEESession` — zero specsmith coupling,
works in any Python 3.10+ project (research, compliance, AI alignment, etc.).

**As an agentic client:** `specsmith run` — AEE-integrated REPL supporting Claude,
GPT, Gemini, and local Ollama models, with skills, hooks, and tool loops.

Every governed project follows: **propose → check → execute → verify → record**.

## VS Code Extension

The **specsmith AEE Workbench** VS Code extension brings the full specsmith workflow into your editor:

- **Multi-tab agent sessions** — one independent agent process per project, running in your right-side panel
- **Live model listing** — fetches current models from Anthropic, OpenAI, Gemini, Mistral, and local Ollama with GPU-aware context sizing
- **Ollama integration** — browse catalog, download models with progress, GPU VRAM detection, task-based model suggestions
- **Governance Panel** (`Ctrl+Shift+G`) — scaffold.yml form editor, governance file status, quick actions (audit/validate/doctor), AI prompt palette
- **API key management** — stored in OS credential store (Windows Credential Manager / macOS Keychain) via VS Code SecretStorage
- **Projects sidebar** — full file tree + governance docs for each project, right-click to open agent session
- **Chat history** — session history saved to `.specsmith/chat/`, replayed on re-open

```
# In VS Code: Ctrl+Shift+P → specsmith: New Agent Session
# Panel is on the right side (View → Open Secondary Side Bar)
```

**[→ specsmith-vscode on GitHub](https://github.com/BitConcepts/specsmith-vscode)**

---

## Install

**Recommended — global install via [pipx](https://pipx.pypa.io) (isolated, no dependency conflicts):**

```bash
pipx install specsmith                    # core CLI + epistemic library
pipx inject specsmith anthropic           # + Claude support
pipx inject specsmith openai             # + GPT / O-series support
pipx inject specsmith google-generativeai # + Gemini support
pipx inject specsmith PySide6            # + GUI (specsmith gui)
```

**Or with pip (into your active environment):**

```bash
pip install specsmith                # core
pip install "specsmith[anthropic]"  # + Claude
pip install "specsmith[openai]"     # + GPT/O-series
pip install "specsmith[gui]"        # + GUI
```

**Update:**

```bash
pipx upgrade specsmith     # pipx install
specsmith self-update      # pip install
```

## Quick Start

```bash
# New project
specsmith init

# Adopt an existing project
specsmith import --project-dir ./my-project

# Check governance health
specsmith audit --project-dir ./my-project

# Run AEE stress-test on requirements
specsmith stress-test --project-dir ./my-project

# Run full epistemic audit
specsmith epistemic-audit --project-dir ./my-project

# Start the agentic REPL (requires a provider installed)
specsmith run --project-dir ./my-project

# Run a single task non-interactively
specsmith run --task "run audit and fix issues"
```

### Using the epistemic library in any Python project

```python
from epistemic import AEESession

session = AEESession("my-project")
session.add_belief(
    artifact_id="HYP-001",
    propositions=["The API always returns valid JSON"],
    epistemic_boundary=["Valid auth token required"],
)
session.accept("HYP-001")
result = session.run()
print(result.summary())
```

See [epistemic library documentation](https://specsmith.readthedocs.io/en/stable/epistemic-library/) for full API reference and examples including linguistics research (glossa-lab), compliance pipelines, and AI alignment workflows.

### Starting an AI Agent Session

The universal pattern for any specsmith-governed project:

```
/agent AGENTS.md
```

This works in Warp, Claude Code, Cursor, and any agent that reads markdown context files. The agent loads AGENTS.md (the governance hub), reads LEDGER.md for session state, and picks up from the last recorded action.

## 50+ CLI Commands

| Command | Purpose |
|---------|---------|
| `init` | Scaffold a new epistemically-governed project |
| `import` | Adopt an existing project |
| `audit` | Drift detection and health checks |
| `stress-test` | AEE adversarial stress-tests on requirements |
| `epistemic-audit` | Full AEE pipeline (stress-test + certainty + recovery) |
| `belief-graph` | Render belief artifact dependency graph |
| `trace seal/verify/log` | Cryptographic decision sealing (STP-inspired) |
| `integrate <tool>` | Epistemic impact analysis before tool integration |
| `run` | Start AEE-integrated agentic REPL |
| `agent providers/tools/skills` | Configure agentic client |
| `validate` | Governance consistency checks |
| `export` | Compliance report with REQ↔TEST coverage |
| `architect` | Interactive architecture generation |
| `credits` | AI credit tracking, analysis, budgets |
| `exec / ps / abort` | Tracked process execution with timeouts |
| `commit / push / sync` | Governance-aware VCS operations |
| `req list/trace/gaps` | Requirement management |
| `ledger add/list/stats` | Change ledger management |

## 33 Project Types

**Software:** Python, Rust, Go, C/C++, .NET, JS/TS, mobile, monorepo, microservices, DevOps/IaC, data/ML, browser extensions.

**Hardware:** FPGA/RTL, Yocto BSP, PCB design, embedded systems.

**Documents:** Technical specifications, user manuals, research papers, API specifications, requirements management.

**Business/Legal:** Business plans, patent applications, legal/compliance frameworks.

Each type gets: tool-aware CI (correct lint/test/security/build tools), domain-specific directory structure, governance rules in AGENTS.md, and pre-populated requirements and test stubs.

## 40+ CLI Commands

| Command | Purpose |
|---------|---------|
| `init` | Scaffold a new governed project |
| `import` | Adopt an existing project (merge mode) |
| `audit` | Drift detection and health checks (`--fix` to auto-repair) |
| `architect` | Interactive architecture generation |
| `validate` | Governance consistency + H11 blocking-loop detection |
| `compress` | Archive old ledger entries |
| `upgrade` | Update governance to new spec version |
| `status` | CI/PR/alert status from VCS platform |
| `diff` | Compare governance against templates |
| `export` | Compliance report with REQ↔TEST coverage |
| `doctor` | Check if verification tools are installed |
| `self-update` | Update specsmith (channel-aware) |
| `credits` | AI credit tracking, analysis, budgets, and rate-limit pacing |
| `exec` / `ps` / `abort` | Tracked process execution with PID tracking and timeout |
| `commit` / `push` / `sync` | Governance-aware VCS operations |
| `branch` / `pr` | Strategy-aware branching and PR creation |
| `ledger` | Structured ledger add/list/stats |
| `req` | Requirements list/add/trace/gaps/orphans |
| `session-end` | End-of-session checklist |

## 7 Agent Integrations

AGENTS.md (cross-platform standard), Warp/Oz, Claude Code, GitHub Copilot, Cursor, Gemini CLI, Windsurf, Aider.

## 3 VCS Platforms

GitHub Actions, GitLab CI, Bitbucket Pipelines — all with tool-aware CI generated from the verification tool registry. Dependabot/Renovate configured per language ecosystem.

## Governance Rules (H1–H12)

specsmith-governed projects enforce 12 hard rules. Two were added in v0.2.3 for agentic workflows:

- **H11** — Every loop or blocking wait in agent-written scripts must have a deadline, a fallback exit, and a diagnostic message on timeout. `specsmith validate` enforces this automatically.
- **H12** — On Windows, multi-step automation goes into a `.cmd` file, not inline shell invocations or `.ps1` files.

See [Governance Model](https://specsmith.readthedocs.io/en/stable/governance/) for the full rule set.

## Proactive Rate Limit Pacing

specsmith ships a rolling-window scheduler that paces AI provider requests before dispatch:

- Built-in RPM/TPM profiles for OpenAI, Anthropic, and Google models (including wildcard fallbacks)
- Pre-dispatch budget check: sleeps until the 60-second window refills instead of overshooting
- Parses OpenAI-style `"Please try again in 10.793s"` messages and obeys them
- Adaptive concurrency: halved after a 429, gradually restored after consecutive successes
- Local overrides always take precedence over built-in defaults

```bash
specsmith credits limits defaults          # list built-in profiles
specsmith credits limits defaults --install  # merge into project config
specsmith credits limits status --provider openai --model gpt-5.4
```

See [Rate Limit Pacing](https://specsmith.readthedocs.io/en/stable/rate-limits/) for full details.

## Documentation

**[specsmith.readthedocs.io](https://specsmith.readthedocs.io)** — Full user manual with tutorials, command reference, project type details, tool registry, governance model, rate-limit pacing, troubleshooting.

## Links

- [PyPI](https://pypi.org/project/specsmith/)
- [Documentation](https://specsmith.readthedocs.io)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Specification](docs/AGENT-WORKFLOW-SPEC.md)
- [Security](SECURITY.md)

## License

MIT — Copyright (c) 2026 BitConcepts, LLC.
