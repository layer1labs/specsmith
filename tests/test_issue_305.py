# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Regression coverage for issue #305 (TEST-480)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from click.testing import CliRunner

from specsmith.cli import main


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _init_git_repo(root: Path) -> None:
    _git(root, "init")
    _git(root, "config", "user.name", "SpecSmith Test")
    _git(root, "config", "user.email", "specsmith-test@example.invalid")
    (root / ".gitignore").write_text(
        ".chronomemory/*\n!.chronomemory/events.wal\n.specsmith/*.sqlite3\n",
        encoding="utf-8",
    )
    wal = root / ".chronomemory" / "events.wal"
    wal.parent.mkdir()
    wal.write_text("", encoding="utf-8")
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    (root / ".specsmith").mkdir()
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "test: initialize fixture")


def test_save_commits_chronomemory_metric_wal_before_reporting_success(
    tmp_path: Path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """A successful save must not leave its own tracked ChronoMemory WAL dirty."""
    _init_git_repo(tmp_path)

    class _Store:
        def __enter__(self) -> _Store:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def backup(self) -> Path:
            backup = tmp_path / ".chronomemory" / "backup" / "save.wal"
            backup.parent.mkdir(exist_ok=True)
            backup.write_text("backup\n", encoding="utf-8")
            return backup

    def _append_metric(self, _record: object) -> None:  # type: ignore[no-untyped-def]
        wal = self._root / ".chronomemory" / "events.wal"
        with wal.open("a", encoding="utf-8") as stream:
            stream.write('{"kind":"session_metric","command":"save"}\n')

    monkeypatch.setattr("specsmith.esdb.ESDB_BACKEND", "chronomemory")
    monkeypatch.setattr("specsmith.esdb.open_default_store", lambda *_args, **_kwargs: _Store())
    monkeypatch.setattr("specsmith.project_metrics.MetricsStore.append", _append_metric)

    result = CliRunner().invoke(
        main, ["save", "--project-dir", str(tmp_path), "--no-push", "--json"]
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True
    assert _git(tmp_path, "status", "--short") == ""
    assert ".chronomemory/events.wal" in _git(tmp_path, "show", "--format=", "--name-only", "HEAD")
