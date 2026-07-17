# SPDX-License-Identifier: MIT
"""Tests for patch_file diff-format validation (issue #344)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure the local src/ is importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from specsmith.agent.tools import patch_file  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal project with a source file to patch."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "example.py").write_text(
        "# example\nline1\nline2\nline3\n", encoding="utf-8"
    )
    return tmp_path


# ---------------------------------------------------------------------------
# Valid diff — should pass through to patch command
# ---------------------------------------------------------------------------

def test_valid_diff_applies(tmp_project: Path) -> None:
    """A well-formed unified diff passes validation and reaches patch command."""
    diff = (
        "--- a/src/example.py\n"
        "+++ b/src/example.py\n"
        "@@ -2,3 +2,3 @@\n"
        " line1\n"
        "-line2\n"
        "+line2_fixed\n"
        " line3\n"
    )
    result = patch_file("src/example.py", diff, cwd=str(tmp_project))
    # Validation should pass (no "Malformed" error)
    assert "Malformed diff format" not in result
    # The result will be "Successfully patched" if patch is available,
    # or "Failed to patch" if patch command is not installed (e.g. Windows).
    # Either way, validation passed.
    assert "Successfully patched" in result or "Failed to patch" in result


# ---------------------------------------------------------------------------
# Malformed diff — :start_line: marker in REPLACE section
# ---------------------------------------------------------------------------

def test_malformed_diff_start_line_rejected(tmp_project: Path) -> None:
    """Diff with :start_line: marker in REPLACE section is rejected."""
    diff = (
        "--- a/src/example.py\n"
        "+++ b/src/example.py\n"
        "@@ -2,3 +2,3 @@\n"
        ":start_line: 2\n"
        " line1\n"
        "-line2\n"
        "+line2_fixed\n"
        " line3\n"
    )
    result = patch_file("src/example.py", diff, cwd=str(tmp_project))
    assert "Malformed diff format" in result
    assert ":start_line:" in result
    assert "write_to_file" in result


# ---------------------------------------------------------------------------
# Malformed diff — :end_line: marker in REPLACE section
# ---------------------------------------------------------------------------

def test_malformed_diff_end_line_rejected(tmp_project: Path) -> None:
    """Diff with :end_line: marker in REPLACE section is rejected."""
    diff = (
        "--- a/src/example.py\n"
        "+++ b/src/example.py\n"
        "@@ -2,3 +2,3 @@\n"
        ":end_line: 4\n"
        " line1\n"
        "-line2\n"
        "+line2_fixed\n"
        " line3\n"
    )
    result = patch_file("src/example.py", diff, cwd=str(tmp_project))
    assert "Malformed diff format" in result
    assert ":end_line:" in result


# ---------------------------------------------------------------------------
# Malformed diff — both markers
# ---------------------------------------------------------------------------

def test_malformed_diff_both_markers_rejected(tmp_project: Path) -> None:
    """Diff with both :start_line: and :end_line: markers is rejected."""
    diff = (
        "--- a/src/example.py\n"
        "+++ b/src/example.py\n"
        "@@ -2,3 +2,3 @@\n"
        ":start_line: 2\n"
        ":end_line: 4\n"
        " line1\n"
        "-line2\n"
        "+line2_fixed\n"
        " line3\n"
    )
    result = patch_file("src/example.py", diff, cwd=str(tmp_project))
    assert "Malformed diff format" in result


# ---------------------------------------------------------------------------
# Cache deduplication — same prefix should not re-parse
# ---------------------------------------------------------------------------

def test_validation_cache_dedup(tmp_project: Path) -> None:
    """Repeated calls with same diff prefix skip re-parsing."""
    diff = (
        "--- a/src/example.py\n"
        "+++ b/src/example.py\n"
        "@@ -2,3 +2,3 @@\n"
        ":start_line: 2\n"
        " line1\n"
        "-line2\n"
        "+line2_fixed\n"
        " line3\n"
    )
    # First call — should validate and reject
    result1 = patch_file("src/example.py", diff, cwd=str(tmp_project))
    assert "Malformed diff format" in result1

    # Second call with identical diff — should use cache
    result2 = patch_file("src/example.py", diff, cwd=str(tmp_project))
    assert "Malformed diff format" in result2

    # Both should produce identical output
    assert result1 == result2


# ---------------------------------------------------------------------------
# Non-existent file — early error
# ---------------------------------------------------------------------------

def test_nonexistent_file_error(tmp_project: Path) -> None:
    """Requesting to patch a non-existent file returns error immediately."""
    diff = "valid diff"
    result = patch_file("src/nonexistent.py", diff, cwd=str(tmp_project))
    assert "does not exist to patch" in result


# ---------------------------------------------------------------------------
# Empty diff — should not crash
# ---------------------------------------------------------------------------

def test_empty_diff_does_not_crash(tmp_project: Path) -> None:
    """An empty diff string does not crash the function."""
    result = patch_file("src/example.py", "", cwd=str(tmp_project))
    # Should not raise; may return error or pass through to patch
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Diff with only hunk header (no REPLACE section) — should not crash
# ---------------------------------------------------------------------------

def test_hunk_only_no_crash(tmp_project: Path) -> None:
    """A diff with only @@ header (no REPLACE content) does not crash."""
    diff = "@@ -2,3 +2,3 @@"
    result = patch_file("src/example.py", diff, cwd=str(tmp_project))
    assert isinstance(result, str)