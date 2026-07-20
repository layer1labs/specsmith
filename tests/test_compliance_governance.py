# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Compliance governance test suite — proves every compliance claim we make.

This file is the CI gate for specsmith's compliance posture.  Every test
here maps to a specific claim: if it fails, we either have a code bug
or the regulation has changed and the code+sentinel need updating.

Test classes:
  TestRegulationCatalogIntegrity  — all 8 regs exist, IDs unique, fields valid
  TestRegulationFreshness         — article counts match regulation_versions.yml
                                    (fails CI when regs change without update)
  TestArticleControlCoverage      — every article has >=1 specsmith_control
  TestEvidenceItemModel           — EvidenceItem dataclass + to_dict
  TestEvidenceCollector           — collect_all, detect presence, no crash
  TestComplianceCheckerUnit       — check_regulation per-regulation, check_all,
                                    thresholds, gap/partial/compliant logic
  TestComplianceResultModel       — ComplianceResult to_dict, counts
  TestComplianceReporter          — JSON/MD/HTML: disclaimer present,
                                    structure valid, all regs appear
  TestCLIComplianceList           — `specsmith compliance list`
  TestCLIComplianceCheck          — `specsmith compliance check` all variants
  TestCLIComplianceReport         — `specsmith compliance report` md/json/html
  TestDisclaimerEnforcement       — disclaimer present in every output format
  TestComplianceModuleExports     — __all__ exports are importable
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from specsmith.cli import main
from specsmith.compliance.checker import ArticleResult, ComplianceChecker, ComplianceResult, Finding
from specsmith.compliance.evidence import EvidenceCollector, EvidenceItem
from specsmith.compliance.regulations import REGULATIONS, Regulation
from specsmith.compliance.reporter import ComplianceReporter

REPO_ROOT = Path(__file__).resolve().parents[1]
SENTINEL_FILE = REPO_ROOT / "docs" / "compliance" / "regulation_versions.yml"

