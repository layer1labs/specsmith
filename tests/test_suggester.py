# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for the NL-to-command suggester (REQ-131 / TEST-131)."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from specsmith.agent.suggester import classify, suggest_command
from specsmith.cli import main


def test_classify_passthrough_for_short_input() -> None:
    assert classify("") == "passthrough"
    assert classify("a") == "passthrough"


def test_classify_command_for_shell_verb() -> None:
    assert classify("git status") == "command"
    assert classify("run tests") == "command"
    assert classify("pytest -q") == "command"


def test_classify_utterance_for_natural_language() -> None:
    assert classify("add a logging module") == "utterance"
    assert classify("explain the broker") == "utterance"


def test_suggest_command_template_match() -> None:
    out = suggest_command("run tests")
    assert out.kind == "command"
    assert out.suggestion == "pytest -q"
    assert out.confidence >= 0.8


def test_suggest_command_single_verb_fallback() -> None:
    out = suggest_command("git")
    assert out.kind == "command"
    assert "git" in out.suggestion
    assert "status" in out.suggestion


def test_suggest_command_explicit_req_increases_confidence() -> None:
    out = suggest_command("fix REQ-130 broken")
    assert out.kind == "utterance"
    assert "REQ-130" in out.candidates
    assert out.confidence >= 0.85


def test_suggest_command_change_verb_without_target() -> None:
    out = suggest_command("fix it")
    assert out.kind == "utterance"
    assert "name the component" in out.suggestion


def test_suggest_command_project_aware_match(tmp_path: Path) -> None:
    (tmp_path / "REQUIREMENTS.md").write_text(
        "## REQ-LOG-001\n- Description: add structured logging to the broker module.\n",
        encoding="utf-8",
    )
    out = suggest_command(
        "document the structured logging behaviour for broker module",
        project_dir=tmp_path,
    )
    assert out.kind == "utterance"
    assert "REQ-LOG-001" in out.candidates


def test_suggest_command_passthrough_for_short_text() -> None:
    out = suggest_command("a")
    assert out.kind == "passthrough"
    assert out.suggestion == "a"


def test_cli_suggest_command_emits_json(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["suggest-command", "git status", "--project-dir", str(tmp_path)],
        env={"SPECSMITH_NO_AUTO_UPDATE": "1", "SPECSMITH_PYPI_CHECKED": "1"},
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "command"
    assert payload["suggestion"] == "git --no-pager status"
