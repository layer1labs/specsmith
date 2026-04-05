# Ledger — specsmith

## Session 2026-04-01 — Initial CLI implementation

**Status:** Complete
**Scope:** Full CLI tool with 5 commands, 4 agent adapters, CI/CD, tests

### Proposal
Build specsmith CLI tool with: init (scaffold generation), audit (health checks),
validate (consistency), compress (ledger archival), upgrade (spec version migration).
Add agent integration adapters for Warp, Claude Code, Cursor, and Copilot.

Estimated cost: high

### Changes
- `src/specsmith/cli.py` — click CLI with init, audit, validate, compress, upgrade
- `src/specsmith/scaffolder.py` — Jinja2 template renderer with project type logic
- `src/specsmith/config.py` — pydantic ProjectConfig with 8 project types
- `src/specsmith/auditor.py` — governance file checks, REQ↔TEST coverage, ledger health
- `src/specsmith/validator.py` — scaffold.yml, AGENTS.md refs, REQ uniqueness
- `src/specsmith/compressor.py` — ledger archival with configurable thresholds
- `src/specsmith/upgrader.py` — governance template re-rendering on version bump
- `src/specsmith/integrations/` — base adapter + Warp, Claude Code, Cursor, Copilot
- `src/specsmith/templates/` — 30+ Jinja2 templates for governed scaffolds
- `.github/workflows/ci.yml` — lint + typecheck + test matrix + security audit
- `.github/workflows/release.yml` — tag-triggered build → GitHub Release
- `docs/REQUIREMENTS.md` — 37 formal requirements
- `docs/TEST_SPEC.md` — 30 test specifications

### Verification
- 36 tests passing (pytest)
- ruff lint: clean
- ruff format: clean
- mypy strict: clean
- CI: lint ✓, security ✓, typecheck pending (fix pushed)

### Open TODOs
- [x] Add VCS platform integrations (GitHub/GitLab/Bitbucket CLI)
- [x] Add Gemini, Windsurf, Aider agent adapters
- [x] Expand CLI runner test coverage
- [x] Self-host governance (this file)

## Session 2026-04-05 — AEE epistemic layer, agentic client, CI/CD, meta-governance

**Status:** Complete
**Branch:** develop
**Spec version:** 0.3.0 (switched from 0.3.0a1 → X.Y.Z.devN scheme)

### What was done

**Applied Epistemic Engineering (AEE) — core implementation:**
- `src/epistemic/` standalone library (7 modules, zero deps): BeliefArtifact, StressTester, FailureModeGraph, RecoveryOperator, CertaintyEngine, TraceVault, AEESession. `from epistemic import AEESession` works in any Python 3.10+ project.
- `src/specsmith/epistemic/` shim re-exporting from `epistemic` (backward compat)
- `src/specsmith/trace.py` — STP-inspired SHA-256 audit chain
- `ledger.py` — CryptoAuditChain (tamper-evident ledger entries)
- 8 new CLI commands: stress-test, epistemic-audit, belief-graph, trace seal/verify/log, integrate
- H13 hard rule (Epistemic Boundaries Required) in governance templates
- 4 new governance templates: epistemic-axioms, belief-registry, failure-modes, uncertainty-map
- 3 new project types: epistemic-pipeline, knowledge-engineering, aee-research
- 33 project types total (up from 30)
- 25 new tests, all passing

**Agentic client (`src/specsmith/agent/`):**
- `specsmith run` — AEE-integrated REPL (Anthropic, OpenAI, Gemini, Ollama; all optional extras)
- 20 specsmith commands as native LLM tools with epistemic contracts
- HookRegistry: H13 enforcement, ledger hints, context budget warning
- SKILL.md loader with domain priority
- Built-in profiles: planner, verifier, epistemic-auditor

**Issue resolutions (all closed):**
- #52: CreditBudget.enforcement_mode soft|hard, specsmith credits check
- #37: specsmith auth set/list/remove/check (OS keyring > file; tokens never logged)
- #17: specsmith workspace init/audit/export (workspace.yml multi-project)
- #16: specsmith watch (polling daemon, LEDGER.md staleness alerts)
- #10: specsmith patent search/prior-art (USPTO ODP API)
- #18: governance templates marketplace (deferred, plugin system is the foundation)

