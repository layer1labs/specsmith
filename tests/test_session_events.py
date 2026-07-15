from __future__ import annotations

import json
from pathlib import Path

import pytest

from specsmith.session_store import (
    _load_events,
    load_session,
    merge_session_events,
    rebuild_local_session_index,
    save_session,
)


def test_divergent_session_events_merge_and_recover(tmp_path: Path) -> None:
    left = {
        "schema_version": 1,
        "event_id": "SESSION-LEFT",
        "saved_at": "2026-01-01T00:00:00Z",
        "context": {"id": "left"},
        "history": [],
    }
    right = {
        "schema_version": 1,
        "event_id": "SESSION-RIGHT",
        "saved_at": "2026-01-02T00:00:00Z",
        "context": {"id": "right"},
        "history": [],
    }
    merged = merge_session_events([right], [left], [right])
    assert [event["event_id"] for event in merged] == ["SESSION-LEFT", "SESSION-RIGHT"]

    event_path = tmp_path / ".chronomemory" / "session-events.jsonl"
    event_path.parent.mkdir()
    event_path.write_text("\n".join(json.dumps(event) for event in merged), encoding="utf-8")
    context, history = load_session(tmp_path)
    assert context == {"id": "right"}
    assert history == []


def test_conflicting_event_id_is_rejected() -> None:
    first = {"event_id": "SESSION-SAME", "saved_at": "1"}
    second = {"event_id": "SESSION-SAME", "saved_at": "2"}
    with pytest.raises(ValueError, match="conflicting"):
        merge_session_events([first], [second])


def test_rebuild_local_index_from_canonical_events(tmp_path: Path) -> None:
    save_session(tmp_path, {"session_id": "one"}, [{"role": "user", "content": "hello"}])
    assert len(_load_events(tmp_path / ".chronomemory" / "session-events.jsonl")) == 1
    assert rebuild_local_session_index(tmp_path) == 1
