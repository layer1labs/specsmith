# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **specsmith CLI tool** (`specsmith init`): interactive or YAML-driven project scaffold generation with Jinja2 templates, pydantic config validation, and 8 project types.
- **`specsmith audit`**: drift detection and health checks — governance file existence, REQ↔TEST coverage, ledger size/staleness, context bloat thresholds.
- **`specsmith validate`**: governance consistency checks — scaffold.yml validation, AGENTS.md reference integrity, requirement ID uniqueness, architecture↔requirements linkage.
- **`specsmith compress`**: ledger archival — moves old entries to `docs/ledger-archive.md`, keeps configurable recent entries.
- **`specsmith upgrade`**: re-renders governance files from templates when spec version bumps.
- **Agent integration adapters**: Warp/Oz (`.warp/skills/SKILL.md`), Claude Code (`CLAUDE.md`), Cursor (`.cursor/rules/governance.mdc`), GitHub Copilot (`.github/copilot-instructions.md`), with adapter registry.
- **36 tests** covering config, scaffolder, auditor, validator, compressor, and all integration adapters.
- **GitHub Actions CI**: lint (ruff), typecheck (mypy --strict), test (pytest, 3 OS × 3 Python), security audit (pip-audit).
- **Release workflow**: tag-triggered build (sdist + wheel) → GitHub Release artifacts (no PyPI yet).
- **Dependabot** for pip and GitHub Actions dependencies.
- **Pre-commit config**: ruff lint/format, trailing whitespace, YAML/TOML checks.
- **Docker local CI**: `Dockerfile.test` + `docker-compose.test.yml` for containerized lint/typecheck/test.
- Formal `docs/REQUIREMENTS.md` (37 requirements) and `docs/TEST_SPEC.md` (30 test cases) for specsmith itself.

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

[Unreleased]: https://github.com/BitConcepts/specsmith/compare/v0.1.0-alpha.1...HEAD
[0.1.0-alpha.1]: https://github.com/BitConcepts/specsmith/releases/tag/v0.1.0-alpha.1
