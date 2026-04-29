# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Phase 3-4 completion tests: mcp loader, notebook + cloud commands.

Covers REQ-121 (MCP), REQ-123 (notebook), REQ-126 (cloud spawn), REQ-124
(perf smoke). The CLI commands are exercised through Click's CliRunner so
the tests stay fully hermetic — no real subprocess, no real PyPI hits.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from specsmith.agent.mcp import (
    MCPServerSpec,
    MCPTool,
    load_mcp_tools,
)
from specsmith.cli import main

# ── MCP loader (REQ-121 / TEST-121) ──────────────────────────────────────────


def test_load_mcp_tools_returns_empty_when_config_missing(tmp_path: Path) -> None:
    """No `.specsmith/mcp.yml` => empty list, not an error."""
    assert load_mcp_tools(tmp_path) == []


def test_load_mcp_tools_parses_one_entry(tmp_path: Path) -> None:
    cfg_dir = tmp_path / ".specsmith"
    cfg_dir.mkdir()
    (cfg_dir / "mcp.yml").write_text(
        "- name: filesystem\n"
        "  command: mcp-server-filesystem\n"
        "  args: ['--root', '.']\n"
        "  env:\n"
        "    HOME: /tmp\n",
        encoding="utf-8",
    )
    tools = load_mcp_tools(tmp_path)
    assert len(tools) == 1
    tool = tools[0]
    assert isinstance(tool, MCPTool)
    assert tool.name == "filesystem"
    assert tool.spec.command == "mcp-server-filesystem"
    assert tool.spec.args == ["--root", "."]
    assert tool.spec.env == {"HOME": "/tmp"}


def test_load_mcp_tools_skips_malformed_entries(tmp_path: Path) -> None:
    """Entries missing name or command must be silently dropped."""
    cfg_dir = tmp_path / ".specsmith"
    cfg_dir.mkdir()
    (cfg_dir / "mcp.yml").write_text(
        "- name: ok\n  command: mcp-real\n- command: nameless\n- name: commandless\n- not_a_dict\n",
        encoding="utf-8",
    )
    tools = load_mcp_tools(tmp_path)
    assert [t.name for t in tools] == ["ok"]


def test_load_mcp_tools_returns_empty_on_unparseable_yaml(tmp_path: Path) -> None:
    cfg_dir = tmp_path / ".specsmith"
    cfg_dir.mkdir()
    (cfg_dir / "mcp.yml").write_text(": : :\n", encoding="utf-8")
    assert load_mcp_tools(tmp_path) == []


def test_mcp_server_spec_round_trip() -> None:
    spec = MCPServerSpec(name="x", command="y", args=["a"], env={"k": "v"})
    assert spec.name == "x"
    assert spec.args == ["a"]
    assert spec.env == {"k": "v"}


# ── Notebook record / replay (REQ-123 / TEST-123) ────────────────────────────


def test_notebook_record_with_session_id_captures_turns(tmp_path: Path) -> None:
    """`--session-id` materialises turns.jsonl as a `## Session turns` section."""
    sid = "sess_abc"
    sess_dir = tmp_path / ".specsmith" / "sessions" / sid
    sess_dir.mkdir(parents=True)
    turns = [
        {"role": "user", "utterance": "add hello world", "timestamp": "2026-04-29T00:00:00Z"},
        {"role": "agent", "utterance": "Plan: write a test", "timestamp": "2026-04-29T00:00:01Z"},
    ]
    (sess_dir / "turns.jsonl").write_text(
        "\n".join(json.dumps(t) for t in turns) + "\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "notebook",
            "record",
            "demo",
            "--project-dir",
            str(tmp_path),
            "--session-id",
            sid,
        ],
        env={"SPECSMITH_NO_AUTO_UPDATE": "1", "SPECSMITH_PYPI_CHECKED": "1"},
    )
    assert result.exit_code == 0, result.output

    nb = (tmp_path / "docs" / "notebooks" / "demo.md").read_text(encoding="utf-8")
    assert "# Notebook" in nb
    assert sid in nb
    assert "## Session turns" in nb
    assert "add hello world" in nb
    assert "Plan: write a test" in nb


