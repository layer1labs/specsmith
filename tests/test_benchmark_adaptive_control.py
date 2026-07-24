from __future__ import annotations

import sys
from pathlib import Path

import pytest

from specsmith.benchmark_audit import audit_benchmark_rows

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from govern_bench import harness as harness_module  # noqa: E402
from govern_bench.harness import (  # noqa: E402
    NormalizedToolCall,
    _active_boundary_has_current_evidence,
    _active_tool_names,
    _build_active_tools,
    _build_focused_repair_tools,
    _exec_read_file_with_evidence,
    _exec_read_files_with_evidence,
    _exec_write_files,
    _focused_validator_repair_progress,
    _looks_like_nonterminal_narration,
    _milestone_contract,
    _milestone_progress,
    _next_incomplete_boundary_paths,
    _openai_sampling_params,
    _read_paths_from_calls,
    _record_written_evidence,
    _replace_adaptive_progress_message,
    _run_missing_completion_validators,
    _scope_contract,
    _scope_progress,
    _serialized_done_tool_call,
    _updated_serialized_action_count,
    _updated_unchanged_read_only_streak,
    _without_read_tools,
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


def test_missing_file_reads_are_versioned_absence_evidence(tmp_path: Path) -> None:
    evidence: dict[str, tuple[str, int]] = {}
    first, first_suppressed = _exec_read_file_with_evidence(
        tmp_path,
        "new_test.py",
        evidence,
        turn=2,
        compress_unchanged=True,
    )
    repeated, repeated_suppressed = _exec_read_file_with_evidence(
        tmp_path,
        "new_test.py",
        evidence,
        turn=3,
        compress_unchanged=True,
    )

    assert first.startswith("ERROR: file not found:")
    assert not first_suppressed
    assert repeated_suppressed
    assert "remains absent" in repeated


def test_successful_model_writes_become_known_evidence(tmp_path: Path) -> None:
    path = tmp_path / "component.py"
    path.write_text("VALUE = 2\n", encoding="utf-8")
    evidence: dict[str, tuple[str, int]] = {}

    _record_written_evidence(tmp_path, ["component.py"], evidence, turn=4)
    repeated, suppressed = _exec_read_file_with_evidence(
        tmp_path,
        "component.py",
        evidence,
        turn=5,
        compress_unchanged=True,
    )

    assert suppressed
    assert "prior read from turn 4" in repeated
    assert "VALUE = 2" not in repeated


def test_long_horizon_milestones_are_bounded_and_progress_replaces_history() -> None:
    task = get_task("T28")
    contract = _milestone_contract(task)
    tools = [
        tool["function"]["name"]
        for tool in _build_active_tools(
            "SPECSMITH_FULL",
            task,
            composite_files=task.is_long_horizon,
        )
    ]

    assert len(task.milestones) == 4
    assert "shared contract and API" in contract
    assert "interactive UI journey" in contract
    assert "no separate planning turn" in contract
    assert "read_file calls in one response" in contract
    assert "existing dependencies and standard libraries" in contract
    assert tools == ["write_files", "read_file", "write_file", "done"]
    assert "backend/main.py" in _milestone_progress(task, ["contracts/incident.schema.json"])
    assert "worker boundary" in _milestone_progress(
        task,
        [
            "contracts/incident.schema.json",
            "backend/main.py",
            "tests/test_backend.py",
        ],
    )
    worker_paths = ["worker/main.go", "worker/main_test.go"]
    assert (
        _next_incomplete_boundary_paths(
            task,
            [
                "contracts/incident.schema.json",
                "backend/main.py",
                "tests/test_backend.py",
            ],
        )
        == worker_paths
    )
    evidence = {path: ("digest", 1) for path in worker_paths}
    assert _active_boundary_has_current_evidence(
        task,
        [
            "contracts/incident.schema.json",
            "backend/main.py",
            "tests/test_backend.py",
        ],
        evidence,
    )
    evidence.pop("worker/main_test.go")
    assert not _active_boundary_has_current_evidence(
        task,
        [
            "contracts/incident.schema.json",
            "backend/main.py",
            "tests/test_backend.py",
        ],
        evidence,
    )

    messages = _replace_adaptive_progress_message([], "first")
    messages = _replace_adaptive_progress_message(messages, "second")
    assert len(messages) == 1
    assert messages[0]["content"].endswith("second")


def test_accepted_aee_work_starts_with_minimal_tools_and_bounded_scope() -> None:
    task = get_task("T1")
    active = _build_active_tools("SPECSMITH_FULL", task)
    initial = [tool["function"]["name"] for tool in active]
    diagnostic = [
        tool["function"]["name"]
        for tool in _build_active_tools("SPECSMITH_FULL", task, diagnostics_required=True)
    ]

    assert initial == ["read_file", "write_file", "done"]
    assert "run_command" not in _active_tool_names(active)
    assert not (_active_tool_names(_without_read_tools(active)) & {"read_file", "read_files"})
    repair_names = _active_tool_names(
        _build_focused_repair_tools(
            "SPECSMITH_FULL",
            task,
            composite_files=True,
            repair_written=True,
        )
    )
    assert repair_names == {"write_files", "write_file", "done"}
    assert {"list_files", "run_command", "ask_clarification"}.issubset(diagnostic)
    assert "app/main.py" in _scope_contract(task)
    assert "tests/test_main.py" in _scope_progress(task, ["app/main.py"])
    assert "call done" in _scope_progress(task, task.expected_files_changed)


def test_serialized_routes_receive_bounded_composite_file_tools(tmp_path: Path) -> None:
    task = get_task("T28")
    scalar_calls = [NormalizedToolCall(id="1", name="read_file", arguments="{}")]
    count = _updated_serialized_action_count(0, scalar_calls)
    count = _updated_serialized_action_count(
        count,
        [NormalizedToolCall(id="2", name="read_files", arguments="{}")],
    )
    count = _updated_serialized_action_count(count, scalar_calls)
    assert count == 2

    names = [
        tool["function"]["name"]
        for tool in _build_active_tools(
            "SPECSMITH_FULL",
            task,
            composite_files=True,
            composite_reads=True,
        )
    ]
    assert names == ["read_files", "write_files", "read_file", "write_file", "done"]

    written: list[str] = []
    output, successful = _exec_write_files(
        tmp_path,
        [
            {"path": "one.py", "content": "ONE = 1\n"},
            {"path": "two.py", "content": "TWO = 2\n"},
        ],
        written,
    )
    assert successful == ["one.py", "two.py"]
    assert written == successful
    assert output.count("OK:") == 2

    content, suppressed = _exec_read_files_with_evidence(
        tmp_path,
        successful,
        {},
        turn=3,
        compress_unchanged=True,
    )
    assert "## one.py" in content and "## two.py" in content
    assert suppressed == []
    assert _read_paths_from_calls(
        [
            NormalizedToolCall(
                id="read-many",
                name="read_files",
                arguments='{"paths":["one.py","two.py"]}',
            )
        ]
    ) == ["one.py", "two.py"]
    repeated_reads = [
        NormalizedToolCall(
            id="read-one",
            name="read_file",
            arguments='{"path":"one.py"}',
        )
    ]
    assert _updated_unchanged_read_only_streak(0, repeated_reads, ["one.py"]) == 1
    assert _updated_unchanged_read_only_streak(1, repeated_reads, ["one.py"]) == 2
    assert _updated_unchanged_read_only_streak(2, repeated_reads, []) == 0
    assert (
        _updated_unchanged_read_only_streak(
            2,
            [NormalizedToolCall(id="write", name="write_file", arguments="{}")],
            [],
        )
        == 0
    )

    focus = _focused_validator_repair_progress(
        task,
        [
            "ruff check . FAILED:\nui/src/App.tsx:20:1 lint failure",
            "python tools/validate_contract.py FAILED:\nmissing field",
            "python tools/validate_ui.py FAILED:\nmissing role selector",
        ],
    )
    assert "contracts/incident.schema.json" in focus
    assert "ui/src/App.tsx" in focus
    assert "ui/tests/incident-console.spec.ts" in focus
    assert "do not reread validator" in focus


def test_full_completion_applies_one_bounded_ruff_safe_fix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    lint_results = iter([(False, "fixable lint"), (True, "clean")])

    def fake_command(_root: Path, command: str) -> tuple[bool, str]:
        calls.append(command)
        if command == "ruff check .":
            return next(lint_results)
        if command == "ruff check . --fix":
            return True, "Fixed 1 error."
        return True, "passed"

    monkeypatch.setattr(harness_module, "_exec_run_command", fake_command)
    receipts: list[str] = []
    lint_ok, tests_ok, _validators, failures = _run_missing_completion_validators(
        tmp_path,
        get_task("T2"),
        False,
        False,
        set(),
        repair_receipts=receipts,
    )

    assert lint_ok and tests_ok and failures == []
    assert calls == [
        "ruff check .",
        "ruff format .",
        "ruff check . --fix",
        "ruff check .",
        "pytest",
    ]
    assert receipts and "formatting/default-safe fixes" in receipts[0]


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
        ("All four milestones have implementation evidence. Calling done.", True),
        ("The repair is ready to call done now.", True),
        ("The implementation and tests are complete.", False),
    ],
)
def test_nonterminal_narration_detection_is_narrow(content: str, expected: bool) -> None:
    assert _looks_like_nonterminal_narration(content) is expected


