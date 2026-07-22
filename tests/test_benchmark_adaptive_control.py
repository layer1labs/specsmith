from __future__ import annotations

import sys
from pathlib import Path

import pytest

from specsmith.benchmark_audit import audit_benchmark_rows

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from govern_bench.harness import (  # noqa: E402
    _exec_read_file_with_evidence,
    _milestone_contract,
    _milestone_progress,
    _replace_adaptive_progress_message,
)
from govern_bench.metrics import estimate_cost, model_tier  # noqa: E402
from govern_bench.select_models import load_registry, select  # noqa: E402
from govern_bench.tasks import get_task  # noqa: E402


def test_unchanged_file_reads_return_digest_receipts_until_content_changes(
    tmp_path: Path,
) -> None:
    path = tmp_path / "component.py"
    path.write_text("VALUE = 1\n", encoding="utf-8")
    evidence: dict[str, tuple[str, int]] = {}

    first, first_suppressed = _exec_read_file_with_evidence(
        tmp_path, "component.py", evidence, turn=1, compress_unchanged=True
    )
    repeated, repeated_suppressed = _exec_read_file_with_evidence(
        tmp_path, "component.py", evidence, turn=2, compress_unchanged=True
    )
    path.write_text("VALUE = 2\n", encoding="utf-8")
    changed, changed_suppressed = _exec_read_file_with_evidence(
        tmp_path, "component.py", evidence, turn=3, compress_unchanged=True
    )

    assert first == "VALUE = 1\n"
    assert not first_suppressed
    assert repeated_suppressed
    assert "UNCHANGED" in repeated
    assert "VALUE = 1" not in repeated
    assert changed == "VALUE = 2\n"
    assert not changed_suppressed


def test_long_horizon_milestones_are_bounded_and_progress_replaces_history() -> None:
    task = get_task("T28")
    contract = _milestone_contract(task)

    assert len(task.milestones) == 4
    assert "shared contract and API" in contract
    assert "interactive UI journey" in contract
    assert "no separate planning turn" in contract
    assert "backend/main.py" in _milestone_progress(task, ["contracts/incident.schema.json"])
    assert "worker boundary" in _milestone_progress(
        task,
        [
            "contracts/incident.schema.json",
            "backend/main.py",
            "tests/test_backend.py",
        ],
    )

    messages = _replace_adaptive_progress_message([], "first")
    messages = _replace_adaptive_progress_message(messages, "second")
    assert len(messages) == 1
    assert messages[0]["content"].endswith("second")


def _audit_row(*, condition: str, passed: bool, transcript: list[dict] | None = None) -> dict:
    return {
        "task": "T28",
        "category": "long_horizon_product",
        "horizon": "long",
        "condition": condition,
        "rep": 1,
        "model": "Qwen/Qwen3-Coder-Next:novita",
        "input_tokens": 20_000,
        "output_tokens": 1_000,
        "llm_turns": 20,
        "passed": passed,
        "tests_passed": passed,
        "project_tests_passed": True,
        "acceptance_oracle_passed": passed,
        "stop_reason": "done" if passed else "max_turns",
        "agent_transcript": transcript or [],
        "skipped": False,
        "error": None,
    }


def test_audit_exposes_task_type_reread_and_milestone_inefficiencies() -> None:
    read_cycle = [
        "read_file:backend/main.py",
        "read_file:worker/main.go",
        "read_file:ui/src/App.tsx",
        "read_file:docs/architecture.md",
    ]
    transcript = [
        {
            "role": "assistant",
            "tool_targets": [
                *read_cycle,
                *read_cycle,
                *read_cycle,
                "write_file:backend/main.py",
                "write_file:tests/test_backend.py",
                "write_file:worker/main.go",
                "write_file:worker/main_test.go",
                "write_file:ui/src/App.tsx",
                "write_file:docs/architecture.md",
            ],
        }
    ]
    report = audit_benchmark_rows(
        [
            _audit_row(condition="CURSOR_RULES", passed=True),
            _audit_row(condition="SPECSMITH_FULL", passed=False, transcript=transcript),
        ]
    )
    codes = {weakness.code for weakness in report.weaknesses}

    assert "broad_reread_churn" in codes
    assert "milestone_fragmentation" in codes
    assert "cursor_correctness_regression" in codes
    assert report.task_type_metrics["long_horizon_product"]["CURSOR_RULES"]["pass_rate"] == 1.0


def test_qwen_agentic_coding_candidates_have_hf_routes_pricing_and_tiers() -> None:
    registry = load_registry(_SCRIPTS_DIR / "govern_bench" / "models.yml")
    candidates = select(registry, groups={"open-qwen"})

    assert {candidate["label"] for candidate in candidates} == {
        "qwen3-coder-next",
        "qwen3-coder-480b",
    }
    assert all(candidate["provider"] == "huggingface" for candidate in candidates)
    assert estimate_cost("Qwen/Qwen3-Coder-Next:novita", 1_000_000, 1_000_000) == pytest.approx(
        1.70
    )
    assert model_tier("Qwen/Qwen3-Coder-Next:novita") == "open-large"
    assert model_tier("Qwen/Qwen3-Coder-480B-A35B-Instruct:novita") == "open-xl"
