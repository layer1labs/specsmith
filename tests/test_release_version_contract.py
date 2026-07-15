# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Release-version contract checks for published SpecSmith artifacts."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _quoted_value(path: Path, pattern: str) -> str:
    match = re.search(pattern, path.read_text(encoding="utf-8"), re.MULTILINE)
    assert match, f"missing release version in {path}"
    return match.group(1)


def test_release_metadata_and_embedded_schema_versions_agree() -> None:
    """TEST-476: a wheel cannot advertise a different project schema version."""
    release_version = _quoted_value(ROOT / "pyproject.toml", r'^version\s*=\s*"([^"]+)"$')
    fallback_version = _quoted_value(
        ROOT / "src" / "specsmith" / "__init__.py",
        r'__version__\s*=\s*"([^"]+)"\s+# fallback',
    )
    schema_version = _quoted_value(
        ROOT / "src" / "specsmith" / "config.py",
        r'spec_version:\s*str\s*=\s*Field\(default="([^"]+)"',
    )
    project_schema = yaml.safe_load((ROOT / "docs" / "SPECSMITH.yml").read_text(encoding="utf-8"))

    assert fallback_version == release_version
    assert schema_version == release_version
    assert project_schema["version"] == release_version
