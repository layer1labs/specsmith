# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Epistemic continuity — cross-session context seed for AgentRunner.

Addresses the gap where ``AgentRunner`` always started with an empty
history, making the agent blind to prior work in the same project.

``build_context_seed()`` assembles a compact, token-budget-capped snapshot
from four sources (newest → oldest priority):

1. **Session state snapshot** (``session-state.json``) — project health,
   phase, compliance score, requirement coverage.
2. **Prior conversation turns** (``conversation-history.jsonl``) — the
   last N turns from the previous session, budget-capped.
3. **Recent LEDGER entries** — the last ``max_ledger`` lines of LEDGER.md
   so the agent knows what decisions and changes have been logged.
4. **Recent ESDB records** — the last ``max_esdb`` ChronoRecords so the
   agent knows what facts and results are in the epistemic store.

The result is a list of ``{role, content}`` dicts that can be prepended
to ``AgentRunner._history`` before the first user turn.

REQ-307: Session state must survive restart; agents resume where they
left off (extended to cover full epistemic continuity).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Maximum total characters injected as seed context.  Large enough to
# carry meaningful history; small enough not to bloat every prompt.
_SEED_CHAR_BUDGET = 8_000
_MAX_LEDGER_LINES = 30
_MAX_ESDB_RECORDS = 5


def build_context_seed(
    project_dir: str | Path,
    *,
    char_budget: int = _SEED_CHAR_BUDGET,
    max_ledger: int = _MAX_LEDGER_LINES,
    max_esdb: int = _MAX_ESDB_RECORDS,
) -> list[dict[str, Any]]:
    """Return a list of history turns to prepend to a new agent session.

    Never raises — all errors are silently swallowed so a broken project
    state or missing optional dependency can never prevent the agent from
    starting.

    Args:
        project_dir: Project root containing ``.specsmith/``.
        char_budget: Maximum total characters across all seed turns.
        max_ledger: Maximum LEDGER.md lines to include.
        max_esdb: Maximum ESDB ChronoRecords to include.

    Returns:
        List of ``{role: str, content: str}`` dicts, oldest first.
        Empty list if no prior context is available.
    """
    root = Path(project_dir).resolve()
    turns: list[dict[str, Any]] = []
    used = 0

    # ── 1. Session state snapshot ─────────────────────────────────────
    session_summary = _load_session_summary(root)
    if session_summary:
        content = _format_session_summary(session_summary)
        if used + len(content) <= char_budget:
            turns.append({"role": "system", "content": content})
            used += len(content)

    # ── 2. Prior conversation history ────────────────────────────────
    hist_turns = _load_conversation_history(root, budget=char_budget - used)
    for t in hist_turns:
        c = json.dumps(t, ensure_ascii=False)
        if used + len(c) > char_budget:
            break
        turns.append(t)
        used += len(c)

    # ── 3. Recent LEDGER entries ─────────────────────────────────────
    ledger_block = _load_ledger_snippet(root, max_lines=max_ledger)
    if ledger_block and used + len(ledger_block) <= char_budget:
        turns.append(
            {
                "role": "system",
                "content": f"[Recent LEDGER entries — last {max_ledger} lines]\n{ledger_block}",
            }
        )
        used += len(ledger_block)

    # ── 4. Recent ESDB records ───────────────────────────────────────
    esdb_block = _load_esdb_snippet(root, max_records=max_esdb)
    if esdb_block and used + len(esdb_block) <= char_budget:
        turns.append(
            {
                "role": "system",
                "content": f"[Recent ESDB records — last {max_esdb}]\n{esdb_block}",
            }
        )

    return turns


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_session_summary(root: Path) -> dict[str, Any] | None:
    """Load session-state.json if present."""
    try:
        from specsmith.session_store import load_session

        ctx_dict, _ = load_session(root)
        return ctx_dict
    except Exception:  # noqa: BLE001
        return None


def _format_session_summary(ctx: dict[str, Any]) -> str:
    """Format session state into a compact resume message."""
    try:
        from specsmith.session_store import make_resume_message

        resume = make_resume_message(ctx)
        content = str(resume.get("content") or "")
        extras = []
        if ctx.get("total_requirements"):
            covered = ctx.get("covered_requirements", 0)
            total = ctx["total_requirements"]
            extras.append(f"REQ coverage: {covered}/{total}")
        if ctx.get("total_tests"):
            extras.append(f"Tests: {ctx['total_tests']}")
        if ctx.get("health_issues"):
            issues = ctx["health_issues"][:3]
            extras.append(f"Health issues: {', '.join(issues)}")
        if extras:
            content += "  " + "  ".join(extras)
        return content
    except Exception:  # noqa: BLE001
        return ""


def _load_conversation_history(
    root: Path,
    *,
    budget: int,
) -> list[dict[str, Any]]:
    """Load prior conversation turns within budget."""
    try:
        from specsmith.session_store import load_session

        _, history = load_session(root)
        result: list[dict[str, Any]] = []
        used = 0
        for turn in reversed(history):
            s = json.dumps(turn, ensure_ascii=False)
            if used + len(s) > budget:
                break
            result.append(turn)
            used += len(s)
        result.reverse()
        return result
    except Exception:  # noqa: BLE001
        return []


def _load_ledger_snippet(root: Path, *, max_lines: int) -> str:
    """Return the last ``max_lines`` of LEDGER.md, newest-first."""
    try:
        candidates = [root / "LEDGER.md", root / "docs" / "LEDGER.md"]
        for path in candidates:
            if path.is_file():
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
                # Skip blank lines and the header, take last N non-empty lines
                content_lines = [ln for ln in lines if ln.strip() and not ln.startswith("# ")]
                snippet = content_lines[-max_lines:]
                return "\n".join(snippet)
        return ""
    except Exception:  # noqa: BLE001
        return ""


def _load_esdb_snippet(root: Path, *, max_records: int) -> str:
    """Return a compact summary of the most recent ESDB ChronoRecords."""
    try:
        from specsmith.esdb.store import ChronoStore

        with ChronoStore(root) as store:
            all_records = store.query()  # active records in insertion order
        recent = all_records[-max_records:] if len(all_records) > max_records else all_records
        if not recent:
            return ""
        lines = []
        for rec in recent:
            line = f"[{rec.id}] {rec.kind}: {rec.label}"
            if rec.data.get("summary"):
                line += f" \u2014 {str(rec.data['summary'])[:120]}"
            lines.append(line)
        return "\n".join(lines)
    except Exception:  # noqa: BLE001
        return ""


__all__ = ["build_context_seed"]
