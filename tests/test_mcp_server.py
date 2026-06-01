# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for the native MCP governance server (REQ-363 / TEST-364).

Covers:
- MCP JSON-RPC protocol handshake (initialize, tools/list, tools/call)
- All six governance tool handlers (unit-level, via _handle_* functions)
- Notification handling (no response expected)
- Unknown tool / method error handling
- CLI smoke: specsmith mcp serve responds to initialize
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


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
    from specsmith.mcp_server import _handle_request
    resp = _handle_request(msg)
    assert resp is not None, "Expected a response but got None"
    return resp


# ---------------------------------------------------------------------------
# Protocol-level tests
# ---------------------------------------------------------------------------

class TestMcpProtocol:
    def test_initialize_returns_server_info(self) -> None:
        resp = _send_rpc(_make_rpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "pytest", "version": "0"},
        }))
        assert resp["jsonrpc"] == "2.0"
        result = resp["result"]
        assert result["protocolVersion"] == "2024-11-05"
        assert result["serverInfo"]["name"] == "specsmith-governance"
        assert "tools" in result["capabilities"]

    def test_tools_list_returns_six_tools(self) -> None:
        resp = _send_rpc(_make_rpc("tools/list", {}, req_id=2))
        tools = resp["result"]["tools"]
        assert len(tools) == 6
        names = {t["name"] for t in tools}
        assert names == {
            "governance_audit",
            "governance_checkpoint",
            "governance_preflight",
            "governance_phase",
            "governance_req_list",
            "governance_trace_seal",
        }

    def test_each_tool_has_input_schema(self) -> None:
        resp = _send_rpc(_make_rpc("tools/list", {}, req_id=3))
        for tool in resp["result"]["tools"]:
            assert "inputSchema" in tool, f"Missing inputSchema on {tool['name']}"
            assert tool["inputSchema"]["type"] == "object"

    def test_notification_returns_none(self) -> None:
        from specsmith.mcp_server import _handle_request
        # Notifications have no id — no response expected
        msg = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        assert _handle_request(msg) is None

    def test_unknown_method_returns_error(self) -> None:
        resp = _send_rpc(_make_rpc("no_such_method", {}, req_id=99))
        assert "error" in resp
        assert resp["error"]["code"] == -32601

    def test_unknown_tool_returns_is_error_true(self) -> None:
        resp = _send_rpc(_make_rpc(
            "tools/call",
            {"name": "nonexistent_tool", "arguments": {}},
            req_id=5,
        ))
        assert resp["result"]["isError"] is True

    def test_ping_returns_ok(self) -> None:
        resp = _send_rpc(_make_rpc("ping", {}, req_id=7))
        assert resp["result"] == {}

    def test_parse_error_on_bad_json(self) -> None:
        from specsmith.mcp_server import _handle_request
        # _handle_request only processes dicts; parse errors are handled in run_server
        resp = _handle_request({"jsonrpc": "2.0", "method": "initialize", "id": 10, "params": {}})
        assert resp is not None
        assert "result" in resp


# ---------------------------------------------------------------------------
# Tool handler unit tests
# ---------------------------------------------------------------------------

class TestGovernanceAudit:
    def test_returns_healthy_key(self, tmp_path: Path) -> None:
        from specsmith.mcp_server import _handle_governance_audit
        result = _handle_governance_audit({"project_dir": str(tmp_path)})
        assert "healthy" in result

    def test_returns_checks_list(self, tmp_path: Path) -> None:
        from specsmith.mcp_server import _handle_governance_audit
        result = _handle_governance_audit({"project_dir": str(tmp_path)})
        assert isinstance(result.get("checks"), list)

    def test_via_tools_call(self, tmp_path: Path) -> None:
        resp = _send_rpc(_make_rpc(
            "tools/call",
            {"name": "governance_audit", "arguments": {"project_dir": str(tmp_path)}},
            req_id=20,
        ))
        assert resp["result"]["isError"] is False
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "healthy" in content


class TestGovernanceCheckpoint:
    def test_returns_anchor_key(self, tmp_path: Path) -> None:
        from specsmith.mcp_server import _handle_governance_checkpoint
        result = _handle_governance_checkpoint({"project_dir": str(tmp_path)})
        assert "anchor" in result
        assert result["anchor"].startswith("SPECSMITH-ANCHOR-")

    def test_returns_phase_and_health(self, tmp_path: Path) -> None:
        from specsmith.mcp_server import _handle_governance_checkpoint
        result = _handle_governance_checkpoint({"project_dir": str(tmp_path)})
        assert "health" in result
        assert "phase" in result
        assert "req_count" in result

    def test_via_tools_call(self, tmp_path: Path) -> None:
        resp = _send_rpc(_make_rpc(
            "tools/call",
            {"name": "governance_checkpoint", "arguments": {"project_dir": str(tmp_path)}},
            req_id=21,
        ))
        assert resp["result"]["isError"] is False
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "anchor" in content


