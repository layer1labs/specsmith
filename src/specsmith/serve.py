# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""specsmith serve — persistent HTTP server for agent sessions.

Replaces the stdio-based ``specsmith run --json-events`` with an HTTP
server that can be connected to by multiple clients (VS Code, browser,
scripts) without restarting the Python process or cold-loading the
Ollama model.

Endpoints:
    POST /api/send          — send a user message (body: {"text": "..."})
    GET  /api/events        — SSE stream of JSONL events
    GET  /api/status        — session state JSON
    POST /api/stop          — stop the current turn
    GET  /api/health        — liveness probe

Launch:
    specsmith serve --port 8421 --project-dir .
"""

from __future__ import annotations

import contextlib
import json
import queue
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any


class _ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Non-blocking HTTP server (one thread per request)."""

    daemon_threads = True
    allow_reuse_address = True


class _EventBus:
    """Thread-safe event bus — the agent thread pushes events, SSE
    clients consume them.  Supports multiple concurrent SSE listeners."""

    def __init__(self) -> None:
        self._listeners: list[queue.Queue[dict[str, Any] | None]] = []
        self._lock = threading.Lock()

    def subscribe(self) -> queue.Queue[dict[str, Any] | None]:
        q: queue.Queue[dict[str, Any] | None] = queue.Queue(maxsize=512)
        with self._lock:
            self._listeners.append(q)
        return q

    def unsubscribe(self, q: queue.Queue[dict[str, Any] | None]) -> None:
        with self._lock, contextlib.suppress(ValueError):
            self._listeners.remove(q)

    def emit(self, event: dict[str, Any]) -> None:
        with self._lock:
            for q in self._listeners:
                with contextlib.suppress(queue.Full):
                    q.put_nowait(event)


class _AgentThread:
    """Wraps AgentRunner in a background thread with message passing."""

    def __init__(
        self,
        project_dir: str,
        provider: str,
        model: str,
        bus: _EventBus,
    ) -> None:
        self._project_dir = project_dir
        self._provider = provider
        self._model = model
        self._bus = bus
        self._inbox: queue.Queue[str | None] = queue.Queue()
        self._runner: Any = None
        self._thread: threading.Thread | None = None
        self._started = False

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True, name="agent")
        self._thread.start()

    def send(self, text: str) -> None:
        self._inbox.put(text)

    def stop_turn(self) -> None:
        """Interrupt the current agent turn (best-effort)."""
        # The runner checks a flag between tool calls
        if self._runner:
            self._runner._hard_stop = True  # noqa: SLF001

    def status(self) -> dict[str, Any]:
        if not self._runner:
            return {"status": "starting"}
        st = self._runner._state  # noqa: SLF001
        return {
            "status": "running" if self._started else "starting",
            "provider": st.provider_name,
            "model": st.model_name,
            "tokens": st.session_tokens,
            "cost_usd": st.total_cost_usd,
            "tool_calls": st.tool_calls_made,
            "elapsed_min": round(st.elapsed_minutes, 1),
        }

    def _run(self) -> None:
        """Agent loop — runs in a background thread."""
        try:
            from specsmith.agent.runner import AgentRunner

            self._runner = AgentRunner(
                project_dir=self._project_dir,
                provider_name=self._provider,
                model=self._model,
                json_events=True,
            )

            # Monkey-patch _emit_event to route through the bus

            def _bus_emit(**kwargs: Any) -> None:
                self._bus.emit(kwargs)

            self._runner._emit_event = _bus_emit  # noqa: SLF001

            # Print banner (emits 'ready' event)
            self._runner._print_banner()  # noqa: SLF001
            self._started = True

            # Main loop: read from inbox, dispatch to runner
            while True:
                text = self._inbox.get()
                if text is None:
                    break  # shutdown signal
                try:
                    self._runner._handle_command(text)  # noqa: SLF001
                except Exception as e:  # noqa: BLE001
                    self._bus.emit({"type": "error", "message": str(e)})
                self._bus.emit({"type": "turn_done"})
        except Exception as e:  # noqa: BLE001
            self._bus.emit({"type": "error", "message": f"Agent crashed: {e}"})
        finally:
            self._bus.emit({"type": "system", "message": "Agent thread ended."})


