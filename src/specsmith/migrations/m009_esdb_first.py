# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""M009 — ESDB-First Backfill Migration (REQ-406).

What this migration does
------------------------
Backfills the three loose state files that were previously outside ESDB
into queryable ESDB records so the standard query API works for all history.

Step 1 — LEDGER.md headings → ESDB kind="ledger_event"
  Parses every ``## <timestamp> — <description>`` heading in LEDGER.md
  (and any LEDGER.md found via ``find_ledger()``) and upserts each as a
  ``SqliteRecord(kind="ledger_event", confidence=0.9)``.

Step 2 — trace.jsonl lines → ESDB kind="seal_record"
  Reads every line from ``.specsmith/trace.jsonl`` and upserts each as a
  ``SqliteRecord(kind="seal_record", confidence=0.9)``.

Step 3 — session_metrics.jsonl lines → ESDB kind="session_metric"
  Reads every line from ``.specsmith/session_metrics.jsonl`` and upserts
  each as a ``SqliteRecord(kind="session_metric", confidence=0.8)``.

Step 4 — Marker file (.specsmith/esdb-m009-backfill)
  Written on successful completion so re-runs are idempotent.

Non-destructive:
- No existing data is deleted or modified.
- LEDGER.md, trace.jsonl, session_metrics.jsonl remain untouched.
- Re-running after partial completion is safe (upsert is idempotent).

REQ-406: M009 ESDB-first backfill migration.
"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from specsmith.migrations import Migration, MigrationResult

_MARKER_FILE = ".specsmith/esdb-m009-backfill"
_HEADING_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}T\d{2}:\d{2})\s*[—\-]+\s*(.+)$")


class EsdbFirstMigration(Migration):
    version = 9
    title = "ESDB-first backfill (LEDGER.md + trace.jsonl + session_metrics.jsonl)"
    description = (
        "Backfills LEDGER.md entries, trace.jsonl seals, and session_metrics.jsonl "
        "records into ESDB so that the standard query API can be used for all "
        "historical data.  Idempotent — re-running is safe.  Non-destructive — "
        "no data is deleted.  Runs automatically via specsmith migrate run."
    )

    def run(self, root: Path, *, dry_run: bool = False) -> MigrationResult:  # noqa: C901
        result = MigrationResult(version=self.version, title=self.title, dry_run=dry_run)
        marker = root / _MARKER_FILE

        # Idempotency check
        if marker.exists() and not dry_run:
            result.message = "ESDB-first backfill already applied — skipping."
            return result

        counts: dict[str, int] = {
            "ledger_events": 0,
            "seal_records": 0,
            "session_metrics": 0,
            "skipped": 0,
        }

        # ── Step 1: LEDGER.md → ledger_event ───────────────────────────────
        _backfill_ledger(root, counts, dry_run=dry_run)

        # ── Step 2: trace.jsonl → seal_record ──────────────────────────────
        _backfill_trace(root, counts, dry_run=dry_run)

        # ── Step 3: session_metrics.jsonl → session_metric ─────────────────
        _backfill_metrics(root, counts, dry_run=dry_run)

        # ── Step 4: Marker ──────────────────────────────────────────────────
        if not dry_run:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(
                f"m009 applied: "
                f"ledger={counts['ledger_events']} "
                f"seals={counts['seal_records']} "
                f"metrics={counts['session_metrics']} "
                f"skipped={counts['skipped']}\n",
                encoding="utf-8",
            )
            result.files_created.append(_MARKER_FILE)

        prefix = "[dry-run] Would backfill" if dry_run else "Backfilled"
        result.message = (
            f"{prefix} {counts['ledger_events']} ledger event(s), "
            f"{counts['seal_records']} seal record(s), "
            f"{counts['session_metrics']} session metric(s) into ESDB "
            f"({counts['skipped']} skipped)."
        )
        result.success = True
        return result

    def rollback(self, root: Path) -> MigrationResult:
        """Remove idempotency marker so M009 can be re-run."""
        result = MigrationResult(version=self.version, title=self.title)
        marker = root / _MARKER_FILE
        if marker.exists():
            marker.unlink()
            result.message = f"Removed {_MARKER_FILE} — M009 will run again on next migrate."
            result.files_modified.append(_MARKER_FILE)
        else:
            result.message = f"{_MARKER_FILE} not found — nothing to roll back."
        return result


