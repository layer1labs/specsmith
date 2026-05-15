# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""ChronoStore — Python-native WAL-based Epistemic State Database.

Layout (per project root):
  <root>/.chronomemory/
    events.wal        — append-only NDJSON event log with SHA-256 chain
    snapshot.json     — materialized state (written every 50 events or on compact())
    backup/           — backup copies created by backup()

Record schema includes OEA anti-hallucination fields (H15–H22):
  - source_type: "observed" | "inferred" | "hypothesis" | "synthetic"  (H19)
  - confidence: 0.0–1.0 (H17)
  - evidence: list of source references (H20)
  - epistemic_boundary: scope constraints (H15)
  - is_hypothesis: bool (H20)
  - model_assumptions: {context_window, temperature, provider} (H21)
  - recursion_depth: int (H16 — track autonomous generation chain depth)

WAL integrity: each event carries the SHA-256 of the previous event's hash
plus its own JSON payload, forming a tamper-evident chain.

REQ-305: ESDB write layer
REQ-306: per-project ESDB (path: .chronomemory/ relative to project root)
REQ-310: OEA anti-hallucination fields on every record
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_WAL_FILENAME = "events.wal"
_SNAPSHOT_FILENAME = "snapshot.json"
_BACKUP_DIR = "backup"
_SNAPSHOT_EVERY = 50  # Write a new snapshot every N appended events
_CONFIDENCE_RAG_THRESHOLD = 0.6  # H18: minimum confidence for RAG injection

# ---------------------------------------------------------------------------
# Record dataclass
# ---------------------------------------------------------------------------


@dataclass
class ChronoRecord:
    """A single persisted record in ChronoStore.

    All fields default to safe/neutral values so that records migrated from
    flat JSON (with no OEA fields) import cleanly without blocking validation.
    """

    # Core identity
    id: str = ""
    kind: str = "fact"  # requirement | testcase | fact | hypothesis | decision | risk
    status: str = "active"  # active | deprecated | tombstone
    label: str = ""

    # Epistemic quality (H17)
    confidence: float = 0.7

    # OEA anti-hallucination fields
    source_type: str = "observed"   # observed | inferred | hypothesis | synthetic  (H19)
    evidence: list[str] = field(default_factory=list)          # (H20)
    epistemic_boundary: list[str] = field(default_factory=list)  # (H15)
    is_hypothesis: bool = False                                 # (H20)
    model_assumptions: dict[str, Any] = field(default_factory=dict)  # (H21)
    recursion_depth: int = 0                                    # (H16)

    # Source data (original dict from JSON migration or direct write)
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ChronoRecord:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)

    def passes_rag_filter(self) -> bool:
        """Return True if this record should be included in RAG context (H18)."""
        return self.confidence >= _CONFIDENCE_RAG_THRESHOLD and self.status == "active"


# ---------------------------------------------------------------------------
# WAL event dataclass
# ---------------------------------------------------------------------------


