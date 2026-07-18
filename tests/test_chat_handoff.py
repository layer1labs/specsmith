# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for chat handoff and context rendering.

Traceability:
    __trace_id__ = "REQ-317"  — verifies handoff context propagation.
"""

from __future__ import annotations

# Traceability marker: all tests in this module verify REQ-317
__trace_id__ = "REQ-317"

from pathlib import Path

import pytest

from specsmith.chat_handoff import (
    build_handoff,
    render_handoff_context,
    store_handoff,
    validate_handoff,
)


def _history() -> list[dict[str, str]]:
    return [
        {"role": "user", "content": "Decide how to preserve provenance."},
        {"role": "assistant", "content": "Use stable source identifiers."},
        {"role": "user", "content": "Keep uncertainty explicit."},
        {"role": "assistant", "content": "Use an extractive handoff."},
        {"role": "user", "content": "Continue implementation."},
    ]


# --- REQ-317: Handoff context propagation tests ---


def test_handoff_is_extractive_and_valid() -> None:
    """TEST-317-01: Handoff must be extractive with valid confidence."""
    handoff = build_handoff(_history(), work_item_ids=["WI-TEST", "WI-TEST"])

    assert handoff["confidence"] == 1.0
    assert handoff["work_item_ids"] == ["WI-TEST"]
    assert handoff["turns"][0]["source_id"].startswith("turn:")
    assert "verify source IDs" in render_handoff_context(handoff)


def test_handoff_rejects_unproven_confidence() -> None:
    """TEST-317-02: Handoff with unproven confidence must be rejected."""
    handoff = build_handoff(_history())
    handoff["confidence"] = 0.8

    with pytest.raises(ValueError, match="confidence"):
        validate_handoff(handoff)


def test_handoff_persists_to_sqlite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-317-03: Handoff must persist to SQLite backend."""
    monkeypatch.setenv("SPECSMITH_ESDB_BACKEND", "sqlite")
    handoff = build_handoff(_history(), work_item_ids=["WI-TEST"])

    store_handoff(tmp_path, handoff)

    # Verify the handoff was stored in the ESDB SQLite store
    from specsmith.esdb import SqliteStore

    with SqliteStore(tmp_path) as store:
        records = store.query(kind="chat_handoff")
        assert len(records) >= 1
        assert records[0].data["confidence"] == 1.0
        assert "WI-TEST" in records[0].data.get("work_item_ids", [])
