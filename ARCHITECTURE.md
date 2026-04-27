Purpose
Specsmith is an open‑source tool that manages the engineering of its own governance, verification, and automation processes.

Core Boundary
Specsmith’s core logic operates within a defined boundary that includes commands, config, and adapters.

Existing Specsmith System
Specsmith comprises:
- AEE (Adaptive Execution Engine) managing tasks.
- Governance layer for requirements and ledger.
- Epistemic confidence checks.

Governance Files
Governance files include:
- ARCHITECTURE.md
- REQUIREMENTS.md
- TEST_SPEC.md
- LEDGER.md

Machine State
Machine‑readable state files under `.specsmith/` must synchronize with human‑readable governance.

Requirement Flow
- Requirements are derived from architecture, assigned IDs, and produce preflight output.

Test Case Flow
- Test cases are generated, linked, and executed to prove requirements.

AEE Verification Flow
Specsmith verifies changes, diffs, tests, and produces confidence scores.

OpenCode Integration Boundary
Specsmith relies on the integration layer OpenCode for filesystem and tool operations.

Integration‑Agnostic Adapter Model
The adapter model is integration‑agnostic and provides required capabilities.

AEE / Epistemic Layer
The epistemic layer handles confidence, iterations, and escalation.

Ledger and Trace Chain
All changes are recorded to LEDGER.md and `.specsmith/ledger.jsonl` with hashes for trace.

Planned Architecture Evolution
Future features include dynamic routing, heavy‑model escalation, and modular adapters.

Architecture Invariants
- All human‑readable governing files must remain the source of truth.
- Machine state must be derived from governance.
- No feature must block bootstrap.

Bootstrap Sequencing Rules
- Defined sequencing for state, requirement, test, verification, and ledger.

Non‑Goals During Bootstrap
- Bootstrap does not implement all optional features immediately but represents them.

IP Evidence, Release, Versioning, Branching, and Documentation Automation
Specsmith supports IP evidence, automated release, semantic versioning, branching guidance, and documentation syncing.

Integration/Automation

### Dynamic Agent and Model Routing
- **Specsmith should eventually support dynamic routing between configured agents/models based on task type.**
- deterministic scripts, JSON rebuilds, and schema work -> coder model
- code implementation, debugging, and review -> coder model
- architecture, governance, long context, recovery, ambiguity, and multi‑step reasoning -> complex/heavy model
- quick summaries or low‑risk questions -> lightweight model
- repeated tool failure or malformed output -> escalates to heavy model
- routing must be configuration‑driven
- routing must be optional and enabled by default
- routing must not make Specsmith directly manage LLM providers
- integration layer remains responsible for actual model execution
- this is a future feature and must not block bootstrap
