# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for the new `workflow`, `history`, and `drive` CLI subcommand groups.

These commands extend the specsmith CLI with Warp-style parameterised
workflows, persistent-session-memory search, and a user-scoped Drive for
sharing rules / workflows / notebooks / mcp configs across machines.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from specsmith.cli import main

# ---------------------------------------------------------------------------
# workflow group
# ---------------------------------------------------------------------------


def test_workflow_record_writes_yaml(tmp_path: Path) -> None:
    runner = CliRunner()
    res = runner.invoke(
        main,
        [
            "workflow",
            "record",
            "fix-issue",
            "--command",
            "echo issue {{ id }} for {{ component }}",
            "--description",
            "Quick issue triage",
            "--param",
            "id",
            "--param",
            "component",
            "--project-dir",
            str(tmp_path),
        ],
    )
    assert res.exit_code == 0, res.output
    target = tmp_path / ".specsmith" / "workflows" / "fix-issue.yml"
    assert target.is_file()
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert data["name"] == "fix-issue"
    assert data["params"] == ["id", "component"]


def test_workflow_list_emits_json(tmp_path: Path) -> None:
    runner = CliRunner()
    runner.invoke(
        main,
        [
            "workflow",
            "record",
            "audit-fix",
            "--command",
            "specsmith audit --fix",
            "--project-dir",
            str(tmp_path),
        ],
    )
    res = runner.invoke(
        main,
        ["workflow", "list", "--json", "--project-dir", str(tmp_path)],
    )
    assert res.exit_code == 0
    items = json.loads(res.output)
    names = [item["name"] for item in items]
    assert "audit-fix" in names


def test_workflow_run_dry_run_substitutes_params(tmp_path: Path) -> None:
    runner = CliRunner()
    runner.invoke(
        main,
        [
            "workflow",
            "record",
            "say",
            "--command",
            "echo hello {{ name }}",
            "--param",
            "name",
            "--project-dir",
            str(tmp_path),
        ],
    )
    res = runner.invoke(
        main,
        [
            "workflow",
            "run",
            "say",
            "--param",
            "name=world",
            "--dry-run",
            "--project-dir",
            str(tmp_path),
        ],
    )
    assert res.exit_code == 0
    assert "echo hello world" in res.output


def test_workflow_run_missing_param_exits_2(tmp_path: Path) -> None:
    runner = CliRunner()
    runner.invoke(
        main,
        [
            "workflow",
            "record",
            "needsparam",
            "--command",
            "echo {{ x }}",
            "--param",
            "x",
            "--project-dir",
            str(tmp_path),
        ],
    )
    res = runner.invoke(
        main,
        ["workflow", "run", "needsparam", "--dry-run", "--project-dir", str(tmp_path)],
    )
    assert res.exit_code == 2
    assert "Missing required params" in res.output


# ---------------------------------------------------------------------------
# history group
# ---------------------------------------------------------------------------


def _seed_session(root: Path, session_id: str, turns: list[dict]) -> None:
    session_dir = root / ".specsmith" / "sessions" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    with (session_dir / "turns.jsonl").open("w", encoding="utf-8") as fh:
        for turn in turns:
            fh.write(json.dumps(turn) + "\n")


def test_history_list_returns_sessions(tmp_path: Path) -> None:
    _seed_session(tmp_path, "alpha", [{"role": "user", "text": "hello"}])
    _seed_session(
        tmp_path, "beta", [{"role": "user", "text": "hi"}, {"role": "agent", "text": "hello"}]
    )
    runner = CliRunner()
    res = runner.invoke(
        main,
        ["history", "list", "--json", "--project-dir", str(tmp_path)],
    )
    assert res.exit_code == 0
    payload = json.loads(res.output)
    sessions = {item["session_id"]: item["turns"] for item in payload}
    assert sessions == {"alpha": 1, "beta": 2}