**CI/CD fixes:**
- 5 rounds of CI fixes: ruff SIM violations, mypy errors (auth.py, trace.py, runner.py, cli.py), test count assertions, sandbox upgrade test
- Dev-release workflow: RTD token validation, HTTP status logging, develop/latest build triggers
- RTD “latest”: PATCH /versions/latest/ with identifier=develop (HTTP 204) — root fix confirmed
- PyPI badge: removed dev badge (shields.io couldn’t show .devN reliably)
- v0.3.0a1 GitHub release/tag deleted; versioning changed to X.Y.Z.devN

**Meta-governance bootstrapping:**
- `scaffold.yml` created for specsmith itself (hand-crafted, enable_epistemic: true)
- west-env: specsmith import run, 14 governance files generated, spec_version 0.3.0, committed

**Documentation:**
- docs/site/aee-primer.md — 10-part comprehensive AEE guide
- docs/site/epistemic-library.md — standalone library API reference + glossa-lab examples
- docs/site/agent-client.md — specsmith run reference
- docs/site/index.md — AEE-first homepage
- README.md, AGENTS.md, mkdocs.yml, CHANGELOG.md all updated
- ECC reference cloned: C:\Users\trist\Development\BitConcepts\everything-claude-code

### Verification
- 25 new epistemic tests (all pass)
- ruff check + format: clean
- mypy strict: clean (0 errors in 62 files)
- CI: green (all 4 jobs pass)
- 0 open GitHub issues
- 0 security/dependabot alerts

### Open TODOs
- [ ] RTD latest: verify homepage shows AEE content after version identifier fix
- [ ] Yank 0.3.0a1 from PyPI (optional — pip install --pre gets 0.3.0a1 until 0.3.0 releases)
- [ ] glossa-lab: adopt epistemic library (AEESession for decipherment hypotheses)
- [ ] scaffolder.py: render epistemic templates for epistemic project types (foundation done, rendering hook pending)
- [ ] Release 0.3.0 stable when ready (merge develop → main, tag v0.3.0)

### Next step
Begin glossa-lab integration — AEESession for Indus hypothesis tracking. Separately, run specsmith import on cpac and cpsc-engine-python to extend governance to the full BitConcepts portfolio.

---

## Session 2026-04-02 — v0.2.0→v0.2.2 release cycle

**Status:** Complete
**Scope:** Major feature release + two patch releases

### Changes
- **v0.2.0**: Uppercase governance filenames, community templates (#42), AI credit tracking (#50/#51), architect command (#49), self-update, multi-language detection, dynamic versioning, VCS commands, ledger/req/test CLIs, plugin scaffold
- **v0.2.1**: Process abort/PID tracking (exec/ps/abort commands), language-specific templates (#41 — Rust, Go, JS/TS), RTD integration (#38), release workflow templates (#44), PyPI integration (#36), template refactor (#45), upgrade --full sync mechanism
- **v0.2.2**: Auto-fix AGENTS.md references on lowercase→uppercase migration, alternate path detection (docs/LEDGER.md, docs/architecture/**), case-insensitive architecture check, CI-gated dev releases

### Issues closed
- #36, #38, #41, #42, #44, #45 (closed), #55, #56 (filed)
- Created v0.3.0 milestone, assigned 6 remaining issues

### Verification
- 115 tests passing (pytest, 3 OS × 3 Python)
- ruff check + format: clean (src/ + tests/)
- mypy strict: clean
- CI: 19/19 checks pass on all PRs before merge
- CodeQL: 0 open alerts
- Dependabot: 0 open alerts

### Open TODOs
- [ ] #55: Fix governance table rendering on RTD (double pipe)
- [ ] #56: Document 15+ missing CLI commands in RTD
- [ ] #52: Credit budget cap enforcement
- [ ] #37: Secure API key management
- [ ] #10: USPTO/MCP patent integration
- [ ] #17: Multi-project workspace management

## 2026-04-05T15:25 — specsmith migration: 0.3.0 → 0.3.0a1.dev8
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `5a6995207163ba49...`
