# AGENTS.md — specsmith

This project is governed by **specsmith**.

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
