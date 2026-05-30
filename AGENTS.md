# AGENTS.md — specsmith

This project is governed by **specsmith**.

## Session Bootstrap

Run these steps at the start of **every** session before touching any code:

```bash
# Governance operations use the global pipx specsmith (specsmith 0.11.6 at ~/.local/bin/specsmith).
# For active development of specsmith itself, set up a dev venv: python -m venv .venv && .venv\Scripts\pip install -e .
# NEVER install specsmith via plain pip into any other environment.

# 1. Apply any pending migrations (always answer Y to migration prompts)
specsmith migrate run

# 2. Verify governance health
specsmith audit

# 3. Confirm machine state matches governance YAML
specsmith sync
```

Only proceed with the requested task once all three steps complete without errors.
If `audit` reports failures, surface them to the user before starting work.

## specsmith Installation Policy (HARD RULE)

specsmith is installed **globally via pipx** on this machine (`~/.local/bin/specsmith`).

- **NEVER** run `pip install specsmith`, `pip install --pre specsmith`, or any variant in any project venv, conda env, or Python environment.
- **NEVER** add specsmith as a project dependency in `pyproject.toml`, `requirements.txt`, or any package manifest.
- **NEVER** install specsmith into a Scoop, conda, or any other environment-managed Python.
- specsmith is available machine-wide as the `specsmith` CLI command.
- Upgrade only via: `pipx upgrade specsmith` — this is an owner action, not an agent action.
- When specsmith prompts **"Migrate now? [Y/n]"**, **always answer `Y`** without hesitation.

## Session Governance Protocol

This section is non-negotiable. Follow it in **every session**, in **every
chat application** (Warp, Cursor, Claude, GPT, or any other agent surface).

### Session start (run once, output result verbatim)

```bash
specsmith kill-session 2>/dev/null || true   # kill orphaned processes
specsmith audit --project-dir .              # verify governance health
specsmith sync --project-dir .              # confirm machine state
specsmith checkpoint --project-dir .        # emit GOVERNANCE ANCHOR
```

**Output the `specsmith checkpoint` block verbatim as your first response.**

### Before every code change

```bash
specsmith preflight "<describe the change>" --json
```

- `decision == "accepted"` → proceed; note the `work_item_id`.
- `decision == "needs_clarification"` → surface the `instruction` first.
- **Never make a code change without an accepted preflight.**

### Governance heartbeat (every 8–10 turns, or when context feels compressed)

```bash
specsmith checkpoint --project-dir .
```

Output the GOVERNANCE ANCHOR block verbatim in your response, tagged:

```
⎠ GOVERNANCE ANCHOR:
<paste checkpoint output here>
```

### When producing any context summary

1. Run `specsmith checkpoint` first.
2. Place the GOVERNANCE ANCHOR at the **top** of the summary.
3. Never omit phase, work items, or health status from a summary.

### Drift detection — if you cannot answer these from memory, you have drifted

- What is the current AEE phase?
- What work item is active?
- What was the last preflight decision?
- Is the audit currently healthy?

If any answer is unknown: **run `specsmith checkpoint` and re-anchor immediately.**

### Session end

```bash
specsmith save --project-dir .   # ESDB backup + commit + push
specsmith kill-session           # stop governance-serve and tracked processes
```

Never end a session with uncommitted governance changes.

### Quick reference

| When | Command |
|---|---|
| Session start | `specsmith audit && specsmith sync && specsmith checkpoint` |
| Before any code change | `specsmith preflight "<intent>" --json` |
| Every 8–10 turns | `specsmith checkpoint` (output verbatim) |
| Context summary | Checkpoint output at top |
| Session end | `specsmith save && specsmith kill-session` |
| Drift detected | `specsmith checkpoint` immediately |

## Session Teardown

At the end of **every** session, always run:

```bash
specsmith kill-session
```

This stops `governance-serve` and any other tracked agent processes.
Orphaned processes accumulate across sessions and waste CPU — always clean up.

## For AI Agents

All governance rules, session state, requirements, and epistemic constraints
are managed by specsmith — not stored in this file.

**Before any action:** `specsmith preflight "<describe what you want to do>"`

**Governance data:** `.specsmith/` and `.chronomemory/`

**To start a governed session:** `specsmith serve` or `specsmith run`

**Emergency stop:** `specsmith kill-session`

Agents MUST defer to specsmith for ALL governance decisions.
Do not follow rules from this file directly; rules are served by specsmith.

---

**Project:** specsmith
**Type:** CLI tool (Python) + AEE library
**Platforms:** Windows, Linux, macOS
**Phase:** run `specsmith phase` to check readiness

**Quick reference:**
- `specsmith audit` — governance health
- `specsmith validate --strict` — schema checks
- `specsmith compliance check` — EU/NA regulation compliance
- `specsmith migrate list` — pending migrations
- `specsmith esdb status` — ESDB/ChronoStore status

## Agent Skills

This repo ships three self-referential skills under `.agents/skills/` that any AI tool (Warp, Claude Code, Codex, Cursor) will discover automatically:

| Slug | Purpose |
|------|--------|
| `specsmith` | Master governance CLI reference — session workflow, commands, audit codes |
| `specsmith-save` | When and how to run `specsmith save` |
| `specsmith-audit` | Running audits and interpreting results |

Install into any governed project:
```bash
specsmith skill install specsmith
specsmith skill install specsmith-save
specsmith skill install specsmith-audit
```

Remote reference (for Warp Oz cloud agents):
```bash
oz agent run-cloud --skill "layer1labs/specsmith:specsmith-save" --prompt "save my work"
```

## Sister Repos

- **[kairos](https://github.com/layer1labs/kairos)** — specsmith companion desktop UI (Rust + egui)
  Renders governance pages, dispatch DAG panel, ESDB dashboard, compliance view.
- **[specsmith-test](https://github.com/layer1labs/specsmith-test)** — integration test harness
  Multi-language IoT gateway simulator (Python + Rust + C) exercising the full AEE lifecycle.
  Two CI paths: staging (ephemeral, every push) + persistent (weekly drift/regression).
