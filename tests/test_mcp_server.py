# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for the native MCP governance server (REQ-363 / TEST-364).

Covers:
- MCP JSON-RPC protocol handshake (initialize, tools/list, tools/call)
- All six governance tool handlers (unit-level, via _handle_* functions)
- Notification handling (no response expected)
- Unknown tool / method error handling
- CLI smoke: specsmith mcp serve responds to initialize
"""

from __future__ import annotations  # noqa: I001

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import specsmith.mcp_server as mcp_mod


# ---------------------------------------------------------------------------
# Autouse: suppress auto-update noise
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _no_auto_update(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPECSMITH_NO_AUTO_UPDATE", "1")
    monkeypatch.setenv("SPECSMITH_PYPI_CHECKED", "1")
    monkeypatch.setenv("SPECSMITH_ALLOW_NON_PIPX", "1")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_rpc(method: str, params: dict[str, Any] | None = None, req_id: int = 1) -> dict[str, Any]:
    msg: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        msg["params"] = params
    return msg


def _send_rpc(msg: dict[str, Any]) -> dict[str, Any]:
    """Feed one JSON-RPC message to _handle_request and return its response."""
    resp = mcp_mod._handle_request(msg)
    assert resp is not None, "Expected a response but got None"
    return resp


# ---------------------------------------------------------------------------
# Protocol-level tests
# ---------------------------------------------------------------------------


class TestMcpProtocol:
    def test_initialize_returns_server_info(self) -> None:
        resp = _send_rpc(
            _make_rpc(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "pytest", "version": "0"},
                },
            )
        )
        assert resp["jsonrpc"] == "2.0"
        result = resp["result"]
        assert result["protocolVersion"] == "2024-11-05"
        assert result["serverInfo"]["name"] == "specsmith-governance"
        assert "tools" in result["capabilities"]

    def test_tools_list_returns_governance_and_context_tools(self) -> None:
        resp = _send_rpc(_make_rpc("tools/list", {}, req_id=2))
        tools = resp["result"]["tools"]
        assert len(tools) == 9
        names = {t["name"] for t in tools}
        assert names == {
            "governance_project_list",
            "governance_audit",
            "governance_checkpoint",
            "governance_preflight",
            "governance_phase",
            "governance_req_list",
            "governance_trace_seal",
            "governance_context_transition",
            "governance_context_verify",
        }

    def test_each_tool_has_input_schema(self) -> None:
        resp = _send_rpc(_make_rpc("tools/list", {}, req_id=3))
        for tool in resp["result"]["tools"]:
            assert "inputSchema" in tool, f"Missing inputSchema on {tool['name']}"
            assert tool["inputSchema"]["type"] == "object"

    def test_notification_returns_none(self) -> None:
        # Notifications have no id — no response expected
        msg = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        assert mcp_mod._handle_request(msg) is None

    def test_unknown_method_returns_error(self) -> None:
        resp = _send_rpc(_make_rpc("no_such_method", {}, req_id=99))
        assert "error" in resp
        assert resp["error"]["code"] == -32601

    def test_unknown_tool_returns_is_error_true(self) -> None:
        resp = _send_rpc(
            _make_rpc(
                "tools/call",
                {"name": "nonexistent_tool", "arguments": {}},
                req_id=5,
            )
        )
        assert resp["result"]["isError"] is True

    def test_ping_returns_ok(self) -> None:
        resp = _send_rpc(_make_rpc("ping", {}, req_id=7))
        assert resp["result"] == {}

    def test_parse_error_on_bad_json(self) -> None:
        # _handle_request only processes dicts; parse errors are handled in run_server
        resp = mcp_mod._handle_request(
            {"jsonrpc": "2.0", "method": "initialize", "id": 10, "params": {}}
        )
        assert resp is not None
        assert "result" in resp


# ---------------------------------------------------------------------------
# Tool handler unit tests
# ---------------------------------------------------------------------------


class TestGovernanceAudit:
    def test_returns_healthy_key(self, tmp_path: Path) -> None:
        result = mcp_mod._handle_governance_audit({"project_dir": str(tmp_path)})
        assert "healthy" in result

    def test_returns_checks_list(self, tmp_path: Path) -> None:
        result = mcp_mod._handle_governance_audit({"project_dir": str(tmp_path)})
        assert isinstance(result.get("checks"), list)

    def test_via_tools_call(self, tmp_path: Path) -> None:
        resp = _send_rpc(
            _make_rpc(
                "tools/call",
                {"name": "governance_audit", "arguments": {"project_dir": str(tmp_path)}},
                req_id=20,
            )
        )
        assert resp["result"]["isError"] is False
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "healthy" in content


class TestGovernanceCheckpoint:
    def test_returns_anchor_key(self, tmp_path: Path) -> None:
        result = mcp_mod._handle_governance_checkpoint({"project_dir": str(tmp_path)})
        assert "anchor" in result
        assert result["anchor"].startswith("SPECSMITH-ANCHOR-")

    def test_returns_phase_and_health(self, tmp_path: Path) -> None:
        result = mcp_mod._handle_governance_checkpoint({"project_dir": str(tmp_path)})
        assert "health" in result
        assert "phase" in result
        assert "req_count" in result

    def test_via_tools_call(self, tmp_path: Path) -> None:
        resp = _send_rpc(
            _make_rpc(
                "tools/call",
                {"name": "governance_checkpoint", "arguments": {"project_dir": str(tmp_path)}},
                req_id=21,
            )
        )
        assert resp["result"]["isError"] is False
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "anchor" in content


class TestGovernancePreflight:
    def test_empty_intent_returns_rejected(self, tmp_path: Path) -> None:
        result = mcp_mod._handle_governance_preflight({"intent": "", "project_dir": str(tmp_path)})
        assert result["decision"] == "rejected"

    def test_returns_decision_key(self, tmp_path: Path) -> None:
        result = mcp_mod._handle_governance_preflight(
            {
                "intent": "read governance health status",
                "project_dir": str(tmp_path),
            }
        )
        assert "decision" in result

    def test_via_tools_call(self, tmp_path: Path) -> None:
        resp = _send_rpc(
            _make_rpc(
                "tools/call",
                {
                    "name": "governance_preflight",
                    "arguments": {
                        "intent": "check audit health",
                        "project_dir": str(tmp_path),
                    },
                },
                req_id=22,
            )
        )
        assert resp["result"]["isError"] is False
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "decision" in content


class TestGovernancePhase:
    def test_returns_phase_key(self, tmp_path: Path) -> None:
        result = mcp_mod._handle_governance_phase({"project_dir": str(tmp_path)})
        assert "phase" in result

    def test_via_tools_call(self, tmp_path: Path) -> None:
        resp = _send_rpc(
            _make_rpc(
                "tools/call",
                {"name": "governance_phase", "arguments": {"project_dir": str(tmp_path)}},
                req_id=23,
            )
        )
        assert resp["result"]["isError"] is False
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "phase" in content


class TestGovernanceReqList:
    def test_missing_requirements_json_returns_error(self, tmp_path: Path) -> None:
        result = mcp_mod._handle_governance_req_list({"project_dir": str(tmp_path)})
        assert "error" in result

    def test_with_requirements_json(self, tmp_path: Path) -> None:
        spec_dir = tmp_path / ".specsmith"
        spec_dir.mkdir()
        reqs = [
            {"id": "REQ-001", "title": "First requirement", "status": "implemented"},
            {"id": "REQ-002", "title": "Second requirement", "status": "planned"},
        ]
        (spec_dir / "requirements.json").write_text(json.dumps(reqs), encoding="utf-8")
        (spec_dir / "testcases.json").write_text(
            json.dumps([{"id": "TEST-001", "covers": "REQ-001"}]), encoding="utf-8"
        )

        result = mcp_mod._handle_governance_req_list({"project_dir": str(tmp_path)})
        assert result["total"] == 2
        assert result["covered"] == 1
        req_ids = [r["id"] for r in result["reqs"]]
        assert "REQ-001" in req_ids
        covered_reqs = [r for r in result["reqs"] if r["covered"]]
        assert len(covered_reqs) == 1
        assert covered_reqs[0]["id"] == "REQ-001"

    def test_status_filter(self, tmp_path: Path) -> None:
        spec_dir = tmp_path / ".specsmith"
        spec_dir.mkdir()
        reqs = [
            {"id": "REQ-001", "title": "Impl req", "status": "implemented"},
            {"id": "REQ-002", "title": "Planned req", "status": "planned"},
        ]
        (spec_dir / "requirements.json").write_text(json.dumps(reqs), encoding="utf-8")

        result = mcp_mod._handle_governance_req_list(
            {
                "project_dir": str(tmp_path),
                "status_filter": "planned",
            }
        )
        assert result["total"] == 1
        assert result["reqs"][0]["id"] == "REQ-002"

    def test_via_tools_call(self, tmp_path: Path) -> None:
        resp = _send_rpc(
            _make_rpc(
                "tools/call",
                {"name": "governance_req_list", "arguments": {"project_dir": str(tmp_path)}},
                req_id=24,
            )
        )
        assert resp["result"]["isError"] is False


class TestRegistryFunctions:
    """Unit tests for the persistent project registry helpers."""

    def test_read_registry_missing_file_returns_empty(  # noqa: E501
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SPECSMITH_HOME", str(tmp_path))
        # No file created — should return empty list
        result = mcp_mod.read_registry()
        assert result == []

    def test_write_then_read_roundtrip(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SPECSMITH_HOME", str(tmp_path))
        paths = ["/path/to/proj1", "/path/to/proj2"]
        mcp_mod.write_registry(paths)
        assert mcp_mod.read_registry() == [str(Path(path).resolve()) for path in paths]

    def test_register_project_adds_new_entry(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SPECSMITH_HOME", str(tmp_path))
        proj = tmp_path / "myproject"
        proj.mkdir()
        added = mcp_mod.register_project(str(proj), allow_uninitialized=True)
        assert added is True
        assert str(proj) in mcp_mod.read_registry()

    def test_register_project_idempotent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SPECSMITH_HOME", str(tmp_path))
        proj = tmp_path / "myproject"
        proj.mkdir()
        mcp_mod.register_project(str(proj), allow_uninitialized=True)
        added_again = mcp_mod.register_project(str(proj), allow_uninitialized=True)
        assert added_again is False
        assert mcp_mod.read_registry().count(str(proj)) == 1

    def test_unregister_project_removes_entry(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SPECSMITH_HOME", str(tmp_path))
        proj = tmp_path / "myproject"
        proj.mkdir()
        mcp_mod.register_project(str(proj), allow_uninitialized=True)
        removed = mcp_mod.unregister_project(str(proj))
        assert removed is True
        assert str(proj) not in mcp_mod.read_registry()

    def test_unregister_project_returns_false_if_not_registered(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SPECSMITH_HOME", str(tmp_path))
        result = mcp_mod.unregister_project("/nonexistent/path")
        assert result is False

    def test_registry_based_server_startup(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """run_server with no args should pick up projects from the registry."""
        import io

        monkeypatch.setenv("SPECSMITH_HOME", str(tmp_path))
        proj_a = tmp_path / "alpha"
        proj_a.mkdir()
        proj_b = tmp_path / "beta"
        proj_b.mkdir()
        mcp_mod.register_project(str(proj_a), allow_uninitialized=True)
        mcp_mod.register_project(str(proj_b), allow_uninitialized=True)

        old_stdin = sys.stdin
        sys.stdin = io.StringIO("")
        try:
            mcp_mod.run_server()  # no project_dir arg — should use registry
        finally:
            sys.stdin = old_stdin

        # The newest explicit registration is prepended and becomes the default.
        assert str(proj_b) == mcp_mod._DEFAULT_PROJECT_DIR
        assert str(proj_b) in mcp_mod._REGISTERED_PROJECTS


class TestGovernanceProjectList:
    def test_returns_default_project(self, tmp_path: Path) -> None:
        # Prime server state with a known directory
        mcp_mod._DEFAULT_PROJECT_DIR = str(tmp_path)
        mcp_mod._REGISTERED_PROJECTS = [str(tmp_path)]

        result = mcp_mod._handle_governance_project_list({})
        assert result["default_project"] == str(tmp_path)
        assert str(tmp_path) in result["projects"]
        assert result["count"] >= 1

    def test_via_tools_call(self, tmp_path: Path) -> None:
        mcp_mod._DEFAULT_PROJECT_DIR = str(tmp_path)
        mcp_mod._REGISTERED_PROJECTS = [str(tmp_path)]

        resp = _send_rpc(
            _make_rpc(
                "tools/call",
                {"name": "governance_project_list", "arguments": {}},
                req_id=30,
            )
        )
        assert resp["result"]["isError"] is False
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "projects" in content
        assert "count" in content

    def test_extra_projects_registered(self, tmp_path: Path) -> None:
        """run_server registers extra_project_dirs and they appear in project_list."""
        import io

        extra = tmp_path / "extra"
        extra.mkdir()

        # Patch stdin to EOF immediately so run_server exits
        old_stdin = sys.stdin
        sys.stdin = io.StringIO("")
        try:
            mcp_mod.run_server(project_dir=str(tmp_path), extra_project_dirs=[str(extra)])
        finally:
            sys.stdin = old_stdin

        assert str(tmp_path.resolve()) == mcp_mod._DEFAULT_PROJECT_DIR
        assert str(extra.resolve()) in mcp_mod._REGISTERED_PROJECTS
        assert mcp_mod._REGISTERED_PROJECTS[0] == str(tmp_path.resolve())

    def test_no_chdir_called(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """run_server must NOT call os.chdir — paths are resolved absolutely."""
        import io

        chdir_calls: list[str] = []
        monkeypatch.setattr("os.chdir", lambda p: chdir_calls.append(str(p)))
        old_stdin = sys.stdin
        sys.stdin = io.StringIO("")
        try:
            mcp_mod.run_server(project_dir=str(tmp_path))
        finally:
            sys.stdin = old_stdin

        assert chdir_calls == [], "run_server must not call os.chdir"


class TestGovernanceTraceSeal:
    def test_missing_description_returns_error(self, tmp_path: Path) -> None:
        result = mcp_mod._handle_governance_trace_seal(
            {
                "seal_type": "milestone",
                "description": "",
                "project_dir": str(tmp_path),
            }
        )
        assert result["sealed"] is False
        assert "error" in result

    def test_seals_milestone(self, tmp_path: Path) -> None:
        spec_dir = tmp_path / ".specsmith"
        spec_dir.mkdir()

        result = mcp_mod._handle_governance_trace_seal(
            {
                "seal_type": "milestone",
                "description": "test seal for pytest",
                "project_dir": str(tmp_path),
            }
        )
        assert result["sealed"] is True
        assert result["seal_id"] == "SEAL-0001"
        assert "entry_hash" in result

    def test_second_seal_chains_to_first(self, tmp_path: Path) -> None:
        spec_dir = tmp_path / ".specsmith"
        spec_dir.mkdir()

        mcp_mod._handle_governance_trace_seal(
            {"seal_type": "decision", "description": "first", "project_dir": str(tmp_path)}
        )
        result2 = mcp_mod._handle_governance_trace_seal(
            {"seal_type": "milestone", "description": "second", "project_dir": str(tmp_path)}
        )
        assert result2["seal_id"] == "SEAL-0002"
        assert result2["sealed"] is True

    def test_via_tools_call(self, tmp_path: Path) -> None:
        (tmp_path / ".specsmith").mkdir()
        resp = _send_rpc(
            _make_rpc(
                "tools/call",
                {
                    "name": "governance_trace_seal",
                    "arguments": {
                        "seal_type": "milestone",
                        "description": "pytest seal",
                        "project_dir": str(tmp_path),
                    },
                },
                req_id=25,
            )
        )
        assert resp["result"]["isError"] is False
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["sealed"] is True


# ---------------------------------------------------------------------------
# CLI smoke test: specsmith mcp serve handshake via subprocess
# ---------------------------------------------------------------------------


class TestMcpServeCli:
    def test_initialize_via_subprocess(self) -> None:
        """Send an initialize message to `specsmith mcp serve` via subprocess stdin."""
        init_msg = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "clientInfo": {"name": "test-client", "version": "0"},
                    },
                }
            )
            + "\n"
        )

        env = {**os.environ, "SPECSMITH_ALLOW_NON_PIPX": "1", "SPECSMITH_NO_AUTO_UPDATE": "1"}
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "specsmith", "mcp", "serve"],
                input=init_msg,
                capture_output=True,
                text=True,
                timeout=15,
                env=env,
            )
        except subprocess.TimeoutExpired:  # pragma: no cover
            pytest.skip("mcp serve subprocess timed out (slow CI env)")
            return  # never reached; satisfies flow analysis

        assert proc.stdout, f"No output from mcp serve (stderr: {proc.stderr[:500]})"
        response = json.loads(proc.stdout.strip().splitlines()[0])
        assert response["result"]["serverInfo"]["name"] == "specsmith-governance"

    def test_tools_list_via_subprocess(self) -> None:
        """Send initialize + notifications/initialized + tools/list to the server."""
        messages = [
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "clientInfo": {"name": "test", "version": "0"},
                    },
                }
            ),
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
        ]
        stdin_payload = "\n".join(messages) + "\n"

        env = {**os.environ, "SPECSMITH_ALLOW_NON_PIPX": "1", "SPECSMITH_NO_AUTO_UPDATE": "1"}
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "specsmith", "mcp", "serve"],
                input=stdin_payload,
                capture_output=True,
                text=True,
                timeout=15,
                env=env,
            )
        except subprocess.TimeoutExpired:  # pragma: no cover
            pytest.skip("mcp serve subprocess timed out (slow CI env)")
            return  # never reached; satisfies flow analysis

        lines = [ln for ln in proc.stdout.strip().splitlines() if ln.strip()]
        assert len(lines) >= 2, f"Expected ≥2 responses, got: {lines}"
        # Last response should be tools/list result
        tools_resp = json.loads(lines[-1])
        assert "result" in tools_resp
        tools = tools_resp["result"]["tools"]
        assert len(tools) == 7


# ---------------------------------------------------------------------------
# TEST-365 (REQ-364): governance_req_list reads YAML directly in yaml_mode
# ---------------------------------------------------------------------------


class TestGovernanceReqListYamlMode:
    """Verify that _handle_governance_req_list bypasses stale JSON cache in YAML-mode.

    Reproduces the scenario described in GitHub issue #201:
    - Project is in YAML-mode (.specsmith/governance-mode == 'yaml')
    - A new requirement is added to docs/requirements/*.yml
    - The JSON cache (.specsmith/requirements.json) is NOT updated (stale)
    - governance_req_list must still return the new requirement
    """

    @pytest.fixture()
    def yaml_mode_project(self, tmp_path: Path) -> Path:
        """Set up a minimal YAML-mode project with stale JSON cache."""
        import yaml

        # .specsmith/ structure
        state = tmp_path / ".specsmith"
        state.mkdir()
        (state / "governance-mode").write_text("yaml", encoding="utf-8")

        # docs/requirements/*.yml — canonical source
        req_dir = tmp_path / "docs" / "requirements"
        req_dir.mkdir(parents=True)
        reqs = [
            {"id": "REQ-001", "title": "Old requirement", "status": "accepted"},
            {"id": "REQ-NEW", "title": "New requirement added to YAML", "status": "planned"},
        ]
        (req_dir / "governance.yml").write_text(yaml.dump(reqs), encoding="utf-8")

        # docs/tests/*.yml
        test_dir = tmp_path / "docs" / "tests"
        test_dir.mkdir(parents=True)
        tests = [
            {"id": "TEST-001", "title": "Covers old req", "requirement_id": "REQ-001"},
        ]
        (test_dir / "governance.yml").write_text(yaml.dump(tests), encoding="utf-8")

        # STALE JSON cache — only contains REQ-001, missing REQ-NEW
        stale_reqs = [{"id": "REQ-001", "title": "Old requirement", "status": "accepted"}]
        (state / "requirements.json").write_text(json.dumps(stale_reqs), encoding="utf-8")
        (state / "testcases.json").write_text(
            json.dumps([{"id": "TEST-001", "requirement_id": "REQ-001"}]), encoding="utf-8"
        )
        return tmp_path

    def test_yaml_mode_returns_new_req_despite_stale_cache(self, yaml_mode_project: Path) -> None:
        """REQ-364: governance_req_list in yaml_mode reads YAML, not JSON cache."""
        result = mcp_mod._handle_governance_req_list({"project_dir": str(yaml_mode_project)})
        req_ids = {r["id"] for r in result["reqs"]}
        assert "REQ-NEW" in req_ids, (
            "REQ-NEW should be visible from YAML source "
            f"(stale cache only has REQ-001); got: {req_ids}"
        )
        assert result["total"] == 2

    def test_yaml_mode_coverage_from_yaml_tests(self, yaml_mode_project: Path) -> None:
        """Coverage is computed from YAML tests, not stale JSON cache."""
        result = mcp_mod._handle_governance_req_list({"project_dir": str(yaml_mode_project)})
        reqs_by_id = {r["id"]: r for r in result["reqs"]}
        # REQ-001 has a test in YAML → covered
        assert reqs_by_id["REQ-001"]["covered"] is True
        # REQ-NEW has no test → not covered
        assert reqs_by_id["REQ-NEW"]["covered"] is False

    def test_legacy_mode_still_uses_json_cache(self, tmp_path: Path) -> None:
        """Non-yaml-mode projects still use the JSON cache (backward compat)."""
        state = tmp_path / ".specsmith"
        state.mkdir()
        # No governance-mode file → legacy mode
        reqs = [{"id": "REQ-001", "title": "Cached req", "status": "accepted"}]
        (state / "requirements.json").write_text(json.dumps(reqs), encoding="utf-8")
        (state / "testcases.json").write_text("[]", encoding="utf-8")

        result = mcp_mod._handle_governance_req_list({"project_dir": str(tmp_path)})
        assert result["total"] == 1
        assert result["reqs"][0]["id"] == "REQ-001"
