# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Machine state sync — keeps .specsmith/ JSON in sync with governance sources.

Implements REQ-003 (Machine State Must Reflect Governance State).

Canonical sources (YAML-first, Markdown fallback):
  docs/requirements/*.yml  ->  .specsmith/requirements.json  ->  docs/REQUIREMENTS.md
  docs/tests/*.yml         ->  .specsmith/testcases.json     ->  docs/TESTS.md

Design contract:
  - When .specsmith/governance-mode == "yaml" (YAML-first mode):
    YAML files are the source of truth.  JSON is a derived cache, MD is generated.
  - When governance-mode is absent/"markdown" (legacy mode):
    Markdown is the source of truth.  JSON is a derived cache.
  - Existing ``input`` / ``expected_behavior`` fields in testcases.json are preserved
    so hand-crafted test specs are not clobbered.
  - workitems.json is NOT managed here — it is runtime state only and should
    be gitignored.  Preflight allocates WI IDs dynamically at runtime.
"""

from __future__ import annotations

import contextlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Markdown parsers
# ---------------------------------------------------------------------------

# Matches either:
#   Style A: ## REQ-001  or  ## REQ-CLI-001 — Title
#   Style B: ## N. Title  (ID comes from inline - **ID:** REQ-NNN field)
_FLEX_REQ_ID = r"REQ-(?:[A-Z][A-Z0-9_]*-)?\d+"
_NUMBERED_HEADING = re.compile(r"^#{1,3}\s+\d+\.\s+(.+?)\s*$")
_DIRECT_HEADING = re.compile(r"^#{1,3}\s+(" + _FLEX_REQ_ID + r")\b")
_ID_FIELD = re.compile(r"^-\s+\*\*ID:\*\*\s+(" + _FLEX_REQ_ID + r")")
_FIELD_LINE = re.compile(r"^-\s+\*\*(.+?):\*\*\s+(.+)")

_FLEX_TEST_ID = r"TEST-(?:[A-Z][A-Z0-9_]*-)?\d+"
_TEST_NUMBERED_HEADING = re.compile(r"^#{1,3}\s+(?:TEST-[A-Z0-9_-]+\s+)?(.+?)\s*$")
_TEST_ID_FIELD = re.compile(r"^-\s+\*\*ID:\*\*\s+(" + _FLEX_TEST_ID + r")")


def parse_requirements_md(text: str) -> list[dict[str, Any]]:
    """Parse REQUIREMENTS.md and return a list of requirement records."""
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    pending_title: str = ""

    def _flush() -> None:
        if current.get("id"):
            records.append(dict(current))

    for line in text.splitlines():
        m_direct = _DIRECT_HEADING.match(line)
        if m_direct:
            _flush()
            current = {"id": m_direct.group(1)}
            pending_title = ""
            continue

        m_num = _NUMBERED_HEADING.match(line)
        if m_num:
            _flush()
            current = {}
            pending_title = m_num.group(1).strip()
            continue

        m_id = _ID_FIELD.match(line)
        if m_id and pending_title and not current.get("id"):
            current["id"] = m_id.group(1)
            current.setdefault("title", pending_title)
            pending_title = ""
            continue

        if current.get("id"):
            m_field = _FIELD_LINE.match(line)
            if m_field:
                key = m_field.group(1).strip().lower()
                val = m_field.group(2).strip()
                if key not in ("id",):
                    current.setdefault(key, val)

    _flush()
    return [
        {
            "id": r["id"],
            "title": r.get("title", r["id"]),
            "description": r.get("description", ""),
            "source": r.get("source", "docs/REQUIREMENTS.md"),
            "status": r.get("status", "defined"),
        }
        for r in records
    ]


def parse_tests_md(text: str) -> list[dict[str, Any]]:
    """Parse TESTS.md and return a list of test case records."""
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    pending_title: str = ""

    def _flush() -> None:
        if current.get("id"):
            records.append(dict(current))

    for line in text.splitlines():
        # TEST-NNN heading or numbered-style
        m_test_heading = re.match(r"^#{1,3}\s+(" + _FLEX_TEST_ID + r")(?:\.\s+(.+?))?\s*$", line)
        if m_test_heading:
            _flush()
            current = {
                "id": m_test_heading.group(1),
                "title": (m_test_heading.group(2) or "").strip(),
            }
            pending_title = ""
            continue

        # Numbered-style heading without TEST- prefix
        m_num = _NUMBERED_HEADING.match(line)
        if m_num and not re.match(r"#{1,3}\s+TEST-", line):
            _flush()
            current = {}
            pending_title = m_num.group(1).strip()
            continue

        # Inline ID field (resolves numbered heading)
        m_id = _TEST_ID_FIELD.match(line)
        if m_id and pending_title and not current.get("id"):
            current["id"] = m_id.group(1)
            current.setdefault("title", pending_title)
            pending_title = ""
            continue

        if current.get("id"):
            m_field = _FIELD_LINE.match(line)
            if m_field:
                key = m_field.group(1).strip().lower()
                val = m_field.group(2).strip()
                if key not in ("id",):
                    current.setdefault(key, val)

    _flush()
    return [
        {
            "id": r["id"],
            "title": r.get("title", r["id"]),
            "description": r.get("description", ""),
            "requirement_id": r.get("requirement id", r.get("requirement_id", "")),
            "type": r.get("type", "unit"),
            "verification_method": r.get(
                "verification method", r.get("verification_method", "evaluator")
            ),
            "input": {},
            "expected_behavior": {},
            "confidence": 1.0,
        }
        for r in records
    ]


# ---------------------------------------------------------------------------
# Sync result
# ---------------------------------------------------------------------------


@dataclass
class SyncResult:
    reqs_before: int
    reqs_after: int
    tests_before: int
    tests_after: int
    reqs_changed: bool
    tests_changed: bool
    dry_run: bool

    @property
    def changed(self) -> bool:
        return self.reqs_changed or self.tests_changed

    @property
    def message(self) -> str:
        status = "would update" if self.dry_run else "synced"
        parts: list[str] = []
        if self.reqs_changed:
            parts.append(f"requirements.json: {self.reqs_before} → {self.reqs_after} entries")
        if self.tests_changed:
            parts.append(f"testcases.json: {self.tests_before} → {self.tests_after} entries")
        if parts:
            return f"Machine state {status}: " + "; ".join(parts)
        return "Machine state already in sync."


# ---------------------------------------------------------------------------
# Core sync
# ---------------------------------------------------------------------------


def run_sync(root: Path, *, dry_run: bool = False) -> SyncResult:
    """Regenerate .specsmith/requirements.json and testcases.json from governance sources.

    In YAML-first mode (governance-mode == "yaml"):
      1. Reads docs/requirements/*.yml and docs/tests/*.yml
      2. Writes .specsmith/requirements.json and testcases.json
      3. Regenerates docs/REQUIREMENTS.md and docs/TESTS.md as artifacts

    In legacy Markdown mode:
      1. Reads docs/REQUIREMENTS.md and docs/TESTS.md
      2. Writes .specsmith/requirements.json and testcases.json

    Args:
        root:    Project root directory.
        dry_run: If True, compute the diff but do not write anything.

    Returns:
        A :class:`SyncResult` describing what changed.
    """
    from specsmith.governance_yaml import (
        generate_requirements_md,
        generate_tests_md,
        is_yaml_mode,
        load_yaml_requirements,
        load_yaml_tests,
    )

    state_dir = root / ".specsmith"
    reqs_md_path = root / "docs" / "REQUIREMENTS.md"
    tests_md_path = root / "docs" / "TESTS.md"
    reqs_json_path = state_dir / "requirements.json"
    tests_json_path = state_dir / "testcases.json"

    if is_yaml_mode(root):
        # ── YAML-first mode ─────────────────────────────────────────────────
        new_reqs = load_yaml_requirements(root)
        new_tests = load_yaml_tests(root)

        # Normalise to the same schema that the Markdown path produces
        new_reqs = [
            {
                "id": r["id"],
                "title": r.get("title", r["id"]),
                "description": str(r.get("description", "")),
                "source": r.get("source", "docs/requirements/"),
                "status": str(r.get("status", "defined")),
            }
            for r in new_reqs
        ]
        new_tests = [
            {
                "id": t["id"],
                "title": t.get("title", t["id"]),
                "description": str(t.get("description", "")),
                "requirement_id": str(t.get("requirement_id", "")),
                "type": str(t.get("type", "unit")),
                "verification_method": str(t.get("verification_method", "evaluator")),
                "input": t.get("input") or {},
                "expected_behavior": t.get("expected_behavior") or {},
                "confidence": float(t.get("confidence", 1.0)),
            }
            for t in new_tests
        ]
    else:
        # ── Legacy Markdown mode ─────────────────────────────────────────────
        new_reqs = []
        if reqs_md_path.exists():
            new_reqs = parse_requirements_md(reqs_md_path.read_text(encoding="utf-8"))

        new_tests = []
        if tests_md_path.exists():
            new_tests = parse_tests_md(tests_md_path.read_text(encoding="utf-8"))

    # Placeholder so the variable is always defined for the merge step below
    new_reqs_obj: list[dict[str, Any]] = new_reqs
    new_tests_obj: list[dict[str, Any]] = new_tests

    # Load existing JSON for comparison (and to preserve hand-crafted fields)
    old_reqs: list[dict[str, Any]] = []
    if reqs_json_path.exists():
        with contextlib.suppress(OSError, ValueError):
            old_reqs = json.loads(reqs_json_path.read_text(encoding="utf-8"))

    old_tests: list[dict[str, Any]] = []
    existing_test_map: dict[str, dict[str, Any]] = {}
    if tests_json_path.exists():
        with contextlib.suppress(OSError, ValueError):
            old_tests = json.loads(tests_json_path.read_text(encoding="utf-8"))
            existing_test_map = {t["id"]: t for t in old_tests if isinstance(t, dict)}

    # Merge: preserve existing input/expected_behavior for tests that already
    # have hand-crafted content so we don't clobber kairos-style detailed specs.
    for tc in new_tests_obj:
        existing = existing_test_map.get(tc["id"], {})
        if existing.get("input"):
            tc["input"] = existing["input"]
        if existing.get("expected_behavior"):
            tc["expected_behavior"] = existing["expected_behavior"]

    # Detect drift (compare by serialising to canonical JSON)
    reqs_before = len(old_reqs)
    tests_before = len(old_tests)
    reqs_changed = json.dumps(new_reqs_obj, sort_keys=True) != json.dumps(old_reqs, sort_keys=True)
    tests_changed = json.dumps(new_tests_obj, sort_keys=True) != json.dumps(
        old_tests, sort_keys=True
    )

    if not dry_run:
        state_dir.mkdir(parents=True, exist_ok=True)
        if reqs_changed:
            reqs_json_path.write_text(
                json.dumps(new_reqs_obj, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        if tests_changed:
            tests_json_path.write_text(
                json.dumps(new_tests_obj, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        # In YAML-first mode also regenerate the Markdown as a derived artifact
        from specsmith.governance_yaml import is_yaml_mode

        if is_yaml_mode(root):
            md_reqs = generate_requirements_md(new_reqs_obj)
            md_tests = generate_tests_md(new_tests_obj)
            reqs_md_path.parent.mkdir(parents=True, exist_ok=True)
            reqs_md_path.write_text(md_reqs, encoding="utf-8")
            tests_md_path.parent.mkdir(parents=True, exist_ok=True)
            tests_md_path.write_text(md_tests, encoding="utf-8")

    return SyncResult(
        reqs_before=reqs_before,
        reqs_after=len(new_reqs_obj),
        tests_before=tests_before,
        tests_after=len(new_tests_obj),
        reqs_changed=reqs_changed,
        tests_changed=tests_changed,
        dry_run=dry_run,
    )


def check_sync(root: Path) -> SyncResult:
    """Check whether machine state is in sync without writing anything.

    Convenience wrapper around :func:`run_sync` with ``dry_run=True``.
    Used by :func:`specsmith.auditor.run_audit` to surface sync drift warnings.
    """
    return run_sync(root, dry_run=True)
