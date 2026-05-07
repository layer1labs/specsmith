# Compliance Report — specsmith

**Generated:** 2026-05-07

## Project Summary

- **Name**: specsmith
- **Type**: CLI tool (Python)
- **Language**: python
- **VCS Platform**: github
- **Spec Version**: 0.10.1

## Verification Tools

- **Lint**: ruff check
- **Typecheck**: mypy
- **Test**: pytest
- **Security**: pip-audit
- **Build**: none
- **Format**: ruff format

## Requirements Coverage Matrix

**Coverage**: 0/0 (0%)


## Audit Summary

- **Passed**: 28
- **Failed**: 0
- **Fixable**: 0
- **Status**: Healthy

- ✓ Required file AGENTS.md exists
- ✓ Required file LEDGER.md exists
- ✓ Governance file docs/governance/RULES.md exists
- ✓ Governance file docs/governance/SESSION-PROTOCOL.md exists
- ✓ Governance file docs/governance/LIFECYCLE.md exists
- ✓ Governance file docs/governance/ROLES.md exists
- ✓ Governance file docs/governance/CONTEXT-BUDGET.md exists
- ✓ Governance file docs/governance/VERIFICATION.md exists
- ✓ Governance file docs/governance/DRIFT-METRICS.md exists
- ✓ Recommended file docs/REQUIREMENTS.md exists
- ✓ Recommended file docs/TESTS.md exists
- ✓ Recommended file docs/ARCHITECTURE.md exists
- ✓ Recommended file docs/SPECSMITH.yml exists
- ✓ Recommended file CONTRIBUTING.md exists
- ✓ Recommended file LICENSE exists
- ✓ All 0 accepted REQ(s) have test coverage
- ✓ LEDGER.md has 116 lines (within threshold)
- ✓ 0 open, 0 closed TODOs
- ✓ AGENTS.md: 130 lines
- ✓ docs/governance/RULES.md: 76 lines
- ✓ docs/governance/SESSION-PROTOCOL.md: 80 lines
- ✓ docs/governance/LIFECYCLE.md: 44 lines
- ✓ docs/governance/ROLES.md: 30 lines
- ✓ docs/governance/CONTEXT-BUDGET.md: 62 lines
- ✓ docs/governance/VERIFICATION.md: 43 lines
- ✓ docs/governance/DRIFT-METRICS.md: 54 lines
- ✓ Trace vault intact (2 seals)
- ✓ Phase 🚀 Release: 100% ready

## Recent Activity

- `bc7d860 feat: rename SPECSMITH.yml (all-caps), all 8 next-steps implemented`
- `c05b399 feat: governance structure overhaul + AI regulation requirements (REQ-206..220)`
- `27c9c06 feat: migrate PLANNED-REQUIREMENTS.md to REQ-130..REQ-205`
- `8ed9a9e fix: verification phase â€” all 5 checks now pass (100%)`
- `7c85e2f chore: normalize to LF, remove stale files, commit pending work`
- `d3f1b2d docs: rename Praxis -> Kairos, add Sister Repos section to AGENTS.md`
- `b448043 Merge pull request #96 from BitConcepts/develop`
- `b7fa720 chore(release): bump version to 0.10.1`
- `e44fce2 Merge pull request #95 from BitConcepts/develop`
- `9f961a0 feat(0.10.1): G1-G4 + C1 + H1-H4 follow-up sweep (#94)`

**Contributors:**
- 226	Tristen Pierson
- 3	dependabot[bot]

## AI System Inventory (REG-010)

### Agent Capabilities
- **run_shell**: Execute a shell command. Safety-checked; destructive commands are blocked.
  *Epistemic claims:* EXEC-001: no python -c for non-trivial code
- **read_file**: Read a text file from the repository.
  *Epistemic claims:* read-only: does not modify files
- **write_file**: Write content to a file (creates or overwrites).
  *Epistemic claims:* modifies filesystem: logged in audit chain
- **patch_file**: Apply a unified diff patch to a file.
  *Epistemic claims:* modifies filesystem: logged in audit chain
- **list_files**: List files matching a glob pattern in a directory.
  *Epistemic claims:* read-only: does not modify files
- **grep**: Search for a pattern in files.
  *Epistemic claims:* read-only: does not modify files
- **git_diff**: Show the git diff for the working tree.
  *Epistemic claims:* read-only: does not modify files
- **git_status**: Show git status for the working tree.
  *Epistemic claims:* read-only: does not modify files
- **run_tests**: Run the project test suite.
  *Epistemic claims:* may modify test artifacts but not source
- **open_url**: Fetch text content from a URL.
  *Epistemic claims:* network: reads external resources
- **search_docs**: Search documentation files in the repo.
  *Epistemic claims:* read-only: does not modify files
- **remember_project_fact**: Store a named fact in the local project index (.repo-index/facts.json).
  *Epistemic claims:* modifies .repo-index/facts.json only

### Risk Classification
- **EU AI Act tier**: GPAI (general-purpose; systemic risk assessment required if >10^25 FLOP)
- **NIST AI RMF**: GOVERN + MAP + MEASURE + MANAGE controls applied
- **Use-case scope**: software development governance; not Annex III high-risk

### Human Oversight Controls
- Preflight gate: all governed actions require human-language approval
- Kill-switch: `specsmith kill-session` halts all active agent sessions
- Escalation: `specsmith preflight --escalate-threshold <float>` gates low-confidence actions
- Retry budget: `agents_max_iterations` in docs/SPECSMITH.yml bounds self-improvement loops

## Governance File Inventory

- ✓ `AGENTS.md`
- ✗ `LEDGER.md`
- ✓ `docs/SPECSMITH.yml`
- ✗ `scaffold.yml`
- ✓ `docs/REQUIREMENTS.md`
- ✓ `docs/TESTS.md`
- ✓ `docs/ARCHITECTURE.md`
- ✓ `docs/governance/RULES.md`
- ✓ `docs/governance/SESSION-PROTOCOL.md`
- ✓ `docs/governance/LIFECYCLE.md`
- ✓ `docs/governance/ROLES.md`
- ✓ `docs/governance/VERIFICATION.md`
