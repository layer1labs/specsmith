"""Tests for the GovernanceBench data pipeline starter."""

from __future__ import annotations

import pytest
from pipeline import etl


def test_run_pipeline_deduplicates_latest(tmp_path):
    records = [
        {"id": 1, "device_id": "d-1", "ts": "2026-01-01T00:00:00Z", "value": 10.0, "status": "ok"},
        {"id": 2, "device_id": "d-1", "ts": "2026-01-01T00:00:00Z", "value": 11.0, "status": "ok"},
        {"id": 3, "device_id": "d-2", "ts": "2026-01-01T00:00:10Z", "value": 5.0, "status": "ok"},
    ]

    output = tmp_path / "events.csv"
    frame = etl.run_pipeline(records, output)

    assert len(frame) == 2, "Pipeline should deduplicate by (device_id, ts)"
    row = frame[frame["device_id"] == "d-1"].iloc[0]
    assert row["value"] == pytest.approx(11.0)


def test_run_pipeline_handles_nullable_value(tmp_path):
    records = [
        {"id": 7, "device_id": "d-8", "ts": "2026-01-01T00:02:00Z", "value": None, "status": "ok"},
    ]

    output = tmp_path / "nullable.csv"
    frame = etl.run_pipeline(records, output)

    assert frame.iloc[0]["value"] == pytest.approx(0.0), "None values should be normalised to 0.0"


def test_export_csv_replaces_null_status(tmp_path):
    frame = etl.apply_schema(
        etl.normalize_records(
            [
                {
                    "id": 9,
                    "device_id": "d-9",
                    "ts": "2026-01-01T00:03:00Z",
                    "value": 4.0,
                    "status": None,
                }
            ]
        )
    )
    output = etl.export_csv(frame, tmp_path / "status.csv")
    text = output.read_text(encoding="utf-8")
    assert ",unknown" in text, "Missing statuses should be normalised before export"
