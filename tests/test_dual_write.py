# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for ESDB-first dual-write paths (REQ-403, REQ-404, REQ-405, REQ-408, REQ-410)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    (tmp_path / ".specsmith").mkdir(parents=True)
    os.environ["SPECSMITH_ESDB_BACKEND"] = "sqlite"
    yield tmp_path
    os.environ.pop("SPECSMITH_ESDB_BACKEND", None)


# ---------------------------------------------------------------------------
# write_ledger_event (REQ-403)
# ---------------------------------------------------------------------------


def test_write_ledger_event_creates_record(tmp_project: Path) -> None:
    """write_ledger_event creates a ledger_event record in ESDB."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_writer import write_ledger_event

    result = write_ledger_event(
        tmp_project,
        description="add feature X",
        entry_type="feature",
        author="agent",
        reqs="REQ-001,REQ-002",
        status="complete",
    )
    assert result is True

    with SqliteStore(tmp_project) as store:
        records = store.query(kind="ledger_event", status="active")

    assert len(records) == 1
    rec = records[0]
    assert rec.label == "add feature X"
    assert rec.confidence == pytest.approx(0.9)
    assert rec.data["description"] == "add feature X"
    assert rec.data["entry_type"] == "feature"
    assert rec.data["author"] == "agent"
    assert "REQ-001" in rec.source_ids
    assert "REQ-002" in rec.source_ids
    assert rec.data["timestamp"]  # non-empty


def test_write_ledger_event_via_add_entry(tmp_project: Path) -> None:
    """ledger.add_entry() creates a ledger_event record as a side effect (REQ-403)."""
    from specsmith.esdb import SqliteStore
    from specsmith.ledger import add_entry

    # Write LEDGER.md first
    ledger_path = tmp_project / "LEDGER.md"
    ledger_path.write_text("# Change Ledger\n", encoding="utf-8")

    add_entry(tmp_project, description="dual write test", entry_type="task", author="test")

    with SqliteStore(tmp_project) as store:
        records = store.query(kind="ledger_event", status="active")

    assert len(records) >= 1
    assert any(r.label == "dual write test" for r in records)


# ---------------------------------------------------------------------------
# write_seal_record (REQ-404)
# ---------------------------------------------------------------------------


def test_write_seal_record_creates_record(tmp_project: Path) -> None:
    """write_seal_record creates a seal_record in ESDB."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_writer import write_seal_record

    record_dict = {
        "seal_id": "SEAL-0001",
        "seal_type": "decision",
        "description": "chose FastAPI",
        "content_hash": "abc123",
        "prev_hash": "0" * 64,
        "entry_hash": "def456",
        "timestamp": "2026-06-25T12:00:00+00:00",
        "author": "test",
        "artifact_ids": ["DEC-001"],
    }
    result = write_seal_record(tmp_project, record_dict)
    assert result is True

    with SqliteStore(tmp_project) as store:
        rec = store.get("ESDB-SEAL-0001")

    assert rec is not None
    assert rec.kind == "seal_record"
    assert rec.label == "chose FastAPI"
    assert rec.confidence == pytest.approx(0.9)
    assert "DEC-001" in rec.source_ids


def test_seal_record_via_tracevault(tmp_project: Path) -> None:
    """TraceVault.seal() creates a seal_record in ESDB as a side effect (REQ-404)."""
    from specsmith.esdb import SqliteStore
    from specsmith.trace import SealType, TraceVault

    vault = TraceVault(tmp_project)
    vault.seal(SealType.DECISION, "adopted DI framework", author="test")

    with SqliteStore(tmp_project) as store:
        records = store.query(kind="seal_record", status="active")

    assert len(records) >= 1
    assert any("DI framework" in r.label for r in records)


def test_write_seal_record_no_seal_id_returns_false(tmp_project: Path) -> None:
    """write_seal_record returns False when seal_id is missing."""
    from specsmith.esdb_writer import write_seal_record

    result = write_seal_record(tmp_project, {"description": "no id"})
    assert result is False


# ---------------------------------------------------------------------------
# write_session_metric (REQ-405)
# ---------------------------------------------------------------------------


