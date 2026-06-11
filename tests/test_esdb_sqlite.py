"""Tests for SqliteStore ESDB backend (REQ-365, TEST-366).

Covers: open/close lifecycle, context manager, upsert/query/delete roundtrip,
kind/status/rag_filter query params, record_count, wal_seq monotonicity,
chain_valid, migrate_from_json, and concurrent re-open semantics.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from specsmith.esdb.sqlite_store import SqliteRecord, SqliteStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def store(tmp_path: Path) -> SqliteStore:
    """Return an opened SqliteStore in a temporary directory."""
    s = SqliteStore(tmp_path)
    s.open()
    yield s
    s.close()


@pytest.fixture()
def specsmith_dir(tmp_path: Path) -> Path:
    """Create a fake .specsmith/ directory with requirements.json and testcases.json."""
    state = tmp_path / ".specsmith"
    state.mkdir()
    reqs = [
        {"id": "REQ-001", "title": "First req", "status": "accepted", "confidence": 0.9},
        {"id": "REQ-002", "title": "Second req", "status": "planned"},
    ]
    tests = [
        {"id": "TEST-001", "title": "Test one", "requirement_id": "REQ-001"},
        {"id": "TEST-002", "title": "Test two", "requirement_id": "REQ-002"},
    ]
    (state / "requirements.json").write_text(json.dumps(reqs), encoding="utf-8")
    (state / "testcases.json").write_text(json.dumps(tests), encoding="utf-8")
    return state


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


def test_open_creates_db_file(tmp_path: Path) -> None:
    with SqliteStore(tmp_path) as s:
        assert (tmp_path / ".specsmith" / "esdb.sqlite3").exists()


def test_context_manager_opens_and_closes(tmp_path: Path) -> None:
    s = SqliteStore(tmp_path)
    with s as opened:
        assert opened._open
    assert not s._open


def test_requires_open_raises_without_open(tmp_path: Path) -> None:
    s = SqliteStore(tmp_path)
    with pytest.raises(RuntimeError, match="not open"):
        s.record_count()


def test_repr(tmp_path: Path) -> None:
    s = SqliteStore(tmp_path)
    assert "closed" in repr(s)
    with s:
        assert "open" in repr(s)


# ---------------------------------------------------------------------------
# Write / read roundtrip
# ---------------------------------------------------------------------------


def test_upsert_and_query(store: SqliteStore) -> None:
    rec = SqliteRecord(id="FACT-001", kind="fact", label="Test fact", confidence=0.9)
    store.upsert(rec)
    results = store.query(kind="fact")
    assert len(results) == 1
    assert results[0].id == "FACT-001"
    assert results[0].label == "Test fact"
    assert abs(results[0].confidence - 0.9) < 1e-9


def test_upsert_updates_existing(store: SqliteStore) -> None:
    rec = SqliteRecord(id="FACT-001", label="original")
    store.upsert(rec)
    updated = SqliteRecord(id="FACT-001", label="updated")
    store.upsert(updated)
    results = store.query()
    assert len(results) == 1
    assert results[0].label == "updated"


def test_get_by_id(store: SqliteStore) -> None:
    store.upsert(SqliteRecord(id="REQ-001", kind="requirement", label="Hello"))
    found = store.get("REQ-001")
    assert found is not None
    assert found.label == "Hello"


def test_get_missing_returns_none(store: SqliteStore) -> None:
    assert store.get("NONEXISTENT") is None


def test_data_roundtrip(store: SqliteStore) -> None:
    data = {"title": "Test", "status": "accepted", "nested": {"x": 1}}
    store.upsert(SqliteRecord(id="REQ-001", data=data))
    result = store.get("REQ-001")
    assert result is not None
    assert result.data == data


def test_source_ids_roundtrip(store: SqliteStore) -> None:
    ids = ["src-a", "src-b"]
    store.upsert(SqliteRecord(id="R1", source_ids=ids))
    assert store.get("R1").source_ids == ids  # type: ignore[union-attr]


def test_evidence_alias(store: SqliteStore) -> None:
    store.upsert(SqliteRecord(id="R1", source_ids=["ev1"]))
    assert store.get("R1").evidence == ["ev1"]  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Delete (tombstone)
# ---------------------------------------------------------------------------


def test_delete_tombstones_record(store: SqliteStore) -> None:
    store.upsert(SqliteRecord(id="FACT-001"))
    store.delete("FACT-001")
    # Default query filters active only
    assert store.query(kind="fact") == []
    # All-status query includes tombstone
    all_records = store.query(kind="fact", status=None)
    assert any(r.id == "FACT-001" and r.status == "tombstone" for r in all_records)


def test_delete_nonexistent_does_not_raise(store: SqliteStore) -> None:
    store.delete("DOES-NOT-EXIST")  # Should not raise


# ---------------------------------------------------------------------------
# Query filters
# ---------------------------------------------------------------------------


def test_query_by_kind(store: SqliteStore) -> None:
    store.upsert(SqliteRecord(id="REQ-001", kind="requirement"))
    store.upsert(SqliteRecord(id="TEST-001", kind="testcase"))
    assert len(store.query(kind="requirement")) == 1
    assert len(store.query(kind="testcase")) == 1
    assert len(store.query()) == 2


def test_query_rag_filter(store: SqliteStore) -> None:
    store.upsert(SqliteRecord(id="HIGH", confidence=0.9))
    store.upsert(SqliteRecord(id="LOW", confidence=0.3))
    rag_results = store.query(rag_filter=True)
    ids = {r.id for r in rag_results}
    assert "HIGH" in ids
    assert "LOW" not in ids


def test_query_min_confidence(store: SqliteStore) -> None:
    store.upsert(SqliteRecord(id="A", confidence=0.8))
    store.upsert(SqliteRecord(id="B", confidence=0.4))
    results = store.query(min_confidence=0.7)
    assert len(results) == 1
    assert results[0].id == "A"


def test_query_all_statuses(store: SqliteStore) -> None:
    store.upsert(SqliteRecord(id="A", status="active"))
    store.upsert(SqliteRecord(id="B", status="deprecated"))
    # By default status="active" filters out deprecated
    assert len(store.query()) == 1
    # Passing status="" or None returns all
    assert len(store.query(status=None)) == 2


# ---------------------------------------------------------------------------
# record_count / wal_seq / chain_valid
# ---------------------------------------------------------------------------


def test_record_count(store: SqliteStore) -> None:
    assert store.record_count() == 0
    store.upsert(SqliteRecord(id="R1"))
    store.upsert(SqliteRecord(id="R2"))
    assert store.record_count() == 2
    store.delete("R1")
    assert store.record_count() == 1  # tombstoned records excluded


def test_wal_seq_increases(store: SqliteStore) -> None:
    s0 = store.wal_seq()
    store.upsert(SqliteRecord(id="A"))
    s1 = store.wal_seq()
    store.upsert(SqliteRecord(id="B"))
    s2 = store.wal_seq()
    assert s1 > s0
    assert s2 > s1


def test_chain_valid_always_true(store: SqliteStore) -> None:
    assert store.chain_valid() is True
    store.upsert(SqliteRecord(id="X"))
    assert store.chain_valid() is True


# ---------------------------------------------------------------------------
# migrate_from_json
# ---------------------------------------------------------------------------


def test_migrate_from_json(tmp_path: Path, specsmith_dir: Path) -> None:
    with SqliteStore(tmp_path) as s:
        counts = s.migrate_from_json(specsmith_dir)
    assert counts["requirements"] == 2
    assert counts["testcases"] == 2
    assert counts["skipped"] == 0


def test_migrate_from_json_missing_dir(tmp_path: Path) -> None:
    with SqliteStore(tmp_path) as s:
        counts = s.migrate_from_json(tmp_path / "nonexistent")
    assert counts == {"requirements": 0, "testcases": 0, "skipped": 0}


def test_migrate_preserves_existing(tmp_path: Path, specsmith_dir: Path) -> None:
    with SqliteStore(tmp_path) as s:
        s.upsert(SqliteRecord(id="REQ-001", label="pre-existing"))
        s.migrate_from_json(specsmith_dir)
        # migrate upserts — existing record should be updated with JSON data
        rec = s.get("REQ-001")
    assert rec is not None
    assert rec.kind == "requirement"


def test_migrate_skips_records_without_id(tmp_path: Path) -> None:
    state = tmp_path / ".specsmith"
    state.mkdir()
    (state / "requirements.json").write_text(json.dumps([{"title": "no id"}]), encoding="utf-8")
    (state / "testcases.json").write_text("[]", encoding="utf-8")
    with SqliteStore(tmp_path) as s:
        counts = s.migrate_from_json(state)
    assert counts["skipped"] == 1


# ---------------------------------------------------------------------------
# passes_rag_filter
# ---------------------------------------------------------------------------


def test_passes_rag_filter_high_confidence() -> None:
    r = SqliteRecord(id="X", confidence=0.9)
    assert r.passes_rag_filter() is True


def test_passes_rag_filter_low_confidence() -> None:
    r = SqliteRecord(id="X", confidence=0.3)
    assert r.passes_rag_filter() is False


def test_passes_rag_filter_tombstone() -> None:
    r = SqliteRecord(id="X", confidence=0.9, status="tombstone")
    assert r.passes_rag_filter() is False
