# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
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
from collections.abc import Sequence
from pathlib import Path
from typing import Any

# Maximum total characters injected as seed context.  Raised from 8 000 to
# 12 000 to accommodate the richer per-kind ESDB query output (REQ-399).
_SEED_CHAR_BUDGET = 12_000
_MAX_LEDGER_LINES = 30
_MAX_PREFLIGHT_RECORDS = 10  # preflight_decision records (conf≥0.6)
_MAX_VERIFY_RECORDS = 5  # verify_result records (conf≥0.6)
_MAX_WI_RECORDS = 5  # work_item records (active status only)


def build_context_seed(
    project_dir: str | Path,
    *,
    char_budget: int = _SEED_CHAR_BUDGET,
    max_ledger: int = _MAX_LEDGER_LINES,
    max_preflight: int = _MAX_PREFLIGHT_RECORDS,
    max_verify: int = _MAX_VERIFY_RECORDS,
    max_wi: int = _MAX_WI_RECORDS,
) -> list[dict[str, Any]]:
    """Return a list of history turns to prepend to a new agent session.

    Never raises — all errors are silently swallowed so a broken project
    state or missing optional dependency can never prevent the agent from
    starting.

    The ESDB query is now **relevance-based** (REQ-399): records are fetched by
    kind (preflight_decision, verify_result, work_item) rather than returning
    the last N records by insertion order.  Only active records with
    confidence ≥ 0.6 are included.  This ensures epistemically low-quality
    records (failed approaches, stale decisions, low-confidence hypotheses) are
    excluded from the context window.

    Args:
        project_dir: Project root containing ``.specsmith/``.
        char_budget: Maximum total characters across all seed turns.
        max_ledger: Maximum LEDGER.md lines to include.
        max_preflight: Max preflight_decision records to include.
        max_verify: Max verify_result records to include.
        max_wi: Max active work_item records to include.

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

    # ── 2. Prior conversation history ────────────────────────────
    hist_turns = _load_conversation_history(root, budget=char_budget - used)
    for t in hist_turns:
        c = json.dumps(t, ensure_ascii=False)
        if used + len(c) > char_budget:
            break
        turns.append(t)
        used += len(c)

    # ── 3. Recent LEDGER entries ─────────────────────────────────
    ledger_block = _load_ledger_snippet(root, max_lines=max_ledger)
    if ledger_block and used + len(ledger_block) <= char_budget:
        turns.append(
            {
                "role": "system",
                "content": f"[Recent LEDGER entries — last {max_ledger} lines]\n{ledger_block}",
            }
        )
        used += len(ledger_block)

    # ── 4. ESDB records — relevance-based by kind (REQ-399) ──────────────
    esdb_block = _load_esdb_by_kind(
        root,
        max_preflight=max_preflight,
        max_verify=max_verify,
        max_wi=max_wi,
    )
    if esdb_block and used + len(esdb_block) <= char_budget:
        turns.append(
            {
                "role": "system",
                "content": (
                    "[ESDB governance context — active preflight"
                    f" decisions, verify results, work items]\n{esdb_block}"
                ),
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


def _load_esdb_by_kind(
    root: Path,
    *,
    max_preflight: int = 10,
    max_verify: int = 5,
    max_wi: int = 5,
) -> str:
    """Return a compact, epistemically-filtered ESDB context block (REQ-399).

    Queries three specific kinds rather than "last N records by insertion
    order" so the context seed is relevant regardless of store size:

    1. ``preflight_decision`` (active, conf≥0.6) — recent accepted preflights;
       sorted highest-confidence first so the best-evidenced ones appear.
    2. ``verify_result``       (active, conf≥0.6) — recent verify outcomes.
    3. ``work_item``           (active, conf≥0.6) — open/in-progress WIs.

    Falls back to ``query.what_is_known()`` for ChronoStore when the SqliteStore
    does not have records of the requested kinds (e.g. before the first preflight).

    Uses ``store.query(kind=..., rag_filter=True)`` which applies the
    confidence≥0.6 filter, honouring H18 (RAG retrieval filtering).
    Infrastructure kinds (edge, rollback_event, token_metric, skill_run) are
    never returned by this function — ESDB spec rule 3 / critical rule §23.
    """
    lines: list[str] = []
    seen_ids: set[str] = set()

    def _fmt(rec: object) -> str:
        rid = getattr(rec, "id", "?")
        kind = getattr(rec, "kind", "?")
        label = getattr(rec, "label", "")
        data = getattr(rec, "data", {}) or {}
        conf = getattr(rec, "confidence", 0.0)
        line = f"[{rid}] {kind} (conf={conf:.2f}): {label[:120]}"
        detail = (
            data.get("decision")
            or data.get("equilibrium")
            or data.get("status")
            or data.get("summary")
        )
        if detail:
            line += f" — {str(detail)[:80]}"
        return line

    def _add_records(records: Sequence[object], max_n: int) -> None:
        added = 0
        for rec in sorted(records, key=lambda r: -getattr(r, "confidence", 0)):
            if added >= max_n:
                break
            rid = getattr(rec, "id", None)
            if rid and rid not in seen_ids:
                lines.append(_fmt(rec))
                seen_ids.add(rid)
                added += 1

    # --- Try SqliteStore (always available, no external dep) -----------------
    try:
        from specsmith.esdb import SqliteStore

        sqlite_path = root / ".specsmith" / "esdb.sqlite3"
        if sqlite_path.exists():
            with SqliteStore(root) as store:
                _add_records(
                    store.query(kind="preflight_decision", rag_filter=True),
                    max_preflight,
                )
                _add_records(
                    store.query(kind="verify_result", rag_filter=True),
                    max_verify,
                )
                _add_records(
                    store.query(kind="work_item", status="active", rag_filter=True),
                    max_wi,
                )
    except Exception:  # noqa: BLE001
        pass

    # --- Supplement / fall back via ChronoStore ------------------------------
    # Only query ChronoStore when we got fewer records than requested so we
    # don't duplicate records that are in both backends.
    chrono_needed = max_preflight + max_verify + max_wi - len(seen_ids)
    if chrono_needed > 0:
        try:
            from chronomemory import ChronoStore
            from chronomemory import query as _cm_query

            with ChronoStore(root) as store:
                known = _cm_query.what_is_known(store)  # active, conf>=0.6, no infra
            # Group by kind and add missing records
            for kind_key, max_n in (
                ("preflight_decision", max_preflight),
                ("verify_result", max_verify),
                ("work_item", max_wi),
            ):
                kind_recs = [r for r in known if getattr(r, "kind", "") == kind_key]
                _add_records(kind_recs, max_n)
        except Exception:  # noqa: BLE001
            pass

    return "\n".join(lines)


__all__ = ["build_context_seed"]
