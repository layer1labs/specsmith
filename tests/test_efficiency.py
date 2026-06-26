# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for specsmith.efficiency — EFF-CURRENT + epistemic quality (REQ-411, REQ-414)."""

from __future__ import annotations

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


def _insert_session_metric(
    root: Path,
    *,
    session_id: str,
    tokens_total: int = 1000,
    passed: bool = True,
    timestamp: str | None = None,
) -> None:
    from specsmith.esdb import SqliteRecord, SqliteStore

    ts = timestamp or datetime.now(timezone.utc).isoformat()
    with SqliteStore(root) as store:
        store.upsert(
            SqliteRecord(
                id=f"MET-{session_id}",
                kind="session_metric",
                status="active",
                label=f"{session_id}: tokens={tokens_total}",
                confidence=0.8,
                data={
                    "session_id": session_id,
                    "tokens_total": tokens_total,
                    "cost_usd": 0.001,
                    "quality_score": 0.9 if passed else 0.3,
                    "passed": passed,
                    "rework_turns": 1,
                    "timestamp": ts,
                },
            )
        )


# ---------------------------------------------------------------------------
# compute_epistemic_quality
# ---------------------------------------------------------------------------


def test_epistemic_quality_no_esdb_returns_zeros(tmp_path: Path) -> None:
    """Returns all-zeros when ESDB doesn't exist."""
    from specsmith.efficiency import compute_epistemic_quality

    result = compute_epistemic_quality(tmp_path)
    assert result["score"] == 0.0
    assert result["confidence_density"] == 0.0


def test_epistemic_quality_empty_esdb_returns_zeros(tmp_project: Path) -> None:
    """Returns all-zeros when ESDB is empty (no active records)."""
    from specsmith.efficiency import compute_epistemic_quality
    from specsmith.esdb import SqliteStore

    with SqliteStore(tmp_project):
        pass  # create DB schema but no records

    result = compute_epistemic_quality(tmp_project)
    assert result["score"] == 0.0


def test_epistemic_quality_confidence_density(tmp_project: Path) -> None:
    """confidence_density == fraction of records with confidence >= 0.7."""
    from specsmith.efficiency import compute_epistemic_quality
    from specsmith.esdb import SqliteRecord, SqliteStore

    with SqliteStore(tmp_project) as store:
        for i, conf in enumerate([0.9, 0.8, 0.7, 0.5, 0.4]):
            store.upsert(
                SqliteRecord(
                    id=f"REC-{i:03d}",
                    kind="fact",
                    status="active",
                    label=f"record {i}",
                    confidence=conf,
                    data={},
                )
            )

    result = compute_epistemic_quality(tmp_project)
    # 3 records (0.9, 0.8, 0.7) have confidence >= 0.7 out of 5
    assert result["confidence_density"] == pytest.approx(0.6)
    assert 0.0 <= result["score"] <= 1.0


def test_epistemic_quality_all_dims_present(tmp_project: Path) -> None:
    """Result dict contains all 6 expected keys."""
    from specsmith.efficiency import compute_epistemic_quality
    from specsmith.esdb import SqliteRecord, SqliteStore

    with SqliteStore(tmp_project) as store:
        store.upsert(
            SqliteRecord(
                id="REC-001",
                kind="fact",
                status="active",
                label="some fact",
                confidence=0.8,
                data={"timestamp": datetime.now(timezone.utc).isoformat()},
            )
        )

    result = compute_epistemic_quality(tmp_project)
    assert set(result.keys()) == {
        "score",
        "confidence_density",
        "recency_score",
        "coherence_score",
        "closure_score",
        "non_contradiction_score",
    }


# ---------------------------------------------------------------------------
# compute_and_upsert_efficiency
# ---------------------------------------------------------------------------


def test_compute_and_upsert_efficiency_no_esdb_returns_false(tmp_path: Path) -> None:
    """Returns False gracefully when esdb.sqlite3 doesn't exist."""
    from specsmith.efficiency import compute_and_upsert_efficiency

    (tmp_path / ".specsmith").mkdir()
    result = compute_and_upsert_efficiency(tmp_path)
    assert result is False


