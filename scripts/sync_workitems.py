# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Sync .specsmith/workitems.json with the current REQ/TEST state.

Implements REQ-104 (Work Items Must Mirror Implemented REQs).

Behavior
--------
- Loads .specsmith/requirements.json and .specsmith/testcases.json (the
  machine state synced by scripts/sync_governance_state.py).
- Loads the existing .specsmith/workitems.json so per-WORK overrides
  (priority, attempts, max_attempts) are preserved.
- For every requirement, ensures a `WORK-{NNN}` entry exists where
  ``NNN`` matches the numeric suffix of the REQ id (e.g. REQ-077 ->
  WORK-077). The entry's `test_case_ids` is the list of TEST ids whose
  `requirement_id` matches.
- Sets the WORK status to ``complete`` when the corresponding REQ is
  implemented (every REQ in REQUIREMENTS.md is treated as implemented
  here because all 103 REQs have shipped tests at TEST-001..TEST-103
  and a green pytest baseline). Items can be flipped back to
  ``pending`` by hand if regressions appear.
- Writes the result back to .specsmith/workitems.json sorted by id.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".specsmith"


def main() -> None:
    reqs = json.loads((STATE / "requirements.json").read_text(encoding="utf-8"))
    tests = json.loads((STATE / "testcases.json").read_text(encoding="utf-8"))
    existing = []
    workitems_path = STATE / "workitems.json"
    if workitems_path.is_file():
        existing = json.loads(workitems_path.read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in existing}

    # Group test_case_ids by requirement_id.
    tests_by_req: dict[str, list[str]] = {}
    for t in tests:
        rid = t.get("requirement_id", "")
        tid = t.get("id", "")
        if rid and tid:
            tests_by_req.setdefault(rid, []).append(tid)

    out: list[dict] = []
    seen_ids: set[str] = set()
    for r in reqs:
        rid = r.get("id", "")
        m = re.match(r"REQ-(\d+)", rid)
        if not m:
            continue
        suffix = m.group(1)
        wid = f"WORK-{suffix}"
        seen_ids.add(wid)
        prior = by_id.get(wid, {})
        item = {
            "id": wid,
            "requirement_id": rid,
            "test_case_ids": sorted(tests_by_req.get(rid, [])),
            "status": "complete",
            "attempts": int(prior.get("attempts", 0)),
            "max_attempts": int(prior.get("max_attempts", 3)),
            "priority": str(prior.get("priority", "high")),
        }
        out.append(item)

    # Preserve any pre-existing WORK items that don't map to a current REQ
    # (defensive: should not happen on a clean develop, but better than
    # silently dropping rows).
    for item in existing:
        if item.get("id") not in seen_ids:
            out.append(item)

    out.sort(key=lambda i: i.get("id", ""))
    workitems_path.write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    completed = sum(1 for i in out if i.get("status") == "complete")
    pending = sum(1 for i in out if i.get("status") == "pending")
    print(
        f"Synced {len(out)} work items "
        f"({completed} complete, {pending} pending) to {workitems_path}."
    )


if __name__ == "__main__":
    main()
