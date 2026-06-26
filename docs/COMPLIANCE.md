# Compliance Report — specsmith

**Generated:** 2026-06-26

## Project Summary

- **Name**: specsmith
- **Type**: CLI tool (Python)
- **Language**: python
- **VCS Platform**: github
- **Spec Version**: 0.17.1

## Verification Tools

- **Lint**: ruff check
- **Typecheck**: mypy
- **Test**: pytest
- **Security**: pip-audit
- **Build**: none
- **Format**: ruff format

## Audit Summary

- **Passed**: 38
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
- ✓ Recommended file docs/ARCHITECTURE.md exists
- ✓ Recommended file docs/SPECSMITH.yml exists
- ✓ Recommended file CONTRIBUTING.md exists
- ✓ Recommended file LICENSE exists
- ✓ docs/requirements/*.yml exists
- ✓ docs/tests/*.yml exists
- ✓ Skipped: test spec file not found
- ✓ LEDGER.md has 242 lines (within 500 threshold)
- ✓ 0 open, 0 closed TODOs
- ✓ AGENTS.md: 191 lines
- ✓ docs/governance/RULES.md: 243 lines
- ✓ docs/governance/SESSION-PROTOCOL.md: 80 lines
- ✓ docs/governance/LIFECYCLE.md: 44 lines
- ✓ docs/governance/ROLES.md: 30 lines
- ✓ docs/governance/CONTEXT-BUDGET.md: 62 lines
- ✓ docs/governance/VERIFICATION.md: 43 lines
- ✓ docs/governance/DRIFT-METRICS.md: 54 lines
- ✓ Trace vault intact (2 seals)
- ✓ Phase 🚀 Release: 100% ready
- ✓ WI-6E21B031 risk=low gates satisfied
- ✓ WI-F78E9240 risk=low gates satisfied
- ✓ WI-9E6EA158 risk=low gates satisfied
- ✓ WI-05066482 risk=low gates satisfied
- ✓ WI-36FDC6DF risk=low gates satisfied
- ✓ WI-F3BD9283 risk=low gates satisfied
- ✓ WI-34CD3DC6 risk=low gates satisfied
- ✓ WI-325BC150 risk=low gates satisfied
- ✓ WI-0003C960 risk=low gates satisfied
- ✓ WI-6DC614CC risk=low gates satisfied

## Recent Activity

- `739ae80 chore: update project files`
- `c317ec9 fix(tests): update test_canonical_tests_md_exists for YAML-first mode`
- `ddb96c7 fix(compliance): fall back to JSON cache for YAML-first projects`
- `3b23b30 fix(audit): raise AGENTS.md default threshold 200→250 (template now 202 lines)`
- `11b0666 feat(bench): add SPECSMITH_DISPATCH multi-agent DAG condition (WI-AB55D02A)`
- `813bb12 merge: fix/agent-run-no-response → develop (silent no-response fix + provider visibility)`
- `0238e00 chore: update project files`
- `1e8f27e docs: update CHANGELOG [Unreleased], commands.md, index.md, esdb/changelog.md for post-0.17.1 features`
- `3eb53b9 chore: update project files`
- `fda6012 feat: m010 post-ESDB cleanup migration (WI-9F1AE964)`

**Contributors:**
- 604	Tristen Pierson
- 4	dependabot[bot]
- 1	Aqil Aziz

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
- **run_gcc**: Compile or build with GCC / G++. Pass compiler flags verbatim via *args*. Use *compiler* to select g++, gcc-12, etc.
  *Epistemic claims:* invokes compiler process; may produce build artifacts
- **run_arm_gcc**: Cross-compile for ARM bare-metal (arm-none-eabi-gcc / g++). Set *compiler* to 'arm-none-eabi-g++' for C++.
  *Epistemic claims:* invokes cross-compiler; produces .elf/.bin artifacts
- **run_aarch64_gcc**: Cross-compile for AArch64 Linux (aarch64-linux-gnu-gcc / g++).
  *Epistemic claims:* invokes cross-compiler; produces shared/static libraries
- **run_iar_compiler**: Build an IAR Embedded Workbench project via IarBuild command-line. Provide the .ewp *project_file* path.
  *Epistemic claims:* requires IAR Embedded Workbench installed; produces .out artifacts
- **run_intel_compiler**: Compile with Intel oneAPI (icx/icpx) or classic (icc/icpc) compilers. Use *compiler* to select the binary.
  *Epistemic claims:* requires Intel oneAPI or classic compiler installed
- **run_clang_format**: Run clang-format on source files. Use *in_place=True* to apply changes, or leave False to print the diff only.
  *Epistemic claims:* modifies source files in-place when in_place=True
- **run_clang_tidy**: Run clang-tidy static analysis on source files. Pass *checks* to filter specific lint rules.
  *Epistemic claims:* read-only analysis unless --fix is passed
- **run_vsg**: Run VSG (VHDL Style Guide) on .vhd/.vhdl files or directories. Use *fix=True* to apply automatic style corrections in place.
  *Epistemic claims:* modifies VHDL source files in-place when fix=True
- **specsmith_run**: Run any specsmith CLI command. Accepts slash-command form ('/specsmith save'), single-word verb shortcuts ('save', 'push', 'pull', 'load', 'sync', 'audit', 'status', 'watch', 'commit', 'validate', 'doctor', 'run'), or the full 'specsmith <args>' form. Use this for all specsmith governance operations.
  *Epistemic claims:* invokes specsmith CLI; may write to .specsmith/ and .chronomemory/; save/push/commit modify git history; load/pull may overwrite local governance state

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
- ✗ `docs/REQUIREMENTS.md`
- ✗ `docs/TESTS.md`
- ✓ `docs/ARCHITECTURE.md`
- ✓ `docs/governance/RULES.md`
- ✓ `docs/governance/SESSION-PROTOCOL.md`
- ✓ `docs/governance/LIFECYCLE.md`
- ✓ `docs/governance/ROLES.md`
- ✓ `docs/governance/VERIFICATION.md`
