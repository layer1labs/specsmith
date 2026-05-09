# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Safe, corruption-resistant governance file writer.

## Design Principles

### Append-only for new entries
New ledger entries, requirements, and test cases are ALWAYS appended to
the existing file content.  The file is never truncated to add new data.

### Backup before overwrite
Any operation that replaces existing content (bulk JSON regeneration,
ledger compression) MUST create a timestamped ``.bak`` file first.
The caller receives the backup path and should validate the new content
before discarding the backup.

### Atomic writes
Overwrites use a write-to-temp-then-rename pattern so a crash mid-write
cannot leave a partially-written governance file.

### Diff on demand
A unified diff of old vs new content can be generated before any
overwrite so the agent or user can review changes before committing.
"""

from __future__ import annotations

import contextlib
import difflib
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Append-only write (safe path for new data)
# ---------------------------------------------------------------------------


def append_file(path: Path, content: str) -> None:
    """Append ``content`` to ``path`` without truncating existing data.

    Creates the file (and any missing parent directories) if it does not
    already exist.  This is the preferred write mode for:

    - New ledger entries
    - New requirement sections
    - New test specifications
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        _atomic_write(path, existing + content)
    else:
        _atomic_write(path, content)


# ---------------------------------------------------------------------------
# Safe overwrite with backup (for operations that replace content)
# ---------------------------------------------------------------------------


def safe_overwrite(
    path: Path,
    new_content: str,
    *,
    reason: str = "",
) -> Path | None:
    """Overwrite ``path`` with ``new_content``, creating a backup first.

    Returns the backup ``Path`` if a backup was made, or ``None`` if the
    file did not previously exist (no backup needed).

    The backup is a copy of the original file named::

        <stem>.<YYYYMMDDTHHMMSS>.bak

    e.g. ``LEDGER.20260507T153000.bak``.

    The caller SHOULD validate the written file and delete the backup once
    satisfied, or restore from backup on failure.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        _atomic_write(path, new_content)
        return None

    # Create timestamped backup
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    backup = path.with_name(f"{path.stem}.{ts}.bak")
    shutil.copy2(path, backup)

    _atomic_write(path, new_content)
    return backup


# ---------------------------------------------------------------------------
# JSON array helpers
# ---------------------------------------------------------------------------


def json_append(path: Path, entries: list[dict[str, Any]]) -> None:
    """Append ``entries`` to a JSON array file (append-only, no backup needed).

    Creates the file with an empty array if it does not exist.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    else:
        existing = []
    existing.extend(entries)
    _atomic_write(path, json.dumps(existing, indent=2, ensure_ascii=False) + "\n")


def json_safe_update(
    path: Path,
    new_data: list[dict[str, Any]],
    *,
    reason: str = "",
) -> Path | None:
    """Replace the content of a JSON array file with a backup.

    Returns the backup ``Path`` or ``None`` (same semantics as
    ``safe_overwrite``).
    """
    new_content = json.dumps(new_data, indent=2, ensure_ascii=False) + "\n"
    return safe_overwrite(path, new_content, reason=reason)


# ---------------------------------------------------------------------------
# Diff helper
# ---------------------------------------------------------------------------


def compute_diff(old_content: str, new_content: str, filename: str = "file") -> str:
    """Return a unified diff between ``old_content`` and ``new_content``.

    Returns an empty string if the contents are identical.
    """
    return "".join(
        difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm="\n",
        )
    )


# ---------------------------------------------------------------------------
# Content integrity
# ---------------------------------------------------------------------------


def sha256_of_file(path: Path) -> str:
    """Return the SHA-256 hex digest of ``path``'s content."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _atomic_write(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` atomically via a temp file + rename.

    Uses the same directory as ``path`` for the temp file to ensure the
    rename is atomic on the same filesystem.
    """
    dir_ = path.parent
    dir_.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dir_, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise
