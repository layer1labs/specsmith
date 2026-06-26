# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""TEST-431 — legacy flat-file deprecation notices + teardown registry (REQ-421).

The ESDB-first overhaul removes legacy JSON/JSONL flat files forward-only. Rather
than delete anything now, every legacy site carries a greppable
``DEPRECATED(REQ-421)`` marker and ``docs/DEPRECATIONS.md`` enumerates each
artifact so a future teardown is a single grep.

These tests enforce that contract:

  1. The registry file exists and enumerates every legacy artifact.
  2. The canonical legacy modules each carry the source marker.
  3. Every marked source module is documented in the registry (no orphan markers),
     keeping the registry in sync with the code as teardown proceeds.
"""

from __future__ import annotations

from pathlib import Path

import pytest

MARKER = "DEPRECATED(REQ-421)"

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src" / "specsmith"
REGISTRY = REPO_ROOT / "docs" / "DEPRECATIONS.md"

# Legacy flat-file artifacts that must be enumerated in the registry.
LEGACY_ARTIFACTS = (
    ".specsmith/trace.jsonl",
    ".specsmith/workitems.json",
    ".specsmith/requirements.json",
    ".specsmith/testcases.json",
    ".specsmith/session_metrics.jsonl",
    ".specsmith/session-state.json",
    ".specsmith/conversation-history.jsonl",
)

# Canonical modules that must carry the source marker.
EXPECTED_MARKED_MODULES = (
    "src/specsmith/trace.py",
    "src/specsmith/wi_store.py",
    "src/specsmith/project_metrics.py",
    "src/specsmith/session_store.py",
    "src/specsmith/sync.py",
    "src/specsmith/auditor.py",
    "src/specsmith/compliance/regulations.py",
)


def _marked_source_files() -> set[str]:
    """Return POSIX repo-relative paths of src/ files containing the marker."""
    marked: set[str] = set()
    for path in SRC_ROOT.rglob("*.py"):
        if MARKER in path.read_text(encoding="utf-8"):
            marked.add(path.relative_to(REPO_ROOT).as_posix())
    return marked


def test_registry_exists() -> None:
    """docs/DEPRECATIONS.md must exist (REQ-421)."""
    assert REGISTRY.is_file(), "docs/DEPRECATIONS.md teardown registry is missing"


@pytest.mark.parametrize("artifact", LEGACY_ARTIFACTS)
def test_registry_enumerates_legacy_artifact(artifact: str) -> None:
    """Every legacy flat-file artifact must be enumerated in the registry (REQ-421)."""
    text = REGISTRY.read_text(encoding="utf-8")
    assert artifact in text, f"{artifact} is not enumerated in docs/DEPRECATIONS.md"


@pytest.mark.parametrize("module", EXPECTED_MARKED_MODULES)
def test_canonical_module_is_marked(module: str) -> None:
    """Each canonical legacy module must carry a DEPRECATED(REQ-421) marker."""
    path = REPO_ROOT / module
    assert path.is_file(), f"expected module {module} not found"
    assert MARKER in path.read_text(encoding="utf-8"), f"{module} is missing the {MARKER} marker"


def test_every_marker_is_documented() -> None:
    """No orphan markers: every marked src module is referenced in the registry (REQ-421)."""
    registry_text = REGISTRY.read_text(encoding="utf-8")
    marked = _marked_source_files()
    assert marked, "expected at least one DEPRECATED(REQ-421) marker in src/"
    undocumented = sorted(m for m in marked if m not in registry_text)
    assert not undocumented, (
        f"these marked modules are not documented in docs/DEPRECATIONS.md: {undocumented}"
    )
