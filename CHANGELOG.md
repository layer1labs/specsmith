# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **30 project types** (up from 20): added spec-document, user-manual, research-paper, business-plan, patent-application, legal-compliance, requirements-mgmt, api-specification, monorepo, browser-extension.
- **`specsmith export`**: generate compliance reports with REQ↔TEST coverage matrix, audit summary, tool status, and governance file inventory. Supports `--output` to save to file.
- **`specsmith import --guided`**: run guided architecture definition after importing an existing project.
- **Auditor auto-fix for CI configs**: `audit --fix` now generates missing CI configs from the tool registry.
- **Domain-specific templates**: patent applications get claim/spec/figure requirements and tests; legal projects get contract/regulatory starters; business plans get exec summary/financials starters; research papers get citation/methodology starters; API specs get endpoint/auth starters.
- **PyPI publishing**: release workflow now publishes to PyPI via trusted publishing (OIDC).
- **Read the Docs site**: comprehensive documentation at specsmith.readthedocs.io with 10 pages covering all commands, 30 types, tool registry, importing, configuration, governance, export, and contributing.
- **CI metadata for document languages**: markdown (pandoc), latex (texlive), openapi (node/spectral), protobuf.
- **Sandbox integration tests**: patent-application scaffold, Rust CLI scaffold, config inheritance, and export command tests.
- **110 tests** across 15 test files, all passing.

## [0.1.0-alpha.2] - 2026-04-01

### Added
- **specsmith CLI tool** with 9 commands: `init`, `import`, `audit`, `validate`, `compress`, `upgrade`, `status`, `diff`.
- **`specsmith import`**: walk an existing project, detect language/build/tests/CI, generate governance overlay (AGENTS.md, LEDGER.md, REQUIREMENTS.md, TEST_SPEC.md, architecture.md). Supports `--force` to overwrite existing files.
- **`specsmith init --guided`**: interactive architecture definition session that auto-generates REQ/TEST stubs and architecture.md from user-defined components.
- **Verification tool registry** (`tools.py`): maps all 20 project types to lint, typecheck, test, security, build, format, and compliance tools. Supports user overrides via `verification_tools` config field.
- **Tool-aware CI generation**: GitHub Actions, GitLab CI, and Bitbucket Pipelines generate correct tool commands per project type (not just Python). CI metadata for 13 languages including setup actions, Docker images, and cache keys.
- **20 project types** (up from 8): added web-frontend, fullstack-js, cli-rust, cli-go, cli-c, library-rust, library-c, dotnet-app, mobile-app, devops-iac, data-ml, microservices.
- **Project detection engine** (`importer.py`): detects language, build system, test framework, CI, governance files, modules, entry points, and VCS state from an existing project directory.
- **Auditor tool verification**: `specsmith audit` now checks that CI configs reference the expected verification tools for the project type.
- **Type-specific governance templates**: AGENTS.md and verification.md now include type-specific rules for Rust, Go, C/C++, web frontend, .NET, DevOps/IaC, data/ML, and microservices projects.
- **Mixed-language CI support**: projects with both Python and JS tools (e.g., backend-frontend) automatically get both runtime setups in CI.
- **Language-specific Dependabot ecosystems**: pip, cargo, gomod, npm, nuget, pub detected from project language.
- **Interactive prompts** for VCS platform, branching strategy, and agent integrations during `specsmith init`.
- **`specsmith status`**: pull CI status, dependency alerts, and open PRs from VCS platform CLI (gh/glab/bb).
- **`specsmith diff`**: compare governance files against what spec templates would generate.
- **`audit --fix`**: auto-repair missing governance files and compress oversized ledgers.
- **Config inheritance**: `extends` field in scaffold.yml to inherit org-level defaults.
- **7 agent integration adapters**: Warp/Oz, Claude Code, Cursor, Copilot, Gemini, Windsurf, Aider.
- **3 VCS platform integrations**: GitHub (`gh`), GitLab (`glab`), Bitbucket (`bb`) with CI/CD, dependency, and security config generation.
- **Domain-specific scaffold directories**: FPGA, Yocto, PCB, Embedded, Web, Rust, Go, C/C++, .NET, Mobile, DevOps, Data/ML, Microservices.
- **Branching strategy config**: gitflow, trunk-based, github-flow with tuning knobs.
- **98 tests** across 12 test files covering CLI, scaffolder, auditor, validator, compressor, integrations, VCS platforms, tool registry, and importer.
- **GitHub Actions CI**: lint (ruff), typecheck (mypy --strict), test (pytest, 3 OS × 3 Python), security audit (pip-audit).
- **Release workflow**: tag-triggered build (sdist + wheel) → GitHub Release artifacts.
- Dependabot, pre-commit, Docker local CI.
- SECURITY.md, MAINTAINERS.md, .github/CODEOWNERS.
- SPDX-License-Identifier: MIT headers on all source files.
- Self-hosted governance: AGENTS.md, LEDGER.md, CONTRIBUTING.md for specsmith itself.

