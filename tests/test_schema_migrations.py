from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from specsmith.cli import main
from specsmith.sync import parse_requirements_md, parse_tests_md


def test_parsers_emit_version_field() -> None:
    reqs = parse_requirements_md("## REQ-001: hello\n- **Status**: defined\n")
    tests = parse_tests_md("## TEST-001\n- **Requirement ID**: REQ-001\n")
    assert reqs and reqs[0]["version"] == 1
    assert tests and tests[0]["version"] == 1


def test_migrate_run_check_json(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "migrate",
            "run",
            "--project-dir",
            str(tmp_path),
            "--check",
            "--json",
        ],
    )
    assert result.exit_code in (0, 1)
    payload = json.loads(result.output or "{}")
    assert "needs_migration" in payload
    assert "pending_versions" in payload


def test_migrate_run_creates_backup_dir(tmp_path: Path) -> None:
    (tmp_path / ".specsmith").mkdir()
    (tmp_path / ".specsmith" / "requirements.json").write_text("[]", encoding="utf-8")
    runner = CliRunner()
    runner.invoke(
        main,
        [
            "migrate",
            "run",
            "--project-dir",
            str(tmp_path),
            "--dry-run",
        ],
    )
    # dry-run should not force backup creation
    assert not (tmp_path / ".specsmith" / "migration-backups").exists()

    runner.invoke(
        main,
        [
            "migrate",
            "run",
            "--project-dir",
            str(tmp_path),
        ],
    )
    backup_root = tmp_path / ".specsmith" / "migration-backups"
    assert backup_root.exists()
    assert any(p.is_dir() for p in backup_root.iterdir())
