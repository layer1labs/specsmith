# specsmith

[![CI](https://github.com/BitConcepts/specsmith/actions/workflows/ci.yml/badge.svg)](https://github.com/BitConcepts/specsmith/actions/workflows/ci.yml)
[![Docs](https://readthedocs.org/projects/specsmith/badge/?version=latest)](https://specsmith.readthedocs.io/en/latest/)
[![PyPI version](https://img.shields.io/pypi/v/specsmith?color=blue)](https://pypi.org/project/specsmith/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Governed project scaffolds for AI-assisted development.**

> Intelligence proposes. Constraints decide. The ledger remembers.

---

## The Problem

AI coding agents are powerful but unstructured. Without governance, they skip verification, lose context between sessions, and produce inconsistent results. specsmith generates the governance layer — the rules, verification tools, CI pipelines, and documentation — that makes AI-assisted development auditable and repeatable.

## What specsmith Does

**For new projects:** `specsmith init` generates a complete project scaffold with governance files, CI/CD, verification tools, and agent integration files tailored to your project type.

**For existing projects:** `specsmith import` detects your project's language, build system, and test framework, then generates governance overlay files without modifying your source code. Existing files are preserved.

**For ongoing governance:** `specsmith audit` checks health, `specsmith export` generates compliance reports, `specsmith doctor` verifies your tools are installed.

Every governed project follows the closed-loop workflow: **propose → check → execute → verify → record**.

## Install

```bash
pip install specsmith
```

## Quick Start

```bash
specsmith init                                     # New project (interactive)
specsmith init --config scaffold.yml               # New project (from config)
specsmith import --project-dir ./my-project        # Adopt existing project
specsmith audit --project-dir ./my-project         # Health check
specsmith export --project-dir ./my-project        # Compliance report
specsmith doctor --project-dir ./my-project        # Tool check
```

## 30 Project Types

**Software:** Python, Rust, Go, C/C++, .NET, JS/TS, mobile, monorepo, microservices, DevOps/IaC, data/ML, browser extensions.

**Hardware:** FPGA/RTL, Yocto BSP, PCB design, embedded systems.

**Documents:** Technical specifications, user manuals, research papers, API specifications, requirements management.

**Business/Legal:** Business plans, patent applications, legal/compliance frameworks.

Each type gets: tool-aware CI (correct lint/test/security/build tools), domain-specific directory structure, governance rules in AGENTS.md, and pre-populated requirements and test stubs.

## 11 CLI Commands

| Command | Purpose |
|---------|---------|
| `init` | Scaffold a new governed project |
| `import` | Adopt an existing project (merge mode) |
| `audit` | Drift detection and health checks (`--fix` to auto-repair) |
| `validate` | Governance file consistency checks |
| `compress` | Archive old ledger entries |
| `upgrade` | Update governance to new spec version |
| `status` | CI/PR/alert status from VCS platform |
| `diff` | Compare governance against templates |
| `export` | Compliance report with REQ↔TEST coverage |
| `doctor` | Check if verification tools are installed |

## 7 Agent Integrations

AGENTS.md (cross-platform standard), Warp/Oz, Claude Code, GitHub Copilot, Cursor, Gemini CLI, Windsurf, Aider.

## 3 VCS Platforms

GitHub Actions, GitLab CI, Bitbucket Pipelines — all with tool-aware CI generated from the verification tool registry. Dependabot/Renovate configured per language ecosystem.

## Documentation

**[specsmith.readthedocs.io](https://specsmith.readthedocs.io)** — Full user manual with tutorials, command reference, project type details, tool registry, governance model, troubleshooting.

## Links

- [PyPI](https://pypi.org/project/specsmith/)
- [Documentation](https://specsmith.readthedocs.io)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Specification](docs/AGENT-WORKFLOW-SPEC.md)
- [Security](SECURITY.md)

## License

MIT — Copyright (c) 2026 BitConcepts, LLC.
