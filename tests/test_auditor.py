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
    # Scaffold config (at root for backward compat — audit now accepts either location)
    (tmp_path / "scaffold.yml").write_text(
        "name: test-project\ntype: cli-python\nspec_version: 0.10.1\nvcs_platform: github\n",
        encoding="utf-8",
    )

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


# ---------------------------------------------------------------------------
# Regression: issue #183 — letter-suffix TEST IDs in req trace
# ---------------------------------------------------------------------------


class TestReqTraceLetterSuffixRegression:
    """Regression tests for #183 — req trace misidentifies TEST-NN-002a/b.

    Root cause: _TEST_ID_PATTERN used \\d+\\b which fails to match when a
    letter immediately follows digits (\\b requires a non-word char boundary,
    but letters are word chars).  This caused current_test to remain pointing
    at the last successfully-parsed ID (TEST-NN-020), so both TEST-NN-002a and
    TEST-NN-002b coverage lines were erroneously attributed to TEST-NN-020.
    """

    def test_letter_suffix_ids_captured_from_tests_md(self, tmp_path: Path) -> None:
        """trace_reqs must return TEST-NN-002a / TEST-NN-002b, not TEST-NN-020 twice."""
        from specsmith.requirements import trace_reqs

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "REQUIREMENTS.md").write_text(
            "# Requirements\n\n## REQ-NN-001\n- **Status**: defined\n\n"
            "## REQ-NN-002\n- **Status**: defined\n",
            encoding="utf-8",
        )
        # Simulate the buggy scenario: TEST-NN-020 appears BEFORE TEST-NN-002a/b
        # so it would stick as current_test if letter suffixes aren't parsed.
        (docs / "TESTS.md").write_text(
            "# Tests\n\n"
            "## TEST-NN-020\n- **Requirement ID**: REQ-NN-001\n\n"
            "## TEST-NN-002a\n- **Requirement ID**: REQ-NN-002\n\n"
            "## TEST-NN-002b\n- **Requirement ID**: REQ-NN-002\n",
            encoding="utf-8",
        )

        traces = trace_reqs(tmp_path)
        by_req = {t["req"]: t["tests"] for t in traces}

        # REQ-NN-001 should map to TEST-NN-020 only
        assert by_req.get("REQ-NN-001") == ["TEST-NN-020"]
        # REQ-NN-002 must map to TEST-NN-002a and TEST-NN-002b — NOT TEST-NN-020 twice
        assert "TEST-NN-002a" in by_req.get("REQ-NN-002", [])
        assert "TEST-NN-002b" in by_req.get("REQ-NN-002", [])
        assert "TEST-NN-020" not in by_req.get("REQ-NN-002", [])

    def test_no_duplicate_ids_in_trace(self, tmp_path: Path) -> None:
        """REQ-NN-002 must not have duplicate entries in its test list."""
        from specsmith.requirements import trace_reqs

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "REQUIREMENTS.md").write_text(
            "# Requirements\n\n## REQ-NN-002\n- **Status**: defined\n",
            encoding="utf-8",
        )
        (docs / "TESTS.md").write_text(
            "# Tests\n\n"
            "## TEST-NN-002a\n- **Requirement ID**: REQ-NN-002\n\n"
            "## TEST-NN-002b\n- **Requirement ID**: REQ-NN-002\n",
            encoding="utf-8",
        )

        traces = trace_reqs(tmp_path)
        tests = traces[0]["tests"]
        assert len(tests) == len(set(tests)), f"Duplicate test IDs: {tests}"

    def test_yaml_mode_uses_testcases_json(self, tmp_path: Path) -> None:
        """In YAML mode, trace_reqs reads testcases.json directly (no regex)."""
        import json

        from specsmith.requirements import trace_reqs

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "REQUIREMENTS.md").write_text(
            "# Requirements\n\n## REQ-NN-002\n- **Status**: defined\n",
            encoding="utf-8",
        )
        state = tmp_path / ".specsmith"
        state.mkdir()
        (state / "testcases.json").write_text(
            json.dumps(
                [
                    {"id": "TEST-NN-002a", "requirement_id": "REQ-NN-002"},
                    {"id": "TEST-NN-002b", "requirement_id": "REQ-NN-002"},
                ]
            ),
            encoding="utf-8",
        )

        traces = trace_reqs(tmp_path)
        by_req = {t["req"]: t["tests"] for t in traces}
        assert sorted(by_req["REQ-NN-002"]) == ["TEST-NN-002a", "TEST-NN-002b"]

    def test_sync_parse_tests_md_preserves_letter_suffix(self, tmp_path: Path) -> None:
        """sync.parse_tests_md must not truncate TEST-NN-002a to TEST-NN-002."""
        from specsmith.sync import parse_tests_md

        text = (
            "## TEST-NN-002a\n"
            "- **Requirement ID**: REQ-NN-002\n\n"
            "## TEST-NN-002b\n"
            "- **Requirement ID**: REQ-NN-002\n"
        )
        records = parse_tests_md(text)
        ids = [r["id"] for r in records]
        assert "TEST-NN-002a" in ids
        assert "TEST-NN-002b" in ids
        assert "TEST-NN-002" not in ids  # must not be truncated
