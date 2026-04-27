# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for specsmith auditor."""

from __future__ import annotations

from pathlib import Path

import pytest

from specsmith.auditor import run_audit


@pytest.fixture
def governed_project(tmp_path: Path) -> Path:
    """Create a minimal governed project for audit testing."""
    (tmp_path / "AGENTS.md").write_text("# AGENTS\nShort hub.\n", encoding="utf-8")
    (tmp_path / "LEDGER.md").write_text("# Ledger\n\n## Session 1\nDone.\n", encoding="utf-8")

    gov = tmp_path / "docs" / "governance"
    gov.mkdir(parents=True)
    for f in (
        "RULES.md",
        "SESSION-PROTOCOL.md",
        "LIFECYCLE.md",
        "ROLES.md",
        "CONTEXT-BUDGET.md",
        "VERIFICATION.md",
        "DRIFT-METRICS.md",
    ):
        (gov / f).write_text(f"# {f}\nContent.\n", encoding="utf-8")

    docs = tmp_path / "docs"
    (docs / "REQUIREMENTS.md").write_text("# Reqs\n", encoding="utf-8")
    (docs / "TESTS.md").write_text("# Tests\n", encoding="utf-8")
    (docs / "ARCHITECTURE.md").write_text("# Arch\n", encoding="utf-8")
    (tmp_path / "CONTRIBUTING.md").write_text("# Contributing\n", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("MIT License\n", encoding="utf-8")

    return tmp_path


class TestAuditHealthy:
    def test_passes_on_governed_project(self, governed_project: Path) -> None:
        report = run_audit(governed_project)
        assert report.healthy
        assert report.failed == 0

    def test_reports_pass_count(self, governed_project: Path) -> None:
        report = run_audit(governed_project)
        assert report.passed > 0


class TestAuditDetectsIssues:
    def test_missing_agents_md(self, tmp_path: Path) -> None:
        (tmp_path / "LEDGER.md").write_text("# Ledger\n", encoding="utf-8")
        report = run_audit(tmp_path)
        failed_names = [r.name for r in report.results if not r.passed]
        assert "file-exists:AGENTS.md" in failed_names

    def test_missing_ledger(self, tmp_path: Path) -> None:
        (tmp_path / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        report = run_audit(tmp_path)
        failed_names = [r.name for r in report.results if not r.passed]
        assert "file-exists:LEDGER.md" in failed_names

    def test_oversized_ledger(self, governed_project: Path) -> None:
        big_ledger = "# Ledger\n" + "\n".join(f"Line {i}" for i in range(600))
        (governed_project / "LEDGER.md").write_text(big_ledger, encoding="utf-8")
        report = run_audit(governed_project)
        size_results = [r for r in report.results if r.name == "ledger-size"]
        assert len(size_results) == 1
        assert not size_results[0].passed

    def test_req_test_coverage(self, governed_project: Path) -> None:
        reqs = "# Reqs\n\nREQ-CLI-001: do things\nREQ-CLI-002: more things\n"
        tests = "# Tests\n\nTEST-CLI-001\nCovers: REQ-CLI-001\n"
        (governed_project / "docs" / "REQUIREMENTS.md").write_text(reqs, encoding="utf-8")
        (governed_project / "docs" / "TESTS.md").write_text(tests, encoding="utf-8")
        report = run_audit(governed_project)
        coverage = [r for r in report.results if r.name == "req-test-coverage"]
        assert len(coverage) == 1
        assert not coverage[0].passed
        assert "REQ-CLI-002" in coverage[0].message