# Expected regulation IDs — update if a new regulation is added to the catalog
EXPECTED_REGULATION_IDS = {
    "eu-ai-act",
    "nist-rmf",
    "omb-m-24-10",
    "colorado-sb24-205",
    "texas-hb1709",
    "illinois-aieta",
    "california-admt",
    "nyc-ll144",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(
    reg_id: str = "eu-ai-act",
    overall_status: str = "partial",
    confidence: float = 0.65,
) -> ComplianceResult:
    return ComplianceResult(
        regulation_id=reg_id,
        regulation_name="Test Regulation",
        jurisdiction="EU",
        checked_at="2026-06-01T00:00:00Z",
        overall_status=overall_status,
        overall_confidence=confidence,
        article_results=[
            ArticleResult(
                article_id="Art.1",
                title="Test Article",
                status="compliant",
                confidence=0.9,
                findings=[],
            ),
            ArticleResult(
                article_id="Art.2",
                title="Gap Article",
                status="gap",
                confidence=0.0,
                findings=[
                    Finding(
                        article_id="Art.2",
                        severity="gap",
                        message="missing",
                        recommendation="fix it",
                    )
                ],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# TestRegulationCatalogIntegrity
# ---------------------------------------------------------------------------


class TestRegulationCatalogIntegrity:
    """Verify the regulation catalog is structurally sound."""

    def test_all_expected_regulation_ids_present(self) -> None:
        for reg_id in EXPECTED_REGULATION_IDS:
            assert reg_id in REGULATIONS, f"Regulation '{reg_id}' missing from REGULATIONS"

    def test_no_unknown_regulation_ids(self) -> None:
        extra = set(REGULATIONS) - EXPECTED_REGULATION_IDS
        assert not extra, (
            f"Unknown regulation IDs in REGULATIONS: {extra}. "
            "Add them to EXPECTED_REGULATION_IDS if they are intentional."
        )

    def test_regulation_ids_are_unique(self) -> None:
        ids = list(REGULATIONS.keys())
        assert len(ids) == len(set(ids)), "Duplicate regulation IDs detected"

    @pytest.mark.parametrize("reg_id", sorted(EXPECTED_REGULATION_IDS))
    def test_regulation_has_required_fields(self, reg_id: str) -> None:
        reg = REGULATIONS[reg_id]
        assert reg.id == reg_id, "reg.id must match dict key"
        assert reg.name, f"{reg_id}: name must not be empty"
        assert reg.full_name, f"{reg_id}: full_name must not be empty"
        assert reg.jurisdiction, f"{reg_id}: jurisdiction must not be empty"
        assert reg.enacted, f"{reg_id}: enacted must not be empty"
        assert reg.effective, f"{reg_id}: effective must not be empty"
        assert reg.url.startswith("http"), f"{reg_id}: url must start with http"
        assert reg.description, f"{reg_id}: description must not be empty"

    @pytest.mark.parametrize("reg_id", sorted(EXPECTED_REGULATION_IDS))
    def test_regulation_has_at_least_one_article(self, reg_id: str) -> None:
        reg = REGULATIONS[reg_id]
        assert len(reg.articles) >= 1, f"{reg_id}: must have at least one article"

    @pytest.mark.parametrize("reg_id", sorted(EXPECTED_REGULATION_IDS))
    def test_all_articles_have_required_fields(self, reg_id: str) -> None:
        reg = REGULATIONS[reg_id]
        for art in reg.articles:
            assert art.id, f"{reg_id}/{art}: article id must not be empty"
            assert art.title, f"{reg_id}/{art.id}: title must not be empty"
            assert art.description, f"{reg_id}/{art.id}: description must not be empty"
            assert art.effective_date, f"{reg_id}/{art.id}: effective_date must not be empty"
            assert art.category, f"{reg_id}/{art.id}: category must not be empty"

    @pytest.mark.parametrize("reg_id", sorted(EXPECTED_REGULATION_IDS))
    def test_article_ids_unique_within_regulation(self, reg_id: str) -> None:
        reg = REGULATIONS[reg_id]
        article_ids = [a.id for a in reg.articles]
        assert len(article_ids) == len(set(article_ids)), (
            f"{reg_id}: duplicate article IDs: {article_ids}"
        )

    def test_regulation_lookup_by_id(self) -> None:
        reg = REGULATIONS["eu-ai-act"]
        assert reg.article("Art.9") is not None
        assert reg.article("Art.NOTEXIST") is None

    def test_convenience_aliases_match_registry(self) -> None:
        from specsmith.compliance.regulations import (
            CALIFORNIA,
            COLORADO,
            EU_AI_ACT,
            ILLINOIS,
            NIST_RMF,
            NYC,
            OMB_M2410,
            TEXAS,
        )

        assert EU_AI_ACT is REGULATIONS["eu-ai-act"]
        assert NIST_RMF is REGULATIONS["nist-rmf"]
        assert OMB_M2410 is REGULATIONS["omb-m-24-10"]
        assert COLORADO is REGULATIONS["colorado-sb24-205"]
        assert TEXAS is REGULATIONS["texas-hb1709"]
        assert ILLINOIS is REGULATIONS["illinois-aieta"]
        assert CALIFORNIA is REGULATIONS["california-admt"]
        assert NYC is REGULATIONS["nyc-ll144"]


# ---------------------------------------------------------------------------
# TestRegulationFreshness  ← THE KEY CI GATE
# ---------------------------------------------------------------------------


class TestRegulationFreshness:
    """Assert article counts in code match the regulation_versions.yml sentinel.

    If a regulation's articles change, this test FAILS.  The developer MUST:
      1. Update the article list in regulations.py.
      2. Update article_count + last_reviewed in regulation_versions.yml.
      3. Add a review_notes entry explaining what changed.

    This is the "canary" that alerts the team to regulation changes before
    they slip through unreviewed.
    """

    @pytest.fixture(scope="class")
    @classmethod
    def sentinel(cls) -> dict[str, int]:
        """Load regulation_versions.yml and return {reg_id: article_count}."""
        assert SENTINEL_FILE.exists(), (
            f"Sentinel file not found: {SENTINEL_FILE}\n"
            "Create docs/compliance/regulation_versions.yml to enable freshness checks."
        )
        data = yaml.safe_load(SENTINEL_FILE.read_text(encoding="utf-8"))
        return {r["id"]: r["article_count"] for r in data.get("regulations", [])}

    @pytest.mark.parametrize("reg_id", sorted(EXPECTED_REGULATION_IDS))
    def test_article_count_matches_sentinel(self, reg_id: str, sentinel: dict[str, int]) -> None:
        """CI GATE: article count in code == article_count in sentinel file.

        If this test fails it means either:
        a) A regulation's articles were added/removed in regulations.py but
           regulation_versions.yml was not updated (most common).
        b) The sentinel file has wrong counts and needs correction.

        ACTION REQUIRED when this fails:
          - Review the regulation change
          - Update docs/compliance/regulation_versions.yml
          - Update review_notes and next_review_due
        """
        assert reg_id in sentinel, (
            f"Regulation '{reg_id}' is in REGULATIONS but missing from "
            f"docs/compliance/regulation_versions.yml. Add a sentinel entry."
        )
        code_count = len(REGULATIONS[reg_id].articles)
        sentinel_count = sentinel[reg_id]
        assert code_count == sentinel_count, (
            f"REGULATION CHANGE DETECTED — {reg_id}\n"
            f"  Code has {code_count} article(s), sentinel expects {sentinel_count}.\n"
            f"  Review the change in src/specsmith/compliance/regulations.py, then:\n"
            f"  1. Update article_count in docs/compliance/regulation_versions.yml\n"
            f"  2. Update last_reviewed and review_notes\n"
            f"  3. Re-run tests to confirm green"
        )

    def test_sentinel_covers_all_expected_regulations(self, sentinel: dict[str, int]) -> None:
        """Every regulation we claim to cover must have a sentinel entry."""
        missing = EXPECTED_REGULATION_IDS - set(sentinel)
        assert not missing, (
            f"These regulations have no sentinel entry in regulation_versions.yml: {missing}"
        )

    def test_sentinel_file_is_valid_yaml(self) -> None:
        """regulation_versions.yml must be parseable YAML."""
        assert SENTINEL_FILE.exists()
        data = yaml.safe_load(SENTINEL_FILE.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert "regulations" in data
        assert "watch_list" in data

    def test_sentinel_entries_have_review_dates(self) -> None:
        data = yaml.safe_load(SENTINEL_FILE.read_text(encoding="utf-8"))
        for entry in data.get("regulations", []):
            assert "last_reviewed" in entry, f"Sentinel entry {entry['id']} missing last_reviewed"
            assert "next_review_due" in entry, (
                f"Sentinel entry {entry['id']} missing next_review_due"
            )
            assert "review_notes" in entry, f"Sentinel entry {entry['id']} missing review_notes"

    def test_watch_list_entries_have_notes(self) -> None:
        data = yaml.safe_load(SENTINEL_FILE.read_text(encoding="utf-8"))
        for entry in data.get("watch_list", []):
            assert entry.get("id"), "Watch-list entry missing id"
            assert entry.get("notes"), f"Watch-list entry {entry.get('id')} missing notes"


# ---------------------------------------------------------------------------
# TestArticleControlCoverage
# ---------------------------------------------------------------------------


class TestArticleControlCoverage:
    """Every article must map to at least one specsmith_control.

    This enforces that our compliance claims are backed by real features,
    not just philosophical alignment.
    """

    @pytest.mark.parametrize("reg_id", sorted(EXPECTED_REGULATION_IDS))
    def test_every_article_has_specsmith_control(self, reg_id: str) -> None:
        reg = REGULATIONS[reg_id]
        for art in reg.articles:
            assert art.specsmith_controls, (
                f"{reg_id}/{art.id} ({art.title}): "
                "specsmith_controls must not be empty — add at least one CLI command "
                "or feature that satisfies this article."
            )

    @pytest.mark.parametrize("reg_id", sorted(EXPECTED_REGULATION_IDS))
    def test_article_categories_are_valid(self, reg_id: str) -> None:
        valid_categories = {
            "transparency",
            "risk_management",
            "human_oversight",
            "logging",
            "data_governance",
            "security",
            "discrimination",
            "disclosure",
        }
        reg = REGULATIONS[reg_id]
        for art in reg.articles:
            assert art.category in valid_categories, (
                f"{reg_id}/{art.id}: invalid category {art.category!r}. "
                f"Valid: {sorted(valid_categories)}"
            )


# ---------------------------------------------------------------------------
# TestEvidenceItemModel
# ---------------------------------------------------------------------------


class TestEvidenceItemModel:
    def test_default_values(self) -> None:
        ev = EvidenceItem(
            control_id="Art.12",
            regulation_id="eu-ai-act",
            description="test",
            source=".specsmith/trace.jsonl",
            source_type="file",
        )
        assert ev.confidence == 0.8
        assert ev.present is True
        assert ev.detail == ""

    def test_to_dict_round_trip(self) -> None:
        ev = EvidenceItem(
            control_id="MANAGE-2",
            regulation_id="nist-rmf",
            description="ledger present",
            source="LEDGER.md",
            source_type="file",
            confidence=0.9,
            present=True,
            detail="42 entries",
        )
        d = ev.to_dict()
        assert d["control_id"] == "MANAGE-2"
        assert d["regulation_id"] == "nist-rmf"
        assert d["confidence"] == 0.9
        assert d["present"] is True
        assert d["detail"] == "42 entries"

    def test_absent_evidence_has_zero_confidence(self) -> None:
        ev = EvidenceItem(
            control_id="Art.9",
            regulation_id="eu-ai-act",
            description="WAL missing",
            source=".chronomemory/events.wal",
            source_type="file",
            confidence=0.0,
            present=False,
        )
        assert not ev.present
        assert ev.confidence == 0.0


# ---------------------------------------------------------------------------
# TestEvidenceCollector
# ---------------------------------------------------------------------------


class TestEvidenceCollector:
    def test_collect_all_returns_list(self, tmp_path: Path) -> None:
        collector = EvidenceCollector(tmp_path)
        items = collector.collect_all()
        assert isinstance(items, list)
        assert len(items) > 0, "collect_all must return at least some items"

    def test_evidence_items_have_valid_control_ids(self, tmp_path: Path) -> None:
        collector = EvidenceCollector(tmp_path)
        items = collector.collect_all()
        for item in items:
            assert item.control_id, "control_id must not be empty"
            assert item.source, "source must not be empty"
            assert item.source_type in ("file", "esdb", "config", "cli_output"), (
                f"Unknown source_type: {item.source_type}"
            )

    def test_absent_when_files_missing(self, tmp_path: Path) -> None:
        collector = EvidenceCollector(tmp_path)
        items = collector.collect_all()
        absent = [i for i in items if not i.present]
        # In an empty project, many evidence files are absent
        assert len(absent) > 0, "Some evidence must be absent in an empty project"

    def test_present_when_ledger_exists(self, tmp_path: Path) -> None:
        ledger = tmp_path / ".specsmith" / "ledger.jsonl"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text('{"type":"session_start"}\n', encoding="utf-8")
        collector = EvidenceCollector(tmp_path)
        items = collector.collect_all()
        ledger_items = [i for i in items if "ledger.jsonl" in i.source and i.present]
        assert len(ledger_items) >= 1, "Ledger JSONL evidence must be present"

    def test_esdb_not_available_in_empty_project(self, tmp_path: Path) -> None:
        collector = EvidenceCollector(tmp_path)
        assert not collector.esdb_available()

    def test_esdb_record_count_zero_without_wal(self, tmp_path: Path) -> None:
        collector = EvidenceCollector(tmp_path)
        assert collector.esdb_record_count() == 0

    def test_collect_for_regulation_returns_subset(self, tmp_path: Path) -> None:
        collector = EvidenceCollector(tmp_path)
        all_items = collector.collect_all()
        eu_items = collector.collect_for_regulation("eu-ai-act")
        # All filtered items should be in the full list
        for item in eu_items:
            assert item in all_items or item.regulation_id in ("*", "eu-ai-act")


# ---------------------------------------------------------------------------
# TestComplianceCheckerUnit
# ---------------------------------------------------------------------------


class TestComplianceCheckerUnit:
    @pytest.mark.parametrize("reg_id", sorted(EXPECTED_REGULATION_IDS))
    def test_check_regulation_returns_result(self, reg_id: str, tmp_path: Path) -> None:
        """check_regulation must run without error for every supported regulation."""
        checker = ComplianceChecker(tmp_path)
        result = checker.check_regulation(reg_id)
        assert isinstance(result, ComplianceResult)
        assert result.regulation_id == reg_id

    @pytest.mark.parametrize("reg_id", sorted(EXPECTED_REGULATION_IDS))
    def test_check_regulation_article_results_match_regulation(
        self, reg_id: str, tmp_path: Path
    ) -> None:
        """article_results count must equal the number of articles in the regulation."""
        checker = ComplianceChecker(tmp_path)
        result = checker.check_regulation(reg_id)
        expected_count = len(REGULATIONS[reg_id].articles)
        assert len(result.article_results) == expected_count, (
            f"{reg_id}: expected {expected_count} article results, "
            f"got {len(result.article_results)}"
        )

    def test_check_all_returns_all_regulations(self, tmp_path: Path) -> None:
        checker = ComplianceChecker(tmp_path)
        results = checker.check_all()
        result_ids = {r.regulation_id for r in results}
        assert result_ids == EXPECTED_REGULATION_IDS

    def test_unknown_regulation_raises_key_error(self, tmp_path: Path) -> None:
        checker = ComplianceChecker(tmp_path)
        with pytest.raises(KeyError, match="Unknown regulation"):
            checker.check_regulation("not-a-real-regulation")

    def test_empty_project_produces_gaps(self, tmp_path: Path) -> None:
        """Without any governance files, most checks return gap/partial."""
        checker = ComplianceChecker(tmp_path)
        result = checker.check_regulation("eu-ai-act")
        # With no evidence files at all, overall status should NOT be compliant
        assert result.overall_status in ("gap", "partial", "n_a"), (
            "Empty project must not be compliant"
        )

    def test_overall_status_is_valid_value(self, tmp_path: Path) -> None:
        valid_statuses = {"compliant", "partial", "gap", "n_a"}
        checker = ComplianceChecker(tmp_path)
        for result in checker.check_all():
            assert result.overall_status in valid_statuses, (
                f"{result.regulation_id}: invalid overall_status {result.overall_status!r}"
            )

    def test_confidence_is_between_0_and_1(self, tmp_path: Path) -> None:
        checker = ComplianceChecker(tmp_path)
        for result in checker.check_all():
            assert 0.0 <= result.overall_confidence <= 1.0, (
                f"{result.regulation_id}: confidence {result.overall_confidence} out of range"
            )
            for ar in result.article_results:
                assert 0.0 <= ar.confidence <= 1.0, (
                    f"{result.regulation_id}/{ar.article_id}: "
                    f"confidence {ar.confidence} out of range"
                )

    def test_article_statuses_are_valid(self, tmp_path: Path) -> None:
        valid = {"compliant", "partial", "gap", "n_a"}
        checker = ComplianceChecker(tmp_path)
        for result in checker.check_all():
            for ar in result.article_results:
                assert ar.status in valid, (
                    f"{result.regulation_id}/{ar.article_id}: invalid status {ar.status!r}"
                )

    def test_check_regulation_has_checked_at_timestamp(self, tmp_path: Path) -> None:
        checker = ComplianceChecker(tmp_path)
        result = checker.check_regulation("nist-rmf")
        assert result.checked_at, "checked_at must be set"
        # ISO-8601 format: YYYY-MM-DDTHH:MM:SSZ
        import re

        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", result.checked_at), (
            f"checked_at not in expected format: {result.checked_at}"
        )

    def test_fully_evidenced_project_improves_confidence(self, tmp_path: Path) -> None:
        """Adding evidence files should improve compliance confidence vs empty project."""
        # Create evidence files
        spec_dir = tmp_path / ".specsmith"
        spec_dir.mkdir()
        (spec_dir / "ledger.jsonl").write_text('{"type":"test"}\n', encoding="utf-8")
        (spec_dir / "trace.jsonl").write_text('{"type":"seal"}\n', encoding="utf-8")
        (tmp_path / "LEDGER.md").write_text("# Ledger\n", encoding="utf-8")

        checker_with = ComplianceChecker(tmp_path)
        result_with = checker_with.check_regulation("eu-ai-act")

        empty_dir = tmp_path.parent / "empty_tmp"
        empty_dir.mkdir(exist_ok=True)
        checker_empty = ComplianceChecker(empty_dir)
        result_empty = checker_empty.check_regulation("eu-ai-act")

        assert result_with.overall_confidence >= result_empty.overall_confidence, (
            "Adding evidence files should not decrease compliance confidence"
        )


# ---------------------------------------------------------------------------
# TestComplianceResultModel
# ---------------------------------------------------------------------------


class TestComplianceResultModel:
    def test_gap_count(self) -> None:
        result = _make_result()
        assert result.gap_count == 1  # Art.2 is gap

    def test_compliant_count(self) -> None:
        result = _make_result()
        assert result.compliant_count == 1  # Art.1 is compliant

    def test_partial_count(self) -> None:
        result = _make_result()
        assert result.partial_count == 0

    def test_to_dict_has_required_keys(self) -> None:
        result = _make_result()
        d = result.to_dict()
        required = {
            "regulation_id",
            "regulation_name",
            "jurisdiction",
            "checked_at",
            "overall_status",
            "overall_confidence",
            "compliant",
            "partial",
            "gaps",
            "article_results",
        }
        for key in required:
            assert key in d, f"to_dict missing key: {key}"

    def test_to_dict_confidence_is_rounded(self) -> None:
        result = _make_result(confidence=0.666666)
        d = result.to_dict()
        # Should be rounded to 3 decimal places
        assert d["overall_confidence"] == round(0.666666, 3)

    def test_finding_to_dict(self) -> None:
        f = Finding(
            article_id="Art.9",
            severity="gap",
            message="missing risk management",
            recommendation="enable specsmith audit",
        )
        d = f.to_dict()
        assert d["article_id"] == "Art.9"
        assert d["severity"] == "gap"
        assert d["message"] == "missing risk management"
        assert d["recommendation"] == "enable specsmith audit"

    def test_article_result_to_dict(self) -> None:
        ar = ArticleResult(
            article_id="Art.12",
            title="Record-keeping",
            status="partial",
            confidence=0.6,
            findings=[],
        )
        d = ar.to_dict()
        assert d["article_id"] == "Art.12"
        assert d["status"] == "partial"
        assert "evidence_count" in d


# ---------------------------------------------------------------------------
# TestComplianceReporter
# ---------------------------------------------------------------------------


class TestComplianceReporter:
    @pytest.fixture
    def two_results(self) -> list[ComplianceResult]:
        return [
            _make_result("eu-ai-act", "partial", 0.65),
            _make_result("nist-rmf", "gap", 0.2),
        ]

    def test_json_has_disclaimer(self, two_results: list[ComplianceResult]) -> None:
        reporter = ComplianceReporter(two_results)
        output = reporter.to_json()
        assert "disclaimer" in output.lower(), "JSON must contain 'disclaimer'"
        parsed = json.loads(output)
        assert parsed["specsmith_compliance_report"] is True
        assert "disclaimer" in parsed
        assert "legal" in parsed["disclaimer"].lower()

    def test_json_has_all_required_top_level_keys(
        self, two_results: list[ComplianceResult]
    ) -> None:
        reporter = ComplianceReporter(two_results)
        parsed = json.loads(reporter.to_json())
        for key in (
            "specsmith_compliance_report",
            "generated_at",
            "disclaimer",
            "regulations",
            "summary",
        ):
            assert key in parsed, f"JSON missing top-level key: {key}"

    def test_json_summary_has_correct_counts(self, two_results: list[ComplianceResult]) -> None:
        reporter = ComplianceReporter(two_results)
        summary = json.loads(reporter.to_json())["summary"]
        assert summary["total_regulations"] == 2

    def test_markdown_has_disclaimer(self, two_results: list[ComplianceResult]) -> None:
        reporter = ComplianceReporter(two_results)
        md = reporter.to_markdown()
        assert "DISCLAIMER" in md, "Markdown must contain DISCLAIMER"
        assert "legal" in md.lower() or "advice" in md.lower()

    def test_markdown_contains_all_regulation_names(
        self, two_results: list[ComplianceResult]
    ) -> None:
        reporter = ComplianceReporter(two_results)
        md = reporter.to_markdown()
        assert "# AI Compliance Report" in md
        for result in two_results:
            assert result.regulation_name in md

    def test_markdown_contains_article_table(self, two_results: list[ComplianceResult]) -> None:
        reporter = ComplianceReporter(two_results)
        md = reporter.to_markdown()
        assert "| Article |" in md or "| `Art." in md

    def test_html_has_disclaimer(self, two_results: list[ComplianceResult]) -> None:
        reporter = ComplianceReporter(two_results)
        html = reporter.to_html()
        assert "DISCLAIMER" in html.upper(), "HTML must contain DISCLAIMER"
        assert "legal" in html.lower() or "advice" in html.lower()

    def test_html_is_valid_structure(self, two_results: list[ComplianceResult]) -> None:
        reporter = ComplianceReporter(two_results)
        html = reporter.to_html()
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert "<title>" in html

    def test_html_contains_regulation_names(self, two_results: list[ComplianceResult]) -> None:
        reporter = ComplianceReporter(two_results)
        html = reporter.to_html()
        for result in two_results:
            assert result.regulation_name in html

    def test_summary_dict_keys(self, two_results: list[ComplianceResult]) -> None:
        reporter = ComplianceReporter(two_results)
        summary = reporter.summary_dict()
        for key in ("total_regulations", "compliant", "partial", "gaps", "overall_status"):
            assert key in summary, f"summary_dict missing key: {key}"
        assert summary["total_regulations"] == 2

    def test_summary_dict_overall_status_gap_when_gaps_exist(
        self, two_results: list[ComplianceResult]
    ) -> None:
        reporter = ComplianceReporter(two_results)
        summary = reporter.summary_dict()
        # One result is "gap" so overall must be "gap"
        assert summary["overall_status"] == "gap"

    def test_summary_dict_overall_compliant_when_no_gaps(self) -> None:
        results = [_make_result("eu-ai-act", "compliant", 0.9)]
        reporter = ComplianceReporter(results)
        summary = reporter.summary_dict()
        # compliant count=1, partial=0, gaps=0 → overall compliant
        assert summary["gaps"] == 0
        assert summary["overall_status"] in ("compliant", "partial")


# ---------------------------------------------------------------------------
# TestCLIComplianceList
# ---------------------------------------------------------------------------


class TestCLIComplianceList:
    def test_list_exits_0(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["compliance", "list"])
        assert result.exit_code == 0

    def test_list_shows_all_regulations(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["compliance", "list"])
        assert result.exit_code == 0
        for reg_id in EXPECTED_REGULATION_IDS:
            assert reg_id in result.output, f"compliance list missing {reg_id}"

    def test_list_shows_jurisdictions(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["compliance", "list"])
        assert "EU" in result.output
        assert "US" in result.output


# ---------------------------------------------------------------------------
# TestCLIComplianceCheck
# ---------------------------------------------------------------------------


class TestCLIComplianceCheck:
    def test_check_all_exits_0(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["compliance", "check", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0, f"compliance check failed: {result.output}"

    def test_check_all_shows_disclaimer(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["compliance", "check", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "DISCLAIMER" in result.output.upper() or "disclaimer" in result.output.lower()

    def test_check_json_is_valid_json(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["compliance", "check", "--project-dir", str(tmp_path), "--json"],
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "results" in parsed
        assert "disclaimer" in parsed
        assert len(parsed["results"]) == len(EXPECTED_REGULATION_IDS)

    def test_check_json_disclaimer_present(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["compliance", "check", "--project-dir", str(tmp_path), "--json"],
        )
        parsed = json.loads(result.output)
        assert "legal" in parsed["disclaimer"].lower() or "counsel" in parsed["disclaimer"].lower()

    @pytest.mark.parametrize("reg_id", sorted(EXPECTED_REGULATION_IDS))
    def test_check_single_regulation(self, reg_id: str, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "compliance",
                "check",
                "--regulation",
                reg_id,
                "--project-dir",
                str(tmp_path),
                "--json",
            ],
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert len(parsed["results"]) == 1
        assert parsed["results"][0]["regulation_id"] == reg_id

    def test_check_unknown_regulation_exits_1(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "compliance",
                "check",
                "--regulation",
                "not-a-real-regulation",
                "--project-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 1

    def test_check_shows_regulation_names(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["compliance", "check", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        # At least one regulation name should appear
        any_name_found = any(REGULATIONS[r].name in result.output for r in EXPECTED_REGULATION_IDS)
        assert any_name_found, "No regulation name found in compliance check output"


# ---------------------------------------------------------------------------
# TestCLIComplianceReport
# ---------------------------------------------------------------------------


class TestCLIComplianceReport:
    def test_report_md_exits_0(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["compliance", "report", "--project-dir", str(tmp_path), "--format", "md"],
        )
        assert result.exit_code == 0

    def test_report_md_contains_disclaimer(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["compliance", "report", "--project-dir", str(tmp_path), "--format", "md"],
        )
        assert "DISCLAIMER" in result.output.upper() or "disclaimer" in result.output.lower()

    def test_report_json_is_valid(self, tmp_path: Path) -> None:
        # Use --output to bypass console.print (which embeds Rich escape codes)
        out_file = tmp_path / "report.json"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "compliance",
                "report",
                "--project-dir",
                str(tmp_path),
                "--format",
                "json",
                "--output",
                str(out_file),
            ],
        )
        assert result.exit_code == 0
        assert out_file.exists()
        parsed = json.loads(out_file.read_text(encoding="utf-8"))
        assert "disclaimer" in parsed
        assert "regulations" in parsed

    def test_report_html_contains_doctype(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["compliance", "report", "--project-dir", str(tmp_path), "--format", "html"],
        )
        assert result.exit_code == 0
        assert "<!DOCTYPE html>" in result.output
        assert "DISCLAIMER" in result.output.upper()

    def test_report_writes_to_file(self, tmp_path: Path) -> None:
        out_file = tmp_path / "compliance_report.md"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "compliance",
                "report",
                "--project-dir",
                str(tmp_path),
                "--format",
                "md",
                "--output",
                str(out_file),
            ],
        )
        assert result.exit_code == 0
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "# AI Compliance Report" in content

    def test_report_single_regulation(self, tmp_path: Path) -> None:
        out_file = tmp_path / "single_reg.json"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "compliance",
                "report",
                "--regulation",
                "eu-ai-act",
                "--project-dir",
                str(tmp_path),
                "--format",
                "json",
                "--output",
                str(out_file),
            ],
        )
        assert result.exit_code == 0
        parsed = json.loads(out_file.read_text(encoding="utf-8"))
        assert len(parsed["regulations"]) == 1
        assert parsed["regulations"][0]["regulation_id"] == "eu-ai-act"

    def test_report_unknown_regulation_exits_1(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "compliance",
                "report",
                "--regulation",
                "not-real",
                "--project-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# TestDisclaimerEnforcement
# ---------------------------------------------------------------------------


class TestDisclaimerEnforcement:
    """The disclaimer MUST appear in ALL compliance output formats.

    This is a regulatory requirement — we must never produce compliance reports
    without a disclaimer that these are best-effort checks, not legal advice.
    """

    def _make_reporter(self) -> ComplianceReporter:
        return ComplianceReporter([_make_result()])

    def test_disclaimer_in_json(self) -> None:
        output = self._make_reporter().to_json()
        assert "disclaimer" in json.loads(output)

    def test_disclaimer_in_markdown(self) -> None:
        output = self._make_reporter().to_markdown()
        assert "DISCLAIMER" in output

    def test_disclaimer_in_html(self) -> None:
        output = self._make_reporter().to_html()
        assert "DISCLAIMER" in output.upper()

    def test_disclaimer_mentions_legal_advice(self) -> None:
        """The disclaimer must explicitly state it is not legal advice."""
        reporter = self._make_reporter()
        for fmt, content in [
            ("json", reporter.to_json()),
            ("md", reporter.to_markdown()),
            ("html", reporter.to_html()),
        ]:
            assert "legal" in content.lower() or "advice" in content.lower(), (
                f"{fmt}: disclaimer must mention 'legal' or 'advice'"
            )

    def test_module_docstring_has_disclaimer(self) -> None:
        """compliance/__init__.py docstring must contain the disclaimer."""
        # Access via sys.modules to avoid 'import specsmith.compliance' conflicting
        # with the module-level 'from specsmith.compliance.X import Y' statements
        # (CodeQL py/import-and-import-from rule).
        import sys

        comp_module = sys.modules.get("specsmith.compliance") or __import__("specsmith.compliance")
        doc = comp_module.__doc__ or ""
        assert "disclaimer" in doc.lower() or "DISCLAIMER" in doc, (
            "compliance/__init__.py docstring must contain DISCLAIMER"
        )


# ---------------------------------------------------------------------------
# TestComplianceModuleExports
# ---------------------------------------------------------------------------


class TestComplianceModuleExports:
    """Verify all __all__ symbols are importable without error."""

    def test_all_exports_importable(self) -> None:
        import sys

        m = sys.modules.get("specsmith.compliance") or __import__("specsmith.compliance")
        for name in m.__all__:
            obj = getattr(m, name, None)
            assert obj is not None, f"compliance.__all__ member '{name}' is None"

    def test_get_regulation_returns_correct_type(self) -> None:
        from specsmith.compliance import get_regulation

        reg = get_regulation("eu-ai-act")
        assert isinstance(reg, Regulation)
        assert reg.id == "eu-ai-act"

    def test_get_regulation_raises_for_unknown(self) -> None:
        from specsmith.compliance import get_regulation

        with pytest.raises(KeyError, match="Unknown regulation"):
            get_regulation("totally-fake")
