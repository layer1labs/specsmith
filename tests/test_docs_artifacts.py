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
