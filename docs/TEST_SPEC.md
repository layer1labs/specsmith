# Test Specification — specsmith

## Unit Tests

### Config

- **TEST-CFG-001**: ProjectConfig creates with minimal input (name + type)
  Covers: REQ-CFG-001
- **TEST-CFG-002**: ProjectConfig rejects invalid project type
  Covers: REQ-CFG-001
- **TEST-CFG-003**: package_name converts hyphens to underscores
  Covers: REQ-CFG-003
- **TEST-CFG-004**: All 20 project types have valid type_label and section_ref
  Covers: REQ-CFG-002

### Auditor

- **TEST-AUD-001**: Audit passes for a fully scaffolded project
  Covers: REQ-AUD-001
- **TEST-AUD-002**: Audit detects missing AGENTS.md
  Covers: REQ-AUD-001
- **TEST-AUD-003**: Audit detects oversized ledger
  Covers: REQ-AUD-004, REQ-AUD-005
- **TEST-AUD-004**: Audit checks governance bloat thresholds
  Covers: REQ-AUD-006
- **TEST-AUD-005**: Audit detects modular governance requirement when AGENTS.md large
  Covers: REQ-AUD-002, REQ-AUD-003

### Validator

- **TEST-VAL-001**: Validate passes for valid scaffold.yml
  Covers: REQ-VAL-001
- **TEST-VAL-002**: Validate detects broken AGENTS.md references
  Covers: REQ-VAL-002
- **TEST-VAL-003**: Validate detects duplicate requirement IDs
  Covers: REQ-VAL-003
- **TEST-VAL-004**: Validate checks architecture.md references requirements
  Covers: REQ-VAL-004

### Compressor

- **TEST-CMP-001**: Compress skips when ledger is below threshold
  Covers: REQ-CMP-003
- **TEST-CMP-002**: Compress archives old entries and creates ledger-archive.md
  Covers: REQ-CMP-001, REQ-CMP-002
- **TEST-CMP-003**: Compress preserves recent entries
  Covers: REQ-CMP-001

### Upgrader

- **TEST-UPG-001**: Upgrade skips when already at target version
  Covers: REQ-UPG-001
- **TEST-UPG-002**: Upgrade re-renders governance files and updates scaffold.yml
  Covers: REQ-UPG-002, REQ-UPG-003

## Integration Tests

### Scaffolder

- **TEST-SCF-001**: CLI Python scaffold creates expected file set
  Covers: REQ-SCF-001, REQ-SCF-002
- **TEST-SCF-002**: FPGA scaffold omits pyproject.toml
  Covers: REQ-SCF-002
- **TEST-SCF-003**: Library scaffold includes pyproject.toml without cli.py
  Covers: REQ-SCF-002
- **TEST-SCF-004**: .gitkeep files created in empty directories
  Covers: REQ-SCF-003
- **TEST-SCF-005**: scaffold.yml written after init
  Covers: REQ-SCF-005
- **TEST-SCF-006**: Warp integration files created when configured
  Covers: REQ-SCF-006, REQ-INT-001

### CLI

- **TEST-CLI-001**: `specsmith --version` outputs version string
  Covers: REQ-CLI-007
- **TEST-CLI-002**: `specsmith init --config` creates project from YAML
  Covers: REQ-CLI-001
- **TEST-CLI-003**: `specsmith audit` exits 0 on healthy project
  Covers: REQ-CLI-002
- **TEST-CLI-004**: `specsmith validate` exits 0 on valid project
  Covers: REQ-CLI-003

### Integrations

- **TEST-INT-001**: Warp adapter generates SKILL.md with project metadata
  Covers: REQ-INT-001
- **TEST-INT-002**: Claude Code adapter generates CLAUDE.md
  Covers: REQ-INT-002
- **TEST-INT-003**: Cursor adapter generates governance.mdc
  Covers: REQ-INT-003
- **TEST-INT-004**: Copilot adapter generates copilot-instructions.md
  Covers: REQ-INT-004
- **TEST-INT-005**: Adapter registry lists all available adapters
  Covers: REQ-INT-005

### Tool Registry

- **TEST-TLR-001**: Python CLI type has ruff, mypy, pytest, pip-audit, ruff format
  Covers: REQ-TLR-001
- **TEST-TLR-002**: Rust CLI type has clippy, cargo check, cargo test, cargo audit, cargo fmt
  Covers: REQ-TLR-001
- **TEST-TLR-003**: Go, web-frontend, FPGA, embedded, .NET types have correct tools
  Covers: REQ-TLR-001