def test_serialized_done_recovery_requires_exact_schema_and_complete_scope() -> None:
    task = get_task("T28")
    complete_scope = list(task.expected_files_changed)
    payload = '{"explanation":"All requirement-linked work is complete.","refused":false}'

    recovered = _serialized_done_tool_call(payload, task, complete_scope, turn=17)

    assert recovered is not None
    assert recovered.id == "serialized-done-17"
    assert recovered.name == "done"
    assert _serialized_done_tool_call(payload, task, complete_scope[:-1], turn=17) is None
    assert (
        _serialized_done_tool_call(
            '{"explanation":"done","refused":false,"extra":true}',
            task,
            complete_scope,
            turn=17,
        )
        is None
    )
    assert (
        _serialized_done_tool_call(
            '{"explanation":"done","refused":true}',
            task,
            complete_scope,
            turn=17,
        )
        is None
    )


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


def test_audit_identifies_provider_tool_continuation_failure() -> None:
    failed = _audit_row(condition="SPECSMITH_FULL", passed=False)
    failed.update(
        {
            "stop_reason": "empty_response",
            "agent_transcript": [
                {
                    "role": "assistant",
                    "tool_calls": ["read_file"],
                    "tool_targets": ["read_file:contracts/incident.schema.json"],
                    "content": "",
                },
                {"role": "assistant", "tool_calls": [], "tool_targets": [], "content": ""},
                {"role": "assistant", "tool_calls": [], "tool_targets": [], "content": ""},
            ],
        }
    )

    report = audit_benchmark_rows([failed])
    weaknesses = {item.code: item for item in report.weaknesses}

    assert "tool_continuation_failure" in weaknesses
    assert "model-native tool protocol" in weaknesses["tool_continuation_failure"].recommendation
    assert report.next_experiment.action == "repair_and_rerun"
    assert "tool_continuation_failure" in report.next_experiment.evidence_codes


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