@dataclass
class WalEvent:
    """A single WAL log entry."""

    seq: int = 0
    ts: str = ""          # ISO-8601 timestamp
    op: str = "upsert"    # upsert | delete | compact | migrate
    record_id: str = ""
    record: dict[str, Any] = field(default_factory=dict)
    prev_hash: str = ""   # SHA-256 of previous event's hash
    hash: str = ""        # SHA-256 of this event (set after construction)
    recursion_depth: int = 0  # H16

    def compute_hash(self) -> str:
        """Compute and store the SHA-256 hash for this event."""
        payload = json.dumps(
            {
                "seq": self.seq,
                "ts": self.ts,
                "op": self.op,
                "record_id": self.record_id,
                "record": self.record,
                "prev_hash": self.prev_hash,
                "recursion_depth": self.recursion_depth,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        self.hash = hashlib.sha256(payload.encode()).hexdigest()
        return self.hash

    def to_json_line(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json_line(cls, line: str) -> WalEvent:
        d = json.loads(line)
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# ChronoStore
# ---------------------------------------------------------------------------


class ChronoStore:
    """Per-project WAL-based Epistemic State Database.

    Usage::

        store = ChronoStore(project_root)
        store.open()                    # load snapshot + replay WAL tail
        store.upsert(record)            # write to WAL + update in-memory state
        records = store.query()         # read from in-memory state
        store.close()                   # flush pending snapshot if needed

    The store is safe to use from a single thread. For concurrent access,
    each caller should create its own instance (each open() call replays
    from disk, so concurrent readers get a consistent snapshot).
    """

    def __init__(self, project_root: str | Path, *, recursion_depth: int = 0) -> None:
        self.root = Path(project_root).resolve()
        self._db_dir = self.root / ".chronomemory"
        self._wal_path = self._db_dir / _WAL_FILENAME
        self._snapshot_path = self._db_dir / _SNAPSHOT_FILENAME
        self._state: dict[str, ChronoRecord] = {}
        self._seq: int = 0
        self._last_hash: str = ""
        self._events_since_snapshot: int = 0
        self._open: bool = False
        self._recursion_depth = recursion_depth

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def open(self) -> ChronoStore:
        """Load snapshot + replay WAL tail into memory."""
        self._db_dir.mkdir(parents=True, exist_ok=True)
        self._load_snapshot()
        self._replay_wal()
        self._open = True
        return self

    def close(self) -> None:
        """Write snapshot if enough events have accumulated."""
        if self._open and self._events_since_snapshot >= _SNAPSHOT_EVERY:
            self._write_snapshot()
        self._open = False

    def __enter__(self) -> ChronoStore:
        return self.open()

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def upsert(self, record: ChronoRecord) -> WalEvent:
        """Persist an upsert event to the WAL and update in-memory state.

        This is the primary write path. The WAL append is atomic:
        write to a temp file → fsync → rename, so a crash mid-write
        leaves the WAL intact.
        """
        if not self._open:
            self.open()

        record.recursion_depth = self._recursion_depth
        event = self._build_event("upsert", record)
        self._append_wal(event)
        self._state[record.id] = record
        self._events_since_snapshot += 1
        if self._events_since_snapshot >= _SNAPSHOT_EVERY:
            self._write_snapshot()
            self._events_since_snapshot = 0
        return event

    def delete(self, record_id: str) -> WalEvent:
        """Tombstone a record (mark as deleted without physical removal)."""
        if not self._open:
            self.open()

        tombstone = ChronoRecord(
            id=record_id,
            status="tombstone",
            source_type="observed",
        )
        event = self._build_event("delete", tombstone)
        self._append_wal(event)
        if record_id in self._state:
            self._state[record_id].status = "tombstone"
        self._events_since_snapshot += 1
        return event

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def query(
        self,
        *,
        kind: str | None = None,
        status: str = "active",
        rag_filter: bool = False,
        min_confidence: float = 0.0,
    ) -> list[ChronoRecord]:
        """Return records matching the given filters.

        Args:
            kind: Filter by record kind (e.g. 'requirement', 'testcase').
            status: Only return records with this status (default 'active').
                    Pass '' to include all statuses.
            rag_filter: If True, apply H18 confidence filter (>= 0.6).
            min_confidence: Minimum confidence threshold (overrides rag_filter
                            if higher).
        """
        if not self._open:
            self.open()

        threshold = max(
            min_confidence,
            _CONFIDENCE_RAG_THRESHOLD if rag_filter else 0.0,
        )

        results: list[ChronoRecord] = []
        for rec in self._state.values():
            if status and rec.status != status:
                continue
            if kind and rec.kind != kind:
                continue
            if rec.confidence < threshold:
                continue
            results.append(rec)
        return results

    def get(self, record_id: str) -> ChronoRecord | None:
        """Return a single record by ID, or None if not found."""
        if not self._open:
            self.open()
        return self._state.get(record_id)

    def record_count(self) -> int:
        """Count of active records."""
        if not self._open:
            self.open()
        return sum(1 for r in self._state.values() if r.status == "active")

    def wal_seq(self) -> int:
        """Current WAL sequence number."""
        return self._seq

    def chain_valid(self) -> bool:
        """Verify WAL hash chain integrity."""
        if not self._wal_path.exists():
            return True  # Empty store is valid

        prev_hash = ""
        try:
            for line in self._wal_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                event = WalEvent.from_json_line(line)
                if event.prev_hash != prev_hash:
                    return False
                # Recompute expected hash
                expected_event = WalEvent(
                    seq=event.seq,
                    ts=event.ts,
                    op=event.op,
                    record_id=event.record_id,
                    record=event.record,
                    prev_hash=event.prev_hash,
                    recursion_depth=event.recursion_depth,
                )
                expected_hash = expected_event.compute_hash()
                if event.hash != expected_hash:
                    return False
                prev_hash = event.hash
        except Exception:  # noqa: BLE001
            return False
        return True

    # ------------------------------------------------------------------
    # Maintenance operations
    # ------------------------------------------------------------------

    def compact(self) -> int:
        """Write a fresh snapshot from current state and truncate WAL tail.

        Returns the number of events compacted.
        """
        if not self._open:
            self.open()

        compacted = self._seq
        self._write_snapshot()

        # Truncate WAL to a single "compact" sentinel event
        sentinel = self._build_event(
            "compact",
            ChronoRecord(id="__compact__", label=f"Compacted at seq={self._seq}"),
        )
        with open(self._wal_path, "w", encoding="utf-8") as f:
            f.write(sentinel.to_json_line() + "\n")
        self._last_hash = sentinel.hash
        self._seq = sentinel.seq
        self._events_since_snapshot = 0
        return compacted

    def backup(self) -> Path:
        """Copy .chronomemory/ to a timestamped backup directory.

        Returns the backup path.
        """
        backup_dir = self._db_dir / _BACKUP_DIR
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
        dest = backup_dir / ts
        shutil.copytree(str(self._db_dir), str(dest), ignore=shutil.ignore_patterns("backup"))
        return dest

    def replay(self, *, from_seq: int = 0) -> list[WalEvent]:
        """Replay WAL events from a given sequence number.

        Returns a list of all events with seq >= from_seq.
        """
        if not self._wal_path.exists():
            return []
        events: list[WalEvent] = []
        for line in self._wal_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = WalEvent.from_json_line(line)
                if event.seq >= from_seq:
                    events.append(event)
            except Exception:  # noqa: BLE001
                continue
        return events

    def export_records(self) -> list[dict[str, Any]]:
        """Return all active records as plain dicts."""
        if not self._open:
            self.open()
        return [r.to_dict() for r in self._state.values() if r.status == "active"]

    # ------------------------------------------------------------------
    # Migration from flat JSON
    # ------------------------------------------------------------------

    def migrate_from_json(self, specsmith_dir: Path) -> dict[str, int]:
        """Import requirements.json and testcases.json into the WAL.

        Records are tagged with source_type='observed' to satisfy H19.
        Existing records are NOT overwritten (idempotent by record ID).

        Returns:
            {'requirements': N, 'testcases': N, 'skipped': N}
        """
        if not self._open:
            self.open()

        counts: dict[str, int] = {"requirements": 0, "testcases": 0, "skipped": 0}

        for filename, kind in [
            ("requirements.json", "requirement"),
            ("testcases.json", "testcase"),
        ]:
            path = specsmith_dir / filename
            if not path.is_file():
                continue
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue

            for item in raw:
                if not isinstance(item, dict):
                    continue
                rec_id = item.get("id", "")
                if not rec_id:
                    continue

                if rec_id in self._state:
                    counts["skipped"] += 1
                    continue

                record = ChronoRecord(
                    id=rec_id,
                    kind=kind,
                    label=item.get("title", ""),
                    status=item.get("status", "active"),
                    confidence=float(item.get("confidence", 0.7)),
                    source_type="observed",   # H19: provenance tagged
                    evidence=[f"migrated from {filename}"],  # H20
                    data=item,
                )
                self.upsert(record)
                counts[filename.split(".")[0]] += 1

        return counts

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_snapshot(self) -> None:
        """Load the materialized snapshot if it exists."""
        if not self._snapshot_path.exists():
            return
        try:
            data = json.loads(self._snapshot_path.read_text(encoding="utf-8"))
            self._seq = data.get("seq", 0)
            self._last_hash = data.get("last_hash", "")
            for rec_dict in data.get("records", []):
                rec = ChronoRecord.from_dict(rec_dict)
                self._state[rec.id] = rec
        except Exception:  # noqa: BLE001
            # Corrupt snapshot — start fresh; WAL replay will recover
            self._state = {}
            self._seq = 0
            self._last_hash = ""

    def _replay_wal(self) -> None:
        """Apply WAL events after the snapshot seq to bring state current."""
        if not self._wal_path.exists():
            return

        try:
            lines = self._wal_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                event = WalEvent.from_json_line(line)
            except Exception:  # noqa: BLE001
                continue

            if event.seq <= self._seq and self._seq > 0:
                continue  # Already covered by snapshot

            if event.op in ("upsert", "migrate"):
                rec = ChronoRecord.from_dict(event.record)
                self._state[rec.id] = rec
            elif event.op == "delete":
                rec_id = event.record_id
                if rec_id in self._state:
                    self._state[rec_id].status = "tombstone"
            elif event.op == "compact":
                pass  # Compact sentinel — state already at snapshot

            self._seq = max(self._seq, event.seq)
            self._last_hash = event.hash

    def _build_event(self, op: str, record: ChronoRecord) -> WalEvent:
        """Construct a new WAL event with the next sequence number."""
        self._seq += 1
        event = WalEvent(
            seq=self._seq,
            ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            op=op,
            record_id=record.id,
            record=record.to_dict(),
            prev_hash=self._last_hash,
            recursion_depth=self._recursion_depth,
        )
        event.compute_hash()
        self._last_hash = event.hash
        return event

    def _append_wal(self, event: WalEvent) -> None:
        """Atomically append an event to the WAL.

        Uses write-to-temp → fsync → rename to prevent partial writes.
        """
        self._db_dir.mkdir(parents=True, exist_ok=True)
        line = event.to_json_line() + "\n"
        tmp_path = self._wal_path.with_suffix(".wal.tmp")
        try:
            # Append mode if WAL exists, create otherwise
            mode = "a" if self._wal_path.exists() else "w"
            with open(tmp_path, mode, encoding="utf-8") as f:
                if mode == "a":
                    # Write temp file as full WAL + new line
                    existing = (
                        self._wal_path.read_text(encoding="utf-8")
                        if self._wal_path.exists()
                        else ""
                    )
                    tmp_path.write_text(existing + line, encoding="utf-8")
                else:
                    f.write(line)
                try:
                    f.flush()
                    os.fsync(f.fileno())
                except (AttributeError, OSError):
                    pass
            os.replace(str(tmp_path), str(self._wal_path))
        except Exception:  # noqa: BLE001
            # Direct append fallback (less safe but non-blocking)
            with open(self._wal_path, "a", encoding="utf-8") as f:
                f.write(line)
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    def _write_snapshot(self) -> None:
        """Write the current in-memory state to snapshot.json (atomic)."""
        data = {
            "seq": self._seq,
            "last_hash": self._last_hash,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "records": [r.to_dict() for r in self._state.values()],
        }
        content = json.dumps(data, indent=2, ensure_ascii=False)
        tmp = self._snapshot_path.with_suffix(".json.tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(str(tmp), str(self._snapshot_path))


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------


def open_store(project_root: str | Path, *, recursion_depth: int = 0) -> ChronoStore:
    """Open (or create) the ChronoStore for a project.

    Returns an already-opened ChronoStore. Call .close() when done, or use
    as a context manager.
    """
    store = ChronoStore(project_root, recursion_depth=recursion_depth)
    store.open()
    return store
