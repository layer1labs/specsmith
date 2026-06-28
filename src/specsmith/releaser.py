# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Releaser — automate version bumps and pre-release validation."""

from __future__ import annotations

import re
from pathlib import Path

# The 5 files that must be updated for every release
_VERSION_FILES: list[tuple[str, str]] = [
    ("pyproject.toml", r'version = "[^"]*"'),
    ("src/specsmith/__init__.py", r'__version__ = "[^"]*"'),  # fallback value
    ("src/specsmith/config.py", r'default="[^"]*", description="Spec version'),
    ("tests/test_smoke.py", r'__version__ == "[^"]*"'),
    ("tests/test_cli.py", r'"[0-9]+\.[0-9]+\.[0-9]+[^"]*" in result\.output'),
]


def bump_version(root: Path, new_version: str) -> list[str]:
    """Bump version in all 5 locations. Returns list of updated files."""
    updated: list[str] = []

    # 1. pyproject.toml
    _replace_in_file(
        root / "pyproject.toml",
        r'version = "[^"]*"',
        f'version = "{new_version}"',
    )
    updated.append("pyproject.toml")

    # 2. __init__.py
    _replace_in_file(
        root / "src/specsmith/__init__.py",
        r'__version__ = "[^"]*"',
        f'__version__ = "{new_version}"',
    )
    updated.append("src/specsmith/__init__.py")

    # 3. config.py spec_version default
    _replace_in_file(
        root / "src/specsmith/config.py",
        r'default="[^"]*", description="Spec version to scaffold from"',
        f'default="{new_version}", description="Spec version to scaffold from"',
    )
    updated.append("src/specsmith/config.py")

    # 4. test_smoke.py
    _replace_in_file(
        root / "tests/test_smoke.py",
        r'__version__ == "[^"]*"',
        f'__version__ == "{new_version}"',
    )
    updated.append("tests/test_smoke.py")

    # 5. test_cli.py — version output assertion
    _replace_in_file(
        root / "tests/test_cli.py",
        r'"[0-9]+\.[0-9]+\.[0-9]+[a-z0-9]*" in result\.output',
        f'"{new_version}" in result.output',
    )
    updated.append("tests/test_cli.py")

    # 6. test_cli.py — upgrade test version
    _replace_in_file(
        root / "tests/test_cli.py",
        r'--spec-version", "[0-9]+\.[0-9]+\.[0-9]+[a-z0-9]*"',
        f'--spec-version", "{new_version}"',
    )

    return updated


# Context tokens that mark a *legitimate* "--pre specsmith" reference rather
# than a stale stable-install instruction. The dev/pre-release channel is a
# supported feature (see channel.py and docs/site/releasing.md), so docs that
# describe it -- and explicit prohibitions ("NEVER run pip install --pre
# specsmith") -- must not be flagged. Only a reference that recommends
# installing the *stable* package with the pre-release flag is stale.
_PRE_OK_CONTEXT: tuple[str, ...] = ("dev", "pre-release", "prerelease", "never", "badge")


def _has_stale_pre_flag(content: str) -> bool:
    """Return True if *content* has a stale ``--pre specsmith`` install hint.

    The scan is line-aware and tracks the nearest Markdown heading so a
    legitimate ``--pre specsmith`` reference inside a dev/pre-release section or
    a prohibition line is ignored. An occurrence is only treated as stale when
    neither its line nor the enclosing section carries a :data:`_PRE_OK_CONTEXT`
    token.
    """
    current_heading = ""
    for line in content.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            current_heading = stripped
        if "--pre specsmith" not in line:
            continue
        context = f"{line} {current_heading}".lower()
        if any(token in context for token in _PRE_OK_CONTEXT):
            continue
        return True
    return False


def scan_stale_refs(root: Path, current_version: str) -> list[str]:
    """Scan docs for stale version references.

    The ``--pre specsmith`` check is context-aware (see
    :func:`_has_stale_pre_flag`) so the supported dev/pre-release channel docs
    and prohibitions do not produce false positives; only stale *stable*-install
    hints are reported.
    """
    issues: list[str] = []
    scan_dirs = [root / "docs" / "site", root]

    for scan_dir in scan_dirs:
        for md_file in scan_dir.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            rel = md_file.relative_to(root)
            if _has_stale_pre_flag(content):
                issues.append(f"{rel}: stale --pre flag")
            if re.search(r"0\.1\.0a\d+", content):
                issues.append(f"{rel}: alpha version reference")

    # Check classifier
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        if "3 - Alpha" in content:
            issues.append("pyproject.toml: classifier still says Alpha")

    return issues


def _replace_in_file(path: Path, pattern: str, replacement: str) -> None:
    """Replace first match of pattern in file."""
    if not path.exists():
        return
    content = path.read_text(encoding="utf-8")
    new_content = re.sub(pattern, replacement, content, count=1)
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
