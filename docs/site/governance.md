# Governance Model

## The Problem specsmith Solves

AI coding agents are stateless. They don't remember what happened last session, don't know what's been tested, and don't follow consistent processes unless told to. specsmith generates the governance layer that makes AI-assisted development auditable and structured.

## The Closed-Loop Workflow

Every AI agent action follows five steps:

1. **Propose** — The agent describes what it wants to do, why, and what risks exist. For non-trivial changes, this is a formal proposal in LEDGER.md.
2. **Check** — The human reviews the proposal. No execution without approval (Hard Rule H2).
3. **Execute** — The agent implements the approved change.
4. **Verify** — The agent runs verification tools (from the [Tool Registry](tool-registry.md)) and records what passed and failed.
5. **Record** — The agent writes a ledger entry with what changed, what was tested, and what's next.

This loop ensures every change is proposed, approved, verified, and recorded.

## File Hierarchy (Authority Order)

Every specsmith-governed project has this authority hierarchy — higher files override lower ones when they conflict:

1. **AGENTS.md + docs/governance/*** — Highest. Governance rules are law.
2. **README.md** — Project intent and scope.
3. **docs/REQUIREMENTS.md** — What the system must do.
4. **docs/ARCHITECTURE.md** — How the system is structured.
5. **docs/TESTS.md** — How the system is verified.
6. **LEDGER.md** — Sole authority for session state (what's been done, what's next).

## AGENTS.md — The Governance Hub

This is the first file every AI agent reads. It contains:

- **Project summary** — type, language, platforms, spec version
- **Governance file registry** — table of modular governance files with load timing
- **Authority hierarchy** — the precedence order above
- **Type-specific rules** — tailored to the project type (e.g., patent claim rules, Rust clippy rules, legal compliance tracking)
- **Quick command reference** — start, resume, save, commit, sync, audit

specsmith generates AGENTS.md with type-specific rules. For example, a patent application gets rules about claim self-containment and prior art tracking, while a Rust CLI gets rules about clippy warnings and doc comments.

## Modular Governance

When AGENTS.md is kept small (~100-150 lines), governance details are delegated to six modular files under `docs/governance/`:

| File | Content | When Loaded |
|------|---------|-------------|
| `RULES.md` | Hard rules H1-H11, stop conditions | Every session start |
| `WORKFLOW.md` | Session lifecycle, proposal format, ledger format | Every session start |
| `ROLES.md` | Agent role boundaries, behavioral rules | Every session start |
| `CONTEXT-BUDGET.md` | Context management, credit optimization | Every session start |
| `VERIFICATION.md` | Verification standards, tools listing, acceptance criteria | When performing verification |
| `DRIFT-METRICS.md` | Drift detection, feedback loops, health signals | On audit or session start |

This lazy-loading approach minimizes token consumption — agents only load VERIFICATION.md when they're actually running tests, not at every session start.

## LEDGER.md — The Session Memory

The ledger is append-only. Agents write entries here after every task:

```markdown
## 2026-04-01 — Add export command

- **Proposal**: Add `specsmith export` to generate compliance reports
- **Changes**: Created exporter.py, wired CLI command, added tests
- **Verified**: 113 tests pass, lint clean, mypy clean
- **Next**: Update documentation site
```

This is how context persists across sessions. When an agent starts with `resume`, it reads the last ledger entry to know where things stand.

## Requirements and Tests

`docs/REQUIREMENTS.md` uses numbered IDs:

```markdown
### REQ-CLI-001
- **Description**: specsmith init scaffolds a governed project from interactive prompts or YAML config
```

`docs/TESTS.md` links tests to requirements:

```markdown
### TEST-CLI-002
- **Covers**: REQ-CLI-001
- **Description**: specsmith init --config creates project from YAML
```

`specsmith audit` checks that every REQ has at least one TEST with a `Covers:` reference. `specsmith export` generates the full coverage matrix.

## Drift Detection

`specsmith audit` checks six health dimensions:

1. **File existence** — Are AGENTS.md, LEDGER.md, and recommended files present?
2. **REQ↔TEST coverage** — Does every requirement have test coverage?
3. **Ledger health** — Is the ledger within size limits? Are there too many open TODOs?
4. **Governance size** — Are individual governance files within line-count thresholds?
5. **Tool configuration** — Does the CI config reference the expected verification tools?
6. **Consistency** — Do AGENTS.md references resolve? Are requirement IDs unique?

`specsmith audit --fix` auto-repairs what it can: creates missing stubs, compresses oversized ledgers, regenerates CI configs.

## Hard Rules (H11 and H12)

Two rules were added in v0.2.3 specifically for long-running agentic workflows:

**H11 — No unbounded loops or blocking I/O without a deadline**

Every loop or blocking wait in agent-written scripts and automation must have an explicit deadline or iteration cap, a fallback exit path when the deadline fires, and a diagnostic message on timeout. Violating patterns include `while True:` / `while ($true)` / `for (;;)` with no deadline guard, I/O polling loops with no deadline, and `sleep` inside a loop with no termination condition.

`specsmith validate` enforces this by scanning `.sh`, `.cmd`, `.ps1`, and `.bash` files under `scripts/` and the project root for infinite-loop patterns without a recognised deadline/timeout guard.

**H12 — Windows multi-step automation via .cmd files**

On Windows, multi-step or heavily-quoted automation sequences must be written to a temporary `.cmd` file and executed from there. Inline multi-line quoting on Windows is fragile and causes avoidable hangs. Do not use `.ps1` files for this class of automation unless there is a concrete PowerShell-only requirement.

See `docs/governance/RULES.md` in any governed project for the full set of H1–H12 rules and stop conditions.

## YAML-First Governance (v0.12+)

As of specsmith v0.12 the governance authority has flipped from Markdown-primary to **YAML-primary**. If your project has a `.specsmith/governance-mode` file containing `yaml`, then:

- `docs/requirements/*.yml` and `docs/tests/*.yml` are the **canonical sources** — edit these, not the Markdown files.
- `docs/REQUIREMENTS.md` and `docs/TESTS.md` are **generated artifacts** — they are overwritten on every sync.
- `.specsmith/requirements.json` and `.specsmith/testcases.json` are JSON caches updated by `specsmith sync`.

### The sync pipeline

```bash
# Full pipeline: YAML → JSON cache → Markdown artifacts
specsmith sync

# Regenerate only Markdown (skip JSON rewrite)
specsmith generate docs

# Dry-run: see what would change without writing
specsmith generate docs --check

# CI gate: exits 1 if JSON cache is out of sync with YAML
specsmith sync --check
```

### Strict schema validation

```bash
specsmith validate --strict           # human-readable output
specsmith validate --strict --json    # structured {ok, strict_errors, strict_warnings}
```

Enforces 8 checks: duplicate REQ IDs, duplicate TEST IDs, missing required fields, orphaned TESTs (reference non-existent REQ), untested REQs (warning), duplicate titles (warning), machine-state drift (warning). Exits 1 on errors; warnings do not block.

### Domain YAML files

Requirements are split into domain files, each covering a logical range of REQ IDs:

| File | REQ range | Domain |
|---|---|---|
| `docs/requirements/governance.yml` | REQ-001..064 | Core AEE governance |
| `docs/requirements/agent.yml` | REQ-065..129 | Nexus + CI |
| `docs/requirements/harness.yml` | REQ-130..160 | Slash commands + subagents |
| `docs/requirements/intelligence.yml` | REQ-161..220 | Instinct, eval, memory |
| `docs/requirements/context.yml` | REQ-244..247 | Context window |
| `docs/requirements/esdb.yml` | REQ-248..262 | ESDB + skills + MCP |
| `docs/requirements/ai_intelligence.yml` | REQ-263..299 | AI model intelligence |
| `docs/requirements/yaml_governance.yml` | REQ-300..399 | YAML governance layer |

To add a new requirement, edit the appropriate domain YAML file and run `specsmith sync`.

### Migrating from Markdown-primary

```bash
python scripts/migrate_governance_to_yaml.py
```

This idempotent script: removes duplicate REQs from REQUIREMENTS.md, re-syncs JSON, exports JSON to grouped YAML files, and writes `.specsmith/governance-mode = yaml`. Safe to re-run.

### CI enforcement

The `validate-strict` and `sync-check` jobs in `.github/workflows/ci.yml` run on every push and PR:

```yaml
- name: Validate governance schema (strict)
  run: specsmith validate --strict --json

- name: Check machine state sync
  run: specsmith sync --check
```

Both jobs block the build on failure. See [YAML Governance Reference](yaml-governance.md) for the full API.
