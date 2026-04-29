# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Reference cloud-agent receiver for `specsmith cloud spawn` (REQ-136).

A minimal stdlib HTTP server that accepts manifest-only POSTs at ``/spawn``
and acks them. The full streaming-back-of-results contract is documented
but kept narrow (and intentionally local-only) so we ship a working
endpoint without baking in vendor coupling.

Auth model: optional ``Authorization: Bearer <token>``. When the server
is started with ``--token``, every request must present it.
Defense-in-depth: the server refuses to bind to any address other than
``127.0.0.1`` unless explicitly given ``--host`` AND ``--allow-cidr``.
"""

from __future__ import annotations

import ipaddress
import json
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any


@dataclass
class CloudReceiverConfig:
    host: str = "127.0.0.1"
    port: int = 9000
    token: str = ""
    allow_cidr: str = ""
    storage_dir: Path = field(default_factory=lambda: Path.home() / ".specsmith" / "cloud-runs")


class _Handler(BaseHTTPRequestHandler):
    config: CloudReceiverConfig = CloudReceiverConfig()

    # noqa: N802 -- BaseHTTPRequestHandler API.
    def do_POST(self) -> None:  # noqa: N802
        if not self._authorize():
            self._respond(401, {"error": "unauthorized"})
            return
        if self.path != "/spawn":
            self._respond(404, {"error": f"unknown path {self.path}"})
            return
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except ValueError:
            self._respond(400, {"error": "invalid json"})
            return
        run_id = str(payload.get("run_id", "")).strip() or _new_run_id()
        target = self.config.storage_dir / run_id
        try:
            target.mkdir(parents=True, exist_ok=True)
            (target / "manifest.json").write_text(
                json.dumps(payload, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            self._respond(500, {"error": f"storage failed: {exc}"})
            return
        self._respond(
            202,
            {
                "run_id": run_id,
                "status": "accepted",
                "stream_url": f"/runs/{run_id}/events",
            },
        )

    def do_GET(self) -> None:  # noqa: N802
        if not self._authorize():
            self._respond(401, {"error": "unauthorized"})
            return
        if self.path == "/health":
            self._respond(200, {"ok": True})
            return
        self._respond(404, {"error": f"unknown path {self.path}"})

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        # Quiet by default — caller sees JSON responses.
        return

    # ── helpers ───────────────────────────────────────────────────────────

    def _authorize(self) -> bool:
        if self.config.token:
            header = self.headers.get("Authorization", "")
            if header != f"Bearer {self.config.token}":
                return False
        if self.config.allow_cidr:
            try:
                net = ipaddress.ip_network(self.config.allow_cidr, strict=False)
                client = ipaddress.ip_address(self.client_address[0])
                if client not in net:
                    return False
            except (ValueError, TypeError):
                return False
        return True

    def _respond(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _new_run_id() -> str:
    import uuid

    return f"cloud_{uuid.uuid4().hex[:12]}"


def _validate_host(config: CloudReceiverConfig) -> None:
    if config.host not in {"127.0.0.1", "::1", "localhost"} and not config.allow_cidr:
        raise RuntimeError(
            "specsmith cloud serve refuses to bind to a non-loopback address "
            "unless --allow-cidr is also set. This is a security guardrail."
        )


def make_server(config: CloudReceiverConfig) -> HTTPServer:
    _validate_host(config)
    config.storage_dir.mkdir(parents=True, exist_ok=True)

    class _Bound(_Handler):
        pass

    _Bound.config = config
    return HTTPServer((config.host, config.port), _Bound)


def run_in_thread(config: CloudReceiverConfig) -> tuple[HTTPServer, threading.Thread]:
    """Start the server in a background thread; useful for tests."""
    server = make_server(config)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


__all__ = [
    "CloudReceiverConfig",
    "make_server",
    "run_in_thread",
]
