from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from specsmith.wi_store import WorkItemStore


def recover_state(
    root: Path,
    work_item_id: str = "",
    *,
    git_diff: str = "",
    test_results_path: Path | None = None,
) -> dict[str, Any]:
    store = WorkItemStore(root)
    item = store.get(work_item_id) if work_item_id else None
    if item is None:
        items = store.load()
        item = items[0] if items else None

    test_results: dict[str, Any] = {}
    if test_results_path and test_results_path.is_file():
        try:
            loaded = json.loads(test_results_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            loaded = {"raw": test_results_path.read_text(encoding="utf-8")}
        if isinstance(loaded, dict):
            test_results = loaded

    failed = int(test_results.get("failed", 0) or 0) + int(test_results.get("errors", 0) or 0)
    diff_lines = len(git_diff.splitlines()) if git_diff else 0
    failed_step = "verification" if failed else "implementation" if diff_lines else "planning"
    impacted_requirements = list(getattr(item, "requirement_ids", []) or []) if item else []
    impacted_tests = list(getattr(item, "test_case_ids", []) or []) if item else []

    recommendation = (
        "Retry after fixing failing tests and re-running verification."
        if failed
        else "Rollback recent code changes and re-run preflight."
        if diff_lines
        else "Re-run plan and collect more evidence before implementation."
    )
    summary = {
        "work_item_id": item.id if item else "",
        "last_known_good_state": "implemented" if item and item.status == "implemented" else "open",
        "failed_step": failed_step,
        "impacted_requirements": impacted_requirements,
        "impacted_tests": impacted_tests,
        "recommended_action": recommendation,
        "test_failures": failed,
        "diff_lines": diff_lines,
    }
    _append_recovery_audit_entry(root, summary)
    return summary


def _append_recovery_audit_entry(root: Path, summary: dict[str, Any]) -> None:
    log_path = root / ".specsmith" / "recovery-log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": "recover",
        "summary": summary,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