def test_history_search_finds_substring(tmp_path: Path) -> None:
    _seed_session(
        tmp_path,
        "alpha",
        [
            {"role": "user", "text": "fix the cleanup regression"},
            {"role": "agent", "text": "all clean"},
        ],
    )
    runner = CliRunner()
    res = runner.invoke(
        main,
        [
            "history",
            "search",
            "regression",
            "--json",
            "--project-dir",
            str(tmp_path),
        ],
    )
    assert res.exit_code == 0
    matches = json.loads(res.output)
    assert len(matches) == 1
    assert matches[0]["session_id"] == "alpha"


# ---------------------------------------------------------------------------
# drive group
# ---------------------------------------------------------------------------


@pytest.fixture
def drive_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect ~/.specsmith/drive/ to a tmp directory for the test."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    return home


def test_drive_push_and_list_workflows(tmp_path: Path, drive_home: Path) -> None:
    project = tmp_path / "project"
    (project / ".specsmith" / "workflows").mkdir(parents=True)
    (project / ".specsmith" / "workflows" / "deploy.yml").write_text(
        "name: deploy\n", encoding="utf-8"
    )
    runner = CliRunner()
    push = runner.invoke(
        main,
        ["drive", "push", "workflows", "--project-dir", str(project)],
    )
    assert push.exit_code == 0
    assert "Pushed 1 file" in push.output

    listing = runner.invoke(main, ["drive", "list", "--json"])
    assert listing.exit_code == 0
    payload = json.loads(listing.output)
    assert payload.get("workflows") == ["deploy.yml"]


def test_drive_pull_skips_existing_without_force(tmp_path: Path, drive_home: Path) -> None:
    # Seed the drive with a notebook
    (drive_home / ".specsmith" / "drive" / "notebooks").mkdir(parents=True)
    (drive_home / ".specsmith" / "drive" / "notebooks" / "smoke.md").write_text(
        "# from drive\n", encoding="utf-8"
    )

    project = tmp_path / "project"
    (project / "docs" / "notebooks").mkdir(parents=True)
    (project / "docs" / "notebooks" / "smoke.md").write_text("# already exists\n", encoding="utf-8")

    runner = CliRunner()
    res = runner.invoke(
        main,
        ["drive", "pull", "notebooks", "--project-dir", str(project)],
    )
    assert res.exit_code == 0
    assert "skipped 1" in res.output
    # Existing project file is preserved
    assert (project / "docs" / "notebooks" / "smoke.md").read_text() == "# already exists\n"

    forced = runner.invoke(
        main,
        ["drive", "pull", "notebooks", "--force", "--project-dir", str(project)],
    )
    assert forced.exit_code == 0
    assert "Pulled 1 file" in forced.output
    assert (project / "docs" / "notebooks" / "smoke.md").read_text() == "# from drive\n"


def test_drive_pull_single_file_kind_mcp(tmp_path: Path, drive_home: Path) -> None:
    drive_mcp = drive_home / ".specsmith" / "drive" / "mcp"
    drive_mcp.mkdir(parents=True)
    (drive_mcp / "mcp.yml").write_text("servers: []\n", encoding="utf-8")

    project = tmp_path / "project"
    project.mkdir()
    runner = CliRunner()
    res = runner.invoke(main, ["drive", "pull", "mcp", "--project-dir", str(project)])
    assert res.exit_code == 0
    assert (project / ".specsmith" / "mcp.yml").is_file()
    assert (project / ".specsmith" / "mcp.yml").read_text(encoding="utf-8") == "servers: []\n"


# ---------------------------------------------------------------------------
# Helpers — make the tests insulated from the auto-update PyPI probe.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _no_auto_update(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPECSMITH_NO_AUTO_UPDATE", "1")
    monkeypatch.setenv("SPECSMITH_PYPI_CHECKED", "1")
    yield
    for var in ("SPECSMITH_NO_AUTO_UPDATE", "SPECSMITH_PYPI_CHECKED"):
        os.environ.pop(var, None)
