# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Real MCP (Model Context Protocol) client for Nexus (REQ-121, REQ-130).

Replaces the prior loader-only stub with a working JSON-RPC 2.0 client
that drives the official MCP handshake over stdio:

* ``initialize`` request -> response (capability negotiation).
* ``notifications/initialized`` notification.
* ``tools/list`` request -> response (tool catalog discovery).
* ``tools/call`` requests -> responses (per-tool invocation).

The Specsmith safety middleware still wraps every call: see
``MCPTool.invoke_with_safety``. Servers configured via ``.specsmith/mcp.yml``
are listed at the top of every ``specsmith chat`` session and exposed to
the orchestrator as additional Nexus tools.

Protocol pin: 2024-11-05 (current stable). Servers that advertise a newer
version still work because MCP guarantees backwards compatibility within
the same major track.
"""

from __future__ import annotations

import contextlib
import json
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MCP_PROTOCOL_VERSION = "2024-11-05"
DEFAULT_REQUEST_TIMEOUT = 30.0


@dataclass
class MCPServerSpec:
    """Static configuration for an MCP server (mirrors `.specsmith/mcp.yml`)."""

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class MCPToolDescriptor:
    """One tool advertised by an MCP server's ``tools/list`` response."""

    name: str
    description: str
    input_schema: dict[str, Any]
    server_name: str


class MCPError(RuntimeError):
    """Raised on transport or JSON-RPC errors from an MCP server."""

    def __init__(self, *, code: int, message: str, data: Any = None) -> None:
        super().__init__(f"MCP error {code}: {message}")
        self.code = code
        self.detail = message
        self.data = data


class MCPSession:
    """One stdio-attached MCP server with full JSON-RPC framing.

    The session owns the subprocess lifecycle. ``open()`` performs the
    initialize handshake and discovery; ``call_tool()`` drives ``tools/call``;
    ``close()`` flushes pending requests and terminates the child.
    Concurrent calls into a single session are not supported (one in-flight
    request at a time, matching the stdio MCP transport model).
    """

    def __init__(self, spec: MCPServerSpec) -> None:
        self.spec = spec
        self._proc: subprocess.Popen[bytes] | None = None
        self._next_id = 1
        self._lock = threading.Lock()
        self._tools: list[MCPToolDescriptor] = []
        self._closed = False

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def open(self, *, timeout: float = DEFAULT_REQUEST_TIMEOUT) -> list[MCPToolDescriptor]:
        """Spawn the server, run the initialize handshake, return discovered tools."""
        env = {**self.spec.env}
        self._proc = subprocess.Popen(  # noqa: S603 - argv is user-configured
            [self.spec.command, *self.spec.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env or None,
            bufsize=0,
        )
        self._request(
            "initialize",
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "specsmith", "version": "0"},
            },
            timeout=timeout,
        )
        # Per spec: send notifications/initialized after a successful initialize.
        self._notify("notifications/initialized", {})
        result = self._request("tools/list", {}, timeout=timeout)
        raw_tools = result.get("tools", []) if isinstance(result, dict) else []
        self._tools = []
        for entry in raw_tools:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            if not name:
                continue
            schema = entry.get("inputSchema", {})
            self._tools.append(
                MCPToolDescriptor(
                    name=str(name),
                    description=str(entry.get("description", "")),
                    input_schema=schema if isinstance(schema, dict) else {},
                    server_name=self.spec.name,
                )
            )
        return list(self._tools)

    def close(self) -> None:
        """Terminate the server. Idempotent."""
        if self._closed:
            return
        self._closed = True
        if self._proc is None:
            return
        try:
            if self._proc.stdin and not self._proc.stdin.closed:
                self._proc.stdin.close()
        except OSError:
            pass
        try:
            self._proc.terminate()
            self._proc.wait(timeout=2.0)
        except (OSError, subprocess.TimeoutExpired):
            with contextlib.suppress(OSError):
                self._proc.kill()

    # ── Public API ────────────────────────────────────────────────────────

    @property
    def tools(self) -> list[MCPToolDescriptor]:
        """Return the catalog discovered during ``open()``."""
        return list(self._tools)

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        *,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
    ) -> str:
        """Invoke ``tools/call`` and return a flat string result.

        MCP returns content blocks; we concatenate text blocks and report
        non-text blocks descriptively so downstream consumers can render a
        single string.
        """
        params: dict[str, Any] = {"name": name}
        if arguments:
            params["arguments"] = arguments
        result = self._request("tools/call", params, timeout=timeout)
        if not isinstance(result, dict):
            return str(result)
        if result.get("isError"):
            return f"mcp error: {_format_content(result.get('content', []))}"
        return _format_content(result.get("content", []))

    # ── JSON-RPC framing ──────────────────────────────────────────────────

    def _request(
        self,
        method: str,
        params: dict[str, Any],
        *,
        timeout: float,
    ) -> Any:
        with self._lock:
            req_id = self._next_id
            self._next_id += 1
            self._send({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})
            response = self._read_response_for(req_id, timeout)
        if "error" in response:
            err = response["error"]
            raise MCPError(
                code=int(err.get("code", -1)),
                message=str(err.get("message", "(no message)")),
                data=err.get("data"),
            )
        return response.get("result", {})

    def _notify(self, method: str, params: dict[str, Any]) -> None:
        with self._lock:
            self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def _send(self, payload: dict[str, Any]) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise MCPError(code=-32000, message="server not open")
        line = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        try:
            self._proc.stdin.write(line)
            self._proc.stdin.flush()
        except (OSError, BrokenPipeError) as exc:
            raise MCPError(code=-32001, message=f"send failed: {exc}") from exc

    def _read_response_for(self, req_id: int, timeout: float) -> dict[str, Any]:
        if self._proc is None or self._proc.stdout is None:
            raise MCPError(code=-32000, message="server not open")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            line = self._proc.stdout.readline()
            if not line:
                stderr_tail = b""
                if self._proc.stderr is not None:
                    try:
                        stderr_tail = self._proc.stderr.read() or b""
                    except OSError:
                        stderr_tail = b""
                raise MCPError(
                    code=-32002,
                    message=f"mcp server closed: {stderr_tail.decode('utf-8', 'replace').strip()}",
                )
            try:
                msg = json.loads(line.decode("utf-8", "replace"))
            except ValueError:
                continue
            if not isinstance(msg, dict):
                continue
            if msg.get("id") == req_id:
                return msg
        raise MCPError(code=-32003, message=f"timeout waiting for response to id={req_id}")


