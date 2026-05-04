# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Unit tests for ``specsmith.agent.endpoints`` (REQ-142, PR-1).

Covers the pure data layer: validation, JSON persistence, redaction, token
resolution dispatch, and the ``/models`` health probe parser. The CLI
group is exercised in ``tests/test_endpoints_cli.py``.
"""

from __future__ import annotations

import http.server
import json
import socket
import threading
from pathlib import Path

import pytest

from specsmith.agent.endpoints import (
    SCHEMA_VERSION,
    Endpoint,
    EndpointAuth,
    EndpointError,
    EndpointHealth,
    EndpointStore,
    _extract_model_ids,
    default_store_path,
)

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_validate_rejects_empty_id() -> None:
    e = Endpoint(id="", name="x", base_url="http://example.com/v1")
    with pytest.raises(EndpointError, match="non-empty"):
        e.validate()


def test_validate_rejects_whitespace_id() -> None:
    e = Endpoint(id="my endpoint", name="x", base_url="http://example.com/v1")
    with pytest.raises(EndpointError, match="whitespace"):
        e.validate()


def test_validate_rejects_non_http_scheme() -> None:
    e = Endpoint(id="x", name="x", base_url="ftp://example.com/v1")
    with pytest.raises(EndpointError, match="http://"):
        e.validate()


def test_validate_requires_token_env_for_bearer_env() -> None:
    e = Endpoint(
        id="x",
        name="x",
        base_url="http://e/v1",
        auth=EndpointAuth(kind="bearer-env", token_env=""),
    )
    with pytest.raises(EndpointError, match="token_env"):
        e.validate()


def test_validate_requires_keyring_user_for_bearer_keyring() -> None:
    e = Endpoint(
        id="x",
        name="x",
        base_url="http://e/v1",
        auth=EndpointAuth(kind="bearer-keyring", keyring_user=""),
    )
    with pytest.raises(EndpointError, match="keyring_user"):
        e.validate()


# ---------------------------------------------------------------------------
# Round-trip + redaction
# ---------------------------------------------------------------------------


def test_to_public_dict_redacts_inline_token() -> None:
    e = Endpoint(
        id="vllm",
        name="vllm",
        base_url="http://10.0.0.4:8000/v1",
        auth=EndpointAuth(kind="bearer-inline", token="sk-supersecret"),
    )
    public = e.to_public_dict()
    assert public["auth"]["kind"] == "bearer-inline"
    assert public["auth"]["token"] == "***"
    assert "sk-supersecret" not in json.dumps(public)


def test_store_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "endpoints.json"
    store = EndpointStore(path=path)
    store.add(
        Endpoint(
            id="home-vllm",
            name="Home vLLM",
            base_url="http://10.0.0.4:8000/v1",
            default_model="qwen-coder",
            tags=["local", "coder"],
        )
    )
    store.save()

    reloaded = EndpointStore.load(path)
    assert reloaded.schema_version == SCHEMA_VERSION
    assert reloaded.default_endpoint_id == "home-vllm"
    assert len(reloaded.endpoints) == 1
    e = reloaded.endpoints[0]
    assert e.base_url == "http://10.0.0.4:8000/v1"
    assert e.default_model == "qwen-coder"
    assert e.tags == ["local", "coder"]
    assert e.created_at  # auto-stamped


def test_store_load_returns_empty_when_missing(tmp_path: Path) -> None:
    path = tmp_path / "absent.json"
    store = EndpointStore.load(path)
    assert store.endpoints == []
    assert store.default_endpoint_id == ""


def test_store_load_rejects_corrupt_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(EndpointError, match="corrupted"):
        EndpointStore.load(path)


def test_store_load_rejects_wrong_schema(tmp_path: Path) -> None:
    path = tmp_path / "v999.json"
    path.write_text(json.dumps({"schema_version": 999, "endpoints": []}), encoding="utf-8")
    with pytest.raises(EndpointError, match="schema_version=999"):
        EndpointStore.load(path)


def test_store_add_blocks_duplicates_without_replace(tmp_path: Path) -> None:
    store = EndpointStore(path=tmp_path / "x.json")
    store.add(Endpoint(id="dup", name="d", base_url="http://e/v1"))
    with pytest.raises(EndpointError, match="already exists"):
        store.add(Endpoint(id="dup", name="d", base_url="http://e/v1"))


def test_store_add_replace_overwrites(tmp_path: Path) -> None:
    store = EndpointStore(path=tmp_path / "x.json")
    store.add(Endpoint(id="dup", name="orig", base_url="http://e/v1"))
    store.add(
        Endpoint(id="dup", name="new", base_url="http://e/v1", default_model="m"),
        replace=True,
    )
    assert store.get("dup").name == "new"
    assert store.get("dup").default_model == "m"


def test_remove_clears_default(tmp_path: Path) -> None:
    store = EndpointStore(path=tmp_path / "x.json")
    store.add(Endpoint(id="a", name="a", base_url="http://e/v1"))
    store.add(Endpoint(id="b", name="b", base_url="http://e/v1"))
    assert store.default_endpoint_id == "a"
    store.remove("a")
    # Falls back to the next endpoint in the list, not empty.
    assert store.default_endpoint_id == "b"
    store.remove("b")
    assert store.default_endpoint_id == ""


def test_resolve_uses_default(tmp_path: Path) -> None:
    store = EndpointStore(path=tmp_path / "x.json")
    store.add(Endpoint(id="a", name="a", base_url="http://e/v1"))
    assert store.resolve(None).id == "a"


def test_resolve_raises_when_no_default(tmp_path: Path) -> None:
    store = EndpointStore(path=tmp_path / "x.json")
    with pytest.raises(EndpointError, match="no endpoint specified"):
        store.resolve(None)


def test_set_default_rejects_unknown(tmp_path: Path) -> None:
    store = EndpointStore(path=tmp_path / "x.json")
    with pytest.raises(EndpointError, match="unknown endpoint"):
        store.set_default("ghost")


def test_default_store_path_honours_specsmith_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("SPECSMITH_HOME", str(tmp_path))
    assert default_store_path() == tmp_path / "endpoints.json"


# ---------------------------------------------------------------------------
# Token resolution
# ---------------------------------------------------------------------------


def test_resolve_token_none_returns_none() -> None:
    e = Endpoint(id="x", name="x", base_url="http://e/v1")
    assert e.resolve_token() is None


def test_resolve_token_bearer_inline_returns_value() -> None:
    e = Endpoint(
        id="x",
        name="x",
        base_url="http://e/v1",
        auth=EndpointAuth(kind="bearer-inline", token="sk-abc"),
    )
    assert e.resolve_token() == "sk-abc"


def test_resolve_token_bearer_env_reads_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MY_VLLM_TOKEN", "lan-token")
    e = Endpoint(
        id="x",
        name="x",
        base_url="http://e/v1",
        auth=EndpointAuth(kind="bearer-env", token_env="MY_VLLM_TOKEN"),
    )
    assert e.resolve_token() == "lan-token"


def test_resolve_token_bearer_env_raises_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ABSENT_TOKEN", raising=False)
    e = Endpoint(
        id="x",
        name="x",
        base_url="http://e/v1",
        auth=EndpointAuth(kind="bearer-env", token_env="ABSENT_TOKEN"),
    )
    with pytest.raises(EndpointError, match="ABSENT_TOKEN"):
        e.resolve_token()


# ---------------------------------------------------------------------------
# /models parser
# ---------------------------------------------------------------------------


def test_extract_model_ids_handles_openai_shape() -> None:
    payload = {"object": "list", "data": [{"id": "m1"}, {"id": "m2"}]}
    assert _extract_model_ids(payload) == ["m1", "m2"]


def test_extract_model_ids_handles_models_array_shape() -> None:
    payload = {"models": ["a", "b"]}
    assert _extract_model_ids(payload) == ["a", "b"]


def test_extract_model_ids_returns_empty_for_unrecognised_payload() -> None:
    assert _extract_model_ids({"unexpected": True}) == []
    assert _extract_model_ids("not a dict") == []


# ---------------------------------------------------------------------------
# health() against an in-process fake /v1/models server
# ---------------------------------------------------------------------------


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class _FakeModelsHandler(http.server.BaseHTTPRequestHandler):
    """Serves OpenAI-shape /v1/models payloads for health() tests."""

    expected_token: str | None = None  # set per-test via class attribute

    def log_message(self, *args: object, **kwargs: object) -> None:  # noqa: D401
        # Quiet the test runner.
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/v1/models":
            self.send_response(404)
            self.end_headers()
            return
        if self.expected_token is not None:
            got = self.headers.get("Authorization", "")
            if got != f"Bearer {self.expected_token}":
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b'{"error": "unauthorized"}')
                return
        body = json.dumps(
            {"object": "list", "data": [{"id": "fake-model-1"}, {"id": "fake-model-2"}]}
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def fake_models_server() -> object:
    port = _free_port()
    server = http.server.HTTPServer(("127.0.0.1", port), _FakeModelsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield port
    finally:
        server.shutdown()
        server.server_close()


def test_health_against_fake_server_lists_models(fake_models_server: int) -> None:
    port = fake_models_server
    e = Endpoint(id="fake", name="fake", base_url=f"http://127.0.0.1:{port}/v1")
    health = e.health(timeout=2.0)
    assert isinstance(health, EndpointHealth)
    assert health.ok
    assert health.status_code == 200
    assert "fake-model-1" in health.models


def test_health_against_unauthenticated_request_returns_401(
    fake_models_server: int,
) -> None:
    port = fake_models_server
    _FakeModelsHandler.expected_token = "right-token"
    try:
        e = Endpoint(
            id="fake",
            name="fake",
            base_url=f"http://127.0.0.1:{port}/v1",
            auth=EndpointAuth(kind="bearer-inline", token="wrong-token"),
        )
        health = e.health(timeout=2.0)
        assert not health.ok
        assert health.status_code == 401
    finally:
        _FakeModelsHandler.expected_token = None


def test_health_against_unreachable_endpoint_returns_error() -> None:
    e = Endpoint(id="ghost", name="ghost", base_url="http://127.0.0.1:1/v1")
    health = e.health(timeout=0.5)
    assert not health.ok
    assert health.error
