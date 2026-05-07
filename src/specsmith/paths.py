# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Canonical path constants for specsmith governance files.

## File Structure Convention
All governance files (except AGENTS.md) live in docs/.
The project scaffold config is docs/specsmith.yml (renamed from scaffold.yml).

  root/
    AGENTS.md          ← only governance file at root
    CONTRIBUTING.md    ← community files stay at root
    CHANGELOG.md
    README.md / LICENSE
    docs/
      specsmith.yml    ← project config (canonical; was scaffold.yml)
      REQUIREMENTS.md  ← formal requirements (canonical)
      TESTS.md         ← test specifications (canonical)
      LEDGER.md        ← session ledger (canonical)
      ARCHITECTURE.md  ← architecture reference

## Backward Compatibility
All lookup helpers check the canonical docs/ location first, then fall
back to the legacy root location so that existing projects continue to
work without immediate migration.

The audit system (auditor.py) WARNS when root-level copies coexist with
docs/ copies, directing users to remove the duplicate.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Canonical file names
# ---------------------------------------------------------------------------

#: Project scaffold config (renamed from scaffold.yml)
SCAFFOLD_FILE = "specsmith.yml"
#: Directory holding all governance docs
DOCS_DIR = "docs"

# Canonical relative paths (from project root)
SCAFFOLD_REL = f"{DOCS_DIR}/{SCAFFOLD_FILE}"
REQUIREMENTS_REL = f"{DOCS_DIR}/REQUIREMENTS.md"
TESTS_REL = f"{DOCS_DIR}/TESTS.md"
LEDGER_REL = f"{DOCS_DIR}/LEDGER.md"
ARCHITECTURE_REL = f"{DOCS_DIR}/ARCHITECTURE.md"

# Legacy names (kept for backward compat checks)
_LEGACY_SCAFFOLD = "scaffold.yml"
_LEGACY_REQUIREMENTS = "REQUIREMENTS.md"
_LEGACY_TESTS = "TESTS.md"
_LEGACY_LEDGER = "LEDGER.md"

#: Files that MUST NOT appear at root in a compliant project
ROOT_BANNED_FILES = [
    "REQUIREMENTS.md",
    "TESTS.md",
    "LEDGER.md",
    _LEGACY_SCAFFOLD,
]


# ---------------------------------------------------------------------------
# Lookup helpers (canonical first, legacy fallback)
# ---------------------------------------------------------------------------


def find_scaffold(root: Path) -> Path | None:
    """Find the project scaffold config file.

    Checks ``docs/specsmith.yml`` first (canonical), then ``scaffold.yml``
    at root (legacy).  Returns ``None`` if neither exists.
    """
    canonical = root / DOCS_DIR / SCAFFOLD_FILE
    if canonical.exists():
        return canonical
    legacy = root / _LEGACY_SCAFFOLD
    if legacy.exists():
        return legacy
    return None


def scaffold_path(root: Path) -> Path:
    """Return the canonical scaffold path (``docs/specsmith.yml``).

    Does **not** check whether the file exists — use ``find_scaffold``
    when you only want an existing path.
    """
    return root / DOCS_DIR / SCAFFOLD_FILE


def find_ledger(root: Path) -> Path | None:
    """Find the project ledger file.

    Checks ``docs/LEDGER.md`` first (canonical), then ``LEDGER.md``
    at root (legacy).  Returns ``None`` if neither exists.
    """
    canonical = root / LEDGER_REL
    if canonical.exists():
        return canonical
    legacy = root / _LEGACY_LEDGER
    if legacy.exists():
        return legacy
    return None


def ledger_path(root: Path) -> Path:
    """Return the canonical ledger path (``docs/LEDGER.md``)."""
    return root / LEDGER_REL


def find_requirements(root: Path) -> Path | None:
    """Find the requirements file (canonical: ``docs/REQUIREMENTS.md``)."""
    canonical = root / REQUIREMENTS_REL
    if canonical.exists():
        return canonical
    legacy = root / _LEGACY_REQUIREMENTS
    if legacy.exists():
        return legacy
    return None


def find_tests(root: Path) -> Path | None:
    """Find the test specification file (canonical: ``docs/TESTS.md``)."""
    canonical = root / TESTS_REL
    if canonical.exists():
        return canonical
    legacy = root / _LEGACY_TESTS
    if legacy.exists():
        return legacy
    return None


# ---------------------------------------------------------------------------
# Enforcement helpers
# ---------------------------------------------------------------------------


def root_violations(root: Path) -> list[str]:
    """Return a list of root-level governance files that should be in docs/.

    A file counts as a violation only when its docs/ counterpart also exists
    (meaning there are two copies) OR when docs/ doesn't exist yet and the
    file needs migration.
    """
    violations: list[str] = []
    for name in ROOT_BANNED_FILES:
        if (root / name).exists():
            violations.append(name)
    return violations
