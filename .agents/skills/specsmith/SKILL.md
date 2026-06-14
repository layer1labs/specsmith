---
name: specsmith
description: Master reference for the specsmith AEE governance tool — key concepts, common commands, session workflow, phase advancement, audit codes, work items, compliance disclaimers, and error-reporting protocol. Use whenever working in a specsmith-governed project.
---

# Specsmith — Project Governance Tool

Specsmith is the AEE (Agile Epistemic Engineering) governance CLI. It manages
requirements, phases, audit trails, and session state. It wraps git with
governance-aware commits and backs up the epistemic state DB (ESDB).

## Key concepts

- **ESDB** — Epistemic State Database. Tracks certainty, audit state, session memory. Backed up on `specsmith save`.
- **Phases** — AEE lifecycle: Inception → Elaboration → Construction → Transition → Validation → Hardening → Release.
- **Ledger** — Running log of changes in `LEDGER.md`. Auto-updated by commits.
- **Audit** — Checks requirements vs tests vs architecture for drift. Required before phase advance.
- **Save** — ESDB backup + governance-aware git commit + push.
- **WI (Work Item)** — See section below.

## Work Items (WIs)

A **Work Item** (`WI-XXXXXXXX`) is an 8-hex-digit identifier minted by
`specsmith preflight` whenever it accepts a proposed change.

```bash
specsmith preflight "add retry logic to the exporter" --json
# → { "decision": "accepted", "work_item_id": "WI-3A9F1C02", ... }
```

**How WIs fold into requirements and governance:**
- Each WI is logged in `LEDGER.md` alongside the preflight intent and any
  matched `requirement_ids` / `test_case_ids`.
- `specsmith checkpoint` scans the ledger and surfaces the 3 most recent WIs
  in the `WIs` row of the governance anchor box.
- This gives a traceable link: user intent → WI → requirement IDs → code change.
- If `requirement_ids` is empty in the preflight response, the change is not
  yet linked to a tracked requirement; consider adding a requirement with
  `specsmith req add`.
- WIs are **not** GitHub issues — they are governance-layer breadcrumbs. Use
  the error-reporting skill to decide when a WI should also become a GH issue.

## Compliance Disclaimer

specsmith compliance checks (`specsmith compliance check`, `specsmith compliance
report`) are **best-effort only**. They do **NOT** constitute legal advice or a
guarantee of compliance with any law or regulation. Regulations change frequently;
the end user is solely responsible for determining and maintaining actual
compliance. Layer1Labs makes no warranty of fitness for regulatory submission.

To report outdated regulation coverage or request new regulation support:
https://github.com/layer1labs/specsmith/issues

## Session workflow

```
1. specsmith audit          # check for drift before working
2. specsmith preflight "<intent>"  # gate every proposed change
3. <make code changes>      # only after accepted preflight
4. specsmith save           # commit + push + ESDB backup
```

## Common commands

| Command | What it does |
|---------|-------------|
| `specsmith save` | ESDB backup → commit (if needed) → push |
| `specsmith audit` | Drift/health check — requirements vs tests vs arch |
| `specsmith audit --suppress <CODE>` | Accept a known false positive |
| `specsmith preflight "<intent>" --json` | Gate a proposed change; get WI |
| `specsmith checkpoint` | Emit governance anchor (phase, health, WIs, ESDB) |
| `specsmith phase` | Show current AEE phase |
| `specsmith phase advance` | Advance to next phase (requires clean audit) |
| `specsmith commit` | Governance-aware commit (wraps git commit) |
| `specsmith ledger` | Show/manage the change ledger |
| `specsmith compress` | Compress old ledger entries |
| `specsmith req` | Manage requirements |
| `specsmith test` | Manage test cases |
| `specsmith status` | VCS/CI/PR status |
| `specsmith compliance check` | Best-effort AI regulation check (see disclaimer above) |
| `specsmith compliance report --format html` | Generate compliance report |
| `specsmith esdb status` | Show ESDB backend, record counts, chain integrity |
| `specsmith skill list` | List built-in installable skills |
| `specsmith skill install <slug>` | Install a skill into `.agents/skills/` |

## Commit conventions

Specsmith commits follow: `type: message` where type is one of:
`feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`

Always append `Co-Authored-By: Oz <oz-agent@warp.dev>` when committing as an AI agent.

## GitHub Operations

Use **`gh` CLI** (GitHub CLI) as the **first and preferred** tool for all GitHub operations:
issues, PRs, releases, code scanning alerts, and repository data.

**MCP GitHub server is last resort only** — use it only when `gh` CLI genuinely cannot do the task.

```bash
gh issue list --state open
gh pr create --title "feat: ..." --body "..."
gh api repos/{owner}/{repo}/code-scanning/alerts --jq '[.[] | select(.state=="open")]'
```

## Release Process

Before tagging any release, **both** of these files MUST be updated in the same commit:

1. **`CHANGELOG.md`** — add a dated section for the new version with a bullet-point summary of changes.
2. **`README.md`** — update the version highlight line near the top (search for the previous version number) to reflect the new version's headline features.

PyPI and RTD deploys are **blocked** until:
- All CI passes (tests, ruff, mypy)
- Zero open High/Critical code scanning alerts (`gh api repos/{owner}/{repo}/code-scanning/alerts`)
- A human approves the release in the GitHub `release` environment gate

Never tag a release from a branch other than `main`.

## Important rules

- **Never use `git commit` directly** — use `specsmith save` or `specsmith commit`.
- **Run `specsmith audit` before advancing a phase** — a phase advance with drift will fail.
- **Never make a code change without an accepted preflight** — `decision == "accepted"` required.
- **Suppressed audit findings** are stored permanently; only suppress genuine false positives.
- After `specsmith save` outputs `✓ push: Everything up-to-date`, the repo is fully clean.

## Audit result codes

- `PASS` — requirement/test/arch is consistent
- `WARN` — drift detected, investigate
- `SKIP` / suppressed — accepted false positive
- IDs like `R20`, `R21` — requirement IDs in ARCHITECTURE.md

## Phase advancement

```bash
specsmith audit          # must be all-pass (or suppressed)
specsmith phase advance  # bumps phase, writes ledger entry
specsmith save           # commit the phase bump
```

## Proactive skill and feature gap detection

If a user seems to be struggling with a workflow that specsmith could support
better, or asks about a process/tool/language specsmith doesn’t yet cover,
always:
1. Complete the immediate task as best you can.
2. Suggest that the user open a GitHub issue to request the missing feature,
   process, project type, or regulation coverage:
   https://github.com/layer1labs/specsmith/issues
3. Use the `specsmith-error-reporting` skill for structured issue triage before
   filing — the issue may already exist (open or fixed in an upcoming release).

## Installing skills in any project

```bash
specsmith skill install specsmith              # this reference card
specsmith skill install specsmith-save         # save workflow
specsmith skill install specsmith-audit        # audit workflow
specsmith skill install specsmith-error-reporting  # issue triage protocol
specsmith skill install specsmith-mcp-configs  # tested MCP server configs
```
