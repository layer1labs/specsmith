# Governance Model

specsmith implements the Agentic AI Development Workflow Specification — a structured governance model for AI-assisted development.

## Core Principle

Every AI agent action follows a closed loop:

**Propose → Check → Execute → Verify → Record**

## File Hierarchy

Every specsmith-governed project has this authority hierarchy:

1. **AGENTS.md** + `docs/governance/*` — highest authority (governance rules)
2. **README.md** — project intent and scope
3. **docs/REQUIREMENTS.md** — what the system must do
4. **docs/architecture.md** — how the system is structured
5. **docs/TEST_SPEC.md** — how the system is verified
6. **LEDGER.md** — sole authority for session state
7. **docs/workflow.md** — how work proceeds

## Modular Governance

When AGENTS.md grows beyond ~150 lines, governance is split into modular files:

- `docs/governance/rules.md` — Hard rules H1–H9, stop conditions
- `docs/governance/workflow.md` — Session lifecycle, proposal/ledger format
- `docs/governance/roles.md` — Agent role boundaries
- `docs/governance/context-budget.md` — Context management, credit optimization
- `docs/governance/verification.md` — Verification standards, acceptance criteria, **project-specific tools**
- `docs/governance/drift-metrics.md` — Drift detection, health signals

## Type-Specific Rules

Each project type gets tailored governance rules in AGENTS.md. Examples:

- **Patent application** — Claims are governance artifacts; independent claims must be self-contained; prior art must be tracked with publication dates
- **Rust CLI** — `cargo clippy` must pass with no warnings; all public APIs need doc comments
- **Legal/compliance** — All changes need version tracking; regulatory references need jurisdiction and effective date; approval workflows are mandatory
- **FPGA/RTL** — Tool invocations must use batch mode only; constraint files are governance artifacts; timing closure is a formal milestone

## Verification

The `verification.md` governance file is populated with the project's specific verification tools from the [Tool Registry](tool-registry.md). Agents read this file to know which tools to run before marking tasks complete.

## Drift Detection

`specsmith audit` checks 6 health dimensions:

1. **File existence** — Required governance files present
2. **REQ↔TEST coverage** — Every requirement has test coverage
3. **Ledger health** — Size within threshold, open TODOs manageable
4. **Governance size** — Files not bloated beyond thresholds
5. **Tool configuration** — CI config references the correct tools
6. **Consistency** — scaffold.yml, AGENTS.md references, requirement uniqueness

## Compliance Reporting

`specsmith export` generates a full compliance report with coverage matrix, audit summary, and file inventory. See [Export & Compliance](export.md).
