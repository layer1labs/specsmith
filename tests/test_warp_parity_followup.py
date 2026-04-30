# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Warp parity follow-up tests.

Covers:
* serve --auth-token (REQ-137)
* cloud spawn client (REQ-136)
* voice transcription wrapper (REQ-141)
* api-surface stability snapshot (REQ-140)
"""

from __future__ import annotations

import json
import socket
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from click.testing import CliRunner

from specsmith.agent.voice import (
    TranscribeResult,
    VoiceUnavailableError,
    is_available,
    transcribe,
)
from specsmith.cli import main
from specsmith.cloud_serve import CloudReceiverConfig
from specsmith.cloud_serve import make_server as make_cloud_server


@pytest.fixture(autouse=True)
def _no_auto_update(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPECSMITH_NO_AUTO_UPDATE", "1")
    monkeypatch.setenv("SPECSMITH_PYPI_CHECKED", "1")


# ---------------------------------------------------------------------------
# REQ-137: serve --auth-token
# ---------------------------------------------------------------------------


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def serve_with_auth(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Start a real specsmith.serve.HTTPServer with bearer auth.

    The agent thread is intentionally NOT started — we only exercise the
    HTTP handler's auth gate, not the runner. This keeps the test hermetic
    (no Ollama, no provider keys).
    """
    from specsmith.serve import make_server

    project = tmp_path / "proj"
    project.mkdir()
    port = _free_port()
    server, agent = make_server(
        project_dir=str(project),
        provider="ollama",
        model="",
        port=port,
        host="127.0.0.1",
        auth_token="t0p-secret",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.05)
    try:
        yield port
    finally:
        server.shutdown()
        server.server_close()


def _http(port: int, path: str, *, token: str | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(  # noqa: S310 - localhost
        f"http://127.0.0.1:{port}{path}",
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8") or "{}")
        except ValueError:
            body = {}
        return exc.code, body


def test_serve_health_does_not_require_auth(serve_with_auth) -> None:  # type: ignore[no-untyped-def]
    status, body = _http(serve_with_auth, "/api/health")
    assert status == 200
    assert body == {"ok": True}


def test_serve_status_requires_auth(serve_with_auth) -> None:  # type: ignore[no-untyped-def]
    status, body = _http(serve_with_auth, "/api/status")
    assert status == 401
    assert body == {"error": "unauthorized"}


def test_serve_status_rejects_wrong_token(serve_with_auth) -> None:  # type: ignore[no-untyped-def]
    status, _ = _http(serve_with_auth, "/api/status", token="wrong")
    assert status == 401


def test_serve_status_accepts_correct_token(serve_with_auth) -> None:  # type: ignore[no-untyped-def]
    status, body = _http(serve_with_auth, "/api/status", token="t0p-secret")
    assert status == 200
    assert "status" in body  # agent thread not started → 'starting'


def test_serve_cli_help_documents_auth_token() -> None:
    runner = CliRunner()
    res = runner.invoke(main, ["serve", "--help"])
    assert res.exit_code == 0
    assert "--auth-token" in res.output
    assert "REQ-137" in res.output


# ---------------------------------------------------------------------------
# REQ-136: cloud spawn client
# ---------------------------------------------------------------------------


@pytest.fixture
def cloud_endpoint(tmp_path: Path):
    port = _free_port()
    config = CloudReceiverConfig(
        host="127.0.0.1",
        port=port,
        token="cloud-secret",
        storage_dir=tmp_path / "cloud-runs",
    )
    server = make_cloud_server(config)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.05)
    try:
        yield port, config
    finally:
        server.shutdown()
        server.server_close()


def test_cloud_spawn_dry_run(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.yml"
    manifest.write_text("task: hello\nrun_id: r1\n", encoding="utf-8")
    runner = CliRunner()
    res = runner.invoke(main, ["cloud", "spawn", str(manifest), "--dry-run"])
    assert res.exit_code == 0
    payload = json.loads(res.output)
    assert payload["manifest"] == {"task": "hello", "run_id": "r1"}
    assert payload["endpoint"].startswith("http://")


def test_cloud_spawn_non_mapping_payload_exits_2(tmp_path: Path) -> None:
    manifest = tmp_path / "bad.json"
    # JSON parses fine but the payload is a list, not a mapping → exit 2.
    manifest.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    runner = CliRunner()
    res = runner.invoke(main, ["cloud", "spawn", str(manifest), "--dry-run"])
    assert res.exit_code == 2
    assert "mapping" in res.output.lower() or "object" in res.output.lower()


def test_cloud_spawn_missing_token_returns_401(  # type: ignore[no-untyped-def]
    tmp_path: Path, cloud_endpoint
) -> None:
    port, _ = cloud_endpoint
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps({"task": "x"}), encoding="utf-8")
    runner = CliRunner()
    res = runner.invoke(
        main,
        ["cloud", "spawn", str(manifest), "--endpoint", f"http://127.0.0.1:{port}"],
    )
    assert res.exit_code != 0
    assert "401" in res.output or "unauthorized" in res.output.lower()


def test_cloud_spawn_with_token_persists_manifest(  # type: ignore[no-untyped-def]
    tmp_path: Path, cloud_endpoint
) -> None:
    port, config = cloud_endpoint
    manifest = tmp_path / "m.json"
    manifest.write_text(
        json.dumps({"task": "demo", "run_id": "spawn_test"}),
        encoding="utf-8",
    )
    runner = CliRunner()
    res = runner.invoke(
        main,
        [
            "cloud",
            "spawn",
            str(manifest),
            "--endpoint",
            f"http://127.0.0.1:{port}",
            "--token",
            "cloud-secret",
        ],
    )
    assert res.exit_code == 0, res.output
    response = json.loads(res.output)
    assert response["run_id"] == "spawn_test"
    persisted = config.storage_dir / "spawn_test" / "manifest.json"
    assert persisted.is_file()


# ---------------------------------------------------------------------------
# REQ-141: voice transcription wrapper
# ---------------------------------------------------------------------------


def test_voice_transcribe_via_stub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPECSMITH_VOICE_STUB", "hello world")
    audio = tmp_path / "fake.wav"
    audio.write_bytes(b"RIFF\0\0\0\0WAVEfmt ")  # not real audio; stub ignores it
    result = transcribe(audio)
    assert isinstance(result, TranscribeResult)
    assert result.text == "hello world"
    assert result.backend == "stub"


def test_voice_transcribe_missing_file_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPECSMITH_VOICE_STUB", "anything")
    with pytest.raises(FileNotFoundError):
        transcribe(Path("does-not-exist.wav"))


def test_voice_transcribe_unavailable_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SPECSMITH_VOICE_STUB", raising=False)
    # Force the import to fail by stubbing sys.modules.
    import sys

    sys.modules.pop("whisper_cpp_python", None)
    monkeypatch.setitem(sys.modules, "whisper_cpp_python", None)
    audio = tmp_path / "fake.wav"
    audio.write_bytes(b"\0")
    with pytest.raises(VoiceUnavailableError):
        transcribe(audio)


def test_voice_is_available_with_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPECSMITH_VOICE_STUB", "stub")
    assert is_available() is True


def test_voice_cli_transcribe_stub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPECSMITH_VOICE_STUB", "transcribed text")
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"\0")
    runner = CliRunner()
    res = runner.invoke(main, ["voice", "transcribe", str(audio)])
    assert res.exit_code == 0
    assert "transcribed text" in res.output


