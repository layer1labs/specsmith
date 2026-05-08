# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Compressor — ledger archival (Spec Section 26.3)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class CompressResult:
    """Result of a compress operation."""

    archived_entries: int
    remaining_entries: int
    archive_path: Path | None
    message: str


# Match ledger entry headers like "## Session YYYY-MM-DD" or "## Entry N"
_ENTRY_HEADER = re.compile(r"^## .+", re.MULTILINE)


def _split_ledger(text: str) -> tuple[str, list[str]]:
    """Split ledger into preamble (before first ##) and entries (## blocks).

    Returns (preamble, [entry1, entry2, ...])
    """
    parts = _ENTRY_HEADER.split(text)
    headers = _ENTRY_HEADER.findall(text)

    preamble = parts[0] if parts else ""
    entries: list[str] = []
    for i, header in enumerate(headers):
        body = parts[i + 1] if i + 1 < len(parts) else ""
        entries.append(header + body)

    return preamble, entries


def _summarize_entries(entries: list[str]) -> str:
    """Create a brief summary of archived entries."""
    if not entries:
        return ""

    lines = [
        f"## Archived ({len(entries)} entries)",
        "",
        f"*Archived on {datetime.now().strftime('%Y-%m-%d')}*",
        "",
    ]

    for entry in entries:
        # Extract the header line
        first_line = entry.split("\n", 1)[0].strip()
        # Try to find a Status: line
        status_match = re.search(r"Status:\s*(.+)", entry)
        status = status_match.group(1).strip() if status_match else "—"
        lines.append(f"- {first_line} — {status}")

    lines.append("")
    return "\n".join(lines)


def run_compress(
    root: Path,
    *,
    threshold: int = 500,
    keep_recent: int = 10,
) -> CompressResult:
    """Compress the ledger by archiving old entries.

    Args:
        root: Project root directory.
        threshold: Only compress if ledger exceeds this many lines.
        keep_recent: Number of recent entries to keep in LEDGER.md.

    Returns:
        CompressResult with details of the operation.
    """
    from specsmith.paths import find_ledger

    _found = find_ledger(root)
    ledger_path = _found

    if not ledger_path or not ledger_path.exists():
        return CompressResult(
            archived_entries=0,
            remaining_entries=0,
            archive_path=None,
            message="LEDGER.md not found",
        )

    text = ledger_path.read_text(encoding="utf-8")
    line_count = len(text.splitlines())

    if line_count <= threshold:
        return CompressResult(
            archived_entries=0,
            remaining_entries=line_count,
            archive_path=None,
            message=(
                f"LEDGER.md has {line_count} lines "
                f"(≤ {threshold} threshold). No compression needed."
            ),
        )

    preamble, entries = _split_ledger(text)

    if len(entries) <= keep_recent:
        return CompressResult(
            archived_entries=0,
            remaining_entries=len(entries),
            archive_path=None,
            message=f"Only {len(entries)} entries — nothing to archive.",
        )

    # Split into archive and keep
    to_archive = entries[:-keep_recent]
    to_keep = entries[-keep_recent:]

    # Write archive
    archive_dir = root / "docs"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / "ledger-archive.md"

    archive_header = (
        "# Ledger Archive\n\nArchived ledger entries. See `LEDGER.md` for current entries.\n\n"
    )

    if archive_path.exists():
        existing = archive_path.read_text(encoding="utf-8")
        archive_content = existing.rstrip() + "\n\n" + "\n".join(to_archive)
    else:
        archive_content = archive_header + "\n".join(to_archive)

    from specsmith.safe_write import safe_overwrite

    safe_overwrite(archive_path, archive_content, reason="ledger compress archive")

    # Rewrite ledger with summary + recent entries (backup created automatically)
    summary = _summarize_entries(to_archive)
    new_ledger = preamble + summary + "\n" + "\n".join(to_keep)
    safe_overwrite(ledger_path, new_ledger, reason="ledger compress")

    return CompressResult(
        archived_entries=len(to_archive),
        remaining_entries=len(to_keep),
        archive_path=archive_path,
        message=(
            f"Archived {len(to_archive)} entries to {archive_path.relative_to(root)}. "
            f"{len(to_keep)} recent entries remain."
        ),
    )
