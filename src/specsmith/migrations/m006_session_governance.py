# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""M006 — Inject Session Governance Protocol into AGENTS.md.

What this migration does
------------------------
Adds the mandatory ``## Session Governance Protocol`` section to AGENTS.md
when it is absent. This section teaches any agent (Warp, Cursor, Claude,
GPT, or any other chat surface) to:

1. Run ``specsmith checkpoint`` at session start and emit the GOVERNANCE ANCHOR
   as the first response.
2. Gate every code change behind ``specsmith preflight``.
3. Emit ``specsmith checkpoint`` every 8–10 turns as a heartbeat so governance
   state survives context summarisation.
4. Include the GOVERNANCE ANCHOR at the top of any context summary.
5. Run ``specsmith save && specsmith kill-session`` at session end.

This is the most impactful upgrade for preventing silent governance drift in
long agentic sessions.

Non-destructive:
- AGENTS.md is backed up to ``.specsmith/agents.md.m006.bak`` before modification.
- The migration is idempotent: re-running it when the section is already present
  is a no-op.
"""

from __future__ import annotations

from pathlib import Path

from specsmith.migrations import Migration, MigrationResult

# ---------------------------------------------------------------------------
# Sentinel strings that indicate the section is already present
# ---------------------------------------------------------------------------

_SENTINELS = [
    "specsmith checkpoint",
    "Session Governance Protocol",
    "GOVERNANCE ANCHOR",
    "governance heartbeat",
]

# ---------------------------------------------------------------------------
# Section text to inject
# ---------------------------------------------------------------------------

_SESSION_GOVERNANCE_SECTION = """
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
"""


class SessionGovernanceMigration(Migration):
    version = 6
    title = "Inject Session Governance Protocol into AGENTS.md"
    description = (
        "Adds the mandatory Session Governance Protocol section to AGENTS.md so "
        "any agent (Warp, Cursor, Claude, GPT) knows to emit specsmith checkpoint "
        "at session start, gate changes behind preflight, and maintain heartbeat "
        "anchors every 8-10 turns to prevent silent governance drift. "
        "Non-destructive — AGENTS.md is backed up before modification."
    )

    def run(self, root: Path, *, dry_run: bool = False) -> MigrationResult:
        result = MigrationResult(version=self.version, title=self.title, dry_run=dry_run)
        messages: list[str] = []

        agents_md = root / "AGENTS.md"
        specsmith_dir = root / ".specsmith"

        if not agents_md.exists():
            messages.append("AGENTS.md not found — skipping.")
            result.message = "  ".join(messages)
            return result

        current = agents_md.read_text(encoding="utf-8", errors="replace")

        # Idempotency check — any sentinel means the section is present
        if any(sentinel in current for sentinel in _SENTINELS):
            messages.append("AGENTS.md already contains Session Governance Protocol — skipping.")
            result.message = "  ".join(messages)
            return result

        if dry_run:
            messages.append(
                "Would inject Session Governance Protocol section into AGENTS.md "
                "and back up to .specsmith/agents.md.m006.bak."
            )
            result.files_created.append(".specsmith/agents.md.m006.bak")
            result.files_modified.append("AGENTS.md")
            result.message = "  ".join(messages)
            return result

        # Back up
        specsmith_dir.mkdir(parents=True, exist_ok=True)
        bak = specsmith_dir / "agents.md.m006.bak"
        bak.write_text(current, encoding="utf-8")
        result.files_created.append(".specsmith/agents.md.m006.bak")

        # Inject the section — find the best insertion point.
        # Strategy: insert BEFORE the first existing ## section after the header
        # (which is typically ## Session Bootstrap), so the governance protocol
        # is at the very top of agent instructions.
        insertion_marker = "## Session Bootstrap"
        if insertion_marker in current:
            # Insert the governance section AFTER Session Bootstrap (it depends
            # on Bootstrap completing first).
            bootstrap_pos = current.find(insertion_marker)
            # Find the next ## heading after Bootstrap to insert before it
            next_section_pos = current.find("\n## ", bootstrap_pos + len(insertion_marker))
            if next_section_pos != -1:
                # Insert between Bootstrap section and whatever comes next
                patched = (
                    current[:next_section_pos]
                    + "\n"
                    + _SESSION_GOVERNANCE_SECTION.strip()
                    + "\n"
                    + current[next_section_pos:]
                )
            else:
                # Bootstrap is the last section — append after it
                patched = current.rstrip() + "\n\n" + _SESSION_GOVERNANCE_SECTION.strip() + "\n"
        else:
            # No Bootstrap section — just append
            separator = "\n\n---\n" if not current.endswith("\n\n") else "\n---\n"
            patched = current + separator + _SESSION_GOVERNANCE_SECTION.strip() + "\n"

        agents_md.write_text(patched, encoding="utf-8")
        result.files_modified.append("AGENTS.md")
        messages.append(
            "Injected Session Governance Protocol section into AGENTS.md "
            "(original backed up to .specsmith/agents.md.m006.bak)."
        )

        result.message = "  ".join(messages)
        return result

    def rollback(self, root: Path) -> MigrationResult:
        """Restore AGENTS.md from the M006 backup."""
        result = MigrationResult(version=self.version, title=self.title)
        messages: list[str] = []

        specsmith_dir = root / ".specsmith"
        bak = specsmith_dir / "agents.md.m006.bak"
        agents_md = root / "AGENTS.md"

        if bak.exists():
            agents_md.write_text(
                bak.read_text(encoding="utf-8", errors="replace"), encoding="utf-8"
            )
            messages.append("Restored AGENTS.md from .specsmith/agents.md.m006.bak.")
            result.files_modified.append("AGENTS.md")
        else:
            messages.append("No AGENTS.md backup found — cannot restore.")

        result.message = "  ".join(messages)
        return result
