"""Fail CI before a non-final package can be uploaded to stable PyPI."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

from specsmith import GOVERNANCE_VERSION
from specsmith.release_guard import require_stable_version

parser = argparse.ArgumentParser()
parser.add_argument("--expected-version")
args = parser.parse_args()

text = Path("pyproject.toml").read_text(encoding="utf-8")
match = re.search(r'^version = "([^"]+)"$', text, re.MULTILINE)
if match is None:
    raise SystemExit("Could not find project version")
version = match.group(1)
try:
    require_stable_version(version, args.expected_version)
except ValueError as error:
    raise SystemExit(str(error)) from error
metadata = yaml.safe_load(Path("docs/SPECSMITH.yml").read_text(encoding="utf-8")) or {}
if metadata.get("version") != version:
    raise SystemExit(
        "Package metadata mismatch: pyproject.toml version "
        f"{version!r} != docs/SPECSMITH.yml version {metadata.get('version')!r}"
    )
if metadata.get("spec_version") != GOVERNANCE_VERSION:
    raise SystemExit(
        "Governance metadata mismatch: candidate governance version "
        f"{GOVERNANCE_VERSION!r} != docs/SPECSMITH.yml spec_version "
        f"{metadata.get('spec_version')!r}"
    )
print(f"Stable release version accepted: {version}")
