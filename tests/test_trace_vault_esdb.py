# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""TEST-430 — ESDB-only trace vault (REQ-420).

The trace vault no longer writes or reads a ``.specsmith/trace.jsonl`` flat
file. Seals are persisted exclusively as ESDB ``seal_record`` entries, and the
SHA-256 hash chain must reconstruct correctly from ESDB alone.

The free SQLite backend is forced for determinism so these tests behave
identically regardless of whether the commercial ChronoStore is installed.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def sqlite_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPECSMITH_ESDB_BACKEND", "sqlite")


def test_seal_does_not_create_trace_jsonl(tmp_path: Path, sqlite_backend: None) -> None:
    """Sealing must NOT create the legacy .specsmith/trace.jsonl flat file (REQ-420)."""
    from specsmith.trace import SealType, TraceVault

    vault = TraceVault(tmp_path)
    vault.seal(SealType.DECISION, "Adopted ESDB-only trace vault")
    vault.seal(SealType.AUDIT_GATE, "Audit gate passed")

    assert not (tmp_path / ".specsmith" / "trace.jsonl").exists()


def test_seals_persist_as_esdb_seal_records(tmp_path: Path, sqlite_backend: None) -> None:
    """Each seal is stored as an active ESDB seal_record entry (REQ-420)."""
    from specsmith.esdb import SqliteStore
    from specsmith.trace import SealType, TraceVault

    vault = TraceVault(tmp_path)
    vault.seal(SealType.DECISION, "First")
    vault.seal(SealType.MILESTONE, "Second")

    with SqliteStore(tmp_path) as store:
        records = store.query(kind="seal_record", status="active")

    assert len(records) == 2
    # The full SealRecord payload is preserved verbatim in record.data.
    assert all("content_hash" in r.data and "prev_hash" in r.data for r in records)


def test_chain_reconstructs_from_esdb_in_fresh_instance(
    tmp_path: Path, sqlite_backend: None
) -> None:
    """A brand-new TraceVault reconstructs a valid chain purely from ESDB (REQ-420)."""
    from specsmith.trace import SealType, TraceVault

    writer = TraceVault(tmp_path)
    writer.seal(SealType.DECISION, "alpha")
    writer.seal(SealType.MILESTONE, "beta")
    writer.seal(SealType.AUDIT_GATE, "gamma")

    # Fresh instance shares no in-memory state — it must read ESDB only.
    reader = TraceVault(tmp_path)
    assert reader.count() == 3

    valid, errors = reader.verify()
    assert valid, f"Chain reconstructed from ESDB must verify; errors: {errors}"

    # Order is preserved (genesis chain link first, then sequential).
    seals = reader.list_seals(limit=10)
    descriptions = [s.description for s in reversed(seals)]
    assert descriptions == ["alpha", "beta", "gamma"]


def test_empty_vault_reports_zero_without_creating_store(
    tmp_path: Path, sqlite_backend: None
) -> None:
    """An unsealed project reports 0 seals and does not create an ESDB store (REQ-420)."""
    from specsmith.trace import TraceVault, count_seal_records

    vault = TraceVault(tmp_path)
    assert vault.count() == 0
    assert count_seal_records(tmp_path) == 0
    # Read-only checks must not materialise an empty store on disk.
    assert not (tmp_path / ".specsmith" / "esdb.sqlite3").exists()
