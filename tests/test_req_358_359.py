# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for REQ-358 (_req_count H2 support) and REQ-359 (sync YAML-mode MD fallback)."""

from __future__ import annotations

import json
from pathlib import Path


# ── REQ-359 / TEST-359: _req_count H2 heading support ─────────────────────────


class TestReqCountH2:
    """_req_count should match ## REQ-XX-NNN (H2) headings, not just ### (H3)."""

    def test_req_count_h2_headings(self, tmp_path: Path) -> None:
        from specsmith.phase import _req_count

        docs = tmp_path / "docs"
        docs.mkdir()
        lines = [f"## REQ-BE-{i:03d}: Requirement {i}" for i in range(1, 6)]
        (docs / "REQUIREMENTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

        assert _req_count(5)(tmp_path) is True
        assert _req_count(6)(tmp_path) is False  # strict boundary

    def test_req_count_h3_still_works(self, tmp_path: Path) -> None:
        from specsmith.phase import _req_count

        docs = tmp_path / "docs"
        docs.mkdir()
        lines = [f"### REQ-{i:03d}: Requirement {i}" for i in range(1, 4)]
        (docs / "REQUIREMENTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

        assert _req_count(3)(tmp_path) is True
        assert _req_count(4)(tmp_path) is False

    def test_req_count_mixed_h2_h3(self, tmp_path: Path) -> None:
        from specsmith.phase import _req_count

        docs = tmp_path / "docs"
        docs.mkdir()
        content = (
            "## REQ-BE-001: First\n"
            "### REQ-BE-002: Second\n"
            "## REQ-BE-003: Third\n"
        )
        (docs / "REQUIREMENTS.md").write_text(content, encoding="utf-8")

        assert _req_count(3)(tmp_path) is True
        assert _req_count(4)(tmp_path) is False


# ── REQ-358 / TEST-358: sync YAML-mode Markdown fallback ──────────────────────


class TestSyncYamlModeMarkdownFallback:
    """run_sync in YAML mode should fall back to REQUIREMENTS.md parsing
    when no YAML requirement files exist but REQUIREMENTS.md has content."""

    def test_sync_yaml_mode_markdown_fallback(self, tmp_path: Path) -> None:
        from specsmith.sync import run_sync

        # Set up YAML mode
        state_dir = tmp_path / ".specsmith"
        state_dir.mkdir()
        (state_dir / "governance-mode").write_text("yaml", encoding="utf-8")

        # Create REQUIREMENTS.md with H2 headings (no YAML files)
        docs = tmp_path / "docs"
        docs.mkdir()
        lines = [f"## REQ-BE-{i:03d}: Backend requirement {i}" for i in range(1, 7)]
        (docs / "REQUIREMENTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

        # No docs/requirements/ directory — forces fallback

        result = run_sync(tmp_path)

        assert result.reqs_after >= 6
        reqs_json = state_dir / "requirements.json"
        assert reqs_json.exists()
        data = json.loads(reqs_json.read_text(encoding="utf-8"))
        assert len(data) == 6

    def test_sync_yaml_mode_no_fallback_when_yaml_exists(self, tmp_path: Path) -> None:
        """When YAML files exist, no fallback should occur."""
        from specsmith.sync import run_sync

        state_dir = tmp_path / ".specsmith"
        state_dir.mkdir()
        (state_dir / "governance-mode").write_text("yaml", encoding="utf-8")

        docs = tmp_path / "docs"
        docs.mkdir()
        req_dir = docs / "requirements"
        req_dir.mkdir()
        (req_dir / "core.yml").write_text(
            "- id: REQ-001\n  title: First\n  status: defined\n",
            encoding="utf-8",
        )

        result = run_sync(tmp_path)

        # Should use YAML source, not fallback
        assert result.reqs_after == 1
