from __future__ import annotations

import json
from pathlib import Path

from cli.main import cli
from click.testing import CliRunner


def _invoke(tmp_path: Path, payload: object, *args: str):
    source = tmp_path / "input.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    return CliRunner().invoke(cli, ["process", str(source), *args])


def test_filter_output_is_clean_json_and_empty_is_success(tmp_path: Path) -> None:
    payload = [
        {"name": "a", "status": "active"},
        {"name": "b", "status": "done"},
    ]
    matched = _invoke(tmp_path, payload, "--filter", "status=active")
    empty = _invoke(tmp_path, payload, "--filter", "status=missing")

    assert matched.exit_code == 0
    assert json.loads(matched.stdout) == [payload[0]]
    assert empty.exit_code == 0
    assert json.loads(empty.stdout) == []


def test_non_array_and_multiple_typed_filters(tmp_path: Path) -> None:
    object_payload = {"status": "active"}
    unchanged = _invoke(tmp_path, object_payload, "--filter", "status=missing")
    assert unchanged.exit_code == 0
    assert json.loads(unchanged.stdout) == object_payload

    rows = [
        {"status": "active", "priority": 2},
        {"status": "active", "priority": 1},
        {"status": "done", "priority": 2},
    ]
    filtered = _invoke(
        tmp_path,
        rows,
        "--filter",
        "status=active",
        "--filter",
        "priority=2",
    )
    assert filtered.exit_code == 0
    assert json.loads(filtered.stdout) == [rows[0]]
