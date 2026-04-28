# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""End-to-end Nexus pipeline test (REQ-110, TEST-110).

Exercises broker -> chat -> verify entirely in-process, with a fake
orchestrator that mirrors the Nexus output contract. This complements
the unit tests in `tests/test_phase1_4_new.py` by checking that the
parts compose correctly when wired through the click command line.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture(autouse=True)
def _silence_autoupdate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable the PyPI/spec-version notifier so stdout stays JSON-only."""
    monkeypatch.setenv("SPECSMITH_NO_AUTO_UPDATE", "1")
    monkeypatch.setenv("SPECSMITH_PYPI_CHECKED", "1")


@pytest.fixture()
def synthetic_project(tmp_path: Path) -> Path:
    """Build a tiny project with one accepted requirement."""
    (tmp_path / "REQUIREMENTS.md").write_text(
        "# Requirements\n\n## REQ-001\n"
        "- **Component**: hello\n"
        "- **Status**: Accepted\n"
        "- **Description**: Print hello world greeting message.\n",
        encoding="utf-8",
    )
    (tmp_path / "TESTS.md").write_text(
        "# Tests\n\n## TEST-001\n"
        "- **ID:** TEST-001\n"
        "- **Requirement ID:** REQ-001\n",
        encoding="utf-8",
    )
    (tmp_path / "LEDGER.md").write_text("# Ledger\n", encoding="utf-8")
    (tmp_path / ".specsmith").mkdir()
    return tmp_path


def test_e2e_preflight_chat_verify(synthetic_project: Path) -> None:
    """REQ-110: broker -> chat -> verify produces a coherent JSONL trail."""
    from specsmith.cli import main

    runner = CliRunner()

    # Step 1: preflight predicts an intent + work item. We use --predict-only
    # so the read-only ask path always lands on `accepted` and the test does
    # not depend on scope-keyword matching heuristics.
    result = runner.invoke(
        main,
        [
            "preflight",
            "summarize the hello component",
            "--project-dir",
            str(synthetic_project),
            "--predict-only",
        ],
    )
    assert result.exit_code == 0, result.output
    decision = json.loads(result.output)
    assert decision["decision"] == "accepted"
    assert decision["intent"] == "read_only_ask"

    # Step 2: chat (standard profile) emits the block protocol.
    result = runner.invoke(
        main,
        [
            "chat",
            "add hello world",
            "--project-dir",
            str(synthetic_project),
            "--session-id",
            "sess_e2e",
        ],
    )
    assert result.exit_code == 0, result.output
    events = [json.loads(line) for line in result.output.splitlines() if line.startswith("{")]
    kinds = {e.get("type") for e in events}
    assert "block_start" in kinds
    assert "task_complete" in kinds

    # Session log was persisted (REQ-120).
    turns = (synthetic_project / ".specsmith" / "sessions" / "sess_e2e" / "turns.jsonl")
    assert turns.is_file()
    payload = [json.loads(line) for line in turns.read_text(encoding="utf-8").splitlines() if line]
    assert payload[-1]["utterance"] == "add hello world"

    # Step 3: verify with reviewer comment (REQ-116).
    diff_path = synthetic_project / "fake.diff"
    diff_path.write_text("--- a\n+++ b\n@@\n-x\n+y\n", encoding="utf-8")
    tests_path = synthetic_project / "tests.json"
    tests_path.write_text(json.dumps({"passed": 1, "failed": 0}), encoding="utf-8")
    result = runner.invoke(
        main,
        [
            "verify",
            "--project-dir",
            str(synthetic_project),
            "--diff",
            str(diff_path),
            "--tests",
            str(tests_path),
            "--changed",
            "src/hello.py",
            "--comment",
            "please add a docstring",
        ],
    )
    assert result.exit_code == 0, result.output
    verdict = json.loads(result.output)
    assert verdict["equilibrium"] is True
    assert verdict["reviewer_comment"] == "please add a docstring"


def test_e2e_chat_safe_mode_emits_tool_request(synthetic_project: Path) -> None:
    """REQ-115: ``--profile safe`` issues a tool_request, not a tool_call."""
    from specsmith.cli import main

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "chat",
            "add hello world",
            "--project-dir",
            str(synthetic_project),
            "--profile",
            "safe",
            "--session-id",
            "sess_safe",
        ],
    )
    assert result.exit_code == 0, result.output
    types = [
        json.loads(line).get("type")
        for line in result.output.splitlines()
        if line.startswith("{")
    ]
    assert "tool_request" in types
    assert "tool_call" not in types
