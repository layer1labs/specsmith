# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Integration tests for ESDB write paths through governance_logic and wi_store.

Tests the full call chain:
  governance_logic.run_preflight()  → esdb_writer.write_preflight_record()  → SqliteStore
  governance_logic.run_verify()     → esdb_writer.write_verify_record()     → SqliteStore
  wi_store.WorkItemStore.create()   → esdb_writer.write_work_item_record()  → SqliteStore
  agent.context_seed.build_context_seed() ← SqliteStore (session resume)

All tests use the free SQLite backend.  No LLM, no chronomemory dep required.

Covers: REQ-395 (TEST-395), REQ-396 (TEST-396), REQ-397 (TEST-397),
        REQ-398 (TEST-398), REQ-399 (TEST-399)
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    """Minimal project root with .specsmith/ directory and SQLite backend forced."""
    (tmp_path / ".specsmith").mkdir(parents=True)
    os.environ["SPECSMITH_ESDB_BACKEND"] = "sqlite"
    yield tmp_path
    os.environ.pop("SPECSMITH_ESDB_BACKEND", None)


# ---------------------------------------------------------------------------
# REQ-395 (TEST-395): ESDBWriter best-effort — never raises
# ---------------------------------------------------------------------------


def test_esdb_writer_best_effort_returns_false_on_bad_root(tmp_path: Path) -> None:
    """write_preflight_record returns False (not raises) for a bad/empty payload."""
    from specsmith.esdb_writer import write_preflight_record

    # Empty payload → no work_item_id → graceful False
    result = write_preflight_record(tmp_path, {})
    assert result is False


def test_esdb_writer_best_effort_write_work_item_bad_wi(tmp_path: Path) -> None:
    """write_work_item_record returns False (not raises) when wi has no id attr."""
    from types import SimpleNamespace

    from specsmith.esdb_writer import write_work_item_record

    # SimpleNamespace with no 'id' attribute will be duck-typed; missing id
    # means the SqliteRecord ctor will raise — should be swallowed.
    bad_wi = SimpleNamespace(
        id="",  # empty id → SqliteRecord constraint
        status="open",
        kind="feature",
        intent="",
        confidence_target=0.7,
        requirement_ids=[],
        test_case_ids=[],
        verified=False,
        promoted_to_req="",
        blast_radius_estimate="",
        created_at="",
        updated_at="",
        closed_reason="",
    )
    os.environ["SPECSMITH_ESDB_BACKEND"] = "sqlite"
    try:
        result = write_work_item_record(tmp_path, bad_wi)
        # Either False or True — important: must not raise
        assert result in (True, False)
    finally:
        os.environ.pop("SPECSMITH_ESDB_BACKEND", None)


# ---------------------------------------------------------------------------
# REQ-396 (TEST-396): run_preflight writes preflight_decision
# ---------------------------------------------------------------------------


def test_run_preflight_writes_preflight_decision(tmp_project: Path) -> None:
    """governance_logic.run_preflight() creates a preflight_decision ESDB record."""
    from specsmith.esdb import SqliteStore
    from specsmith.governance_logic import run_preflight

    payload = run_preflight("explain how the system works", tmp_project)

    assert payload["decision"] == "accepted"
    wi_id = payload["work_item_id"]
    assert wi_id, "Expected a WI to be minted for an accepted read_only_ask"

    with SqliteStore(tmp_project) as store:
        rec = store.get(f"PF-{wi_id}")

    assert rec is not None, f"Expected ESDB record for PF-{wi_id}"
    assert rec.kind == "preflight_decision"
    assert rec.status == "active"
    assert rec.confidence == pytest.approx(payload["confidence_target"], abs=0.01)
    assert rec.data["decision"] == "accepted"
    assert rec.data["work_item_id"] == wi_id


def test_run_preflight_predict_only_no_esdb_record(tmp_project: Path) -> None:
    """predict_only=True does not mint a WI and thus writes no ESDB record."""
    from specsmith.esdb import SqliteStore
    from specsmith.governance_logic import run_preflight

    payload = run_preflight(
        "explain how the system works",
        tmp_project,
        predict_only=True,
    )

    assert payload["decision"] == "accepted"
    assert payload["work_item_id"] == ""  # no WI minted

    with SqliteStore(tmp_project) as store:
        assert store.record_count() == 0, "predict_only=True must write no ESDB records"


# ---------------------------------------------------------------------------
# REQ-397 (TEST-397): run_verify writes verify_result and tombstones preflight
# ---------------------------------------------------------------------------


