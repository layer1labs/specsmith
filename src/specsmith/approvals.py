from __future__ import annotations

import json
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

APPROVAL_TYPES = ("requirement", "plan", "implementation", "verification", "release")


@dataclass
class ApprovalRecord:
    approval_type: str
    work_item_id: str
    approver: str
    timestamp: str
    scope: str
    rationale: str
    requirement_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _approvals_path(root: Path) -> Path:
    return root / ".specsmith" / "approvals.json"


def load_approvals(root: Path) -> list[ApprovalRecord]:
    path = _approvals_path(root)
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(raw, list):
        return []
    out: list[ApprovalRecord] = []
    for row in raw:
        if isinstance(row, dict):
            out.append(
                ApprovalRecord(
                    approval_type=str(row.get("approval_type", "")),
                    work_item_id=str(row.get("work_item_id", "")),
                    approver=str(row.get("approver", "")),
                    timestamp=str(row.get("timestamp", "")),
                    scope=str(row.get("scope", "")),
                    rationale=str(row.get("rationale", "")),
                    requirement_ids=list(row.get("requirement_ids", []) or []),
                )
            )
    return out


def save_approvals(root: Path, approvals: list[ApprovalRecord]) -> None:
    path = _approvals_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([a.to_dict() for a in approvals], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def detect_approver(root: Path) -> str:
    def _git_config(key: str) -> str:
        try:
            proc = subprocess.run(
                ["git", "-C", str(root), "config", "--get", key],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception:  # noqa: BLE001
            return ""
        return (proc.stdout or "").strip()

    name = _git_config("user.name")
    email = _git_config("user.email")
    if name and email:
        return f"{name} <{email}>"
    if name:
        return name
    if email:
        return email
    return "unknown-approver"


def record_approval(
    root: Path,
    approval_type: str,
    work_item_id: str,
    rationale: str,
    *,
    scope: str = "",
    requirement_ids: list[str] | None = None,
) -> ApprovalRecord:
    if approval_type not in APPROVAL_TYPES:
        msg = f"approval_type must be one of {APPROVAL_TYPES}"
        raise ValueError(msg)
    approvals = load_approvals(root)
    record = ApprovalRecord(
        approval_type=approval_type,
        work_item_id=work_item_id,
        approver=detect_approver(root),
        timestamp=_now_iso(),
        scope=scope or work_item_id,
        rationale=rationale.strip(),
        requirement_ids=list(requirement_ids or []),
    )
    approvals.append(record)
    save_approvals(root, approvals)
    return record


def approvals_by_work_item(root: Path, work_item_id: str) -> list[ApprovalRecord]:
    return [a for a in load_approvals(root) if a.work_item_id == work_item_id]
