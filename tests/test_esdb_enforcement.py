# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Regression tests for ESDB fallback and legacy policy enforcement."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from specsmith.cli import main
from specsmith.esdb.sqlite_store import SqliteRecord, SqliteStore
from specsmith.sync import _should_auto_migrate, auto_migrate_if_needed, run_sync


def _run(args: list[str]):  # type: ignore[return]  # noqa: ANN201
    runner = CliRunner()
    return runner.invoke(
        main,
        args,
        env={
            "SPECSMITH_NO_AUTO_UPDATE": "1",
            "SPECSMITH_PYPI_CHECKED": "1",
            "SPECSMITH_ALLOW_NON_PIPX": "1",
        },
    )


def test_run_sync_normalizes_legacy_esdb_gitignore(tmp_path: Path) -> None:
    """Legacy broad ignores are removed and canonical ESDB policy is injected."""
    (tmp_path / ".gitignore").write_text(
        "\n".join(
            [
                ".specsmith/",
                ".chronomemory/",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    run_sync(tmp_path)

    lines = {
        line.strip()
        for line in (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    assert ".specsmith/" not in lines
    assert ".chronomemory/" not in lines
    assert ".chronomemory/backup/" in lines
    assert ".specsmith/workitems.json" in lines
    assert "!.specsmith/esdb.sqlite3" in lines
    assert "!.chronomemory/events.wal" in lines
    assert "!.chronomemory/snapshot.json" in lines


def test_save_uses_sqlite_store_backup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """specsmith save should create a SQLite backup when ChronoStore is unavailable."""
    monkeypatch.setenv("SPECSMITH_ESDB_BACKEND", "sqlite")
    with SqliteStore(tmp_path) as store:
        store.upsert(
            SqliteRecord(
                id="REQ-001",
                kind="requirement",
                label="SQLite fallback requirement",
            )
        )

    result = _run(["save", "--project-dir", str(tmp_path), "--no-push", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    backup_step = next(step for step in payload["steps"] if step["step"] == "esdb_backup")
    assert backup_step["ok"] is True
    assert backup_step["backend"] == "sqlite"

    backup_path = Path(backup_step["path"])
    assert backup_path.is_file()
    assert backup_path.suffix == ".sqlite3"


def test_should_auto_migrate_true_when_store_empty(tmp_path: Path) -> None:
    state = tmp_path / ".specsmith"
    state.mkdir()
    (state / "requirements.json").write_text(
        json.dumps([{"id": "REQ-001", "title": "R"}]), encoding="utf-8"
    )
    (state / "testcases.json").write_text("[]", encoding="utf-8")

    with SqliteStore(tmp_path) as store:
        assert _should_auto_migrate(store, state) is True


def test_should_auto_migrate_false_when_store_non_empty(tmp_path: Path) -> None:
    state = tmp_path / ".specsmith"
    state.mkdir()
    (state / "requirements.json").write_text(
        json.dumps([{"id": "REQ-001", "title": "R"}]), encoding="utf-8"
    )
    (state / "testcases.json").write_text("[]", encoding="utf-8")

    with SqliteStore(tmp_path) as store:
        store.upsert(SqliteRecord(id="REQ-000", kind="requirement", label="already-there"))
        assert _should_auto_migrate(store, state) is False


def test_auto_migrate_if_needed_populates_sqlite_from_legacy_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SPECSMITH_ESDB_BACKEND", "sqlite")
    state = tmp_path / ".specsmith"
    state.mkdir()
    (state / "requirements.json").write_text(
        json.dumps([{"id": "REQ-101", "title": "Auto migrated req"}]), encoding="utf-8"
    )
    (state / "testcases.json").write_text(
        json.dumps(
            [{"id": "TEST-101", "title": "Auto migrated test", "requirement_id": "REQ-101"}]
        ),
        encoding="utf-8",
    )

    counts = auto_migrate_if_needed(tmp_path)
    assert counts.get("requirements") == 1
    assert counts.get("testcases") == 1

    with SqliteStore(tmp_path) as store:
        assert store.record_count() >= 2
