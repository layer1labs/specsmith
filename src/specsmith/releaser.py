# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Releaser — automate version bumps and pre-release validation."""

from __future__ import annotations

import re
from pathlib import Path

# The 5 files that must be updated for every release
_VERSION_FILES: list[tuple[str, str]] = [
    ("pyproject.toml", r'version = "[^"]*"'),
    ("src/specsmith/__init__.py", r'__version__ = "[^"]*"'),
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


def scan_stale_refs(root: Path, current_version: str) -> list[str]:
    """Scan docs for stale version references."""
    issues: list[str] = []
    scan_dirs = [root / "docs" / "site", root]
    scan_patterns = [
        (r"--pre specsmith", "stale --pre flag"),
        (r"0\.1\.0a\d+", "alpha version reference"),
    ]

    for scan_dir in scan_dirs:
        for md_file in scan_dir.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            for pattern, desc in scan_patterns:
                if re.search(pattern, content):
                    rel = md_file.relative_to(root)
                    issues.append(f"{rel}: {desc}")

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
