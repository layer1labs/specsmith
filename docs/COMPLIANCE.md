# Compliance Report — specsmith

**Generated:** 2026-07-13

## Project Summary

- **Name**: specsmith
- **Type**: python
- **Language**: python
- **VCS Platform**: github
- **Spec Version**: 0.22.2

## Verification Tools

- **Lint**: ruff check
- **Typecheck**: mypy
- **Test**: pytest
- **Security**: pip-audit
- **Build**: none
- **Format**: ruff format

## Audit Summary

- **Passed**: 74
- **Failed**: 1
- **Fixable**: 0
- **Status**: Issues found

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
- ✓ axioms.yaml valid (m001 content-blob, kind=axioms)
- ✓ context-budget.yaml valid (m001 content-blob, kind=context-budget)
- ✓ drift-metrics.yaml valid (m001 content-blob, kind=drift-metrics)
- ✓ lifecycle.yaml valid (m001 content-blob, kind=lifecycle)
- ✓ roles.yaml valid (m001 content-blob, kind=roles)
- ✓ rules.yaml contains structured 'rules' entries
- ✓ session-protocol.yaml valid (m001 content-blob, kind=session-protocol)
- ✓ verification.yaml valid (m001 content-blob, kind=verification)
- ✓ All 412 accepted REQ(s) have test coverage
- ✓ LEDGER.md has 475 lines (within 500 threshold)
- ✓ 0 open, 0 closed TODOs
- ✓ AGENTS.md: 122 lines
- ✓ docs/governance/RULES.md: 18 lines
- ✓ docs/governance/SESSION-PROTOCOL.md: 50 lines
- ✓ docs/governance/LIFECYCLE.md: 28 lines
- ✓ docs/governance/ROLES.md: 51 lines
- ✓ docs/governance/CONTEXT-BUDGET.md: 40 lines
- ✓ docs/governance/VERIFICATION.md: 49 lines
- ✓ docs/governance/DRIFT-METRICS.md: 44 lines
- ✓ Phase 🚀 Release: 100% ready
- ✓ WI-C5A3000C risk=low gates satisfied
- ✓ WI-424D94E9 risk=low gates satisfied
- ✓ WI-75940FB5 risk=low gates satisfied
- ✓ WI-55ED3D3C risk=low gates satisfied
- ✓ WI-F1579D03 risk=low gates satisfied
- ✓ WI-3E135E87 risk=low gates satisfied
- ✓ WI-0A0CBF48 risk=low gates satisfied
- ✓ WI-D3390673 risk=low gates satisfied
- ✓ WI-EE91A49E risk=low gates satisfied
- ✓ WI-75EB75D4 risk=low gates satisfied
- ✓ WI-AD2B9BF6 risk=low gates satisfied
- ✓ WI-100A6DB0 risk=low gates satisfied
- ✓ WI-1FA34EDD risk=low gates satisfied
- ✓ WI-54FBF673 risk=low gates satisfied
- ✓ WI-7195E80A risk=low gates satisfied
- ✓ WI-CCB839B8 risk=low gates satisfied
- ✓ WI-90F68EC4 risk=low gates satisfied
- ✓ WI-AD8285B7 risk=low gates satisfied
- ✓ WI-F9B14D9C risk=low gates satisfied
- ✓ WI-C4FB242E risk=low gates satisfied
- ✓ WI-C1B608A9 risk=low gates satisfied
- ✓ WI-FCA45C63 risk=low gates satisfied
- ✓ WI-14572445 risk=low gates satisfied
- ✓ WI-549942F2 risk=low gates satisfied
- ✓ WI-6484EE02 risk=low gates satisfied
- ✓ WI-CFC9C82C risk=low gates satisfied
- ✓ WI-508DEB6C risk=medium gates satisfied
- ✓ WI-605822F2 risk=low gates satisfied
- ✓ WI-A210227F risk=low gates satisfied
- ✓ WI-5A57E6D6 risk=low gates satisfied
- ✓ WI-940D7073 risk=low gates satisfied
- ✓ WI-094C4FE3 risk=low gates satisfied
- ✓ WI-898AEB59 risk=low gates satisfied
- ✓ WI-B4E3F895 risk=low gates satisfied
- ✓ WI-1DDA18E0 risk=low gates satisfied
- ✓ WI-DA14F483 risk=medium gates satisfied
- ✓ WI-8F467602 risk=medium gates satisfied
- ✓ WI-5C560143 risk=medium gates satisfied
- ✗ WI-6C92EE21 risk=medium missing gates: linked tests
- ✓ WI-260B314F risk=low gates satisfied

## Recent Activity

- `bf45813 Merge pull request #294 from layer1labs/codex/close-release-0.22.0`
- `0f75440 chore(governance): close v0.22.0 release`
- `61b556e Merge pull request #293 from layer1labs/codex/release-0.22.0`
- `1f75e19 release: prepare v0.22.0`
- `52c33fd KILL SWITCH ACTIVATED: emergency stop`
- `da69815 KILL SWITCH ACTIVATED: emergency stop`
- `46da691 Merge pull request #292 from layer1labs/codex/clear-postmerge-codeql`
- `05d3e38 fix: clear remaining post-merge CodeQL findings`
- `eafcd63 Merge pull request #291 from layer1labs/codex/epistemic-release`
- `76adac6 fix: resolve remaining CodeQL review findings`

**Contributors:**
- 726	Tristen Pierson
- 5	dependabot[bot]
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
