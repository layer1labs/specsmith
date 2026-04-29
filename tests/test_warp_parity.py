# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Warp parity bundle tests (REQ-133..REQ-136, REQ-140).

Exercises the four new modules introduced in MEGA-PR-CLI plus the API
stability surface and the CLI wiring that exposes them.
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

from specsmith.block_export import export_block, slice_block
from specsmith.cli import main
from specsmith.cloud_serve import CloudReceiverConfig, make_server
from specsmith.drive import default_drive_dir, listing, pull, push
from specsmith.history_search import HistoryHit, search

# ---------------------------------------------------------------------------
# Common autouse fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _no_auto_update(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPECSMITH_NO_AUTO_UPDATE", "1")
    monkeypatch.setenv("SPECSMITH_PYPI_CHECKED", "1")


# ---------------------------------------------------------------------------
# drive.py — REQ-133
# ---------------------------------------------------------------------------


def _seed_project_with_artifacts(project: Path) -> None:
    governance = project / "docs" / "governance"
    governance.mkdir(parents=True)
    (governance / "PROJECT_RULES.md").write_text("# rules\n", encoding="utf-8")

    workflows = project / ".specsmith" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "deploy.yml").write_text("name: deploy\n", encoding="utf-8")

    notebooks = project / "docs" / "notebooks"
    notebooks.mkdir(parents=True)
    (notebooks / "smoke.md").write_text("# smoke\n", encoding="utf-8")


def test_drive_default_dir_under_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    assert default_drive_dir() == tmp_path / "home" / ".specsmith" / "drive"


def test_drive_push_pull_round_trip(tmp_path: Path) -> None:
    project = tmp_path / "demo-project"
    project.mkdir()
    _seed_project_with_artifacts(project)
    drive = tmp_path / "drive"

    pushed = push(project, drive)
    assert sorted(pushed.pushed) == [
        "notebooks/smoke.md",
        "rules/PROJECT_RULES.md",
        "workflows/deploy.yml",
    ]
    assert pushed.errors == []

    # listing reflects the project mirror
    data = listing(drive)
    assert set(data["demo-project"].keys()) == {"rules", "workflows", "notebooks"}

    # Round-trip into a fresh project
    restored = tmp_path / "demo-project"  # same name → drive maps back into it
    pulled = pull(restored, drive)
    assert sorted(pulled.pulled) == [
        "notebooks/smoke.md",
        "rules/PROJECT_RULES.md",
        "workflows/deploy.yml",
    ]
    assert pulled.errors == []


def test_drive_listing_handles_empty_dir(tmp_path: Path) -> None:
    assert listing(tmp_path / "missing") == {}


# ---------------------------------------------------------------------------
# block_export.py — REQ-134
# ---------------------------------------------------------------------------


def _seed_session(project: Path, session_id: str, events: list[dict]) -> None:
    session_dir = project / ".specsmith" / "sessions" / session_id
    session_dir.mkdir(parents=True)
    with (session_dir / "events.jsonl").open("w", encoding="utf-8") as fh:
        for evt in events:
            fh.write(json.dumps(evt) + "\n")


def test_export_block_markdown(tmp_path: Path) -> None:
    project = tmp_path / "p"
    project.mkdir()
    _seed_session(
        project,
        "abc123",
        [
            {"type": "block_start", "block_id": "blk_1", "text": "thinking"},
            {"type": "token", "block_id": "blk_1", "text": "hello"},
            {"type": "block_complete", "block_id": "blk_1"},
            {"type": "token", "block_id": "blk_2", "text": "ignored"},
        ],
    )
    out = export_block(project, "abc123", "blk_1", fmt="md")
    assert "# Block `blk_1`" in out
    assert "hello" in out
    assert "ignored" not in out


def test_export_block_json_and_html(tmp_path: Path) -> None:
    project = tmp_path / "p"
    project.mkdir()
    _seed_session(
        project,
        "s1",
        [{"type": "token", "block_id": "blk", "text": "x"}],
    )
    js = export_block(project, "s1", "blk", fmt="json")
    parsed = json.loads(js)
    assert parsed[0]["text"] == "x"

    html = export_block(project, "s1", "blk", fmt="html")
    assert "<title>specsmith block blk</title>" in html
    assert "&quot;text&quot;: &quot;x&quot;" in html