def test_run_verify_writes_verify_result(tmp_project: Path) -> None:
    """governance_logic.run_verify() creates a verify_result ESDB record on equilibrium."""
    from specsmith.esdb import SqliteStore
    from specsmith.governance_logic import run_verify

    wi_id = "WI-INTEG001"
    result = run_verify(
        diff="--- a\n+++ b\n@@\n-x\n+y\n",
        files_changed=["src/foo.py"],
        test_results={"passed": 1, "failed": 0},
        project_dir=tmp_project,
        work_item_id=wi_id,
    )

    assert result["equilibrium"] is True

    with SqliteStore(tmp_project) as store:
        rec = store.get(f"VERIFY-{wi_id}")

    assert rec is not None
    assert rec.kind == "verify_result"
    assert rec.status == "active"
    assert rec.confidence == pytest.approx(0.85)
    assert rec.data["equilibrium"] is True
    assert wi_id in rec.source_ids


def test_run_verify_no_equilibrium_writes_low_confidence(tmp_project: Path) -> None:
    """run_verify() without equilibrium writes a verify_result with confidence=0.4."""
    from specsmith.esdb import SqliteStore
    from specsmith.governance_logic import run_verify

    wi_id = "WI-INTEG002"
    result = run_verify(
        diff="--- a\n+++ b\n@@\n-x\n+y\n",
        files_changed=["src/bar.py"],
        test_results={"passed": 0, "failed": 2},
        project_dir=tmp_project,
        work_item_id=wi_id,
    )

    assert result["equilibrium"] is False

    with SqliteStore(tmp_project) as store:
        rec = store.get(f"VERIFY-{wi_id}")

    assert rec is not None
    assert rec.confidence == pytest.approx(0.4)
    assert rec.data["equilibrium"] is False


def test_run_verify_tombstones_preflight_on_equilibrium(tmp_project: Path) -> None:
    """run_verify() with equilibrium tombstones the preflight_decision record."""
    from specsmith.esdb import SqliteStore
    from specsmith.governance_logic import run_preflight, run_verify

    # Mint a preflight first
    payload = run_preflight("explain how the system works", tmp_project)
    wi_id = payload["work_item_id"]
    assert wi_id

    # Verify with equilibrium → should tombstone preflight_decision
    run_verify(
        diff="--- a\n+++ b\n@@\n-x\n+y\n",
        files_changed=["src/foo.py"],
        test_results={"passed": 1, "failed": 0},
        project_dir=tmp_project,
        work_item_id=wi_id,
    )

    with SqliteStore(tmp_project) as store:
        pf_rec = store.get(f"PF-{wi_id}")

    assert pf_rec is not None
    assert pf_rec.status == "tombstone", (
        f"Expected PF-{wi_id} to be tombstoned after equilibrium, got {pf_rec.status!r}"
    )


# ---------------------------------------------------------------------------
# REQ-398 (TEST-398): wi_store mutations sync to ESDB
# ---------------------------------------------------------------------------


def test_wi_store_create_writes_work_item(tmp_project: Path) -> None:
    """WorkItemStore.create() upserts a kind='work_item' ESDB record with status=active."""
    from specsmith.esdb import SqliteStore
    from specsmith.wi_store import WorkItemStore

    store = WorkItemStore(tmp_project)
    wi = store.create(
        "WI-WITEST01",
        intent="add retry logic",
        requirement_ids=["REQ-001"],
        test_case_ids=["TEST-001"],
    )
    assert wi.id == "WI-WITEST01"

    with SqliteStore(tmp_project) as esdb:
        rec = esdb.get("WI-WITEST01")

    assert rec is not None
    assert rec.kind == "work_item"
    assert rec.status == "active"
    assert "REQ-001" in rec.source_ids
    assert "TEST-001" in rec.source_ids
    assert rec.data["status"] == "open"


def test_wi_store_mark_implemented_stays_active(tmp_project: Path) -> None:
    """mark_implemented() transitions WI to implemented — ESDB record stays active."""
    from specsmith.esdb import SqliteStore
    from specsmith.wi_store import WorkItemStore

    store = WorkItemStore(tmp_project)
    store.create("WI-WITEST02", intent="add feature")
    store.mark_implemented("WI-WITEST02")

    with SqliteStore(tmp_project) as esdb:
        rec = esdb.get("WI-WITEST02")

    assert rec is not None
    assert rec.kind == "work_item"
    assert rec.status == "active"  # implemented is not terminal → active
    assert rec.data["status"] == "implemented"
    assert rec.data["verified"] is True


def test_wi_store_close_tombstones_esdb(tmp_project: Path) -> None:
    """Closing a WI (terminal state) tombstones the ESDB work_item record."""
    from specsmith.esdb import SqliteStore
    from specsmith.wi_store import WorkItemStore

    store = WorkItemStore(tmp_project)
    store.create("WI-WITEST03", intent="fix bug")
    store.mark_implemented("WI-WITEST03")
    store.set_status("WI-WITEST03", "closed", reason="satisfied REQ-001")

    with SqliteStore(tmp_project) as esdb:
        rec = esdb.get("WI-WITEST03")

    assert rec is not None
    assert rec.kind == "work_item"
    assert rec.status == "tombstone", f"Expected tombstone for closed WI, got {rec.status!r}"
    assert rec.data["status"] == "closed"


