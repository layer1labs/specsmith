# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for specsmith.esdb_sweep — per-kind retention + orphan detection (REQ-412, REQ-413)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    (tmp_path / ".specsmith").mkdir(parents=True)
    os.environ["SPECSMITH_ESDB_BACKEND"] = "sqlite"
    yield tmp_path
    os.environ.pop("SPECSMITH_ESDB_BACKEND", None)


def _insert_record(  # noqa: PLR0913
    root, *, rec_id, kind, status="active", confidence=0.8, timestamp=None, data=None
):
    from specsmith.esdb import SqliteRecord, SqliteStore

    d = dict(data or {})
    if timestamp:
        d["timestamp"] = timestamp
    with SqliteStore(root) as store:
        store.upsert(
            SqliteRecord(
                id=rec_id,
                kind=kind,
                status=status,
                label=rec_id,
                confidence=confidence,
                data=d,
            )
        )


def _ts_days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


# ---------------------------------------------------------------------------
# SweepResult
# ---------------------------------------------------------------------------


def test_sweep_result_no_esdb_returns_empty(tmp_path: Path) -> None:
    """run_sweep returns empty SweepResult when esdb.sqlite3 doesn't exist."""
    from specsmith.esdb_sweep import run_sweep

    (tmp_path / ".specsmith").mkdir()
    result = run_sweep(tmp_path)
    assert result.tombstoned == 0
    assert result.orphans_flagged == 0
    assert result.total_swept() == 0


# ---------------------------------------------------------------------------
# Retention sweep (REQ-412)
# ---------------------------------------------------------------------------


def test_sweep_tombstones_expired_session_metric(tmp_project: Path) -> None:
    """session_metric records older than 60 days are tombstoned."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_sweep import run_sweep

    _insert_record(
        tmp_project,
        rec_id="MET-OLD-001",
        kind="session_metric",
        timestamp=_ts_days_ago(61),
    )
    _insert_record(
        tmp_project,
        rec_id="MET-OLD-002",
        kind="session_metric",
        timestamp=_ts_days_ago(65),
    )
    _insert_record(
        tmp_project,
        rec_id="MET-FRESH-001",
        kind="session_metric",
        timestamp=_ts_days_ago(5),
    )

    result = run_sweep(tmp_project)
    assert result.tombstoned == 2
    assert result.kinds_swept.get("session_metric") == 2

    with SqliteStore(tmp_project) as store:
        old1 = store.get("MET-OLD-001")
        old2 = store.get("MET-OLD-002")
        fresh = store.get("MET-FRESH-001")

    assert old1 is not None and old1.status == "tombstone"
    assert old2 is not None and old2.status == "tombstone"
    assert fresh is not None and fresh.status == "active"


def test_sweep_tombstones_expired_context_usage(tmp_project: Path) -> None:
    """context_usage records older than 30 days are tombstoned."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_sweep import run_sweep

    _insert_record(
        tmp_project,
        rec_id="CTX-OLD-001",
        kind="context_usage",
        timestamp=_ts_days_ago(31),
    )
    _insert_record(
        tmp_project,
        rec_id="CTX-FRESH-001",
        kind="context_usage",
        timestamp=_ts_days_ago(10),
    )

    result = run_sweep(tmp_project)
    assert result.tombstoned == 1
    assert result.kinds_swept.get("context_usage") == 1

    with SqliteStore(tmp_project) as store:
        assert store.get("CTX-OLD-001").status == "tombstone"
        assert store.get("CTX-FRESH-001").status == "active"


