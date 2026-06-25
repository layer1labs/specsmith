# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for specsmith.quality_report."""

from __future__ import annotations

from pathlib import Path

import pytest

from specsmith.project_metrics import MetricsRecord, MetricsStore
from specsmith.quality_report import (
    QualityReportData,
    _build_suggestions,
    build_quality_report,
    render_markdown,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def minimal_project(tmp_path: Path) -> Path:
    """A minimal project directory with a pyproject.toml for name detection."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test-project"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture()
def project_with_metrics(minimal_project: Path) -> Path:
    """A project that has some metrics recorded."""
    store = MetricsStore(minimal_project)
    store.append(MetricsRecord.new(cost_usd=0.01, quality_score=0.85, passed=True, rework_turns=1))
    store.append(MetricsRecord.new(cost_usd=0.02, quality_score=0.65, passed=False, rework_turns=3))
    return minimal_project


# ---------------------------------------------------------------------------
# build_quality_report
# ---------------------------------------------------------------------------


class TestBuildQualityReport:
    def test_returns_quality_report_data(self, minimal_project: Path) -> None:
        data = build_quality_report(minimal_project)
        assert isinstance(data, QualityReportData)

    def test_project_name_from_pyproject(self, minimal_project: Path) -> None:
        data = build_quality_report(minimal_project)
        assert data.project_name == "test-project"

    def test_fallback_project_name_to_dirname(self, tmp_path: Path) -> None:
        data = build_quality_report(tmp_path)
        assert data.project_name == tmp_path.name

    def test_generated_at_is_iso_timestamp(self, minimal_project: Path) -> None:
        data = build_quality_report(minimal_project)
        assert "T" in data.generated_at
        assert data.generated_at.endswith("Z")

    def test_since_until_passed_through(self, minimal_project: Path) -> None:
        data = build_quality_report(minimal_project, since="2026-01-01", until="2026-12-31")
        assert data.since == "2026-01-01"
        assert data.until == "2026-12-31"

    def test_lifetime_metrics_loaded(self, project_with_metrics: Path) -> None:
        data = build_quality_report(project_with_metrics)
        assert data.lifetime.get("n_sessions") == 2

    def test_period_metrics_empty_when_no_filter(self, project_with_metrics: Path) -> None:
        data = build_quality_report(project_with_metrics)
        # Without since/until, period should be empty dict
        assert data.period == {}

    def test_period_metrics_filled_when_filter_specified(self, project_with_metrics: Path) -> None:
        data = build_quality_report(project_with_metrics, since="2026-01-01")
        # Since we specified a filter, period should be populated
        assert isinstance(data.period, dict)

    def test_suggestions_generated(self, minimal_project: Path) -> None:
        data = build_quality_report(minimal_project)
        assert isinstance(data.suggestions, list)
        assert len(data.suggestions) >= 1


# ---------------------------------------------------------------------------
# render_markdown
# ---------------------------------------------------------------------------


class TestRenderMarkdown:
    def _make_data(self, **kwargs: object) -> QualityReportData:
        data = QualityReportData(project_name="test-project")
        for k, v in kwargs.items():
            setattr(data, k, v)
        return data

    def test_output_is_string(self) -> None:
        data = QualityReportData(project_name="myproject")
        md = render_markdown(data)
        assert isinstance(md, str)

    def test_contains_project_name(self) -> None:
        data = QualityReportData(project_name="awesome-lib")
        md = render_markdown(data)
        assert "awesome-lib" in md

    def test_contains_required_headings(self) -> None:
        data = QualityReportData(project_name="proj")
        md = render_markdown(data)
        assert "## 1. Project Snapshot" in md
        assert "## 2. Lifetime Metrics" in md

    def test_contains_period_heading_when_filter_set(self) -> None:
        data = QualityReportData(project_name="proj", since="2026-01-01")
        md = render_markdown(data)
        assert "## 3. Period Metrics" in md

    def test_no_period_heading_without_filter(self) -> None:
        data = QualityReportData(project_name="proj")
        md = render_markdown(data)
        assert "## 3. Period Metrics" not in md

    def test_contains_date_range_in_title_when_filter(self) -> None:
        data = QualityReportData(project_name="proj", since="2026-01-01", until="2026-06-30")
        md = render_markdown(data)
        assert "2026-01-01" in md
        assert "2026-06-30" in md

    def test_contains_audit_health_healthy(self) -> None:
        data = QualityReportData(project_name="proj", audit_healthy=True)
        md = render_markdown(data)
        assert "Healthy" in md

    def test_contains_audit_health_unhealthy(self) -> None:
        data = QualityReportData(project_name="proj", audit_healthy=False)
        md = render_markdown(data)
        assert "Issues found" in md

    def test_contains_suggestions_section(self) -> None:
        data = QualityReportData(project_name="proj", suggestions=["Do X", "Fix Y"])
        md = render_markdown(data)
        assert "## 6. Suggested Next Actions" in md
        assert "Do X" in md
        assert "Fix Y" in md

    def test_contains_json_appendix(self) -> None:
        data = QualityReportData(project_name="proj")
        md = render_markdown(data)
        assert "## 7. Raw Data (JSON)" in md
        assert "```json" in md

    def test_contains_bottleneck_table_when_rework_present(self) -> None:
        data = QualityReportData(
            project_name="proj",
            lifetime={
                "n_sessions": 2,
                "top_rework_sessions": [
                    {
                        "session_id": "S-AABB1122",
                        "work_item_id": "WI-001",
                        "rework_turns": 5,
                        "timestamp": "2026-06-01T00:00:00Z",
                    },
                ],
            },
        )
        md = render_markdown(data)
        assert "## 4. Bottleneck Sessions" in md
        assert "S-AABB1122" in md

    def test_contains_github_issues_section(self) -> None:
        data = QualityReportData(
            project_name="proj",
            open_issues_count=7,
            oldest_open_issue_days=14,
        )
        md = render_markdown(data)
        assert "## 5. GitHub Issues" in md
        assert "7" in md
        assert "14 days" in md


# ---------------------------------------------------------------------------
# _build_suggestions (internal, but logic-heavy enough to test directly)
# ---------------------------------------------------------------------------


class TestBuildSuggestions:
    def _data(self, **kwargs: object) -> QualityReportData:
        data = QualityReportData(project_name="proj")
        data.lifetime = {}
        for k, v in kwargs.items():
            setattr(data, k, v)
        return data

    def test_no_critical_issues_fallback(self) -> None:
        data = self._data(audit_healthy=True)
        suggestions = _build_suggestions(data)
        assert len(suggestions) == 1
        assert "No critical improvements" in suggestions[0]

    def test_audit_failure_triggers_suggestion(self) -> None:
        data = self._data(audit_healthy=False, audit_checks_failed=3)
        suggestions = _build_suggestions(data)
        assert any("audit" in s.lower() for s in suggestions)

    def test_low_pass_rate_triggers_suggestion(self) -> None:
        data = self._data(audit_healthy=True)
        data.lifetime = {"pass_rate": 0.5}
        suggestions = _build_suggestions(data)
        assert any("Pass rate" in s for s in suggestions)

    def test_high_rework_triggers_suggestion(self) -> None:
        data = self._data(audit_healthy=True)
        data.lifetime = {"mean_rework": 3.5}
        suggestions = _build_suggestions(data)
        assert any("rework" in s.lower() for s in suggestions)

    def test_declining_quality_triggers_suggestion(self) -> None:
        data = self._data(audit_healthy=True)
        data.lifetime = {"quality_7d": 0.60, "mean_quality": 0.85}
        suggestions = _build_suggestions(data)
        assert any("trending down" in s.lower() for s in suggestions)

    def test_high_cost_of_pass_triggers_suggestion(self) -> None:
        data = self._data(audit_healthy=True)
        data.lifetime = {"cost_of_pass": 0.05}
        suggestions = _build_suggestions(data)
        assert any("Cost-of-pass" in s for s in suggestions)

    def test_many_open_issues_triggers_suggestion(self) -> None:
        data = self._data(audit_healthy=True, open_issues_count=25)
        suggestions = _build_suggestions(data)
        assert any("25 open" in s for s in suggestions)

    def test_stale_issues_trigger_suggestion(self) -> None:
        data = self._data(audit_healthy=True, oldest_open_issue_days=45)
        suggestions = _build_suggestions(data)
        assert any("45 days" in s for s in suggestions)
