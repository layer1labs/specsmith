# specsmith

**Forge governed project scaffolds from the Agentic AI Development Workflow Specification.**

> Intelligence proposes. Constraints decide. The ledger remembers.

specsmith is a CLI tool that generates full project scaffolds with built-in AI agent governance. It creates the file structure, CI/CD pipelines, governance documents, and agent integration files that AI coding assistants need to work within a structured, auditable workflow.

Every scaffolded project follows the closed-loop workflow: **propose → check → execute → verify → record**.

## Key Features

- **30 project types** — Python, Rust, Go, C/C++, JS/TS, .NET, FPGA, Yocto, PCB, mobile, DevOps, data/ML, microservices, patent applications, legal/compliance, business plans, technical specs, research papers, and more.
- **Tool-aware CI generation** — CI configs automatically use the correct lint, test, security, and build tools for each project type across GitHub Actions, GitLab CI, and Bitbucket Pipelines.
- **Project importer** — Adopt existing projects by detecting language, build system, test framework, and CI, then generating governance overlay files.
- **10 CLI commands** — `init`, `import`, `audit`, `validate`, `compress`, `upgrade`, `status`, `diff`, `export`.
- **7 agent integrations** — Warp/Oz, Claude Code, Cursor, GitHub Copilot, Gemini, Windsurf, Aider.
- **Compliance reporting** — `specsmith export` generates REQ↔TEST coverage matrices, audit summaries, and governance file inventories.

## Quick Install

```bash
pip install specsmith
```

## Quick Start

```bash
# Interactive scaffold
specsmith init

# Import an existing project
specsmith import --project-dir ./my-project

# Health check
specsmith audit --project-dir ./my-project
```

See [Getting Started](getting-started.md) for the full walkthrough.
