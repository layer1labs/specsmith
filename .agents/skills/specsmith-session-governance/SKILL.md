# Specsmith Session Governance Skill

This skill describes the **mandatory session protocol** for any agent working
in a specsmith-governed project. It prevents silent drift and keeps governance
state alive across context summarization without modifying the agent runtime.

## Why agents drift
When a conversation gets long, any chat application (Warp, Cursor, Claude,
GPT) summarizes the history. That summary discards: the current work item ID,
the last preflight decision, the project phase, and any uncommitted changes.
The agent then operates on stale or invented governance state.

## The fix: three rules

### Rule 1 — Initialization (every session start)
```bash
specsmith kill-session 2>/dev/null || true   # kill orphaned processes
specsmith audit --project-dir .              # verify governance health
specsmith sync --project-dir .              # confirm machine state
specsmith checkpoint --project-dir .        # emit and display the anchor
```
Output the checkpoint verbatim as your first response. This establishes the
governance baseline that all subsequent work traces back to.

### Rule 2 — Preflight gate (before EVERY proposed code change)
```bash
specsmith preflight "<describe the change you intend to make>" --json
```
- If `decision == "accepted"`: proceed with the work item ID in scope.
- If `decision == "needs_clarification"`: surface the instruction to the user
  before making any changes.
- Never make a code change without an accepted preflight.

### Rule 3 — Heartbeat (every 8-10 turns, or when context > 60%)
```bash
specsmith checkpoint --project-dir .
```
Output the GOVERNANCE ANCHOR block verbatim in your response. Tag it clearly:

```
⎠ GOVERNANCE ANCHOR (output of `specsmith checkpoint`):
╔═════...
║ GOVERNANCE ANCHOR  2026-05-19T22:43:04Z
║ Project : specsmith
...
╚═════...
```

**When producing any context summary, ALWAYS include the most recent
GOVERNANCE ANCHOR verbatim at the top of the summary.** The anchor is the
minimum viable governance state that must survive summarization.

## End of session
```bash
specsmith save --project-dir .    # ESDB backup + commit + push
specsmith kill-session            # clean up processes
```
Never end a session with uncommitted governance changes.

## Detecting drift (self-check)
If you notice you cannot answer any of these from memory, you have drifted
and MUST re-anchor immediately:
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
| Every 8-10 turns | `specsmith checkpoint` (output verbatim) |
| Context summary | Include checkpoint output at top |
| Session end | `specsmith save && specsmith kill-session` |
| Drift detected | `specsmith checkpoint` immediately |
