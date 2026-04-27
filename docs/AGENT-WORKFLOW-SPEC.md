# Agentic AI Development Workflow Specification

**Version:** 0.1.0-alpha.1
**Status:** Reference specification
**Purpose:** This document fully describes a specification-first, constraint-governed agentic AI development workflow. It is intended to be given to an AI agent to scaffold and govern any new project — software, firmware, FPGA/RTL, embedded Linux, or hardware — regardless of domain.

---

## 1. Core Philosophy

> Intelligence proposes. Constraints decide. The ledger remembers.

This workflow treats AI agents as **proposal generators**, not authorities. All meaningful work flows through a closed loop:

1. **State loading** — read governance files and current project state
2. **Proposal emission** — describe what will be done, within what bounds
3. **Constraint checking** — verify the proposal does not violate rules
4. **Bounded execution** — implement exactly what was proposed, nothing more
5. **Verification** — confirm what changed, what passed, what failed
6. **Ledger update** — record the outcome as the new accepted state

No step may be skipped. No work is considered done without completing all six steps.

### Authority model

- Prompts are not authority
- Plans are not authority
- Code is not authority
- **The ledger + accepted repository state is authority**

Agents do not decide. Agents do not own truth. The human operator holds final authority over all acceptance decisions.

---

## 2. Governance Files

Every project governed by this workflow MUST contain the following files at the repository root or in `docs/`.

### 2.1 AGENTS.md (repository root)

The primary behavioral control document for all agents operating in the repository. AGENTS.md MUST be kept small and focused (~100–150 lines). It defines:

- project identity, platforms, and tech stack
- a file registry pointing to all governance documents
- quick command reference
- project-type-specific rules

**AGENTS.md is the highest-authority document.** If any other document conflicts with AGENTS.md, AGENTS.md wins.

### 2.1.1 Modular governance documents (docs/governance/)

Detailed governance rules are split into focused, referenceable documents under `docs/governance/`. AGENTS.md explicitly delegates to these files, and they inherit its authority level. This modular split is RECOMMENDED for all projects and REQUIRED when a monolithic AGENTS.md would exceed ~200 lines.

| File | Content | Load timing |
| ---- | ------- | ----------- |
| `docs/governance/RULES.md` | Hard rules, stop conditions | Every session start |
| `docs/governance/WORKFLOW.md` | Session lifecycle, proposal format, ledger format | Every session start |
| `docs/governance/ROLES.md` | Agent role definition, behavioral rules | Every session start |
| `docs/governance/CONTEXT-BUDGET.md` | Context window management, credit optimization | Every session start |
| `docs/governance/VERIFICATION.md` | Verification standards, acceptance criteria | When performing verification |
| `docs/governance/DRIFT-METRICS.md` | Drift detection, feedback loops, health signals | On `audit` command or session start |

Agents read AGENTS.md in full on every session. The governance docs listed with "Every session start" timing are read immediately after. Other governance docs are loaded on demand when the task requires them. This lazy-loading approach minimizes credit consumption (see Section 25).

For small projects where all governance fits in ~200 lines, a single monolithic AGENTS.md containing all rules inline is acceptable.

### 2.2 LEDGER.md (repository root or docs/)

The append-only record of all meaningful work. Every session, every task, every decision MUST be recorded here.

Rules:
- Every meaningful task MUST be recorded
- Every session MUST append an entry
- All open TODOs MUST live in the ledger
- No work is considered complete without a ledger entry
- LEDGER.md is the ONLY authoritative source for session continuity
- Do NOT create `NEXT_SESSION.md`, `STATUS.md`, or similar files — all continuity lives in the ledger

### 2.3 README.md (repository root)

Project overview, architecture summary, component descriptions, repository structure, near-term goals, and current status. Must be kept in sync with architectural reality.

### 2.4 docs/ARCHITECTURE.md

System architecture: components, boundaries, interfaces, runtime modes, platform expectations, constraints, and design principles.

### 2.5 docs/governance/SESSION-PROTOCOL.md

Session lifecycle: session types (start, resume, save, commit, sync), proposal format, ledger entry format.

### 2.5.1 docs/governance/LIFECYCLE.md

Project lifecycle: the 7 AEE phases (inception → release), readiness gates, phase artifacts.

### 2.6 docs/services.md (if applicable)

Service and startup expectations per platform. Required when the project includes background services, tray applications, daemons, or OS-level startup integration.

### 2.7 docs/REQUIREMENTS.md

Formal, numbered requirements derived from the architecture. Each requirement is testable and traceable.

### 2.8 docs/TESTS.md

Test cases linked to requirements. Each test references one or more requirements. Defines smoke tests, platform tests, boundary tests, and regression structure.

---

## 3. Document Authority Hierarchy

When documents conflict, precedence is resolved top-down:

1. **AGENTS.md + docs/governance/*** — behavioral rules, hard constraints, stop conditions (highest). Governance docs inherit AGENTS.md's authority because AGENTS.md explicitly delegates to them.
2. **README.md** — project intent and scope
3. **docs/REQUIREMENTS.md** — what the system must do
4. **docs/ARCHITECTURE.md** — how the system is structured
5. **docs/TESTS.md** — how the system is verified
6. **LEDGER.md** — what has been done and what remains (sole authority for session state)
7. **docs/governance/SESSION-PROTOCOL.md** — how sessions work
8. **docs/services.md** — platform-specific startup/service behavior

If a requirement contradicts the architecture, the requirement wins. If AGENTS.md contradicts a requirement, AGENTS.md wins.

**Derivation vs. conflict resolution:** Requirements are derived from architecture (Section 15), meaning architecture is the *source* for requirements. However, once a requirement is accepted, it outranks architecture in the hierarchy. If a conflict arises between an accepted requirement and the architecture, the requirement wins — and the architecture must be updated to align. This is not circular: architecture informs what requirements *should* exist, but requirements govern what the system *must* do.

---

## 4. Session Lifecycle

Agents MUST follow structured session flows. Five session types are defined.

### 4.1 NEW SESSION (start)

Trigger: fresh conversation targeting the repository.

```
Load AGENTS.md, README.md, docs/ARCHITECTURE.md, docs/WORKFLOW.md,
docs/services.md (if it exists), docs/REQUIREMENTS.md, docs/TESTS.md, and LEDGER.md.

Output:
1. Current system understanding
2. Current known state from ledger
3. Open TODOs
4. Suggested next task

Then produce a Proposal.
```

Context window optimization (see Section 10):
- Read AGENTS.md in full
- Read only the last ~300 lines of LEDGER.md
- Read only the first ~200 lines of REQUIREMENTS.md and TESTS.md
- Read architecture.md by section header (first ~40 lines) unless a section is task-relevant

### 4.2 RESUME SESSION (resume)

Trigger: returning to ongoing work.

```
Load AGENTS.md and LEDGER.md.

Summarize:
- last completed task
- current objective
- open TODOs
- risks

Then propose next bounded task.
```

### 4.3 SAVE SESSION (save)

Trigger: end of a work session.

```
Prepare LEDGER.md entry for this session.

Include:
- what changed
- what was verified
- what remains incomplete
- next recommended step

Do not invent results.
```

### 4.4 GIT COMMIT (commit)

Trigger: preparing a version control commit.

```
Prepare commit summary:
- what changed
- why
- files touched
- checks performed

Generate commit message.
Then list commands to execute.
```

### 4.5 GIT UPDATE (sync)

Trigger: pulling latest changes.

```
1. Check repository status
2. Pull latest changes
3. Summarize what changed
4. Identify conflicts or risks
```

### 4.6 Session boundary rules

- A new conversation is a new session, NOT a new project
- All governance rules in AGENTS.md persist across sessions
- Agents MUST NOT reset or ignore project rules across conversation boundaries
- Past chat messages from previous conversations are not available; agents MUST rely on on-disk documents (ledger, requirements, tests) as the source of truth

---

## 5. Proposal Format

Before any non-trivial work, the agent MUST produce a proposal using exactly this structure:

```
## Proposal

Objective:      <what this task accomplishes>
Scope:          <what is included and what is excluded>
Assumptions:    <explicit BeliefArtifact IDs or stated assumptions this proposal relies on>
Inputs:         <what context, files, or state this depends on>
Outputs:        <what files, artifacts, or state changes will result>
Files touched:  <explicit list of files created, modified, or deleted>
Checks:         <what verification will be performed>
Stress-test:    <one adversarial challenge to the proposal's core assumptions>
Risks:          <what could go wrong or what is uncertain>
Rollback:       <how to undo this work if it fails>
Estimated cost: <low | medium | high — see Section 25>
Decision request: <what the human must approve before execution>
```

The `Assumptions:` and `Stress-test:` fields are mandatory per H13 (Epistemic Boundaries Required). A proposal without declared assumptions is a stop condition.

Rules:
- No non-trivial work begins without a proposal
- No proposal executes without human approval
- Proposals must be bounded — one task, not a plan for everything
- Proposals must not silently expand scope
- If new information changes the approach during execution, the agent must stop, update the proposal, and re-request approval

---

## 6. Ledger Entry Format

Every ledger entry MUST follow this structure:

```markdown
## [YYYY-MM-DD] Entry — <short title>

Objective:
What was done:
Files changed:
Checks run:
Results:
Token estimate: <low | medium | high>
Open TODOs:
Risks:
Next step:
```

Rules:
- Entries are append-only — never modify previous entries
- "What was done" must describe only actual outcomes, not intentions
- "Checks run" must list actual checks performed, or explicitly state "none"
- "Results" must report pass/fail/unknown — never claim success without evidence
- "Open TODOs" must be complete — this is the canonical TODO list. Use `- [ ]` for incomplete items and `- [x]` for completed items.
- "Next step" is the recommended starting point for the next session

---

## 7. Agent Role Definition

### Agents ARE:
- Proposal generators
- Assistants and drafting aides
- Consistency checkers (requirements ↔ tests ↔ architecture)
- Reviewers and summarizers
- Context loaders and state reconstructors

### Agents are NOT:
- Decision-makers
- Autonomous actors without human intent
- Sources of project truth
- Authorities on completion or correctness

### Behavioral rules:
- Agents SHALL never invent, infer, or assume undocumented project state
- Agents SHALL implement changes directly (creating/editing files) rather than asking the human to make manual edits, unless automatic edits fail
- All drafted material MUST be clearly labeled as a draft or proposal
- Agents MUST NOT claim that drafted material is "done"
- Agents MUST NOT bypass review, testing, or ledger updates
- All acceptance of drafts or edits to authoritative documents is a human decision

---

## 8. Hard Rules

These rules are non-negotiable. Violation of any hard rule is a stop condition.

### H1 — Ledger required
No ledger entry = work not done.

### H2 — Proposal required
No proposal = no execution.

### H3 — Cross-platform awareness
All work must consider every target platform. If a platform is unsupported or deferred, that must be stated explicitly.

### H4 — Environment isolation
No system-dependent assumptions. Virtual environments required. No reliance on global interpreters or system packages.

### H5 — Explicit startup
No hidden service logic. All startup behavior must be documented and inspectable.

### H6 — No silent scope expansion
If the task grows beyond the proposal, stop and re-propose.

### H7 — No undocumented state changes
Every file creation, modification, or deletion must be traceable to a proposal and recorded in the ledger.

### H8 — Documentation is implementation
Architecture-affecting changes MUST update relevant docs in the same work cycle. Documentation must not lag behind implementation.

### H9 — Execution timeout required
All agent-invoked commands MUST have a timeout. No command may run indefinitely. If a command hangs, it must be killed, recorded in the ledger, and escalated after one retry. See Section 27.

---

## 9. Stop Conditions

Agents MUST stop and request clarification if ANY of the following are true:

- Missing inputs (files, context, or dependencies not available)
- Unclear state (ledger is inconsistent or missing)
- Undocumented platform assumptions
- No proposal has been approved
- No ledger path exists (LEDGER.md missing or unwritable)
- Requirement-without-test detected
- Test-without-requirement detected
- Architecture contradicts requirements
- Proposed work would violate a hard rule
- Proposed work would silently expand scope

---

## 10. Context Window Management

Large governance files consume agent context rapidly. Agents MUST actively manage context window consumption.

### On session load:
- Read AGENTS.md in full (rules are authoritative, no shortcuts)
- Read only the **last ~300 lines** of LEDGER.md (recent entries + next-session block)
- Read only the **first ~200 lines** of REQUIREMENTS.md and TESTS.md (TOC + active items)
- Read architecture.md by section header only (~first 40 lines) unless a specific section is task-relevant
- Older ledger entries, deep requirement sections, and full architecture are loaded only when explicitly needed

### During a session:
- NEVER re-read a file already in context unless it has been modified since the last read
- Use line ranges for all reads of files longer than ~200 lines
- Prefer grep or semantic search over reading entire files when looking for specific content
- Batch file reads into a single call rather than sequential calls
- Keep responses concise — summarize rather than echoing large file contents
- Do not repeat plan or proposal contents after creating them
- After multi-step tasks, give a brief summary (2–4 sentences) rather than recapping every file touched

### Conversation summarization recovery:
Whenever the conversation is optimized, summarized, or truncated by the platform, agents MUST **immediately re-read AGENTS.md in full** before performing ANY further actions. Summarization loses nuance from project rules; the only way to restore it is to re-read the authoritative source. No exceptions.

### File size guidelines:
Track approximate line counts of governance files. Example thresholds:
- AGENTS.md: ~200–500 lines — read in full
- LEDGER.md: grows unbounded — read last ~300 lines
- REQUIREMENTS.md: ~100–400 lines — read first ~200
- TESTS.md: ~100–600 lines — read first ~200
- architecture.md: ~100–400 lines — read first ~40, expand by section

Treat context window exhaustion as a **preventable defect**.

---

## 11. Conflict and Consistency Handling

If an agent detects any of the following:

- A requirement without a corresponding test
- A test without a corresponding requirement
- Architecture that violates or contradicts requirements
- Ledger inconsistencies (e.g., completed TODO still listed as open)
- Documentation that contradicts implementation

The agent SHALL:
1. Report the issue explicitly
2. Reference exact document locations (file, line, requirement ID)
3. NOT propose fixes unless explicitly requested by the human
4. Record the inconsistency in the current session's ledger entry under "Risks"

---

## 12. Verification and Acceptance

### Verification minimum

Every meaningful task must record:
- What changed
- What was tested
- What passed
- What failed
- What is unknown

If checks were not run, that must be stated explicitly. "Not tested" is acceptable. "Tested" without evidence is not.

### Acceptance standard

Work is accepted ONLY if:
- Proposal matched execution (no scope creep)
- Checks were run and results recorded
- Ledger was updated
- Next step was defined

If any condition is not met, the work is **provisional only** and must be marked as such in the ledger.

---

## 13. Environment and Bootstrap Requirements

### 13.1 Environment isolation

Every project MUST be environment-controlled and system-agnostic:
- Use virtual environments (Python venv, Node node_modules, etc.)
- Do not rely on global interpreters or system packages
- Environment must be reproducible from a clean clone

### 13.2 Required scripts

Every project MUST have a single, documented way to set up and run:

```
scripts/
  setup.ps1     # Windows setup
  setup.sh      # Linux/macOS setup
  run.ps1       # Windows run
  run.sh        # Linux/macOS run
  exec.ps1      # (recommended) Windows command runner with timeout/logging
  exec.sh       # (recommended) POSIX command runner with timeout/logging
```

The `exec.*` scripts are optional but strongly recommended. They wrap all external tool invocations with timeout enforcement, exit code capture, and log output. When exec scripts exist, agents MUST use them for all external commands. See Section 27 for the execution safety protocol.

Setup scripts must:
- Create virtual environments
- Install dependencies
- Validate prerequisites
- Be idempotent (safe to run multiple times)

Run scripts must:
- Activate the environment
- Ensure dependencies are installed
- Launch the application entrypoint
- Be the single canonical way to start the system

### 13.3 Shell wrapper pattern

For projects with complex tooling (build systems, external tools, etc.), a unified shell wrapper is recommended:

```
shell.ps1     # Windows: canonical entry point for all tool invocations
shell.sh      # Linux/macOS: canonical entry point for all tool invocations
```

Benefits:
- Auto-bootstraps environment if missing
- Activates virtual environment automatically
- Ensures artifacts land in correct directories
- Prevents tool pollution at repository root
- Provides consistent logging and progress reporting

When shell wrappers exist, agents MUST use them for all tool invocations. Direct tool invocation is forbidden.

---

## 14. Cross-Platform Rules

Any work that affects the following MUST explicitly state impact on every target platform:
- Startup or shutdown behavior
- Service control or lifecycle
- File paths or directory structure
- Packaging or installation
- Local runtime behavior
- Tray or desktop integration
- Background execution
- IPC or inter-process communication

If one platform is intentionally unsupported, unaffected, or deferred, that MUST be stated explicitly.

Platform-specific logic MUST be isolated:
- Service/startup logic under `services/<platform>/`
- Platform-specific scripts clearly named or separated
- No platform assumptions copied between operating systems
- No behavior inferred from one OS applied to another

---

## 15. Requirements Schema

Requirements MUST be formal, numbered, and testable.

### Naming convention

```
REQ-<COMPONENT>-<NUMBER>

Components:
  BE    = Backend
  FE    = Frontend
  CLI   = CLI entrypoint and argument parsing
  CMD   = CLI subcommand behavior
  TRAY  = Tray application
  SVC   = Service/startup layer
  API   = API boundary
  CFG   = Configuration
  LOG   = Logging/diagnostics
  SEC   = Security
  XP    = Cross-platform
  INT   = Integration/boundary
  RTL   = RTL/HDL design (FPGA)
  SIM   = Simulation/testbench (FPGA)
  SYN   = Synthesis (FPGA)
  IMPL  = Implementation/place-and-route (FPGA)
  BSP   = Board support package (embedded Linux)
  IMG   = Image generation (embedded Linux)
  PKG   = Package/recipe (embedded Linux)
  DTS   = Device tree (embedded Linux)
  KRN   = Kernel configuration (embedded Linux)
  SCH   = Schematic (PCB)
  PCB   = PCB layout
  BOM   = Bill of materials (PCB)
  FAB   = Fabrication output (PCB)
  MCAD  = Mechanical/enclosure (PCB)

This list is extensible. Projects may define additional component codes
as needed, documented in their REQUIREMENTS.md naming convention section.
```

### Requirement format

```markdown
### REQ-BE-001 — Backend health endpoint

The backend MUST expose a health endpoint that returns the current service
status. The response MUST include at minimum: status (healthy/degraded/down),
uptime, and version.

- **Priority:** P1
- **Platform:** all
- **Testable:** yes
- **Test:** TEST-BE-001
- **Status:** draft | accepted | implemented | verified
```

### Rules:
- Every requirement MUST have a unique ID
- Every requirement MUST reference at least one test (or explicitly state "test pending")
- Every requirement MUST have a status
- Requirements with status "accepted" or higher are binding
- Requirements are derived from architecture — if architecture doesn't support a requirement, the architecture must be extended first

---

## 16. Test Specification Schema

Tests MUST be linked to requirements and structured for automation.

### Naming convention

```
TEST-<COMPONENT>-<NUMBER>
```

### Test format

```markdown
### TEST-BE-001 — Health endpoint returns valid status

**Requirement:** REQ-BE-001
**Type:** smoke | unit | integration | platform | boundary
**Platform:** all | windows | linux | macos
**Automated:** yes | no | planned

**Preconditions:**
- Backend is running in development mode

**Steps:**
1. Send GET request to health endpoint
2. Verify response status code is 200
3. Verify response body contains status, uptime, and version fields
4. Verify status value is one of: healthy, degraded, down

**Expected result:**
- Response is valid JSON with all required fields
- Status is "healthy" when backend is fully operational

**Pass criteria:** All steps pass
**Fail criteria:** Any step fails or response is malformed
```

### Rules:
- Every test MUST reference at least one requirement
- Tests with type "smoke" are run on every change
- Tests with type "platform" must specify which platform(s)
- Tests with type "boundary" verify that component boundaries are respected (e.g., tray cannot access backend internals)

---

## 17. Project Type Schemas

Different project types require different governance emphasis. The core workflow (Sections 1–12) applies to ALL project types. The following schemas define additional structure per type. Project types 17.1–17.4 cover software. Types 17.5–17.8 cover hardware, FPGA, embedded Linux, and PCB domains.

### 17.1 Python backend + web frontend

```
<project>/
├─ AGENTS.md
├─ LEDGER.md
├─ README.md
├─ .gitignore
├─ .gitattributes
├─ docs/
│  ├─ architecture.md
│  ├─ workflow.md
│  ├─ services.md
│  ├─ REQUIREMENTS.md
│  └─ TESTS.md
├─ backend/
│  ├─ pyproject.toml          # or requirements.txt
│  ├─ src/
│  │  └─ <package>/
│  │     ├─ __init__.py
│  │     ├─ main.py           # entrypoint
│  │     ├─ config.py
│  │     ├─ api/              # API routes
│  │     ├─ services/         # business logic
│  │     ├─ models/           # data models
│  │     └─ utils/
│  └─ tests/
├─ frontend/
│  ├─ package.json
│  ├─ src/
│  └─ tests/
├─ scripts/
│  ├─ setup.ps1
│  ├─ setup.sh
│  ├─ run.ps1
│  └─ run.sh
└─ services/
   ├─ windows/
   ├─ linux/
   └─ macos/
```

Additional governance:
- Backend owns all state and logic
- Frontend communicates only via explicit API
- API boundary must be documented in architecture.md
- Health endpoint is a P1 requirement

### 17.2 Python backend + web frontend + tray application

Same as 17.1, plus:

```
├─ tray/
│  ├─ <framework config>
│  ├─ src/
│  └─ tests/
```

Additional governance:
- Tray MUST NOT contain backend logic
- Tray MUST NOT own application state
- Tray communicates via explicit interfaces (HTTP API, IPC, CLI)
- Tray is replaceable without affecting backend behavior
- Tray framework decision must be documented in architecture.md
- Platform-specific tray behavior must be documented in services.md

### 17.3 CLI tool (Python)

```
<project>/
├─ AGENTS.md
├─ LEDGER.md
├─ README.md
├─ .gitignore
├─ .gitattributes
├─ docs/
│  ├─ architecture.md
│  ├─ workflow.md
│  ├─ REQUIREMENTS.md
│  └─ TESTS.md
├─ src/
│  └─ <package>/
│     ├─ __init__.py
│     ├─ cli.py               # CLI entrypoint
│     ├─ commands/
│     └─ utils/
├─ tests/
├─ scripts/
│  ├─ setup.ps1
│  ├─ setup.sh
│  ├─ run.ps1
│  └─ run.sh
└─ pyproject.toml
```

Additional governance:
- No services.md unless the CLI has daemon/background modes
- Cross-platform rules still apply to all file path and process behavior
- CLI must have `--help` for all commands
- Exit codes must be documented and tested

### 17.4 Library / SDK (Python)

```
<project>/
├─ AGENTS.md
├─ LEDGER.md
├─ README.md
├─ .gitignore
├─ .gitattributes
├─ docs/
│  ├─ architecture.md
│  ├─ workflow.md
│  ├─ REQUIREMENTS.md
│  ├─ TESTS.md
│  └─ api-reference.md
├─ src/
│  └─ <package>/
├─ tests/
├─ examples/
├─ scripts/
│  ├─ setup.ps1
│  ├─ setup.sh
│  ├─ run.ps1
│  └─ run.sh
└─ pyproject.toml
```

Additional governance:
- Public API surface must be documented in api-reference.md
- Breaking changes require a ledger entry and version bump proposal
- No services.md unless the library manages background processes
- Examples must be tested or at minimum validated during CI

### 17.5 Embedded / hardware project

All project types include the governance files from Section 2 and the required scripts from Section 13.2. This type adds:

```
├─ hardware/
│  ├─ boards/
│  ├─ scripts/
│  └─ ip_repo/               # (FPGA) or schematics/ (PCB)
├─ .work/                     # ALL build artifacts (never committed)
│  ├─ outputs/
│  ├─ env/
│  └─ logs/
├─ shell.ps1                  # unified tool wrapper (Windows)
└─ shell.sh                   # unified tool wrapper (POSIX)
```

Additional governance:
- Shell wrappers are mandatory for all tool invocations
- `.work/` directory contains ALL generated artifacts — never at repo root
- `.work/` is in `.gitignore` — never committed
- Tool-specific pollution checks at session start
- Target hardware connectivity and deployment documented in AGENTS.md
- Build verification (source ↔ deployed) is mandatory before testing

### 17.6 FPGA / RTL project

All project types include the governance files from Section 2 and the required scripts from Section 13.2. This type adds:

```
├─ rtl/
│  ├─ src/
│  ├─ testbenches/
│  └─ sims/
├─ constraints/
│  ├─ timing/
│  └─ physical/
├─ ip_cores/
├─ docs/
│  └─ hw-interfaces.md
├─ .work/
│  ├─ synth/
│  ├─ impl/
│  ├─ bitstreams/
│  └─ logs/
├─ shell.ps1
└─ shell.sh
```

Additional governance:
- Shell wrappers are mandatory for all Vivado/Quartus/EDA tool invocations
- Constraint files (`.xdc`, `.sdc`, etc.) are governance artifacts — changes require proposals
- Verification vocabulary is: syntax/lint → simulation → synthesis → implementation/place-and-route → timing closure → bitstream
- Timing closure is a formal milestone, not an implicit side effect of the build
- `.work/` contains all generated artifacts — never at repo root
- Tool invocations MUST use batch/non-interactive modes only

### 17.7 Yocto / embedded Linux BSP project

All project types include the governance files from Section 2 and the required scripts from Section 13.2. This type adds:

```
├─ meta-<project>/
│  ├─ conf/
│  ├─ recipes-bsp/
│  ├─ recipes-core/
│  └─ recipes-kernel/
├─ kas/
│  ├─ distro.yml
│  └─ board.yml
├─ configs/
│  ├─ machine/
│  └─ distro/
├─ docs/
│  └─ bsp-guide.md
├─ .work/
│  ├─ downloads/
│  ├─ sstate-cache/
│  ├─ tmp/
│  └─ logs/
├─ shell.ps1
└─ shell.sh
```

Additional governance:
- KAS YAML files are governance artifacts — changes require proposals
- Machine and distro configurations must be documented in architecture.md
- Verification vocabulary is: layer compatibility → bitbake build → image generation → target boot test → package validation
- Build durations may be long; proposals must state expected build time and artifact size
- Shared state and download caches belong under `.work/` when the project manages them locally
- Host/environment assumptions must be documented explicitly due to cross-build complexity

### 17.8 PCB / hardware design project

All project types include the governance files from Section 2 and the required scripts from Section 13.2. This type adds:

```
├─ schematics/
├─ layout/
├─ bom/
├─ fabrication/
├─ 3d-models/
├─ docs/
│  └─ hw-spec.md
├─ .work/
│  ├─ exports/
│  ├─ drc/
│  └─ logs/
├─ shell.ps1
└─ shell.sh
```

Additional governance:
- BOM files are governance artifacts — changes require proposals
- Schematic review is a formal gate before layout work begins
- Verification vocabulary is: ERC → DRC → BOM validation → 3D clearance/fit check → fabrication output review
- ECAD-MCAD synchronization points must be documented in workflow.md
- Generated Gerbers, pick-and-place files, 3D exports, and manufacturing outputs belong under `.work/` or `fabrication/` — not at repo root
- Mechanical constraints and enclosure assumptions must be documented explicitly

---

## 18. Scaffold Bootstrap Procedure

When an agent is asked to scaffold a new project using this workflow:

**Note:** The bootstrap procedure is exempt from the proposal requirement (H2). The human's request to scaffold a project serves as implicit approval. The first formal proposal is produced at Step 6, after the scaffold is complete.

### Step 1: Gather inputs
- Project name
- Project type (from Section 17)
- Target platforms (Windows, Linux, macOS — which subset)
- Primary language/runtime
- Frontend framework (if applicable)
- Tray framework (if applicable)
- Any known technology decisions

### Step 2: Create repository structure
- Create directory structure per the selected project type schema
- Create `.gitignore` with appropriate patterns for the language/framework
- Create `.gitattributes` with line-ending rules per file type
- Create `.gitkeep` files in empty directories
- Initialize git repository

### Step 3: Create governance files
- **AGENTS.md** — focused hub (~100–150 lines): project identity, platform, tech stack, file registry pointing to `docs/governance/*`, quick command reference, and project-type-specific rules from the relevant Section 17 subsection.
- **docs/governance/RULES.md** — hard rules (H1–H9) and stop conditions, adapted from Sections 8–9
- **docs/governance/WORKFLOW.md** — session lifecycle, proposal format, ledger format, adapted from Sections 4–6
- **docs/governance/ROLES.md** — agent role definition and behavioral rules, adapted from Section 7
- **docs/governance/CONTEXT-BUDGET.md** — context window management and credit optimization, adapted from Sections 10 and 25
- **docs/governance/VERIFICATION.md** — verification and acceptance standards, adapted from Sections 11–12
- **docs/governance/DRIFT-METRICS.md** — drift detection and feedback loop protocol, adapted from Section 26
- **README.md** — project overview, architecture summary, component descriptions, structure, goals, status
- **LEDGER.md** — bootstrap entry recording the scaffold creation
- **docs/ARCHITECTURE.md** — component model, boundaries, interfaces, platform expectations, runtime modes
- **docs/WORKFLOW.md** — work loop, proposal rules, milestones, cross-platform rules, verification rules
- **docs/services.md** — (if applicable) platform service/startup expectations
- **docs/REQUIREMENTS.md** — initial requirements derived from architecture (may be sparse)
- **docs/TESTS.md** — initial test specifications linked to requirements (may be sparse)

### Step 4: Create bootstrap scripts
- `scripts/setup.ps1` and `scripts/setup.sh` — environment setup (may be stubs initially)
- `scripts/run.ps1` and `scripts/run.sh` — application run (may be stubs initially)
- Stubs should print a clear "not yet implemented" message and exit cleanly

### Step 5: Create initial ledger entry

```markdown
## [YYYY-MM-DD] Entry — Project scaffold

Objective: Create initial project scaffold with governance files
What was done: Repository structure, governance docs, bootstrap scripts created
Files changed: (list all created files)
Checks run: directory structure verified, governance files present, scripts executable
Results: scaffold complete, no runtime code yet
Open TODOs: (adapt to selected project type — omit items that do not apply)
- [ ] Extend architecture with concrete interface specifications
- [ ] Define formal requirements
- [ ] Define test specifications
- [ ] Implement primary code scaffold (e.g., backend, CLI entrypoint, library API)
- [ ] Implement frontend scaffold (if applicable)
- [ ] Implement service/startup integration (if applicable)
Risks: technology decisions not yet finalized
Next step: extend architecture.md with concrete, testable specifications
```

### Step 6: Verify and propose
- Verify all governance files are present and internally consistent
- Verify .gitignore covers all expected artifact patterns
- Verify .gitattributes handles all expected file types
- Produce a proposal for the first implementation task (typically: extend architecture)
- Wait for human approval before proceeding

---

## 19. Git Workflow

### Commit messages
Commits should be concise and traceable:
```
<type>: <short description>

<body: what changed and why>

Co-Authored-By: <agent name> <agent email>
```

Types: `scaffold`, `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### Branch strategy
Not prescribed by this workflow. Use whatever strategy the project adopts (trunk-based, feature branches, etc.). The workflow is branch-agnostic.

### PR expectations
Pull requests should be:
- Narrow (one bounded task)
- Explainable (what changed, why, what was checked)
- Cross-platform aware (state impact per platform)
- Explicit about uncertainty (what was not tested, what is provisional)

---

## 20. Technology Decision Tracking

Technology decisions (framework choices, IPC mechanisms, database engines, etc.) MUST be tracked explicitly. Two approaches:

### Option A: decisions section in architecture.md

```markdown
## Technology Decisions

### DEC-001 — Backend framework: FastAPI
**Date:** YYYY-MM-DD
**Status:** accepted
**Rationale:** async support, OpenAPI generation, lightweight
**Alternatives considered:** Flask, Django
**Decided by:** <human>

### DEC-002 — Frontend framework: React + Vite
...
```

### Option B: dedicated docs/decisions.md

Same format, separate file. Useful when decisions are numerous.

Rules:
- Decisions MUST be recorded before implementation begins
- Decisions MUST have a status (proposed, accepted, superseded)
- Superseded decisions are never deleted — they are marked as superseded with a reference to the replacement
- Agents MUST NOT make technology decisions — they may propose, but the human decides

---

## 21. Anti-Patterns

The following behaviors are explicitly forbidden:

1. **Silent scope expansion** — doing more than the proposal approved
2. **Invented state** — claiming something exists, works, or was tested without evidence
3. **Skipped ledger** — completing work without a ledger entry
4. **Implicit service logic** — background behavior that is not documented
5. **Platform assumption copying** — assuming Linux behavior works on Windows or vice versa
6. **Documentation debt** — implementing without updating docs in the same cycle
7. **Authority overreach** — agents claiming decisions, completion, or correctness
8. **Context window waste** — reading entire large files when only a section is needed
9. **Orphaned files** — creating temporary, status, or session files outside the ledger
10. **Undocumented technology choices** — using a framework or tool without a recorded decision
11. **Hung processes** — invoking commands without timeouts, launching GUI tools, triggering interactive prompts, or running commands that open pagers
12. **Credit waste** — re-reading unchanged files, reading entire files for one line, verbose confirmations that echo back file contents, redundant proposals

---

## 22. Quick Command Reference

Agents should recognize these short commands from the human:

| Command  | Meaning                          |
| -------- | -------------------------------- |
| `start`  | New session (Section 4.1)        |
| `resume` | Resume from ledger (Section 4.2) |
| `save`   | Write ledger entry (Section 4.3) |
| `commit` | Prepare git commit (Section 4.4) |
| `sync`   | Pull latest changes (Section 4.5)|
| `audit`  | Run drift/health checks (Section 26)|

---

## 23. Checklist: Is This Workflow Being Followed?

Use this checklist to audit compliance:

- Does AGENTS.md exist and define all hard rules?
- Does LEDGER.md exist with at least one entry?
- Does every recent task have a ledger entry?
- Does every ledger entry include all required fields?
- Is there a proposal for the current or most recent task?
- Did the most recent task's execution match its proposal scope?
- Were checks run and results recorded?
- Is the next step defined in the most recent ledger entry?
- Are governance files internally consistent (requirements ↔ tests ↔ architecture)?
- Are technology decisions recorded before they are implemented?
- Are cross-platform impacts stated for platform-sensitive work?
- Is the documentation current with the implementation?

### Drift and health metrics (see Section 26 for details)
- Is the requirements ↔ tests ↔ architecture consistency score 100%?
- Are there stale TODOs open for more than 5 sessions?
- Is LEDGER.md under ~500 lines (or has it been archived)?
- Are governance files within their size thresholds?
- Do the last 5 ledger entries all have proposals, verification, and next steps?
- Has documentation been updated as recently as the code it describes?

If any answer is "no," that is a defect to be addressed before continuing.

---

## 24. Modular AGENTS.md Architecture

This workflow supports two governance layouts:

1. **Monolithic** — a single `AGENTS.md` containing all governance inline
2. **Modular** — a focused `AGENTS.md` hub plus delegated governance documents under `docs/governance/`

The modular layout is RECOMMENDED for all projects and REQUIRED when a monolithic `AGENTS.md` would exceed ~200 lines.

### 24.1 Design goals

The modular layout exists to:
- reduce context consumption
- improve instruction discoverability
- make authority boundaries explicit
- let agents load only the governance documents needed for the current task

### 24.2 Required structure for modular projects

```
AGENTS.md
docs/
  governance/
    rules.md
    workflow.md
    roles.md
    context-budget.md
    verification.md
    drift-metrics.md
```

### 24.3 AGENTS.md responsibilities

In the modular layout, AGENTS.md MUST remain small and focused. It should contain:
- project identity and purpose
- target platforms
- primary language/runtime
- project type
- quick command reference
- governance file registry
- project-type-specific rules

AGENTS.md MUST NOT duplicate large blocks of rules that live in `docs/governance/*`.

### 24.4 Governance document responsibilities

- `rules.md` — hard rules and stop conditions
- `workflow.md` — session lifecycle, proposal format, ledger format
- `roles.md` — role boundaries and behavioral rules
- `context-budget.md` — context loading rules and credit optimization protocol
- `verification.md` — verification, acceptance, and audit standards
- `drift-metrics.md` — health signals, drift detection, and corrective actions

### 24.5 Authority

AGENTS.md remains the highest-authority document. Governance docs inherit that authority because AGENTS.md explicitly delegates to them. If a governance document contradicts AGENTS.md, AGENTS.md wins.

---

## 25. Credit and Token Optimization

Agent workflows must be optimized for the least amount of credit use consistent with correctness.

### 25.1 Core principle

Credits are spent on:
- loading context
- making tool calls
- producing verbose responses
- rerunning expensive checks

Treat unnecessary credit consumption as a process defect.

### 25.2 Estimated cost field

Every proposal MUST include:

`Estimated cost: low | medium | high`

Guidance:
- **low** — docs-only work, single-file edits, small scaffolds
- **medium** — multi-file implementation, routine refactors, standard test runs
- **high** — architecture changes, large builds, FPGA implementation, Yocto image builds, broad audits

### 25.3 Token estimate field

Every ledger entry MUST include:

`Token estimate: low | medium | high`

This is an estimate of actual session cost, useful for identifying wasteful task patterns over time.

### 25.4 Lazy loading protocol

On session start, agents SHOULD load only:
- `AGENTS.md`
- `docs/governance/RULES.md`
- `docs/governance/CONTEXT-BUDGET.md`
- recent `LEDGER.md`

Load these on demand:
- `docs/governance/WORKFLOW.md` when preparing proposals or ledger entries
- `docs/governance/ROLES.md` when role boundaries are relevant
- `docs/governance/VERIFICATION.md` when testing, auditing, or accepting work
- `docs/governance/DRIFT-METRICS.md` when running `audit` or diagnosing process health

### 25.5 Response economy rules

Agents MUST:
- summarize rather than echo file contents
- avoid repeating proposal contents after creation
- batch file reads and writes
- prefer grep/semantic search over full-file reads
- avoid long explanatory prose unless the human requests it
- provide only the evidence needed to support a conclusion

Agents MUST NOT:
- quote large sections of unchanged files
- restate rules already in AGENTS.md unless needed for clarification
- produce “status theater” messages that add no new information

### 25.6 Efficient verification order

Run the cheapest checks first:
1. static validation / lint / syntax
2. type checks / unit tests
3. integration tests
4. expensive builds / hardware flows / long-running checks

If a cheaper check fails, fix that before running more expensive checks unless there is a specific reason not to.

### 25.7 Credit-waste anti-patterns

Examples of waste:
- re-reading unchanged governance files
- reading entire files for one symbol or line
- verbose confirmations of obvious actions
- repeating the full plan after creating it
- running broad test suites before syntax/lint passes
- performing duplicate searches for the same concept

---

## 26. Drift Detection and Feedback Loops

Specifications, rules, documentation, and agent behavior drift over time. This workflow includes health signals and corrective actions to detect and address that drift.

### 26.1 Health signals

Agents SHOULD evaluate these signals on `audit`, and MAY evaluate them at session start for large or long-running projects.

#### Consistency score

Check:
- every requirement has at least one test
- every test maps to at least one requirement
- architecture supports all accepted requirements

Target: **100%**

#### Ledger health

Check:
- every entry has all required fields
- open TODOs are accurate
- stale TODOs are identified (open for more than 5 sessions)
- no completed TODO remains listed as open

#### Documentation currency

Check:
- architecture reflects implementation
- README reflects current structure and status
- requirements/tests reflect the accepted architecture

#### Governance size health

Check:
- AGENTS.md remains within target size
- governance docs remain focused
- LEDGER.md remains under manageable size (~500 lines) or has been archived

#### Rule compliance

Check the most recent ledger entries:
- was a proposal present?
- was verification recorded?
- was a next step recorded?
- was scope respected?

### 26.2 Drift response protocol

If a health signal fails:

1. Report the failure explicitly
2. Reference the exact files/sections involved
3. Record the issue in the current ledger entry under Risks
4. Recommend the smallest bounded corrective task

### 26.3 Ledger compression

When `LEDGER.md` exceeds ~500 lines:
- archive older entries into `docs/ledger-archive.md`
- keep a short summary block at the top of `LEDGER.md`
- retain only recent entries and active TODOs in `LEDGER.md`

The archive MUST preserve history. No information is deleted.

### 26.4 Audit command

The `audit` command runs the health checks above and reports:
- pass/fail per signal
- a summary score or status
- recommended corrective tasks

### 26.5 Feedback loop priority

When drift is detected, correct the cheapest root cause first:
1. compress/optimize context
2. update stale docs
3. remove or split oversized governance files
4. strengthen rules or load order
5. revise workflow if the same failure repeats

---

## 27. Execution Safety and Timeout Protection

Agents must not launch commands that hang indefinitely or require the human to kill them manually.

### 27.1 Timeout requirement

All agent-invoked commands MUST have a timeout.

Default guidance:
- read/query commands: ~10 seconds
- lint/typecheck/tests: ~30 seconds
- normal builds: ~120 seconds
- long hardware flows: explicit higher timeout stated in the proposal

### 27.2 Non-interactive execution

Agents MUST use non-interactive flags whenever available, for example:
- `--no-input`
- `--yes`
- `--batch`
- `--non-interactive`
- `--no-pager`

Agents MUST NOT intentionally launch:
- GUI tools
- pagers
- interactive REPLs
- commands that block on credentials or prompts

### 27.3 Timeout handling protocol

If a command exceeds its timeout, the agent MUST:
1. kill the process tree
2. record the timeout in the ledger
3. retry at most once if there is a clear reason
4. escalate to the human if the retry also times out

### 27.4 Shim / wrapper execution layer

Projects SHOULD provide:

```
scripts/exec.ps1
scripts/exec.sh
```

These scripts are the canonical command runners and should:
- enforce timeouts
- capture stdout/stderr
- log exit codes
- kill child processes on timeout
- normalize tool invocation behavior

When `exec.*` scripts exist, agents MUST use them for all external commands.

### 27.5 Shell wrapper and env shim guidance

For toolchains prone to hanging or polluting the environment (e.g., Vivado, Quartus, Yocto shells), projects SHOULD use:
- `shell.ps1` / `shell.sh` for environment setup
- `exec.ps1` / `exec.sh` for bounded command execution

This shim layer isolates environment setup from command execution and reduces the risk of agents hanging their own shell context.

### 27.6 Known hung-process patterns

Examples:
- Vivado GUI mode instead of batch mode
- Python REPL instead of script execution
- git commands that trigger auth prompts
- commands that open pagers or full-screen UIs
- watch-mode test runners unless explicitly requested

These are forbidden unless the human explicitly requests an interactive session.

---

## 28. Multi-Agent Coordination

When multiple agents work on the same project, the ledger becomes the coordination surface.

### 28.1 Agent identity

Ledger entries SHOULD record the agent name or role responsible for the work. This makes concurrent work traceable.

### 28.2 Scope isolation

Each agent MUST stay within its approved proposal scope. Agents must not edit files outside their bounded task unless they stop and re-propose.

### 28.3 Conflict detection

Before executing a task, an agent SHOULD check whether files in scope have changed since the last relevant ledger entry. If they have, the agent must re-evaluate the proposal before continuing.

### 28.4 Test separation

When practical, implementation and test-writing should occur in separate sessions or by separate agents. This reduces the risk of writing tests that merely mirror the implementation instead of validating the contract.

### 28.5 Shared rules

All agents in the project read the same governance files. No agent may operate under a private or divergent rule set without explicit human approval and documentation.
