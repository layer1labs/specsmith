# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Requirements and test gap analysis."""

from __future__ import annotations

import re
from pathlib import Path

_REQ_PATTERN = re.compile(r"\b(REQ-[A-Z]+-\d+)\b")
_TEST_COVERS_PATTERN = re.compile(
    r"(?:Covers|\*\*Requirement:?\*\*|Requirement):?\s*"
    r"(REQ-[A-Z]+-\d+(?:\s*,\s*REQ-[A-Z]+-\d+)*)"
)
_TEST_ID_PATTERN = re.compile(r"\b(TEST-[A-Z]+-\d+)\b")


def list_reqs(root: Path) -> list[dict[str, str]]:
    """Parse REQUIREMENTS.md and return list of requirement entries."""
    req_path = root / "docs" / "REQUIREMENTS.md"
    if not req_path.exists():
        return []

    content = req_path.read_text(encoding="utf-8")
    reqs: list[dict[str, str]] = []
    current: dict[str, str] = {}

    for line in content.splitlines():
        req_match = re.match(r"^#{2,3}\s+(REQ-[A-Z]+-\d+)", line)
        if req_match:
            if current:
                reqs.append(current)
            current = {"id": req_match.group(1)}
        elif line.startswith("- **") and current:
            m = re.match(r"- \*\*(.+?)\*\*:\s*(.+)", line)
            if m:
                current[m.group(1).lower()] = m.group(2).strip()

    if current:
        reqs.append(current)
    return reqs


def add_req(
    root: Path,
    req_id: str,
    *,
    component: str = "",
    priority: str = "medium",
    description: str = "",
) -> None:
    """Append a new requirement to REQUIREMENTS.md."""
    req_path = root / "docs" / "REQUIREMENTS.md"
    entry = f"\n### {req_id}\n"
    if component:
        entry += f"- **Component**: {component}\n"
    entry += f"- **Priority**: {priority}\n"
    entry += "- **Status**: Draft\n"
    if description:
        entry += f"- **Description**: {description}\n"

    content = req_path.read_text(encoding="utf-8") if req_path.exists() else "# Requirements\n"

    content += entry
    req_path.parent.mkdir(parents=True, exist_ok=True)
    req_path.write_text(content, encoding="utf-8")


def trace_reqs(root: Path) -> list[dict[str, object]]:
    """Map each REQ to its covering TESTs."""
    req_path = root / "docs" / "REQUIREMENTS.md"
    test_path = root / "docs" / "TESTS.md"

    req_ids: list[str] = []
    if req_path.exists():
        req_ids = sorted(set(_REQ_PATTERN.findall(req_path.read_text(encoding="utf-8"))))

    covered_by: dict[str, list[str]] = {r: [] for r in req_ids}

    if test_path.exists():
        test_text = test_path.read_text(encoding="utf-8")
        current_test = ""
        for line in test_text.splitlines():
            test_match = _TEST_ID_PATTERN.search(line)
            if test_match and line.startswith("#"):
                current_test = test_match.group(1)
            covers_match = _TEST_COVERS_PATTERN.search(line)
            if covers_match and current_test:
                for rid in _REQ_PATTERN.findall(covers_match.group(0)):
                    if rid in covered_by:
                        covered_by[rid].append(current_test)

    return [
        {"req": r, "tests": tests, "covered": len(tests) > 0} for r, tests in covered_by.items()
    ]


def get_gaps(root: Path) -> list[str]:
    """Return REQ IDs that have no test coverage."""
    return [t["req"] for t in trace_reqs(root) if not t["covered"]]  # type: ignore[misc]


def get_orphan_tests(root: Path) -> list[str]:
    """Return TEST IDs that reference non-existent REQs."""
    req_path = root / "docs" / "REQUIREMENTS.md"
    test_path = root / "docs" / "TESTS.md"

    req_ids: set[str] = set()
    if req_path.exists():
        req_ids = set(_REQ_PATTERN.findall(req_path.read_text(encoding="utf-8")))

    orphans: list[str] = []
    if test_path.exists():
        test_text = test_path.read_text(encoding="utf-8")
        for match in _TEST_COVERS_PATTERN.finditer(test_text):
            for rid in _REQ_PATTERN.findall(match.group(0)):
                if rid not in req_ids and rid not in orphans:
                    orphans.append(rid)

    return sorted(orphans)
