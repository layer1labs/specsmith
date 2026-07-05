# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""specsmith.esdb.sqlite_store — SQLite-backed ESDB (REQ-365).

SqliteStore is the **free, MIT-licensed default** ESDB backend shipped with
specsmith.  It requires no external dependencies (uses Python stdlib ``sqlite3``)
and no commercial license.

Database file: ``<project_root>/.specsmith/esdb.sqlite3``

Interface is intentionally compatible with chronomemory ChronoStore so that
callers can swap backends transparently via ``open_default_store()``.

Differences from ChronoStore (by design):
- No SHA-256 WAL chain — SQLite ACID guarantees integrity instead.
  ``chain_valid()`` always returns True.
- No OEA anti-hallucination fields (H15–H22) on individual records.
  Those are exclusively a ChronoStore / chronomemory feature.
- No Rust acceleration.
- No context-pack compiler, dependency graph, or epistemic rollback.
- ``wal_seq()`` returns the SQLite rowid of the last inserted record.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DB_FILENAME = "esdb.sqlite3"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS records (
    id          TEXT PRIMARY KEY,
    kind        TEXT NOT NULL DEFAULT 'fact',
    status      TEXT NOT NULL DEFAULT 'active',
    label       TEXT NOT NULL DEFAULT '',
    confidence  REAL NOT NULL DEFAULT 0.7,
    data        TEXT NOT NULL DEFAULT '{}',
    source_ids  TEXT NOT NULL DEFAULT '[]',
    created_at  REAL NOT NULL
)
"""
_CREATE_AUDIT_TABLE = """
CREATE TABLE IF NOT EXISTS audit_events (
    event_id         TEXT PRIMARY KEY,
    timestamp        TEXT NOT NULL,
    prev_hash        TEXT NOT NULL,
    current_hash     TEXT NOT NULL,
    actor            TEXT NOT NULL,
    command_source   TEXT NOT NULL,
    work_item_id     TEXT NOT NULL,
    payload_hash     TEXT NOT NULL
)
"""

_UPSERT_SQL = """
INSERT INTO records (id, kind, status, label, confidence, data, source_ids, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    kind       = excluded.kind,
    status     = excluded.status,
    label      = excluded.label,
    confidence = excluded.confidence,
    data       = excluded.data,
    source_ids = excluded.source_ids
"""


# ---------------------------------------------------------------------------
# SqliteRecord — mirrors EsdbRecord for the SQLite backend
# ---------------------------------------------------------------------------


class SqliteRecord:
    """A single record in SqliteStore — mirrors EsdbRecord / ChronoRecord."""

    __slots__ = ("confidence", "data", "id", "kind", "label", "source_ids", "status")

    def __init__(
        self,
        id: str,
        kind: str = "fact",
        status: str = "active",
        label: str = "",
        confidence: float = 0.7,
        data: dict[str, Any] | None = None,
        source_ids: list[str] | None = None,
    ) -> None:
        self.id = id
        self.kind = kind
        self.status = status
        self.label = label
        self.confidence = confidence
        self.data = data or {}
        self.source_ids = source_ids or []

    # Alias used by callers that expect ChronoRecord-style attribute
    @property
    def evidence(self) -> list[str]:
        return self.source_ids

    def passes_rag_filter(self) -> bool:
        return self.confidence >= 0.6 and self.status == "active"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "status": self.status,
            "label": self.label,
            "confidence": self.confidence,
            "data": self.data,
            "source_ids": self.source_ids,
        }

    def __repr__(self) -> str:
        return (
            f"SqliteRecord(id={self.id!r}, kind={self.kind!r}, "
            f"label={self.label!r}, confidence={self.confidence:.2f})"
        )


# ---------------------------------------------------------------------------
# SqliteStore
# ---------------------------------------------------------------------------


class SqliteStore:
    """SQLite-backed ESDB store (free MIT default backend).

    Usage::

        store = SqliteStore(project_root)
        store.open()
        store.upsert(SqliteRecord(id="REQ-001", kind="requirement", label="..."))
        records = store.query(kind="requirement")
        store.close()

    Or as a context manager::

        with SqliteStore(project_root) as store:
            store.upsert(...)
    """

    def __init__(self, project_root: str | Path) -> None:
        # CodeQL py/path-injection: normalize with os.path.realpath AND assert the
        # DB path stays within the project root (containment), then store the
        # sanitised values so the open() sinks (mkdir/connect) receive clean paths.
        _root = os.path.realpath(str(project_root))
        _db = os.path.realpath(os.path.join(_root, ".specsmith", _DB_FILENAME))
        if _db != _root and not _db.startswith(_root + os.sep):
            raise ValueError(f"Database path escapes project root: {_db!r}")
        self.root = Path(_root)
        self._db_path = Path(_db)
        self._conn: sqlite3.Connection | None = None
        self._open: bool = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def open(self) -> SqliteStore:
        """Open the database and create the schema if needed."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(_CREATE_TABLE)
        self._conn.execute(_CREATE_AUDIT_TABLE)
        self._conn.commit()
        self._open = True
        return self

    def close(self) -> None:
        if self._conn is not None:
            self._conn.commit()
            self._conn.close()
            self._conn = None
        self._open = False

    def __enter__(self) -> SqliteStore:
        return self.open()

    def __exit__(self, *_: object) -> None:
        self.close()

    def _require_open(self) -> sqlite3.Connection:
        if self._conn is None or not self._open:
            raise RuntimeError("SqliteStore is not open — call open() or use as context manager")
        return self._conn

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def upsert(self, record: SqliteRecord) -> None:
        """Insert or update a record."""
        conn = self._require_open()
        conn.execute(
            _UPSERT_SQL,
            (
                record.id,
                record.kind,
                record.status,
                record.label,
                record.confidence,
                json.dumps(record.data, ensure_ascii=False),
                json.dumps(record.source_ids, ensure_ascii=False),
                time.time(),
            ),
        )
        conn.commit()

    def delete(self, record_id: str) -> None:
        """Tombstone a record (sets status='tombstone', does not physically delete)."""
        conn = self._require_open()
        conn.execute(
            "UPDATE records SET status='tombstone' WHERE id=?",
            (record_id,),
        )
        conn.commit()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def query(
        self,
        *,
        kind: str | None = None,
        status: str | None = "active",
        rag_filter: bool = False,
        min_confidence: float = 0.0,
    ) -> list[SqliteRecord]:
        """Query records with optional filters.

        Args:
            kind:           Filter by record kind (None = all kinds).
            status:         Filter by status; pass ``""`` or ``None`` for all statuses.
            rag_filter:     If True apply ``confidence >= 0.6`` threshold (H18).
            min_confidence: Additional minimum confidence threshold.

        """
        conn = self._require_open()
        clauses: list[str] = []
        params: list[Any] = []

        if kind:
            clauses.append("kind = ?")
            params.append(kind)
        if status:
            clauses.append("status = ?")
            params.append(status)
        threshold = max(0.6 if rag_filter else 0.0, min_confidence)
        if threshold > 0.0:
            clauses.append("confidence >= ?")
            params.append(threshold)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = conn.execute(
            f"SELECT * FROM records {where} ORDER BY rowid",  # noqa: S608
            params,
        ).fetchall()

        return [
            SqliteRecord(
                id=row["id"],
                kind=row["kind"],
                status=row["status"],
                label=row["label"],
                confidence=row["confidence"],
                data=json.loads(row["data"]),
                source_ids=json.loads(row["source_ids"]),
            )
            for row in rows
        ]

    def get(self, record_id: str) -> SqliteRecord | None:
        """Return a single record by ID, or None."""
        conn = self._require_open()
        row = conn.execute("SELECT * FROM records WHERE id=?", (record_id,)).fetchone()
        if row is None:
            return None
        return SqliteRecord(
            id=row["id"],
            kind=row["kind"],
            status=row["status"],
            label=row["label"],
            confidence=row["confidence"],
            data=json.loads(row["data"]),
            source_ids=json.loads(row["source_ids"]),
        )

    # ------------------------------------------------------------------
    # Metadata / compatibility
    # ------------------------------------------------------------------

    def record_count(self) -> int:
        """Count of non-tombstone records."""
        conn = self._require_open()
        row = conn.execute("SELECT COUNT(*) FROM records WHERE status != 'tombstone'").fetchone()
        return int(row[0]) if row else 0

    def wal_seq(self) -> int:
        """Return the rowid of the last inserted record (monotonically increasing)."""
        conn = self._require_open()
        row = conn.execute("SELECT MAX(rowid) FROM records").fetchone()
        return int(row[0]) if row and row[0] is not None else 0

    def backup(self, backup_dir: str | Path | None = None) -> Path:
        """Create a timestamped SQLite snapshot and return its path."""
        conn = self._require_open()
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        dest_dir = Path(backup_dir) if backup_dir else self._db_path.parent / "backups"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"esdb_sqlite_backup_{ts}.sqlite3"

        backup_conn = sqlite3.connect(str(dest))
        try:
            conn.backup(backup_conn)
        finally:
            backup_conn.close()

        return dest

    def chain_valid(self) -> bool:
        """Return True when the SQLite audit event hash chain verifies."""
        return self.verify_audit_chain()["ok"]

    def append_audit_event(
        self,
        *,
        payload: dict[str, Any],
        command_source: str = "specsmith",
        work_item_id: str = "",
        actor: str = "",
    ) -> str:
        """Append a tamper-evident audit event and return its event_id."""
        conn = self._require_open()
        ts = datetime.now(timezone.utc).isoformat()
        payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        prev_row = conn.execute(
            "SELECT current_hash FROM audit_events ORDER BY rowid DESC LIMIT 1",
        ).fetchone()
        prev_hash = str(prev_row["current_hash"]) if prev_row else "0" * 64
        event_id = f"EVT-{uuid.uuid4().hex[:16].upper()}"
        resolved_actor = actor or _default_actor()
        material = (
            f"{event_id}|{ts}|{prev_hash}|{resolved_actor}|{command_source}|"
            f"{work_item_id}|{payload_hash}"
        )
        current_hash = hashlib.sha256(material.encode("utf-8")).hexdigest()
        conn.execute(
            """
            INSERT INTO audit_events (
                event_id, timestamp, prev_hash, current_hash,
                actor, command_source, work_item_id, payload_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                ts,
                prev_hash,
                current_hash,
                resolved_actor,
                command_source,
                work_item_id,
                payload_hash,
            ),
        )
        conn.commit()
        return event_id

    def verify_audit_chain(self) -> dict[str, Any]:
        """Verify audit hash chain integrity and return an audit report."""
        conn = self._require_open()
        rows = conn.execute("SELECT * FROM audit_events ORDER BY rowid").fetchall()
        expected_prev = "0" * 64
        errors: list[str] = []
        for row in rows:
            event_id = str(row["event_id"])
            prev_hash = str(row["prev_hash"])
            if prev_hash != expected_prev:
                errors.append(
                    f"{event_id}: prev_hash mismatch "
                    f"(expected {expected_prev[:12]}..., got {prev_hash[:12]}...)",
                )
            material = (
                f"{event_id}|{row['timestamp']}|{row['prev_hash']}|{row['actor']}|"
                f"{row['command_source']}|{row['work_item_id']}|{row['payload_hash']}"
            )
            calc_hash = hashlib.sha256(str(material).encode("utf-8")).hexdigest()
            current_hash = str(row["current_hash"])
            if current_hash != calc_hash:
                errors.append(
                    f"{event_id}: current_hash mismatch "
                    f"(expected {calc_hash[:12]}..., got {current_hash[:12]}...)",
                )
            expected_prev = current_hash
        return {"ok": len(errors) == 0, "errors": errors, "event_count": len(rows)}

    def compact(self) -> None:
        """Run VACUUM to reclaim space (no-op equivalent to ChronoStore.compact)."""
        conn = self._require_open()
        conn.execute("VACUUM")

    # ------------------------------------------------------------------
    # Migration helper
    # ------------------------------------------------------------------

    def migrate_from_json(self, specsmith_dir: str | Path) -> dict[str, int]:
        """Bulk-import requirements and test cases from .specsmith/*.json files.

        Returns a dict with counts: ``{"requirements": N, "testcases": M, "skipped": K}``.
        Already-present records (by ID) are updated in-place.
        """
        # CodeQL py/path-injection: normalize + containment-check each JSON path
        # before the .exists()/.read_text() sinks below.
        _state = os.path.realpath(str(specsmith_dir))
        counts: dict[str, int] = {"requirements": 0, "testcases": 0, "skipped": 0}

        _req = os.path.realpath(os.path.join(_state, "requirements.json"))
        if _req != _state and not _req.startswith(_state + os.sep):
            raise ValueError(f"Path escapes state directory: {_req!r}")
        req_path = Path(_req)
        if req_path.exists():
            try:
                reqs = json.loads(req_path.read_text(encoding="utf-8"))
                for r in reqs:
                    if not isinstance(r, dict) or not r.get("id"):
                        counts["skipped"] += 1
                        continue
                    self.upsert(
                        SqliteRecord(
                            id=str(r["id"]),
                            kind="requirement",
                            label=str(r.get("title", r.get("id", ""))),
                            confidence=float(r.get("confidence", 0.7)),
                            data=r,
                        ),
                    )
                    counts["requirements"] += 1
            except (OSError, ValueError):
                counts["skipped"] += 1  # file unreadable or invalid JSON

        _test = os.path.realpath(os.path.join(_state, "testcases.json"))
        if _test != _state and not _test.startswith(_state + os.sep):
            raise ValueError(f"Path escapes state directory: {_test!r}")
        test_path = Path(_test)
        if test_path.exists():
            try:
                tests = json.loads(test_path.read_text(encoding="utf-8"))
                for t in tests:
                    if not isinstance(t, dict) or not t.get("id"):
                        counts["skipped"] += 1
                        continue
                    self.upsert(
                        SqliteRecord(
                            id=str(t["id"]),
                            kind="testcase",
                            label=str(t.get("title", t.get("id", ""))),
                            confidence=float(t.get("confidence", 1.0)),
                            data=t,
                        ),
                    )
                    counts["testcases"] += 1
            except (OSError, ValueError):
                counts["skipped"] += 1  # file unreadable or invalid JSON

        return counts

    def __repr__(self) -> str:
        state = "open" if self._open else "closed"
        return f"SqliteStore({self._db_path}, {state})"


def _default_actor() -> str:
    """Resolve actor from environment or git config."""
    actor = os.environ.get("SPECSMITH_ACTOR", "").strip()
    if actor:
        return actor
    git_name = (
        os.environ.get("GIT_AUTHOR_NAME", "").strip()
        or os.environ.get("GIT_COMMITTER_NAME", "").strip()
    )
    if git_name:
        return git_name
    return os.environ.get("USERNAME", "").strip() or os.environ.get("USER", "").strip() or "unknown"
