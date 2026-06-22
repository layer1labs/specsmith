# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Requirements and test gap analysis."""

from __future__ import annotations

import re
from pathlib import Path
from typing import cast

# Flexible patterns that handle both two-part (REQ-001) and three-part
# (REQ-CLI-001, REG-012) identifiers used across projects.
# Letter suffixes (e.g. TEST-NN-002a, TEST-NN-002b) are supported via [a-z]* —
# without this, the \b word boundary after \d+ would not match when a letter
# follows digits, causing the ID to be silently skipped (#183).
_FLEX_REQ = r"REQ-(?:[A-Z][A-Z0-9_]*-)?\d+"
_FLEX_TEST = r"TEST-(?:[A-Z][A-Z0-9_]*-)?\d+[a-z]*"

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
    title: str = "",
    component: str = "",
    priority: str = "medium",
    description: str = "",
) -> None:
    """Append a new requirement to REQUIREMENTS.md.

    Emits the standard Style A format::

        ## REQ-NNN: Title
        Description text as a plain paragraph.

    This matches the format already used by every other requirement in
    REQUIREMENTS.md and is correctly parsed by ``sync`` and ``preflight``.
    """
    req_path = root / "docs" / "REQUIREMENTS.md"
    # Build heading:  ## REQ-NNN  or  ## REQ-NNN: Title
    heading_title = f": {title}" if title else ""
    entry = f"\n## {req_id}{heading_title}\n"
    if description:
        # Plain paragraph — not a bullet list (matches parser expectations)
        entry += f"{description}\n"
    # Legacy fields kept for backward-compat but written as metadata bullets
    if component:
        entry += f"- **Component**: {component}\n"
    if priority and priority != "medium":
        entry += f"- **Priority**: {priority}\n"

    content = req_path.read_text(encoding="utf-8") if req_path.exists() else "# Requirements\n"

    content += entry
    req_path.parent.mkdir(parents=True, exist_ok=True)
    req_path.write_text(content, encoding="utf-8")


def trace_reqs(root: Path) -> list[dict[str, object]]:
    """Map each REQ to its covering TESTs.

    In YAML-first mode, reads .specsmith/testcases.json directly — this avoids
    regex-based ID parsing entirely and correctly handles letter-suffix IDs
    (e.g. TEST-NN-002a, TEST-NN-002b) that were previously misidentified (#183).
    Falls back to TESTS.md regex parsing in legacy Markdown mode.
    """
    import json as _json

    req_path = root / "docs" / "REQUIREMENTS.md"
    test_path = root / "docs" / "TESTS.md"
    testcases_json = root / ".specsmith" / "testcases.json"

    req_ids: list[str] = []
    if req_path.exists():
        req_ids = sorted(set(_REQ_PATTERN.findall(req_path.read_text(encoding="utf-8"))))

    covered_by: dict[str, list[str]] = {r: [] for r in req_ids}

    # YAML mode: prefer machine-readable testcases.json — exact IDs, no regex.
    if testcases_json.is_file():
        try:
            records = _json.loads(testcases_json.read_text(encoding="utf-8"))
            for record in records:
                if (
                    isinstance(record, dict)
                    and isinstance(record.get("requirement_id"), str)
                    and isinstance(record.get("id"), str)
                ):
                    rid = record["requirement_id"]
                    if rid in covered_by:
                        covered_by[rid].append(record["id"])
            return [
                {"req": r, "tests": tests, "covered": len(tests) > 0}
                for r, tests in covered_by.items()
            ]
        except (OSError, ValueError):
            pass  # Fall through to TESTS.md regex parsing

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
    return [cast(str, t["req"]) for t in trace_reqs(root) if not t["covered"]]


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