def test_wi_store_archive_tombstones_esdb(tmp_project: Path) -> None:
    """Archiving a WI (terminal) tombstones the ESDB work_item record."""
    from specsmith.esdb import SqliteStore
    from specsmith.wi_store import WorkItemStore

    store = WorkItemStore(tmp_project)
    store.create("WI-WITEST04", intent="deferred work")
    store.set_status("WI-WITEST04", "archived", reason="deferred")

    with SqliteStore(tmp_project) as esdb:
        rec = esdb.get("WI-WITEST04")

    assert rec is not None
    assert rec.status == "tombstone"


def test_wi_store_promote_tombstones_esdb(tmp_project: Path) -> None:
    """Promoting a WI to a REQ (terminal) tombstones the ESDB work_item record."""
    from specsmith.esdb import SqliteStore
    from specsmith.wi_store import WorkItemStore

    store = WorkItemStore(tmp_project)
    store.create("WI-WITEST05", intent="new feature")
    store.mark_implemented("WI-WITEST05")
    store.promote_to_req("WI-WITEST05", "REQ-999")

    with SqliteStore(tmp_project) as esdb:
        rec = esdb.get("WI-WITEST05")

    assert rec is not None
    assert rec.status == "tombstone"
    assert rec.data["promoted_to_req"] == "REQ-999"


# ---------------------------------------------------------------------------
# REQ-399 (TEST-399): context seed session-resume integration
# ---------------------------------------------------------------------------


def test_context_seed_session_resume_includes_preflight(tmp_project: Path) -> None:
    """build_context_seed() picks up preflight_decision records written to ESDB."""
    from specsmith.agent.context_seed import build_context_seed
    from specsmith.esdb import SqliteRecord, SqliteStore

    # Seed ESDB with a high-confidence preflight_decision
    with SqliteStore(tmp_project) as store:
        store.upsert(
            SqliteRecord(
                id="WI-SESSION01",
                kind="preflight_decision",
                label="add retry logic to broker",
                confidence=0.8,
                status="active",
                data={"decision": "accepted", "work_item_id": "WI-SESSION01"},
                source_ids=["REQ-001"],
            )
        )

    seed = build_context_seed(tmp_project)

    esdb_turn = next(
        (t for t in seed if "ESDB governance context" in t.get("content", "")),
        None,
    )
    assert esdb_turn is not None, "Expected an ESDB governance context turn in the seed"
    assert "WI-SESSION01" in esdb_turn["content"]
    assert "preflight_decision" in esdb_turn["content"]


def test_context_seed_low_confidence_excluded_from_resume(tmp_project: Path) -> None:
    """Records with confidence < 0.6 are NOT included in the context seed (H18)."""
    from specsmith.agent.context_seed import build_context_seed
    from specsmith.esdb import SqliteRecord, SqliteStore

    with SqliteStore(tmp_project) as store:
        store.upsert(
            SqliteRecord(
                id="WI-LOWCONF01",
                kind="preflight_decision",
                label="stale low-confidence decision",
                confidence=0.3,  # below H18 filter threshold
                status="active",
            )
        )

    seed = build_context_seed(tmp_project)

    # Either no ESDB turn at all, or if present, the low-conf record must be absent
    for turn in seed:
        assert "WI-LOWCONF01" not in turn.get("content", ""), (
            "Low-confidence record leaked into context seed"
        )


def test_context_seed_verify_result_included_in_resume(tmp_project: Path) -> None:
    """verify_result records appear in the context seed for session resume."""
    from specsmith.agent.context_seed import build_context_seed
    from specsmith.esdb import SqliteRecord, SqliteStore

    with SqliteStore(tmp_project) as store:
        store.upsert(
            SqliteRecord(
                id="VERIFY-WI-RES001",
                kind="verify_result",
                label="All tests passed.",
                confidence=0.85,
                status="active",
                data={"equilibrium": True, "work_item_id": "WI-RES001"},
                source_ids=["WI-RES001"],
            )
        )

    seed = build_context_seed(tmp_project)

    esdb_turn = next(
        (t for t in seed if "ESDB governance context" in t.get("content", "")),
        None,
    )
    assert esdb_turn is not None
    assert "VERIFY-WI-RES001" in esdb_turn["content"]


def test_context_seed_empty_esdb_returns_no_esdb_turn(tmp_project: Path) -> None:
    """With no ESDB records, build_context_seed() returns no ESDB governance turn."""
    from specsmith.agent.context_seed import build_context_seed

    seed = build_context_seed(tmp_project)

    esdb_turn = next(
        (t for t in seed if "ESDB governance context" in t.get("content", "")),
        None,
    )
    assert esdb_turn is None, "Expected no ESDB turn when store is empty"