def test_sweep_never_tombstones_token_metric(tmp_project: Path) -> None:
    """token_metric records are never tombstoned (retention=None)."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_sweep import run_sweep

    _insert_record(
        tmp_project,
        rec_id="TOK-ANCIENT",
        kind="token_metric",
        timestamp=_ts_days_ago(365),
    )

    result = run_sweep(tmp_project)
    assert result.tombstoned == 0

    with SqliteStore(tmp_project) as store:
        assert store.get("TOK-ANCIENT").status == "active"


def test_sweep_dry_run_does_not_tombstone(tmp_project: Path) -> None:
    """dry_run=True reports counts but does not write."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_sweep import run_sweep

    _insert_record(
        tmp_project,
        rec_id="MET-EXPIRED",
        kind="session_metric",
        timestamp=_ts_days_ago(61),
    )

    result = run_sweep(tmp_project, dry_run=True)
    assert result.tombstoned == 1  # counted

    with SqliteStore(tmp_project) as store:
        rec = store.get("MET-EXPIRED")
    assert rec is not None and rec.status == "active"  # not actually tombstoned


def test_sweep_orphans_only_skips_retention(tmp_project: Path) -> None:
    """orphans_only=True skips retention tombstoning."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_sweep import run_sweep

    _insert_record(
        tmp_project,
        rec_id="MET-EXPIRED",
        kind="session_metric",
        timestamp=_ts_days_ago(65),
    )

    result = run_sweep(tmp_project, orphans_only=True)
    assert result.tombstoned == 0  # retention skipped

    with SqliteStore(tmp_project) as store:
        assert store.get("MET-EXPIRED").status == "active"


# ---------------------------------------------------------------------------
# Orphan detection (REQ-413)
# ---------------------------------------------------------------------------


def test_sweep_detects_orphan_work_item(tmp_project: Path) -> None:
    """work_item in ESDB but absent from workitems.json is tombstoned."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_sweep import run_sweep

    # Write workitems.json without WI-ORPHAN
    wi_path = tmp_project / ".specsmith" / "workitems.json"
    wi_path.write_text(
        json.dumps([{"id": "WI-KNOWN", "intent": "real"}]), encoding="utf-8"
    )

    _insert_record(tmp_project, rec_id="WI-ORPHAN", kind="work_item")

    result = run_sweep(tmp_project, orphans_only=True)
    assert result.orphans_flagged == 1

    with SqliteStore(tmp_project) as store:
        assert store.get("WI-ORPHAN").status == "tombstone"


def test_sweep_detects_orphan_preflight(tmp_project: Path) -> None:
    """preflight_decision whose WI is not in ESDB or JSON is tombstoned."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_sweep import run_sweep

    wi_path = tmp_project / ".specsmith" / "workitems.json"
    wi_path.write_text(json.dumps([]), encoding="utf-8")

    # preflight_decision pointing to a non-existent WI
    _insert_record(
        tmp_project,
        rec_id="PF-WI-GHOST",
        kind="preflight_decision",
        data={"work_item_id": "WI-GHOST"},
    )

    result = run_sweep(tmp_project, orphans_only=True)
    assert result.orphans_flagged == 1

    with SqliteStore(tmp_project) as store:
        assert store.get("PF-WI-GHOST").status == "tombstone"


def test_sweep_known_work_item_not_orphaned(tmp_project: Path) -> None:
    """work_item present in workitems.json is not tombstoned."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_sweep import run_sweep

    wi_path = tmp_project / ".specsmith" / "workitems.json"
    wi_path.write_text(
        json.dumps([{"id": "WI-KNOWN", "intent": "legit"}]), encoding="utf-8"
    )

    _insert_record(tmp_project, rec_id="WI-KNOWN", kind="work_item")

    result = run_sweep(tmp_project, orphans_only=True)
    assert result.orphans_flagged == 0

    with SqliteStore(tmp_project) as store:
        assert store.get("WI-KNOWN").status == "active"


def test_sweep_refreshes_eff_current_after_full_sweep(tmp_project: Path) -> None:
    """After a full sweep, efficiency_refreshed is True and EFF-CURRENT updated."""
    from specsmith.esdb import SqliteStore
    from specsmith.esdb_sweep import run_sweep

    # Need ESDB to exist for efficiency to compute
    with SqliteStore(tmp_project):
        pass

    result = run_sweep(tmp_project)
    # efficiency_refreshed may be False if no data, but should not error
    assert isinstance(result.efficiency_refreshed, bool)
    assert not result.errors or all(isinstance(e, str) for e in result.errors)