def _format_content(blocks: Any) -> str:
    """Concatenate MCP content blocks into a single human-readable string."""
    if not isinstance(blocks, list):
        return str(blocks)
    parts: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        kind = block.get("type", "")
        if kind == "text":
            parts.append(str(block.get("text", "")))
        elif kind == "image":
            parts.append(f"[image: {block.get('mimeType', 'unknown')}]")
        elif kind == "resource":
            uri = (block.get("resource") or {}).get("uri", "?")
            parts.append(f"[resource: {uri}]")
        else:
            parts.append(f"[unknown block: {kind}]")
    return "\n".join(parts) if parts else "(empty mcp response)"


@dataclass
class MCPTool:
    """A Nexus-side handle that wraps one descriptor + an open session."""

    descriptor: MCPToolDescriptor
    session: MCPSession

    @property
    def name(self) -> str:
        return self.descriptor.name

    @property
    def server(self) -> str:
        return self.descriptor.server_name

    @property
    def description(self) -> str:
        return self.descriptor.description

    @property
    def spec(self) -> MCPServerSpec:
        """Back-compat shim — older callers expect a `.spec` attribute."""
        return self.session.spec

    def invoke(self, arguments: dict[str, Any] | None = None) -> str:
        """Direct invocation (no safety middleware)."""
        return self.session.call_tool(self.descriptor.name, arguments)

    def invoke_with_safety(
        self,
        arguments: dict[str, Any] | None,
        safety_check: Callable[[str, dict[str, Any]], tuple[bool, str]] | None,
    ) -> str:
        """Invoke after running the supplied safety check.

        The check returns ``(allowed, reason)``. When disallowed, the call
        is not made and a redacted error string is returned.
        """
        if safety_check is not None:
            allowed, reason = safety_check(self.descriptor.name, arguments or {})
            if not allowed:
                return f"mcp blocked by safety: {reason}"
        return self.invoke(arguments or None)


# ── Loader-style helpers (back-compat with prior callers) ────────────────


def _read_specs(project_dir: Path) -> list[MCPServerSpec]:
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
    out: list[MCPServerSpec] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name", "")).strip()
        command = str(entry.get("command", "")).strip()
        if not name or not command:
            continue
        args_raw = entry.get("args", []) or []
        env_raw = entry.get("env", {}) or {}
        out.append(
            MCPServerSpec(
                name=name,
                command=command,
                args=[str(a) for a in args_raw if isinstance(a, (str, int, float))],
                env={str(k): str(v) for k, v in env_raw.items()},
            )
        )
    return out


def load_mcp_tools(project_dir: Path) -> list[MCPTool]:
    """Open every configured MCP server and return its tools (back-compat).

    Servers that fail to open are silently skipped. Returns an empty list
    when no servers are configured. The underlying sessions remain open
    until the process exits — convenient for one-shot scripts and tests.
    Long-running consumers should prefer :func:`open_mcp_sessions` and
    explicitly ``close()`` each session.
    """
    sessions = open_mcp_sessions(project_dir)
    out: list[MCPTool] = []
    for session in sessions:
        for descriptor in session.tools:
            out.append(MCPTool(descriptor=descriptor, session=session))
    return out


def open_mcp_sessions(project_dir: Path) -> list[MCPSession]:
    """Open all configured MCP sessions and return them. Caller owns close."""
    out: list[MCPSession] = []
    for spec in _read_specs(project_dir):
        session = MCPSession(spec)
        try:
            session.open()
        except (OSError, MCPError):
            session.close()
            continue
        out.append(session)
    return out


__all__ = [
    "MCP_PROTOCOL_VERSION",
    "MCPError",
    "MCPServerSpec",
    "MCPSession",
    "MCPTool",
    "MCPToolDescriptor",
    "load_mcp_tools",
    "open_mcp_sessions",
]
