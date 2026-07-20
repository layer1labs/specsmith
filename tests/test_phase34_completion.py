# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Phase 3-4 completion tests: mcp loader and notebook commands.

Covers REQ-121 (MCP), REQ-123 (notebook), and REQ-124 (perf smoke). The
CLI commands are exercised through Click's CliRunner so the tests stay
fully hermetic — no real subprocess, no real PyPI hits.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specsmith.agent.mcp import (
    MCPServerSpec,
    _read_specs,
    load_mcp_tools,
)

# ── MCP config parser (REQ-121 / TEST-121) ───────────────────────────
#
# `load_mcp_tools()` now actually opens an MCP server (REQ-130). End-to-end
# tests using a fake stdio server live in `test_mcp_client.py`. The tests
# below cover only the YAML config parser, so they remain hermetic.


def test_load_mcp_tools_returns_empty_when_config_missing(tmp_path: Path) -> None:
    """No `.specsmith/mcp.yml` => empty list, not an error."""
    assert load_mcp_tools(tmp_path) == []


def test_read_specs_parses_one_entry(tmp_path: Path) -> None:
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
    specs = _read_specs(tmp_path)
    assert len(specs) == 1
    spec = specs[0]
    assert spec.name == "filesystem"
    assert spec.command == "mcp-server-filesystem"
    assert spec.args == ["--root", "."]
    assert spec.env == {"HOME": "/tmp"}


def test_read_specs_skips_malformed_entries(tmp_path: Path) -> None:
    """Entries missing name or command must be silently dropped."""
    cfg_dir = tmp_path / ".specsmith"
    cfg_dir.mkdir()
    (cfg_dir / "mcp.yml").write_text(
        "- name: ok\n  command: mcp-real\n- command: nameless\n- name: commandless\n- not_a_dict\n",
        encoding="utf-8",
    )
    specs = _read_specs(tmp_path)
    assert [s.name for s in specs] == ["ok"]


def test_read_specs_returns_empty_on_unparseable_yaml(tmp_path: Path) -> None:
    cfg_dir = tmp_path / ".specsmith"
    cfg_dir.mkdir()
    (cfg_dir / "mcp.yml").write_text(": : :\n", encoding="utf-8")
    assert _read_specs(tmp_path) == []


def test_load_mcp_tools_skips_servers_that_fail_to_start(tmp_path: Path) -> None:
    """Real MCP client sweep: servers that don't open are dropped silently."""
    cfg_dir = tmp_path / ".specsmith"
    cfg_dir.mkdir()
    (cfg_dir / "mcp.yml").write_text(
        "- name: missing\n  command: definitely-not-a-real-mcp-binary-xyz\n",
        encoding="utf-8",
    )
    assert load_mcp_tools(tmp_path) == []


def test_mcp_server_spec_round_trip() -> None:
    spec = MCPServerSpec(name="x", command="y", args=["a"], env={"k": "v"})
    assert spec.name == "x"
    assert spec.args == ["a"]
    assert spec.env == {"k": "v"}


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