def test_write_session_metric_creates_record(tmp_project: Path) -> None:
    """write_session_metric creates a session_metric record in ESDB."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_writer import write_session_metric

    record_dict = {
        "session_id": "S-ABCDEF01",
        "timestamp": "2026-06-25T12:00:00Z",
        "tokens_total": 2000,
        "cost_usd": 0.002,
        "passed": True,
        "rework_turns": 1,
        "work_item_id": "WI-TEST01",
    }
    result = write_session_metric(tmp_project, record_dict)
    assert result is True

    with SqliteStore(tmp_project) as store:
        rec = store.get("MET-S-ABCDEF01")

    assert rec is not None
    assert rec.kind == "session_metric"
    assert rec.confidence == pytest.approx(0.8)
    assert rec.data["tokens_total"] == 2000
    assert rec.data["passed"] is True
    assert "WI-TEST01" in rec.source_ids


def test_session_metric_via_metricsstore(tmp_project: Path) -> None:
    """MetricsStore.append() creates a session_metric in ESDB (REQ-405)."""
    from specsmith.esdb import SqliteStore
    from specsmith.project_metrics import MetricsRecord, MetricsStore

    store_ms = MetricsStore(tmp_project)
    store_ms.append(
        MetricsRecord.new(passed=True, input_tokens=800, output_tokens=700, command="test")
    )

    with SqliteStore(tmp_project) as store:
        records = store.query(kind="session_metric", status="active")

    assert len(records) >= 1
    assert any(r.data.get("passed") is True for r in records)


# ---------------------------------------------------------------------------
# write_token_metric (REQ-410)
# ---------------------------------------------------------------------------


def test_write_token_metric_creates_record(tmp_project: Path) -> None:
    """write_token_metric creates a token_metric record in ESDB."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_writer import write_token_metric

    # Pre-initialise the ESDB schema so the sqlite file exists before the call
    with SqliteStore(tmp_project):
        pass

    result = write_token_metric(
        tmp_project,
        input_tokens=100,
        output_tokens=50,
        cost_usd=0.001,
        model="ollama",
        command_source="chat",
        work_item_id="WI-TEST",
    )
    assert result is True

    with SqliteStore(tmp_project) as store:
        records = store.query(kind="token_metric", status="active")

    assert len(records) == 1
    rec = records[0]
    assert rec.id.startswith("TOK-")
    assert rec.confidence == pytest.approx(1.0)
    assert rec.data["input_tokens"] == 100
    assert rec.data["output_tokens"] == 50
    assert rec.data["total_tokens"] == 150
    assert "WI-TEST" in rec.source_ids


def test_write_token_metric_no_esdb_returns_false(tmp_path: Path) -> None:
    """write_token_metric returns False (not raises) when no ESDB exists."""
    from specsmith.esdb_writer import write_token_metric

    (tmp_path / ".specsmith").mkdir()
    result = write_token_metric(tmp_path, input_tokens=10, output_tokens=5)
    assert result is False


# ---------------------------------------------------------------------------
# ESDB-first commit message (REQ-408)
# ---------------------------------------------------------------------------


def test_generate_commit_message_uses_esdb_first(tmp_project: Path) -> None:
    """generate_commit_message reads from ledger_event ESDB records first (REQ-408)."""
    from specsmith.esdb_writer import write_ledger_event
    from specsmith.vcs_commands import generate_commit_message

    # Create a LEDGER.md with a different message
    ledger_path = tmp_project / "LEDGER.md"
    ledger_path.write_text(
        "# Change Ledger\n\n## 2026-06-01T10:00 — old ledger message\n",
        encoding="utf-8",
    )

    # Write a ledger_event to ESDB with a newer timestamp
    write_ledger_event(
        tmp_project,
        description="esdb-based commit message",
        entry_type="task",
        author="test",
    )

    msg = generate_commit_message(tmp_project)
    assert msg == "esdb-based commit message"


def test_generate_commit_message_falls_back_to_ledger_md(tmp_project: Path) -> None:
    """generate_commit_message falls back to LEDGER.md when no ESDB records exist."""
    from specsmith.vcs_commands import generate_commit_message

    ledger_path = tmp_project / "LEDGER.md"
    ledger_path.write_text(
        "# Change Ledger\n\n## 2026-06-01T10:00 — fallback ledger message\n",
        encoding="utf-8",
    )

    msg = generate_commit_message(tmp_project)
    assert "fallback ledger message" in msg
