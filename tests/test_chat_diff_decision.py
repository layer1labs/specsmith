# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for `specsmith chat --interactive` inline diff-decision flow.

The diff-decision protocol is the second half of the interactive contract
(``test_chat_stdin_protocol`` covers tool_decision). When the broker
matches a requirement, the chat command emits one diff block per matched
REQ and consumes a ``diff_decision`` JSON line from stdin per block. A
non-accept verdict with a ``comment`` field becomes the next-retry
reviewer comment (REQ-116).
"""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from specsmith.cli import main

REQUIREMENTS_MD = """# Requirements

## 1. Hello world greeter

- **ID:** REQ-001
- **Description:** Implement a hello world greeter so the agent can introduce itself.
"""


def _seed_project(tmp_path: Path) -> None:
    """Write the minimum REQUIREMENTS.md so the broker has a scope match."""
    (tmp_path / "REQUIREMENTS.md").write_text(REQUIREMENTS_MD, encoding="utf-8")


def _events(output: str) -> list[dict]:
    return [
        json.loads(line)
        for line in output.splitlines()
        if line.startswith("{") and '"type"' in line
    ]


def test_chat_interactive_diff_decision_emits_diff_block(tmp_path: Path) -> None:
    """A matched REQ should produce a diff block_start whose status accepts."""
    _seed_project(tmp_path)
    runner = CliRunner()
    decisions = (
        json.dumps({"type": "tool_decision", "decision": "approve"})
        + "\n"
        + json.dumps({"type": "diff_decision", "decision": "accept"})
        + "\n"
    )
    res = runner.invoke(
        main,
        [
            "chat",
            "add hello world greeter",
            "--project-dir",
            str(tmp_path),
            "--profile",
            "safe",
            "--interactive",
            "--decision-timeout",
            "5",
        ],
        input=decisions,
        env={"SPECSMITH_DISABLE_REAL_CHAT": "1"},
    )
    assert res.exit_code == 0, res.output
    events = _events(res.output)
    diff_blocks = [e for e in events if e.get("type") == "block_start" and e.get("kind") == "diff"]
    assert diff_blocks, "expected at least one diff block_start"
    diff_completes = [
        e
        for e in events
        if e.get("type") == "block_complete" and e.get("block_id") == diff_blocks[0]["block_id"]
    ]
    assert diff_completes, "diff block should have been completed"
    assert diff_completes[-1]["payload"].get("status") == "accept"


def test_chat_interactive_diff_decision_reject_threads_comment(tmp_path: Path) -> None:
    """A non-accept verdict with a comment should fold into the final summary."""
    _seed_project(tmp_path)
    runner = CliRunner()
    decisions = (
        json.dumps({"type": "tool_decision", "decision": "approve"})
        + "\n"
        + json.dumps(
            {
                "type": "diff_decision",
                "decision": "reject",
                "comment": "use uppercase greeting",
            }
        )
        + "\n"
    )
    res = runner.invoke(
        main,
        [
            "chat",
            "add hello world greeter",
            "--project-dir",
            str(tmp_path),
            "--profile",
            "safe",
            "--interactive",
            "--decision-timeout",
            "5",
        ],
        input=decisions,
        env={"SPECSMITH_DISABLE_REAL_CHAT": "1"},
    )
    assert res.exit_code == 0, res.output
    events = _events(res.output)
    diff_completes = [
        e
        for e in events
        if e.get("type") == "block_complete" and e.get("payload", {}).get("status") == "reject"
    ]
    assert diff_completes, "expected the diff block to be completed with reject status"
    completes = [e for e in events if e.get("type") == "task_complete"]
    assert completes
    assert "use uppercase greeting" in completes[-1].get("summary", "")


def test_chat_interactive_diff_decision_timeout_uses_timeout_status(
    tmp_path: Path,
) -> None:
    """No diff_decision on stdin should mark the diff block as timeout."""
    _seed_project(tmp_path)
    runner = CliRunner()
    decisions = json.dumps({"type": "tool_decision", "decision": "approve"}) + "\n"
    res = runner.invoke(
        main,
        [
            "chat",
            "add hello world greeter",
            "--project-dir",
            str(tmp_path),
            "--profile",
            "safe",
            "--interactive",
            "--decision-timeout",
            "1",
        ],
        input=decisions,
        env={"SPECSMITH_DISABLE_REAL_CHAT": "1"},
    )
    assert res.exit_code == 0, res.output
    events = _events(res.output)
    diff_completes = [
        e
        for e in events
        if e.get("type") == "block_complete" and e.get("payload", {}).get("status") == "timeout"
    ]
    assert diff_completes, "expected at least one diff block to time out"
