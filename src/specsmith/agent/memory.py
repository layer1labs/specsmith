# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Persistent session memory for the Nexus chat surface (REQ-120, REQ-125).

Every chat turn (user utterance, broker decision, task result, tool calls)
is appended as JSONL to ``.specsmith/sessions/<session_id>/turns.jsonl``.
The orchestrator prepends the most-recent turns (capped by character
budget) to its first message so the LLM has continuity across runs.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def _session_dir(project_dir: Path, session_id: str) -> Path:
    return Path(project_dir) / ".specsmith" / "sessions" / session_id


def _turns_path(project_dir: Path, session_id: str) -> Path:
    return _session_dir(project_dir, session_id) / "turns.jsonl"


def append_turn(
    project_dir: Path,
    session_id: str,
    turn: dict[str, Any],
) -> None:
    """Append ``turn`` to the session log. Adds a UTC timestamp if missing."""
    path = _turns_path(project_dir, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = dict(turn)
    record.setdefault("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def all_turns(project_dir: Path, session_id: str) -> list[dict[str, Any]]:
    """Return every recorded turn for ``session_id`` (oldest-first)."""
    path = _turns_path(project_dir, session_id)
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def recent_turns(
    project_dir: Path,
    session_id: str,
    *,
    max_chars: int = 20_000,
) -> list[dict[str, Any]]:
    """Return the most recent turns whose serialized size fits ``max_chars``.

    Truncates oldest-first so the prompt always carries the latest context.
    """
    turns = all_turns(project_dir, session_id)
    out: list[dict[str, Any]] = []
    used = 0
    for turn in reversed(turns):
        size = len(json.dumps(turn, ensure_ascii=False))
        if used + size > max_chars:
            break
        out.append(turn)
        used += size
    out.reverse()
    return out


__all__ = ["append_turn", "all_turns", "recent_turns"]