def test_voice_cli_status_with_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPECSMITH_VOICE_STUB", "1")
    runner = CliRunner()
    res = runner.invoke(main, ["voice", "status"])
    assert res.exit_code == 0
    assert "available" in res.output


# ---------------------------------------------------------------------------
# REQ-140: api-surface stability snapshot
# ---------------------------------------------------------------------------


_FIXTURE = Path(__file__).parent / "fixtures" / "api_surface.json"


def test_api_surface_fixture_exists() -> None:
    """The fixture must be checked in so we can diff against drift."""
    assert _FIXTURE.is_file(), f"missing snapshot: {_FIXTURE}"


def test_api_surface_matches_fixture() -> None:
    """`specsmith api-surface` output must match the frozen fixture.

    When this fails after intentional surface changes, regenerate via:
        py -m specsmith.cli api-surface > tests/fixtures/api_surface.json
    """
    runner = CliRunner()
    res = runner.invoke(main, ["api-surface"])
    assert res.exit_code == 0
    actual = json.loads(res.output)
    expected = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    assert actual == expected, (
        "API surface drifted. Regenerate the snapshot if intentional:\n"
        "  py -m specsmith.cli api-surface > tests/fixtures/api_surface.json"
    )


def test_api_surface_contains_required_1_0_commands() -> None:
    """Spot-check that the 1.0 contract commands are still in the surface."""
    runner = CliRunner()
    res = runner.invoke(main, ["api-surface"])
    payload = json.loads(res.output)
    required = {
        "preflight",
        "verify",
        "audit",
        "validate",
        "doctor",
        "scan",
        "init",
        "import",
        "ledger",
        "drive",
        "history",
        "chat",
        "chat-export-block",
        "cloud",
        "cloud-serve",
        "voice",
        "api-surface",
        "suggest-command",
        "serve",
    }
    assert required.issubset(set(payload["cli_commands"]))


def test_api_surface_exit_codes_frozen() -> None:
    runner = CliRunner()
    res = runner.invoke(main, ["api-surface"])
    payload = json.loads(res.output)
    codes = payload["exit_codes"]
    assert codes["preflight_accepted"] == 0
    assert codes["preflight_needs_clarification"] == 2
    assert codes["preflight_blocked"] == 3
    assert codes["verify_ok"] == 0
    assert codes["verify_retry"] == 2
    assert codes["verify_stop"] == 3


def test_api_surface_event_types_frozen() -> None:
    runner = CliRunner()
    res = runner.invoke(main, ["api-surface"])
    payload = json.loads(res.output)
    events = set(payload["event_types"])
    assert {
        "block_start",
        "block_complete",
        "token",
        "plan_step",
        "tool_call",
        "tool_request",
        "tool_result",
        "diff",
        "task_complete",
    } == events
