# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for specsmith auditor."""

from __future__ import annotations

from pathlib import Path

import pytest

from specsmith.auditor import check_industrial_artifacts, run_audit


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


def test_industrial_artifacts_normalizes_windows_declared_paths(tmp_path: Path) -> None:
    # Simulate a Windows user who put a single backslash path in scaffold.yml.
    # YAML plain scalars treat backslash as literal, so the parsed value is
    # "hardware\device.eds" (one backslash) which must normalise to the posix
    # found path "hardware/device.eds".
    (tmp_path / "scaffold.yml").write_text(
        "name: test\n"
        "type: cli-python\n"
        "industrial_artifacts:\n"
        "  canopen_eds:\n"
        "    - path: hardware\\device.eds\n",
        encoding="utf-8",
    )
    (tmp_path / "hardware").mkdir()
    (tmp_path / "hardware" / "device.eds").write_text("EDS CONTENT", encoding="utf-8")

    results = check_industrial_artifacts(tmp_path)
    assert results
    assert any(r.name == "industrial-artifacts" and r.passed for r in results)


def test_industrial_artifacts_plain_string_entries_no_false_positive(tmp_path: Path) -> None:
    """Regression test for #257: plain string canopen_eds entries must not be
    treated as undeclared even though they pass isinstance(e, dict) == False."""
    (tmp_path / "scaffold.yml").write_text(
        "name: test\n"
        "type: cli-python\n"
        "industrial_artifacts:\n"
        "  canopen_eds:\n"
        "    - application/canopen/device.eds\n"
        "    - application/canopen/device.xdd\n",
        encoding="utf-8",
    )
    can_dir = tmp_path / "application" / "canopen"
    can_dir.mkdir(parents=True)
    (can_dir / "device.eds").write_text("EDS", encoding="utf-8")
    (can_dir / "device.xdd").write_text("XDD", encoding="utf-8")

    results = check_industrial_artifacts(tmp_path)
    assert results
    assert any(r.name == "industrial-artifacts" and r.passed for r in results), (
        f"Expected pass but got: {[r.message for r in results]}"
    )


def test_industrial_artifacts_mixed_string_and_dict_entries(tmp_path: Path) -> None:
    """Mixed plain-string and dict entries should both be recognised (#257)."""
    (tmp_path / "scaffold.yml").write_text(
        "name: test\n"
        "type: cli-python\n"
        "industrial_artifacts:\n"
        "  canopen_eds:\n"
        "    - application/canopen/a.eds\n"
        "    - path: application/canopen/b.eds\n"
        "      device: MyDevice\n",
        encoding="utf-8",
    )
    can_dir = tmp_path / "application" / "canopen"
    can_dir.mkdir(parents=True)
    (can_dir / "a.eds").write_text("EDS", encoding="utf-8")
    (can_dir / "b.eds").write_text("EDS", encoding="utf-8")

    results = check_industrial_artifacts(tmp_path)
    assert any(r.name == "industrial-artifacts" and r.passed for r in results)


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


# ---------------------------------------------------------------------------
# REQ-357: accepted_warnings suppression
# ---------------------------------------------------------------------------


class TestAcceptedWarningsSuppression:
    """Tests for REQ-357 — accepted_warnings suppression in auditor."""

    def test_accepted_warnings_suppresses_type_mismatch(self, tmp_path: Path) -> None:
        """scaffold_type_mismatch alias should suppress the type-mismatch check."""
        # Set up a minimal project with a type that will mismatch detection
        (tmp_path / "AGENTS.md").write_text("# AGENTS\nShort.\n", encoding="utf-8")
        (tmp_path / "LEDGER.md").write_text("# Ledger\nDone.\n", encoding="utf-8")
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "TESTS.md").write_text("# Tests\n", encoding="utf-8")
        # Use a type that differs from what detect_project will infer.
        # "backend-frontend" is unlikely to match a near-empty tmp project.
        (tmp_path / "scaffold.yml").write_text(
            "name: test\n"
            "type: backend-frontend\n"
            "spec_version: 0.10.1\n"
            "vcs_platform: github\n"
            "accepted_warnings:\n"
            "  - scaffold_type_mismatch\n",
            encoding="utf-8",
        )

        report = run_audit(tmp_path)

        # Find the type-mismatch result
        tm_results = [r for r in report.results if r.name == "type-mismatch"]
        if tm_results:
            assert tm_results[0].suppressed is True
            assert tm_results[0].passed is True
        # The suppressed result must not count as a failure
        type_mismatch_failures = [
            r for r in report.results if r.name == "type-mismatch" and not r.passed
        ]
        assert len(type_mismatch_failures) == 0

    def test_ledger_line_threshold_suppresses_ledger_size(self, tmp_path: Path) -> None:
        """ledger_line_threshold alias should suppress ledger-size check."""
        (tmp_path / "AGENTS.md").write_text("# AGENTS\nShort.\n", encoding="utf-8")
        big_ledger = "# Ledger\n" + "\n".join(f"Line {i}" for i in range(600))
        (tmp_path / "LEDGER.md").write_text(big_ledger, encoding="utf-8")
        (tmp_path / "scaffold.yml").write_text(
            "name: test\n"
            "type: cli-python\n"
            "spec_version: 0.10.1\n"
            "vcs_platform: github\n"
            "accepted_warnings:\n"
            "  - ledger_line_threshold\n",
            encoding="utf-8",
        )

        report = run_audit(tmp_path)

        size_results = [r for r in report.results if r.name == "ledger-size"]
        assert len(size_results) == 1
        assert size_results[0].suppressed is True
        assert size_results[0].passed is True
        # Should not count toward failures
        assert all(r.passed or r.name != "ledger-size" for r in report.results)

    def test_audit_suppressions_backward_compat(self, tmp_path: Path) -> None:
        """Old audit_suppressions: [ledger_size] field should still suppress ledger-size."""
        (tmp_path / "AGENTS.md").write_text("# AGENTS\nShort.\n", encoding="utf-8")
        big_ledger = "# Ledger\n" + "\n".join(f"Line {i}" for i in range(600))
        (tmp_path / "LEDGER.md").write_text(big_ledger, encoding="utf-8")
        (tmp_path / "scaffold.yml").write_text(
            "name: test\n"
            "type: cli-python\n"
            "spec_version: 0.10.1\n"
            "vcs_platform: github\n"
            "audit_suppressions:\n"
            "  - ledger_size\n",
            encoding="utf-8",
        )

        report = run_audit(tmp_path)

        size_results = [r for r in report.results if r.name == "ledger-size"]
        assert len(size_results) == 1
        assert size_results[0].suppressed is True
        assert size_results[0].passed is True

    def test_suppressed_count_property(self, tmp_path: Path) -> None:
        """AuditReport.suppressed_count should reflect the number of suppressed results."""
        from specsmith.auditor import AuditReport, AuditResult, _apply_accepted_warnings

        report = AuditReport(
            results=[
                AuditResult(name="ledger-size", passed=False, message="too big", fixable=True),
                AuditResult(name="type-mismatch", passed=False, message="mismatch"),
                AuditResult(name="other-check", passed=True, message="ok"),
            ]
        )
        _apply_accepted_warnings(report, ["ledger_line_threshold", "scaffold_type_mismatch"])

        assert report.suppressed_count == 2
        assert report.failed == 0
        assert report.healthy is True


