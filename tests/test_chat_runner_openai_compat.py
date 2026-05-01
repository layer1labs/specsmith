# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""End-to-end test for the BYOE openai-compat driver (REQ-142, PR-2).

Runs an in-process fake ``/chat/completions`` SSE server, wires up an
:class:`Endpoint` pointing at it, and asserts that
:func:`chat_runner.run_chat` streams tokens through the new
``_run_openai_compat`` driver when ``endpoint_id`` is set.
"""

from __future__ import annotations

import http.server
import json
import socket
import threading
from pathlib import Path

import pytest

from specsmith.agent.chat_runner import _run_openai_compat, run_chat
from specsmith.agent.endpoints import Endpoint, EndpointAuth, EndpointStore
from specsmith.agent.events import EventEmitter


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


_REPLY = "Plan:\n- ok\nFiles changed:\n- a.py\nTest results:\nNext action:\n"


class _FakeChatHandler(http.server.BaseHTTPRequestHandler):
    """Streams a canned SSE chat-completions response."""

    expected_token: str | None = None
    last_request_body: dict | None = None

    def log_message(self, *args: object, **kwargs: object) -> None:  # noqa: D401
        return

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self.send_response(404)
            self.end_headers()
            return
        if self.expected_token is not None:
            got = self.headers.get("Authorization", "")
            if got != f"Bearer {self.expected_token}":
                self.send_response(401)
                self.end_headers()
                return
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length).decode("utf-8")
        try:
            _FakeChatHandler.last_request_body = json.loads(body)
        except json.JSONDecodeError:
            _FakeChatHandler.last_request_body = None

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()

        chunks = [_REPLY[i : i + 16] for i in range(0, len(_REPLY), 16)]
        for chunk in chunks:
            payload = json.dumps(
                {
                    "id": "chatcmpl-fake",
                    "object": "chat.completion.chunk",
                    "choices": [{"delta": {"content": chunk}, "index": 0}],
                }
            )
            self.wfile.write(f"data: {payload}\n\n".encode())
            self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


@pytest.fixture
def fake_chat_server() -> object:
    port = _free_port()
    server = http.server.HTTPServer(("127.0.0.1", port), _FakeChatHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield port
    finally:
        server.shutdown()
        server.server_close()
        _FakeChatHandler.expected_token = None
        _FakeChatHandler.last_request_body = None


# ---------------------------------------------------------------------------
# _run_openai_compat — direct
# ---------------------------------------------------------------------------


def test_openai_compat_streams_tokens(fake_chat_server: int) -> None:
    port = fake_chat_server
    emitter = EventEmitter()
    endpoint = Endpoint(
        id="fake",
        name="fake",
        base_url=f"http://127.0.0.1:{port}/v1",
        default_model="fake-model",
    )
    text = _run_openai_compat(
        [{"role": "user", "content": "hello"}], emitter, "block-1", endpoint=endpoint
    )
    assert text is not None
    assert "Files changed" in text
    assert _FakeChatHandler.last_request_body is not None
    assert _FakeChatHandler.last_request_body["model"] == "fake-model"
    assert _FakeChatHandler.last_request_body["stream"] is True


def test_openai_compat_returns_none_without_default_model(fake_chat_server: int) -> None:
    port = fake_chat_server
    emitter = EventEmitter()
    endpoint = Endpoint(
        id="fake",
        name="fake",
        base_url=f"http://127.0.0.1:{port}/v1",
        default_model="",
    )
    text = _run_openai_compat(
        [{"role": "user", "content": "hi"}], emitter, "block-1", endpoint=endpoint
    )
    assert text is None


def test_openai_compat_returns_none_when_unauthorised(fake_chat_server: int) -> None:
    port = fake_chat_server
    _FakeChatHandler.expected_token = "right-token"
    emitter = EventEmitter()
    endpoint = Endpoint(
        id="fake",
        name="fake",
        base_url=f"http://127.0.0.1:{port}/v1",
        default_model="fake-model",
        auth=EndpointAuth(kind="bearer-inline", token="wrong-token"),
    )
    text = _run_openai_compat(
        [{"role": "user", "content": "hi"}], emitter, "block-1", endpoint=endpoint
    )
    assert text is None


# ---------------------------------------------------------------------------
# run_chat with endpoint_id (PR-2 entry point)
# ---------------------------------------------------------------------------


def test_run_chat_with_endpoint_id_routes_to_openai_compat(
    fake_chat_server: int,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    port = fake_chat_server
    monkeypatch.setenv("SPECSMITH_HOME", str(tmp_path))
    # No ANTHROPIC_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY → would otherwise
    # fall back to the auto-detect chain (Ollama may or may not be running).
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    store = EndpointStore.load()
    store.add(
        Endpoint(
            id="fake",
            name="fake",
            base_url=f"http://127.0.0.1:{port}/v1",
            default_model="fake-model",
        )
    )
    store.save()

    emitter = EventEmitter()
    result = run_chat(
        "do something",
        project_dir=tmp_path,
        profile="standard",
        session_id="sess",
        emitter=emitter,
        msg_block="block-1",
        endpoint_id="fake",
    )
    assert result is not None
    assert result.provider == "openai_compat"
    assert "Files changed" in result.raw_text
    assert _FakeChatHandler.last_request_body is not None
    assert _FakeChatHandler.last_request_body["model"] == "fake-model"
