# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Session state persistence — save and restore session context across restarts.

Files written under .specsmith/:
  session-state.json         — latest SessionContext snapshot
  conversation-history.jsonl — last N conversation turns (capped at MAX_TURNS)

On ``init_session()``, the previous session state is loaded and injected
as the first synthetic history entry so the model has prior context.

REQ-307: Session state must survive restart; agents resume where they left off.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

MAX_TURNS = 200  # Maximum conversation turns to retain in history file


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
    state_path = specsmith_dir / "session-state.json"
    ctx_dict["saved_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _atomic_write_json(state_path, ctx_dict)

    # Write conversation-history.jsonl (capped at MAX_TURNS)
    hist_path = specsmith_dir / "conversation-history.jsonl"
    capped = history[-MAX_TURNS:]
    _atomic_write_jsonl(hist_path, capped)


def load_session(
    root: Path,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Load the previous session state and conversation history.

    Returns:
        (ctx_dict | None, history_turns)
    """
    specsmith_dir = root / ".specsmith"

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
