# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for specsmith.project_metrics."""

from __future__ import annotations

from pathlib import Path

from specsmith.project_metrics import MetricsRecord, MetricsStore

# ---------------------------------------------------------------------------
# MetricsRecord
# ---------------------------------------------------------------------------


class TestMetricsRecord:
    def test_new_generates_session_id(self) -> None:
        rec = MetricsRecord.new()
        assert rec.session_id.startswith("S-")
        assert len(rec.session_id) == 10  # "S-" + 8 hex chars

    def test_new_generates_timestamp(self) -> None:
        rec = MetricsRecord.new()
        # ISO-8601 UTC: "YYYY-MM-DDTHH:MM:SSZ"
        assert len(rec.timestamp) == 20
        assert rec.timestamp.endswith("Z")

    def test_tokens_total(self) -> None:
        rec = MetricsRecord.new(input_tokens=100, output_tokens=50)
        assert rec.tokens_total == 150

    def test_to_dict_includes_tokens_total(self) -> None:
        rec = MetricsRecord.new(input_tokens=200, output_tokens=100)
        d = rec.to_dict()
        assert d["tokens_total"] == 300
        assert "session_id" in d
        assert "timestamp" in d

    def test_from_dict_round_trip(self) -> None:
        rec = MetricsRecord.new(
            input_tokens=10,
            output_tokens=5,
            cost_usd=0.0012,
            quality_score=0.85,
            passed=True,
            rework_turns=2,
            work_item_id="WI-001",
            model="gpt-4o",
            command="save",
            notes="test run",
        )
        d = rec.to_dict()
        rec2 = MetricsRecord.from_dict(d)
        assert rec2.session_id == rec.session_id
        assert rec2.input_tokens == 10
        assert rec2.output_tokens == 5
        assert abs(rec2.cost_usd - 0.0012) < 1e-9
        assert abs(rec2.quality_score - 0.85) < 1e-9
        assert rec2.passed is True
        assert rec2.rework_turns == 2
        assert rec2.work_item_id == "WI-001"
        assert rec2.model == "gpt-4o"
        assert rec2.command == "save"
        assert rec2.notes == "test run"

    def test_from_dict_handles_missing_fields(self) -> None:
        rec = MetricsRecord.from_dict(
            {"session_id": "S-ABCDEF12", "timestamp": "2026-01-01T00:00:00Z"}
        )
        assert rec.input_tokens == 0
        assert rec.cost_usd == 0.0
        assert rec.passed is False
        assert rec.rework_turns == 1


# ---------------------------------------------------------------------------
# MetricsStore — write and read
# ---------------------------------------------------------------------------


