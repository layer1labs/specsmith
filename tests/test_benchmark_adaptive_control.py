from __future__ import annotations

import sys
from pathlib import Path

import pytest

from specsmith.benchmark_audit import audit_benchmark_rows

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from govern_bench.harness import (  # noqa: E402
    _build_active_tools,
    _exec_read_file_with_evidence,
    _looks_like_nonterminal_narration,
    _milestone_contract,
    _milestone_progress,
    _openai_sampling_params,
    _replace_adaptive_progress_message,
    _scope_contract,
    _scope_progress,
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


def test_accepted_aee_work_starts_with_minimal_tools_and_bounded_scope() -> None:
    task = get_task("T1")
    initial = [tool["function"]["name"] for tool in _build_active_tools("SPECSMITH_FULL", task)]
    diagnostic = [
        tool["function"]["name"]
        for tool in _build_active_tools("SPECSMITH_FULL", task, diagnostics_required=True)
    ]

    assert initial == ["read_file", "write_file", "done"]
    assert {"list_files", "run_command", "ask_clarification"}.issubset(diagnostic)
    assert "app/main.py" in _scope_contract(task)
    assert "tests/test_main.py" in _scope_progress(task, ["app/main.py"])
    assert "call done" in _scope_progress(task, task.expected_files_changed)


def test_qwen_sampling_uses_official_model_specific_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("BENCH_TEMPERATURE", raising=False)

    assert _openai_sampling_params("Qwen/Qwen3-Coder-Next:novita") == {
        "temperature": 1.0,
        "top_p": 0.95,
    }
    assert _openai_sampling_params("Qwen/Qwen3-Coder-480B-A35B-Instruct:novita") == {
        "temperature": 0.7,
        "top_p": 0.8,
    }
    assert _openai_sampling_params("Qwen/Qwen3.6-35B-A3B:deepinfra") == {
        "temperature": 0.6,
        "top_p": 0.95,
    }

    monkeypatch.setenv("BENCH_TEMPERATURE", "0.33")
    assert _openai_sampling_params("Qwen/Qwen3-Coder-Next:novita") == {"temperature": 0.33}


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("Let me update the tests next.", True),
        ("Now I'll run the validator.", True),
        ("The implementation and tests are complete.", False),
    ],
)
def test_nonterminal_narration_detection_is_narrow(content: str, expected: bool) -> None:
    assert _looks_like_nonterminal_narration(content) is expected


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


def test_audit_exposes_tool_serialization_text_stops_and_scope_expansion() -> None:
    serialized = _audit_row(condition="SPECSMITH_FULL", passed=False)
    serialized.update(
        {
            "stop_reason": "text_response",
            "expected_files_changed": ["backend/main.py"],
            "files_written": ["backend/main.py", "notes/debug.txt"],
            "agent_transcript": [
                {
                    "role": "assistant",
                    "tool_calls": ["read_file"],
                    "tool_targets": [f"read_file:file-{index}.txt"],
                }
                for index in range(6)
            ],
        }
    )

    report = audit_benchmark_rows([serialized])
    codes = {weakness.code for weakness in report.weaknesses}

    assert {"premature_text_stop", "tool_call_serialization", "scope_expansion"} <= codes


def test_qwen_agentic_coding_candidates_have_hf_routes_pricing_and_tiers() -> None:
    registry = load_registry(_SCRIPTS_DIR / "govern_bench" / "models.yml")
    candidates = select(registry, groups={"open-qwen"})

    assert {candidate["label"] for candidate in candidates} == {
        "qwen3-coder-next",
        "qwen3-coder-480b",
        "qwen3.6-35b-deepinfra",
    }
    assert all(candidate["provider"] == "huggingface" for candidate in candidates)
    assert estimate_cost("Qwen/Qwen3-Coder-Next:novita", 1_000_000, 1_000_000) == pytest.approx(
        1.70
    )
    assert model_tier("Qwen/Qwen3-Coder-Next:novita") == "open-large"
    assert model_tier("Qwen/Qwen3-Coder-480B-A35B-Instruct:novita") == "open-xl"
    assert estimate_cost("Qwen/Qwen3.6-35B-A3B:deepinfra", 1_000_000, 1_000_000) == pytest.approx(
        1.10
    )
