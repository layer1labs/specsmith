# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for host-terminal detection (REQ-444)."""

from __future__ import annotations

from specsmith.agent.terminal_env import TerminalInfo, detect_terminal


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
        assert d == {"is_warp": True, "program": "WarpTerminal", "version": ""}

    def test_frozen_dataclass(self) -> None:
        info = TerminalInfo(is_warp=False, program="x", version="1")
        try:
            info.is_warp = True  # type: ignore[misc]
        except AttributeError:
            pass
        else:  # pragma: no cover - dataclass should be frozen
            raise AssertionError("TerminalInfo should be frozen")


class TestBannerReflectsTerminal:
    def test_runner_reads_terminal(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("TERM_PROGRAM", "WarpTerminal")
        from specsmith.agent.runner import AgentRunner

        runner = AgentRunner(project_dir=str(tmp_path), json_events=True)
        assert runner.terminal.is_warp is True
