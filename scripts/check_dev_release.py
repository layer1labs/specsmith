"""Fail CI unless a development artifact has an explicit PEP 440 dev version."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from specsmith.release_guard import require_development_version

parser = argparse.ArgumentParser()
parser.add_argument("--expected-version")
args = parser.parse_args()

text = Path("pyproject.toml").read_text(encoding="utf-8")
match = re.search(r'^version = "([^"]+)"$', text, re.MULTILINE)
if match is None:
    raise SystemExit("Could not find project version")

version = match.group(1)
try:
    require_development_version(version, args.expected_version)
except ValueError as error:
    raise SystemExit(str(error)) from error
print(f"Development release version accepted: {version}")
