# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Per-block share/export for `specsmith chat` (REQ-134).

Reads ``.specsmith/sessions/<session_id>/events.jsonl`` (the chat replay log
or, fallback, ``turns.jsonl``) and slices a single block out as a
self-contained Markdown / JSON / HTML snippet.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def _events_path(project_dir: Path, session_id: str) -> Path | None:
    base = project_dir / ".specsmith" / "sessions" / session_id
    candidates = [
        base / "events.jsonl",
        base / "turns.jsonl",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def _read_events(events_path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def slice_block(events: list[dict[str, Any]], block_id: str) -> list[dict[str, Any]]:
    """Return all events tagged with ``block_id``, plus the bracketing
    block_start/block_complete events that defined it.
    """
    out: list[dict[str, Any]] = []
    for evt in events:
        if evt.get("block_id") == block_id or evt.get("id") == block_id:
            out.append(evt)
    return out


def export_block(
    project_dir: Path,
    session_id: str,
    block_id: str,
    *,
    fmt: str = "md",
) -> str:
    """Export the events for ``block_id`` as a string in ``fmt``.

    Raises FileNotFoundError if no session log exists.
    Raises KeyError if the block is not found.
    """
    events_path = _events_path(project_dir, session_id)
    if events_path is None:
        raise FileNotFoundError(f"No session log for {session_id} in {project_dir}")
    events = _read_events(events_path)
    matching = slice_block(events, block_id)
    if not matching:
        raise KeyError(f"block_id {block_id} not found in session {session_id}")
    if fmt == "json":
        return json.dumps(matching, indent=2)
    if fmt == "html":
        rows = "".join(
            f"<li><pre>{html.escape(json.dumps(evt, indent=2))}</pre></li>" for evt in matching
        )
        return (
            f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<title>specsmith block {html.escape(block_id)}</title></head>"
            f"<body><h1>Block {html.escape(block_id)}</h1>"
            f"<p>session {html.escape(session_id)}</p><ol>{rows}</ol></body></html>"
        )
    # default: markdown
    lines: list[str] = [
        f"# Block `{block_id}`",
        f"_session_: `{session_id}`",
        "",
    ]
    for evt in matching:
        kind = str(evt.get("type", "event"))
        lines.append(f"## {kind}")
        if "text" in evt:
            lines.append(str(evt["text"]))
        else:
            lines.append("```json")
            lines.append(json.dumps(evt, indent=2))
            lines.append("```")
        lines.append("")
    return "\n".join(lines)


__all__ = ["export_block", "slice_block"]
