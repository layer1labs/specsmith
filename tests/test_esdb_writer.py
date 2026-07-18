# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for specsmith.esdb_writer and related ESDB full-coverage changes.

Covers REQ-395 through REQ-401:
  - write_preflight_record  (REQ-396)
  - write_verify_record     (REQ-397)
  - write_work_item_record  (REQ-398)
  - context_seed relevance query (REQ-399)
  - context eviction write-back  (REQ-400)
  - m008 migration backfill      (REQ-401)

All tests use the free SQLite backend (no chronomemory dep required).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    """Return a tmp project root with an initialised .specsmith/ directory."""
    specsmith_dir = tmp_path / ".specsmith"
    specsmith_dir.mkdir(parents=True)
    # Force the SQLite backend so these tests never require chronomemory.
    os.environ["SPECSMITH_ESDB_BACKEND"] = "sqlite"
    yield tmp_path
    # Clean up env override after each test.
    os.environ.pop("SPECSMITH_ESDB_BACKEND", None)


def _make_preflight_payload(
    wi_id: str = "WI-AABBCCDD",
    decision: str = "accepted",
    confidence: float = 0.75,
    req_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "decision": decision,
        "work_item_id": wi_id,
        "requirement_ids": req_ids or ["REQ-001"],
        "test_case_ids": ["TEST-001"],
        "confidence_target": confidence,
        "instruction": "Proceed under governance.",
        "intent": "change",
        "ai_disclosure": {"governed_by": "specsmith"},
    }


def _make_verify_result(
    wi_id: str = "WI-AABBCCDD",
    equilibrium: bool = True,
) -> dict[str, Any]:
    return {
        "equilibrium": equilibrium,
        "confidence": 0.85 if equilibrium else 0.4,
        "summary": "All tests passed." if equilibrium else "1 test failure.",
        "files_changed": ["src/foo.py"],
        "test_results": {"passed": 10, "failed": 0},
        "retry_strategy": "",
        "work_item_id": wi_id,
    }


def _make_wi(
    wi_id: str = "WI-AABBCCDD",
    status: str = "open",
    intent: str = "add retry logic",
    req_ids: list[str] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=wi_id,
        status=status,
        kind="feature",
        intent=intent,
        confidence_target=0.8,
        requirement_ids=req_ids or ["REQ-001"],
        test_case_ids=["TEST-001"],
        verified=False,
        promoted_to_req="",
        blast_radius_estimate="local",
        created_at="2026-06-25T00:00:00Z",
        updated_at="2026-06-25T00:00:00Z",
        closed_reason="",
    )


# ---------------------------------------------------------------------------
# REQ-396: write_preflight_record
# ---------------------------------------------------------------------------


def test_write_preflight_record_sqlite(tmp_project: Path) -> None:
    """A preflight payload is written to SqliteStore as kind='preflight_decision'."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_writer import write_preflight_record

    payload = _make_preflight_payload()
    result = write_preflight_record(tmp_project, payload)
    assert result is True

    with SqliteStore(tmp_project) as store:
        rec = store.get("PF-WI-AABBCCDD")

    assert rec is not None, "Expected a record with id='PF-WI-AABBCCDD'"
    assert rec.kind == "preflight_decision"
    assert rec.status == "active"
    assert rec.confidence == pytest.approx(0.75)
    assert "REQ-001" in rec.source_ids
    assert rec.data["decision"] == "accepted"
    assert rec.data["work_item_id"] == "WI-AABBCCDD"


def test_write_preflight_record_no_wi_id_is_noop(tmp_project: Path) -> None:
    """Preflight without a work_item_id (needs_clarification) is not persisted."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_writer import write_preflight_record

    payload = _make_preflight_payload(wi_id="", decision="needs_clarification")
    result = write_preflight_record(tmp_project, payload)
    assert result is False  # no WI minted → nothing to persist

    with SqliteStore(tmp_project) as store:
        assert store.record_count() == 0


# ---------------------------------------------------------------------------
# REQ-397: write_verify_record
# ---------------------------------------------------------------------------


def test_write_verify_record_sqlite_equilibrium(tmp_project: Path) -> None:
    """Verify result on equilibrium is persisted with confidence=0.85."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_writer import write_verify_record

    result_payload = _make_verify_result(equilibrium=True)
    ok = write_verify_record(tmp_project, result_payload)
    assert ok is True

    with SqliteStore(tmp_project) as store:
        rec = store.get("VERIFY-WI-AABBCCDD")

    assert rec is not None
    assert rec.kind == "verify_result"
    assert rec.confidence == pytest.approx(0.85)
    assert rec.data["equilibrium"] is True
    assert "WI-AABBCCDD" in rec.source_ids


def test_write_verify_record_tombstones_preflight_on_equilibrium(tmp_project: Path) -> None:
    """When equilibrium, the corresponding preflight_decision record is tombstoned."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_writer import write_preflight_record, write_verify_record

    # First write a preflight record
    write_preflight_record(tmp_project, _make_preflight_payload())

    # Then verify with equilibrium
    write_verify_record(tmp_project, _make_verify_result(equilibrium=True))

    with SqliteStore(tmp_project) as store:
        pf = store.get("PF-WI-AABBCCDD")

    # After equilibrium, the preflight record should be tombstoned
    assert pf is not None
    assert pf.status == "tombstone", f"Expected tombstone, got {pf.status!r}"


