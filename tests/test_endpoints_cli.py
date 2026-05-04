# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""CLI integration tests for `specsmith endpoints` (REQ-142, PR-1)."""

from __future__ import annotations

import http.server
import json
import socket
import threading
from pathlib import Path

import pytest
from click.testing import CliRunner

from specsmith.cli import main


@pytest.fixture(autouse=True)
def _no_auto_update(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPECSMITH_NO_AUTO_UPDATE", "1")
    monkeypatch.setenv("SPECSMITH_PYPI_CHECKED", "1")


@pytest.fixture(autouse=True)
def _isolated_specsmith_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Redirect ``~/.specsmith`` so CLI invocations never touch the real one."""
    monkeypatch.setenv("SPECSMITH_HOME", str(tmp_path))


def _runner_invoke(*args: str) -> object:
    return CliRunner().invoke(main, list(args))


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class _FakeModelsHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args: object, **kwargs: object) -> None:  # noqa: D401
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/v1/models":
            body = json.dumps(
                {"object": "list", "data": [{"id": "fake-1"}, {"id": "fake-2"}]}
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


@pytest.fixture
def fake_endpoint_server() -> object:
    port = _free_port()
    server = http.server.HTTPServer(("127.0.0.1", port), _FakeModelsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield port
    finally:
        server.shutdown()
        server.server_close()


def test_endpoints_help_lists_subcommands() -> None:
    res = _runner_invoke("endpoints", "--help")
    assert res.exit_code == 0
    for sub in ("add", "list", "remove", "default", "test", "models"):
        assert sub in res.output


def test_endpoints_add_and_list_round_trip(tmp_path: Path) -> None:
    res = _runner_invoke(
        "endpoints",
        "add",
        "--id",
        "home-vllm",
        "--name",
        "Home vLLM",
        "--base-url",
        "http://10.0.0.4:8000/v1",
        "--default-model",
        "qwen-coder",
        "--auth",
        "none",
        "--json",
    )
    assert res.exit_code == 0, res.output
    payload = json.loads(res.output)
    assert payload["endpoint"]["id"] == "home-vllm"
    assert payload["default"] == "home-vllm"

    list_res = _runner_invoke("endpoints", "list", "--json")
    assert list_res.exit_code == 0
    listed = json.loads(list_res.output)
    assert listed["default_endpoint_id"] == "home-vllm"
    assert listed["endpoints"][0]["id"] == "home-vllm"
    # token must never leak even when no token was provided
    assert "token" not in json.dumps(listed) or listed["endpoints"][0]["auth"]["kind"] == "none"


def test_endpoints_add_inline_token_redacts_in_list_output() -> None:
    add_res = _runner_invoke(
        "endpoints",
        "add",
        "--id",
        "secured",
        "--name",
        "Secured",
        "--base-url",
        "https://lan.example.com/v1",
        "--auth",
        "bearer-inline",
        "--token",
        "sk-supersecret",
        "--json",
    )
    assert add_res.exit_code == 0, add_res.output

    list_res = _runner_invoke("endpoints", "list", "--json")
    assert list_res.exit_code == 0
    body = list_res.output
    assert "sk-supersecret" not in body
    parsed = json.loads(body)
    assert parsed["endpoints"][0]["auth"]["token"] == "***"


def test_endpoints_add_duplicate_id_exits_2() -> None:
    base_args = [
        "endpoints",
        "add",
        "--id",
        "dup",
        "--name",
        "d",
        "--base-url",
        "http://e/v1",
    ]
    first = _runner_invoke(*base_args)
    assert first.exit_code == 0
    second = _runner_invoke(*base_args)
    assert second.exit_code == 2
    assert "already exists" in second.output


def test_endpoints_add_invalid_url_exits_2() -> None:
    res = _runner_invoke(
        "endpoints",
        "add",
        "--id",
        "bad",
        "--name",
        "bad",
        "--base-url",
        "ftp://nope/v1",
    )
    assert res.exit_code == 2
    assert "http://" in res.output


def test_endpoints_remove_unknown_exits_1() -> None:
    res = _runner_invoke("endpoints", "remove", "ghost")
    assert res.exit_code == 1
    assert "unknown endpoint" in res.output


def test_endpoints_default_unknown_exits_1() -> None:
    res = _runner_invoke("endpoints", "default", "ghost")
    assert res.exit_code == 1
    assert "unknown endpoint" in res.output


def test_endpoints_default_promotes_existing() -> None:
    _runner_invoke("endpoints", "add", "--id", "a", "--name", "a", "--base-url", "http://e/v1")
    _runner_invoke("endpoints", "add", "--id", "b", "--name", "b", "--base-url", "http://e/v1")
    res = _runner_invoke("endpoints", "default", "b")
    assert res.exit_code == 0
    listed = json.loads(_runner_invoke("endpoints", "list", "--json").output)
    assert listed["default_endpoint_id"] == "b"


def test_endpoints_test_against_fake_server(fake_endpoint_server: int) -> None:
    port = fake_endpoint_server
    add = _runner_invoke(
        "endpoints",
        "add",
        "--id",
        "fake",
        "--name",
        "fake",
        "--base-url",
        f"http://127.0.0.1:{port}/v1",
    )
    assert add.exit_code == 0, add.output

    res = _runner_invoke("endpoints", "test", "fake", "--json", "--timeout", "2")
    assert res.exit_code == 0, res.output
    payload = json.loads(res.output)
    assert payload["ok"] is True
    assert "fake-1" in payload["models"]


def test_endpoints_models_against_fake_server(fake_endpoint_server: int) -> None:
    port = fake_endpoint_server
    _runner_invoke(
        "endpoints",
        "add",
        "--id",
        "fake",
        "--name",
        "fake",
        "--base-url",
        f"http://127.0.0.1:{port}/v1",
    )
    res = _runner_invoke("endpoints", "models", "fake", "--json")
    assert res.exit_code == 0
    payload = json.loads(res.output)
    assert payload["models"] == ["fake-1", "fake-2"]


def test_endpoints_test_unreachable_exits_1() -> None:
    _runner_invoke(
        "endpoints",
        "add",
        "--id",
        "ghost",
        "--name",
        "ghost",
        "--base-url",
        "http://127.0.0.1:1/v1",
    )
    res = _runner_invoke("endpoints", "test", "ghost", "--json", "--timeout", "0.5")
    assert res.exit_code == 1
    payload = json.loads(res.output)
    assert payload["ok"] is False
    assert payload["error"]
