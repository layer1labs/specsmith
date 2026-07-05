# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Trace Vault — Sovereign Trace Protocol (STP) inspired decision sealing.

The TraceVault provides cryptographic proof of "what was decided, when, and
in what sequence." Every seal creates a SealRecord that chains to the previous
one via a SHA-256 hash. This makes the sequence of decisions tamper-evident:
modifying any record invalidates all subsequent hashes.

This is directly inspired by the Sovereign Trace Protocol (STP) in the VERITAS
platform (AionSystem) and the BLAKE3 audit chain in the Auto-Revision Epistemic
Engine (ARE). We use SHA-256 from Python's stdlib for zero-dependency portability;
BLAKE3 can be substituted by installing the optional `blake3` package.

Seal types
----------
decision      — A technology or governance decision has been recorded
                (corresponds to STP template 06 "Scope Anchor")
milestone     — A project milestone has been reached
                (corresponds to STP template 08 "Foresight Seal")
audit-gate    — An epistemic audit gate has been passed
                (corresponds to STP template 02 "Research Priority")
logic-knot    — A Logic Knot has been detected and recorded
                (corresponds to STP template 01 "AI Failure")
stress-test   — A stress-test run has been completed and sealed
epistemic     — Generic epistemic state transition

Storage
-------
Seals are stored exclusively as ``seal_record`` entries in the ESDB (the free
SQLite backend or the commercial ChronoStore backend) — REQ-420. The legacy
append-only ``.specsmith/trace.jsonl`` flat file is no longer written or read;
the SHA-256 hash chain is preserved verbatim inside each ESDB record's data.

References
----------
VERITAS/STP: https://github.com/AionSystem/VERITAS
ARE audit chain: https://github.com/organvm-i-theoria/auto-revision-epistemic-engine

"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class SealType(str, Enum):
    """Type of a SealRecord."""

    DECISION = "decision"
    MILESTONE = "milestone"
    AUDIT_GATE = "audit-gate"
    LOGIC_KNOT = "logic-knot"
    STRESS_TEST = "stress-test"
    EPISTEMIC = "epistemic"


@dataclass
class SealRecord:
    """An immutable, cryptographically chained record of a significant event.

    Fields
    ------
    seal_id : str
        Auto-generated sequential ID (e.g. "SEAL-0001").
    seal_type : str
        The type of event being sealed.
    description : str
        Human-readable description of what is being sealed.
    content_hash : str
        SHA-256 hash of the description+type+timestamp for content integrity.
    prev_hash : str
        SHA-256 hash of the previous SealRecord. "0" * 64 for genesis.
    entry_hash : str
        SHA-256 hash of this entire record (for chain verification).
    timestamp : str
        ISO 8601 UTC timestamp.
    author : str
        Who or what created this seal (agent name, tool, etc.).
    artifact_ids : list[str]
        BeliefArtifact IDs affected by or associated with this seal.
    """

    seal_id: str
    seal_type: str
    description: str
    content_hash: str
    prev_hash: str
    entry_hash: str
    timestamp: str
    author: str = "specsmith"
    artifact_ids: list[str] | None = None

    def to_dict(self) -> dict[str, object]:
        d = asdict(self)
        if d["artifact_ids"] is None:
            d["artifact_ids"] = []
        return d

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> SealRecord:
        return cls(
            seal_id=str(d["seal_id"]),
            seal_type=str(d["seal_type"]),
            description=str(d["description"]),
            content_hash=str(d["content_hash"]),
            prev_hash=str(d["prev_hash"]),
            entry_hash=str(d["entry_hash"]),
            timestamp=str(d["timestamp"]),
            author=str(d.get("author", "specsmith")),
            artifact_ids=_parse_ids(d.get("artifact_ids")),
        )


def _parse_ids(raw: object) -> list[str]:
    """Parse artifact_ids from a JSON value safely."""
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw]


_GENESIS_HASH = "0" * 64


