# specsmith Documentation

**Applied Epistemic Engineering toolkit for AI-assisted development.**

> Intelligence proposes. Constraints decide. The ledger remembers.

specsmith treats belief systems like code: **codable, testable, and deployable**. It scaffolds
epistemically-governed projects, stress-tests requirements as BeliefArtifacts, runs
cryptographically-sealed trace vaults, and orchestrates AI agents under formal AEE governance.

It also co-installs the **standalone `epistemic` Python library** for direct use in any project:

```python
from epistemic import AEESession          # zero deps, works anywhere
session = AEESession("my-project")
session.add_belief("HYP-001", ["The hypothesis holds"])
result = session.run()
print(result.summary())
```

## What is Applied Epistemic Engineering?

AEE treats requirements, decisions, and hypotheses like code:

- **Codable** — every claim is a `BeliefArtifact` with propositions and explicit epistemic boundaries
- **Testable** — `StressTester` applies 8 adversarial challenges to surface failure modes and Logic Knots
- **Deployable** — beliefs that survive stress-testing are sealed with cryptographic proof (`TraceVault`)

The 4-step AEE core method: **Frame → Disassemble → Stress-Test → Reconstruct**

## Why specsmith?

AI agents produce knowledge claims constantly — requirements, architecture decisions, test results — but have no mechanism to assess their epistemic quality. Without AEE governance:

- Requirements are vague, compound, or untestable
- Conflicting claims (Logic Knots) silently accumulate
- Critical decisions lack tamper-evident audit trails
- Agent context is lost between sessions

specsmith provides the **governance + epistemic layer** that makes AI-assisted development auditable, repeatable, and epistemically sound.

## What You Get

When you run `specsmith init` or `specsmith import`, your project gets:

**AEE Epistemic Layer:**

- **`epistemic` library** — zero-dep Python library, `from epistemic import AEESession` works anywhere
- **`specsmith stress-test`** — adversarial challenges on every requirement (8 challenge categories)
- **`specsmith epistemic-audit`** — full AEE pipeline: certainty scores, logic knot detection, recovery proposals
- **`specsmith trace seal/verify`** — tamper-evident SHA-256 decision audit chain
- **Epistemic governance templates** — belief-registry.md, failure-modes.md, uncertainty-map.md

**Governance Infrastructure:**

- **AGENTS.md** — governance hub read by every AI agent; includes H13 (epistemic boundaries required)
- **LEDGER.md** — SHA-256-chained append-only record; the sole authority for session continuity
- **docs/governance/** — modular rules, workflow, roles, context budget, verification, drift metrics
- **docs/REQUIREMENTS.md** — requirements parseable as `BeliefArtifact` instances
- **CI config** — GitHub Actions, GitLab CI, Bitbucket Pipelines with correct tools per project type

**Agentic Client:**

- **`specsmith run`** — AEE-integrated REPL (Anthropic, OpenAI, Gemini, Ollama)
- **Skills** — SKILL.md loader with domain priority; built-in profiles: planner, verifier, epistemic-auditor
- **Hooks** — H13 enforcement, ledger hints, context budget alerts

!!! note "Documentation Versions"
    **Stable:** [specsmith.readthedocs.io/en/stable/](https://specsmith.readthedocs.io/en/stable/) — matches `pip install specsmith`
    **Dev (latest):** [specsmith.readthedocs.io/en/latest/](https://specsmith.readthedocs.io/en/latest/) — matches `pip install --pre specsmith`

## The AEE Workflow — 7 Phases

specsmith tracks your project through the full AEE development cycle:

```
🌱 Inception → 🏗 Architecture → 📋 Requirements → ✅ Test Spec
   → ⚙ Implementation → 🔬 Verification → 🚀 Release
```

```bash
specsmith phase          # show current phase + readiness checklist
specsmith phase next     # advance to next phase (checks prerequisites first)
specsmith phase list     # list all 7 phases
```

The active phase is shown in the Kairos Governance panel as a colored pill with readiness % and a Next Phase button.

## Kairos — Recommended Terminal Client

**[Kairos](https://github.com/BitConcepts/kairos)** is the recommended client for specsmith — a fully local, governance-ready terminal with zero cloud dependencies.

- **Governance Tools Panel** — live compliance controls, kill-switch, permission profile, audit log viewer
- **Context window fill indicator** — real-time fill bar; auto-compression at 80%; hard 15% ceiling
- **AI Providers table** — bucket score columns (R/C/L) sourced from HF leaderboard sync
- **ESDB, Skills, Eval, MCP pages** — full specsmith feature surface under Settings → Specsmith
- **BYOE** — any OpenAI-compatible endpoint; defaults to local specsmith on `127.0.0.1:7700`
- **Zero telemetry, zero login** — credentials stay local; no account required

```bash
cargo run --release --bin kairos   # build and run from source
```

**[→ Kairos on GitHub](https://github.com/BitConcepts/kairos)**

!!! note "VS Code Extension deprecated"
    The specsmith VS Code extension has been deprecated in favour of Kairos. Existing installs continue to work but will not receive new features.

## Quick Start

```bash
pipx install specsmith            # recommended: isolated install
pip install specsmith[anthropic]  # or via pip + Claude support

# New project
specsmith init

# Adopt an existing project
specsmith import --project-dir ./my-project

# Check current AEE workflow phase
specsmith phase

# Run AEE stress-test on requirements
specsmith stress-test --project-dir ./my-project

# Full epistemic audit (certainty + logic knots + recovery)
specsmith epistemic-audit --project-dir ./my-project

# Start agentic REPL (local Ollama, no API key needed)
specsmith run --provider ollama --model qwen2.5:14b

# Check governance health
specsmith audit --project-dir ./my-project
```

### Using the epistemic library

```python
from epistemic import AEESession, ConfidenceLevel, BeliefStatus

session = AEESession("my-project", threshold=0.7)
session.add_belief(
    artifact_id="REQ-API-001",
    propositions=["The API returns HTTP 200 for valid requests"],
    epistemic_boundary=["Platform: all", "Auth: JWT required"],
    status=BeliefStatus.ACCEPTED,
)
session.add_evidence("REQ-API-001", "Integration test suite passes")
result = session.run()
print(result.summary())
```

Works in any Python 3.10+ project. See [epistemic Library Reference](epistemic-library.md) for full API.

## Documentation Guide

| Section | What You'll Learn |
|---------|------------------|
| [Getting Started](getting-started.md) | Installation, first project, first import — full walkthrough |
| [AEE Primer](aee-primer.md) | Applied Epistemic Engineering from zero to productive (10 parts) |
| [epistemic Library](epistemic-library.md) | Standalone library API reference + integration examples |
| [Agentic Client](agent-client.md) | `specsmith run` — multi-provider REPL, skills, hooks, model routing |
| [CLI Commands](commands.md) | Every command with all options, examples, and behavior |
| [Project Types](project-types.md) | All 33 types with directory structures, tools, and governance rules |
| [Tool Registry](tool-registry.md) | How tool-aware CI works, what tools each type uses, how to override |
| [Importing Projects](importing.md) | How detection works, merge behavior, type inference logic |
| [Configuration](configuration.md) | Every scaffold.yml field explained with examples |
| [Governance Model](governance.md) | The closed-loop workflow, file hierarchy, modular governance |
| [YAML Governance](yaml-governance.md) | YAML-first governance: domain files, sync pipeline, strict validation, migration |
| [Export & Compliance](export.md) | Generating coverage reports, understanding the output |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |
| [Contributing](contributing.md) | Adding project types, code standards, PR process |
