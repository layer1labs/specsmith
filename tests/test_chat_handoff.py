# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from specsmith.chat_handoff import (
    build_handoff,
    render_handoff_context,
    store_handoff,
    validate_handoff,
)
from specsmith.commands.zoo_code import zoo_code_group
from specsmith.context_orchestrator import ContextOrchestrator, OptimizeResultEx
from specsmith.session_store import save_session


def _history() -> list[dict[str, str]]:
    return [
        {"role": "user", "content": "Decide how to preserve provenance."},
        {"role": "assistant", "content": "Use stable source identifiers."},
        {"role": "user", "content": "Keep uncertainty explicit."},
        {"role": "assistant", "content": "Use an extractive handoff."},
        {"role": "user", "content": "Continue implementation."},
    ]


def test_handoff_is_extractive_and_valid() -> None:
    handoff = build_handoff(_history(), work_item_ids=["WI-TEST", "WI-TEST"])

    assert handoff["confidence"] == 1.0
    assert handoff["work_item_ids"] == ["WI-TEST"]
    assert handoff["turns"][0]["source_id"].startswith("turn:")
    assert "verify source IDs" in render_handoff_context(handoff)


def test_handoff_rejects_unproven_confidence() -> None:
    handoff = build_handoff(_history())
    handoff["confidence"] = 0.8

    with pytest.raises(ValueError, match="confidence"):
        validate_handoff(handoff)


def test_handoff_persists_to_sqlite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPECSMITH_ESDB_BACKEND", "sqlite")
    handoff = build_handoff(_history())
    store_handoff(tmp_path, handoff)

    from specsmith.esdb import SqliteStore

    with SqliteStore(tmp_path) as store:
        assert store.get(handoff["id"]) is not None


def test_tier_two_replaces_history_with_a_provenance_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SPECSMITH_ESDB_BACKEND", "sqlite")
    result = OptimizeResultEx(history=_history())
    ContextOrchestrator(tmp_path)._run_tier2(result)

    assert result.history[0]["content"].startswith("[Epistemic handoff HANDOFF-")
    assert len(result.history) == 4


def test_zoo_code_exports_portable_handoff(tmp_path: Path) -> None:
    save_session(tmp_path, {"work_item_ids": ["WI-TEST"]}, _history())
    output = tmp_path / "handoff.json"
    result = CliRunner().invoke(
        zoo_code_group,
        ["export-handoff", "--project-dir", str(tmp_path), "--output", str(output)],
    )

    assert result.exit_code == 0, result.output
    exported = json.loads(output.read_text(encoding="utf-8"))
    assert exported["kind"] == "epistemic_chat_handoff"
