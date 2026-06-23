from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from specsmith.cli import main
from specsmith.esdb.sqlite_store import SqliteStore


def test_esdb_verify_chain_json(tmp_path: Path) -> None:
    with SqliteStore(tmp_path) as store:
        store.append_audit_event(payload={"action": "seed"}, command_source="test")
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["esdb", "verify-chain", "--project-dir", str(tmp_path), "--json"],
    )
    assert result.exit_code == 0
    assert '"ok"' in result.output
    assert '"event_count"' in result.output


def test_esdb_verify_chain_detects_tamper(tmp_path: Path) -> None:
    with SqliteStore(tmp_path) as store:
        store.append_audit_event(payload={"action": "seed"}, command_source="test")
    db = tmp_path / ".specsmith" / "esdb.sqlite3"
    import sqlite3

    with sqlite3.connect(str(db)) as conn:
        conn.execute("UPDATE audit_events SET payload_hash='tampered' WHERE rowid=1")
        conn.commit()
    runner = CliRunner()
    result = runner.invoke(main, ["esdb", "verify-chain", "--project-dir", str(tmp_path)])
    assert result.exit_code == 1
