# Architecture — Specsmith Self-Governing AEE System

## 1. Purpose

Specsmith is an Applied Epistemic Engineering toolkit and governance engine.

It scaffolds epistemically governed projects, records project beliefs, derives requirements, maps requirements to tests, verifies evidence, tracks uncertainty, and records decisions in a tamper-evident ledger.

Specsmith must be capable of governing its own development.

This repository is being bootstrapped so Specsmith can use its own governance system to manage future changes.

## 2. Core Boundary

Specsmith has two major layers:

### Governance Layer

The governance layer owns:

- `ARCHITECTURE.md`
- `REQUIREMENTS.md`
- `TESTS.md`
- `LEDGER.md`
- `.specsmith/requirements.json`
- `.specsmith/testcases.json`
- `.specsmith/workitems.json`
- `.specsmith/ledger.jsonl`
- `.specsmith/ledger-chain.txt`

The governance layer decides:

- what the system is supposed to do
- what requirements exist
- what tests prove those requirements
- what work items should be created
- whether output satisfies the requirements
- whether epistemic confidence is sufficient
- whether retry or escalation is needed

### Runtime Layer

The runtime layer executes actions through:

- Specsmith CLI commands
- OpenCode sessions
- agent commands
- test runners
- filesystem tools
- git operations
- future integrations

The runtime layer performs work, but governance determines whether the work is valid.

## 3. Existing Specsmith System

Specsmith currently includes:

- Click-based CLI entrypoint
- scaffold generation
- governance file generation
- AEE commands
- agentic client commands
- auditor/exporter/importer functionality
- optional LLM/provider support
- GUI workbench
- trace vault and ledger functionality
- compatibility shim for the standalone `epistemic` package

Existing major modules include:

- `cli.py`
- `config.py`
- `scaffolder.py`
- `tools.py`
- `importer.py`
- `exporter.py`
- `auditor.py`
- `ledger.py`
- `integrations/`
- `vcs/`
- `src/epistemic/`
- `src/specsmith/agent/`
- `src/specsmith/gui/`

## 4. Governance Files

Specsmith governance is represented in both human-readable and machine-readable forms.

### Human-readable governance files

- `ARCHITECTURE.md` — canonical architectural source of truth
- `REQUIREMENTS.md` — declarative requirement list
- `TESTS.md` — test specification and requirement-to-test expectations
- `LEDGER.md` — human-readable audit trail

### Machine-readable governance files

- `.specsmith/requirements.json`
- `.specsmith/testcases.json`
- `.specsmith/workitems.json`
- `.specsmith/ledger.jsonl`
- `.specsmith/ledger-chain.txt`

Machine-readable files are the bridge between governance documents and agent/tool execution.

## 5. Machine State

Machine state lives under `.specsmith/`.

Current required state files:

- `.specsmith/requirements.json`
- `.specsmith/testcases.json`
- `.specsmith/workitems.json`
- `.specsmith/ledger.jsonl`
- `.specsmith/ledger-chain.txt`

Planned future state may include:

- `.specsmith/runs/`
- `.specsmith/evals/`
- `.specsmith/instincts.json`
- `.specsmith/teams/`
- `.specsmith/worktrees/`
- `.specsmith/agent-memory/`

Machine state must not replace the human-readable governance documents. Both must stay aligned.

## 6. Requirement Flow

Planned behavior:

1. `ARCHITECTURE.md` defines architectural intent.
2. Specsmith derives requirements from `ARCHITECTURE.md`.
3. Requirements are written to `REQUIREMENTS.md`.
4. Structured requirements are written to `.specsmith/requirements.json`.
5. Requirements are assigned stable IDs.
6. Requirements are linked to test cases.
7. Work items are created from accepted requirements or user requests.
8. Every change is recorded in the ledger.

A requirement must be:

- atomic
- testable where practical
- traceable to a source
- stable across repeated ingestion
- linked to verification evidence

## 7. Test Case Flow

Planned behavior:

1. Accepted requirements produce or link to test cases.
2. Test cases are recorded in `TESTS.md`.
3. Structured test cases are written to `.specsmith/testcases.json`.
4. Tests are executed through pytest or other registered tools.
5. Test results are attached to work items.
6. Verification evaluates whether tests provide sufficient evidence.
7. Results are recorded in `LEDGER.md` and `.specsmith/ledger.jsonl`.

Test cases must map back to requirement IDs.

## 8. AEE Verification Flow

AEE verification is Specsmith’s epistemic evaluation layer.

The verification flow includes:

1. Frame — identify the belief, requirement, or work item under evaluation.
2. Disassemble — break the claim into concrete assertions.
3. Stress-Test — challenge assertions using tests, evidence, contradictions, and failure modes.
4. Score — calculate confidence based on coverage, evidence quality, freshness, and failures.
5. Reconstruct — propose bounded recovery or retry steps.
6. Seal — record the result in the ledger and trace chain.

Verification must produce more than pass/fail.

It should produce:

