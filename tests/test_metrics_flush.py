# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for flush_session_metrics helper."""

from __future__ import annotations

from pathlib import Path

from specsmith.project_metrics import MetricsStore, flush_session_metrics


def _latest_record(tmp_path: Path):
    records = MetricsStore(tmp_path).load()
    assert records
    return records[-1]


def test_flush_session_metrics_writes_non_zero_tokens(tmp_path: Path) -> None:
    flush_session_metrics(
        tmp_path,
        work_item_id="WI-436",
        model="anthropic",
        input_tokens=120,
        output_tokens=80,
        cost_usd=0.0025,
    )
    rec = _latest_record(tmp_path)
    assert rec.input_tokens == 120
    assert rec.output_tokens == 80
    assert rec.tokens_total == 200


def test_flush_session_metrics_preserves_model_and_work_item_id(tmp_path: Path) -> None:
    flush_session_metrics(
        tmp_path,
        work_item_id="WI-REQ-436",
        model="gpt-4o-mini",
        input_tokens=1,
        output_tokens=1,
    )
    rec = _latest_record(tmp_path)
    assert rec.model == "gpt-4o-mini"
    assert rec.work_item_id == "WI-REQ-436"


def test_flush_session_metrics_writes_record_when_all_values_zero(tmp_path: Path) -> None:
    flush_session_metrics(tmp_path)
    records = MetricsStore(tmp_path).load()
    assert len(records) == 1
    rec = records[0]
    assert rec.input_tokens == 0
    assert rec.output_tokens == 0
    assert rec.cost_usd == 0.0
