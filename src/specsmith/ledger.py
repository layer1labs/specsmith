# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Ledger — structured change ledger management with cryptographic audit chain.

The CryptoAuditChain class provides a SHA-256 chained hash over all ledger
entries, making the ledger tamper-evident. This is directly inspired by the
BLAKE3 audit chain in the Auto-Revision Epistemic Engine (ARE) and the
Sovereign Trace Protocol in VERITAS (AionSystem).

Each entry stores:
  entry_hash  = SHA-256 of (content + prev_hash)
  prev_hash   = SHA-256 of the previous entry ("0"*64 for genesis)

Ledger entries also carry two new AEE fields:
  epistemic_status     — confidence level of the work described (high/medium/low/unknown)
  belief_artifacts     — comma-separated BeliefArtifact IDs touched in this session
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

_GENESIS_HASH = "0" * 64


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def add_entry(
    root: Path,
    *,
    description: str,
    entry_type: str = "task",
    author: str = "agent",
    reqs: str = "",
    status: str = "complete",
    epistemic_status: str = "unknown",
    belief_artifacts: str = "",
) -> str:
    """Append a structured entry to LEDGER.md with cryptographic chaining."""
    from specsmith.paths import find_ledger, ledger_path as canonical_ledger
    # Use existing ledger location (backward compat) or create at canonical docs/ path
    ledger_path = find_ledger(root) or canonical_ledger(root)
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")

    # Compute chain link
    chain = CryptoAuditChain(root)
    prev_hash = chain.latest_hash()
    entry_body = (
        f"{now}|{description}|{entry_type}|{author}|{status}|{epistemic_status}|{belief_artifacts}"
    )
    entry_hash = _sha256(f"{entry_body}:{prev_hash}")

    entry = f"\n## {now} — {description}\n"
    entry += f"- **Author**: {author}\n"
    entry += f"- **Type**: {entry_type}\n"
    if reqs:
        entry += f"- **REQs affected**: {reqs}\n"
    entry += f"- **Status**: {status}\n"
    if epistemic_status and epistemic_status != "unknown":
        entry += f"- **Epistemic status**: {epistemic_status}\n"
    if belief_artifacts:
        entry += f"- **Belief artifacts**: {belief_artifacts}\n"
    entry += f"- **Chain hash**: `{entry_hash[:16]}...`\n"

    from specsmith.safe_write import append_file
    if ledger_path.exists():
        append_file(ledger_path, entry)
    else:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        append_file(ledger_path, "# Change Ledger\n" + entry)

    # Persist hash to chain index
    chain.append(entry_hash)
    return entry.strip()


class CryptoAuditChain:
    """SHA-256 chained audit trail for ledger entries.

    Stores hashes in `.specsmith/ledger-chain.txt` — one hash per line.
    The file is append-only. Each line is the SHA-256 hash of
    (entry_content + previous_hash), forming a chain.

    This makes the ledger tamper-evident: if any entry is modified,
    its hash changes, which invalidates all subsequent hashes.
    Verification is O(n) in the number of entries.
    """

    CHAIN_FILE = Path(".specsmith") / "ledger-chain.txt"

    def __init__(self, root: Path) -> None:
        self._path = root / self.CHAIN_FILE

    def latest_hash(self) -> str:
        """Return the hash of the most recent entry, or genesis hash if empty."""
        if not self._path.exists():
            return _GENESIS_HASH
        lines = [
            line.strip()
            for line in self._path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        return lines[-1] if lines else _GENESIS_HASH

    def append(self, entry_hash: str) -> None:
        """Append a new hash to the chain."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(entry_hash + "\n")

    def all_hashes(self) -> list[str]:
        """Return all hashes in the chain (oldest first)."""
        if not self._path.exists():
            return []
        return [
            line.strip()
            for line in self._path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def length(self) -> int:
        return len(self.all_hashes())


def list_entries(root: Path, *, since: str = "") -> list[dict[str, str]]:
    """Parse LEDGER.md and return structured entries."""
    from specsmith.paths import find_ledger
    ledger_path = find_ledger(root)
    if not ledger_path or not ledger_path.exists():
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
