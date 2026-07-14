# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Regression coverage for legacy ChronoMemory WAL migration repair."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from specsmith.cli import main


class _LegacyChronoStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.compacted = False
        self.backup_called = False
        self.migrated = False

    def __enter__(self) -> _LegacyChronoStore:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def chain_valid(self) -> bool:
        return self.compacted

    def backup(self) -> Path:
        self.backup_called = True
        return self.root / ".chronomemory" / "backup" / "legacy-wal"

    def compact(self) -> None:
        self.compacted = True

    def migrate_from_json(self, _state_dir: Path) -> dict[str, int]:
        self.migrated = True
        return {"requirements": 0, "testcases": 0, "skipped": 0}


def test_esdb_migrate_repairs_invalid_legacy_chronomemory_wal(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """TEST-478: invalid legacy chains are backed up, compacted, and recorded."""
    state_dir = tmp_path / ".specsmith"
    state_dir.mkdir()
    (state_dir / "requirements.json").write_text("[]", encoding="utf-8")
    (state_dir / "testcases.json").write_text("[]", encoding="utf-8")
    store = _LegacyChronoStore(tmp_path)

    monkeypatch.setattr("specsmith.esdb.open_default_store", lambda *_args, **_kwargs: store)
    monkeypatch.setattr("specsmith.esdb.ESDB_BACKEND", "chronomemory")

    result = CliRunner().invoke(
        main,
        ["esdb", "migrate", "--project-dir", str(tmp_path), "--json"],
        env={"SPECSMITH_NO_AUTO_UPDATE": "1"},
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["wal_repair"] == {
        "attempted": True,
        "detected_invalid": True,
        "method": "backup_then_compact",
        "backup_path": str(tmp_path / ".chronomemory" / "backup" / "legacy-wal"),
        "chain_valid_after": True,
        "ok": True,
    }
    assert store.backup_called
    assert store.compacted
    assert store.migrated
    manifest = json.loads((state_dir / "esdb_migration_manifest.json").read_text(encoding="utf-8"))
    assert manifest["wal_repair"] == payload["wal_repair"]