def test_notebook_record_with_no_artifacts_writes_a_helpful_placeholder(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["notebook", "record", "empty", "--project-dir", str(tmp_path)],
        env={"SPECSMITH_NO_AUTO_UPDATE": "1", "SPECSMITH_PYPI_CHECKED": "1"},
    )
    assert result.exit_code == 0, result.output
    nb = (tmp_path / "docs" / "notebooks" / "empty.md").read_text(encoding="utf-8")
    assert "No artifacts captured" in nb


def test_notebook_replay_prints_recorded_notebook(tmp_path: Path) -> None:
    nb_dir = tmp_path / "docs" / "notebooks"
    nb_dir.mkdir(parents=True)
    (nb_dir / "demo.md").write_text("# Notebook — demo\nhello\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["notebook", "replay", "demo", "--project-dir", str(tmp_path)],
        env={"SPECSMITH_NO_AUTO_UPDATE": "1", "SPECSMITH_PYPI_CHECKED": "1"},
    )
    assert result.exit_code == 0
    assert "hello" in result.output


def test_notebook_replay_missing_slug_exits_non_zero(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["notebook", "replay", "ghost", "--project-dir", str(tmp_path)],
        env={"SPECSMITH_NO_AUTO_UPDATE": "1", "SPECSMITH_PYPI_CHECKED": "1"},
    )
    assert result.exit_code == 1
    assert "No notebook" in result.output


# ── Cloud spawn (REQ-126 / TEST-126) ─────────────────────────────────────────


def test_cloud_spawn_dry_run_writes_manifest_without_posting(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "cloud",
            "spawn",
            "add hello world",
            "--project-dir",
            str(tmp_path),
            "--dry-run",
        ],
        env={"SPECSMITH_NO_AUTO_UPDATE": "1", "SPECSMITH_PYPI_CHECKED": "1"},
    )
    assert result.exit_code == 0, result.output
    cloud_root = tmp_path / ".specsmith" / "cloud"
    assert cloud_root.is_dir()
    runs = list(cloud_root.iterdir())
    assert len(runs) == 1, "exactly one run directory should have been created"
    manifest = json.loads((runs[0] / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["utterance"] == "add hello world"
    assert manifest["dry_run"] is True
    assert (runs[0] / "workspace.tar.gz").is_file()


def test_cloud_spawn_help_documents_endpoint(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["cloud", "spawn", "--help"])
    assert result.exit_code == 0
    assert "--endpoint" in result.output
    assert "--dry-run" in result.output


# ── Perf smoke (REQ-124 / TEST-124) ──────────────────────────────────────────


def test_perf_smoke_script_main_writes_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run the perf-smoke script's main() with a tiny REQ count and a stubbed
    `_time_preflight` so the test never spawns a real subprocess.

    Verifies that ``baseline.json`` is written with the expected schema.
    """
    import importlib.util

    perf_path = Path(__file__).resolve().parent.parent / "scripts" / "perf_smoke.py"
    spec = importlib.util.spec_from_file_location("perf_smoke", perf_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Replace the slow subprocess call with a deterministic stub.
    monkeypatch.setattr(module, "_time_preflight", lambda *_a, **_k: 0.05)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.argv", ["perf_smoke.py", "--reqs", "5", "--project-dir", str(tmp_path)]
    )

    rc = module.main()
    assert rc == 0

    baseline = json.loads(
        (tmp_path / ".specsmith" / "perf" / "baseline.json").read_text(encoding="utf-8")
    )
    assert baseline["n_reqs"] == 5
    assert len(baseline["timings_seconds"]) == 3
    assert baseline["median_seconds"] == pytest.approx(0.05, abs=1e-3)
