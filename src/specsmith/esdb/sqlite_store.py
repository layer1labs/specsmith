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

import json
import sqlite3
import time
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

    __slots__ = ("id", "kind", "status", "label", "confidence", "data", "source_ids")

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
        self.root = Path(project_root).resolve()
        self._db_path = self.root / ".specsmith" / _DB_FILENAME
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

    def chain_valid(self) -> bool:
        """Always True — SQLite ACID guarantees integrity (no SHA-256 WAL chain)."""
        return True

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
        state_dir = Path(specsmith_dir)
        counts: dict[str, int] = {"requirements": 0, "testcases": 0, "skipped": 0}

        req_path = state_dir / "requirements.json"
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
                        )
                    )
                    counts["requirements"] += 1
            except (OSError, ValueError):
                counts["skipped"] += 1  # file unreadable or invalid JSON

        test_path = state_dir / "testcases.json"
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
                        )
                    )
                    counts["testcases"] += 1
            except (OSError, ValueError):
                counts["skipped"] += 1  # file unreadable or invalid JSON

        return counts

    def __repr__(self) -> str:
        state = "open" if self._open else "closed"
        return f"SqliteStore({self._db_path}, {state})"