- **TEST-TLR-004**: All 30 project types have at least one tool registered
  Covers: REQ-TLR-001, REQ-CFG-002
- **TEST-TLR-005**: get_tools() returns defaults from registry
  Covers: REQ-TLR-001
- **TEST-TLR-006**: get_tools() respects verification_tools overrides
  Covers: REQ-TLR-003, REQ-CFG-004
- **TEST-TLR-007**: Format check commands convert correctly (ruff, cargo fmt, prettier)
  Covers: REQ-TLR-004
- **TEST-TLR-008**: All languages in LANG_CI_META have docker_image
  Covers: REQ-TLR-002

### Importer

- **TEST-IMP-001**: Detects Python project (language, build system, test framework, type)
  Covers: REQ-IMP-001, REQ-IMP-002, REQ-IMP-003, REQ-IMP-006
- **TEST-IMP-002**: Detects Rust project
  Covers: REQ-IMP-001, REQ-IMP-002, REQ-IMP-006
- **TEST-IMP-003**: Detects JS web project
  Covers: REQ-IMP-001, REQ-IMP-002, REQ-IMP-006
- **TEST-IMP-004**: Detects entry points and test files
  Covers: REQ-IMP-005
- **TEST-IMP-005**: Detects GitHub CI and governance files
  Covers: REQ-IMP-004, REQ-IMP-005
- **TEST-IMP-006**: Empty directory returns safe defaults
  Covers: REQ-IMP-006
- **TEST-IMP-007**: generate_import_config produces correct ProjectConfig
  Covers: REQ-IMP-006, REQ-CFG-005
- **TEST-IMP-008**: Overlay creates all 5 governance files
  Covers: REQ-IMP-007
- **TEST-IMP-009**: Overlay skips existing files without --force
  Covers: REQ-IMP-008
- **TEST-IMP-010**: Overlay force-overwrites existing files
  Covers: REQ-IMP-008

### VCS Platforms (Tool-Aware CI)

- **TEST-VCS-001**: GitHub CI for Python has ruff, mypy, pytest, pip-audit
  Covers: REQ-VCS-001
- **TEST-VCS-002**: GitHub CI for Rust has cargo clippy, cargo test, rust-toolchain
  Covers: REQ-VCS-001, REQ-VCS-002
- **TEST-VCS-003**: GitHub CI for Go has golangci-lint, go test, setup-go
  Covers: REQ-VCS-001, REQ-VCS-002
- **TEST-VCS-004**: GitHub CI for FPGA has vsg, ghdl
  Covers: REQ-VCS-001, REQ-VCS-002
- **TEST-VCS-005**: Dependabot config uses correct ecosystem (pip, cargo, gomod)
  Covers: REQ-VCS-003
- **TEST-VCS-006**: GitLab CI for Rust uses rust:latest image and cargo commands
  Covers: REQ-VCS-001
- **TEST-VCS-007**: Bitbucket pipelines for Python has python:3.12-slim image
  Covers: REQ-VCS-001

### Sandbox — Import Workflow

- **TEST-SBX-001**: Full import of realistic Python CLI project (detection, overlay, audit)
  Covers: REQ-CLI-008, REQ-IMP-001, REQ-IMP-002, REQ-IMP-003, REQ-IMP-006, REQ-IMP-007
- **TEST-SBX-002**: Import skip behavior (no overwrite without --force)
  Covers: REQ-IMP-008
- **TEST-SBX-003**: Import force overwrites existing files
  Covers: REQ-IMP-008
- **TEST-SBX-004**: Import idempotent restart
  Covers: REQ-IMP-007

### Sandbox — New Project Workflow

- **TEST-SBX-005**: Full scaffold from config with all commands (audit/validate/compress/upgrade/diff)
  Covers: REQ-CLI-001, REQ-CLI-002, REQ-CLI-003, REQ-CLI-004, REQ-CLI-005, REQ-CLI-006, REQ-CLI-011, REQ-SCF-001, REQ-SCF-002, REQ-SCF-004, REQ-SCF-005, REQ-SCF-006, REQ-TPL-001, REQ-TPL-004
- **TEST-SBX-006**: Scaffold idempotent restart
  Covers: REQ-SCF-001
- **TEST-SBX-007**: Auditor tool verification on scaffolded project
  Covers: REQ-AUD-007, REQ-AUD-008

### Sandbox — Import with Existing Docs