def test_write_verify_record_no_tombstone_without_equilibrium(tmp_project: Path) -> None:
    """Without equilibrium, the preflight_decision record stays active."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_writer import write_preflight_record, write_verify_record

    write_preflight_record(tmp_project, _make_preflight_payload())
    write_verify_record(tmp_project, _make_verify_result(equilibrium=False))

    with SqliteStore(tmp_project) as store:
        pf = store.get("PF-WI-AABBCCDD")

    assert pf is not None
    assert pf.status == "active"


# ---------------------------------------------------------------------------
# REQ-398: write_work_item_record
# ---------------------------------------------------------------------------


def test_write_work_item_record_sqlite(tmp_project: Path) -> None:
    """WorkItem is written to SqliteStore as kind='work_item'."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_writer import write_work_item_record

    wi = _make_wi()
    ok = write_work_item_record(tmp_project, wi)
    assert ok is True

    with SqliteStore(tmp_project) as store:
        rec = store.get("WI-AABBCCDD")

    assert rec is not None
    assert rec.kind == "work_item"
    assert rec.status == "active"  # open → active
    assert "REQ-001" in rec.source_ids
    assert rec.data["status"] == "open"


def test_write_work_item_record_terminal_becomes_tombstone(tmp_project: Path) -> None:
    """Closed/promoted WIs get ESDB status='tombstone'."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_writer import write_work_item_record

    for terminal_status in ("closed", "promoted", "archived", "rejected"):
        wi = _make_wi(wi_id=f"WI-{terminal_status.upper()[:8]:08}", status=terminal_status)
        write_work_item_record(tmp_project, wi)

    with SqliteStore(tmp_project) as store:
        # All four should be tombstoned
        active = store.query(kind="work_item", status="active")
        tombstoned = store.query(kind="work_item", status="tombstone")

    assert len(active) == 0
    assert len(tombstoned) == 4


# ---------------------------------------------------------------------------
# REQ-399: context_seed relevance query
# ---------------------------------------------------------------------------


def test_context_seed_uses_preflight_records(tmp_project: Path) -> None:
    """build_context_seed includes preflight_decision records from SqliteStore."""
    from specsmith.agent.context_seed import build_context_seed
    from specsmith.esdb_writer import write_preflight_record

    # Write a preflight record
    payload = _make_preflight_payload(wi_id="WI-SEED0001", confidence=0.8)
    write_preflight_record(tmp_project, payload)

    seed = build_context_seed(tmp_project)

    # Find the ESDB system turn
    esdb_turn = next(
        (t for t in seed if "ESDB governance context" in t.get("content", "")),
        None,
    )
    assert esdb_turn is not None, "No ESDB governance context turn in seed"
    assert "WI-SEED0001" in esdb_turn["content"], "Preflight record missing from context seed"
    assert "preflight_decision" in esdb_turn["content"]


def test_context_seed_excludes_low_confidence_records(tmp_project: Path) -> None:
    """build_context_seed omits records with confidence < 0.6 (H18 RAG filter)."""
    from specsmith.agent.context_seed import build_context_seed
    from specsmith.esdb import SqliteRecord, SqliteStore

    # Write a low-confidence record directly
    with SqliteStore(tmp_project) as store:
        store.upsert(
            SqliteRecord(
                id="LOW-CONF-001",
                kind="preflight_decision",
                label="low confidence test",
                confidence=0.3,  # below 0.6 threshold
            )
        )

    seed = build_context_seed(tmp_project)
    esdb_turn = next(
        (t for t in seed if "ESDB governance context" in t.get("content", "")),
        None,
    )
    # Low-confidence record should not appear
    if esdb_turn is not None:
        assert "LOW-CONF-001" not in esdb_turn["content"]


# ---------------------------------------------------------------------------
# REQ-471: non-destructive context residency write-back
# ---------------------------------------------------------------------------


def test_eviction_writes_residency_without_tombstone(tmp_project: Path) -> None:
    """Offloading marks residency cold while durable records remain active."""
    from specsmith.context_orchestrator import ContextOrchestrator
    from specsmith.esdb import SqliteRecord, SqliteStore

    # Write two records: one high, one low confidence
    with SqliteStore(tmp_project) as store:
        store.upsert(
            SqliteRecord(
                id="HIGH-001",
                kind="preflight_decision",
                label="high conf",
                confidence=0.9,
            )
        )
        store.upsert(
            SqliteRecord(
                id="LOW-001",
                kind="preflight_decision",
                label="low conf",
                confidence=0.3,
            )
        )

    orchestrator = ContextOrchestrator(tmp_project)
    evicted = orchestrator._evict_low_confidence_records(min_confidence=0.5)  # noqa: SLF001

    assert evicted == 1  # only the low-confidence record

    with SqliteStore(tmp_project) as store:
        low_rec = store.get("LOW-001")
        high_rec = store.get("HIGH-001")

    assert low_rec is not None and low_rec.status == "active"
    assert high_rec is not None and high_rec.status == "active"
    residency = json.loads(
        (tmp_project / ".specsmith/context-residency.json").read_text(encoding="utf-8")
    )
    assert residency["records"] == {"LOW-001": "cold"}


def test_eviction_exempts_governance_kinds(tmp_project: Path) -> None:
    """Governance records remain pinned and active."""
    from specsmith.context_orchestrator import ContextOrchestrator
    from specsmith.esdb import SqliteRecord, SqliteStore

    with SqliteStore(tmp_project) as store:
        store.upsert(
            SqliteRecord(
                id="REQ-001",
                kind="requirement",
                label="a requirement",
                confidence=0.1,  # low confidence
            )
        )

    orchestrator = ContextOrchestrator(tmp_project)
    evicted = orchestrator._evict_low_confidence_records(min_confidence=0.5)  # noqa: SLF001

    assert evicted == 0  # requirement is exempt

    with SqliteStore(tmp_project) as store:
        rec = store.get("REQ-001")
    assert rec is not None and rec.status == "active"


# ---------------------------------------------------------------------------
# REQ-401: M008 migration backfill
# ---------------------------------------------------------------------------


def test_m008_backfills_workitems(tmp_project: Path) -> None:
    """M008 migration imports existing workitems.json into ESDB."""
    from specsmith.esdb import SqliteStore
    from specsmith.migrations.m008_esdb_full_coverage import EsdbFullCoverageMigration

    # Write a workitems.json with two WIs
    wi_data = [
        {
            "id": "WI-M008AA01",
            "status": "open",
            "intent": "test m008",
            "requirement_ids": ["REQ-001"],
            "test_case_ids": [],
            "confidence_target": 0.7,
        },
        {
            "id": "WI-M008BB02",
            "status": "closed",
            "intent": "done",
            "requirement_ids": [],
            "test_case_ids": [],
            "confidence_target": 0.85,
        },
    ]
    (tmp_project / ".specsmith" / "workitems.json").write_text(
        json.dumps(wi_data), encoding="utf-8"
    )

    migration = EsdbFullCoverageMigration()
    result = migration.run(tmp_project)

    assert result.success is True
    assert result.dry_run is False
    assert "2 work item(s)" in result.message

    with SqliteStore(tmp_project) as store:
        rec_open = store.get("WI-M008AA01")
        rec_closed = store.get("WI-M008BB02")

    assert rec_open is not None and rec_open.kind == "work_item" and rec_open.status == "active"
    assert rec_closed is not None and rec_closed.kind == "work_item"
    assert rec_closed.status == "tombstone"


def test_m008_is_idempotent(tmp_project: Path) -> None:
    """Running M008 twice does not fail or double-count."""
    from specsmith.migrations.m008_esdb_full_coverage import EsdbFullCoverageMigration

    (tmp_project / ".specsmith" / "workitems.json").write_text("[]", encoding="utf-8")

    migration = EsdbFullCoverageMigration()
    r1 = migration.run(tmp_project)
    r2 = migration.run(tmp_project)

    assert r1.success is True
    assert r2.success is True
    assert "already applied" in r2.message


def test_m008_dry_run_no_writes(tmp_project: Path) -> None:
    """M008 dry-run reports counts but writes nothing."""
    from specsmith.esdb import SqliteStore
    from specsmith.migrations.m008_esdb_full_coverage import EsdbFullCoverageMigration

    wi_data = [
        {
            "id": "WI-DRYRUN01",
            "status": "open",
            "intent": "dry",
            "requirement_ids": [],
            "test_case_ids": [],
            "confidence_target": 0.7,
        }
    ]
    wi_path = tmp_project / ".specsmith" / "workitems.json"
    wi_path.write_text(json.dumps(wi_data), encoding="utf-8")

    migration = EsdbFullCoverageMigration()
    result = migration.run(tmp_project, dry_run=True)

    assert result.dry_run is True
    assert "1 work item(s)" in result.message
    # Marker file must NOT exist after a dry run
    assert not (tmp_project / ".specsmith" / "esdb-full-coverage").exists()

    with SqliteStore(tmp_project) as store:
        assert store.record_count() == 0


def test_m008_rollback_removes_marker(tmp_project: Path) -> None:
    """M008 rollback removes the idempotency marker so re-run is possible."""
    from specsmith.migrations.m008_esdb_full_coverage import EsdbFullCoverageMigration

    (tmp_project / ".specsmith" / "workitems.json").write_text("[]", encoding="utf-8")
    migration = EsdbFullCoverageMigration()
    migration.run(tmp_project)  # create marker

    assert (tmp_project / ".specsmith" / "esdb-full-coverage").exists()

    rollback_result = migration.rollback(tmp_project)
    assert rollback_result.success is True
    assert not (tmp_project / ".specsmith" / "esdb-full-coverage").exists()
