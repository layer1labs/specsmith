# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""specsmith.efficiency — EFF-CURRENT rolling efficiency metric + epistemic quality (REQ-403..416).

Provides two public functions:

``compute_epistemic_quality(root)``
    Computes a 5-dimension composite epistemic quality score from the current ESDB
    state.  Returns a dict with individual dimension scores and the composite.

``compute_and_upsert_efficiency(root)``
    Reads session_metric, token_metric and context_usage records from ESDB,
    computes rolling stats, appends epistemic quality, and upserts the result
    as ``EFF-CURRENT`` (kind=``efficiency_metric``).

Both functions are **best-effort** — all errors are silently swallowed so a
broken ESDB state can never prevent callers from proceeding.

``EFF-CURRENT`` is a single upserted record (confidence=1.0, never evicted)
that serves as the live project efficiency dashboard.  It is read by:
  - ``build_context_seed()``   → auto-tune seed parameters
  - ``ContextOrchestrator``    → adjust compression tier thresholds
  - ``specsmith inspect``      → display efficiency + quality in the inspect block

REQ-411: efficiency_metric EFF-CURRENT record
REQ-414: epistemic quality score in EFF-CURRENT
REQ-415: context_seed auto-tune from EFF-CURRENT
"""

from __future__ import annotations

import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_epistemic_quality(root: str | Path) -> dict[str, float]:
    """Compute a 5-dimension epistemic quality score from ESDB active records.

    Dimensions (each 0.0–1.0):
      confidence_density (weight 0.30) — fraction of active records with conf ≥ 0.7
      recency_score      (weight 0.20) — fraction of records with timestamp < 90 days ago
      coherence_score    (weight 0.20) — fraction of active WIs that have a PF-{id} record
      closure_score      (weight 0.15) — min(1, verify_result_count / active_preflight_count)
      non_contradiction  (weight 0.15) — 1 − duplicate_ratio (label[:60] deduplicate)

    Composite = weighted sum, clamped to [0.0, 1.0].
    Falls back to all-zeros on any error.
    """
    _ZERO: dict[str, float] = {
        "score": 0.0,
        "confidence_density": 0.0,
        "recency_score": 0.0,
        "coherence_score": 0.0,
        "closure_score": 0.0,
        "non_contradiction_score": 0.0,
    }
    try:
        from specsmith.esdb import SqliteStore

        sqlite_path = Path(root) / ".specsmith" / "esdb.sqlite3"
        if not sqlite_path.exists():
            return _ZERO

        cutoff_90d = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")

        with SqliteStore(Path(root)) as store:
            active = store.query(status="active")
            all_records = store.query(status="")  # all statuses for counting

        if not active:
            return _ZERO

        total = len(active)

        # 1. Confidence density
        high_conf = sum(1 for r in active if r.confidence >= 0.7)
        confidence_density = high_conf / total

        # 2. Recency score — use timestamp in data; fall back to insertion order
        recent = 0
        for r in active:
            ts = r.data.get("timestamp") or r.data.get("computed_at") or ""
            if ts and ts[:10] >= cutoff_90d:
                recent += 1
            elif not ts:
                # No timestamp — treat as recent (new records without timestamps)
                recent += 1
        recency_score = recent / total

        # 3. Coherence — WIs with matching preflight
        wi_records = [r for r in active if r.kind == "work_item"]
        if wi_records:
            active_ids = {r.id for r in all_records if r.status == "active"}
            wi_with_pf = sum(1 for wi in wi_records if f"PF-{wi.id}" in active_ids)
            coherence_score = wi_with_pf / len(wi_records)
        else:
            coherence_score = 1.0  # No WIs = no coherence gap

        # 4. Closure — verify_result / active preflight_decision
        preflight_count = sum(1 for r in active if r.kind == "preflight_decision")
        verify_count = sum(1 for r in all_records if r.kind == "verify_result")
        closure_score = min(1.0, verify_count / max(1, preflight_count))

        # 5. Non-contradiction — label deduplication
        seen_labels: set[str] = set()
        duplicates = 0
        for r in active:
            if not r.label:
                continue
            key = r.label[:60].lower().strip()
            if key in seen_labels:
                duplicates += 1
            else:
                seen_labels.add(key)
        non_contradiction_score = 1.0 - (duplicates / total)

        composite = (
            0.30 * confidence_density
            + 0.20 * recency_score
            + 0.20 * coherence_score
            + 0.15 * closure_score
            + 0.15 * non_contradiction_score
        )
        composite = max(0.0, min(1.0, composite))

        return {
            "score": round(composite, 4),
            "confidence_density": round(confidence_density, 4),
            "recency_score": round(recency_score, 4),
            "coherence_score": round(coherence_score, 4),
            "closure_score": round(closure_score, 4),
            "non_contradiction_score": round(non_contradiction_score, 4),
        }
    except Exception:  # noqa: BLE001
        return _ZERO


def compute_and_upsert_efficiency(root: str | Path) -> bool:
    """Compute rolling efficiency stats and upsert EFF-CURRENT to ESDB (REQ-411).

    Reads the last 20 session_metric, token_metric, and context_usage records.
    Computes benchmark stats, epistemic quality, and degradation flag.
    Upserts ``SqliteRecord(id="EFF-CURRENT", kind="efficiency_metric", ...)``.

    Returns True on success, False on error (error is swallowed).
    """
    try:
        from specsmith.esdb import SqliteRecord, SqliteStore, open_default_store

        root_path = Path(root)
        sqlite_path = root_path / ".specsmith" / "esdb.sqlite3"
        if not sqlite_path.exists():
            # Store will be created on first write — nothing to compute yet
            return False

        with SqliteStore(root_path) as store:
            session_records = store.query(kind="session_metric", status="active")
            context_records = store.query(kind="context_usage", status="active")
            all_active = store.query(status="active")

        # Sort by timestamp desc, take last 20 for rolling window
        def _ts(r: Any) -> str:
            return str(r.data.get("timestamp") or r.data.get("computed_at") or "")

        session_recent = sorted(session_records, key=_ts, reverse=True)[:20]
        session_50 = sorted(session_records, key=_ts, reverse=True)[:50]

        # --- Rolling metrics from session_metric records ---
        passing = [r for r in session_recent if r.data.get("passed")]
        tokens_per_correct: float | None = None
        cost_of_pass: float | None = None
        if passing:
            tok_vals = [float(r.data.get("tokens_total") or 0) for r in passing]
            cost_vals = [float(r.data.get("cost_usd") or 0) for r in passing]
            if any(v > 0 for v in tok_vals):
                tokens_per_correct = statistics.mean(v for v in tok_vals if v > 0)
            if any(v > 0 for v in cost_vals):
                cost_of_pass = statistics.mean(v for v in cost_vals if v > 0)

        # 7-day quality trend
        cutoff_7d = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()[:10]
        quality_recent = [
            float(r.data.get("quality_score") or 0)
            for r in session_recent
            if (r.data.get("timestamp") or "") >= cutoff_7d
            and float(r.data.get("quality_score") or 0) > 0
        ]
        quality_trend_7d: float | None = (
            round(statistics.mean(quality_recent), 4) if quality_recent else None
        )

        rework_vals = [float(r.data.get("rework_turns") or 1) for r in session_recent]
        mean_rework = round(statistics.mean(rework_vals), 2) if rework_vals else None

        # Baseline from last 50 sessions
        passing_50 = [r for r in session_50 if r.data.get("passed")]
        baseline: float | None = None
        if passing_50:
            b_vals = [float(r.data.get("tokens_total") or 0) for r in passing_50]
            if any(v > 0 for v in b_vals):
                baseline = statistics.mean(v for v in b_vals if v > 0)

        # Degradation detection
        degraded = False
        if tokens_per_correct is not None and baseline and baseline > 0:
            degraded = tokens_per_correct > 2.0 * baseline

        # Context char efficiency from context_usage
        ctx_recent = sorted(context_records, key=_ts, reverse=True)[:20]
        ctx_fill_vals = [
            float(r.data.get("seed_fill_pct") or 0) / 100.0
            for r in ctx_recent
            if r.data.get("seed_fill_pct") is not None
        ]
        context_char_efficiency = (
            round(statistics.mean(ctx_fill_vals), 4) if ctx_fill_vals else None
        )

        # Context health score (confidence density)
        total_active = len(all_active)
        high_conf = sum(1 for r in all_active if r.confidence >= 0.7)
        context_health_score = round(high_conf / max(1, total_active), 4)

        # Epistemic quality
        epistemic_quality = compute_epistemic_quality(root)

        data: dict[str, Any] = {
            "tokens_per_correct_answer": (
                round(tokens_per_correct, 1) if tokens_per_correct is not None else None
            ),
            "cost_of_pass_usd": (round(cost_of_pass, 6) if cost_of_pass is not None else None),
            "quality_trend_7d": quality_trend_7d,
            "mean_rework_turns": mean_rework,
            "context_char_efficiency": context_char_efficiency,
            "context_health_score": context_health_score,
            "baseline_tokens_per_pass": (round(baseline, 1) if baseline is not None else None),
            "sessions_analyzed": len(session_recent),
            "degraded": degraded,
            "epistemic_quality": epistemic_quality,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

        eq_score = epistemic_quality.get("score", 0.0)
        band = _band_label(eq_score)
        record = SqliteRecord(
            id="EFF-CURRENT",
            kind="efficiency_metric",
            status="active",
            label=f"Project efficiency snapshot (quality={eq_score:.2f} {band})",
            confidence=1.0,
            data=data,
        )
        with open_default_store(root_path, warn=False) as store:
            store.upsert(record)
        return True
    except Exception:  # noqa: BLE001
        return False


def _band_label(score: float) -> str:
    """Return human-readable quality band label."""
    if score >= 0.85:
        return "excellent"
    if score >= 0.70:
        return "good"
    if score >= 0.50:
        return "fair"
    return "poor"


def _band_emoji(score: float) -> str:
    """Return emoji for quality band."""
    if score >= 0.85:
        return "✓"
    if score >= 0.70:
        return "~"
    if score >= 0.50:
        return "!"
    return "✗"


__all__ = [
    "_band_emoji",
    "_band_label",
    "compute_and_upsert_efficiency",
    "compute_epistemic_quality",
]