- **TEST-SBX-013**: Import preserves existing REQUIREMENTS.md, TEST_SPEC.md, architecture docs
  Covers: REQ-IMP-008
- **TEST-SBX-014**: Import with --force overwrites existing docs
  Covers: REQ-IMP-008

### Sandbox — Non-Python Types

- **TEST-SBX-008**: Patent application scaffold with domain directories, requirements, tests, tools
  Covers: REQ-CFG-002, REQ-TPL-002, REQ-TPL-003
- **TEST-SBX-009**: Rust CLI scaffold with cargo CI, dependabot, and governance rules
  Covers: REQ-CFG-002, REQ-VCS-001, REQ-VCS-002
- **TEST-SBX-010**: Config inheritance (extends field) merges org defaults with child
  Covers: REQ-CFG-001, REQ-VCS-004
- **TEST-SBX-011**: Export command generates compliance report with tools and audit
  Covers: REQ-EXP-001, REQ-EXP-002, REQ-EXP-003, REQ-EXP-004
- **TEST-SBX-012**: Export to file with --output flag
  Covers: REQ-EXP-005

### Git VCS Commands

- **TEST-GIT-001**: commit generates message from ledger entry
  Covers: REQ-GIT-001
- **TEST-GIT-002**: commit refuses when ledger is stale
  Covers: REQ-GIT-002
- **TEST-GIT-003**: commit runs audit before committing
  Covers: REQ-GIT-003
- **TEST-GIT-004**: push sends to correct remote
  Covers: REQ-GIT-004
- **TEST-GIT-005**: push blocks direct-to-main from feature branch
  Covers: REQ-GIT-005
- **TEST-GIT-006**: branch create uses develop as base for gitflow
  Covers: REQ-GIT-006
- **TEST-GIT-007**: branch list annotates strategy context
  Covers: REQ-GIT-007
- **TEST-GIT-008**: pr includes ledger summary and audit in description
  Covers: REQ-GIT-008
- **TEST-GIT-009**: pr targets develop for features, main for hotfixes
  Covers: REQ-GIT-009
- **TEST-GIT-010**: sync warns on upstream governance changes
  Covers: REQ-GIT-010

### Self-Update and Migration

- **TEST-UPD-001**: update --check reports version comparison without installing
  Covers: REQ-UPD-001
- **TEST-UPD-002**: update detects when already at latest version
  Covers: REQ-UPD-001
- **TEST-UPD-003**: migrate-project detects spec_version mismatch
  Covers: REQ-UPD-004
- **TEST-UPD-004**: migrate-project regenerates governance templates
  Covers: REQ-UPD-005
- **TEST-UPD-005**: migrate-project --dry-run shows changes without writing
  Covers: REQ-UPD-007
- **TEST-UPD-006**: migrate-project preserves REQUIREMENTS.md and TEST_SPEC.md
  Covers: REQ-UPD-010
- **TEST-UPD-007**: migrate-project appends entry to LEDGER.md
  Covers: REQ-UPD-009
- **TEST-UPD-008**: agent adapters include update check instruction
  Covers: REQ-UPD-008

### Workflow Logic

- **TEST-WFL-001**: agent adapter includes post-save commit proposal logic
  Covers: REQ-WFL-001
- **TEST-WFL-002**: agent adapter includes session-end push reminder
  Covers: REQ-WFL-002
- **TEST-WFL-003**: agent adapter includes branch-check for gitflow
  Covers: REQ-WFL-003
- **TEST-WFL-004**: agent adapter includes branch proposal for new tasks
  Covers: REQ-WFL-004
- **TEST-WFL-005**: agent adapter includes PR proposal when feature complete
  Covers: REQ-WFL-005
- **TEST-WFL-006**: agent adapter includes sync-first in session start
  Covers: REQ-WFL-006
- **TEST-WFL-007**: commit --auto-push commits and pushes in sequence
  Covers: REQ-WFL-009
- **TEST-WFL-008**: session-end checklist reports unpushed commits and dirty files
  Covers: REQ-WFL-010

### Cross-Platform (CI Matrix)

- **TEST-XPL-001**: CI matrix runs tests on Windows, Linux, macOS with Python 3.10, 3.12, 3.13
  Covers: REQ-XPL-001, REQ-XPL-002

### CLI Commands (Additional Coverage)

- **TEST-CLI-005**: `specsmith init --guided` generates REQ/TEST stubs interactively
  Covers: REQ-CLI-009
- **TEST-CLI-006**: `specsmith status` runs VCS platform status check
  Covers: REQ-CLI-010
