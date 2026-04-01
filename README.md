# specsmith

[![CI](https://github.com/BitConcepts/specsmith/actions/workflows/ci.yml/badge.svg)](https://github.com/BitConcepts/specsmith/actions/workflows/ci.yml)
[![Docs](https://readthedocs.org/projects/specsmith/badge/?version=latest)](https://specsmith.readthedocs.io/en/latest/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Forge governed project scaffolds from the Agentic AI Development Workflow Specification.

> Intelligence proposes. Constraints decide. The ledger remembers.

---

## What is specsmith?

`specsmith` is a CLI tool that generates full project scaffolds with built-in AI agent governance. It creates the file structure, CI/CD pipelines, governance documents, and agent integration files that AI coding assistants need to work within a structured, auditable workflow.

Every scaffolded project follows the closed-loop workflow: **propose → check → execute → verify → record**.

## Install

```bash
pip install specsmith
```

From source:

```bash
git clone https://github.com/BitConcepts/specsmith.git
cd specsmith
pip install -e ".[dev]"
```

## Quick Start

```bash
# Interactive scaffold
specsmith init

# From config file
specsmith init --config scaffold.yml --no-git

# Guided scaffold with architecture definition
specsmith init --guided

# Import an existing project (generate governance overlay)
specsmith import --project-dir ./my-existing-project
specsmith import --project-dir ./my-existing-project --force

# Health checks on an existing governed project
specsmith audit --project-dir ./my-project
specsmith validate --project-dir ./my-project

# Ledger maintenance
specsmith compress --project-dir ./my-project

# Upgrade governance to newer spec version
specsmith upgrade --spec-version 0.2.0 --project-dir ./my-project

# VCS platform status (CI, alerts, PRs)
specsmith status --project-dir ./my-project

# Compare governance files against templates
specsmith diff --project-dir ./my-project
```

## Commands

| Command | Description |
|---------|-------------|
| `specsmith init` | Scaffold a new governed project (interactive or YAML-driven) |
| `specsmith init --guided` | Scaffold with interactive architecture definition (REQ/TEST stub generation) |
| `specsmith import` | Import an existing project and generate governance overlay |
| `specsmith audit [--fix]` | Drift detection and health checks; `--fix` auto-repairs missing files and oversized ledgers |
| `specsmith validate` | Governance consistency (scaffold.yml, AGENTS.md refs, REQ uniqueness, arch↔req linkage) |
| `specsmith compress` | Archive old ledger entries to `docs/ledger-archive.md` |
| `specsmith upgrade` | Re-render governance files for a new spec version |
| `specsmith status` | Show CI status, dependency alerts, and open PRs from VCS platform CLI |
| `specsmith diff` | Compare governance files against what spec templates would generate |

## Project Types

specsmith supports 30 project types, each with type-specific directory structures, CI tooling, and governance rules.
See [full project types reference](https://specsmith.readthedocs.io/project-types/) for details.

| # | Type | Spec Section | Verification Tools |
|---|------|-------------|--------------------|
| 1 | Python backend + web frontend | 17.1 | ruff, mypy, pytest, pip-audit |
| 2 | Python backend + web frontend + tray | 17.2 | ruff, mypy, pytest, pip-audit |
| 3 | CLI tool (Python) | 17.3 | ruff, mypy, pytest, pip-audit |
| 4 | Library / SDK (Python) | 17.4 | ruff, mypy, pytest, pip-audit |
| 5 | Embedded / hardware | 17.5 | clang-tidy, cppcheck, ctest, flawfinder |
| 6 | FPGA / RTL | 17.6 | vsg, verilator, ghdl, cocotb |
| 7 | Yocto / embedded Linux BSP | 17.7 | oelint-adv, bitbake |
| 8 | PCB / hardware design | 17.8 | drc-check, erc-check, kicad-cli |
| 9 | Web frontend (SPA) | 17.9 | eslint, tsc, vitest, prettier |
| 10 | Fullstack JS/TS | 17.10 | eslint, tsc, vitest, jest |
| 11 | CLI tool (Rust) | 17.11 | clippy, cargo check/test/audit, rustfmt |
| 12 | CLI tool (Go) | 17.12 | golangci-lint, go test, govulncheck |
| 13 | CLI tool (C/C++) | 17.13 | clang-tidy, cppcheck, ctest, clang-format |
| 14 | Library / crate (Rust) | 17.14 | clippy, cargo check/test/audit, rustfmt |
| 15 | Library (C/C++) | 17.15 | clang-tidy, cppcheck, ctest, clang-format |
| 16 | .NET / C# application | 17.16 | dotnet format/test/audit |
| 17 | Mobile app | 17.17 | flutter analyze/test, eslint |
| 18 | DevOps / IaC | 17.18 | tflint, ansible-lint, tfsec, checkov |
| 19 | Data / ML pipeline | 17.19 | ruff, mypy, pytest, pip-audit |
| 20 | Microservices | 17.20 | ruff, eslint, pytest, jest, docker compose |
| 21 | Technical specification | 17.21 | vale, markdownlint, cspell, pandoc |
| 22 | User manual / documentation | 17.22 | vale, markdownlint, cspell, sphinx |
| 23 | Research paper / white paper | 17.23 | vale, cspell, chktex, pdflatex |
| 24 | Business plan / proposal | 17.24 | vale, cspell, prettier, pandoc |
| 25 | Patent application | 17.25 | vale, cspell, pandoc, claim-ref-check |
| 26 | Legal / compliance | 17.26 | vale, cspell, pandoc, regulation-ref-check |
| 27 | Requirements management | 17.27 | vale, markdownlint, req-trace |
| 28 | API specification | 17.28 | spectral, buf lint, schemathesis |
| 29 | Monorepo (multi-package) | 17.29 | eslint, ruff, nx/turbo, npm audit |
| 30 | Browser extension | 17.30 | eslint, web-ext lint, tsc, vitest |

## Agent Integrations

specsmith generates agent-specific governance files so AI assistants understand your project's rules:

| Agent | Generated File |
|-------|---------------|
| **AGENTS.md** (cross-tool standard) | `AGENTS.md` (always) |
| Warp / Oz | `.warp/skills/SKILL.md` |
| Claude Code | `CLAUDE.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Cursor | `.cursor/rules/governance.mdc` |
| Gemini CLI | `GEMINI.md` |
| Windsurf | `.windsurfrules` |
| Aider | `.aider.conf.yml` |

## VCS Platform Support

CI configs are **tool-aware** — generated from the verification tool registry per project type.

| Platform | CLI | CI Config | Dependency Mgmt | Security |
|----------|-----|-----------|-----------------|----------|
| **GitHub** | `gh` | GitHub Actions | Dependabot (pip/cargo/gomod/npm/nuget) | Tool-specific per type |
| **GitLab** | `glab` | `.gitlab-ci.yml` | Renovate | Tool-specific per type |
| **Bitbucket** | `bb` | Bitbucket Pipelines | Renovate | Tool-specific per type |

## Branching Strategy

Configure one of three branching strategies per project:

- **gitflow** (default) — `main` + `develop` + feature/release/hotfix branches
- **trunk-based** — single `main` with short-lived feature branches
- **github-flow** — `main` + feature branches with PR-based workflow

Branch protection (required reviews, CI checks, no force push) is configurable.

## Configuration

Projects are configured via `scaffold.yml`:

```yaml
name: my-project
type: cli-python
platforms: [windows, linux, macos]
language: python
vcs_platform: github
branching_strategy: gitflow
require_pr_reviews: true
required_approvals: 1
require_ci_pass: true
integrations: [agents-md, warp, claude-code]
```

| `specsmith export` | Generate compliance report (REQ coverage, audit summary, tool status) |

## Documentation

Full documentation: [specsmith.readthedocs.io](https://specsmith.readthedocs.io)

## Specification

See [`docs/AGENT-WORKFLOW-SPEC.md`](docs/AGENT-WORKFLOW-SPEC.md) for the complete workflow specification.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and guidelines.

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## License

MIT — Copyright (c) 2026 BitConcepts, LLC. See [LICENSE](LICENSE).