def test_open_frontier_candidates_have_verified_routes_pricing_and_tiers() -> None:
    registry = load_registry(_SCRIPTS_DIR / "govern_bench" / "models.yml")
    candidates = select(registry, groups={"open-frontier"})

    assert {candidate["label"] for candidate in candidates} == {
        "kimi-k2.7-code",
        "glm-5.2",
        "deepseek-v4-pro",
        "minimax-m3",
    }
    assert all(candidate["provider"] == "huggingface" for candidate in candidates)
    expected_costs = {
        "moonshotai/Kimi-K2.7-Code:deepinfra": 4.24,
        "zai-org/GLM-5.2:deepinfra": 3.93,
        "deepseek-ai/DeepSeek-V4-Pro:novita": 4.80,
        "MiniMaxAI/MiniMax-M3:novita": 1.50,
    }
    for candidate in candidates:
        model = candidate["model"]
        assert estimate_cost(model, 1_000_000, 1_000_000) == pytest.approx(expected_costs[model])
        assert model_tier(model) == "open-xl"


def test_gpt_oss_admission_uses_pinned_tool_route_and_exact_pricing() -> None:
    registry = load_registry(_SCRIPTS_DIR / "govern_bench" / "models.yml")
    candidates = select(registry, groups={"open"}, model_ids={"gpt-oss-120b"})

    assert candidates == [
        {
            "label": "gpt-oss-120b",
            "provider": "huggingface",
            "model": "openai/gpt-oss-120b:novita",
            "group": "open",
            "tier": "open-xl",
        }
    ]
    assert estimate_cost("openai/gpt-oss-120b:novita", 1_000_000, 1_000_000) == pytest.approx(0.30)
    assert model_tier("openai/gpt-oss-120b:novita") == "open-xl"
