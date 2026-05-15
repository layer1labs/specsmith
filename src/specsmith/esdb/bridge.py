# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs / BitConcepts, LLC.
"""ESDB bridge — adapter between .specsmith/ JSON and ESDB concepts.

Delegation strategy:
  1. If .chronomemory/events.wal exists → delegate to ChronoStore (full
     WAL-based engine with OEA anti-hallucination fields).
  2. Otherwise → read flat .specsmith/*.json files (legacy fallback).

Write operations (upsert_record, delete_record) are only available when
ChronoStore is active. Callers should run ``specsmith esdb migrate`` to
convert a legacy project before calling write paths.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EsdbRecord:
    """Python mirror of the Rust Record type."""

    id: str
    kind: str
    status: str = "active"
    confidence: float = 0.7
    label: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    source_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return the original source data dict (used for export/backup)."""
        return (
            self.data
            if self.data
            else {
                "id": self.id,
                "kind": self.kind,
                "status": self.status,
                "confidence": self.confidence,
                "label": self.label,
            }
        )


@dataclass
class EsdbStatus:
    """ESDB health status for the REST API."""

    available: bool
    backend: str  # "esdb" or "json-fallback"
    record_count: int = 0
    wal_seq: int = 0
    epoch: int = 0
    chain_valid: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "backend": self.backend,
            "record_count": self.record_count,
            "wal_seq": self.wal_seq,
            "epoch": self.epoch,
            "chain_valid": self.chain_valid,
        }


class EsdbBridge:
    """Unified bridge to ESDB: delegates to ChronoStore when available.

    Delegation strategy:
      - ChronoStore (.chronomemory/events.wal): full WAL engine, all writes
      - JSON fallback (.specsmith/*.json): legacy read-only access
    """

    def __init__(self, project_dir: str = ".") -> None:
        self.root = Path(project_dir).resolve()
        self._requirements: list[EsdbRecord] | None = None
        self._testcases: list[EsdbRecord] | None = None
        self._store: Any = None  # ChronoStore | None

    def _get_store(self) -> Any:
        """Return an open ChronoStore if available, else None."""
        if self._store is not None:
            return self._store
        wal = self.root / ".chronomemory" / "events.wal"
        if wal.exists():
            try:
                from specsmith.esdb.store import ChronoStore

                self._store = ChronoStore(self.root).open()
            except Exception:  # noqa: BLE001
                self._store = None
        return self._store

    def status(self) -> EsdbStatus:
        """Return ESDB status."""
        store = self._get_store()
        if store is not None:
            return EsdbStatus(
                available=True,
                backend="ChronoStore WAL",
                record_count=store.record_count(),
                wal_seq=store.wal_seq(),
                chain_valid=store.chain_valid(),
            )
        # Legacy JSON fallback
        reqs = self._load_requirements()
        tests = self._load_testcases()
        return EsdbStatus(
            available=True,
            backend=".specsmith/ JSON (run esdb migrate to upgrade)",
            record_count=len(reqs) + len(tests),
        )

    def requirements(self) -> list[EsdbRecord]:
        """Load requirements as ESDB records."""
        store = self._get_store()
        if store is not None:
            return [
                EsdbRecord(
                    id=r.id,
                    kind=r.kind,
                    status=r.status,
                    confidence=r.confidence,
                    label=r.label,
                    data=r.data,
                    source_ids=r.evidence,
                )
                for r in store.query(kind="requirement")
            ]
        return self._load_requirements()

    def testcases(self) -> list[EsdbRecord]:
        """Load test cases as ESDB records."""
        store = self._get_store()
        if store is not None:
            return [
                EsdbRecord(
                    id=r.id,
                    kind=r.kind,
                    status=r.status,
                    confidence=r.confidence,
                    label=r.label,
                    data=r.data,
                    source_ids=r.evidence,
                )
                for r in store.query(kind="testcase")
            ]
        return self._load_testcases()

    def record_counts(self) -> dict[str, int]:
        """Record counts by kind (for dashboard)."""
        store = self._get_store()
        if store is not None:
            records = store.query()
            counts: dict[str, int] = {}
            for r in records:
                counts[r.kind] = counts.get(r.kind, 0) + 1
            return counts
        return {
            "requirements": len(self._load_requirements()),
            "testcases": len(self._load_testcases()),
        }

    def upsert_record(self, record: EsdbRecord) -> bool:
        """Write or update a record. Returns True if ChronoStore is active."""
        store = self._get_store()
        if store is None:
            return False
        try:
            from specsmith.esdb.store import ChronoRecord

            chrono_rec = ChronoRecord(
                id=record.id,
                kind=record.kind,
                status=record.status,
                confidence=record.confidence,
                label=record.label,
                data=record.data,
                evidence=record.source_ids,
            )
            store.upsert(chrono_rec)
            return True
        except Exception:  # noqa: BLE001
            return False

    def delete_record(self, record_id: str) -> bool:
        """Tombstone a record. Returns True if ChronoStore is active."""
        store = self._get_store()
        if store is None:
            return False
        try:
            store.delete(record_id)
            return True
        except Exception:  # noqa: BLE001
            return False

    def _load_requirements(self) -> list[EsdbRecord]:
        if self._requirements is not None:
            return self._requirements
        path = self.root / ".specsmith" / "requirements.json"
        if not path.is_file():
            self._requirements = []
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            self._requirements = [
                EsdbRecord(
                    id=r.get("id", ""),
                    kind="requirement",
                    label=r.get("title", ""),
                    confidence=float(r.get("confidence", 0.7)),
                    data=r,
                )
                for r in raw
                if isinstance(r, dict)
            ]
        except (OSError, ValueError):
            self._requirements = []
        return self._requirements

    def _load_testcases(self) -> list[EsdbRecord]:
        if self._testcases is not None:
            return self._testcases
        path = self.root / ".specsmith" / "testcases.json"
        if not path.is_file():
            self._testcases = []
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            self._testcases = [
                EsdbRecord(
                    id=r.get("id", ""),
                    kind="testcase",
                    label=r.get("title", ""),
                    confidence=float(r.get("confidence", 1.0)),
                    data=r,
                )
                for r in raw
                if isinstance(r, dict)
            ]
        except (OSError, ValueError):
            self._testcases = []
        return self._testcases
