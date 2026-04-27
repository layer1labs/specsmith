# forge-cli — Agent Governance

**Project:** forge-cli
**Type:** CLI tool (Python) — Section 17.3
**Platforms:** Windows, Linux, macOS
**Spec version:** 0.3.0

---

> **SESSION START — AUTO-LOAD REQUIRED**
> You have just read this file. **Do not ask for confirmation.**
> Immediately read the following files before doing anything else:
> 1. `docs/governance/RULES.md`
> 2. `docs/governance/WORKFLOW.md`
> 3. `docs/governance/ROLES.md`
> 4. `docs/governance/CONTEXT-BUDGET.md`
>
> Then read `LEDGER.md` to restore session state. Proceed directly to the start protocol below.

---

## Governance File Registry

This project uses the modular governance layout. Read this file in full on every session. Load governance docs per the timing column.

| File | Content | Load timing |
| ---- | ------- | ----------- |
| `docs/governance/RULES.md` | Hard rules H1–H9, stop conditions | **AUTO-LOAD** (no prompt) |
| `docs/governance/WORKFLOW.md` | Session lifecycle, proposal format, ledger format | **AUTO-LOAD** (no prompt) |
| `docs/governance/ROLES.md` | Agent role boundaries, behavioral rules | **AUTO-LOAD** (no prompt) |
| `docs/governance/CONTEXT-BUDGET.md` | Context management, credit optimization | **AUTO-LOAD** (no prompt) |
| `docs/governance/VERIFICATION.md` | Verification standards, acceptance criteria | When performing verification |
| `docs/governance/DRIFT-METRICS.md` | Drift detection, feedback loops, health signals | On `audit` or session start |

Other project documents:

| File | Content |
| ---- | ------- |
| `README.md` | Project overview, structure, goals, status |
| `LEDGER.md` | Append-only work record (sole authority for session state) |
| `docs/ARCHITECTURE.md` | Components, boundaries, interfaces, platform expectations |
| `docs/WORKFLOW.md` | Work loop, milestones, PR expectations |
| `docs/REQUIREMENTS.md` | Formal, numbered, testable requirements |
| `docs/TEST_SPEC.md` | Test cases linked to requirements |

---

## Authority Hierarchy

1. **AGENTS.md + docs/governance/*** — highest (governance docs inherit this file's authority)
2. **README.md** — project intent and scope
3. **docs/REQUIREMENTS.md** — what the system must do
4. **docs/ARCHITECTURE.md** — how the system is structured
5. **docs/TEST_SPEC.md** — how the system is verified
6. **LEDGER.md** — sole authority for session state
7. **docs/WORKFLOW.md** — how work proceeds

---

## Project-Specific Rules
- CLI must have `--help` for all commands
- Exit codes must be documented and tested
- No services.md unless daemon/background modes are added
- Cross-platform rules apply to all file path and process behavior

---

## Epistemic Governance (AEE)

This project follows Applied Epistemic Engineering (AEE) principles. Every proposal MUST:
- State its `Assumptions:` field (H13 — Epistemic Boundaries Required)
- State its `Stress-test:` field — one adversarial challenge to the proposal's assumptions

Run `specsmith epistemic-audit` to check epistemic health:
- Equilibrium = all belief artifacts stress-tested with no critical failures
- Certainty ≥ 0.7 (default threshold)
- No Logic Knots (conflicting accepted requirements)

`specsmith trace seal decision "<description>"` — seal any significant decision
`specsmith stress-test` — adversarial challenges against REQUIREMENTS.md
`specsmith belief-graph` — visualize BeliefArtifact dependency graph

Stop condition (H13): P1 requirement with confidence below MEDIUM = work stops.

---

## Session Lifecycle

### Start Protocol
1. Load `docs/governance/RULES.md`, `WORKFLOW.md`, `ROLES.md`, `CONTEXT-BUDGET.md` — **already done if you followed the auto-load instruction above**
2. Read `LEDGER.md` — restore session state
3. `specsmith sync` — pull latest changes
4. `specsmith update --check` — verify specsmith is current
5. Check branch: verify you're on the correct branch for the task
6. Propose next task

### During Work
- After each task: `save` → `specsmith commit` (if verification passes)
- Propose commit after successful verification + ledger save
- Batch pushes: push after milestones, not every commit
- Refuse to work on main directly (use feature branches)

### End Protocol
1. `specsmith session-end` — run checklist
2. Commit any uncommitted work
3. Push all unpushed commits
4. If feature complete: propose PR

## Quick Command Reference

| Command        | Meaning                                        |
| -------------- | ---------------------------------------------- |
| `start`        | New session (sync + update check + branch check) |
| `resume`       | Resume from ledger                             |
| `save`         | Write ledger entry                             |
| `commit`       | `specsmith commit` (audit + commit)            |
| `push`         | `specsmith push` (with safety checks)          |
| `sync`         | `specsmith sync` (pull + conflict warning)     |
| `audit`        | `specsmith audit`                              |
| `branch`       | `specsmith branch create`                      |
| `pr`           | `specsmith pr` (create PR with governance)     |
| `update`       | `specsmith update` (check + install + migrate) |
| `session-end`  | `specsmith session-end` (end checklist)        |

**specsmith install / update:**

```bash
# Recommended — global isolated install
pipx install specsmith
pipx inject specsmith anthropic openai  # add LLM providers
pipx upgrade specsmith                  # update

# Or with pip
pip install specsmith
specsmith self-update
```