class TestMetricsStoreAppendLoad:
    def test_append_creates_file(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        store.append(MetricsRecord.new(command="save"))
        metrics_file = tmp_path / ".specsmith" / "session_metrics.jsonl"
        assert metrics_file.exists()

    def test_load_returns_empty_when_no_file(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        assert store.load() == []

    def test_append_and_load_round_trip(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        rec = MetricsRecord.new(cost_usd=0.005, passed=True, rework_turns=1)
        store.append(rec)
        records = store.load()
        assert len(records) == 1
        assert records[0].session_id == rec.session_id
        assert abs(records[0].cost_usd - 0.005) < 1e-9
        assert records[0].passed is True

    def test_append_multiple_records(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        for i in range(5):
            store.append(MetricsRecord.new(rework_turns=i + 1))
        records = store.load()
        assert len(records) == 5

    def test_load_skips_corrupt_lines(self, tmp_path: Path) -> None:
        metrics_file = tmp_path / ".specsmith" / "session_metrics.jsonl"
        metrics_file.parent.mkdir(parents=True)
        store = MetricsStore(tmp_path)
        store.append(MetricsRecord.new(command="good"))
        # Inject a corrupt line
        with metrics_file.open("a", encoding="utf-8") as fh:
            fh.write("{not valid json}\n")
        store.append(MetricsRecord.new(command="also_good"))
        records = store.load()
        # Only the two valid records should be returned
        assert len(records) == 2

    def test_reset_removes_file(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        store.append(MetricsRecord.new())
        store.reset()
        assert store.load() == []

    def test_reset_noop_when_no_file(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        store.reset()  # should not raise


# ---------------------------------------------------------------------------
# Date filtering
# ---------------------------------------------------------------------------


class TestMetricsStoreFiltering:
    def _make_record(self, timestamp: str, **kwargs: object) -> MetricsRecord:
        rec = MetricsRecord.new(**kwargs)  # type: ignore[arg-type]
        rec.timestamp = timestamp
        return rec

    def test_since_filter_includes_boundary(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        store.append(self._make_record("2026-01-01T00:00:00Z", cost_usd=1.0))
        store.append(self._make_record("2026-06-15T12:00:00Z", cost_usd=2.0))
        store.append(self._make_record("2025-12-31T23:59:59Z", cost_usd=3.0))
        records = store.load(since="2026-01-01")
        assert len(records) == 2
        for r in records:
            assert r.timestamp >= "2026-01-01"

    def test_until_filter_includes_boundary(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        store.append(self._make_record("2026-01-01T00:00:00Z", cost_usd=1.0))
        store.append(self._make_record("2026-06-15T12:00:00Z", cost_usd=2.0))
        store.append(self._make_record("2026-12-31T00:00:00Z", cost_usd=3.0))
        records = store.load(until="2026-06-15")
        assert len(records) == 2
        for r in records:
            assert r.timestamp[:10] <= "2026-06-15"

    def test_since_until_combined(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        store.append(self._make_record("2026-01-01T00:00:00Z"))
        store.append(self._make_record("2026-03-15T00:00:00Z"))
        store.append(self._make_record("2026-06-01T00:00:00Z"))
        records = store.load(since="2026-02-01", until="2026-04-30")
        assert len(records) == 1
        assert records[0].timestamp[:10] == "2026-03-15"


# ---------------------------------------------------------------------------
# Aggregates
# ---------------------------------------------------------------------------


class TestCostOfPass:
    def _store_with_records(self, tmp_path: Path, records: list[MetricsRecord]) -> MetricsStore:
        store = MetricsStore(tmp_path)
        for r in records:
            store.append(r)
        return store

    def test_returns_inf_when_no_records(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        assert store.cost_of_pass() == float("inf")

    def test_returns_inf_when_no_costed_records(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        store.append(MetricsRecord.new(passed=True))  # cost_usd=0
        assert store.cost_of_pass() == float("inf")

    def test_returns_inf_when_pass_rate_zero(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        store.append(MetricsRecord.new(cost_usd=0.01, passed=False))
        assert store.cost_of_pass() == float("inf")

    def test_cost_of_pass_single_passing_session(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        store.append(MetricsRecord.new(cost_usd=0.01, passed=True))
        cop = store.cost_of_pass()
        # mean_cost=0.01, pass_rate=1.0  →  cop=0.01
        assert abs(cop - 0.01) < 1e-9

    def test_cost_of_pass_50_percent_pass_rate(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        store.append(MetricsRecord.new(cost_usd=0.01, passed=True))
        store.append(MetricsRecord.new(cost_usd=0.01, passed=False))
        cop = store.cost_of_pass()
        # mean_cost=0.01, pass_rate=0.5  →  cop=0.02
        assert abs(cop - 0.02) < 1e-9


class TestQualityTrend:
    def test_returns_none_when_no_records(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        assert store.quality_trend() is None

    def test_returns_mean_within_window(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        # Two records 5 days apart — both within 7-day window
        store.append(MetricsRecord.new(quality_score=0.8))
        store.append(MetricsRecord.new(quality_score=0.6))
        trend = store.quality_trend()
        assert trend is not None
        assert abs(trend - 0.7) < 1e-9

    def test_zero_quality_excluded_from_trend(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        store.append(MetricsRecord.new(quality_score=0.0))  # should be excluded
        store.append(MetricsRecord.new(quality_score=0.9))
        trend = store.quality_trend()
        assert trend is not None
        assert abs(trend - 0.9) < 1e-9


class TestReport:
    def test_empty_store_returns_zero_sessions(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        report = store.report()
        assert report["n_sessions"] == 0
        assert report["pass_rate"] is None

    def test_report_aggregates_correctly(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        store.append(
            MetricsRecord.new(cost_usd=0.01, quality_score=0.9, passed=True, rework_turns=1)
        )
        store.append(
            MetricsRecord.new(cost_usd=0.02, quality_score=0.7, passed=False, rework_turns=3)
        )
        report = store.report()
        assert report["n_sessions"] == 2
        assert report["pass_rate"] == 0.5
        assert abs(report["total_cost_usd"] - 0.03) < 1e-9
        assert abs(report["mean_cost_usd"] - 0.015) < 1e-9
        assert abs(report["mean_quality"] - 0.8) < 1e-9
        assert report["mean_rework"] == 2.0

    def test_report_top_rework_sessions(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        for turns in [1, 3, 2, 5, 4, 6]:
            store.append(MetricsRecord.new(rework_turns=turns))
        report = store.report()
        top = report["top_rework_sessions"]
        assert len(top) == 5
        assert top[0]["rework_turns"] == 6  # worst first

    def test_report_since_filter_applied(self, tmp_path: Path) -> None:
        store = MetricsStore(tmp_path)
        rec_old = MetricsRecord.new(cost_usd=0.05)
        rec_old.timestamp = "2025-01-01T00:00:00Z"
        store.append(rec_old)
        rec_new = MetricsRecord.new(cost_usd=0.01, passed=True)
        rec_new.timestamp = "2026-06-01T00:00:00Z"
        store.append(rec_new)
        report = store.report(since="2026-01-01")
        assert report["n_sessions"] == 1
        assert abs(report["total_cost_usd"] - 0.01) < 1e-9
