# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""M005 — Register specsmith_run as the canonical agent governance command.

What this migration does
------------------------
1. Creates (or patches) ``.specsmith/agent-tools.json`` to declare
   ``specsmith_run`` as the primary governance command for agents, listing
   its verb shortcuts and slash-command prefix.

2. Updates ``AGENTS.md`` (if it exists and does not already mention
   ``/specsmith``) to add a concise "Governance commands" section that
   documents the ``/specsmith <args>`` slash-command interface.

Both steps are non-destructive:
- ``agent-tools.json`` is written fresh (it is machine-managed, not
  hand-edited).
- ``AGENTS.md`` receives a small append block; the original content is
  preserved.  A backup is stored at ``.specsmith/agents.md.m005.bak``.

REQ-SM-001: agents must use ``specsmith_run`` / ``/specsmith <args>`` for
all governance operations instead of raw ``specsmith`` shell calls.
"""

from __future__ import annotations

import json
from pathlib import Path

from specsmith.migrations import Migration, MigrationResult

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Verb shortcuts that specsmith_run recognises (must stay in sync with tools.py)
_VERB_SHORTCUTS = [
    "audit",
    "commit",
    "doctor",
    "load",
    "pull",
    "push",
    "run",
    "save",
    "status",
    "sync",
    "validate",
    "watch",
]

_AGENT_TOOLS_CONTENT = {
    "schema_version": 1,
    "primary_governance_command": "specsmith_run",
    "slash_prefix": "/specsmith",
    "verb_shortcuts": _VERB_SHORTCUTS,
    "description": (
        "Use specsmith_run() or /specsmith <args> in the Nexus REPL for all "
        "governance operations (save, load, push, pull, audit, status, …). "
        "REQ-SM-001: agents must not invoke the specsmith binary directly via "
        "run_shell when specsmith_run is available."
    ),
}

_AGENTS_MD_PATCH = """
## Governance commands (specsmith_run / /specsmith)

All specsmith governance operations should be invoked through the
``specsmith_run`` agent tool or the ``/specsmith`` REPL slash command.

**In the Nexus REPL:**

```
/specsmith save               # backup + commit + push governance state
/specsmith load               # pull + restore governance state
/specsmith audit --strict     # strict governance audit
/specsmith status             # show governance status
/specsmith push               # git push governance changes
/specsmith pull               # git pull governance changes
/specsmith sync               # full two-way sync
/specsmith watch              # watch CI and block until green
```

**Verb shortcuts** (single word, no prefix needed in tool calls):
``save``, ``load``, ``push``, ``pull``, ``sync``, ``audit``, ``status``,
``watch``, ``commit``, ``validate``, ``doctor``, ``run``.

These are all equivalent: ``specsmith_run("save")``,
``specsmith_run("/specsmith save")``, ``specsmith_run("specsmith save")``.
"""


class AgentRunToolMigration(Migration):
    version = 5
    title = "Register specsmith_run as the default agent governance command"
    description = (
        "Creates .specsmith/agent-tools.json declaring specsmith_run as the "
        "primary governance command, and patches AGENTS.md to document the "
        "/specsmith slash-command interface. Non-destructive — AGENTS.md is "
        "backed up before modification."
    )

    def run(self, root: Path, *, dry_run: bool = False) -> MigrationResult:
        result = MigrationResult(version=self.version, title=self.title, dry_run=dry_run)
        messages: list[str] = []

        # ── 1. Write .specsmith/agent-tools.json ────────────────────────────
        specsmith_dir = root / ".specsmith"
        tools_json = specsmith_dir / "agent-tools.json"

        if dry_run:
            messages.append(
                "Would write .specsmith/agent-tools.json "
                "(primary_governance_command=specsmith_run)."
            )
            result.files_created.append(".specsmith/agent-tools.json")
        else:
            specsmith_dir.mkdir(parents=True, exist_ok=True)
            tools_json.write_text(
                json.dumps(_AGENT_TOOLS_CONTENT, indent=2),
                encoding="utf-8",
            )
            messages.append("Wrote .specsmith/agent-tools.json.")
            result.files_created.append(".specsmith/agent-tools.json")

        # ── 2. Patch AGENTS.md ───────────────────────────────────────────────
        agents_md = root / "AGENTS.md"
        if not agents_md.exists():
            messages.append("AGENTS.md not found — skipping documentation patch.")
        else:
            current = agents_md.read_text(encoding="utf-8", errors="replace")
            if "/specsmith" in current:
                messages.append(
                    "AGENTS.md already documents /specsmith — skipping documentation patch."
                )
            elif dry_run:
                messages.append(
                    "Would append /specsmith governance commands section to AGENTS.md "
                    "and back up to .specsmith/agents.md.m005.bak."
                )
                result.files_created.append(".specsmith/agents.md.m005.bak")
                result.files_modified.append("AGENTS.md")
            else:
                # Back up
                bak = specsmith_dir / "agents.md.m005.bak"
                bak.write_text(current, encoding="utf-8")
                result.files_created.append(".specsmith/agents.md.m005.bak")

                # Append governance section
                separator = "\n\n---\n" if not current.endswith("\n\n") else "\n---\n"
                agents_md.write_text(
                    current + separator + _AGENTS_MD_PATCH.lstrip("\n"),
                    encoding="utf-8",
                )
                result.files_modified.append("AGENTS.md")
                messages.append(
                    "Appended /specsmith governance commands section to AGENTS.md "
                    "(original backed up to .specsmith/agents.md.m005.bak)."
                )

        result.message = "  ".join(messages)
        return result

    def rollback(self, root: Path) -> MigrationResult:
        """Restore AGENTS.md from the M005 backup and remove agent-tools.json."""
        result = MigrationResult(version=self.version, title=self.title)
        messages: list[str] = []

        specsmith_dir = root / ".specsmith"

        # Remove agent-tools.json
        tools_json = specsmith_dir / "agent-tools.json"
        if tools_json.exists():
            tools_json.unlink()
            messages.append("Removed .specsmith/agent-tools.json.")

        # Restore AGENTS.md from backup
        bak = specsmith_dir / "agents.md.m005.bak"
        agents_md = root / "AGENTS.md"
        if bak.exists():
            agents_md.write_text(
                bak.read_text(encoding="utf-8", errors="replace"),
                encoding="utf-8",
            )
            messages.append("Restored AGENTS.md from .specsmith/agents.md.m005.bak.")
            result.files_modified.append("AGENTS.md")
        else:
            messages.append("No AGENTS.md backup found — cannot restore.")

        result.message = "  ".join(messages)
        return result
