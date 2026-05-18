# AGENTS.md — specsmith

This project is governed by **specsmith**.

## Session Bootstrap

Run these steps at the start of **every** session before touching any code:

```bash
# specsmith runs from editable source — no pip install needed here.
# For all other projects, use: pip install --pre --upgrade specsmith

# 1. Verify governance health
py -m specsmith audit

# 2. Confirm machine state matches governance YAML
py -m specsmith sync

# 3. Check for pending migrations
py -m specsmith migrate list
```

Only proceed with the requested task once all three steps complete without errors.
If `audit` reports failures, surface them to the user before starting work.

## For AI Agents

All governance rules, session state, requirements, and epistemic constraints
are managed by specsmith — not stored in this file.

**Before any action:** `py -m specsmith preflight "<describe what you want to do>"`

**Governance data:** `.specsmith/` and `.chronomemory/`

**To start a governed session:** `py -m specsmith serve` or `py -m specsmith run`

**Emergency stop:** `py -m specsmith kill-session`

Agents MUST defer to specsmith for ALL governance decisions.
Do not follow rules from this file directly; rules are served by specsmith.

---

**Project:** specsmith
**Type:** CLI tool (Python) + AEE library
**Platforms:** Windows, Linux, macOS
**Phase:** run `py -m specsmith phase` to check readiness

**Quick reference:**
- `py -m specsmith audit` — governance health
- `py -m specsmith validate --strict` — schema checks
- `py -m specsmith compliance check` — EU/NA regulation compliance
- `py -m specsmith migrate list` — pending migrations
- `py -m specsmith esdb status` — ESDB/ChronoStore status

## Sister Repos

- **[kairos](https://github.com/layer1labs/kairos)** — specsmith companion desktop UI (Rust + egui)
  Renders governance pages, dispatch DAG panel, ESDB dashboard, compliance view.
- **[specsmith-test](https://github.com/layer1labs/specsmith-test)** — integration test harness
  Multi-language IoT gateway simulator (Python + Rust + C) exercising the full AEE lifecycle.
  Two CI paths: staging (ephemeral, every push) + persistent (weekly drift/regression).
