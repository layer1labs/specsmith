"""Regression tests for GovernanceBench result completeness (REQ-484 / TEST-510)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from govern_bench.compare_runs import (  # noqa: E402
    split_input_spec,
    validate_comparable,
    validate_results,
)
from govern_bench.metrics import estimate_cost, model_tier  # noqa: E402
from govern_bench.run_bench import incomplete_real_run  # noqa: E402


def _row(
    *,
    task: str = "T1",
    condition: str = "UNGOVERNED",
    rep: int = 1,
    model: str = "gpt-4o-mini",
    skipped: bool = False,
    error: str | None = None,
) -> dict:
    return {
        "task": task,
        "condition": condition,
        "rep": rep,
        "model": model,
        "provider": "openai",
        "tokens": 100,
        "cost_usd": 0.001,
        "passed": True,
        "quality": 1.0,
        "rework_turns": 1,
        "lint_passed": True,
        "tests_passed": True,
        "skipped": skipped,
        "error": error,
    }


def test_complete_results_return_cell_signature() -> None:
    rows = [
        _row(condition="UNGOVERNED", rep=1),
        _row(condition="UNGOVERNED", rep=2),
        _row(condition="SPECSMITH_FULL", rep=1),
        _row(condition="SPECSMITH_FULL", rep=2),
    ]
    assert validate_results(rows, "test") == {
        ("T1", "UNGOVERNED", 1),
        ("T1", "UNGOVERNED", 2),
        ("T1", "SPECSMITH_FULL", 1),
        ("T1", "SPECSMITH_FULL", 2),
    }


@pytest.mark.parametrize(
    ("skipped", "error"),
    [(True, None), (True, "HTTP 402 depleted credits"), (False, "HTTP 429 rate limit")],
)
def test_provider_failures_are_rejected(skipped: bool, error: str | None) -> None:
    with pytest.raises(ValueError, match="incomplete cell"):
        validate_results([_row(skipped=skipped, error=error)], "test")


def test_duplicate_cells_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate cell"):
        validate_results([_row(), _row()], "test")


def test_uneven_repetition_sets_are_rejected() -> None:
    rows = [
        _row(condition="UNGOVERNED", rep=1),
        _row(condition="UNGOVERNED", rep=2),
        _row(condition="SPECSMITH_FULL", rep=1),
    ]
    with pytest.raises(ValueError, match="uneven repetition sets"):
        validate_results(rows, "test")


def test_cross_model_cell_mismatch_is_rejected() -> None:
    reference = ("gpt", {("T1", "UNGOVERNED", 1), ("T1", "SPECSMITH_FULL", 1)})
    incomplete = ("qwen", {("T1", "UNGOVERNED", 1)})
    with pytest.raises(ValueError, match="cell set differs"):
        validate_comparable([reference, incomplete])


def test_comparison_input_parser_preserves_windows_drive_path() -> None:
    assert split_input_spec(r"C:\tmp\bench-results.json") == (
        r"C:\tmp\bench-results.json",
        None,
    )
    assert split_input_spec("bench-results.json:model-label") == (
        "bench-results.json",
        "model-label",
    )


@pytest.mark.parametrize(("skipped", "errored"), [(1, 0), (0, 1), (3, 2)])
def test_real_run_fails_on_any_incomplete_cell(skipped: int, errored: int) -> None:
    assert incomplete_real_run(dry_run=False, skipped=skipped, errored=errored)
    assert not incomplete_real_run(dry_run=True, skipped=skipped, errored=errored)


def test_complete_real_run_remains_publishable() -> None:
    assert not incomplete_real_run(dry_run=False, skipped=0, errored=0)


def test_current_model_pricing_and_tiers() -> None:
    assert estimate_cost("gpt-5.6-luna", 1_000_000, 1_000_000) == 7.0
    assert estimate_cost("gpt-5.6-terra", 1_000_000, 1_000_000) == 17.5
    assert estimate_cost("gpt-5.6-sol", 1_000_000, 1_000_000) == 35.0
    assert estimate_cost("Qwen/Qwen3.6-35B-A3B:deepinfra", 1_000_000, 1_000_000) == pytest.approx(
        1.10
    )
    assert model_tier("gpt-5.6-luna") == "mini"
    assert model_tier("gpt-5.6-terra") == "mid"
    assert model_tier("gpt-5.6-sol") == "frontier"
    assert model_tier("Qwen/Qwen3.6-35B-A3B:deepinfra") == "open-mid"
