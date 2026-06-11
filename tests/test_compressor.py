# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for specsmith compressor."""

from __future__ import annotations

from pathlib import Path

from specsmith.compressor import run_compress


class TestCompressSkips:
    def test_no_ledger(self, tmp_path: Path) -> None:
        result = run_compress(tmp_path)
        assert result.archived_entries == 0
        assert "not found" in result.message

    def test_below_threshold(self, tmp_path: Path) -> None:
        (tmp_path / "LEDGER.md").write_text("# Ledger\n\n## Session 1\nDone.\n", encoding="utf-8")
        result = run_compress(tmp_path)
        assert result.archived_entries == 0
        assert "No compression needed" in result.message


class TestCompressArchives:
    def test_archives_old_entries(self, tmp_path: Path) -> None:
        # Create a ledger with many entries that exceeds threshold
        lines = ["# Ledger\n\n"]
        for i in range(25):
            lines.append(f"## Session {i}\n")
            lines.extend([f"Line {j} of session {i}\n" for j in range(25)])
        (tmp_path / "LEDGER.md").write_text("".join(lines), encoding="utf-8")

        result = run_compress(tmp_path, threshold=100, keep_recent=5)
        assert result.archived_entries == 20
        assert result.remaining_entries == 5
        assert result.archive_path is not None
        assert result.archive_path.exists()

    def test_preserves_recent(self, tmp_path: Path) -> None:
        lines = ["# Ledger\n\n"]
        for i in range(15):
            lines.append(f"## Session {i}\n")
            lines.extend([f"Content {j}\n" for j in range(40)])
        (tmp_path / "LEDGER.md").write_text("".join(lines), encoding="utf-8")

        run_compress(tmp_path, threshold=100, keep_recent=5)
        ledger_text = (tmp_path / "LEDGER.md").read_text(encoding="utf-8")
        # Recent sessions should still be there
        assert "## Session 14" in ledger_text
        assert "## Session 13" in ledger_text
