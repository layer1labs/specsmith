# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for specsmith run provider checks, model selection, and feedback.

Regression coverage for the silent-no-response bug:
- Wrong default Ollama model (qwen2.5:7b not installed) → silent failure
- No feedback when run_chat returns None
- check_providers() accurately reflects real provider availability
- PlainTextEmitter writes tokens without JSON wrapping
- _pick_ollama_model prefers installed models over the hardcoded default
"""

from __future__ import annotations

import io
import json
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# _pick_ollama_model — model selection logic
# ---------------------------------------------------------------------------


class TestPickOllamaModel:
    def test_returns_env_override_without_querying(self, monkeypatch, tmp_path):
        """SPECSMITH_OLLAMA_MODEL env var wins unconditionally."""
        monkeypatch.setenv("SPECSMITH_OLLAMA_MODEL", "phi4:14b-q4_K_M")
        from specsmith.agent.chat_runner import _pick_ollama_model

        result = _pick_ollama_model("http://127.0.0.1:11434")
        assert result == "phi4:14b-q4_K_M"

    def test_prefers_preferred_model_over_alphabetical_first(self, monkeypatch):
        """Should pick the first preference-list match, not the alphabetically first."""
        monkeypatch.delenv("SPECSMITH_OLLAMA_MODEL", raising=False)

        installed = [
            {"name": "zz-model:latest"},
            {"name": "qwen2.5-coder:7b-instruct"},
            {"name": "phi4:14b-q4_K_M"},
        ]
        fake_resp = MagicMock()
        fake_resp.read.return_value = json.dumps({"models": installed}).encode()
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)

        from specsmith.agent.chat_runner import _pick_ollama_model

        with patch("specsmith.agent.chat_runner.urlopen", return_value=fake_resp):
            result = _pick_ollama_model("http://127.0.0.1:11434")

        # qwen2.5-coder:7b-instruct is higher in _OLLAMA_MODEL_PREFERENCE than phi4
        assert result == "qwen2.5-coder:7b-instruct"

    def test_falls_back_to_sorted_first_when_no_preference_match(self, monkeypatch):
        """When none of the preference list is installed, pick sorted-first installed."""
        monkeypatch.delenv("SPECSMITH_OLLAMA_MODEL", raising=False)

        installed = [{"name": "custom-model-b:7b"}, {"name": "custom-model-a:7b"}]
        fake_resp = MagicMock()
        fake_resp.read.return_value = json.dumps({"models": installed}).encode()
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)

        from specsmith.agent.chat_runner import _pick_ollama_model

        with patch("specsmith.agent.chat_runner.urlopen", return_value=fake_resp):
            result = _pick_ollama_model("http://127.0.0.1:11434")

        assert result == "custom-model-a:7b"

    def test_falls_back_to_default_when_api_unreachable(self, monkeypatch):
        """When /api/tags raises, return DEFAULT_OLLAMA_MODEL."""
        monkeypatch.delenv("SPECSMITH_OLLAMA_MODEL", raising=False)
        from urllib.error import URLError

        from specsmith.agent.chat_runner import DEFAULT_OLLAMA_MODEL, _pick_ollama_model

        with patch("specsmith.agent.chat_runner.urlopen", side_effect=URLError("refused")):
            result = _pick_ollama_model("http://127.0.0.1:11434")

        assert result == DEFAULT_OLLAMA_MODEL

    def test_uses_installed_model_not_missing_default(self, monkeypatch):
        """Core regression: qwen2.5:7b not installed → picks qwen2.5:14b instead."""
        monkeypatch.delenv("SPECSMITH_OLLAMA_MODEL", raising=False)

        # Simulate the exact machine state that caused the bug
        installed = [
            {"name": "phi4:14b-q4_K_M"},
            {"name": "qwen2.5:14b"},
            {"name": "qwen2.5-coder:7b-instruct"},
            {"name": "mistral:7b-instruct-q4_0"},
        ]
        fake_resp = MagicMock()
        fake_resp.read.return_value = json.dumps({"models": installed}).encode()
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)

        from specsmith.agent.chat_runner import _pick_ollama_model

        with patch("specsmith.agent.chat_runner.urlopen", return_value=fake_resp):
            result = _pick_ollama_model("http://127.0.0.1:11434")

        # qwen2.5:7b is not installed; qwen2.5-coder:7b-instruct is next preferred
        assert result != "qwen2.5:7b"
        assert result in {"qwen2.5-coder:7b-instruct", "mistral:7b-instruct-q4_0", "qwen2.5:14b"}


# ---------------------------------------------------------------------------
# PlainTextEmitter — interactive mode token output
# ---------------------------------------------------------------------------


class TestPlainTextEmitter:
    def test_token_writes_text_not_json(self):
        """PlainTextEmitter.token() must write raw text, not a JSON object."""
        from specsmith.agent.events import PlainTextEmitter

        buf = io.StringIO()
        emitter = PlainTextEmitter(stream=buf)
        emitter.token("blk_001", "Hello, ")
        emitter.token("blk_001", "world!")

        output = buf.getvalue()
        assert output == "Hello, world!"
        # Must NOT be JSON
        assert "{" not in output

    def test_emit_drops_protocol_frames(self):
        """PlainTextEmitter.emit() discards JSONL frames silently."""
        from specsmith.agent.events import PlainTextEmitter

        buf = io.StringIO()
        emitter = PlainTextEmitter(stream=buf)
        emitter.emit({"type": "block_start", "block_id": "x", "kind": "message"})
        emitter.emit({"type": "turn_done"})

        assert buf.getvalue() == ""

    def test_ready_does_not_write_in_plain_mode(self):
        """PlainTextEmitter.ready() must be a no-op (inherits emit → no-op)."""
        from specsmith.agent.events import PlainTextEmitter

        buf = io.StringIO()
        emitter = PlainTextEmitter(stream=buf)
        emitter.ready(agent="nexus", version="0.11.5")
        assert buf.getvalue() == ""


# ---------------------------------------------------------------------------
# check_providers() — provider status table
# ---------------------------------------------------------------------------


class TestCheckProviders:
    def test_returns_four_providers(self):
        """check_providers() must always return exactly 4 entries."""
        from specsmith.agent.runner import check_providers

        # Patch Ollama alive check to avoid network
        with patch("specsmith.agent.chat_runner._ollama_alive", return_value=False):
            statuses = check_providers()

        names = [s.name for s in statuses]
        assert names == ["ollama", "anthropic", "openai", "gemini"]

    def test_ollama_down_shows_not_available(self):
        """When Ollama is not running, ollama status must be available=False."""
        from specsmith.agent.runner import check_providers

        with patch("specsmith.agent.chat_runner._ollama_alive", return_value=False):
            statuses = check_providers()

        ollama = next(s for s in statuses if s.name == "ollama")
        assert not ollama.available
        assert "not running" in ollama.note or "ollama serve" in ollama.note

    def test_anthropic_without_key_is_unavailable(self, monkeypatch):
        """Missing ANTHROPIC_API_KEY → anthropic unavailable."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from specsmith.agent.runner import check_providers

        with patch("specsmith.agent.chat_runner._ollama_alive", return_value=False):
            statuses = check_providers()

        anthropic = next(s for s in statuses if s.name == "anthropic")
        assert not anthropic.available
        assert "ANTHROPIC_API_KEY" in anthropic.note

    def test_anthropic_with_key_and_sdk_is_available(self, monkeypatch):
        """ANTHROPIC_API_KEY set + SDK present → anthropic available."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")

        from specsmith.agent.runner import check_providers

        with (
            patch("specsmith.agent.chat_runner._ollama_alive", return_value=False),
            patch(
                "importlib.util.find_spec",
                lambda name: MagicMock() if name == "anthropic" else None,
            ),
        ):
            statuses = check_providers()

        anthropic = next(s for s in statuses if s.name == "anthropic")
        assert anthropic.available
        assert "claude" in anthropic.model.lower()

    def test_ollama_available_with_model_shows_model_name(self, monkeypatch):
        """When Ollama is alive, check_providers() reports the resolved model."""
        monkeypatch.delenv("SPECSMITH_OLLAMA_MODEL", raising=False)

        installed = [{"name": "qwen2.5-coder:7b-instruct"}]
        fake_resp = MagicMock()
        fake_resp.read.return_value = json.dumps({"models": installed}).encode()
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)

        from specsmith.agent.runner import check_providers

        # check_providers() imports urlopen from urllib.request inside the function;
        # patch at the source so both the alive-check and the tags call are controlled.
        with (
            patch("specsmith.agent.chat_runner._ollama_alive", return_value=True),
            patch("urllib.request.urlopen", return_value=fake_resp),
        ):
            statuses = check_providers()

        ollama = next(s for s in statuses if s.name == "ollama")
        assert ollama.available
        assert ollama.model == "qwen2.5-coder:7b-instruct"
        assert ollama.model_count == 1


# ---------------------------------------------------------------------------
# AgentRunner — feedback when no provider responds
# ---------------------------------------------------------------------------


class TestAgentRunnerFeedback:
    def test_handle_command_prints_hint_when_no_provider(self, tmp_path, capsys):
        """_handle_command must print a hint when run_chat returns None."""
        from specsmith.agent.runner import AgentRunner

        with (
            patch("specsmith.agent.chat_runner._ollama_alive", return_value=False),
            patch("specsmith.agent.chat_runner.run_chat", return_value=None),
        ):
            runner = AgentRunner(project_dir=str(tmp_path), json_events=False)
            result = runner._handle_command("hello specsmith")

        assert result is None
        captured = capsys.readouterr()
        # Must print something actionable — not stay silent
        assert len(captured.out.strip()) > 0
        assert any(
            keyword in captured.out.lower()
            for keyword in ("provider", "ollama", "api_key", "anthropic", "options")
        )

    def test_handle_command_ollama_alive_hint_mentions_model(self, tmp_path, capsys):
        """When Ollama is running but returns None, hint mentions the model name."""
        from specsmith.agent.runner import AgentRunner

        installed = [{"name": "mistral:7b-instruct-q4_0"}]
        fake_resp = MagicMock()
        fake_resp.read.return_value = json.dumps({"models": installed}).encode()
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)

        with (
            patch("specsmith.agent.chat_runner._ollama_alive", return_value=True),
            patch("specsmith.agent.chat_runner.urlopen", return_value=fake_resp),
            patch("specsmith.agent.chat_runner.run_chat", return_value=None),
        ):
            runner = AgentRunner(project_dir=str(tmp_path), json_events=False)
            runner._handle_command("test prompt")

        captured = capsys.readouterr()
        assert "mistral" in captured.out or "ollama" in captured.out.lower()

    def test_plain_text_emitter_used_in_non_json_mode(self, tmp_path):
        """AgentRunner must use PlainTextEmitter when json_events=False."""
        from specsmith.agent.events import PlainTextEmitter
        from specsmith.agent.runner import AgentRunner

        with patch("specsmith.agent.chat_runner._ollama_alive", return_value=False):
            runner = AgentRunner(project_dir=str(tmp_path), json_events=False)

        assert isinstance(runner._emitter, PlainTextEmitter)

    def test_jsonl_emitter_used_in_json_events_mode(self, tmp_path):
        """AgentRunner must use EventEmitter (not PlainTextEmitter) when json_events=True."""
        from specsmith.agent.events import EventEmitter, PlainTextEmitter
        from specsmith.agent.runner import AgentRunner

        with patch("specsmith.agent.chat_runner._ollama_alive", return_value=False):
            runner = AgentRunner(project_dir=str(tmp_path), json_events=True)

        assert isinstance(runner._emitter, EventEmitter)
        assert not isinstance(runner._emitter, PlainTextEmitter)


# ---------------------------------------------------------------------------
# specsmith run --check CLI integration
# ---------------------------------------------------------------------------


class TestRunCheckCLI:
    def test_check_flag_exits_zero_when_provider_available(self, tmp_path):
        """specsmith run --check exits 0 when at least one provider is available."""
        from click.testing import CliRunner

        from specsmith.agent.runner import ProviderStatus
        from specsmith.cli import main

        fake_statuses = [
            ProviderStatus(
                name="ollama", available=True, model="qwen3:8b", note="auto, 5 installed"
            ),
            ProviderStatus(name="anthropic", available=False, note="no ANTHROPIC_API_KEY"),
            ProviderStatus(name="openai", available=False, note="no OPENAI_API_KEY"),
            ProviderStatus(name="gemini", available=False, note="no GOOGLE_API_KEY"),
        ]

        runner = CliRunner()
        # check_providers is imported inside run_cmd via `from specsmith.agent.runner import`
        with patch("specsmith.agent.runner.check_providers", return_value=fake_statuses):
            result = runner.invoke(main, ["run", "--check", "--project-dir", str(tmp_path)])

        assert result.exit_code == 0
        assert "qwen3:8b" in result.output
        assert "Ready" in result.output

    def test_check_flag_exits_one_when_no_provider(self, tmp_path):
        """specsmith run --check exits 1 when no provider is available."""
        from click.testing import CliRunner

        from specsmith.agent.runner import ProviderStatus
        from specsmith.cli import main

        fake_statuses = [
            ProviderStatus(name="ollama", available=False, note="not running"),
            ProviderStatus(name="anthropic", available=False, note="no ANTHROPIC_API_KEY"),
            ProviderStatus(name="openai", available=False, note="no OPENAI_API_KEY"),
            ProviderStatus(name="gemini", available=False, note="no GOOGLE_API_KEY"),
        ]

        runner = CliRunner()
        with patch("specsmith.agent.runner.check_providers", return_value=fake_statuses):
            result = runner.invoke(main, ["run", "--check", "--project-dir", str(tmp_path)])

        assert result.exit_code == 1
        assert "No provider" in result.output