def _esdb_store_exists(root: Path) -> bool:
    """Return True when an ESDB store already exists for *root* (either backend).

    Used to keep read-only operations side-effect free: querying via
    ``open_default_store`` would otherwise create an empty store on disk.
    """
    specsmith_dir = root / ".specsmith"
    return (specsmith_dir / "esdb.sqlite3").exists() or (root / ".chronomemory").exists()


def _seal_seq(record: SealRecord) -> int:
    """Parse the trailing integer of a seal_id (e.g. ``SEAL-0007`` -> 7).

    Used to order seals deterministically by creation sequence regardless of the
    backend's native record ordering, so the hash chain reconstructs correctly.
    """
    try:
        return int(str(record.seal_id).rsplit("-", 1)[-1])
    except (ValueError, IndexError):
        return 0


def _load_seals_from_esdb(root: Path) -> list[SealRecord]:
    """Reconstruct all active ``seal_record`` entries from ESDB, in chain order.

    REQ-420: the trace vault is ESDB-only. Forward-only — any missing store or
    backend error yields an empty list (treated as an empty/genesis vault).
    """
    if not _esdb_store_exists(root):
        return []
    try:
        from specsmith.esdb import open_default_store

        with open_default_store(root, warn=False) as store:
            records = store.query(kind="seal_record", status="active")
        seals: list[SealRecord] = []
        for rec in records:
            try:
                seals.append(SealRecord.from_dict(rec.data))
            except (KeyError, TypeError, ValueError):
                continue  # skip malformed records — forward-only
    except Exception:  # noqa: BLE001 — forward-only: ESDB error => empty vault
        return []
    seals.sort(key=_seal_seq)
    return seals


def count_seal_records(root: Path) -> int:
    """Return the number of active ``seal_record`` entries in ESDB (REQ-420).

    Forward-only count used by phase readiness checks. Returns 0 when no ESDB
    store exists or on any backend error, and never creates a store.
    """
    if not _esdb_store_exists(root):
        return 0
    try:
        from specsmith.esdb import open_default_store

        with open_default_store(root, warn=False) as store:
            return len(store.query(kind="seal_record", status="active"))
    except Exception:  # noqa: BLE001 — forward-only: ESDB error => 0
        return 0


