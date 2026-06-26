# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""TEST-432 — SQLite <-> ChronoMemory parity (REQ-422).

The free SQLite ESDB backend must provide the same governance-knowledge surface
as the commercial ChronoStore for two paths that previously only worked when a
``.chronomemory`` WAL existed:

  1. ``retrieval.build_index`` — high-confidence governance records are injected
     into the RAG index; infrastructure kinds are excluded (critical rule §18).
  2. ``ContextOrchestrator._count_critical_records`` — active records with
     confidence >= CRITICAL_CONFIDENCE are counted for Tier-3 protection.

The tests force the SQLite backend and use a fresh project dir (no
``.chronomemory``) so the SQLite parity branches are exercised deterministically.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture()
def sqlite_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPECSMITH_ESDB_BACKEND", "sqlite")


def _seed(root: Path) -> None:
    from specsmith.esdb import SqliteRecord, SqliteStore

    with SqliteStore(root) as store:
        store.upsert(
            SqliteRecord(
                id="REQ-001",
                kind="requirement",
                label="Login flow",
                confidence=0.9,
                data={"description": "users can log in"},
            )
        )
        # Low-confidence record: filtered out by the RAG confidence threshold.
        store.upsert(
            SqliteRecord(
                id="REQ-LOW",
                kind="requirement",
                label="Low confidence",
                confidence=0.3,
                data={"description": "speculative"},
            )
        )
        # Infrastructure record: excluded from the RAG index by kind.
        store.upsert(
            SqliteRecord(
                id="TOK-1",
                kind="token_metric",
                label="tokens",
                confidence=1.0,
                data={"input_tokens": 10},
            )
        )


def test_build_index_injects_governance_records_on_sqlite(
    tmp_path: Path, sqlite_backend: None
) -> None:
    """build_index injects high-confidence governance records from SQLite (REQ-422)."""
    from specsmith.retrieval import build_index

    _seed(tmp_path)
    build_index(tmp_path)

    index = json.loads(
        (tmp_path / ".specsmith" / "retrieval-index.json").read_text(encoding="utf-8")
    )
    paths = [e["path"] for e in index["entries"]]

    assert any("esdb/requirement/REQ-001" in p for p in paths), (
        "High-confidence governance record must be injected into the RAG index"
    )


def test_build_index_excludes_infra_and_low_confidence_on_sqlite(
    tmp_path: Path, sqlite_backend: None
) -> None:
    """Infrastructure kinds and low-confidence records are excluded (REQ-422, rule §18)."""
    from specsmith.retrieval import build_index

    _seed(tmp_path)
    build_index(tmp_path)

    index = json.loads(
        (tmp_path / ".specsmith" / "retrieval-index.json").read_text(encoding="utf-8")
    )
    paths = [e["path"] for e in index["entries"]]

    assert not any("token_metric" in p for p in paths), "Infra kinds must be excluded"
    assert not any("REQ-LOW" in p for p in paths), "Low-confidence records must be filtered"


def test_count_critical_records_sqlite_fallback(tmp_path: Path, sqlite_backend: None) -> None:
    """_count_critical_records counts active high-confidence records via SQLite (REQ-422)."""
    from specsmith.context_orchestrator import ContextOrchestrator
    from specsmith.esdb import SqliteRecord, SqliteStore

    with SqliteStore(tmp_path) as store:
        store.upsert(SqliteRecord(id="A", kind="fact", confidence=0.9, data={}))
        store.upsert(SqliteRecord(id="B", kind="fact", confidence=0.5, data={}))
        store.upsert(SqliteRecord(id="C", kind="requirement", confidence=0.8, data={}))

    orch = ContextOrchestrator(tmp_path)
    # A (0.9) and C (0.8) are >= CRITICAL_CONFIDENCE (0.7); B (0.5) is not.
    assert orch._count_critical_records() == 2


def test_count_critical_records_zero_without_store(tmp_path: Path, sqlite_backend: None) -> None:
    """No ESDB store => zero critical records, no store created (REQ-422)."""
    from specsmith.context_orchestrator import ContextOrchestrator

    orch = ContextOrchestrator(tmp_path)
    assert orch._count_critical_records() == 0
    assert not (tmp_path / ".specsmith" / "esdb.sqlite3").exists()