- status
- confidence
- target confidence
- equilibrium state
- failures
- uncertainties
- contradictions
- retry recommendation

Epistemic equilibrium is reached only when confidence meets the target and no blocking contradictions remain.

## 9. OpenCode Integration Boundary

OpenCode is the first external execution environment for this governance model.

OpenCode should:

- execute filesystem operations
- run shell commands
- edit code
- run tests
- gather diffs
- provide output evidence

Specsmith should:

- preflight requests
- map requests to requirements
- map requirements to tests
- decide priority
- verify evidence
- recommend retries
- record ledger events

Specsmith core must not depend on OpenCode.

OpenCode-specific behavior must live behind an integration adapter.

## 10. Integration-Agnostic Adapter Model

Specsmith must support future integrations beyond OpenCode.

Potential integrations include:

- OpenCode
- Cursor
- Claude Code
- GitHub Actions
- VS Code
- JetBrains
- Theia-based Specsmith IDE
- CI/CD systems
- future project management systems

Core governance logic must remain independent from any one integration.

Adapters translate between the host environment and Specsmith’s standard governance contract.

## 11. AEE / Epistemic Layer

The standalone `epistemic` package is the canonical location for AEE machinery.

Key components include:

- `BeliefArtifact`
- `StressTester`
- `FailureModeGraph`
- `RecoveryOperator`
- `CertaintyEngine`
- `AEESession`
- `TraceVault`

Specsmith re-exports AEE symbols through `specsmith.epistemic` for compatibility.

The verification engine should use AEE concepts rather than simple binary validation.

## 12. Ledger and Trace Chain

Specsmith must maintain a durable audit trail.

Ledger artifacts:

- `LEDGER.md`
- `.specsmith/ledger.jsonl`
- `.specsmith/ledger-chain.txt`

The ledger records:

- architecture changes
- requirement creation
- test case creation
- work item creation
- verification results
- retry recommendations
- final status changes

The trace chain must be tamper-evident using chained hashes.

## 13. Planned Architecture Evolution

### Phase 1 — Core Harness Depth

Planned modules:

- `src/specsmith/operations.py`
- `src/specsmith/commands/`
- `src/specsmith/instinct.py`
- `src/specsmith/eval/`

Phase 1 goals:

- add typed project operations
- reduce raw shell usage
- expose harness slash commands
- persist reusable session patterns
- support Eval-Driven Development

### Phase 2 — Multi-Agent Layer

Planned modules:

- `src/specsmith/agent/spawner.py`
- `src/specsmith/agent/teams.py`
- `src/specsmith/agent/orchestrator.py`
- `src/specsmith/agent/flags.py`
- `src/specsmith/memory.py`

Phase 2 goals:

- subagent spawning
- team coordination
- orchestrator-worker routing
- feature-flagged tool schema visibility
- cross-session memory

### Phase 3 — Service and IDE

Planned modules:

- `src/specsmith/server/`
- `specsmith-ide/`

Phase 3 goals:

- local HTTP/WebSocket service
- Theia-based IDE
- AEE visual panels
- eval dashboards
- ledger browser
- instinct registry

## 14. Architecture Invariants

The following invariants must hold:

- Specsmith core MUST remain integration-agnostic.
- OpenCode-specific logic MUST NOT live in core.
- Governance files MUST remain human-readable.
- Machine state MUST remain synchronized with governance files.
- Requirements MUST be traceable to architecture or explicit user input.
- Test cases MUST map to requirements.
- Verification MUST use AEE concepts: confidence, uncertainty, contradiction, equilibrium.
- Retries MUST be bounded.
- Ledger events MUST be recorded for governance changes.
- Feature flags MUST remove hidden tool schemas from LLM calls, not merely block execution.
- Project operations MUST be cross-platform.
- Eval grading MUST measure outcomes, not execution paths.
- Instinct extraction MUST be user-reviewed before promotion.
- Subagents MUST NOT recursively spawn subagents.
- Filesystem mailbox communication MUST remain simple and debuggable.
- Orchestration SHOULD prefer local Ollama for routing when possible.

## 15. Bootstrap Sequencing Rules

Current bootstrap sequence:

1. Establish governance files.
2. Align `ARCHITECTURE.md`.
3. Derive initial requirements into `REQUIREMENTS.md`.
4. Write structured requirements to `.specsmith/requirements.json`.
5. Generate initial test specs.
6. Write structured test cases to `.specsmith/testcases.json`.
7. Create work item flow.
8. Add verification flow.
9. Record all actions in ledger.
10. Only then begin deeper implementation changes.

Specsmith must not claim to govern itself until architecture, requirements, test specs, work items, and ledger flow are aligned.

## 16. Non-Goals During Bootstrap

During bootstrap, do not yet implement:

- full model orchestration
- full OpenCode plugin runtime
- GUI changes
- multi-agent teams
- daemon service
- Theia IDE
- automatic unbounded retries
- hidden background governance loops

Bootstrap is limited to making Specsmith capable of governing its own future development.