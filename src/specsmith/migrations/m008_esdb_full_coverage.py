# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""M008 — ESDB Full-Coverage Backfill Migration (REQ-401).

What this migration does
------------------------
Backfills existing flat-JSON project state into ESDB records so that
``build_context_seed()`` can find them during session resume.

Step 1 — Work items (.specsmith/workitems.json → ESDB kind="work_item")
  Every existing WorkItem is upserted as an ESDB record via
  ``write_work_item_record()``.  Status mapping:
    open / implemented → ESDB status="active"
    promoted / closed / archived / rejected → ESDB status="tombstone"

Step 2 — Ledger audit events (SQLite audit_events table → ESDB kind="ledger_event")
  Every row in the SQLite ``audit_events`` table is upserted as a
  ``SqliteRecord(kind="ledger_event")``.  This makes ledger history queryable
  via the standard ESDB API rather than requiring direct SQLite access.

Step 3 — Marker file (.specsmith/esdb-full-coverage)
  Written on successful completion so re-runs are idempotent.

Non-destructive:
- No existing data is deleted or modified.
- workitems.json and esdb.sqlite3 are unchanged.
- Re-running after partial completion is safe (upsert is idempotent).

REQ-401: M008 ESDB full-coverage backfill migration.
"""

from __future__ import annotations

import json
from pathlib import Path

from specsmith.migrations import Migration, MigrationResult

_MARKER_FILE = ".specsmith/esdb-full-coverage"


class EsdbFullCoverageMigration(Migration):
    version = 8
    title = "ESDB full-coverage backfill (work items + ledger events)"
    description = (
        "Backfills existing workitems.json and SQLite ledger audit_events into "
        "the ESDB store so build_context_seed() can include them in session "
        "resume context.  Idempotent — re-running is safe.  Non-destructive — "
        "no data is deleted.  Runs automatically via specsmith migrate run."
    )

    def run(self, root: Path, *, dry_run: bool = False) -> MigrationResult:  # noqa: C901
        result = MigrationResult(version=self.version, title=self.title, dry_run=dry_run)
        marker = root / _MARKER_FILE

        # Idempotency check
        if marker.exists() and not dry_run:
            result.message = "ESDB full-coverage backfill already applied — skipping."
            return result

        counts: dict[str, int] = {"work_items": 0, "ledger_events": 0, "skipped": 0}

        # ── Step 1: Work items ──────────────────────────────────────────────
        wi_path = root / ".specsmith" / "workitems.json"
        if wi_path.exists():
            try:
                raw = json.loads(wi_path.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    if not dry_run:
                        from specsmith.esdb_writer import write_work_item_record

                        for wi_dict in raw:
                            if not isinstance(wi_dict, dict) or not wi_dict.get("id"):
                                counts["skipped"] += 1
                                continue
                            try:
                                # Duck-type a minimal WI object for write_work_item_record
                                wi = _DictProxy(wi_dict)
                                if write_work_item_record(root, wi):
                                    counts["work_items"] += 1
                                else:
                                    counts["skipped"] += 1
                            except Exception:  # noqa: BLE001
                                counts["skipped"] += 1
                    else:
                        counts["work_items"] = sum(
                            1 for d in raw if isinstance(d, dict) and d.get("id")
                        )
            except (OSError, ValueError):
                counts["skipped"] += 1

        # ── Step 2: Ledger audit events (SQLite → ESDB) ─────────────────────
        sqlite_path = root / ".specsmith" / "esdb.sqlite3"
        if sqlite_path.exists():
            try:
                import sqlite3

                from specsmith.esdb import SqliteRecord, SqliteStore

                conn = sqlite3.connect(str(sqlite_path))
                conn.row_factory = sqlite3.Row
                try:
                    rows = conn.execute("SELECT * FROM audit_events ORDER BY rowid").fetchall()
                except sqlite3.OperationalError:
                    rows = []
                finally:
                    conn.close()

                if rows and not dry_run:
                    with SqliteStore(root) as store:
                        for row in rows:
                            event_id = str(row["event_id"])
                            existing = store.get(f"LEDGER-{event_id}")
                            if existing is not None:
                                counts["ledger_events"] += 1
                                continue  # already imported
                            try:
                                # payload_hash is a hash, not the payload itself;
                                # use actor + command_source for the label
                                try:
                                    payload_text = (
                                        f"{row['command_source']}: {row['work_item_id']}"
                                        if row["work_item_id"]
                                        else str(row["command_source"])
                                    )
                                except Exception:  # noqa: BLE001
                                    payload_text = event_id

                                rec = SqliteRecord(
                                    id=f"LEDGER-{event_id}",
                                    kind="ledger_event",
                                    status="active",
                                    label=payload_text[:200],
                                    confidence=0.9,  # ledger events are high-confidence facts
                                    data={
                                        "event_id": event_id,
                                        "timestamp": str(row["timestamp"]),
                                        "actor": str(row["actor"]),
                                        "command_source": str(row["command_source"]),
                                        "work_item_id": str(row["work_item_id"]),
                                    },
                                    source_ids=[str(row["work_item_id"])]
                                    if row["work_item_id"]
                                    else [],
                                )
                                store.upsert(rec)
                                counts["ledger_events"] += 1
                            except Exception:  # noqa: BLE001
                                counts["skipped"] += 1
                elif rows:
                    counts["ledger_events"] = len(rows)

            except Exception:  # noqa: BLE001
                counts["skipped"] += 1

        # ── Step 3: Write marker ─────────────────────────────────────────────
        if not dry_run:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(
                f"m008 applied: work_items={counts['work_items']} "
                f"ledger_events={counts['ledger_events']} "
                f"skipped={counts['skipped']}\n",
                encoding="utf-8",
            )
            result.files_created.append(_MARKER_FILE)

        wi_n = counts["work_items"]
        le_n = counts["ledger_events"]
        sk_n = counts["skipped"]
        prefix = "[dry-run] Would backfill" if dry_run else "Backfilled"
        result.message = (
            f"{prefix} {wi_n} work item(s) and {le_n} ledger event(s) into ESDB ({sk_n} skipped)."
        )
        result.success = True
        return result

    def rollback(self, root: Path) -> MigrationResult:
        """Remove the idempotency marker so M008 can be re-run."""
        result = MigrationResult(version=self.version, title=self.title)
        marker = root / _MARKER_FILE
        if marker.exists():
            marker.unlink()
            result.message = f"Removed {_MARKER_FILE} — M008 will run again on next migrate."
            result.files_modified.append(_MARKER_FILE)
        else:
            result.message = f"{_MARKER_FILE} not found — nothing to roll back."
        return result


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


class _DictProxy:
    """Minimal duck-type wrapper so write_work_item_record() accepts a plain dict."""

    __slots__ = ("_d",)

    def __init__(self, d: dict) -> None:  # type: ignore[type-arg]
        object.__setattr__(self, "_d", d)

    def __getattr__(self, name: str) -> object:
        d: dict = object.__getattribute__(self, "_d")  # type: ignore[type-arg]
        if name in d:
            return d[name]
        # Provide sensible defaults for optional fields
        defaults: dict[str, object] = {  # type: ignore[type-arg]
            "status": "open",
            "kind": "feature",
            "intent": "",
            "requirement_ids": [],
            "test_case_ids": [],
            "confidence_target": 0.7,
            "verified": False,
            "promoted_to_req": "",
            "blast_radius_estimate": "",
            "created_at": "",
            "updated_at": "",
            "closed_reason": "",
        }
        if name in defaults:
            return defaults[name]
        raise AttributeError(name)
