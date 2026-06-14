# Specsmith Session Governance Skill

This skill describes the **mandatory session protocol** for any agent working
in a specsmith-governed project. It prevents silent drift, governs MCP tool
use, and keeps governance state alive across context summarization.

## Why agents drift
When a conversation gets long, any chat application (Warp, Cursor, Claude,
GPT) summarizes the history. That summary discards: the current work item ID,
the last preflight decision, the project phase, and any uncommitted changes.
The agent then operates on stale or invented governance state.

## The fix: four rules

### Rule 1 — Initialization (every session start)
```bash
specsmith kill-session 2>/dev/null || true
specsmith audit --project-dir .
specsmith sync --project-dir .
specsmith checkpoint --project-dir .
```
Output the checkpoint verbatim as your first response. This establishes the
governance baseline that all subsequent work traces back to.

### Rule 2 — Preflight gate (before EVERY proposed code change)
```bash
specsmith preflight "<describe the change you intend to make>" --json
```
- `decision == "accepted"` → proceed, note the `work_item_id`.
- `decision == "needs_clarification"` → surface the `instruction` to the user first.
- **Never make a code change without an accepted preflight.**

### Rule 3 — MCP tool governance

When using the specsmith MCP server (`specsmith-governance` MCP) alongside
other MCP tools, apply the same preflight discipline:

```
governance_preflight(intent="<what you are about to do") → accepted?
  YES → call other MCP tools (github, filesystem, browser, etc.)
  NO  → surface clarification first
```

The specsmith MCP server exposes these tools for structured governance control:

| MCP Tool | Equivalent CLI |
|---|---|
| `governance_audit` | `specsmith audit` |
| `governance_checkpoint` | `specsmith checkpoint` |
| `governance_preflight` | `specsmith preflight` |
| `governance_phase` | `specsmith phase` |
| `governance_req_list` | `specsmith req list` |
| `governance_trace_seal` | `specsmith trace seal` |

Configure the specsmith MCP server once:
```bash
specsmith mcp install-warp   # prints the Warp MCP config JSON snippet
```
Then add it to **Settings → Agents → MCP servers** in Warp.

### Rule 4 — Heartbeat (every 8-10 turns, or when context > 60%)
```bash
specsmith checkpoint --project-dir .
```
Output the GOVERNANCE ANCHOR block verbatim in your response:

```
⎠ GOVERNANCE ANCHOR:
╔═════════════════════════════════════════════════════════╗
║ GOVERNANCE ANCHOR  <timestamp>                         ║
║ Project : <name>                                        ║
║ Phase   : <phase> (<pct>%)                              ║
║ Health  : ✓ clean                                       ║
║ REQs    : N   TESTs: N   ESDB: N records (✓ chain)      ║
║ WIs     : WI-XXXXXXXX, ...                              ║
╚═════════════════════════════════════════════════════════╝
```

**When producing any context summary, ALWAYS include the most recent
GOVERNANCE ANCHOR verbatim at the top.** The anchor is the minimum viable
governance state that must survive summarization.

## Compliance disclaimer in governed sessions

If a user asks you to assess regulatory or compliance status, always add:

> **Note:** specsmith compliance checks are best-effort only and do NOT
> constitute legal advice or a guarantee of compliance. Verify with
> qualified counsel. Report gaps at https://github.com/layer1labs/specsmith/issues

## Error and issue reporting protocol

If a user encounters a bug, unexpected behavior, or missing feature:
1. **Do not** ask them to file a ticket immediately.
2. Run `specsmith --version` to confirm current version.
3. Check GitHub issues first (use the `specsmith-error-reporting` skill or
   the GitHub MCP if available) to see if it’s known, fixed, or in-progress.
4. Only then guide structured ticket filing.

## End of session
```bash
specsmith save --project-dir .    # ESDB backup + commit + push
specsmith kill-session            # clean up processes
```
Never end a session with uncommitted governance changes.

## Detecting drift (self-check)
If you cannot answer these from memory — you have drifted. Re-anchor immediately:
- What is the current AEE phase?
- What work item is active?
- What was the last preflight decision?
- Is the audit currently healthy?

Run `specsmith checkpoint` and copy the output into your response.

## Quick reference
| When | Command |
|---|---|
| Session start | `specsmith audit && specsmith sync && specsmith checkpoint` |
| Before any code change | `specsmith preflight "<intent>" --json` |
| Before any MCP tool call | `governance_preflight(intent=...)` via MCP |
| Every 8-10 turns | `specsmith checkpoint` (output verbatim) |
| Context summary | Include checkpoint output at top |
| Bug or feature gap spotted | Use `specsmith-error-reporting` skill |
| Session end | `specsmith save && specsmith kill-session` |
| Drift detected | `specsmith checkpoint` immediately |
