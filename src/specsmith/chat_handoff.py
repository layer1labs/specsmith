# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Evidence-preserving chat compaction and portable agent handoffs (REQ-446)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = 1
_MAX_EXCERPT = 280


def build_handoff(
    history: list[dict[str, Any]],
    *,
    work_item_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Build an extractive, provenance-preserving envelope from chat turns.

    This deliberately does not ask an LLM to invent a prose summary.  Each
    compacted claim remains a bounded excerpt linked to a deterministic turn ID,
    allowing another agent to inspect the original history before relying on it.
    """
    turns: list[dict[str, str]] = []
    for index, turn in enumerate(history):
        role = turn.get("role")
        content = turn.get("content")
        if not isinstance(role, str) or not isinstance(content, str) or not content.strip():
            continue
        canonical = json.dumps(
            {"role": role, "content": content}, sort_keys=True, ensure_ascii=False
        )
        source_id = f"turn:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:16]}"
        turns.append(
            {
                "source_id": source_id,
                "role": role,
                "excerpt": content.strip()[:_MAX_EXCERPT],
                "position": str(index),
            },
        )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "kind": "epistemic_chat_handoff",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "confidence": 1.0,
        "uncertainty": "Extractive envelope; excerpts are not inferred claims.",
        "work_item_ids": sorted(set(work_item_ids or [])),
        "turns": turns,
    }
    fingerprint = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:16].upper()
    payload["id"] = f"HANDOFF-{digest}"
    validate_handoff(payload)
    return payload


def validate_handoff(payload: dict[str, Any]) -> None:
    """Reject malformed or unsupported handoff claims before persistence/import."""
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("kind") != "epistemic_chat_handoff"
    ):
        raise ValueError("unsupported handoff schema")
    if not isinstance(payload.get("id"), str) or not payload["id"].startswith("HANDOFF-"):
        raise ValueError("handoff must have a stable ID")
    if payload.get("confidence") != 1.0:
        raise ValueError("extractive handoffs must retain confidence 1.0")
    for turn in payload.get("turns", []):
        if not isinstance(turn, dict) or not isinstance(turn.get("source_id"), str):
            raise ValueError("handoff turn is missing provenance")
        if not isinstance(turn.get("excerpt"), str) or len(turn["excerpt"]) > _MAX_EXCERPT:
            raise ValueError("handoff excerpt is invalid")


def render_handoff_context(payload: dict[str, Any]) -> str:
    """Render a bounded context entry that tells agents how to verify it."""
    validate_handoff(payload)
    excerpts = "\n".join(
        f"- [{turn['source_id']}] {turn['role']}: {turn['excerpt']}" for turn in payload["turns"]
    )
    return (
        f"[Epistemic handoff {payload['id']} | {len(payload['turns'])} extractive turns | "
        "verify source IDs before treating excerpts as decisions]\n"
        f"{excerpts}"
    )


def store_handoff(root: Any, payload: dict[str, Any]) -> None:
    """Persist a validated handoff in the active ESDB backend."""
    validate_handoff(payload)
    from specsmith.esdb import SqliteRecord, open_default_store

    with open_default_store(root) as store:
        store.upsert(
            SqliteRecord(
                id=payload["id"],
                kind="chat_handoff",
                label="Epistemic chat handoff",
                confidence=1.0,
                data=payload,
            ),
        )
