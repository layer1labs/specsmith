# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""MCP (Model Context Protocol) tool consumption for Nexus (REQ-121).

Reads ``.specsmith/mcp.yml`` (a list of server configs) and returns a list
of tool wrappers that Nexus can register alongside its built-in tool set.
The wrappers are invoked over stdio per the MCP spec (subprocess +
JSON-RPC framing). For 1.0 we ship the loader and the wrapper interface;
the actual stdio JSON-RPC client is implemented but kept narrow so the
Specsmith safety middleware fully wraps every call.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class MCPServerSpec:
    """Static configuration for an MCP server.

    Mirrors `.specsmith/mcp.yml` entries; the YAML parser turns each
    entry into one of these.
    """

    name: str
    command: str
    args: list[str]
    env: dict[str, str]


@dataclass
class MCPTool:
    """A Nexus-side handle to an MCP server.

    Calling ``invoke(payload)`` opens a subprocess, sends the payload as
    a JSON-RPC ``tools/call`` request, and returns the response. Errors
    surface as plain strings; the orchestrator wraps the call with the
    standard Specsmith safety middleware so destructive payloads are
    blocked exactly the same way as native Nexus tools.
    """

    spec: MCPServerSpec

    @property
    def name(self) -> str:
        return self.spec.name

    def invoke(self, payload: dict[str, Any]) -> str:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": payload,
        }
        body = json.dumps(request) + "\n"
        try:
            proc = subprocess.run(  # noqa: S603 - argv is configured by user
                [self.spec.command, *self.spec.args],
                input=body,
                capture_output=True,
                text=True,
                timeout=30,
                env={**self.spec.env},
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return f"mcp error: {exc}"
        if proc.returncode != 0:
            return f"mcp error: {proc.stderr.strip() or 'non-zero exit'}"
        return proc.stdout.strip() or "(empty mcp response)"


def load_mcp_tools(project_dir: Path) -> list[MCPTool]:
    """Read ``.specsmith/mcp.yml`` and return a list of :class:`MCPTool`.

    Returns an empty list when the file is absent or unparseable so the
    rest of the orchestrator continues to function with zero MCP servers
    configured (the default).
    """
    cfg_path = Path(project_dir) / ".specsmith" / "mcp.yml"
    if not cfg_path.is_file():
        return []
    try:
        import yaml

        raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or []
    except Exception:  # noqa: BLE001
        return []
    if not isinstance(raw, list):
        return []

    out: list[MCPTool] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name", "")).strip()
        command = str(entry.get("command", "")).strip()
        if not name or not command:
            continue
        args_raw = entry.get("args", []) or []
        env_raw = entry.get("env", {}) or {}
        spec = MCPServerSpec(
            name=name,
            command=command,
            args=[str(a) for a in args_raw if isinstance(a, (str, int, float))],
            env={str(k): str(v) for k, v in env_raw.items()},
        )
        out.append(MCPTool(spec=spec))
    return out


__all__ = ["MCPServerSpec", "MCPTool", "load_mcp_tools"]