- **TEST-CLI-007**: `specsmith export` generates compliance report
  Covers: REQ-CLI-012
- **TEST-CLI-008**: `specsmith import --guided` runs architecture after import
  Covers: REQ-CLI-013

### Applied Epistemic Engineering

- **TEST-AEE-001**: `BeliefArtifact` creates with required fields (id, propositions, boundary, confidence, status)
  Covers: REQ-AEE-001
- **TEST-AEE-002**: `BeliefArtifact.add_evidence()` elevates confidence from UNKNOWN to LOW
  Covers: REQ-AEE-004
- **TEST-AEE-003**: `BeliefArtifact.to_dict()` returns JSON-serializable dict
  Covers: REQ-AEE-005
- **TEST-AEE-004**: `parse_requirements_as_beliefs()` parses REQUIREMENTS.md correctly
  Covers: REQ-AEE-002
- **TEST-AEE-005**: `beliefs_from_dicts()` constructs BeliefArtifacts from plain dicts
  Covers: REQ-AEE-003

### Stress Testing

- **TEST-STR-001**: `StressTester` flags empty propositions as CRITICAL failure
  Covers: REQ-STR-001, REQ-STR-002
- **TEST-STR-002**: `StressTester` detects vagueness (imprecise language)
  Covers: REQ-STR-002
- **TEST-STR-003**: `StressTester` equilibrium is True for clean draft artifact
  Covers: REQ-STR-005
- **TEST-STR-004**: Accepted artifact without test coverage gets HIGH failure
  Covers: REQ-STR-002
- **TEST-STR-005**: Duplicate accepted IDs detected as Logic Knot
  Covers: REQ-STR-003, REQ-STR-004

### Failure-Mode Graph

- **TEST-FMG-001**: `FailureModeGraph.equilibrium_check()` passes with no failures
  Covers: REQ-FMG-001, REQ-FMG-003
- **TEST-FMG-002**: `equilibrium_check()` fails when critical failures present
  Covers: REQ-FMG-003
- **TEST-FMG-003**: `logic_knot_detect()` returns detected knots
  Covers: REQ-FMG-004
- **TEST-FMG-004**: `render_text()` shows equilibrium status
  Covers: REQ-FMG-002
- **TEST-FMG-005**: `render_mermaid()` produces valid Mermaid graph TD output
  Covers: REQ-FMG-002

### Certainty Engine

- **TEST-CRT-001**: UNKNOWN confidence + no propositions = score 0.0
  Covers: REQ-CRT-001
- **TEST-CRT-002**: MEDIUM confidence + test coverage ≈ 0.55
  Covers: REQ-CRT-001
- **TEST-CRT-003**: Weakest-link propagation: dependent score ≤ upstream score
  Covers: REQ-CRT-002
- **TEST-CRT-004**: `component_averages` groups scores by component code
  Covers: REQ-CRT-003
- **TEST-CRT-005**: `below_threshold` contains IDs of low-scoring artifacts
  Covers: REQ-CRT-004

### Trace Vault

- **TEST-TRC-001**: `TraceVault` chain verification passes for intact chain
  Covers: REQ-TRC-001, REQ-TRC-002
- **TEST-TRC-002**: `TraceVault` detects tampered entry (hash mismatch)
  Covers: REQ-TRC-002
- **TEST-TRC-003**: First seal uses genesis hash; second seal chains to first
  Covers: REQ-TRC-001, REQ-TRC-004

### AEESession

- **TEST-EPI-001**: `AEESession.run()` returns AEEResult with summary
  Covers: REQ-EPI-003, REQ-EPI-004
- **TEST-EPI-002**: `AEESession.save()` and `load()` round-trip belief state
  Covers: REQ-EPI-005
- **TEST-EPI-003**: `from epistemic import AEESession` imports cleanly
  Covers: REQ-EPI-001, REQ-EPI-002
- **TEST-EPI-004**: `specsmith.epistemic` re-exports `BeliefArtifact` from `epistemic`
  Covers: REQ-EPI-006

### Agentic Client

- **TEST-AGT-001**: `AgentRunner` initializes without a provider (deferred to first call)
  Covers: REQ-AGT-001, REQ-AGT-003
- **TEST-AGT-002**: `build_tool_registry()` returns 20+ tools including `audit` and `epistemic_audit`
  Covers: REQ-AGT-006
- **TEST-AGT-003**: `load_skills()` finds built-in profiles (epistemic-auditor, planner, verifier)
  Covers: REQ-AGT-007
