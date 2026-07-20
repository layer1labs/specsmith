# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Regression coverage for documentation build artifacts."""

from pathlib import Path


def test_mkdocs_site_output_is_ignored_for_projects_and_scaffolds() -> None:
    """Documentation builds must not leave a governed worktree dirty."""
    root = Path(__file__).parents[1]
    project_lines = (root / ".gitignore").read_text(encoding="utf-8").splitlines()
    template_lines = (
        (root / "src" / "specsmith" / "templates" / "gitignore.j2")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert "/site/" in project_lines
    assert "/site/" in template_lines


def test_public_rtd_links_use_translation_free_routes() -> None:
    """Published links must match the project's active RTD versioning scheme."""
    root = Path(__file__).parents[1]
    candidates = [root / "README.md"]
    candidates.extend((root / "docs" / "site").rglob("*.md"))
    candidates.extend((root / "src" / "specsmith").rglob("*.py"))
    candidates.extend((root / "src" / "specsmith").rglob("*.j2"))

    obsolete = "specsmith.readthedocs.io/en/"
    offenders = [
        str(path.relative_to(root))
        for path in candidates
        if obsolete in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
