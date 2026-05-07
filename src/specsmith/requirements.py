# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Requirements and test gap analysis."""

from __future__ import annotations

import re
from pathlib import Path

# Flexible patterns that handle both two-part (REQ-001) and three-part
# (REQ-CLI-001, REG-012) identifiers used across projects.
_FLEX_REQ = r"REQ-(?:[A-Z][A-Z0-9_]*-)?\d+"
_FLEX_TEST = r"TEST-(?:[A-Z][A-Z0-9_]*-)?\d+"

_REQ_PATTERN = re.compile(r"\b(" + _FLEX_REQ + r")\b")
_TEST_COVERS_PATTERN = re.compile(
    r"(?:Covers|\*\*Requirement(?:\s+ID)?:?\*\*|Requirement(?:\s+ID)?):?\s*"
    r"(" + _FLEX_REQ + r"(?:\s*,\s*" + _FLEX_REQ + r")*)"
)
_TEST_ID_PATTERN = re.compile(r"\b(" + _FLEX_TEST + r")\b")

# Heading detectors for REQUIREMENTS.md (two styles supported):
#   Style A: ## REQ-001 or ## REQ-CLI-001
#   Style B: ## 1. Some Title  (id comes from a - **ID:** field)
_DIRECT_REQ_HEADING = re.compile(r"^#{2,3}\s+(" + _FLEX_REQ + r")")
_NUMBERED_HEADING = re.compile(r"^#{2,3}\s+\d+\.\s+(.+)$")
_ID_FIELD = re.compile(r"^-\s+\*\*ID:\*\*\s+(" + _FLEX_REQ + r")\s*$")
_FIELD_LINE = re.compile(r"^-\s+\*\*(.+?)\*\*:\s*(.+)")


def list_reqs(root: Path) -> list[dict[str, str]]:
    """Parse REQUIREMENTS.md and return list of requirement entries.

    Handles both Style A (``## REQ-001`` heading) and Style B
    (``## 1. Title`` numbered heading with ``- **ID:** REQ-001`` inline field).
    """
    req_path = root / "docs" / "REQUIREMENTS.md"
    if not req_path.exists():
        return []

    content = req_path.read_text(encoding="utf-8")
    reqs: list[dict[str, str]] = []
    current: dict[str, str] = {}
    pending_title: str = ""  # title from a Style B numbered heading

    def _flush() -> None:
        if current.get("id"):
            reqs.append(dict(current))

    for line in content.splitlines():
        # Style A: ## REQ-001 or ## REQ-CLI-001
        m_direct = _DIRECT_REQ_HEADING.match(line)
        if m_direct:
            _flush()
            current = {"id": m_direct.group(1)}
            pending_title = ""
            continue

        # Style B step 1: ## N. Title
        m_numbered = _NUMBERED_HEADING.match(line)
        if m_numbered:
            _flush()
            current = {}
            pending_title = m_numbered.group(1).strip()
            continue

        # Style B step 2: - **ID:** REQ-NNN resolves the pending title
        m_id = _ID_FIELD.match(line)
        if m_id and pending_title and not current.get("id"):
            current["id"] = m_id.group(1)
            current.setdefault("title", pending_title)
            pending_title = ""
            continue

        # Field lines under any active section
        if current.get("id"):
            m_field = _FIELD_LINE.match(line)
            if m_field:
                key = m_field.group(1).lower()
                val = m_field.group(2).strip()
                if key != "id":  # already captured
                    current.setdefault(key, val)

    _flush()
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