class _Handler(BaseHTTPRequestHandler):
    """HTTP request handler for the serve endpoints."""

    bus: _EventBus
    agent: _AgentThread
    auth_token: str = ""  # populated by run_server / make_server when set

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        """Suppress default stderr logging."""

    # ── Auth ─────────────────────────────────────────────────────────
    # REQ-137: when run_server is started with --auth-token, every
    # request must present `Authorization: Bearer <token>`. /api/health
    # is the only unauthenticated endpoint so liveness probes still
    # work behind a load balancer that strips Authorization.
    def _authorize(self) -> bool:
        token = type(self).auth_token
        if not token:
            return True
        if self.path == "/api/health":
            return True
        header = self.headers.get("Authorization", "")
        return header == f"Bearer {token}"

    def do_GET(self) -> None:  # noqa: N802
        if not self._authorize():
            self._json_response({"error": "unauthorized"}, code=401)
            return
        if self.path == "/api/events":
            self._sse()
        elif self.path == "/api/status":
            self._json_response(self.agent.status())
        elif self.path == "/api/health":
            self._json_response({"ok": True})
        else:
            self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        if not self._authorize():
            self._json_response({"error": "unauthorized"}, code=401)
            return
        if self.path == "/api/send":
            body = self._read_json()
            text = body.get("text", "").strip() if body else ""
            if not text:
                self._json_response({"error": "missing text"}, code=400)
                return
            self.agent.send(text)
            self._json_response({"ok": True})
        elif self.path == "/api/stop":
            self.agent.stop_turn()
            self._json_response({"ok": True})
        else:
            self.send_error(404)

    def do_DELETE(self) -> None:  # noqa: N802
        if not self._authorize():
            self._json_response({"error": "unauthorized"}, code=401)
            return
        if self.path == "/api/session":
            self.agent.send(None)  # type: ignore[arg-type]
            self._json_response({"ok": True, "message": "session ending"})
        else:
            self.send_error(404)

    # ── SSE ────────────────────────────────────────────────────────

    def _sse(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        q = self.bus.subscribe()
        try:
            while True:
                try:
                    event = q.get(timeout=30)
                except queue.Empty:
                    # Send SSE comment as keepalive
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                    continue
                if event is None:
                    break
                data = json.dumps(event, ensure_ascii=False)
                self.wfile.write(f"data: {data}\n\n".encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass  # client disconnected
        finally:
            self.bus.unsubscribe(q)

    # ── Helpers ────────────────────────────────────────────────────

    def _read_json(self) -> dict[str, Any] | None:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return None
        raw = self.rfile.read(length)
        try:
            result: dict[str, Any] = json.loads(raw)
            return result
        except json.JSONDecodeError:
            return None

    def _json_response(
        self,
        data: dict[str, Any],
        code: int = 200,
    ) -> None:
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def make_server(
    *,
    project_dir: str = ".",
    provider: str = "ollama",
    model: str = "",
    port: int = 8421,
    host: str = "127.0.0.1",
    auth_token: str = "",
) -> tuple[_ThreadedHTTPServer, _AgentThread]:
    """Build the HTTP server + agent thread without serving yet.

    Used by tests so they can drive a fresh server inside the same
    process. Production callers go through ``run_server`` which adds
    the banner + serve_forever loop.
    """
    project_dir = str(Path(project_dir).resolve())
    bus = _EventBus()
    agent = _AgentThread(project_dir, provider, model, bus)

    class Handler(_Handler):
        pass

    Handler.bus = bus
    Handler.agent = agent
    Handler.auth_token = auth_token

    server = _ThreadedHTTPServer((host, port), Handler)
    return server, agent


def run_server(
    *,
    project_dir: str = ".",
    provider: str = "ollama",
    model: str = "",
    port: int = 8421,
    host: str = "127.0.0.1",
    auth_token: str = "",
) -> None:
    """Start the specsmith HTTP server."""
    server, agent = make_server(
        project_dir=project_dir,
        provider=provider,
        model=model,
        port=port,
        host=host,
        auth_token=auth_token,
    )
    agent.start()

    auth_note = "  Auth:     bearer-token required\n" if auth_token else ""
    print(  # noqa: T201
        f"specsmith serve — http://{host}:{port}\n"
        f"  Project:  {project_dir}\n"
        f"  Provider: {provider}/{model or '(default)'}\n"
        f"{auth_note}"
        f"  Endpoints:\n"
        f"    GET  /api/events  — SSE event stream\n"
        f"    POST /api/send    — send a message\n"
        f"    GET  /api/status  — session status\n"
        f"    POST /api/stop    — stop current turn\n"
        f"    GET  /api/health  — unauthenticated liveness\n"
        f"  Press Ctrl+C to stop.\n",
        file=sys.stderr,
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        agent.send(None)  # type: ignore[arg-type]
        server.shutdown()
