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


## GitHub Operations

Use **`gh` CLI** (GitHub CLI) as the **first and preferred** tool for all GitHub operations —
issues, PRs, releases, code scanning alerts, and repository data.

**MCP GitHub server is last resort only** — use it only when `gh` CLI genuinely cannot do the task.

```bash
gh issue list --state open
gh pr list --state open
gh api repos/{owner}/{repo}/code-scanning/alerts --jq '[.[] | select(.state=="open")]'
gh release create v1.0.0 dist/* --generate-notes
```

## Code Quality Gate

Before **any** commit, both checks MUST pass with zero violations:

```bash
ruff check src/ tests/           # linting — zero violations required
ruff format --check src/ tests/  # formatting — zero violations required
```

Never suppress a `ruff` violation with `# noqa` unless it is a documented false positive.
When using `# noqa`, always include the rule code and a one-line explanation:

```python
except Exception:  # noqa: BLE001  # intentional: fire-and-forget cleanup; log is written above
```

## CodeQL Safe Patterns

Follow these patterns to keep CodeQL (security + quality scanning) alerts at zero:

**Path sanitization** — always use `os.path.realpath()`, never `Path.resolve()`:
```python
import os
# CORRECT — CodeQL recognises os.path.realpath() as a taint sanitizer
safe_path = os.path.realpath(str(user_input))

# WRONG — CodeQL does NOT recognise Path.resolve() as a sanitizer
safe_path = Path(user_input).resolve()  # triggers py/path-injection
```

**Import discipline** — no inline `import X` when `from X import Y` exists at module level:
```python
from specsmith.compliance import ComplianceChecker  # module-level ← fine

def my_test():
    import specsmith.compliance as c  # WRONG: triggers py/import-and-import-from
```

**Empty except blocks** — always add comment + `# noqa: BLE001`:
```python
# CORRECT
except Exception:  # noqa: BLE001  # intentional: ...
    pass

# WRONG — bare empty except triggers CodeQL empty-except alert
except Exception:
    pass
```

## YAML-First Governance (Current Mode)

Requirements live in `docs/requirements/*.yml`; tests in `docs/tests/*.yml`. Edit YAML files, run `specsmith sync`, commit both YAML + JSON. `REQUIREMENTS.md` / `TESTS.md` are deprecated. To migrate from markdown mode: `specsmith migrate run && specsmith sync && specsmith audit`.

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

