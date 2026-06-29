# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for host-terminal detection (REQ-444)."""

from __future__ import annotations

import io

from specsmith.agent.terminal_env import TerminalInfo, detect_terminal, emit_warp_notification


class TestDetectTerminal:
    def test_detects_warp_via_term_program(self) -> None:
        info = detect_terminal(
            {"TERM_PROGRAM": "WarpTerminal", "TERM_PROGRAM_VERSION": "0.2026.06.01"}
        )
        assert info.is_warp is True
        assert info.program == "WarpTerminal"
        assert info.version == "0.2026.06.01"

    def test_detects_warp_via_warp_env_var(self) -> None:
        info = detect_terminal({"WARP_HONOR_PS1": "0"})
        assert info.is_warp is True
        # Program is backfilled when only a WARP_* signal is present.
        assert info.program == "WarpTerminal"

    def test_non_warp_terminal(self) -> None:
        info = detect_terminal({"TERM_PROGRAM": "iTerm.app"})
        assert info.is_warp is False
        assert info.program == "iTerm.app"
        assert info.version == ""

    def test_empty_env(self) -> None:
        info = detect_terminal({})
        assert info.is_warp is False
        assert info.program == ""
        assert info.version == ""

    def test_as_dict_round_trip(self) -> None:
        info = detect_terminal({"TERM_PROGRAM": "WarpTerminal"})
        d = info.as_dict()
        assert d == {
            "is_warp": True,
            "program": "WarpTerminal",
            "version": "",
            "active_agent": "",
        }

    def test_frozen_dataclass(self) -> None:
        info = TerminalInfo(is_warp=False, program="x", version="1")
        try:
            info.is_warp = True  # type: ignore[misc]
        except AttributeError:
            pass
        else:  # pragma: no cover - dataclass should be frozen
            raise AssertionError("TerminalInfo should be frozen")


class TestActiveAgentDetection:
    def test_detects_specsmith_repl(self) -> None:
        info = detect_terminal({"SPECSMITH_RUN_ACTIVE": "1"})
        assert info.active_agent == "specsmith"

    def test_detects_aider_via_model(self) -> None:
        info = detect_terminal({"AIDER_MODEL": "gpt-4o"})
        assert info.active_agent == "aider"

    def test_detects_aider_via_config(self) -> None:
        info = detect_terminal({"AIDER_CONFIG": "/home/user/.aider.conf.yml"})
        assert info.active_agent == "aider"

    def test_detects_claude(self) -> None:
        info = detect_terminal({"CLAUDE_CODE_ENTRYPOINT": "cli"})
        assert info.active_agent == "claude"

    def test_detects_codex(self) -> None:
        info = detect_terminal({"CODEX_CLI_SESSION": "abc123"})
        assert info.active_agent == "codex"

    def test_detects_gemini(self) -> None:
        info = detect_terminal({"GEMINI_CLI": "1"})
        assert info.active_agent == "gemini"

    def test_no_agent_in_plain_shell(self) -> None:
        info = detect_terminal({"TERM_PROGRAM": "iTerm.app"})
        assert info.active_agent == ""

    def test_specsmith_wins_over_aider_when_both_present(self) -> None:
        # SPECSMITH_RUN_ACTIVE is checked first in the signals dict.
        info = detect_terminal({"SPECSMITH_RUN_ACTIVE": "1", "AIDER_MODEL": "gpt-4o"})
        assert info.active_agent == "specsmith"

    def test_active_agent_included_in_as_dict(self) -> None:
        info = detect_terminal({"AIDER_MODEL": "claude-3-5-sonnet"})
        assert info.as_dict()["active_agent"] == "aider"


class TestEmitWarpNotification:
    def test_writes_osc9_sequence_to_explicit_stream(self) -> None:
        buf = io.StringIO()
        emit_warp_notification("hello warp", stream=buf)
        assert buf.getvalue() == "\033]9;hello warp\007"

    def test_message_is_included_verbatim(self) -> None:
        buf = io.StringIO()
        emit_warp_notification("specsmith run | myproj | governance active", stream=buf)
        assert "specsmith run | myproj | governance active" in buf.getvalue()

    def test_empty_message_still_writes_osc_frame(self) -> None:
        buf = io.StringIO()
        emit_warp_notification("", stream=buf)
        # Should still write the OSC frame (empty body is valid)
        assert "\033]9;" in buf.getvalue()

    def test_no_exception_on_closed_stream(self) -> None:
        buf = io.StringIO()
        buf.close()
        # Must not raise
        emit_warp_notification("test", stream=buf)


class TestBannerReflectsTerminal:
    def test_runner_reads_terminal(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("TERM_PROGRAM", "WarpTerminal")
        from specsmith.agent.runner import AgentRunner

        runner = AgentRunner(project_dir=str(tmp_path), json_events=True)
        assert runner.terminal.is_warp is True

    def test_runner_sets_specsmith_run_active(self, tmp_path, monkeypatch) -> None:
        import os

        monkeypatch.delenv("SPECSMITH_RUN_ACTIVE", raising=False)
        from specsmith.agent.runner import AgentRunner

        AgentRunner(project_dir=str(tmp_path), json_events=True)
        assert os.environ.get("SPECSMITH_RUN_ACTIVE") == "1"
