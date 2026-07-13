# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Regression tests for ESDB fallback and legacy policy enforcement."""

from __future__ import annotations

import json
import subprocess
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
    # Broad ignores must be gone
    assert ".specsmith/" not in lines
    assert ".chronomemory/" not in lines
    # Mergeable source-of-truth must be tracked; SQLite remains local runtime state.
    assert ".specsmith/esdb.sqlite3" in lines
    assert ".specsmith/esdb.sqlite3-shm" in lines
    assert ".specsmith/esdb.sqlite3-wal" in lines
    assert "!.specsmith/esdb.sqlite3" not in lines
    assert "!.specsmith/esdb_migration_manifest.json" in lines
    assert "!.chronomemory/events.wal" in lines
    assert "!.chronomemory/snapshot.json" in lines
    assert "!.chronomemory/session-events.jsonl" in lines
    # Deny-list (ephemeral runtime) must be present
    assert ".chronomemory/backup/" in lines
    assert ".specsmith/workitems.json" in lines
    assert ".specsmith/ledger-chain.txt" in lines
    assert ".specsmith/trace.jsonl" in lines
    assert ".specsmith/backups/" in lines
    assert ".specsmith/session_metrics.jsonl" in lines
    assert ".specsmith/migration-backups/" in lines
    assert ".specsmith/migration-state.json" in lines
    assert ".specsmith/agent-tools.json" in lines
    assert ".specsmith/esdb-full-coverage" in lines
    # esdb_migration_manifest must NOT appear as a bare deny rule
    assert ".specsmith/esdb_migration_manifest.json" not in lines


def test_run_sync_rewrites_stale_auto_normalized_gitignore(tmp_path: Path) -> None:
    """A stale generated allow rule must not keep the SQLite cache tracked."""
    (tmp_path / ".gitignore").write_text(
        "\n".join(
            [
                "# project rule",
                "dist/",
                "# specsmith ESDB policy (auto-normalized)",
                "# Tracked (governance source-of-truth):",
                "!.specsmith/esdb.sqlite3",
                "!.specsmith/requirements.json",
                "# Ephemeral runtime paths (never commit):",
                ".specsmith/workitems.json",
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
    assert "# project rule" in lines
    assert "dist/" in lines
    assert "!.specsmith/esdb.sqlite3" not in lines
    assert ".specsmith/esdb.sqlite3" in lines
    assert "!.chronomemory/session-events.jsonl" in lines


def test_normalizer_policy_sets_are_disjoint() -> None:
    """_GIT_TRACKED_POLICY and _GIT_IGNORED_POLICY must never overlap."""
    from specsmith.sync import _GIT_IGNORED_POLICY, _GIT_TRACKED_POLICY

    tracked = set(_GIT_TRACKED_POLICY)
    ignored = set(_GIT_IGNORED_POLICY)
    overlap = tracked & ignored
    assert not overlap, f"Paths in both allow and deny policy: {overlap}"


def test_normalizer_idempotent(tmp_path: Path) -> None:
    """Running normalize twice must not change the file on the second pass."""
    from specsmith.sync import normalize_esdb_gitignore_policy

    normalize_esdb_gitignore_policy(tmp_path)
    content_after_first = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    normalize_esdb_gitignore_policy(tmp_path)
    content_after_second = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert content_after_first == content_after_second


def test_normalizer_untrack_dry_run_returns_diverged(tmp_path: Path) -> None:
    """dry_run=True reports diverged paths without modifying git index."""
    from unittest.mock import MagicMock, patch

    from specsmith.sync import _untrack_diverged_paths

    # Simulate git ls-files returning a tracked workitems.json
    fake_result = MagicMock()
    fake_result.stdout = ".specsmith/workitems.json\n"
    with patch("subprocess.run", return_value=fake_result):
        diverged = _untrack_diverged_paths(tmp_path, dry_run=True)

    assert ".specsmith/workitems.json" in diverged


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


def test_save_does_not_commit_generated_esdb_or_migration_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Save commits canonical policy changes but never local runtime artifacts."""
    monkeypatch.setenv("SPECSMITH_ESDB_BACKEND", "sqlite")

    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    git("init")
    git("config", "user.name", "SpecSmith Test")
    git("config", "user.email", "specsmith-test@example.invalid")
    (tmp_path / "README.md").write_text("fixture\n", encoding="utf-8")
    git("add", "README.md")
    git("commit", "-m", "test: initialize fixture")

    state = tmp_path / ".specsmith"
    state.mkdir()
    generated_paths = (
        ".specsmith/agent-tools.json",
        ".specsmith/agents.md.bak",
        ".specsmith/agents.md.m005.bak",
        ".specsmith/migration-state.json",
        ".specsmith/migration-backups/fixture/state.json",
        ".specsmith/esdb-full-coverage",
        ".specsmith/esdb-m009-backfill",
        ".specsmith/esdb-m010-cleanup",
    )
    for relative_path in generated_paths:
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("generated\n", encoding="utf-8")
    with SqliteStore(tmp_path) as store:
        store.upsert(SqliteRecord(id="REQ-001", kind="requirement", label="fixture"))

    result = _run(["save", "--project-dir", str(tmp_path), "--no-push", "--json"])
    assert result.exit_code == 0, result.output

    committed = set(git("show", "--format=", "--name-only", "HEAD").splitlines())
    forbidden = {".specsmith/esdb.sqlite3", *generated_paths}
    assert committed.isdisjoint(forbidden)
    for relative_path in forbidden:
        ignored = subprocess.run(
            ["git", "check-ignore", "--quiet", "--", relative_path],
            cwd=tmp_path,
            check=False,
        )
        assert ignored.returncode == 0, relative_path


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
