#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Migrate specsmith governance from Markdown-primary to YAML-primary.

Steps performed:
  1. Remove duplicate REQ-221..243 from docs/REQUIREMENTS.md
     (they are confirmed duplicates of REQ-130..135 + REQ-161..179)
  2. Re-sync .specsmith/requirements.json from cleaned MD
  3. Migrate all REQs and TESTs from JSON → grouped YAML files under
     docs/requirements/*.yml and docs/tests/*.yml
  4. Write .specsmith/governance-mode  (yaml)  to signal YAML-first sync

Run once; idempotent (re-running is safe).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml  # PyYAML — already in specsmith's deps

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REQS_MD = DOCS / "REQUIREMENTS.md"
TESTS_MD = DOCS / "TESTS.md"
REQS_JSON = ROOT / ".specsmith" / "requirements.json"
TESTS_JSON = ROOT / ".specsmith" / "testcases.json"
REQS_YAML_DIR = DOCS / "requirements"
TESTS_YAML_DIR = DOCS / "tests"
GOV_MODE_FILE = ROOT / ".specsmith" / "governance-mode"

# Duplicate IDs to remove (confirmed duplicates of lower-numbered originals)
DUPLICATE_REQS = set(f"REQ-{i}" for i in range(221, 244))

# Section groupings: (filename_stem, list of REQ id ranges as (lo, hi) tuples)
REQ_GROUPS: list[tuple[str, list[tuple[int, int]]]] = [
    ("governance", [(1, 64)]),
    ("agent", [(65, 129)]),
    ("harness", [(130, 160)]),
    ("intelligence", [(161, 220)]),
    ("context", [(244, 247)]),
    ("esdb", [(248, 262)]),
    ("ai_intelligence", [(263, 299)]),
]
# All remaining REQs fall into "overflow"
OVERFLOW_GROUP = "overflow"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _req_num(req_id: str) -> int:
    m = re.match(r"REQ-(\d+)$", req_id)
    return int(m.group(1)) if m else 9999


def _test_num(test_id: str) -> int:
    m = re.match(r"TEST-(\d+)$", test_id)
    return int(m.group(1)) if m else 9999


def _group_for_req(req_id: str) -> str:
    n = _req_num(req_id)
    for stem, ranges in REQ_GROUPS:
        for lo, hi in ranges:
            if lo <= n <= hi:
                return stem
    return OVERFLOW_GROUP


# ---------------------------------------------------------------------------
# Step 1: Remove duplicate REQs from REQUIREMENTS.md
# ---------------------------------------------------------------------------


def remove_duplicate_reqs(path: Path) -> int:
    """Remove sections for duplicate REQ IDs; return count removed."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    # We'll collect line ranges to drop.
    # A REQ section starts at "## REQ-NNN" and ends just before the next "## " heading.
    # We also handle the style-B "## N. Title" heading that resolves via - **ID:** REQ-NNN.

    # Build a list of (start_line, end_line) for sections belonging to DUPLICATE_REQS.
    # We'll do a two-pass approach.

    # Find all heading line indices and their associated REQ IDs (if any)
    heading_indices: list[tuple[int, str | None]] = []  # (line_idx, req_id_or_None)

    direct_heading_re = re.compile(r"^#{1,3}\s+(REQ-\d+)\b")
    numbered_heading_re = re.compile(r"^#{1,3}\s+\d+\.")
    id_field_re = re.compile(r"^-\s+\*\*ID:\*\*\s+(REQ-\d+)")

    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n")
        m_direct = direct_heading_re.match(line)
        if m_direct:
            heading_indices.append((i, m_direct.group(1)))
            i += 1
            continue
        m_num = numbered_heading_re.match(line)
        if m_num and re.match(r"^#{1,3} ", line):
            # Look ahead for - **ID:** REQ-NNN within next 10 lines
            req_id = None
            for j in range(i + 1, min(i + 10, len(lines))):
                m_id = id_field_re.match(lines[j].rstrip("\n"))
                if m_id:
                    req_id = m_id.group(1)
                    break
                # Stop if we hit another heading
                if re.match(r"^#{1,3}\s+", lines[j]) and j != i:
                    break
            heading_indices.append((i, req_id))
            i += 1
            continue
        i += 1

    # Now determine ranges to drop
    to_drop: set[int] = set()
    for idx, (line_idx, req_id) in enumerate(heading_indices):
        if req_id and req_id in DUPLICATE_REQS:
            # Section runs from line_idx to just before the next heading
            end = heading_indices[idx + 1][0] if idx + 1 < len(heading_indices) else len(lines)
            for k in range(line_idx, end):
                to_drop.add(k)

    kept = [line for i, line in enumerate(lines) if i not in to_drop]
    path.write_text("".join(kept), encoding="utf-8")
    return len(to_drop)


# ---------------------------------------------------------------------------
# Step 2: Re-sync machine state from cleaned MD
# ---------------------------------------------------------------------------


def resync(root: Path) -> None:
    """Re-run specsmith sync."""
    sys.path.insert(0, str(root / "src"))
    from specsmith.sync import run_sync

    result = run_sync(root)
    print(
        f"  sync: reqs {result.reqs_before} → {result.reqs_after},"
        f" tests {result.tests_before} → {result.tests_after}"
    )


# ---------------------------------------------------------------------------
# Step 3: Export REQs/TESTs from JSON → grouped YAML files
# ---------------------------------------------------------------------------


def _yaml_dump_list(items: list[dict]) -> str:
    """Dump a list of dicts as clean YAML."""
    return yaml.dump(
        items,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        indent=2,
    )


def migrate_reqs_to_yaml(reqs_json: Path, out_dir: Path) -> dict[str, int]:
    """Export requirements.json → grouped YAML files."""
    reqs: list[dict] = json.loads(reqs_json.read_text("utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)

    groups: dict[str, list[dict]] = {}
    for r in reqs:
        g = _group_for_req(r["id"])
        groups.setdefault(g, []).append(r)

    counts: dict[str, int] = {}
    for stem, items in groups.items():
        items_sorted = sorted(items, key=lambda x: _req_num(x["id"]))
        dest = out_dir / f"{stem}.yml"
        header = (
            f"# specsmith requirements — {stem}\n"
            "# CANONICAL SOURCE: edit this file, not docs/REQUIREMENTS.md\n"
            "# docs/REQUIREMENTS.md is regenerated from these YAML files.\n"
            "#\n"
            "# Schema: id (REQ-NNN), title, description, source, status\n"
            "# Required fields: id, title, status\n"
        )
        dest.write_text(header + _yaml_dump_list(items_sorted), encoding="utf-8")
        counts[stem] = len(items_sorted)

    return counts


def migrate_tests_to_yaml(tests_json: Path, out_dir: Path) -> dict[str, int]:
    """Export testcases.json → grouped YAML files (grouped by req_id range)."""
    tests: list[dict] = json.loads(tests_json.read_text("utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)

    groups: dict[str, list[dict]] = {}
    for t in tests:
        req_id = t.get("requirement_id", "")
        g = _group_for_req(req_id) if req_id else OVERFLOW_GROUP
        groups.setdefault(g, []).append(t)

    counts: dict[str, int] = {}
    for stem, items in groups.items():
        items_sorted = sorted(items, key=lambda x: _test_num(x["id"]))
        dest = out_dir / f"{stem}.yml"
        header = (
            f"# specsmith test cases — {stem}\n"
            "# CANONICAL SOURCE: edit this file, not docs/TESTS.md\n"
            "# docs/TESTS.md is regenerated from these YAML files.\n"
            "#\n"
            "# Schema: id, title, description, requirement_id, type,\n"
            "#         verification_method, input, expected_behavior, confidence\n"
            "# Required fields: id, title, requirement_id\n"
        )
        dest.write_text(header + _yaml_dump_list(items_sorted), encoding="utf-8")
        counts[stem] = len(items_sorted)

    return counts


# ---------------------------------------------------------------------------
# Step 4: Write governance-mode flag
# ---------------------------------------------------------------------------


def write_governance_mode(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("yaml\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("specsmith governance → YAML migration")
    print("=" * 40)

    # Step 1: Remove duplicates
    print(f"\n[1] Removing duplicate REQs ({len(DUPLICATE_REQS)}) from REQUIREMENTS.md...")
    n = remove_duplicate_reqs(REQS_MD)
    print(f"    Dropped {n} lines from REQUIREMENTS.md")

    # Step 2: Re-sync machine state
    print("\n[2] Re-syncing .specsmith/ from cleaned REQUIREMENTS.md...")
    resync(ROOT)

    # Step 3: Migrate to YAML
    print("\n[3] Exporting requirements.json → docs/requirements/*.yml")
    req_counts = migrate_reqs_to_yaml(REQS_JSON, REQS_YAML_DIR)
    for stem, count in sorted(req_counts.items()):
        print(f"    {stem}.yml: {count} requirements")
    total_reqs = sum(req_counts.values())
    print(f"    Total: {total_reqs} requirements across {len(req_counts)} files")

    print("\n[4] Exporting testcases.json → docs/tests/*.yml")
    test_counts = migrate_tests_to_yaml(TESTS_JSON, TESTS_YAML_DIR)
    for stem, count in sorted(test_counts.items()):
        print(f"    {stem}.yml: {count} test cases")
    total_tests = sum(test_counts.values())
    print(f"    Total: {total_tests} test cases across {len(test_counts)} files")

    # Step 4: Write governance-mode flag
    print("\n[5] Writing .specsmith/governance-mode = yaml")
    write_governance_mode(GOV_MODE_FILE)

    print("\nDone. Next steps:")
    print("  - specsmith sync     (reads YAML if available, updates JSON + MD)")
    print("  - specsmith validate --strict  (schema checks)")
    print("  - git add docs/requirements docs/tests .specsmith/governance-mode")


if __name__ == "__main__":
    main()
