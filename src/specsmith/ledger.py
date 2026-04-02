# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Ledger — structured change ledger management."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def add_entry(
    root: Path,
    *,
    description: str,
    entry_type: str = "task",
    author: str = "agent",
    reqs: str = "",
    status: str = "complete",
) -> str:
    """Append a structured entry to LEDGER.md."""
    ledger_path = root / "LEDGER.md"
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")

    entry = f"\n## {now} — {description}\n"
    entry += f"- **Author**: {author}\n"
    entry += f"- **Type**: {entry_type}\n"
    if reqs:
        entry += f"- **REQs affected**: {reqs}\n"
    entry += f"- **Status**: {status}\n"

    if ledger_path.exists():
        content = ledger_path.read_text(encoding="utf-8")
        content += entry
    else:
        content = "# Change Ledger\n" + entry

    ledger_path.write_text(content, encoding="utf-8")
    return entry.strip()


def list_entries(root: Path, *, since: str = "") -> list[dict[str, str]]:
    """Parse LEDGER.md and return structured entries."""
    ledger_path = root / "LEDGER.md"
    if not ledger_path.exists():
        return []

    content = ledger_path.read_text(encoding="utf-8")
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}

    for line in content.splitlines():
        heading = re.match(r"^## (.+)", line)
        if heading:
            if current:
                entries.append(current)
            current = {"heading": heading.group(1).strip()}
        elif line.startswith("- **") and current:
            m = re.match(r"- \*\*(.+?)\*\*:\s*(.+)", line)
            if m:
                current[m.group(1).lower()] = m.group(2).strip()

    if current:
        entries.append(current)

    if since:
        entries = [e for e in entries if e.get("heading", "") >= since]

    return entries


def get_stats(root: Path) -> dict[str, object]:
    """Get ledger statistics."""
    entries = list_entries(root)
    authors: dict[str, int] = {}
    types: dict[str, int] = {}

    for e in entries:
        author = e.get("author", "unknown")
        authors[author] = authors.get(author, 0) + 1
        etype = e.get("type", "unknown")
        types[etype] = types.get(etype, 0) + 1

    return {
        "total_entries": len(entries),
        "authors": authors,
        "types": types,
    }
