# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Unit tests for the Phase 1-4 agent modules (TEST-108..TEST-125)."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from specsmith.agent.events import EventEmitter
from specsmith.agent.memory import all_turns, append_turn, recent_turns
from specsmith.agent.router import DEFAULT_MAPPING, choose_tier
from specsmith.agent.rules import load_rules
from specsmith.agent.verifier import (
    VerifierReport,
    report_from_chat_sections,
    score,
)

# ── REQ-108 / TEST-108 ────────────────────────────────────────────────────────


def test_verifier_score_rewards_clean_runs() -> None:
    report = VerifierReport(test_passed=10, test_failed=0, has_changes=True)
    verdict = score(report, confidence_target=0.7)
    assert verdict.equilibrium is True
    assert verdict.confidence == 1.0


def test_verifier_score_punishes_failures_and_ruff_errors() -> None:
    report = VerifierReport(test_passed=5, test_failed=2, ruff_errors=1, has_changes=True)
    verdict = score(report, confidence_target=0.7)
    assert verdict.equilibrium is False
    # base capped at 0.5 (failures), then *0.7 (ruff) = 0.35
    assert verdict.confidence == pytest.approx(0.35, abs=1e-3)


def test_verifier_report_from_chat_sections_extracts_counts() -> None:
    sections = {"test_results": "5 passed, 1 failed", "diff": "--- a\n+++ b\n"}
    report = report_from_chat_sections(sections, files_changed=["a.py"])
    assert report.test_passed == 5
    assert report.test_failed == 1
    assert report.has_changes is True


# ── REQ-112..REQ-114 / TEST-112..TEST-114 ────────────────────────────────────


def test_event_emitter_jsonl_round_trip() -> None:
    buf = io.StringIO()
    emitter = EventEmitter(stream=buf)
    block = emitter.block_start("plan", agent="nexus", note="hi")
    emitter.token(block, "hello")
    emitter.tool_call(block, "verify", {"x": 1})
    emitter.block_complete(block, status="complete")
    emitter.task_complete(success=True, confidence=0.8, summary="ok", profile="standard")
    lines = [json.loads(line) for line in buf.getvalue().splitlines() if line]
    kinds = [evt["type"] for evt in lines]
    assert kinds == [
        "block_start",
        "token",
        "tool_call",
        "block_complete",
        "task_complete",
    ]


# ── REQ-119 / TEST-119 ────────────────────────────────────────────────────────


def test_load_rules_combines_governance_and_h_rules(tmp_path: Path) -> None:
    gov = tmp_path / "docs" / "governance"
    gov.mkdir(parents=True)
    (gov / "DRIFT_RULES.md").write_text("Always check ledger.\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(
        "# Hard rules\n- **H1** Never delete ledger.\n- H2 No exec.\n",
        encoding="utf-8",
    )
    rules = load_rules(tmp_path)
    assert "DRIFT_RULES" in rules
    assert "Always check ledger" in rules
    assert "H1" in rules and "H2" in rules


def test_load_rules_returns_empty_when_no_files(tmp_path: Path) -> None:
    assert load_rules(tmp_path) == ""


# ── REQ-120 / TEST-120 ────────────────────────────────────────────────────────


def test_memory_append_and_recent_turns(tmp_path: Path) -> None:
    sid = "sess_unit"
    append_turn(tmp_path, sid, {"role": "user", "utterance": "hello"})
    append_turn(tmp_path, sid, {"role": "agent", "utterance": "world"})
    full = all_turns(tmp_path, sid)
    assert [t["utterance"] for t in full] == ["hello", "world"]
    recent = recent_turns(tmp_path, sid, max_chars=80)
    # max_chars=80 only fits the most recent serialized record (which
    # includes a timestamp + role/utterance keys), not both.
    assert recent and recent[-1]["utterance"] == "world"
    assert len(recent) == 1


# ── REQ-122 / TEST-122 ────────────────────────────────────────────────────────


def test_router_default_mapping_and_retry_escalation() -> None:
    assert choose_tier("read_only_ask") == DEFAULT_MAPPING["read_only_ask"]
    assert choose_tier("change") == "coder"
    # Retries 0..1 keep the original tier.
    assert choose_tier("change", retry_count=1) == "coder"
    # Retry >= 2 escalates coder -> heavy.
    assert choose_tier("change", retry_count=2) == "heavy"


def test_router_respects_project_overrides(tmp_path: Path) -> None:
    cfg_dir = tmp_path / ".specsmith"
    cfg_dir.mkdir()
    (cfg_dir / "config.yml").write_text(
        "routing:\n  change: heavy\n  read_only_ask: fast\n", encoding="utf-8"
    )
    assert choose_tier("change", project_dir=tmp_path) == "heavy"
    assert choose_tier("read_only_ask", project_dir=tmp_path) == "fast"
