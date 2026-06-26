# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""specsmith.esdb_writer — centralised best-effort ESDB write paths (REQ-395..402).

This module provides the write paths that were previously missing from ESDB:
  - Preflight decisions  (kind="preflight_decision")
  - Verify results       (kind="verify_result")
  - Work item records    (kind="work_item")

All three functions are **best-effort** — they are wrapped in try/except so
they never block their callers when ESDB is unavailable or the store fails.

Backend-agnostic: uses ``open_default_store()`` which dispatches to either
the free SQLite backend or the commercial ChronoStore backend depending on
what is installed and licensed.

Record confidence mapping:
  preflight_decision  → payload["confidence_target"]   (0.7–0.9 typical)
  verify_result       → 0.85 on equilibrium, 0.4 otherwise
  work_item           → wi.confidence_target; tombstone on terminal states

REQ-395: ESDBWriter utility module
REQ-396: Preflight decision ESDB write path
REQ-397: Verify result ESDB write path
REQ-398: Work item ESDB synchronisation
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass  # avoid circular imports at runtime


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _short_hash(text: str, length: int = 8) -> str:
    """Return first *length* hex chars of SHA-256 of *text*."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length].upper()


# ---------------------------------------------------------------------------
# Public write functions — all best-effort (wrapped in try/except by callers)
# ---------------------------------------------------------------------------


def write_preflight_record(
    project_root: str | Path,
    payload: dict[str, Any],
) -> bool:
    """Upsert a ``preflight_decision`` ESDB record from a preflight payload.

    Called by ``run_preflight()`` after the work item is minted.

    Record shape:
      id          = payload["work_item_id"]  (e.g. "WI-3A9F1C02")
      kind        = "preflight_decision"
      label       = utterance extracted from payload
      confidence  = payload["confidence_target"]
      source_ids  = payload["requirement_ids"]
      status      = "active"
      data        = {decision, intent, work_item_id, test_case_ids, ...}

    Returns True on success, False on any error (error is swallowed).
    """
    try:
        work_item_id = payload.get("work_item_id", "")
        if not work_item_id:
            return False  # only persist accepted preflights that minted a WI

        from specsmith.esdb import SqliteRecord, open_default_store

        root = Path(project_root)
        pf_id = f"PF-{work_item_id}"
        record = SqliteRecord(
            id=pf_id,
            kind="preflight_decision",
            status="active",
            label=str(payload.get("instruction", payload.get("intent", "")))[:200],
            confidence=float(payload.get("confidence_target", 0.7)),
            data={
                "decision": payload.get("decision", ""),
                "intent": payload.get("intent", ""),
                "work_item_id": work_item_id,
                "test_case_ids": payload.get("test_case_ids", []),
                "instruction": payload.get("instruction", ""),
                "ai_disclosure": payload.get("ai_disclosure", {}),
            },
            source_ids=list(payload.get("requirement_ids", [])),
        )
        with open_default_store(root, warn=False) as store:
            store.upsert(record)
        return True
    except Exception:  # noqa: BLE001 — best-effort; never blocks preflight
        return False


def write_verify_record(
    project_root: str | Path,
    result: dict[str, Any],
) -> bool:
    """Upsert a ``verify_result`` ESDB record from a verify payload.

    Called by ``run_verify()`` after the work item is marked implemented.

    Record shape:
      id          = "VERIFY-{work_item_id}"
      kind        = "verify_result"
      label       = brief summary string
      confidence  = 0.85 on equilibrium else 0.4
      source_ids  = [work_item_id] (links to preflight_decision record)
      status      = "active"
      data        = {equilibrium, retry_strategy, files_changed_count, ...}

    When equilibrium is reached the corresponding ``preflight_decision``
    record is tombstoned (status → "tombstone") to signal completion.

    Returns True on success, False on any error.
    """
    try:
        work_item_id = result.get("work_item_id", "")
        equilibrium = bool(result.get("equilibrium", False))
        confidence = 0.85 if equilibrium else 0.4

        from specsmith.esdb import SqliteRecord, open_default_store

        root = Path(project_root)
        verify_id = (
            f"VERIFY-{work_item_id}" if work_item_id else f"VERIFY-{_short_hash(str(result))}"
        )

        record = SqliteRecord(
            id=verify_id,
            kind="verify_result",
            status="active",
            label=str(result.get("summary", ""))[:200],
            confidence=confidence,
            data={
                "equilibrium": equilibrium,
                "confidence": result.get("confidence", confidence),
                "retry_strategy": result.get("retry_strategy", ""),
                "files_changed_count": len(result.get("files_changed", [])),
                "work_item_id": work_item_id,
            },
            source_ids=[work_item_id] if work_item_id else [],
        )
        with open_default_store(root, warn=False) as store:
            store.upsert(record)
            # When equilibrium reached, tombstone the preflight_decision record
            # so context seed knows this WI is complete.
            if equilibrium and work_item_id:
                pf_id = f"PF-{work_item_id}"
                existing = store.get(pf_id)
                if existing is not None and existing.kind == "preflight_decision":
                    store.delete(pf_id)
        return True
    except Exception:  # noqa: BLE001 — best-effort
        return False


def write_work_item_record(
    project_root: str | Path,
    wi: Any,  # WorkItem — avoid circular import; duck-typed
) -> bool:
    """Upsert a ``work_item`` ESDB record mirroring a WorkItem.

    Called by WorkItemStore after create/set_status/mark_implemented/promote.

    Record shape:
      id          = wi.id  (e.g. "WI-3A9F1C02")
      kind        = "work_item"
      label       = wi.intent[:200]
      confidence  = wi.confidence_target
      source_ids  = wi.requirement_ids + wi.test_case_ids
      status      = "active"  for open/implemented
                    "tombstone" for promoted/closed/archived/rejected
      data        = {status, kind, verified, promoted_to_req, blast_radius, ...}

    Returns True on success, False on any error.
    """
    try:
        from specsmith.esdb import SqliteRecord, open_default_store

        _TERMINAL = frozenset({"promoted", "closed", "archived", "rejected"})
        esdb_status = "tombstone" if wi.status in _TERMINAL else "active"

        source_ids = list(getattr(wi, "requirement_ids", []))
        source_ids += list(getattr(wi, "test_case_ids", []))

        record = SqliteRecord(
            id=wi.id,
            kind="work_item",
            status=esdb_status,
            label=str(wi.intent or wi.id)[:200],
            confidence=float(getattr(wi, "confidence_target", 0.7)),
            data={
                "status": wi.status,
                "kind": getattr(wi, "kind", "feature"),
                "verified": getattr(wi, "verified", False),
                "promoted_to_req": getattr(wi, "promoted_to_req", ""),
                "blast_radius_estimate": getattr(wi, "blast_radius_estimate", ""),
                "created_at": getattr(wi, "created_at", ""),
                "updated_at": getattr(wi, "updated_at", ""),
                "closed_reason": getattr(wi, "closed_reason", ""),
            },
            source_ids=source_ids,
        )
        root = Path(project_root)
        with open_default_store(root, warn=False) as store:
            store.upsert(record)
        return True
    except Exception:  # noqa: BLE001 — best-effort
        return False


__all__ = [
    "write_preflight_record",
    "write_verify_record",
    "write_work_item_record",
]