- **TEST-AGT-004**: `HookRegistry` fires H13 warning when AEE tool called
  Covers: REQ-AGT-008, REQ-AGT-009
- **TEST-AGT-005**: `specsmith run --task` executes single task and returns output
  Covers: REQ-AGT-002
- **TEST-AGT-006**: `specsmith run` auto-detects provider from SPECSMITH_PROVIDER env var
  Covers: REQ-AGT-004
- **TEST-AGT-007**: All provider extras are optional; no error if not installed
  Covers: REQ-AGT-005
- **TEST-AGT-008**: `specsmith agent providers` lists provider status
  Covers: REQ-AGT-010

### Certainty Engine (additional)

- **TEST-CRT-006**: `CertaintyEngine` threshold is configurable via constructor
  Covers: REQ-CRT-005

### Trace Vault (additional)

- **TEST-TRC-004**: `CryptoAuditChain` stores entry_hash in ledger-chain.txt
  Covers: REQ-TRC-003
- **TEST-TRC-005**: `specsmith trace seal` creates SealRecord in .specsmith/trace.jsonl
  Covers: REQ-TRC-005

### epistemic Library (additional)

- **TEST-EPI-005**: `epistemic` package has `py.typed` marker file
  Covers: REQ-EPI-007

### Failure-Mode Graph (additional)

- **TEST-FMG-006**: `FailureModeGraph` builds edges from `BeliefArtifact.inferential_links`
  Covers: REQ-FMG-005

### Recovery Operator

- **TEST-RCV-001**: `RecoveryOperator.propose()` returns list sorted by severity
  Covers: REQ-RCV-001, REQ-RCV-003
- **TEST-RCV-002**: `RecoveryProposal` objects are not auto-applied
  Covers: REQ-RCV-002
- **TEST-RCV-003**: `RecoveryOperator` generates proposals for Logic Knots
  Covers: REQ-RCV-004
- **TEST-RCV-004**: `format_proposals()` returns human-readable string
  Covers: REQ-RCV-001

### Auth (#37)

- **TEST-AUTH-001**: `specsmith auth set <platform>` stores token without logging value
  Covers: REQ-AUTH-001, REQ-AUTH-006
- **TEST-AUTH-002**: `specsmith auth list` shows masked token, not plaintext
  Covers: REQ-AUTH-002
- **TEST-AUTH-003**: `specsmith auth remove <platform>` deletes stored credential
  Covers: REQ-AUTH-003
- **TEST-AUTH-004**: `specsmith auth check` reports which platforms have tokens
  Covers: REQ-AUTH-004
- **TEST-AUTH-005**: `get_token()` checks env var first, keyring second, file third
  Covers: REQ-AUTH-005
- **TEST-AUTH-006**: Token value is never returned in CLI output
  Covers: REQ-AUTH-006

### Workspace (#17)

- **TEST-WRK-001**: `specsmith workspace init` creates workspace.yml
  Covers: REQ-WRK-001
- **TEST-WRK-002**: `specsmith workspace audit` runs audit across all projects
  Covers: REQ-WRK-002
- **TEST-WRK-003**: `specsmith workspace export` generates combined report
  Covers: REQ-WRK-003
- **TEST-WRK-004**: workspace.yml supports projects list with org-level defaults
  Covers: REQ-WRK-004

### Watch (#16)

- **TEST-WCH-001**: `specsmith watch` polls project directory and detects drift
  Covers: REQ-WCH-001
- **TEST-WCH-002**: watch alerts when LEDGER.md mtime < code file mtime
  Covers: REQ-WCH-002
- **TEST-WCH-003**: watch uses polling fallback when watchdog not installed
  Covers: REQ-WCH-003

### Patent (#10)

- **TEST-PAT-001**: `specsmith patent search` calls USPTO ODP API and returns results
  Covers: REQ-PAT-001
- **TEST-PAT-002**: `specsmith patent prior-art` extracts key terms and builds query
  Covers: REQ-PAT-002
- **TEST-PAT-003**: Patent commands raise RuntimeError without USPTO_API_KEY
  Covers: REQ-PAT-003
- **TEST-PAT-004**: `save_prior_art_report()` writes markdown to prior-art/ directory
  Covers: REQ-PAT-004

### Auto-Update

- **TEST-AUP-001**: `_maybe_prompt_project_update` checks scaffold.yml spec_version
  Covers: REQ-AUP-001
- **TEST-AUP-002**: auto-update prompt offered when spec_version < installed version
  Covers: REQ-AUP-002