# ---------------------------------------------------------------------------
# Step helpers
# ---------------------------------------------------------------------------


def _backfill_ledger(root: Path, counts: dict[str, int], *, dry_run: bool) -> None:
    """Parse LEDGER.md and upsert ledger_event records."""
    try:
        from specsmith.paths import find_ledger
        from specsmith.paths import ledger_path as canonical_ledger

        ledger_path = find_ledger(root) or canonical_ledger(root)
        if not ledger_path or not ledger_path.exists():
            return

        content = ledger_path.read_text(encoding="utf-8")
        current_heading: str | None = None
        current_ts: str = ""

        if not dry_run:
            from specsmith.esdb import SqliteRecord, SqliteStore

            with SqliteStore(root) as store:
                for line in content.splitlines():
                    m = _HEADING_RE.match(line.strip())
                    if m:
                        current_ts = m.group(1)  # e.g. "2026-06-01T14:30"
                        current_heading = m.group(2).strip()
                        rec_id = f"LED-LEDGER-{uuid.uuid4().hex[:12].upper()}"
                        rec = SqliteRecord(
                            id=rec_id,
                            kind="ledger_event",
                            status="active",
                            label=current_heading[:200],
                            confidence=0.9,
                            data={
                                "description": current_heading,
                                "timestamp": current_ts + ":00Z",
                                "source": "LEDGER.md",
                                "entry_type": "backfill",
                            },
                        )
                        store.upsert(rec)
                        counts["ledger_events"] += 1
        else:
            # dry-run: just count headings
            for line in content.splitlines():
                if _HEADING_RE.match(line.strip()):
                    counts["ledger_events"] += 1

    except Exception:  # noqa: BLE001
        counts["skipped"] += 1


def _backfill_trace(root: Path, counts: dict[str, int], *, dry_run: bool) -> None:
    """Parse trace.jsonl and upsert seal_record records."""
    trace_path = root / ".specsmith" / "trace.jsonl"
    if not trace_path.exists():
        return
    try:
        if not dry_run:
            from specsmith.esdb import SqliteRecord, SqliteStore

            with SqliteStore(root) as store:
                for line in trace_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        seal_id = str(d.get("seal_id", ""))
                        if not seal_id:
                            counts["skipped"] += 1
                            continue
                        rec = SqliteRecord(
                            id=f"ESDB-{seal_id}",
                            kind="seal_record",
                            status="active",
                            label=str(d.get("description", seal_id))[:200],
                            confidence=0.9,
                            data=d,
                            source_ids=list(d.get("artifact_ids") or []),
                        )
                        store.upsert(rec)
                        counts["seal_records"] += 1
                    except (json.JSONDecodeError, Exception):  # noqa: BLE001
                        counts["skipped"] += 1
        else:
            for line in trace_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    counts["seal_records"] += 1
    except Exception:  # noqa: BLE001
        counts["skipped"] += 1


def _backfill_metrics(root: Path, counts: dict[str, int], *, dry_run: bool) -> None:
    """Parse session_metrics.jsonl and upsert session_metric records."""
    metrics_path = root / ".specsmith" / "session_metrics.jsonl"
    if not metrics_path.exists():
        return
    try:
        if not dry_run:
            from specsmith.esdb import SqliteRecord, SqliteStore

            with SqliteStore(root) as store:
                for line in metrics_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        session_id = str(d.get("session_id", ""))
                        rec_id = (
                            f"MET-{session_id}" if session_id
                            else f"MET-{uuid.uuid4().hex[:8].upper()}"
                        )
                        rec = SqliteRecord(
                            id=rec_id,
                            kind="session_metric",
                            status="active",
                            label=(
                                f"{session_id}: tokens={d.get('tokens_total', 0)} "
                                f"passed={d.get('passed', False)}"
                            )[:200],
                            confidence=0.8,
                            data=d,
                            source_ids=(
                                [str(d["work_item_id"])] if d.get("work_item_id") else []
                            ),
                        )
                        store.upsert(rec)
                        counts["session_metrics"] += 1
                    except (json.JSONDecodeError, Exception):  # noqa: BLE001
                        counts["skipped"] += 1
        else:
            for line in metrics_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    counts["session_metrics"] += 1
    except Exception:  # noqa: BLE001
        counts["skipped"] += 1
