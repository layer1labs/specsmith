# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""End-to-end tests for the real MCP JSON-RPC client (REQ-130 / TEST-130).

Uses ``tests/fixtures/mcp_fake_server.py`` so we can drive the full
handshake without depending on any external MCP server installation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from specsmith.agent.mcp import (
    MCP_PROTOCOL_VERSION,
    MCPError,
    MCPServerSpec,
    MCPSession,
    MCPTool,
    open_mcp_sessions,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
FAKE = FIXTURES / "mcp_fake_server.py"


def _spec(env: dict[str, str] | None = None) -> MCPServerSpec:
    return MCPServerSpec(
        name="fake",
        command=sys.executable,
        args=[str(FAKE)],
        env=env or {},
    )


# ── Discovery / handshake (TEST-130a..c) ─────────────────────────────────


def test_session_open_runs_handshake_and_lists_tools() -> None:
    session = MCPSession(_spec())
    try:
        tools = session.open()
        assert {t.name for t in tools} == {"echo", "boom"}
        echo = next(t for t in tools if t.name == "echo")
        assert "Echo" in echo.description
        assert echo.input_schema.get("required") == ["text"]
        assert echo.server_name == "fake"
    finally:
        session.close()


def test_session_open_pins_protocol_version_constant() -> None:
    # Make sure the public protocol-pin constant is the latest stable.
    assert MCP_PROTOCOL_VERSION == "2024-11-05"


def test_session_close_is_idempotent() -> None:
    session = MCPSession(_spec())
    session.open()
    session.close()
    session.close()  # second close must not raise


# ── Tool invocation (TEST-130d..g) ───────────────────────────────────────


def test_call_tool_returns_concatenated_text_blocks() -> None:
    session = MCPSession(_spec())
    try:
        session.open()
        result = session.call_tool("echo", {"text": "hello world"})
        assert result == "hello world"
    finally:
        session.close()


def test_call_tool_iserror_is_prefixed() -> None:
    session = MCPSession(_spec())
    try:
        session.open()
        result = session.call_tool("boom", {})
        assert result.startswith("mcp error:")
        assert "intentional boom" in result
    finally:
        session.close()


def test_call_tool_unknown_name_raises_mcp_error() -> None:
    session = MCPSession(_spec())
    try:
        session.open()
        with pytest.raises(MCPError) as exc:
            session.call_tool("does-not-exist", {})
        assert exc.value.code == -32601
    finally:
        session.close()


def test_mcp_tool_invoke_with_safety_blocks_disallowed_payloads() -> None:
    session = MCPSession(_spec())
    try:
        session.open()
        echo = next(t for t in session.tools if t.name == "echo")
        tool = MCPTool(descriptor=echo, session=session)

        def _check(name: str, args: dict[str, object]) -> tuple[bool, str]:
            text = str(args.get("text", ""))
            if "rm -rf" in text:
                return False, "destructive command refused"
            return True, ""

        # Allowed → flows through to call_tool.
        assert tool.invoke_with_safety({"text": "ok"}, _check) == "ok"
        # Disallowed → returns redacted message and never calls the server.
        blocked = tool.invoke_with_safety({"text": "rm -rf /"}, _check)
        assert blocked.startswith("mcp blocked by safety:")
    finally:
        session.close()


# ── Failure modes (TEST-130h..j) ─────────────────────────────────────────


def test_session_open_raises_when_server_crashes_during_initialize() -> None:
    session = MCPSession(_spec(env={"MCP_FAKE_CRASH_ON": "initialize"}))
    try:
        with pytest.raises(MCPError) as exc:
            session.open()
        assert exc.value.code == -32002
    finally:
        session.close()


def test_open_mcp_sessions_skips_servers_that_fail_to_start(
    tmp_path: Path,
) -> None:
    cfg = tmp_path / ".specsmith"
    cfg.mkdir()
    # First entry resolves, second does not.
    cfg.joinpath("mcp.yml").write_text(
        "- name: real\n"
        f"  command: {sys.executable}\n"
        f"  args: ['{FAKE.as_posix()}']\n"
        "- name: missing\n"
        "  command: definitely-not-a-real-mcp-binary-xyz\n",
        encoding="utf-8",
    )
    sessions = open_mcp_sessions(tmp_path)
    try:
        assert len(sessions) == 1
        assert sessions[0].spec.name == "real"
        assert {t.name for t in sessions[0].tools} == {"echo", "boom"}
    finally:
        for s in sessions:
            s.close()
