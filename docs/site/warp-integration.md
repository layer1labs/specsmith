# Warp Terminal Integration

specsmith v0.12.0 ships native integration with [Warp](https://www.warp.dev) terminal at two levels:

1. **MCP governance server** — Warp/Oz (and any MCP client) can call governance commands as structured tool calls without shell roundtrips.
2. **Repository workflows** — seven `Ctrl+Shift+R`-searchable workflows appear automatically when you open this repo in Warp.

---

## Native MCP Server Setup

### What it does

`specsmith mcp serve` starts a zero-dependency MCP server (JSON-RPC 2.0, protocol pin 2024-11-05) over stdio. Once configured in Warp, Oz can call any of six governance tools natively — getting back structured JSON, not terminal output.

### One-time setup

**Step 1:** Get the config snippet:

```bash
specsmith mcp install-warp
```

Output:
```json
{
  "specsmith-governance": {
    "command": "specsmith",
    "args": ["mcp", "serve", "--project-dir", "/path/to/your/project"]
  }
}
```

**Step 2:** Open **Warp → Settings → Agents → MCP servers** and paste the JSON.

After saving, Warp/Oz will show `specsmith-governance` as an available tool server. Oz will call governance commands automatically when they are relevant to the task.

### Using with oz agent run (inline)

For one-off cloud agent runs, pass the config inline:

```bash
oz agent run \
  --mcp '{"specsmith-governance": {"command": "specsmith", "args": ["mcp", "serve"]}}' \
  --prompt "check governance health, run a preflight for my next change, and report what phase we are in"
```

---

## MCP Tools Reference

| Tool | Description | Required inputs | Returns |
|---|---|---|---|
| `governance_audit` | Run the full governance audit | `project_dir` (optional) | `healthy`, `passed`, `failed`, `checks[]` |
| `governance_checkpoint` | Emit GOVERNANCE ANCHOR snapshot | `project_dir` (optional) | `anchor`, `phase`, `health`, `req_count`, `test_count`, `esdb_chain_valid`, `recent_work_items` |
| `governance_preflight` | Preflight a proposed change | `intent` (required), `project_dir` | `decision`, `work_item_id`, `instruction` |
| `governance_phase` | Current AEE phase + readiness | `project_dir` (optional) | `phase`, `label`, `pct`, `failing_checks` |
| `governance_req_list` | List all requirements | `project_dir`, `status_filter` | `total`, `covered`, `reqs[]` |
| `governance_trace_seal` | Seal a milestone or decision | `seal_type`, `description`, `project_dir` | `sealed`, `seal_id`, `entry_hash` |

### governance_audit

Returns a complete governance health picture. Oz uses this to decide whether to proceed with a change.

```json
{
  "healthy": true,
  "passed": 27,
  "failed": 0,
  "fixable": 0,
  "suppressed": 0,
  "checks": [
    {"name": "file-exists:AGENTS.md", "passed": true, "message": "Required file AGENTS.md exists"},
    ...
  ]
}
```

### governance_checkpoint

Emits the GOVERNANCE ANCHOR — include this verbatim in any context summary. Oz calls this automatically every 8–10 turns via the `specsmith-session-governance` skill.

```json
{
  "anchor": "SPECSMITH-ANCHOR-2026-06-01T20:00:00Z",
  "project": "specsmith",
  "phase": "release",
  "phase_label": "🚀 Release",
  "phase_pct": 100,
  "health": "clean",
  "req_count": 321,
  "test_count": 325,
  "esdb_chain_valid": true,
  "recent_work_items": ["WI-7320B3C9"]
}
```

### governance_preflight

Gate every code change through this. Returns `accepted` + `work_item_id` to proceed, or `needs_clarification` with an instruction to refine the intent.

```json
{
  "decision": "accepted",
  "work_item_id": "WI-7320B3C9",
  "instruction": "Change request matched existing governance scope. Proceed under Specsmith verification.",
  "intent": "change"
}
```

### governance_phase

Tells Oz what phase the project is in and what checks are failing.

```json
{
  "phase": "release",
  "label": "🚀 Release",
  "pct": 75,
  "description": "CHANGELOG updated, release tag created, compliance report filed.",
  "failing_checks": ["Trace vault has seals"]
}
```

### governance_req_list

List requirements, optionally filtered by status (`planned`, `implemented`, `partial`, `deprecated`).

```json
{
  "total": 321,
  "covered": 321,
  "reqs": [
    {"id": "REQ-363", "title": "specsmith mcp serve: native stdio MCP server...", "status": "implemented", "covered": true},
    ...
  ]
}
```

### governance_trace_seal

Seal types: `decision`, `milestone`, `audit-gate`, `logic-knot`, `stress-test`, `epistemic`.

```json
{
  "sealed": true,
  "seal_id": "SEAL-0001",
  "seal_type": "milestone",
  "description": "v0.12.0 released — native MCP governance server",
  "timestamp": "2026-06-01T20:00:00+00:00",
  "entry_hash": "a3f9b2c1..."
}
```

---

## Repository Workflows (Ctrl+Shift+R)

Opening the specsmith repo in Warp automatically makes seven governance workflows available via `Ctrl+Shift+R` search.

| Workflow name | What it runs | When to use |
|---|---|---|
| specsmith — Session Start | kill → migrate → audit → sync → checkpoint | Start of every session |
| specsmith — Audit | `specsmith audit` | Check governance health |
| specsmith — Checkpoint | `specsmith checkpoint` | Every 8–10 turns, or before a context summary |
| specsmith — Preflight | `specsmith preflight "{{intent}}" --json` | Before any code change |
| specsmith — Save | `specsmith save` | After completing a feature or fix |
| specsmith — Phase Status | `specsmith phase show` | See current AEE phase + failing checks |
| specsmith — Session End | `specsmith save && specsmith kill-session` | End of every session |

### Session workflow

```
1. Ctrl+Shift+R → "specsmith session start" → Enter
   (runs: kill → migrate → audit → sync → checkpoint)

2. Make your changes, using Preflight before each one

3. Ctrl+Shift+R → "specsmith save" → Enter

4. At end of day: Ctrl+Shift+R → "specsmith session end" → Enter
```

---

## Skill Auto-Discovery

The specsmith repo ships five governance skills in `.agents/skills/`. Warp/Oz auto-discovers these and loads them at session start:

| Skill | Purpose |
|---|---|
| `specsmith` | Master CLI reference — session workflow, commands, audit codes |
| `specsmith-audit` | Running audits and interpreting results |
| `specsmith-save` | When and how to run `specsmith save` |
| `specsmith-session-governance` | Drift prevention, heartbeat every 8–10 turns, preflight gate |
| `release-pilot` | Gitflow release-cut workflow |

The `specsmith-session-governance` skill is the most important for AI sessions — it instructs Oz to enforce the preflight gate before every code change and emit a checkpoint every 8–10 turns automatically.

---

## Third-party CLI agent toolbar

Warp shows its coding agent toolbelt automatically for natively supported agents (claude, codex, gemini, cursor). For **specsmith** and **aider** — which are not yet natively supported — add the following regex once in **Warp → Settings → Agents → Third party CLI agents → Commands that enable the toolbar**:

```
specsmith\s+run|aider
```

Once saved, the toolbelt appears whenever `specsmith run` or `aider` is active in any pane, giving you:

| Feature | Available |
|---|---|
| Rich Input editor (`Ctrl+G`) | ✓ |
| Attach code as context | ✓ |
| File Explorer | ✓ |
| Tab Configs | ✓ |
| Remote Control | ✓ |
| Agent notifications | via OSC 9 (see below) |

### Desktop notifications

`specsmith run` emits OSC 9 notifications directly from the REPL — no plugin required. Warp (and iTerm2, Windows Terminal) intercepts the escape sequence and surfaces it as a desktop popup. The notification fires once on session start:

```
specsmith run | <project> | governance active
```

### REPL detection

When Grace starts through `specsmith run`, it sets `SPECSMITH_RUN_ACTIVE=1` in the environment. Child governance commands can detect the local REPL context. Detection table for all supported REPLs:

| REPL | Toolbar | Detection signal |
|---|---|---|
| `specsmith run` | Custom regex | `SPECSMITH_RUN_ACTIVE=1` |
| `aider` | Custom regex | `AIDER_MODEL` / `AIDER_CONFIG` |
| `claude` | Native | `CLAUDE_CODE_ENTRYPOINT` |
| `codex` | Native | `CODEX_CLI_SESSION` |
| `gemini` | Native | `GEMINI_CLI` |
| `cursor` | Native | `CURSOR_TRACE_ID` |

To regenerate `.warp/SETUP.md` with the full setup guide:

```bash
specsmith integrate warp
```

---

## Troubleshooting

**`specsmith mcp serve` not found in Warp MCP servers list**

Ensure specsmith is installed via pipx (not pip):
```bash
pipx install specsmith
which specsmith   # should point to ~/.local/bin/specsmith or ~/pipx/venvs/...
```

**MCP tool call returns an error**

Run `specsmith audit` manually to check governance health. Some tools (like `governance_req_list`) require `.specsmith/requirements.json` to exist — run `specsmith sync` first.

**Checkpoint returns `phase: "unknown"`**

The project directory needs a `docs/SPECSMITH.yml` or `scaffold.yml` file. Run `specsmith init` or `specsmith import` to set up governance.

**`governance_trace_seal` fails**

The `.specsmith/` directory must exist. Run `specsmith sync` first.
