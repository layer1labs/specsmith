# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Governance RTD table rendering** (#55): rows 2–6 of the Modular Governance table in `docs/site/governance.md` started with `||` instead of `|`, breaking layout. Introduced during the uppercase filename migration.

### Added
- **RTD commands page complete** (#56): `docs/site/commands.md` now documents all 40+ commands — previously 13 of 40+ were documented. Added sections for `exec`/`ps`/`abort`, `commit`/`push`/`sync`/`branch`/`pr`, `session-end`, `update`, `apply`, `migrate-project`, `release`, `verify-release`, `ledger add/list/stats`, `req list/add/trace/gaps/orphans`, `plugin`, `serve`, and `credits limits`.
- **H11/H12 governance rules and blocking-loop enforcement** (#58): two new hard rules added to the `RULES.md` governance template. H11 requires every loop or blocking wait in agent-written scripts to have a deadline, fallback exit, and diagnostic message. H12 requires Windows multi-step automation to use `.cmd` files. `specsmith validate` now scans `.sh`/`.cmd`/`.ps1`/`.bash` files under `scripts/` and the project root and flags infinite-loop patterns without a recognised deadline/timeout guard.
- **Proactive per-model rate-limit pacing** (#59): `BUILTIN_PROFILES` constant ships conservative RPM/TPM defaults for OpenAI (gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo, o1, o1-mini, o3-mini, gpt-5.4, wildcard), Anthropic (claude-opus-4, claude-sonnet-4, claude-haiku-3-5, claude-3-5-sonnet, wildcard), and Google (gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash, gemini-2.5-pro, wildcard). Two new `credits limits` subcommands: `status` (rolling-window RPM/TPM/concurrency snapshot) and `defaults` (list or `--install` built-in profiles). Local overrides always take precedence over built-ins.
- **Rate Limit Pacing RTD page**: new `docs/site/rate-limits.md` documents the scheduler model, built-in profiles table, CLI commands, persistent state, and the Python API.
- **README updated**: new sections for Governance Rules (H11/H12) and Proactive Rate Limit Pacing with RTD links. Commands table expanded to all major command groups.

## [0.2.2]

### Fixed
- **Upgrade auto-fixes AGENTS.md references**: when `upgrade` renames governance files (lowercase→uppercase), it now rewrites path references in AGENTS.md, CLAUDE.md, GEMINI.md, SKILL.md, and all agent config files automatically.
- **Alternate path detection**: auditor and upgrader now find LEDGER.md at `docs/LEDGER.md` and architecture docs in subdirectories (e.g. `docs/architecture/`). No more false "missing" reports or duplicate stub creation.
- **Case-insensitive architecture check**: `docs/ARCHITECTURE.md` recommended check now works regardless of filename casing.
- **CI-gated dev releases**: dev-release workflow now runs full test suite (ruff check+format, mypy, pytest) before PyPI publish.

## [0.2.1] - 2026-04-02

### Added
- **Process execution with PID tracking**: `specsmith exec`, `specsmith ps`, `specsmith abort` — cross-platform (Windows taskkill / POSIX SIGTERM+SIGKILL) process tracking and abort. PID files in `.specsmith/pids/`.
- **`specsmith upgrade --full`**: full sync of infrastructure files — regenerates exec shims, CI configs, agent integrations. Creates missing community/config files. Safe: never overwrites user docs.
- **Language-specific scaffold templates** (#41): Rust (Cargo.toml, main.rs), Go (go.mod, main.go), JS/TS (package.json for web-frontend, fullstack-js).
- **ReadTheDocs templates** (#38): `.readthedocs.yaml` and `mkdocs.yml` for Python/doc projects.
- **Release workflow templates** (#44): `.github/workflows/release.yml` with test gate, language-aware build, GitHub Release, PyPI OIDC publish.
- **PyPI integration** (#36): OIDC-based trusted publishing via release workflow template.

### Changed
- **Template directory restructured** (#45): `pyproject.toml.j2` moved to `python/`. Templates organized into `python/`, `rust/`, `go/`, `js/`, `community/`, `governance/`, `docs/`, `scripts/`, `workflows/`.
- **CI-gated releases**: both dev-release and stable release workflows now run full test suite (ruff check+format, mypy, pytest) before PyPI publish.
- Exec shims (`exec.cmd`, `exec.sh`) now write PID files for `specsmith ps`/`specsmith abort`.

## [0.2.0] - 2026-04-02

### Added
- **Community templates** (#42): `CONTRIBUTING.md`, `LICENSE` (MIT/Apache-2.0), `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/` (bug report + feature request). Config fields: `license` (default MIT), `community_files` list.
- **AI credit tracking** (#50): `specsmith credits` subcommand group — record, summary, report, analyze, budget. Tracks tokens/cost per session, model, provider, and task. JSON storage at `.specsmith/credits.json`.
- **Credit spend analysis** (#51): `specsmith credits analyze` detects model inefficiency, token waste, governance bloat, cost trends. Generates optimization recommendations with estimated savings.
- **Credit budget/watermarks**: `specsmith credits budget --cap 50 --watermarks 5,10,25,50`. Monthly caps, alert thresholds, watermark notifications.
- **Auto-init credit tracking**: `init`, `import`, and `upgrade` all create `.specsmith/credit-budget.json` with unlimited default budget. `.specsmith/` gitignored.
- **`specsmith architect`** (#49): interactive architecture generation — scans project, interviews user about components/data flow/deployment, generates rich `docs/ARCHITECTURE.md`.
- **`specsmith self-update`**: auto-detects channel (stable/dev), supports `--channel` override and `--version` pinning.
- **Multi-language detection**: importer detects and reports all significant languages (primary + secondary).
- **Dynamic versioning**: `__version__` reads from `importlib.metadata`. Docs use `{{ version }}` hook. Tests are version-agnostic.
- **Dev-release workflow for managed projects** (#35): gitflow + GitHub + Python generates `.github/workflows/dev-release.yml`.
- **Type-specific templates**: .gitattributes (#39) for 15 language types, .gitignore (#40) expanded for all 30 types, .editorconfig (#43) with per-language indent settings.
- **Yocto/bitbake/devicetree/markdown**: `.bbclass`, `.inc`, `.dts`, `.dtsi` in language detection; `kas.yml` build system; enhanced CI metadata.
- **No-hardcoded-versions rule** (H10): governance template and WARP rule.
- **Agent credit instructions**: Warp and Claude adapters include credit recording commands.
- **Session-end credit summary**: `session-end` shows total spend and budget alerts.
- **VCS commands**: `specsmith commit`, `push`, `sync`, `branch`, `pr`, `session-end` for governed git workflows.
- **Structured ledger CLI**: `specsmith ledger add/list/stats` for append-only change tracking.
- **Requirements CLI**: `specsmith req list/add/trace/coverage` for requirements management.
- **Test gap analysis**: `specsmith test gaps/orphans/summary` for REQ↔TEST coverage.
- **Plugin system scaffold**: `specsmith plugin list`, entry-point-based extensibility.

### Fixed
- **Import with large AGENTS.md** (#46): broader keyword extraction, diff marker stripping, paragraph dedup, existing doc detection.
- **UnboundLocalError on import** with existing docs: scoping fix for REQUIREMENTS/TEST_SPEC/architecture skip logic.
- **Audit false positive**: architecture docs found in subdirectories (e.g., `docs/architecture/DESIGN.md`).
- **`audit --fix`** now generates missing recommended files (ARCHITECTURE.md from scan, REQUIREMENTS.md, TEST_SPEC.md stubs).
- **Topic-aware section classification** (#47): body content keywords route sections to correct governance files.
- **Type-specific audit thresholds** (#48): FPGA/embedded get higher limits (rules=1000, verification=600).

### Changed
- **Uppercase governance filenames**: all scaffolded markdown files use uppercase stems (RULES.md, WORKFLOW.md, ROLES.md, CONTEXT-BUDGET.md, VERIFICATION.md, DRIFT-METRICS.md, ARCHITECTURE.md). Upgrader auto-migrates legacy lowercase filenames on both case-sensitive and case-insensitive filesystems.
- Auditor now recommends `CONTRIBUTING.md` and `LICENSE`.
- RTD default version set to `stable`, default branch set to `develop`.
- Docs version references use dynamic `{{ version }}` instead of hardcoded strings.
- `init.py.j2` template for managed projects uses `importlib.metadata` pattern.
- Governance file size thresholds raised globally (rules=800, verification=400).
- Yocto toolset: added `testimage`, `yocto-check-layer` compliance.
- Release workflow now runs full test suite before building.

## [0.1.3] - 2026-04-01

### Fixed
- **PyPI sidebar links**: added Documentation (specsmith.readthedocs.io) and Issues (GitHub) to project URLs.
- **PyPI badge**: switched to cache-busting shields.io URL.

## [0.1.2] - 2026-04-01

### Fixed
- **PyPI classifier**: updated from "Development Status :: 3 - Alpha" to "Production/Stable".
- **Stale alpha references**: removed `--pre` flag text and alpha-period notes from getting-started.md and troubleshooting.md.

### Added
- **Release workflow guide** (`docs/site/releasing.md`): complete gitflow release process with pre-release checklist, post-release verification, version locations (5 places), and lessons learned.
- **WARP rule**: added release checks (classifier, stale versions, install commands) to `.warp/rules/documentation-updates.md`.

## [0.1.1] - 2026-04-01

### Security
- **Fix incomplete URL substring sanitization** (CodeQL alert #1): VCS platform detection in the importer now uses proper URL host parsing (`urllib.parse.urlparse` for HTTPS, explicit host extraction for SSH remotes) instead of substring matching. Prevents potential misidentification from spoofed hostnames.

## [0.1.0] - 2026-04-01

### Added
- **11 CLI commands**: `init`, `import`, `audit`, `validate`, `compress`, `upgrade`, `status`, `diff`, `export`, `doctor`.
- **30 project types** across 6 categories: software (Python, Rust, Go, C/C++, .NET, JS/TS, mobile, monorepo, microservices, DevOps, data/ML, browser extension), hardware (FPGA, Yocto, PCB, embedded), documents (spec, manual, paper, API spec, requirements mgmt), business/legal (business plan, patent, legal/compliance).
- **Verification tool registry**: maps each type to lint/typecheck/test/security/build/format/compliance tools with CI metadata for 16 languages.
- **Tool-aware CI generation**: GitHub Actions, GitLab CI, Bitbucket Pipelines with correct tools per project type. Mixed-language support (Python+JS auto-detects Node.js).
- **Project importer**: `specsmith import` detects language, build system, test framework, CI, governance, modules, and entry points. Merge mode preserves existing files.
- **`specsmith export`**: compliance reports with REQ↔TEST coverage matrix, audit summary, git activity, tool status, governance inventory.
- **`specsmith doctor`**: checks if verification tools are installed on PATH.
- **`specsmith init --guided`**: interactive architecture definition with REQ/TEST stub generation.
- **Auditor**: 6 health checks (files, REQ↔TEST, ledger, governance size, tool config, consistency). `--fix` auto-repairs missing files and CI configs.
- **Domain-specific templates**: patent claims/spec/figures, legal contracts/regulatory, business exec-summary/financials, research citations/methodology, API endpoints/auth.
- **7 agent integrations**: AGENTS.md, Warp/Oz, Claude Code, Cursor, Copilot, Gemini, Windsurf, Aider.
- **3 VCS platforms**: GitHub (`gh`), GitLab (`glab`), Bitbucket (`bb`) with CI/CD, dependency management (Dependabot/Renovate per ecosystem), and status checks.
- **Config inheritance**: `extends` field in scaffold.yml for org-level defaults.
- **Type-specific .gitignore**: Rust, Go, Node, Kotlin, .NET, KiCad, FPGA, Zephyr, LaTeX, Terraform patterns.
- **Type-specific governance rules**: 20+ project types have tailored AGENTS.md rules.
- **Read the Docs**: 13-page user manual at specsmith.readthedocs.io.
- **PyPI publishing**: automated via trusted publishing (OIDC).
- **GitHub infrastructure**: issue templates (bug, feature, new type), PR template, Discussions, 12 labels.
- **Self-governance**: 74 requirements, 113 tests, 100% REQ↔TEST coverage, audit healthy (9/9).
- **`python -m specsmith`** supported via `__main__.py`.

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

[Unreleased]: https://github.com/BitConcepts/specsmith/compare/v0.2.2...HEAD
[0.2.3-dev]: https://github.com/BitConcepts/specsmith/compare/v0.2.2...develop
[0.2.2]: https://github.com/BitConcepts/specsmith/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/BitConcepts/specsmith/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/BitConcepts/specsmith/compare/v0.1.3...v0.2.0
[0.1.3]: https://github.com/BitConcepts/specsmith/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/BitConcepts/specsmith/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/BitConcepts/specsmith/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/BitConcepts/specsmith/compare/v0.1.0-alpha.2...v0.1.0
[0.1.0-alpha.2]: https://github.com/BitConcepts/specsmith/compare/v0.1.0-alpha.1...v0.1.0-alpha.2
[0.1.0-alpha.1]: https://github.com/BitConcepts/specsmith/releases/tag/v0.1.0-alpha.1
