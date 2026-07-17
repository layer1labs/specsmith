# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for the release-tooling stale-reference scanner (REQ-050).

These cover the context-aware ``--pre specsmith`` check so the supported
dev/pre-release channel docs and explicit prohibitions are not reported as
stale, while genuine stable-install hints still are.

Traceability:
    __trace_id__ = "REQ-050"  — all tests in this module verify REQ-050.
"""

from __future__ import annotations

# Traceability marker: all tests in this module verify REQ-050
__trace_id__ = "REQ-050"

from pathlib import Path

from specsmith.releaser import _has_stale_pre_flag, scan_stale_refs


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --- REQ-050: Stale-reference scanner tests ---

def test_dev_channel_pre_reference_not_flagged(tmp_path: Path) -> None:
    """TEST-050-01: A dev-docs note mapping dev docs to the pre-release install is legitimate."""
    _write(
        tmp_path / "docs" / "site" / "index.md",
        "# Docs\n\n**Dev (latest):** matches `pip install --pre specsmith`\n",
    )
    assert scan_stale_refs(tmp_path, "0.18.0") == []


def test_dev_release_section_pre_reference_not_flagged(tmp_path: Path) -> None:
    """TEST-050-02: An install hint under a 'Dev Releases' heading is legitimate dev-channel docs."""
    _write(
        tmp_path / "docs" / "site" / "releasing.md",
        "## Dev Releases (develop branch)\n\nInstall: `pip install --pre specsmith`\n",
    )
    assert scan_stale_refs(tmp_path, "0.18.0") == []


def test_prohibition_pre_reference_not_flagged(tmp_path: Path) -> None:
    """TEST-050-03: A prohibition must not be read as a stale install hint."""
    _write(
        tmp_path / "AGENTS.md",
        "## Install policy\n\n- NEVER run `pip install --pre specsmith` in any environment.\n",
    )
    assert scan_stale_refs(tmp_path, "0.18.0") == []


def test_stale_stable_install_hint_is_flagged(tmp_path: Path) -> None:
    """TEST-050-04: Recommending --pre for a normal install under a neutral heading is stale."""
    _write(
        tmp_path / "docs" / "site" / "getting-started.md",
        "## Quick Start\n\nInstall specsmith: `pip install --pre specsmith`\n",
    )
    rel = Path("docs") / "site" / "getting-started.md"
    assert scan_stale_refs(tmp_path, "0.18.0") == [f"{rel}: stale --pre flag"]


def test_alpha_version_reference_flagged(tmp_path: Path) -> None:
    """TEST-050-05: The narrow 0.1.0aN alpha pattern is still reported."""
    _write(tmp_path / "README.md", "# x\n\nsee 0.1.0a3 builds\n")
    assert scan_stale_refs(tmp_path, "0.18.0") == ["README.md: alpha version reference"]


def test_alpha_classifier_flagged(tmp_path: Path) -> None:
    """TEST-050-06: A '3 - Alpha' classifier in pyproject.toml is still reported."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nclassifiers = ["Development Status :: 3 - Alpha"]\n',
        encoding="utf-8",
    )
    assert "pyproject.toml: classifier still says Alpha" in scan_stale_refs(tmp_path, "0.18.0")


def test_clean_docs_no_issues(tmp_path: Path) -> None:
    """TEST-050-07: Stable install instructions and a non-alpha classifier produce no issues."""
    _write(tmp_path / "docs" / "site" / "index.md", "# Docs\n\n`pip install specsmith`\n")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nclassifiers = ["Development Status :: 5 - Production/Stable"]\n',
        encoding="utf-8",
    )
    assert scan_stale_refs(tmp_path, "0.18.0") == []


def test_has_stale_pre_flag_unit() -> None:
    """TEST-050-08: Direct checks of the line+heading-aware helper."""
    # Neutral install hint with no qualifying context -> stale.
    assert _has_stale_pre_flag("Install: `pip install --pre specsmith`") is True
    # Heading context marks the section as dev -> legitimate.
    assert _has_stale_pre_flag("## Dev Releases\nrun `pip install --pre specsmith`") is False
    # Prohibition -> legitimate.
    assert _has_stale_pre_flag("NEVER `pip install --pre specsmith`") is False
    # No pre-release flag at all.
    assert _has_stale_pre_flag("`pip install specsmith`") is False