def test_compute_and_upsert_efficiency_creates_eff_current(tmp_project: Path) -> None:
    """Creates an EFF-CURRENT record in ESDB (REQ-411)."""
    from specsmith.efficiency import compute_and_upsert_efficiency
    from specsmith.esdb import SqliteStore

    # Need at least an ESDB to exist
    with SqliteStore(tmp_project):
        pass  # create schema

    _insert_session_metric(tmp_project, session_id="S-001", tokens_total=2000, passed=True)
    _insert_session_metric(tmp_project, session_id="S-002", tokens_total=1500, passed=True)
    _insert_session_metric(tmp_project, session_id="S-003", tokens_total=900, passed=False)

    result = compute_and_upsert_efficiency(tmp_project)
    assert result is True

    with SqliteStore(tmp_project) as store:
        rec = store.get("EFF-CURRENT")

    assert rec is not None
    assert rec.kind == "efficiency_metric"
    assert rec.confidence == pytest.approx(1.0)
    assert rec.data["sessions_analyzed"] == 3
    eq = rec.data["epistemic_quality"]
    assert isinstance(eq, dict)
    assert 0.0 <= eq["score"] <= 1.0


def test_compute_and_upsert_efficiency_idempotent(tmp_project: Path) -> None:
    """Calling twice doesn't create duplicate EFF-CURRENT records."""
    from specsmith.efficiency import compute_and_upsert_efficiency
    from specsmith.esdb import SqliteStore

    with SqliteStore(tmp_project):
        pass

    _insert_session_metric(tmp_project, session_id="S-001", passed=True)
    compute_and_upsert_efficiency(tmp_project)
    compute_and_upsert_efficiency(tmp_project)

    with SqliteStore(tmp_project) as store:
        eff_records = store.query(kind="efficiency_metric", status="active")
    assert len(eff_records) == 1, "Should only have one EFF-CURRENT record"


def test_compute_and_upsert_efficiency_degraded_flag(tmp_project: Path) -> None:
    """Sets degraded=True when tokens_per_correct_answer > 2x baseline."""
    from specsmith.efficiency import compute_and_upsert_efficiency
    from specsmith.esdb import SqliteRecord, SqliteStore

    with SqliteStore(tmp_project) as store:
        # 50 passing sessions with low token count (baseline)
        for i in range(50):
            ts_old = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
            store.upsert(
                SqliteRecord(
                    id=f"MET-OLD-{i:03d}",
                    kind="session_metric",
                    status="active",
                    label=f"old-{i}",
                    confidence=0.8,
                    data={
                        "session_id": f"S-OLD-{i}",
                        "tokens_total": 500,  # baseline 500
                        "passed": True,
                        "rework_turns": 1,
                        "timestamp": ts_old,
                    },
                )
            )
        # 20 recent passing sessions with very high token count
        for i in range(20):
            ts_recent = datetime.now(timezone.utc).isoformat()
            store.upsert(
                SqliteRecord(
                    id=f"MET-NEW-{i:03d}",
                    kind="session_metric",
                    status="active",
                    label=f"new-{i}",
                    confidence=0.8,
                    data={
                        "session_id": f"S-NEW-{i}",
                        "tokens_total": 5000,  # 10x baseline → degraded
                        "passed": True,
                        "rework_turns": 1,
                        "timestamp": ts_recent,
                    },
                )
            )

    result = compute_and_upsert_efficiency(tmp_project)
    assert result is True

    with SqliteStore(tmp_project) as store:
        rec = store.get("EFF-CURRENT")

    assert rec is not None
    # tokens_per_correct_answer (mean of recent 20 passing) = 5000
    # baseline (mean of all 50 passing) ≈ 500
    # 5000 > 2 * 500 → degraded
    assert rec.data["degraded"] is True
