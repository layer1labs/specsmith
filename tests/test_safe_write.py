# SPDX-License-Identifier: MIT
"""Regression coverage for deterministic managed governance writes."""

from pathlib import Path

from specsmith.safe_write import safe_overwrite


def test_identical_safe_overwrite_is_a_no_op(tmp_path: Path) -> None:
    path = tmp_path / "RULES.md"
    path.write_text("stable\n", encoding="utf-8")
    before = path.stat().st_mtime_ns

    backup = safe_overwrite(path, "stable\n", backup_dir=tmp_path / "backups")

    assert backup is None
    assert path.stat().st_mtime_ns == before
    assert not (tmp_path / "backups").exists()


def test_changed_managed_write_uses_project_local_backup_directory(tmp_path: Path) -> None:
    path = tmp_path / "docs" / "governance" / "RULES.md"
    path.parent.mkdir(parents=True)
    path.write_text("old\n", encoding="utf-8")
    backup_dir = tmp_path / ".specsmith" / "backups" / "governance"

    backup = safe_overwrite(path, "new\n", backup_dir=backup_dir)

    assert backup is not None
    assert backup.parent == backup_dir
    assert backup.read_text(encoding="utf-8") == "old\n"
    assert path.read_text(encoding="utf-8") == "new\n"
