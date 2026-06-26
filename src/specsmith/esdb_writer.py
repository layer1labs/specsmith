# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""specsmith.esdb_writer — centralised best-effort ESDB write paths (REQ-395..402, REQ-410).

This module provides the write paths that were previously missing from ESDB:
  - Preflight decisions  (kind="preflight_decision")
  - Verify results       (kind="verify_result")
  - Work item records    (kind="work_item")
  - Token metrics        (kind="token_metric")  ← REQ-410

All functions are **best-effort** — they are wrapped in try/except so
they never block their callers when ESDB is unavailable or the store fails.

Backend-agnostic: uses ``open_default_store()`` which dispatches to either
the free SQLite backend or the commercial ChronoStore backend depending on
what is installed and licensed.

Record confidence mapping:
  preflight_decision  → payload["confidence_target"]   (0.7–0.9 typical)
  verify_result       → 0.85 on equilibrium, 0.4 otherwise
  work_item           → wi.confidence_target; tombstone on terminal states
  token_metric        → 1.0 (objective measurement; never evicted)

REQ-395: ESDBWriter utility module
REQ-396: Preflight decision ESDB write path
REQ-397: Verify result ESDB write path
REQ-398: Work item ESDB synchronisation
REQ-410: Token metric ESDB write path
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
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


def write_token_metric(
    project_root: str | Path,
    *,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float = 0.0,
    model: str = "",
    command_source: str = "agent",
    work_item_id: str = "",
) -> bool:
    """Upsert a ``token_metric`` ESDB record for one LLM turn (REQ-410).

    Called by AgentRunner after every ChatRunResult.  Confidence=1.0 because
    token counts are objective measurements — never evicted by the sweep.

    Record shape:
      id            = "TOK-{uuid8}"
      kind          = "token_metric"
      label         = "{command_source}: {input_tokens}in {output_tokens}out"
      confidence    = 1.0
      data          = {input_tokens, output_tokens, total_tokens, cost_usd,
                       model, command_source, work_item_id, timestamp}

    Returns True on success, False on any error.
    """
    try:
        from specsmith.esdb import SqliteRecord, open_default_store

        root = Path(project_root)
        tok_id = f"TOK-{uuid.uuid4().hex[:8].upper()}"
        total = input_tokens + output_tokens
        record = SqliteRecord(
            id=tok_id,
            kind="token_metric",
            status="active",
            label=f"{command_source}: {input_tokens}in {output_tokens}out",
            confidence=1.0,
            data={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total,
                "cost_usd": cost_usd,
                "model": model,
                "command_source": command_source,
                "work_item_id": work_item_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            source_ids=[work_item_id] if work_item_id else [],
        )
        with open_default_store(root, warn=False) as store:
            store.upsert(record)
        return True
    except Exception:  # noqa: BLE001 — best-effort; never blocks caller
        return False


def write_ledger_event(
    project_root: str | Path,
    *,
    description: str,
    entry_type: str = "task",
    author: str = "agent",
    reqs: str = "",
    status: str = "complete",
    epistemic_status: str = "unknown",
    belief_artifacts: str = "",
    entry_hash: str = "",
) -> bool:
    """Upsert a ``ledger_event`` ESDB record from a ledger entry (REQ-403).

    Called best-effort by ``ledger.add_entry()`` after writing LEDGER.md.
    Confidence=0.9; retention=90 days (managed by esdb_sweep).

    Returns True on success, False on any error.
    """
    try:
        from specsmith.esdb import SqliteRecord, open_default_store

        root = Path(project_root)
        rec_id = f"LED-{uuid.uuid4().hex[:12].upper()}"
        record = SqliteRecord(
            id=rec_id,
            kind="ledger_event",
            status="active",
            label=description[:200],
            confidence=0.9,
            data={
                "description": description,
                "entry_type": entry_type,
                "author": author,
                "reqs": reqs,
                "status": status,
                "epistemic_status": epistemic_status,
                "belief_artifacts": belief_artifacts,
                "entry_hash": entry_hash,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            source_ids=[r.strip() for r in reqs.split(",") if r.strip()] if reqs else [],
        )
        with open_default_store(root, warn=False) as store:
            store.upsert(record)
        return True
    except Exception:  # noqa: BLE001 — best-effort; never blocks add_entry
        return False


def write_seal_record(
    project_root: str | Path,
    record_dict: dict[str, Any],
) -> bool:
    """Upsert a ``seal_record`` ESDB record from a TraceVault SealRecord (REQ-404).

    Called best-effort by ``TraceVault._append()`` after writing trace.jsonl.
    Confidence=0.9; seal_record records are kept forever (no retention sweep).

    Args:
        project_root: Project root directory.
        record_dict:  ``SealRecord.to_dict()`` output.

    Returns True on success, False on any error.
    """
    try:
        from specsmith.esdb import SqliteRecord, open_default_store

        root = Path(project_root)
        seal_id = str(record_dict.get("seal_id", ""))
        if not seal_id:
            return False
        description = str(record_dict.get("description", ""))
        record = SqliteRecord(
            id=f"ESDB-{seal_id}",
            kind="seal_record",
            status="active",
            label=description[:200],
            confidence=0.9,
            data=dict(record_dict),
            source_ids=list(record_dict.get("artifact_ids") or []),
        )
        with open_default_store(root, warn=False) as store:
            store.upsert(record)
        return True
    except Exception:  # noqa: BLE001 — best-effort; never blocks seal()
        return False


def write_session_metric(
    project_root: str | Path,
    record_dict: dict[str, Any],
) -> bool:
    """Upsert a ``session_metric`` ESDB record from a MetricsRecord (REQ-405).

    Called best-effort by ``MetricsStore.append()`` after writing session_metrics.jsonl.
    Confidence=0.8; retention=60 days (managed by esdb_sweep).

    Args:
        project_root: Project root directory.
        record_dict:  ``MetricsRecord.to_dict()`` output.

    Returns True on success, False on any error.
    """
    try:
        from specsmith.esdb import SqliteRecord, open_default_store

        root = Path(project_root)
        session_id = str(record_dict.get("session_id", ""))
        rec_id = f"MET-{session_id}" if session_id else f"MET-{uuid.uuid4().hex[:8].upper()}"
        record = SqliteRecord(
            id=rec_id,
            kind="session_metric",
            status="active",
            label=(
                f"{session_id}: tokens={record_dict.get('tokens_total', 0)} "
                f"passed={record_dict.get('passed', False)}"
            )[:200],
            confidence=0.8,
            data=dict(record_dict),
            source_ids=(
                [str(record_dict["work_item_id"])]
                if record_dict.get("work_item_id")
                else []
            ),
        )
        with open_default_store(root, warn=False) as store:
            store.upsert(record)
        return True
    except Exception:  # noqa: BLE001 — best-effort; never blocks append()
        return False


__all__ = [
    "write_preflight_record",
    "write_verify_record",
    "write_work_item_record",
    "write_token_metric",
    "write_ledger_event",
    "write_seal_record",
    "write_session_metric",
]
