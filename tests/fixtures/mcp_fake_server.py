# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Fake stdio MCP server for unit tests (TEST-130).

Implements just enough of the JSON-RPC 2.0 MCP protocol to exercise
``specsmith.agent.mcp.MCPSession``:

* ``initialize`` -> succeeds, advertises tools capability.
* ``notifications/initialized`` -> no response.
* ``tools/list`` -> returns two tools ``echo`` and ``boom``.
* ``tools/call`` -> ``echo`` returns text content; ``boom`` returns
  isError=True; unknown names emit a JSON-RPC error response.

Behaviour is configurable via env vars so individual tests can opt into
specific failure modes:

* ``MCP_FAKE_CRASH_ON=<method>`` -> exit before responding to that method.
* ``MCP_FAKE_DELAY=<seconds>`` -> sleep before each response (for timeout tests).
* ``MCP_FAKE_PROTOCOL=<version>`` -> override advertised protocolVersion.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any


def _send(message: dict[str, Any]) -> None:
    line = json.dumps(message, ensure_ascii=False) + "\n"
    sys.stdout.write(line)
    sys.stdout.flush()


def _maybe_crash(method: str) -> None:
    crash_on = os.environ.get("MCP_FAKE_CRASH_ON", "")
    if crash_on and crash_on == method:
        # Drop into a crash that closes stdout so the client sees EOF.
        sys.stdout.close()
        sys.exit(7)


def _maybe_delay() -> None:
    raw = os.environ.get("MCP_FAKE_DELAY", "")
    if not raw:
        return
    try:
        delay = float(raw)
    except ValueError:
        return
    time.sleep(delay)


def _handle_initialize(req_id: int) -> None:
    _maybe_crash("initialize")
    _maybe_delay()
    _send(
        {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": os.environ.get("MCP_FAKE_PROTOCOL", "2024-11-05"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "fake-mcp", "version": "0.1"},
            },
        }
    )


def _handle_tools_list(req_id: int) -> None:
    _maybe_crash("tools/list")
    _maybe_delay()
    _send(
        {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "echo",
                        "description": "Echo the supplied text back to the client.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"text": {"type": "string"}},
                            "required": ["text"],
                        },
                    },
                    {
                        "name": "boom",
                        "description": "Always returns isError=True.",
                        "inputSchema": {"type": "object"},
                    },
                ]
            },
        }
    )


def _handle_tools_call(req_id: int, params: dict[str, Any]) -> None:
    _maybe_crash("tools/call")
    _maybe_delay()
    name = params.get("name", "")
    args = params.get("arguments", {}) or {}
    if name == "echo":
        text = str(args.get("text", ""))
        _send(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": text}]},
            }
        )
        return
    if name == "boom":
        _send(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": "intentional boom"}],
                },
            }
        )
        return
    _send(
        {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"unknown tool: {name}"},
        }
    )


def main() -> int:
    while True:
        line = sys.stdin.readline()
        if not line:
            return 0
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if not isinstance(msg, dict):
            continue
        method = msg.get("method", "")
        req_id = msg.get("id")
        # Notifications carry no id and never receive a response.
        if req_id is None:
            continue
        if method == "initialize":
            _handle_initialize(int(req_id))
        elif method == "tools/list":
            _handle_tools_list(int(req_id))
        elif method == "tools/call":
            _handle_tools_call(int(req_id), msg.get("params") or {})
        else:
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"unknown method: {method}"},
                }
            )


if __name__ == "__main__":
    raise SystemExit(main())