class TraceVault:
    """Append-only, cryptographically chained store of SealRecords.

    REQ-420: the vault reads from and writes to the ESDB exclusively, storing
    each seal as a ``seal_record`` entry (SQLite or ChronoStore backend). Each
    seal chains to the previous via SHA-256 hashes, forming a tamper-evident
    audit trail. The legacy ``.specsmith/trace.jsonl`` flat file is no longer
    used.

    Usage::

        vault = TraceVault(root=Path("."))
        seal = vault.seal(
            seal_type=SealType.DECISION,
            description="Adopted FastAPI as backend framework",
            artifact_ids=["DEC-001"],
        )
        valid = vault.verify()
    """

    # DEPRECATED(REQ-421): legacy flat-file location. Superseded by ESDB
    # ``seal_record`` entries (REQ-420). Retained only so any external tooling
    # that still references the path keeps importing; nothing writes it anymore.
    # Teardown: remove TRACE_FILE/_path once all specsmith projects are ESDB-only.
    TRACE_FILE = Path(".specsmith") / "trace.jsonl"

    def __init__(self, root: Path) -> None:
        self._root = root
        # DEPRECATED(REQ-421): legacy flat-file path; retained, never written.
        self._path = root / self.TRACE_FILE

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def seal(
        self,
        seal_type: SealType | str,
        description: str,
        author: str = "specsmith",
        artifact_ids: list[str] | None = None,
    ) -> SealRecord:
        """Create and append a new SealRecord to the vault.

        Returns the created SealRecord.
        """
        records = self._load()
        seq = len(records) + 1
        seal_id = f"SEAL-{seq:04d}"
        prev_hash = records[-1].entry_hash if records else _GENESIS_HASH
        timestamp = datetime.now(timezone.utc).isoformat()

        seal_type_str = seal_type.value if isinstance(seal_type, SealType) else seal_type

        # Content hash: covers the meaningful content of the seal
        content = f"{seal_id}:{seal_type_str}:{description}:{timestamp}"
        content_hash = _sha256(content)

        # Entry hash: covers the full record including chain link
        entry_content = f"{content_hash}:{prev_hash}"
        entry_hash = _sha256(entry_content)

        record = SealRecord(
            seal_id=seal_id,
            seal_type=seal_type_str,
            description=description,
            content_hash=content_hash,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
            timestamp=timestamp,
            author=author,
            artifact_ids=artifact_ids or [],
        )

        self._append(record)
        return record

    def verify(self) -> tuple[bool, list[str]]:
        """Verify the integrity of the entire trace chain.

        Returns (is_valid, list_of_errors). An empty error list means
        the chain is intact and unmodified.
        """
        records = self._load()
        if not records:
            return True, []

        errors: list[str] = []
        prev_hash = _GENESIS_HASH

        for rec in records:
            # Recompute content_hash from stored fields (catches description tampering)
            expected_content = f"{rec.seal_id}:{rec.seal_type}:{rec.description}:{rec.timestamp}"
            expected_content_hash = _sha256(expected_content)
            if rec.content_hash != expected_content_hash:
                errors.append(f"{rec.seal_id}: content_hash invalid — metadata tampered")

            # Verify entry_hash is correct
            expected_entry = _sha256(f"{rec.content_hash}:{rec.prev_hash}")
            if rec.entry_hash != expected_entry:
                errors.append(
                    f"{rec.seal_id}: entry_hash invalid — record may have been tampered with",
                )

            # Verify chain link
            if rec.prev_hash != prev_hash:
                errors.append(
                    f"{rec.seal_id}: prev_hash mismatch "
                    f"(expected {prev_hash[:16]}..., got {rec.prev_hash[:16]}...)",
                )

            prev_hash = rec.entry_hash

        return len(errors) == 0, errors

    def list_seals(
        self,
        seal_type: str | None = None,
        limit: int = 50,
    ) -> list[SealRecord]:
        """Return seals, optionally filtered by type, most recent first."""
        records = self._load()
        if seal_type:
            records = [r for r in records if r.seal_type == seal_type]
        return list(reversed(records[-limit:]))

    def get_latest(self) -> SealRecord | None:
        """Return the most recent SealRecord, or None if vault is empty."""
        records = self._load()
        return records[-1] if records else None

    def count(self) -> int:
        """Return the number of seals in the vault."""
        return len(self._load())

    def format_log(self, limit: int = 20) -> str:
        """Format the vault contents as a human-readable log."""
        records = list(reversed(self._load()[-limit:]))
        if not records:
            return "Trace vault is empty."

        lines = [
            f"Trace Vault — {len(self._load())} total seals",
            "=" * 50,
        ]
        for rec in records:
            lines.append(
                f"  {rec.seal_id}  [{rec.seal_type:12s}]  {rec.timestamp[:19]}Z  {rec.author}",
            )
            lines.append(f"    {rec.description[:100]}")
            if rec.artifact_ids:
                lines.append(f"    Artifacts: {', '.join(rec.artifact_ids)}")
            lines.append(f"    Hash: {rec.entry_hash[:16]}...")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> list[SealRecord]:
        # REQ-420: seals are reconstructed exclusively from ESDB ``seal_record``
        # entries; the legacy .specsmith/trace.jsonl flat file is never read.
        return _load_seals_from_esdb(self._root)

    def _append(self, record: SealRecord) -> None:
        # REQ-420: ESDB is the single source of truth. Persist the seal as a
        # ``seal_record`` ESDB entry only — no .specsmith/trace.jsonl is written.
        # Forward-only: a persistence failure raises so the seal is never
        # silently lost (best-effort callers already wrap seal() in try/except).
        from specsmith.esdb_writer import write_seal_record

        if not write_seal_record(self._root, record.to_dict()):
            raise RuntimeError(f"TraceVault: failed to persist seal {record.seal_id} to ESDB")


def _sha256(text: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
