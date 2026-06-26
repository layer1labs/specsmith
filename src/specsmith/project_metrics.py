# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Project-level governance metrics — lifetime token, cost, quality, and cost-of-pass tracking.

Records are stored as append-only NDJSON at::

    <project_root>/.specsmith/session_metrics.jsonl

One record is written per ``specsmith save`` call (auto-hook) or explicitly
via ``specsmith metrics add``.  Records accumulate for the full lifetime of the
project and can be filtered by date range for period reports.

Primary metrics:
    tokens_total     — input + output tokens consumed in the session
    cost_usd         — estimated API cost (USD) for the session
    quality_score    — 0.0–1.0 judge score (manual or from harness)
    passed           — bool; session work item passed acceptance criteria
    rework_turns     — number of re-implementation turns needed (1 = first-pass)

Derived metrics:
    cost_of_pass     — mean_cost / pass_rate (expected USD per correct answer)
    quality_trend    — rolling-N-day mean quality_score
"""

from __future__ import annotations

import json
import statistics
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# DEPRECATED(REQ-421): legacy NDJSON metrics file. Superseded by the ESDB
# ``session_metric`` kind (REQ-405 dual-write in MetricsStore.append). Retained
# for back-compat reads until teardown. See docs/DEPRECATIONS.md.
_METRICS_FILE = Path(".specsmith") / "session_metrics.jsonl"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


def _ISO_NOW() -> str:  # noqa: N802
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class MetricsRecord:
    """A single session's governance metrics."""

    session_id: str
    timestamp: str  # ISO-8601 UTC

    # Token and cost
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0

    # Quality
    quality_score: float = 0.0  # 0.0–1.0 from LLM judge or manual entry
    passed: bool = False  # did this session's work item pass?
    rework_turns: int = 1  # 1 = first-pass success

    # Provenance
    work_item_id: str = ""
    model: str = ""
    command: str = ""  # the specsmith command that triggered this record
    notes: str = ""

    @property
    def tokens_total(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["tokens_total"] = self.tokens_total
        return d

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> MetricsRecord:
        return cls(
            session_id=str(raw.get("session_id") or "").strip(),
            timestamp=str(raw.get("timestamp") or _ISO_NOW()),
            input_tokens=int(raw.get("input_tokens", 0)),
            output_tokens=int(raw.get("output_tokens", 0)),
            cost_usd=float(raw.get("cost_usd", 0.0)),
            quality_score=float(raw.get("quality_score", 0.0)),
            passed=bool(raw.get("passed", False)),
            rework_turns=int(raw.get("rework_turns", 1)),
            work_item_id=str(raw.get("work_item_id") or ""),
            model=str(raw.get("model") or ""),
            command=str(raw.get("command") or ""),
            notes=str(raw.get("notes") or ""),
        )

    @classmethod
    def new(
        cls,
        *,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        quality_score: float = 0.0,
        passed: bool = False,
        rework_turns: int = 1,
        work_item_id: str = "",
        model: str = "",
        command: str = "",
        notes: str = "",
    ) -> MetricsRecord:
        """Factory for creating a new record with auto-generated session_id and timestamp."""
        return cls(
            session_id=f"S-{uuid.uuid4().hex[:8].upper()}",
            timestamp=_ISO_NOW(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
            passed=passed,
            rework_turns=rework_turns,
            work_item_id=work_item_id,
            model=model,
            command=command,
            notes=notes,
        )


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------


class MetricsStore:
    """Append-only NDJSON store for project-level governance metrics.

    Usage::

        store = MetricsStore(project_root)
        store.append(MetricsRecord.new(cost_usd=0.0015, passed=True, ...))
        records = store.load(since="2026-01-01")
        report  = store.report(since="2026-06-01")
    """

    def __init__(self, root: Path | str) -> None:
        self._root = Path(root)
        self._path = self._root / _METRICS_FILE

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def append(self, record: MetricsRecord) -> None:
        """Append one metrics record to the NDJSON file."""
        # DEPRECATED(REQ-421): legacy NDJSON write. The forward path is the ESDB
        # ``session_metric`` dual-write below (REQ-405); this file write is kept
        # until teardown. See docs/DEPRECATIONS.md.
        self._path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record.to_dict(), ensure_ascii=False)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        # Dual-write: best-effort session_metric in ESDB (REQ-405).
        try:
            from specsmith.esdb_writer import write_session_metric

            write_session_metric(self._root, record.to_dict())
        except Exception:  # noqa: BLE001
            pass

    def reset(self) -> None:
        """Erase all metrics (destructive — requires explicit caller confirmation)."""
        if self._path.exists():
            self._path.unlink()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def load(
        self,
        since: str | None = None,
        until: str | None = None,
    ) -> list[MetricsRecord]:
        """Return records, optionally filtered to a date range.

        Args:
            since: ISO-8601 date string (inclusive), e.g. ``"2026-01-01"``.
            until: ISO-8601 date string (inclusive), e.g. ``"2026-06-30"``.
        """
        if not self._path.exists():
            return []
        records: list[MetricsRecord] = []
        with self._path.open(encoding="utf-8") as fh:
            for raw_line in fh:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    raw = json.loads(raw_line)
                    if not isinstance(raw, dict):
                        continue
                    rec = MetricsRecord.from_dict(raw)
                    if since and rec.timestamp < since:
                        continue
                    if until and rec.timestamp[:10] > until:
                        continue
                    records.append(rec)
                except (json.JSONDecodeError, ValueError):
                    continue  # skip corrupt lines
        return records

    # ------------------------------------------------------------------
    # Aggregates
    # ------------------------------------------------------------------

    def cost_of_pass(
        self,
        records: list[MetricsRecord] | None = None,
        *,
        since: str | None = None,
        until: str | None = None,
    ) -> float:
        """Expected USD cost to produce one correct answer.

        cost_of_pass = mean_cost_usd / pass_rate

        Returns float('inf') if pass_rate is 0.
        """
        recs = records if records is not None else self.load(since=since, until=until)
        if not recs:
            return float("inf")
        costed = [r for r in recs if r.cost_usd > 0]
        if not costed:
            return float("inf")
        pass_rate = sum(1 for r in costed if r.passed) / len(costed)
        if pass_rate == 0:
            return float("inf")
        mean_cost = statistics.mean(r.cost_usd for r in costed)
        return mean_cost / pass_rate

    def quality_trend(
        self,
        records: list[MetricsRecord] | None = None,
        *,
        window_days: int = 7,
        since: str | None = None,
        until: str | None = None,
    ) -> float | None:
        """Rolling mean quality_score over the last ``window_days`` days.

        Returns None if no records with quality > 0 exist in the window.
        """
        recs = records if records is not None else self.load(since=since, until=until)
        if not recs:
            return None
        # Determine cutoff: window_days before the most recent record
        sorted_ts = sorted(r.timestamp for r in recs)
        if not sorted_ts:
            return None
        latest = sorted_ts[-1]
        # Simple string comparison works for ISO-8601 timestamps
        cutoff_year = int(latest[:4])
        cutoff_month = int(latest[5:7])
        cutoff_day = int(latest[8:10])
        import datetime as _dt

        latest_date = _dt.date(cutoff_year, cutoff_month, cutoff_day)
        cutoff_date = latest_date - _dt.timedelta(days=window_days)
        cutoff = cutoff_date.isoformat()
        windowed = [r for r in recs if r.timestamp[:10] >= cutoff and r.quality_score > 0]
        if not windowed:
            return None
        return statistics.mean(r.quality_score for r in windowed)

    def token_trend(
        self,
        records: list[MetricsRecord] | None = None,
        *,
        since: str | None = None,
        until: str | None = None,
    ) -> float | None:
        """Mean tokens_total across the loaded records. None if no records."""
        recs = records if records is not None else self.load(since=since, until=until)
        tokened = [r for r in recs if r.tokens_total > 0]
        if not tokened:
            return None
        return statistics.mean(r.tokens_total for r in tokened)

    def report(
        self,
        since: str | None = None,
        until: str | None = None,
    ) -> dict[str, Any]:
        """Return a summary dict suitable for CLI display or JSON output.

        Keys:
            n_sessions       — total records in range
            pass_rate        — fraction of sessions that passed
            mean_tokens      — mean total tokens per session
            mean_cost_usd    — mean cost per session
            total_cost_usd   — cumulative cost in range
            cost_of_pass     — expected cost per correct answer
            mean_quality     — mean quality_score (>0 sessions only)
            quality_7d       — 7-day rolling quality mean
            mean_rework      — mean rework_turns
            since            — applied since filter
            until            — applied until filter
        """
        recs = self.load(since=since, until=until)
        if not recs:
            return {
                "n_sessions": 0,
                "pass_rate": None,
                "mean_tokens": None,
                "mean_cost_usd": None,
                "total_cost_usd": 0.0,
                "cost_of_pass": None,
                "mean_quality": None,
                "quality_7d": None,
                "mean_rework": None,
                "since": since,
                "until": until,
            }

        costed = [r for r in recs if r.cost_usd > 0]
        passed = [r for r in recs if r.passed]
        quality_recs = [r for r in recs if r.quality_score > 0]

        pass_rate = len(passed) / len(recs) if recs else None
        mean_cost = statistics.mean(r.cost_usd for r in costed) if costed else None
        total_cost = sum(r.cost_usd for r in recs)
        cop = self.cost_of_pass(recs) if costed else None
        mean_quality = (
            statistics.mean(r.quality_score for r in quality_recs) if quality_recs else None
        )
        q7d = self.quality_trend(recs, window_days=7)
        mean_tokens = self.token_trend(recs)
        mean_rework = statistics.mean(r.rework_turns for r in recs) if recs else None

        # Top-5 sessions by rework_turns (worst first) for bottleneck analysis
        top_rework = sorted(recs, key=lambda r: r.rework_turns, reverse=True)[:5]

        return {
            "n_sessions": len(recs),
            "pass_rate": round(pass_rate, 4) if pass_rate is not None else None,
            "mean_tokens": round(mean_tokens, 1) if mean_tokens is not None else None,
            "mean_cost_usd": round(mean_cost, 6) if mean_cost is not None else None,
            "total_cost_usd": round(total_cost, 6),
            "cost_of_pass": round(cop, 6) if cop is not None and cop < float("inf") else None,
            "mean_quality": round(mean_quality, 4) if mean_quality is not None else None,
            "quality_7d": round(q7d, 4) if q7d is not None else None,
            "mean_rework": round(mean_rework, 2) if mean_rework is not None else None,
            "top_rework_sessions": [
                {
                    "session_id": r.session_id,
                    "rework_turns": r.rework_turns,
                    "work_item_id": r.work_item_id,
                    "timestamp": r.timestamp,
                }
                for r in top_rework
            ],
            "since": since,
            "until": until,
        }