# ---------------------------------------------------------------------------
# Regression: issue #195 — LEDGER open-TODO counter false positive
# ---------------------------------------------------------------------------


class TestLedgerTodoCounterRegression:
    """Regression tests for #195 — prose '- [ ]' strings must not be counted."""

    def test_prose_todo_reference_not_counted(self, tmp_path: Path) -> None:
        """A narrative Checks run: line referencing '- [ ]' must not add open TODOs."""
        from specsmith.auditor import check_ledger_health

        ledger = (
            "# Ledger\n\n"
            "## Session 2026-05-30\n"
            "### Checks run:\n"
            "- TODO closure: all 109 - [ ] items changed to - [x] (batch, 2026-05-30)\n"
        )
        (tmp_path / "LEDGER.md").write_text(ledger, encoding="utf-8")
        results = check_ledger_health(tmp_path)
        todo_result = next(r for r in results if r.name == "ledger-open-todos")
        assert todo_result.passed
        assert "0 open" in todo_result.message

    def test_real_open_todo_is_counted(self, tmp_path: Path) -> None:
        """A genuine checklist item starting with '- [ ]' must still be counted."""
        from specsmith.auditor import check_ledger_health

        ledger = "# Ledger\n\n" + "\n".join(f"- [ ] item {i}" for i in range(25))
        (tmp_path / "LEDGER.md").write_text(ledger, encoding="utf-8")
        results = check_ledger_health(tmp_path)
        todo_result = next(r for r in results if r.name == "ledger-open-todos")
        assert not todo_result.passed
        assert "25 open" in todo_result.message


# ---------------------------------------------------------------------------
# Regression: issue #194 — check_type_mismatch false positive for FPGA types
# ---------------------------------------------------------------------------


class TestTypeMismatchExplicitOnlyTypes:
    """Regression tests for #194 — hardware/vendor types skip auto-detection."""

    def test_fpga_rtl_amd_skips_detection(self, tmp_path: Path) -> None:
        """fpga-rtl-amd type must pass type-mismatch even when Python files dominate."""
        from specsmith.auditor import check_type_mismatch

        # Lots of .py files to simulate an FPGA project with Python tooling
        src = tmp_path / "python"
        src.mkdir()
        for i in range(20):
            (src / f"tool_{i}.py").write_text("pass\n", encoding="utf-8")

        (tmp_path / "scaffold.yml").write_text(
            "name: fpga-project\ntype: fpga-rtl-amd\nspec_version: 0.10.1\nvcs_platform: github\n",
            encoding="utf-8",
        )
        results = check_type_mismatch(tmp_path)
        assert len(results) == 1
        assert results[0].passed
        assert "explicitly set" in results[0].message

    @pytest.mark.parametrize(
        "ptype",
        [
            "fpga-rtl",
            "fpga-rtl-intel",
            "fpga-rtl-lattice",
            "mixed-fpga-embedded",
            "mixed-fpga-firmware",
            "embedded-hardware",
            "pcb-hardware",
            "yocto-bsp",
        ],
    )
    def test_all_explicit_only_types_skip_detection(self, tmp_path: Path, ptype: str) -> None:
        """Every member of _EXPLICIT_ONLY_TYPES must bypass auto-detection."""
        from specsmith.auditor import check_type_mismatch

        (tmp_path / "scaffold.yml").write_text(
            f"name: proj\ntype: {ptype}\nspec_version: 0.10.1\nvcs_platform: github\n",
            encoding="utf-8",
        )
        results = check_type_mismatch(tmp_path)
        assert len(results) == 1
        assert results[0].passed
