from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Literal, TypedDict

ACTION_TYPES = (
    "read_file",
    "write_file",
    "run_command",
    "create_plan",
    "update_plan",
    "test_run",
    "failure",
    "retry",
    "human_approval",
)

ActionType = Literal[
    "read_file",
    "write_file",
    "run_command",
    "create_plan",
    "update_plan",
    "test_run",
    "failure",
    "retry",
    "human_approval",
]


class NormalizedAgentAction(TypedDict, total=False):
    id: str
    timestamp: str
    action_type: ActionType
    target: str
    details: dict[str, Any]
    success: bool
    error: str
    retry_count: int
    requires_human_approval: bool
    work_item_id: str
    raw: dict[str, Any]


_ACTION_ALIASES: dict[str, ActionType] = {
    "read": "read_file",
    "readfile": "read_file",
    "read_file": "read_file",
    "write": "write_file",
    "writefile": "write_file",
    "write_file": "write_file",
    "run": "run_command",
    "command": "run_command",
    "run_command": "run_command",
    "plan_create": "create_plan",
    "create_plan": "create_plan",
    "plan_update": "update_plan",
    "update_plan": "update_plan",
    "test": "test_run",
    "test_run": "test_run",
    "failure": "failure",
    "error": "failure",
    "retry": "retry",
    "approval": "human_approval",
    "human_approval": "human_approval",
}


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _coerce_action_type(value: str) -> ActionType:
    key = value.strip().lower().replace("-", "_")
    return _ACTION_ALIASES.get(key, "run_command")


def normalize_action(raw: dict[str, Any], work_item_id: str) -> NormalizedAgentAction:
    action_name = str(raw.get("action") or raw.get("type") or raw.get("event") or "run_command")
    action_type = _coerce_action_type(action_name)
    target = str(raw.get("target") or raw.get("path") or raw.get("command") or "")
    action_id = str(raw.get("id") or f"ACT-{uuid.uuid4().hex[:10].upper()}")
    retry_count = int(raw.get("retry_count") or raw.get("retries") or 0)
    requires_human_approval = bool(
        raw.get("requires_human_approval")
        or raw.get("human_approval")
        or action_type == "human_approval"
    )
    success = raw.get("success")
    if success is None:
        success = action_type not in ("failure",)
    return {
        "id": action_id,
        "timestamp": str(raw.get("timestamp") or _now_iso()),
        "action_type": action_type,
        "target": target,
        "details": raw.get("details") if isinstance(raw.get("details"), dict) else {},
        "success": bool(success),
        "error": str(raw.get("error") or ""),
        "retry_count": retry_count,
        "requires_human_approval": requires_human_approval,
        "work_item_id": work_item_id,
        "raw": raw,
    }


def normalize_transcript_payload(payload: Any, work_item_id: str) -> list[NormalizedAgentAction]:
    if isinstance(payload, dict):
        records = payload.get("actions")
        items = records if isinstance(records, list) else [payload]
    elif isinstance(payload, list):
        items = payload
    else:
        items = []
    normalized: list[NormalizedAgentAction] = []
    for item in items:
        if isinstance(item, dict):
            normalized.append(normalize_action(item, work_item_id=work_item_id))
    return normalized


def import_transcript_json(
    project_dir: Path,
    transcript_path: Path,
    work_item_id: str,
) -> list[NormalizedAgentAction]:
    payload = json.loads(transcript_path.read_text(encoding="utf-8"))
    actions = normalize_transcript_payload(payload, work_item_id=work_item_id)
    out_dir = project_dir / ".specsmith"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "transcripts.jsonl"
    with out_path.open("a", encoding="utf-8") as handle:
        for action in actions:
            handle.write(json.dumps(action, ensure_ascii=False) + "\n")
    return actions