### Changed
- **Windows scripts**: replaced all `.ps1` templates with `.cmd` for environment compatibility.
- **GitHub Actions**: bumped to `checkout@v6` + `setup-python@v6`.
- **Branch protection**: `main` branch protected via GitHub rulesets (no deletion, no force push).
- Gitflow branching with `develop` branch created and synced.

## [0.1.0-alpha.1] - 2026-03-31

### Added
- **Modular AGENTS.md architecture** (Section 24): focused hub (~100-150 lines) plus 6 delegated governance docs under `docs/governance/` (rules.md, workflow.md, roles.md, context-budget.md, verification.md, drift-metrics.md). Lazy-loaded per task type to minimize credit use.
- **Credit and token optimization** (Section 25): `Estimated cost:` field in proposals, `Token estimate:` field in ledger entries, lazy loading protocol, response economy rules, efficient verification ordering, credit-waste anti-patterns.
- **Drift detection and feedback loops** (Section 26): 5 health signals (consistency, ledger health, documentation currency, governance size, rule compliance), drift response protocol, ledger compression to `docs/ledger-archive.md`, `audit` command.
- **Execution safety and timeout protection** (Section 27): mandatory timeouts on all agent-invoked commands, non-interactive execution mandate, timeout handling protocol (kill → record → retry once → escalate), `scripts/exec.ps1` and `scripts/exec.sh` shim/wrapper layer, known hung-process patterns catalog.
- **Multi-agent coordination** (Section 28): agent identity in ledger entries, scope isolation, conflict detection, test separation principle.
- **FPGA / RTL project type** (Section 17.6): directory structure, constraint files as governance artifacts, synthesis → P&R → timing closure verification vocabulary, batch-only tool invocation mandate.
- **Yocto / embedded Linux BSP project type** (Section 17.7): meta-layer structure, KAS YAML as governance artifacts, build-time awareness in proposals, sstate/download cache management.
- **PCB / hardware design project type** (Section 17.8): schematic-review gate, BOM as governance artifact, ERC → DRC → fab verification pipeline, ECAD-MCAD sync documentation requirement.
- 15 new requirement component codes for FPGA (RTL, SIM, SYN, IMPL), embedded Linux (BSP, IMG, PKG, DTS, KRN), and PCB (SCH, PCB, BOM, FAB, MCAD) domains.
- Hard rule **H9 — Execution timeout required**: all agent commands must have timeouts.
- Anti-patterns #11 (hung processes) and #12 (credit waste).
- `audit` command in quick command reference (Section 22).
- Drift and health metrics added to compliance checklist (Section 23).
- `scripts/exec.ps1` and `scripts/exec.sh` added to recommended scripts (Section 13.2).

### Changed
- **Version** set to 0.1.0-alpha.1 (SemVer pre-release; will not reach 1.0.0 until production-ready).
- **Purpose statement** (Section 1) expanded: now covers software, firmware, FPGA/RTL, embedded Linux, and hardware projects.
- **AGENTS.md definition** (Section 2.1) restructured: must be kept small (~100-150 lines), serves as a hub referencing modular governance docs.
- **Authority hierarchy** (Section 3) updated: `docs/governance/*` files inherit AGENTS.md's authority via explicit delegation.
- **Proposal format** (Section 5) gained `Estimated cost:` field.
- **Ledger entry format** (Section 6) gained `Token estimate:` field.
- **Bootstrap procedure** (Section 18 Step 3) now creates `docs/governance/` directory with all 6 modular governance files.
- **Section 17 intro** updated to reference project types 17.5-17.8 covering hardware domains.

### Fixed
- **G1**: Bootstrap procedure now explicitly exempt from proposal requirement (H2) — was ambiguous in original.
- **G2**: Authority hierarchy no longer mislabels LEDGER.md as "lowest" when workflow.md and services.md are below it.
- **G3**: Added "Derivation vs. conflict resolution" paragraph clarifying requirements-vs-architecture precedence.
- **G4**: Library/SDK project type (17.4) now includes required `scripts/` directory.
- **G5**: Embedded/hardware project type (17.5) now explicitly references Section 2 and Section 13.2 instead of vague "same core structure."
- **G6**: Bootstrap ledger template TODOs now annotated "(adapt to selected project type)."
- **G7**: AGENTS.md adaptation guidance in bootstrap now specifies what "adapt" means concretely.
- **G8**: Added CLI and CMD component codes to requirements schema; noted list is extensible.
- **G9**: Session start file list now marks services.md as conditional ("if it exists").
- **G10**: Open TODOs format specified as `- [ ]` / `- [x]` checkbox syntax.

[Unreleased]: https://github.com/BitConcepts/specsmith/compare/v0.1.0-alpha.2...HEAD
[0.1.0-alpha.2]: https://github.com/BitConcepts/specsmith/compare/v0.1.0-alpha.1...v0.1.0-alpha.2
[0.1.0-alpha.1]: https://github.com/BitConcepts/specsmith/releases/tag/v0.1.0-alpha.1
