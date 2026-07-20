# SPDX-License-Identifier: MIT
"""Smoke tests for the bridge handshake (REQ-145).

These tests are deliberately minimal — they verify the contract the VS
Code extension's :class:`SpecsmithBridge` depends on:

  * :meth:`AgentRunner._print_banner` emits a ``{"type": "ready", ...}``
    JSONL line on stdout when ``json_events=True``.
  * :meth:`EventEmitter.ready` writes the expected schema.

Slow integration tests (subprocess spawn, end-to-end stdin loop) live in
``tests/sandbox/`` so the unit suite stays fast.
"""

from __future__ import annotations

import io
import json

from specsmith.agent.events import EventEmitter
from specsmith.agent.runner import AgentRunner


def test_event_emitter_ready_writes_expected_schema() -> None:
    buf = io.StringIO()
    emitter = EventEmitter(stream=buf)
    emitter.ready(
        agent="nexus",
        version="9.9.9",
        project_dir="/tmp/proj",
        provider="ollama",
        model="qwen2.5:7b",
        capabilities=["chat", "endpoints"],
    )
    line = buf.getvalue().strip()
    payload = json.loads(line)
    assert payload["type"] == "ready"
    assert payload["agent"] == "nexus"
    assert payload["version"] == "9.9.9"
    assert payload["project_dir"] == "/tmp/proj"
    assert payload["provider"] == "ollama"
    assert payload["model"] == "qwen2.5:7b"
    assert payload["capabilities"] == ["chat", "endpoints"]
    assert "timestamp" in payload


def test_agent_runner_print_banner_emits_ready(tmp_path) -> None:
    buf = io.StringIO()
    emitter = EventEmitter(stream=buf)
    runner = AgentRunner(
        project_dir=str(tmp_path),
        provider_name="ollama",
        model="qwen2.5:7b",
        json_events=True,
        emitter=emitter,
    )
    runner._print_banner()
    line = buf.getvalue().strip()
    payload = json.loads(line)
    assert payload["type"] == "ready"
    assert payload["provider"] == "ollama"
    assert payload["model"] == "qwen2.5:7b"
    assert "chat" in payload["capabilities"]


def test_agent_runner_handle_command_clear_resets_history(tmp_path) -> None:
    buf = io.StringIO()
    runner = AgentRunner(
        project_dir=str(tmp_path),
        json_events=True,
        emitter=EventEmitter(stream=buf),
    )
    runner._history.append({"role": "user", "text": "hi"})
    runner._handle_command("/clear")
    assert runner._history == []
    assert not runner._context_compressed


def test_agent_runner_compresses_history_before_paid_context(tmp_path, monkeypatch) -> None:
    buf = io.StringIO()
    runner = AgentRunner(
        project_dir=str(tmp_path),
        json_events=True,
        emitter=EventEmitter(stream=buf),
    )
    runner._history = [{"role": "user", "text": "x" * 200}]
    monkeypatch.setenv("SPECSMITH_CONTEXT_COMPRESS_CHARS", "100")

    from specsmith.agent import context_compressor

    monkeypatch.setattr(
        context_compressor,
        "compress_history_elements",
        lambda history, **kwargs: (
            [{"role": "system", "text": "compressed evidence"}],
            {"ok": True, "space_saved_pct": 75.0},
        ),
    )

    stats = runner._compress_context_if_needed()
    assert stats["ok"]
    assert runner._context_compressed
    assert runner._history == [{"role": "system", "text": "compressed evidence"}]
    assert "context compressed" in buf.getvalue()


def test_agent_runner_help_and_status_are_local(tmp_path) -> None:
    buf = io.StringIO()
    runner = AgentRunner(
        project_dir=str(tmp_path),
        provider_name="ollama",
        model="qwen2.5:7b",
        json_events=True,
        emitter=EventEmitter(stream=buf),
    )
    assert runner._handle_command("/help") is None
    assert runner._handle_command("/status") is None
    output = buf.getvalue()
    assert "Grace is the optional local fallback" in output
    assert "provider=ollama" in output
    assert "context_compressed=False" in output
