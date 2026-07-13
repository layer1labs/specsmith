# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Session state persistence — save and restore session context across restarts.

Files written under .specsmith/:
  session-state.json         — latest SessionContext snapshot
  conversation-history.jsonl — last N conversation turns (capped at MAX_TURNS)

On ``init_session()``, the previous session state is loaded and injected
as the first synthetic history entry so the model has prior context.

REQ-307: Session state must survive restart; agents resume where they left off.

DEPRECATED(REQ-421): ``session-state.json`` and ``conversation-history.jsonl``
are legacy flat files with no ESDB equivalent yet; migration to ESDB session
records is tracked in docs/DEPRECATIONS.md.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

MAX_TURNS = 200  # Maximum conversation turns to retain in history file
_EVENTS_FILE = "session-events.jsonl"


def save_session(
    root: Path,
    ctx_dict: dict[str, Any],
    history: list[dict[str, Any]],
) -> None:
    """Atomically persist session state and conversation history.

    Args:
        root: Project root (or home dir for global sessions).
        ctx_dict: SessionContext.to_dict() output.
        history: List of {role, content} conversation turn dicts.

    """
    specsmith_dir = root / ".specsmith"
    specsmith_dir.mkdir(parents=True, exist_ok=True)

    # Write session-state.json atomically
    # DEPRECATED(REQ-421): legacy flat-file session snapshot; ESDB migration
    # tracked in docs/DEPRECATIONS.md.
    state_path = specsmith_dir / "session-state.json"
    ctx_dict["saved_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _atomic_write_json(state_path, ctx_dict)

    # Write conversation-history.jsonl (capped at MAX_TURNS)
    # DEPRECATED(REQ-421): legacy flat-file conversation history; see DEPRECATIONS.md.
    hist_path = specsmith_dir / "conversation-history.jsonl"
    capped = history[-MAX_TURNS:]
    _atomic_write_jsonl(hist_path, capped)

    # Canonical, merge-friendly session history. SQLite remains a local index;
    # this append-only text artifact is safe to review and reconcile in Git.
    events_path = root / ".chronomemory" / _EVENTS_FILE
    events_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "schema_version": 1,
        "saved_at": ctx_dict["saved_at"],
        "context": ctx_dict,
        "history": capped,
    }
    canonical = json.dumps(event, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16].upper()
    event["event_id"] = "SESSION-" + digest
    existing = _load_events(events_path)
    _atomic_write_jsonl(events_path, merge_session_events(existing, [event]))


def load_session(
    root: Path,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Load the previous session state and conversation history.

    Returns:
        (ctx_dict | None, history_turns)

    """
    specsmith_dir = root / ".specsmith"
    events = _load_events(root / ".chronomemory" / _EVENTS_FILE)
    if events:
        valid = [
            event
            for event in events
            if event.get("schema_version") == 1 and isinstance(event.get("context"), dict)
        ]
        if valid:
            latest = max(valid, key=lambda e: str(e.get("saved_at", "")))
            history = latest.get("history", [])
            if isinstance(history, list) and all(isinstance(turn, dict) for turn in history):
                return dict(latest["context"]), history

    # Load session state
    state_path = specsmith_dir / "session-state.json"
    ctx_dict: dict[str, Any] | None = None
    if state_path.is_file():
        try:
            ctx_dict = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            ctx_dict = None

    # Load conversation history
    hist_path = specsmith_dir / "conversation-history.jsonl"
    history: list[dict[str, Any]] = []
    if hist_path.is_file():
        try:
            for line in hist_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    history.append(json.loads(line))
        except Exception:  # noqa: BLE001
            history = []

    return ctx_dict, history


def merge_session_events(*event_sets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge branch event sets by immutable ID in deterministic replay order."""
    merged: dict[str, dict[str, Any]] = {}
    for events in event_sets:
        for event in events:
            event_id = event.get("event_id")
            if not isinstance(event_id, str) or not event_id.startswith("SESSION-"):
                continue
            existing = merged.get(event_id)
            if existing is None:
                merged[event_id] = event
            elif json.dumps(existing, sort_keys=True) != json.dumps(event, sort_keys=True):
                raise ValueError(f"conflicting session event ID: {event_id}")
    return sorted(
        merged.values(), key=lambda event: (str(event.get("saved_at", "")), event["event_id"])
    )


def rebuild_local_session_index(root: Path) -> int:
    """Rebuild local SQLite session records from canonical session events."""
    from specsmith.esdb import SqliteRecord, SqliteStore

    events = merge_session_events(_load_events(root / ".chronomemory" / _EVENTS_FILE))
    with SqliteStore(root) as store:
        for event in events:
            store.upsert(
                SqliteRecord(
                    id=event["event_id"],
                    kind="session_event",
                    label="Canonical session event",
                    confidence=1.0,
                    data=event,
                )
            )
    return len(events)


def make_resume_message(ctx_dict: dict[str, Any]) -> dict[str, Any]:
    """Build a synthetic assistant turn to inject at the start of a resumed session.

    This gives the model awareness that it is resuming rather than starting fresh,
    and summarises key state from the previous session.
    """
    session_id = ctx_dict.get("session_id", "unknown")
    saved_at = ctx_dict.get("saved_at", "")
    project = ctx_dict.get("project_name", ctx_dict.get("project_dir", ""))
    phase = ctx_dict.get("phase_label", ctx_dict.get("phase", ""))
    health = ctx_dict.get("health_score", "?")
    compliance = ctx_dict.get("compliance_score", "?")

    parts = [
        f"[Resuming session {session_id}",
        f"saved at {saved_at}" if saved_at else "",
        f"Project: {project}" if project else "",
        f"Phase: {phase}" if phase else "",
        f"Health: {health}%  Compliance: {compliance}%" if isinstance(health, int) else "",
    ]
    summary = " | ".join(p for p in parts if p) + "]"

    return {"role": "assistant", "content": summary}


def save_if_governed(root: Path, ctx_dict: dict[str, Any], history: list[dict[str, Any]]) -> bool:
    """Save session state only if the project has a .specsmith/ directory.

    Returns True if saved, False if the project is not governed.
    """
    if not (root / ".specsmith").is_dir():
        return False
    try:
        save_session(root, ctx_dict, history)
        return True
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    """Write JSON atomically via temp→rename."""
    content = json.dumps(data, indent=2, ensure_ascii=False)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(str(tmp), str(path))


def _atomic_write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    """Write JSONL atomically via temp→rename."""
    lines = [json.dumps(r, ensure_ascii=False) for r in records]
    content = "\n".join(lines) + ("\n" if lines else "")
    tmp = path.with_suffix(".jsonl.tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(str(tmp), str(path))


def _load_events(path: Path) -> list[dict[str, Any]]:
    """Read well-formed canonical events, ignoring malformed merge remnants."""
    if not path.is_file():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events