- **TEST-AUP-003**: SPECSMITH_NO_AUTO_UPDATE=1 suppresses the prompt
  Covers: REQ-AUP-003
- **TEST-AUP-004**: auto-update skips meta-commands (update, migrate-project)
  Covers: REQ-AUP-004

### Credit Hard Cap (#52)

- **TEST-CHC-001**: `CreditBudget.enforcement_mode` field defaults to 'soft'
  Covers: REQ-CHC-001
- **TEST-CHC-002**: `specsmith credits check` shows spend vs budget with bar
  Covers: REQ-CHC-002
- **TEST-CHC-003**: Hard cap exits with code 2 when monthly cap exceeded
  Covers: REQ-CHC-003
- **TEST-CHC-004**: `specsmith credits budget --enforcement hard` sets hard mode
  Covers: REQ-CHC-004

### Scaffolder Epistemic

- **TEST-SCF-EPI-001**: `specsmith init` with epistemic-pipeline renders epistemic templates
  Covers: REQ-SCF-EPI-001
- **TEST-SCF-EPI-002**: `enable_epistemic=true` in scaffold.yml adds epistemic governance
  Covers: REQ-SCF-EPI-002
- **TEST-SCF-EPI-003**: epistemic project types get domain-specific directory structures
  Covers: REQ-SCF-EPI-003

### Architecture Generation

- **TEST-ARC-001**: `specsmith architect` scans modules and language distribution
  Covers: REQ-ARC-001
- **TEST-ARC-002**: `specsmith architect` prompts for components in interactive mode
  Covers: REQ-ARC-002
- **TEST-ARC-003**: `specsmith architect --non-interactive` generates without prompts
  Covers: REQ-ARC-003
- **TEST-ARC-004**: `specsmith audit --fix` generates architecture.md from scan
  Covers: REQ-ARC-004

### Credits

- **TEST-CRD-001**: `specsmith credits record` stores entry with model/tokens/cost
  Covers: REQ-CRD-001
- **TEST-CRD-002**: `specsmith credits summary` shows aggregate by model and provider
  Covers: REQ-CRD-002
- **TEST-CRD-003**: `specsmith credits report` generates markdown report
  Covers: REQ-CRD-003
- **TEST-CRD-004**: `specsmith credits analyze` detects inefficiency and waste
  Covers: REQ-CRD-004
- **TEST-CRD-005**: `specsmith credits budget` configures cap and watermarks
  Covers: REQ-CRD-005
- **TEST-CRD-006**: credit tracking auto-initialized on init with unlimited budget
  Covers: REQ-CRD-006
- **TEST-CRD-007**: `.specsmith/` is gitignored in generated projects
  Covers: REQ-CRD-007
- **TEST-CRD-008**: session-end checklist includes credit summary
  Covers: REQ-CRD-008
- **TEST-CRD-009**: Warp and Claude adapters include credit recording instructions
  Covers: REQ-CRD-009

### Self-Update

- **TEST-SLF-001**: `specsmith self-update` detects stable vs dev channel from version
  Covers: REQ-SLF-001
- **TEST-SLF-002**: `specsmith self-update --channel dev` forces dev channel
  Covers: REQ-SLF-002
- **TEST-SLF-003**: `specsmith self-update --version X.Y.Z` pins specific version
  Covers: REQ-SLF-003

### Templates

- **TEST-TPL-005**: .gitattributes template includes type-specific patterns for 33 project types
  Covers: REQ-TPL-005
- **TEST-TPL-006**: .gitignore template includes type-specific patterns for 33 project types
  Covers: REQ-TPL-006
- **TEST-TPL-007**: .editorconfig template includes type-specific indent/EOL settings
  Covers: REQ-TPL-007
- **TEST-TPL-008**: Yocto language detection includes .bbclass, .inc, .dts, .dtsi
  Covers: REQ-TPL-008

### Migration

- **TEST-UPD-009**: `specsmith update --yes` installs without confirmation
  Covers: REQ-UPD-002
- **TEST-UPD-010**: `specsmith update` triggers migrate-project after successful update
  Covers: REQ-UPD-003
- **TEST-UPD-011**: `specsmith migrate-project` preserves existing REQs and ledger entries
  Covers: REQ-UPD-006

### Workflow Logic (additional)

- **TEST-WFL-009**: `specsmith update --check` runs at session start and proposes update
  Covers: REQ-WFL-007
- **TEST-WFL-010**: `specsmith session-end` reports unpushed commits and dirty files
  Covers: REQ-WFL-008
