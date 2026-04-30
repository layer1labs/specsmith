# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for `specsmith chat --interactive` stdin decision protocol.

The interactive flow lets an IDE consumer (e.g. the VS Code extension)
drive the safe-mode approval and inline diff review by writing JSON
decision lines to the CLI's stdin.
"""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from specsmith.cli import main


def test_chat_safe_mode_denies_when_no_stdin(tmp_path: Path) -> None:
    """Without --interactive, safe profile emits tool_request and stops."""
    runner = CliRunner()
    res = runner.invoke(
        main,
        ["chat", "add hello world", "--project-dir", str(tmp_path), "--profile", "safe"],
    )
    assert res.exit_code == 0, res.output
    events = [json.loads(line) for line in res.output.strip().splitlines() if line.startswith("{")]
    assert "tool_request" in [e.get("type") for e in events]


def test_chat_interactive_safe_mode_approve(tmp_path: Path) -> None:
    """With --interactive and an approve decision on stdin, chat continues."""
    runner = CliRunner()
    decision = json.dumps({"type": "tool_decision", "decision": "approve"}) + "\n"
    res = runner.invoke(
        main,
        [
            "chat",
            "add hello world",
            "--project-dir",
            str(tmp_path),
            "--profile",
            "safe",
            "--interactive",
            "--decision-timeout",
            "5",
        ],
        input=decision,
    )
    assert res.exit_code == 0, res.output
    # When approved, we should see a tool_call event after the tool_request.
    types = [
        json.loads(line).get("type")
        for line in res.output.strip().splitlines()
        if line.startswith("{")
    ]
    assert "tool_request" in types
    assert "tool_call" in types


def test_chat_interactive_safe_mode_deny(tmp_path: Path) -> None:
    """With --interactive and a deny decision, chat exits with task_complete success=False."""
    runner = CliRunner()
    decision = json.dumps({"type": "tool_decision", "decision": "deny", "reason": "not_now"}) + "\n"
    res = runner.invoke(
        main,
        [
            "chat",
            "add hello world",
            "--project-dir",
            str(tmp_path),
            "--profile",
            "safe",
            "--interactive",
            "--decision-timeout",
            "5",
        ],
        input=decision,
    )
    assert res.exit_code == 0, res.output
    parsed = [
        json.loads(line)
        for line in res.output.strip().splitlines()
        if line.startswith("{") and '"type"' in line
    ]
    completes = [e for e in parsed if e.get("type") == "task_complete"]
    assert completes
    assert completes[-1].get("success") is False