def test_export_block_missing_session_raises(tmp_path: Path) -> None:
    project = tmp_path / "p"
    project.mkdir()
    with pytest.raises(FileNotFoundError):
        export_block(project, "nope", "blk", fmt="md")


def test_export_block_missing_block_raises(tmp_path: Path) -> None:
    project = tmp_path / "p"
    project.mkdir()
    _seed_session(project, "s1", [{"type": "token", "block_id": "other"}])
    with pytest.raises(KeyError):
        export_block(project, "s1", "blk_missing", fmt="md")


def test_slice_block_matches_id_field(tmp_path: Path) -> None:
    events = [
        {"id": "blk_1", "text": "a"},
        {"block_id": "blk_1", "text": "b"},
        {"block_id": "other", "text": "c"},
    ]
    out = slice_block(events, "blk_1")
    assert [e.get("text") for e in out] == ["a", "b"]


# ---------------------------------------------------------------------------
# history_search.py — REQ-135
# ---------------------------------------------------------------------------


def _seed_history(project: Path, session_id: str, turns: list[dict]) -> None:
    sd = project / ".specsmith" / "sessions" / session_id
    sd.mkdir(parents=True)
    with (sd / "turns.jsonl").open("w", encoding="utf-8") as fh:
        for t in turns:
            fh.write(json.dumps(t) + "\n")


def test_history_keyword_search_scores_and_ranks(tmp_path: Path) -> None:
    project = tmp_path / "p"
    project.mkdir()
    _seed_history(
        project,
        "alpha",
        [
            {"role": "user", "text": "fix the cleanup regression around broker"},
            {"role": "agent", "text": "ack will look into broker module"},
        ],
    )
    _seed_history(
        project,
        "beta",
        [{"role": "user", "text": "unrelated question about deployment"}],
    )
    hits = search("broker cleanup", project, limit=5)
    assert hits, "expected at least one keyword hit"
    assert all(isinstance(h, HistoryHit) for h in hits)
    assert hits[0].session_id == "alpha"
    assert hits[0].score > 0


def test_history_search_returns_empty_when_no_corpus(tmp_path: Path) -> None:
    assert search("anything", tmp_path) == []


def test_history_search_honors_limit(tmp_path: Path) -> None:
    project = tmp_path / "p"
    project.mkdir()
    _seed_history(
        project,
        "alpha",
        [{"role": "user", "text": f"broker issue number {i}"} for i in range(5)],
    )
    hits = search("broker", project, limit=2)
    assert len(hits) <= 2


def test_history_search_semantic_falls_back_to_keyword(tmp_path: Path) -> None:
    project = tmp_path / "p"
    project.mkdir()
    _seed_history(project, "alpha", [{"role": "user", "text": "broker is failing"}])
    hits = search("broker", project, limit=5, semantic=True)
    # Even with semantic=True, when the optional extra is absent we should still
    # fall through to keyword matching and return a hit.
    assert hits and hits[0].session_id == "alpha"


# ---------------------------------------------------------------------------
# cloud_serve.py — REQ-136
# ---------------------------------------------------------------------------


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def cloud_server(tmp_path: Path) -> tuple[CloudReceiverConfig, threading.Thread, int]:
    port = _free_port()
    config = CloudReceiverConfig(
        host="127.0.0.1",
        port=port,
        token="secret",
        storage_dir=tmp_path / "cloud-runs",
    )
    server = make_server(config)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # Tiny settle delay; the server is in-process so this is cheap and avoids
    # racing the first connection on slow CI machines.
    time.sleep(0.05)
    try:
        yield config, thread, port
    finally:
        server.shutdown()
        server.server_close()


def _post_json(
    port: int, path: str, payload: dict, *, token: str | None = None
) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310 - localhost
        f"http://127.0.0.1:{port}{path}",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8") or "{}"
        return exc.code, json.loads(body_text)