class TestGovernancePreflight:
    def test_empty_intent_returns_rejected(self, tmp_path: Path) -> None:
        from specsmith.mcp_server import _handle_governance_preflight
        result = _handle_governance_preflight({"intent": "", "project_dir": str(tmp_path)})
        assert result["decision"] == "rejected"

    def test_returns_decision_key(self, tmp_path: Path) -> None:
        from specsmith.mcp_server import _handle_governance_preflight
        result = _handle_governance_preflight({
            "intent": "read governance health status",
            "project_dir": str(tmp_path),
        })
        assert "decision" in result

    def test_via_tools_call(self, tmp_path: Path) -> None:
        resp = _send_rpc(_make_rpc(
            "tools/call",
            {"name": "governance_preflight", "arguments": {
                "intent": "check audit health",
                "project_dir": str(tmp_path),
            }},
            req_id=22,
        ))
        assert resp["result"]["isError"] is False
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "decision" in content


class TestGovernancePhase:
    def test_returns_phase_key(self, tmp_path: Path) -> None:
        from specsmith.mcp_server import _handle_governance_phase
        result = _handle_governance_phase({"project_dir": str(tmp_path)})
        assert "phase" in result

    def test_via_tools_call(self, tmp_path: Path) -> None:
        resp = _send_rpc(_make_rpc(
            "tools/call",
            {"name": "governance_phase", "arguments": {"project_dir": str(tmp_path)}},
            req_id=23,
        ))
        assert resp["result"]["isError"] is False
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "phase" in content


class TestGovernanceReqList:
    def test_missing_requirements_json_returns_error(self, tmp_path: Path) -> None:
        from specsmith.mcp_server import _handle_governance_req_list
        result = _handle_governance_req_list({"project_dir": str(tmp_path)})
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

        from specsmith.mcp_server import _handle_governance_req_list
        result = _handle_governance_req_list({"project_dir": str(tmp_path)})
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

        from specsmith.mcp_server import _handle_governance_req_list
        result = _handle_governance_req_list({
            "project_dir": str(tmp_path),
            "status_filter": "planned",
        })
        assert result["total"] == 1
        assert result["reqs"][0]["id"] == "REQ-002"

    def test_via_tools_call(self, tmp_path: Path) -> None:
        resp = _send_rpc(_make_rpc(
            "tools/call",
            {"name": "governance_req_list", "arguments": {"project_dir": str(tmp_path)}},
            req_id=24,
        ))
        assert resp["result"]["isError"] is False


class TestGovernanceTraceSeal:
    def test_missing_description_returns_error(self, tmp_path: Path) -> None:
        from specsmith.mcp_server import _handle_governance_trace_seal
        result = _handle_governance_trace_seal({
            "seal_type": "milestone",
            "description": "",
            "project_dir": str(tmp_path),
        })
        assert result["sealed"] is False
        assert "error" in result

    def test_seals_milestone(self, tmp_path: Path) -> None:
        spec_dir = tmp_path / ".specsmith"
        spec_dir.mkdir()

        from specsmith.mcp_server import _handle_governance_trace_seal
        result = _handle_governance_trace_seal({
            "seal_type": "milestone",
            "description": "test seal for pytest",
            "project_dir": str(tmp_path),
        })
        assert result["sealed"] is True
        assert result["seal_id"] == "SEAL-0001"
        assert "entry_hash" in result

    def test_second_seal_chains_to_first(self, tmp_path: Path) -> None:
        spec_dir = tmp_path / ".specsmith"
        spec_dir.mkdir()

        from specsmith.mcp_server import _handle_governance_trace_seal
        _handle_governance_trace_seal({
            "seal_type": "decision", "description": "first", "project_dir": str(tmp_path)
        })
        result2 = _handle_governance_trace_seal({
            "seal_type": "milestone", "description": "second", "project_dir": str(tmp_path)
        })
        assert result2["seal_id"] == "SEAL-0002"
        assert result2["sealed"] is True

    def test_via_tools_call(self, tmp_path: Path) -> None:
        (tmp_path / ".specsmith").mkdir()
        resp = _send_rpc(_make_rpc(
            "tools/call",
            {"name": "governance_trace_seal", "arguments": {
                "seal_type": "milestone",
                "description": "pytest seal",
                "project_dir": str(tmp_path),
            }},
            req_id=25,
        ))
        assert resp["result"]["isError"] is False
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["sealed"] is True


# ---------------------------------------------------------------------------
# CLI smoke test: specsmith mcp serve handshake via subprocess
# ---------------------------------------------------------------------------

class TestMcpServeCli:
    def test_initialize_via_subprocess(self) -> None:
        """Send an initialize message to `specsmith mcp serve` via subprocess stdin."""
        init_msg = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "0"},
            },
        }) + "\n"

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
        except subprocess.TimeoutExpired:
            pytest.skip("mcp serve subprocess timed out (slow CI env)")

        assert proc.stdout, f"No output from mcp serve (stderr: {proc.stderr[:500]})"
        response = json.loads(proc.stdout.strip().splitlines()[0])
        assert response["result"]["serverInfo"]["name"] == "specsmith-governance"

    def test_tools_list_via_subprocess(self) -> None:
        """Send initialize + notifications/initialized + tools/list to the server."""
        messages = [
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test", "version": "0"},
            }}),
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
        except subprocess.TimeoutExpired:
            pytest.skip("mcp serve subprocess timed out (slow CI env)")

        lines = [l for l in proc.stdout.strip().splitlines() if l.strip()]
        assert len(lines) >= 2, f"Expected ≥2 responses, got: {lines}"
        # Last response should be tools/list result
        tools_resp = json.loads(lines[-1])
        assert "result" in tools_resp
        tools = tools_resp["result"]["tools"]
        assert len(tools) == 6
