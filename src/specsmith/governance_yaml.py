# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""YAML-native governance layer (REQ-003 extension).

When ``docs/requirements/*.yml`` and ``docs/tests/*.yml`` exist and
``.specsmith/governance-mode`` contains ``yaml``, this module is the canonical
source of truth — Markdown files are *generated* from YAML, not the other way
around.

Public surface
--------------
- ``load_yaml_requirements(root)``  → list[dict]
- ``load_yaml_tests(root)``         → list[dict]
- ``save_yaml_requirements(root, reqs)``  — writes back to grouped files
- ``save_yaml_tests(root, tests)``        — writes back to grouped files
- ``generate_requirements_md(reqs)``  → str
- ``generate_tests_md(tests)``        → str
- ``is_yaml_mode(root)``              → bool
- ``strict_validate(root)``           → ValidationReport
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml  # PyYAML — already a specsmith dep

# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

_REQ_REQUIRED = {"id", "title", "status"}
_TEST_REQUIRED = {"id", "title", "requirement_id"}

# Groups: maps file stem → REQ numeric ranges (inclusive)
_REQ_GROUPS: list[tuple[str, list[tuple[int, int]]]] = [
    ("governance", [(1, 64)]),
    ("agent", [(65, 129)]),
    ("harness", [(130, 160)]),
    ("intelligence", [(161, 220)]),
    ("context", [(244, 247)]),
    ("esdb", [(248, 262)]),
    ("ai_intelligence", [(263, 299)]),
    ("yaml_governance", [(300, 399)]),
]
_OVERFLOW_GROUP = "overflow"


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
    for stem, ranges in _REQ_GROUPS:
        for lo, hi in ranges:
            if lo <= n <= hi:
                return stem
    return _OVERFLOW_GROUP


def _yaml_load(path: Path) -> list[dict[str, Any]]:
    """Load a YAML file; return [] on any error or if content is not a list."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [d for d in data if isinstance(d, dict)]
    except Exception:  # noqa: BLE001
        pass
    return []


def _yaml_dump(items: list[dict[str, Any]], header: str) -> str:
    """Serialize items to YAML string with a comment header."""
    body = yaml.dump(
        items,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        indent=2,
    )
    return header + body


# ---------------------------------------------------------------------------
# Mode detection
# ---------------------------------------------------------------------------


def is_yaml_mode(root: Path) -> bool:
    """Return True if .specsmith/governance-mode == 'yaml'."""
    mode_file = root / ".specsmith" / "governance-mode"
    if not mode_file.exists():
        return False
    return mode_file.read_text(encoding="utf-8").strip().lower() == "yaml"


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------


def load_yaml_requirements(root: Path) -> list[dict[str, Any]]:
    """Load all requirements from docs/requirements/*.yml, sorted by REQ number."""
    yaml_dir = root / "docs" / "requirements"
    if not yaml_dir.is_dir():
        return []
    all_reqs: list[dict[str, Any]] = []
    for yf in sorted(yaml_dir.glob("*.yml")):
        all_reqs.extend(_yaml_load(yf))
    # Deduplicate by ID (last-write-wins for duplicate IDs)
    seen: dict[str, dict[str, Any]] = {}
    for r in all_reqs:
        if r.get("id"):
            seen[r["id"]] = r
    return sorted(seen.values(), key=lambda r: _req_num(str(r.get("id", ""))))


def load_yaml_tests(root: Path) -> list[dict[str, Any]]:
    """Load all test cases from docs/tests/*.yml, sorted by TEST number."""
    yaml_dir = root / "docs" / "tests"
    if not yaml_dir.is_dir():
        return []
    all_tests: list[dict[str, Any]] = []
    for yf in sorted(yaml_dir.glob("*.yml")):
        all_tests.extend(_yaml_load(yf))
    seen: dict[str, dict[str, Any]] = {}
    for t in all_tests:
        if t.get("id"):
            seen[t["id"]] = t
    return sorted(seen.values(), key=lambda t: _test_num(str(t.get("id", ""))))


# ---------------------------------------------------------------------------
# Save (write back to grouped files)
# ---------------------------------------------------------------------------

_REQ_FILE_HEADER = (
    "# specsmith requirements — {stem}\n"
    "# CANONICAL SOURCE: edit this file, not docs/REQUIREMENTS.md\n"
    "# docs/REQUIREMENTS.md is regenerated from these YAML files.\n"
    "#\n"
    "# Schema: id (REQ-NNN), title, description, source, status\n"
    "# Required fields: id, title, status\n"
)
_TEST_FILE_HEADER = (
    "# specsmith test cases — {stem}\n"
    "# CANONICAL SOURCE: edit this file, not docs/TESTS.md\n"
    "# docs/TESTS.md is regenerated from these YAML files.\n"
    "#\n"
    "# Schema: id, title, description, requirement_id, type,\n"
    "#         verification_method, input, expected_behavior, confidence\n"
    "# Required fields: id, title, requirement_id\n"
)


def save_yaml_requirements(root: Path, reqs: list[dict[str, Any]]) -> None:
    """Write requirements back to docs/requirements/*.yml grouped files."""
    yaml_dir = root / "docs" / "requirements"
    yaml_dir.mkdir(parents=True, exist_ok=True)
    groups: dict[str, list[dict[str, Any]]] = {}
    for r in reqs:
        g = _group_for_req(str(r.get("id", "")))
        groups.setdefault(g, []).append(r)
    for stem, items in groups.items():
        items_sorted = sorted(items, key=lambda r: _req_num(str(r.get("id", ""))))
        header = _REQ_FILE_HEADER.format(stem=stem)
        (yaml_dir / f"{stem}.yml").write_text(_yaml_dump(items_sorted, header), encoding="utf-8")


def save_yaml_tests(root: Path, tests: list[dict[str, Any]]) -> None:
    """Write test cases back to docs/tests/*.yml grouped files."""
    yaml_dir = root / "docs" / "tests"
    yaml_dir.mkdir(parents=True, exist_ok=True)
    groups: dict[str, list[dict[str, Any]]] = {}
    for t in tests:
        req_id = str(t.get("requirement_id", ""))
        g = _group_for_req(req_id) if req_id else _OVERFLOW_GROUP
        groups.setdefault(g, []).append(t)
    for stem, items in groups.items():
        items_sorted = sorted(items, key=lambda t: _test_num(str(t.get("id", ""))))
        header = _TEST_FILE_HEADER.format(stem=stem)
        (yaml_dir / f"{stem}.yml").write_text(_yaml_dump(items_sorted, header), encoding="utf-8")


# ---------------------------------------------------------------------------
# MD generation (YAML → Markdown)
# ---------------------------------------------------------------------------

_MD_REQ_HEADER = "# Requirements\n\n"
_MD_TEST_HEADER = "# Test Specification\n\n"


def generate_requirements_md(reqs: list[dict[str, Any]]) -> str:
    """Render a REQUIREMENTS.md string from the canonical YAML records."""
    lines: list[str] = [_MD_REQ_HEADER]
    for r in reqs:
        rid = r.get("id", "")
        title = r.get("title", rid)
        lines.append(f"## {rid}. {title}\n")
        lines.append(f"- **ID:** {rid}\n")
        lines.append(f"- **Title:** {title}\n")
        desc = r.get("description", "")
        if desc:
            lines.append(f"- **Description:** {desc}\n")
        status = r.get("status", "defined")
        lines.append(f"- **Status:** {status}\n")
        source = r.get("source", "docs/REQUIREMENTS.md")
        lines.append(f"- **Source:** {source}\n")
        # Extra fields (priority, section, etc.)
        for k, v in r.items():
            if k not in ("id", "title", "description", "status", "source"):
                lines.append(f"- **{k.title()}:** {v}\n")
        lines.append("\n")
    return "".join(lines)


def generate_tests_md(tests: list[dict[str, Any]]) -> str:
    """Render a TESTS.md string from the canonical YAML records."""
    lines: list[str] = [_MD_TEST_HEADER]
    for t in tests:
        tid = t.get("id", "")
        title = t.get("title", tid)
        lines.append(f"## {tid}. {title}\n")
        lines.append(f"- **ID:** {tid}\n")
        lines.append(f"- **Title:** {title}\n")
        desc = t.get("description", "")
        if desc:
            lines.append(f"- **Description:** {desc}\n")
        req_id = t.get("requirement_id", "")
        if req_id:
            lines.append(f"- **Requirement ID:** {req_id}\n")
        for k in ("type", "verification_method"):
            v = t.get(k, "")
            if v:
                label = k.replace("_", " ").title()
                lines.append(f"- **{label}:** {v}\n")
        inp = t.get("input", {})
        if inp and inp != {}:
            lines.append(f"- **Input:** {inp}\n")
        exp = t.get("expected_behavior", {})
        if exp and exp != {}:
            lines.append(f"- **Expected Behavior:** {exp}\n")
        conf = t.get("confidence", 1.0)
        lines.append(f"- **Confidence:** {conf}\n")
        lines.append("\n")
    return "".join(lines)


# ---------------------------------------------------------------------------
# Strict validation
# ---------------------------------------------------------------------------


@dataclass
class StrictViolation:
    check: str
    message: str
    severity: str = "error"  # "error" | "warning"


@dataclass
class StrictValidationReport:
    violations: list[StrictViolation] = field(default_factory=list)

    @property
    def errors(self) -> list[StrictViolation]:
        return [v for v in self.violations if v.severity == "error"]

    @property
    def warnings(self) -> list[StrictViolation]:
        return [v for v in self.violations if v.severity == "warning"]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def add(self, check: str, message: str, severity: str = "error") -> None:
        self.violations.append(StrictViolation(check, message, severity))


def strict_validate(root: Path) -> StrictValidationReport:
    """Run the strict governance schema checks.

    Checks performed:
    - Duplicate REQ IDs across YAML files
    - Duplicate TEST IDs across YAML files
    - Missing required fields (id, title, status for REQs; id, title, requirement_id for TESTs)
    - Orphaned tests (TEST references non-existent REQ ID)
    - REQs without any test coverage
    - Machine state drift (JSON out of sync with YAML)
    - Title duplicates (same title, different IDs)
    """
    report = StrictValidationReport()

    # --- Load both sources ---
    if is_yaml_mode(root):
        reqs = load_yaml_requirements(root)
        tests = load_yaml_tests(root)
    else:
        # Fall back to JSON machine state
        import contextlib
        import json as _json

        reqs = []
        tests = []
        reqs_json = root / ".specsmith" / "requirements.json"
        tests_json = root / ".specsmith" / "testcases.json"
        with contextlib.suppress(OSError, ValueError):
            reqs = _json.loads(reqs_json.read_text("utf-8"))
        with contextlib.suppress(OSError, ValueError):
            tests = _json.loads(tests_json.read_text("utf-8"))

    req_ids = [str(r.get("id", "")) for r in reqs]
    test_ids = [str(t.get("id", "")) for t in tests]

    # 1. Duplicate REQ IDs
    req_id_counts: dict[str, int] = {}
    for rid in req_ids:
        req_id_counts[rid] = req_id_counts.get(rid, 0) + 1
    for rid, count in sorted(req_id_counts.items()):
        if count > 1:
            report.add("dup-req-id", f"Duplicate REQ ID: {rid} appears {count} times")

    # 2. Duplicate TEST IDs
    test_id_counts: dict[str, int] = {}
    for tid in test_ids:
        test_id_counts[tid] = test_id_counts.get(tid, 0) + 1
    for tid, count in sorted(test_id_counts.items()):
        if count > 1:
            report.add("dup-test-id", f"Duplicate TEST ID: {tid} appears {count} times")

    # 3. Missing required REQ fields
    req_id_set = set(req_ids)
    for r in reqs:
        missing = _REQ_REQUIRED - {k for k, v in r.items() if v is not None and v != ""}
        if missing:
            report.add(
                "req-schema",
                f"REQ {r.get('id', '?')} missing required fields: {sorted(missing)}",
            )

    # 4. Missing required TEST fields
    for t in tests:
        missing = _TEST_REQUIRED - {k for k, v in t.items() if v is not None and v != ""}
        if missing:
            report.add(
                "test-schema",
                f"TEST {t.get('id', '?')} missing required fields: {sorted(missing)}",
            )

    # 5. Orphaned tests (TEST references non-existent REQ)
    for t in tests:
        req_ref = str(t.get("requirement_id", ""))
        if req_ref and req_ref not in req_id_set:
            report.add(
                "orphan-test",
                f"TEST {t.get('id', '?')} references non-existent {req_ref}",
            )

    # 6. REQs without any test coverage
    tested_reqs = {str(t.get("requirement_id", "")) for t in tests}
    for r in reqs:
        rid = str(r.get("id", ""))
        if rid and rid not in tested_reqs:
            report.add(
                "untested-req",
                f"{rid} has no test coverage",
                severity="warning",
            )

    # 7. Duplicate titles (different IDs with identical titles)
    title_to_ids: dict[str, list[str]] = {}
    for r in reqs:
        t_lower = str(r.get("title", "")).lower().strip()
        if t_lower:
            title_to_ids.setdefault(t_lower, []).append(str(r.get("id", "")))
    for title, ids in sorted(title_to_ids.items()):
        if len(ids) > 1:
            report.add(
                "dup-req-title",
                f"Duplicate REQ title '{title[:60]}' shared by: {ids}",
                severity="warning",
            )

    # 8. Machine state drift check (if YAML mode)
    if is_yaml_mode(root):
        import contextlib
        import json as _json

        old_reqs: list[dict[str, Any]] = []
        reqs_json = root / ".specsmith" / "requirements.json"
        with contextlib.suppress(OSError, ValueError):
            old_reqs = _json.loads(reqs_json.read_text("utf-8"))

        old_req_ids = {str(r.get("id", "")) for r in old_reqs}
        yaml_req_ids = {str(r.get("id", "")) for r in reqs}
        if old_req_ids != yaml_req_ids:
            new_in_yaml = yaml_req_ids - old_req_ids
            stale_in_json = old_req_ids - yaml_req_ids
            if new_in_yaml:
                report.add(
                    "sync-drift",
                    f"YAML has {len(new_in_yaml)} REQs not in JSON — run 'specsmith sync'",
                    severity="warning",
                )
            if stale_in_json:
                report.add(
                    "sync-drift",
                    f"JSON has {len(stale_in_json)} stale REQs not in YAML — run 'specsmith sync'",
                    severity="warning",
                )

    return report