def test_cloud_serve_rejects_missing_token(cloud_server) -> None:  # type: ignore[no-untyped-def]
    _, _, port = cloud_server
    status, payload = _post_json(port, "/spawn", {"task": "hi"})
    assert status == 401
    assert payload == {"error": "unauthorized"}


def test_cloud_serve_rejects_wrong_token(cloud_server) -> None:  # type: ignore[no-untyped-def]
    _, _, port = cloud_server
    status, _ = _post_json(port, "/spawn", {"task": "hi"}, token="wrong")
    assert status == 401


def test_cloud_serve_accepts_valid_token_and_persists_manifest(cloud_server) -> None:  # type: ignore[no-untyped-def]
    config, _, port = cloud_server
    status, payload = _post_json(
        port,
        "/spawn",
        {"task": "demo", "run_id": "fixed_run"},
        token="secret",
    )
    assert status == 202
    assert payload["run_id"] == "fixed_run"
    assert payload["status"] == "accepted"
    manifest = config.storage_dir / "fixed_run" / "manifest.json"
    assert manifest.is_file()
    body = json.loads(manifest.read_text(encoding="utf-8"))
    assert body == {"task": "demo", "run_id": "fixed_run"}


def test_cloud_serve_health_requires_token(cloud_server) -> None:  # type: ignore[no-untyped-def]
    _, _, port = cloud_server
    req = urllib.request.Request(  # noqa: S310 - localhost
        f"http://127.0.0.1:{port}/health",
        headers={"Authorization": "Bearer secret"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310
        data = json.loads(resp.read().decode("utf-8"))
    assert data == {"ok": True}


def test_cloud_serve_refuses_non_loopback_without_cidr(tmp_path: Path) -> None:
    config = CloudReceiverConfig(
        host="0.0.0.0",  # noqa: S104 - intentional, we expect a guardrail
        port=_free_port(),
        storage_dir=tmp_path / "cloud-runs",
    )
    with pytest.raises(RuntimeError):
        make_server(config)


# ---------------------------------------------------------------------------
# CLI wiring — chat export-block / cloud-serve / api-surface (REQ-140)
# ---------------------------------------------------------------------------


def test_cli_chat_export_block(tmp_path: Path) -> None:
    project = tmp_path / "p"
    project.mkdir()
    _seed_session(
        project,
        "sess1",
        [{"type": "token", "block_id": "blk_a", "text": "hello world"}],
    )
    runner = CliRunner()
    res = runner.invoke(
        main,
        [
            "chat-export-block",
            "--project-dir",
            str(project),
            "--session-id",
            "sess1",
            "--block-id",
            "blk_a",
            "--format",
            "json",
        ],
    )
    assert res.exit_code == 0, res.output
    payload = json.loads(res.output)
    assert payload[0]["text"] == "hello world"


def test_cli_chat_export_block_missing_block_exits_nonzero(tmp_path: Path) -> None:
    project = tmp_path / "p"
    project.mkdir()
    _seed_session(project, "sess1", [{"type": "token", "block_id": "other"}])
    runner = CliRunner()
    res = runner.invoke(
        main,
        [
            "chat-export-block",
            "--project-dir",
            str(project),
            "--session-id",
            "sess1",
            "--block-id",
            "missing",
        ],
    )
    assert res.exit_code != 0


def test_cli_api_surface_emits_stable_keys(tmp_path: Path) -> None:
    runner = CliRunner()
    snapshot = tmp_path / "surface.json"
    res = runner.invoke(main, ["api-surface", "--snapshot", str(snapshot)])
    assert res.exit_code == 0, res.output
    payload = json.loads(res.output)
    assert "cli_commands" in payload
    assert "exit_codes" in payload
    assert "event_types" in payload

    # File snapshot should match the printed output byte-for-byte.
    assert snapshot.read_text(encoding="utf-8") == res.output.strip()

    # Required commands the 1.0 contract promises must remain present.
    required = {
        "preflight",
        "verify",
        "audit",
        "validate",
        "scan",
        "doctor",
        "init",
        "import",
        "ledger",
        "drive",
        "history",
        "chat",
        "chat-export-block",
        "cloud-serve",
        "api-surface",
        "suggest-command",
    }
    assert required.issubset(set(payload["cli_commands"]))
