# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Release-version contract checks for published SpecSmith artifacts.

Traceability:
    __trace_id__ = "TEST-476"  — verifies release metadata consistency.
"""

from __future__ import annotations

# Traceability marker: all tests in this module verify TEST-476
__trace_id__ = "TEST-476"

import re
from pathlib import Path

import yaml

from specsmith._config_schema import _normalize_scaffold_raw

ROOT = Path(__file__).resolve().parents[1]


def _quoted_value(path: Path, pattern: str) -> str:
    match = re.search(pattern, path.read_text(encoding="utf-8"), re.MULTILINE)
    assert match, f"missing release version in {path}"
    return match.group(1)


# --- TEST-476: Release metadata consistency ---


def test_release_metadata_and_embedded_schema_versions_agree() -> None:
    """TEST-476: a wheel cannot advertise a different project schema version."""
    release_version = _quoted_value(ROOT / "pyproject.toml", r'^version\s*=\s*"([^"]+)"$')
    fallback_version = _quoted_value(
        ROOT / "src" / "specsmith" / "__init__.py",
        r'__version__\s*=\s*"([^"]+)"\s+# fallback',
    )
    # GOVERNANCE_VERSION is the single source of truth for schema version (Fix #319)
    governance_version = _quoted_value(
        ROOT / "src" / "specsmith" / "__init__.py",
        r'GOVERNANCE_VERSION(?::\s*str)?\s*=\s*"([^"]+)"',
    )
    project_schema = yaml.safe_load((ROOT / "docs" / "SPECSMITH.yml").read_text(encoding="utf-8"))

    assert fallback_version == release_version
    assert governance_version == release_version
    assert project_schema["version"] == release_version
    assert project_schema["spec_version"] == governance_version


def test_legacy_self_project_version_normalizes_without_losing_package_version() -> None:
    legacy = {"name": "specsmith", "version": "0.21.0"}

    normalized = _normalize_scaffold_raw(legacy)

    assert normalized["version"] == "0.21.0"
    assert normalized["spec_version"] == "0.21.0"


def test_non_self_project_version_is_not_reinterpreted_as_governance_version() -> None:
    project = {"name": "consumer", "version": "9.0.0"}

    normalized = _normalize_scaffold_raw(project)

    assert normalized == project


def test_legacy_self_project_metadata_drives_forward_migration_detection(
    tmp_path: Path, monkeypatch
) -> None:
    from specsmith import updater

    metadata_path = tmp_path / "docs" / "SPECSMITH.yml"
    metadata_path.parent.mkdir()
    metadata_path.write_text("name: specsmith\nversion: 0.21.0\n", encoding="utf-8")
    monkeypatch.setattr(updater, "GOVERNANCE_VERSION", "0.22.5")

    project_version, candidate_version = updater.check_project_version(tmp_path)

    assert (project_version, candidate_version) == ("0.21.0", "0.22.5")
    assert updater.needs_migration(tmp_path)
