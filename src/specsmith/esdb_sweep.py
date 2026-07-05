# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""specsmith.esdb_sweep — Per-kind tombstone sweep + orphan detection (REQ-412).

The sweep runs in two modes:

``orphans_only=False`` (default / scheduled)
    Tombstones records whose *retention period* has expired, then removes orphans.
    Calls ``compute_and_upsert_efficiency()`` after sweep to refresh EFF-CURRENT.

``orphans_only=True`` (fast path, called from ``specsmith save``)
    Only flags orphaned work_item / preflight_decision records.
    Skips retention-based tombstoning to keep the save path fast.

Retention periods (``_RETENTION_DAYS``)
    - ``session_metric``     60 days
    - ``context_usage``      30 days
    - ``ledger_event``       90 days
    - ``seal_record``        None  (keep forever)
    - ``token_metric``       None  (keep forever)
    - ``efficiency_metric``  None  (keep forever — only one EFF-CURRENT)
    - All others             None  (keep forever by default)

Orphan detection
    A ``work_item`` record is an orphan if it is in ``status='active'`` in ESDB
    but absent from ``workitems.json`` (removed outside of specsmith).
    A ``preflight_decision`` record is an orphan if its parent WI id is not found
    in either ESDB or ``workitems.json``.

REQ-412: esdb_sweep with per-kind retention
REQ-413: orphan detection for work_item / preflight_decision
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Retention registry (days; None = keep forever)
# ---------------------------------------------------------------------------

_RETENTION_DAYS: dict[str, int | None] = {
    "session_metric": 60,
    "context_usage": 30,
    "ledger_event": 90,
    "seal_record": None,
    "token_metric": None,
    "efficiency_metric": None,
    "token_usage": None,  # alias guard
}


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class SweepResult:
    """Summary of an ESDB sweep run."""

    tombstoned: int = 0
    """Number of records tombstoned due to expired retention."""

    orphans_flagged: int = 0
    """Number of orphan records tombstoned."""

    efficiency_refreshed: bool = False
    """Whether EFF-CURRENT was refreshed after the sweep."""

    errors: list[str] = field(default_factory=list)
    """Non-fatal error messages encountered during sweep."""

    kinds_swept: dict[str, int] = field(default_factory=dict)
    """Per-kind tombstone counts for records with expired retention."""

    def total_swept(self) -> int:
        return self.tombstoned + self.orphans_flagged

    def __str__(self) -> str:
        parts = [
            f"tombstoned={self.tombstoned}",
            f"orphans={self.orphans_flagged}",
        ]
        if self.efficiency_refreshed:
            parts.append("EFF-CURRENT refreshed")
        if self.errors:
            parts.append(f"errors={len(self.errors)}")
        return f"SweepResult({', '.join(parts)})"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_sweep(
    root: str | Path,
    *,
    orphans_only: bool = False,
    dry_run: bool = False,
) -> SweepResult:
    """Run an ESDB sweep and return a :class:`SweepResult`.

    Args:
        root:         Project root (parent of ``.specsmith/``).
        orphans_only: If True, only perform orphan detection (skip retention sweep).
                      Intended for the fast ``specsmith save`` path.
        dry_run:      If True, compute what would be swept but do not actually
                      tombstone any records.

    Returns:
        :class:`SweepResult` with counts and any non-fatal errors.

    """
    result = SweepResult()
    root_path = Path(root)
    sqlite_path = root_path / ".specsmith" / "esdb.sqlite3"

    if not sqlite_path.exists():
        return result  # No ESDB yet — nothing to sweep

    try:
        from specsmith.esdb import SqliteStore
    except ImportError as exc:
        result.errors.append(f"esdb import failed: {exc}")
        return result

    # ------------------------------------------------------------------
    # Phase 1: Retention-based tombstoning (skipped in orphans_only mode)
    # ------------------------------------------------------------------
    if not orphans_only:
        try:
            with SqliteStore(root_path) as store:
                for kind, max_days in _RETENTION_DAYS.items():
                    if max_days is None:
                        continue
                    cutoff = datetime.now(timezone.utc) - timedelta(days=max_days)
                    cutoff_iso = cutoff.isoformat()

                    records = store.query(kind=kind, status="active")
                    swept_kind = 0
                    for r in records:
                        ts_str = str(
                            r.data.get("timestamp")
                            or r.data.get("computed_at")
                            or r.data.get("created_at")
                            or "",
                        )
                        if ts_str and ts_str < cutoff_iso:
                            if not dry_run:
                                store.delete(r.id)
                            swept_kind += 1

                    if swept_kind:
                        result.kinds_swept[kind] = swept_kind
                        result.tombstoned += swept_kind

        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"retention sweep failed: {exc}")

    # ------------------------------------------------------------------
    # Phase 2: Orphan detection
    # ------------------------------------------------------------------
    try:
        wi_from_json = _load_wi_ids_from_json(root_path)

        with SqliteStore(root_path) as store:
            esdb_wi_ids = {r.id for r in store.query(kind="work_item", status="active")}
            preflight_records = store.query(kind="preflight_decision", status="active")

            # Orphan work_items: in ESDB but absent from workitems.json
            orphan_wis = esdb_wi_ids - wi_from_json
            for wi_id in orphan_wis:
                if not dry_run:
                    store.delete(wi_id)
                result.orphans_flagged += 1

            # Orphan preflights: parent WI not in ESDB or JSON
            all_known_wis = esdb_wi_ids | wi_from_json
            for pf in preflight_records:
                parent_wi = pf.data.get("work_item_id") or pf.data.get("wi_id") or ""
                if parent_wi and parent_wi not in all_known_wis:
                    if not dry_run:
                        store.delete(pf.id)
                    result.orphans_flagged += 1

    except Exception as exc:  # noqa: BLE001
        result.errors.append(f"orphan detection failed: {exc}")

    # ------------------------------------------------------------------
    # Phase 3: Refresh EFF-CURRENT (only in full sweep, not orphans-only)
    # ------------------------------------------------------------------
    if not orphans_only and not dry_run:
        try:
            from specsmith.efficiency import compute_and_upsert_efficiency

            result.efficiency_refreshed = compute_and_upsert_efficiency(root_path)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"efficiency refresh failed: {exc}")

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_wi_ids_from_json(root_path: Path) -> set[str]:
    """Return WI IDs from ``.specsmith/workitems.json``."""
    wi_path = root_path / ".specsmith" / "workitems.json"
    if not wi_path.exists():
        return set()
    try:
        data: list[dict[str, Any]] = json.loads(wi_path.read_text(encoding="utf-8"))
        return {str(wi.get("id", "")) for wi in data if isinstance(wi, dict) and wi.get("id")}
    except (OSError, ValueError):
        return set()


__all__ = ["SweepResult", "run_sweep"]
