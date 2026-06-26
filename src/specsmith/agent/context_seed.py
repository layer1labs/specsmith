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
import uuid
from collections.abc import Sequence
from datetime import datetime, timezone
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

    REQ-407: ESDB-first ledger snippet (falls back to LEDGER.md).
    REQ-415: auto-tune seed parameters from EFF-CURRENT.
    REQ-416: write context_usage record per build_context_seed() call.

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
    session_id = uuid.uuid4().hex[:16].upper()
    turns: list[dict[str, Any]] = []
    used = 0

    # Auto-tune parameters from EFF-CURRENT (REQ-415)
    eff = _load_efficiency_params(root)
    if eff.get("degraded"):
        # Reduce budget when context is degraded to force tighter seeds
        char_budget = int(char_budget * 0.75)
    if eff.get("context_char_efficiency") is not None:
        # Scale max_ledger based on fill efficiency: high fill → fewer ledger lines
        fill_eff = float(eff["context_char_efficiency"])
        if fill_eff > 0.9:
            max_ledger = max(10, max_ledger // 2)

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

    # ── 3. Recent LEDGER entries — ESDB-first (REQ-407) ─────────────────
    ledger_block = _load_ledger_snippet(root, max_lines=max_ledger)
    if ledger_block and used + len(ledger_block) <= char_budget:
        turns.append(
            {
                "role": "system",
                "content": f"[Recent LEDGER entries — last {max_ledger} lines]\n{ledger_block}",
            }
        )
        used += len(ledger_block)

    # ── 4. Efficiency degradation warning ────────────────────────────────
    if eff.get("degraded"):
        eq_score = eff.get("epistemic_quality_score", 0.0)
        tpc = eff.get("tokens_per_correct_answer")
        baseline = eff.get("baseline_tokens_per_pass")
        warn_parts = ["[EFFICIENCY WARNING: context degraded"]
        if tpc is not None and baseline is not None:
            warn_parts.append(f"tokens/pass={tpc:.0f} vs baseline={baseline:.0f}")
        if eq_score:
            warn_parts.append(f"epistemic_quality={eq_score:.2f}")
        warn_parts.append("— consider specsmith esdb sweep]")
        warn_content = " ".join(warn_parts)
        turns.append({"role": "system", "content": warn_content})
        used += len(warn_content)

    # ── 5. ESDB records — relevance-based by kind (REQ-399) ──────────────
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
        used += len(esdb_block)

    # ── 6. Write context_usage record (REQ-416) ──────────────────────────
    _write_context_usage(
        root,
        session_id=session_id,
        seed_chars=used,
        seed_fill_pct=round(used / max(1, char_budget) * 100.0, 1),
        turns_count=len(turns),
        degraded=bool(eff.get("degraded")),
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
    """Return the last ``max_lines`` of ledger entries — ESDB-first (REQ-407).

    Query order:
      1. ESDB ``ledger_event`` records (sorted by timestamp desc).
      2. Fall back to LEDGER.md file if ESDB has no ledger_event records.
    """
    # 1. Try ESDB first
    try:
        from specsmith.esdb import SqliteStore

        sqlite_path = root / ".specsmith" / "esdb.sqlite3"
        if sqlite_path.exists():
            with SqliteStore(root) as store:
                records = store.query(kind="ledger_event", status="active")
            if records:
                # Sort newest first by timestamp in data, then take last max_lines
                def _ts(r: Any) -> str:
                    return str(r.data.get("timestamp") or "")

                sorted_recs = sorted(records, key=_ts, reverse=True)[:max_lines]
                lines_out = [
                    f"{r.data.get('timestamp', '')[:16]} — {r.label[:120]}"
                    for r in sorted_recs
                ]
                return "\n".join(lines_out)
    except Exception:  # noqa: BLE001
        pass

    # 2. Fall back to LEDGER.md file
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


def _load_efficiency_params(root: Path) -> dict[str, Any]:
    """Load EFF-CURRENT from ESDB and return its data dict (REQ-415).

    Returns an empty dict on any error (best-effort).
    """
    try:
        from specsmith.esdb import SqliteStore

        sqlite_path = root / ".specsmith" / "esdb.sqlite3"
        if not sqlite_path.exists():
            return {}
        with SqliteStore(root) as store:
            rec = store.get("EFF-CURRENT")
        if rec is None:
            return {}
        data = dict(rec.data)
        # Flatten epistemic_quality score for convenience
        eq = data.get("epistemic_quality")
        if isinstance(eq, dict):
            data["epistemic_quality_score"] = eq.get("score", 0.0)
        return data
    except Exception:  # noqa: BLE001
        return {}


def _write_context_usage(
    root: Path,
    *,
    session_id: str,
    seed_chars: int,
    seed_fill_pct: float,
    turns_count: int,
    degraded: bool,
) -> None:
    """Write a context_usage record to ESDB (REQ-416, best-effort)."""
    try:
        from specsmith.esdb import SqliteRecord, open_default_store

        rec_id = f"CTX-{session_id}"
        record = SqliteRecord(
            id=rec_id,
            kind="context_usage",
            status="active",
            label=f"seed session={session_id} fill={seed_fill_pct:.1f}%",
            confidence=1.0,
            data={
                "session_id": session_id,
                "seed_chars": seed_chars,
                "seed_fill_pct": seed_fill_pct,
                "turns_count": turns_count,
                "degraded_at_seed": degraded,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        with open_default_store(root, warn=False) as store:
            store.upsert(record)
    except Exception:  # noqa: BLE001
        pass


__all__ = ["build_context_seed"]
