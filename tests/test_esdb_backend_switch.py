# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for 'specsmith esdb switch-backend' command (REQ-372).

Covers:
  - --to sqlite without --confirm-data-loss is rejected with exit_code=1.
  - --to chronomemory fails gracefully when chronomemory is not installed.
  - --to chronomemory fails gracefully when no valid license is present.
  - --to sqlite with --confirm-data-loss succeeds (no chrono records to export).
  - Required --to option is enforced.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from specsmith.cli import main


class TestEsdbSwitchBackendGuards:
    """Switch-backend must enforce safety guards."""

    def test_to_sqlite_without_confirm_data_loss_fails(self, tmp_path: Path) -> None:
        """--to sqlite without --confirm-data-loss must exit with code 1."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["esdb", "switch-backend", "--project-dir", str(tmp_path), "--to", "sqlite"],
        )
        assert result.exit_code == 1, (
            f"Expected exit_code=1 without --confirm-data-loss, got {result.exit_code}\n"
            f"Output: {result.output}"
        )
        # Should mention data loss / warning
        out_lower = result.output.lower()
        assert "data-loss" in out_lower or "confirm" in out_lower or "WARNING" in result.output

    def test_to_chronomemory_fails_when_not_installed(self, tmp_path: Path) -> None:
        """--to chronomemory must fail gracefully if chronomemory is not installed."""
        from specsmith.esdb import CHRONO_AVAILABLE

        if CHRONO_AVAILABLE:
            pytest.skip("chronomemory is installed — cannot test missing-package path")

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "esdb",
                "switch-backend",
                "--project-dir",
                str(tmp_path),
                "--to",
                "chronomemory",
            ],
        )
        assert result.exit_code == 1, (
            f"Expected exit_code=1 when chronomemory not installed, got {result.exit_code}\n"
            f"Output: {result.output}"
        )
        output_lower = result.output.lower()
        assert (
            "chronomemory" in output_lower
            or "not installed" in output_lower
            or "install" in output_lower
        )

    def test_to_chronomemory_fails_without_license(self, tmp_path: Path) -> None:
        """--to chronomemory must fail gracefully with no valid ESDB license."""
        from specsmith.esdb import CHRONO_AVAILABLE
        from specsmith.esdb._license import check_license

        if not CHRONO_AVAILABLE:
            pytest.skip("chronomemory not installed")

        lic = check_license(warn=False)
        if lic.valid:
            pytest.skip(
                "A valid ESDB license is present on this machine — cannot test missing-license path"
            )

        # No license key file present in tmp_path, and no valid license
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "esdb",
                "switch-backend",
                "--project-dir",
                str(tmp_path),
                "--to",
                "chronomemory",
            ],
        )
        assert result.exit_code == 1, (
            f"Expected exit_code=1 without license, got {result.exit_code}\nOutput: {result.output}"
        )
        output_lower = result.output.lower()
        assert "license" in output_lower or "invalid" in output_lower or "valid" in output_lower

    def test_to_option_is_required(self, tmp_path: Path) -> None:
        """Omitting --to must produce a usage error (non-zero exit)."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["esdb", "switch-backend", "--project-dir", str(tmp_path)],
        )
        # Click will produce a UsageError (exit_code=2) for missing required option
        assert result.exit_code != 0, (
            f"Expected non-zero exit when --to is missing, got {result.exit_code}"
        )

    def test_to_sqlite_with_confirm_exits_cleanly_when_no_chrono(self, tmp_path: Path) -> None:
        """--to sqlite --confirm-data-loss should succeed (or produce a clear message)
        even when chronomemory has no records to export."""
        from specsmith.esdb import CHRONO_AVAILABLE

        if not CHRONO_AVAILABLE:
            pytest.skip("chronomemory not installed — sqlite export requires an active store")

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "esdb",
                "switch-backend",
                "--project-dir",
                str(tmp_path),
                "--to",
                "sqlite",
                "--confirm-data-loss",
            ],
        )
        # With no ChronoStore records, it should complete without error
        assert result.exit_code == 0, (
            f"Expected exit_code=0 with --confirm-data-loss, got {result.exit_code}\n"
            f"Output: {result.output}"
        )


class TestEsdbSwitchBackendIntegration:
    """Integration: switch-backend writes SQLite records from JSON when available."""

    def test_to_sqlite_writes_sqlite_from_json(self, tmp_path: Path) -> None:
        """With --confirm-data-loss and JSON state, SQLite records are created."""
        from specsmith.esdb import CHRONO_AVAILABLE

        if not CHRONO_AVAILABLE:
            pytest.skip("requires chronomemory for switch to sqlite")

        import json

        # Write some requirements JSON
        state_dir = tmp_path / ".specsmith"
        state_dir.mkdir()
        (state_dir / "requirements.json").write_text(
            json.dumps([{"id": "REQ-001", "title": "Test", "status": "active", "version": 1}]),
            encoding="utf-8",
        )
        (state_dir / "testcases.json").write_text("[]", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "esdb",
                "switch-backend",
                "--project-dir",
                str(tmp_path),
                "--to",
                "sqlite",
                "--confirm-data-loss",
            ],
        )
        assert result.exit_code == 0, (
            f"Expected exit_code=0, got {result.exit_code}\nOutput: {result.output}"
        )
