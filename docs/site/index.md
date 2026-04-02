# specsmith Documentation

**Forge governed project scaffolds from the Agentic AI Development Workflow Specification.**

specsmith generates project structures with built-in AI agent governance — the rules, verification tools, CI/CD pipelines, and documentation that keep AI coding assistants working within an auditable, structured workflow.

## Why specsmith?

AI coding agents (Warp/Oz, Claude Code, Cursor, Copilot, etc.) are powerful but unstructured. Without governance, they:

- Make changes without proposals or review
- Skip verification steps
- Lose context between sessions
- Generate inconsistent project structures

specsmith solves this by generating a **governance layer** that agents read and follow: propose before acting, verify before recording, log everything in the ledger.

## What You Get

When you run `specsmith init` or `specsmith import`, your project gets:

- **AGENTS.md** — The governance hub. Every AI agent reads this first. Contains authority hierarchy, type-specific rules, and pointers to modular governance files.
- **LEDGER.md** — Append-only record of all changes. The agent writes here after every task. This is how context persists across sessions.
- **docs/governance/** — Six modular files: rules, workflow, roles, context budget, verification standards, drift metrics. Loaded lazily to minimize token use.
- **docs/REQUIREMENTS.md** — Numbered, testable requirements. For patent projects, pre-populated with claim/specification/figure requirements. For API projects, endpoint/auth requirements.
- **docs/TEST_SPEC.md** — Test cases linked to requirements via `Covers: REQ-xxx` references. The audit command checks this linkage.
- **CI config** — GitHub Actions, GitLab CI, or Bitbucket Pipelines with the exact tools for your project type (not generic Python-only configs).
- **Dependency management** — Dependabot or Renovate configured for the correct package ecosystem.
- **Agent integration files** — Warp SKILL.md, CLAUDE.md, Copilot instructions, Cursor rules, etc.

!!! note "Documentation Versions"
    **Stable:** [specsmith.readthedocs.io/en/stable/](https://specsmith.readthedocs.io/en/stable/) — matches `pip install specsmith`
    **Dev (latest):** [specsmith.readthedocs.io/en/latest/](https://specsmith.readthedocs.io/en/latest/) — matches `pip install --pre specsmith`

## Quick Start

```bash
pip install specsmith

# New project (interactive)
specsmith init

# Adopt an existing project
specsmith import --project-dir ./my-project

# Check governance health
specsmith audit --project-dir ./my-project

# Generate compliance report
specsmith export --project-dir ./my-project
```

## Documentation Guide

| Section | What You'll Learn |
|---------|------------------|
| [Getting Started](getting-started.md) | Installation, first project, first import — with full walkthrough |
| [CLI Commands](commands.md) | Every command with all options, examples, and behavior details |
| [Project Types](project-types.md) | All 30 types with directory structures, tools, and governance rules |
| [Tool Registry](tool-registry.md) | How tool-aware CI works, what tools each type uses, how to override |
| [Importing Projects](importing.md) | How detection works, merge behavior, type inference logic |
| [Configuration](configuration.md) | Every scaffold.yml field explained with examples |
| [Governance Model](governance.md) | The closed-loop workflow, file hierarchy, modular governance |
| [Agent Integrations](agent-integrations.md) | How each AI agent reads governance files |
| [Doctor](doctor.md) | Checking if your tools are installed |
| [Export & Compliance](export.md) | Generating coverage reports, understanding the output |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |
| [Contributing](contributing.md) | Adding project types, code standards, PR process |
