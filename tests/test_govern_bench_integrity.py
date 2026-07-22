"""Regression tests for GovernanceBench result completeness (REQ-484 / TEST-510)."""

from __future__ import annotations

import io
import runpy
import sys
import urllib.error
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import govern_bench.harness as harness_module  # noqa: E402
from govern_bench.compare_runs import (  # noqa: E402
    rollup,
    split_input_spec,
    validate_comparable,
    validate_results,
)
from govern_bench.conditions import get_condition  # noqa: E402
from govern_bench.harness import (  # noqa: E402
    NormalizedAssistantMessage,
    NormalizedLLMResponse,
    NormalizedToolCall,
    NormalizedUsage,
    _build_file_context,
    _build_project_diff,
    _build_tools,
    _call_openai_provider,
    _completion_gate,
    _copy_project_fixture,
    _exec_list_files,
    _exec_read_file,
    _exec_run_command,
    _exec_write_file,
    _get_project_dir,
    _install_acceptance_oracle,
    _openai_completion_token_param,
    _openai_reasoning_params,
    _run_agent_loop,
    _run_governance_controller,
    _updated_validator_evidence,
    _updated_verification_evidence,
)
from govern_bench.metrics import estimate_cost, model_tier  # noqa: E402
from govern_bench.probe_models import (  # noqa: E402
    _chat_probe_payload,
    _http_error_message,
    _probe_chat_endpoint,
)
from govern_bench.report import _task_list_label  # noqa: E402
from govern_bench.run_bench import _configure_console_output, incomplete_real_run  # noqa: E402
from govern_bench.tasks import get_task  # noqa: E402


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


def test_file_bodies_are_just_in_time_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "main.py").write_text("SECRET_EAGER_CONTEXT = True\n", encoding="utf-8")
    monkeypatch.delenv("BENCH_CONTEXT_BYTES", raising=False)

    assert _build_file_context(tmp_path, "main.py") == ""

    monkeypatch.setenv("BENCH_CONTEXT_BYTES", "100")
    assert "SECRET_EAGER_CONTEXT" in _build_file_context(tmp_path, "main.py")


def test_gpt56_openai_call_uses_stable_cache_key_and_records_cache_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    def create(**kwargs):
        captured.update(kwargs)
        usage = SimpleNamespace(
            prompt_tokens=100,
            completion_tokens=5,
            prompt_tokens_details=SimpleNamespace(
                cached_tokens=80,
                cache_write_tokens=10,
            ),
        )
        message = SimpleNamespace(content="done", tool_calls=[])
        return SimpleNamespace(usage=usage, choices=[SimpleNamespace(message=message)])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setenv("BENCH_PROMPT_CACHE_KEY", "governancebench:test")

    response = _call_openai_provider(
        "openai",
        client,
        "gpt-5.6-sol",
        [{"role": "user", "content": "repair"}],
        [],
    )

    assert captured["prompt_cache_key"] == "governancebench:test"
    assert response.usage.cached_tokens == 80
    assert response.usage.cache_write_tokens == 10


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


def test_comparison_rollup_reports_tokens_per_correct_answer() -> None:
    rows = [_row(rep=1), _row(rep=2)]
    rows[1]["passed"] = False
    stats = rollup(rows)["T1"]["UNGOVERNED"]
    assert stats["tokens_per_correct_answer"] == pytest.approx(200.0)


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


def test_windows_console_output_uses_replacement_errors() -> None:
    class LegacyConsole:
        errors: str | None = None

        def reconfigure(self, *, errors: str) -> None:
            self.errors = errors

    stream = LegacyConsole()
    _configure_console_output(stream)
    assert stream.errors == "replace"


def test_live_probe_requires_credential_without_network() -> None:
    result = _probe_chat_endpoint(
        "gpt-4o-mini",
        None,
        "https://api.openai.com/v1/chat/completions",
        1.0,
    )
    assert not result["ok"]
    assert "credential" in result["error"]


def test_probe_payload_matches_reasoning_and_tool_surfaces() -> None:
    regular = _chat_probe_payload("gpt-4o-mini")
    reasoning = _chat_probe_payload("gpt-5.6-sol")
    assert regular["max_tokens"] == 32
    assert regular["temperature"] == 0
    assert reasoning["max_completion_tokens"] == 32
    assert reasoning["reasoning_effort"] == "none"
    assert "temperature" not in reasoning
    assert regular["tools"][0]["function"]["name"] == "ping"


def test_probe_http_error_reports_only_bounded_provider_message() -> None:
    exc = urllib.error.HTTPError(
        "https://api.openai.com/v1/chat/completions",
        400,
        "Bad Request",
        {},
        io.BytesIO(b'{"error":{"message":"Unsupported parameter: max_completion_tokens"}}'),
    )
    message = _http_error_message(exc)
    assert message == "HTTP 400 Bad Request: Unsupported parameter: max_completion_tokens"
    assert "api.openai.com" not in message


def test_current_model_pricing_and_tiers() -> None:
    assert estimate_cost("gpt-5.6-luna", 1_000_000, 1_000_000) == 7.0
    assert estimate_cost("gpt-5.6-terra", 1_000_000, 1_000_000) == 17.5
    assert estimate_cost("gpt-5.6-sol", 1_000_000, 1_000_000) == 35.0
    assert estimate_cost("Qwen/Qwen3.6-35B-A3B:scaleway", 1_000_000, 1_000_000) == pytest.approx(
        1.995
    )
    assert model_tier("gpt-5.6-luna") == "mini"
    assert model_tier("gpt-5.6-terra") == "mid"
    assert model_tier("gpt-5.6-sol") == "frontier"
    assert model_tier("Qwen/Qwen3.6-35B-A3B:scaleway") == "open-mid"


def test_safety_oracles_are_hidden_from_agents() -> None:
    for task_id in ("T6", "T7"):
        task = get_task(task_id)
        assert task.acceptance_criteria
        assert task.visible_acceptance_criteria == ""


@pytest.mark.parametrize("task_id", ["T1", "T2", "T10", "T11", "T13", "T28"])
def test_default_coding_task_oracle_rejects_clean_noop(tmp_path: Path, task_id: str) -> None:
    task = get_task(task_id)
    project_root = tmp_path / "project"
    _copy_project_fixture(_get_project_dir(task.project), project_root)
    oracle_dir = _install_acceptance_oracle(task, project_root)

    assert oracle_dir.is_dir()
    passed, output = _exec_run_command(project_root, "pytest .governancebench_oracle")
    assert not passed, f"{task_id} clean fixture unexpectedly satisfied its oracle:\n{output}"


def test_long_horizon_task_has_polyglot_ui_scope_and_extended_turn_budget() -> None:
    task = get_task("T28")

    assert task.is_long_horizon
    assert task.max_turns == 20
    assert task.enforce_completion_validators
    assert {"python", "go", "typescript", "json-schema", "css"} <= set(task.languages)
    assert task.project_subdir == "incident_console"
    project = _get_project_dir(task.project)
    assert (project / "backend" / "main.py").is_file()
    assert (project / "worker" / "main.go").is_file()
    assert (project / "ui" / "src" / "App.tsx").is_file()


def test_t28_oracle_accepts_equivalent_schema_and_empty_state_forms(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fastapi_module = ModuleType("fastapi")
    testclient_module = ModuleType("fastapi.testclient")
    testclient_module.TestClient = object  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "fastapi", fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.testclient", testclient_module)
    oracle = runpy.run_path(
        str(_SCRIPTS_DIR / "govern_bench" / "oracles" / "T28" / "test_acceptance.py")
    )
    allows_null = oracle["_allows_null"]
    has_empty_state = oracle["_has_empty_state"]
    has_architecture_record = oracle["_has_architecture_record"]

    assert allows_null({"type": ["string", "null"]})
    assert allows_null({"anyOf": [{"type": "string"}, {"type": "null"}]})
    assert allows_null({"oneOf": [{"type": "string"}, {"type": "null"}]})
    assert not allows_null({"type": "string"})
    assert has_empty_state("incidents.length === 0 && <p>No incidents found.</p>")
    assert has_empty_state("return <EmptyState />")
    assert not has_empty_state("return incidents.map(renderIncident)")
    equivalent_architecture = (
        "Python Go React schema data flow process-local state. " + "decision " * 95
    )
    assert has_architecture_record(equivalent_architecture)
    end_to_end_architecture = (
        "Python Go React schema components. End-to-end flow and failures. " + "decision " * 95
    )
    assert has_architecture_record(end_to_end_architecture)


def test_comparison_workflow_excludes_audit_json_objects() -> None:
    workflow = (_SCRIPTS_DIR.parent / ".github" / "workflows" / "bench.yml").read_text(
        encoding="utf-8"
    )
    assert '[[ "$file" == *.audit.json ]] || FILES+=("$file")' in workflow


def test_standard_task_without_oracle_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="No evaluator-only acceptance oracle"):
        _install_acceptance_oracle(get_task("T3"), tmp_path)


def test_validation_commands_do_not_create_cache_artifacts(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _copy_project_fixture(_get_project_dir("agentic-todo-api"), project_root)
    _exec_run_command(project_root, "pytest")
    _exec_run_command(project_root, "ruff check .")
    assert not (project_root / ".pytest_cache").exists()
    assert not (project_root / ".ruff_cache").exists()


def test_file_tools_return_safe_errors_for_directories_and_malformed_paths(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    files_written: list[str] = []

    assert _exec_read_file(project_root, ".").startswith("ERROR: path is not a file")
    assert _exec_write_file(project_root, ".", "content", files_written).startswith(
        "ERROR: path is not a file"
    )
    assert _exec_read_file(project_root, "\x00").startswith("ERROR:")
    assert _exec_list_files(project_root, "\x00").startswith("ERROR:")
    assert files_written == []


def test_file_tools_reject_prefix_collision_traversal(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    sibling = tmp_path / "project-escape"
    project_root.mkdir()
    sibling.mkdir()
    (sibling / "secret.txt").write_text("secret", encoding="utf-8")
    traversal = "../project-escape/secret.txt"

    assert _exec_read_file(project_root, traversal) == "ERROR: path traversal denied"
    assert _exec_write_file(project_root, traversal, "changed", []) == (
        "ERROR: path traversal denied"
    )
    assert _exec_list_files(project_root, "../project-escape") == "ERROR: path traversal denied"
    assert (sibling / "secret.txt").read_text(encoding="utf-8") == "secret"


def test_standard_validation_isolates_hidden_oracle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    oracle_dir = project_root / ".governancebench_oracle"
    events: list[tuple[str, bool]] = []

    def fake_run_command(root: Path, command: str) -> tuple[bool, str]:
        assert root == project_root
        events.append((command, oracle_dir.exists()))
        return True, command

    def fake_install(task: object, root: Path) -> Path:
        assert task == get_task("T1")
        assert root == project_root
        events.append(("install", oracle_dir.exists()))
        oracle_dir.mkdir()
        return oracle_dir

    monkeypatch.setattr(harness_module, "_exec_run_command", fake_run_command)
    monkeypatch.setattr(harness_module, "_install_acceptance_oracle", fake_install)

    result = harness_module._run_standard_validation(get_task("T1"), project_root)

    assert result == (True, "ruff check .", True, "pytest", True, "pytest .governancebench_oracle")
    assert events == [
        ("ruff check .", False),
        ("pytest", False),
        ("install", False),
        ("pytest .governancebench_oracle", True),
    ]
    assert not oracle_dir.exists()


def test_project_diff_excludes_evaluator_and_cache_artifacts(tmp_path: Path) -> None:
    source = tmp_path / "source"
    project = tmp_path / "project"
    source.mkdir()
    project.mkdir()
    (source / "app.py").write_text("before\n", encoding="utf-8")
    (project / "app.py").write_text("after\n", encoding="utf-8")
    for root in (source, project):
        for directory in (".pytest_cache", ".ruff_cache", "__pycache__"):
            cache_dir = root / directory
            cache_dir.mkdir()
            (cache_dir / "artifact").write_text(str(root), encoding="utf-8")
    oracle_dir = project / ".governancebench_oracle"
    oracle_dir.mkdir()
    (oracle_dir / "test_acceptance.py").write_text("assert False\n", encoding="utf-8")

    diff = _build_project_diff(source, project)
    assert "app.py" in diff
    assert "artifact" not in diff
    assert "governancebench_oracle" not in diff


def test_project_diff_keeps_no_newline_files_replayable(tmp_path: Path) -> None:
    source = tmp_path / "source"
    project = tmp_path / "project"
    source.mkdir()
    project.mkdir()
    (project / "a.txt").write_text("first", encoding="utf-8")
    (project / "b.txt").write_text("second\n", encoding="utf-8")

    diff = _build_project_diff(source, project)

    assert "+first\n\\ No newline at end of file\n--- a/b.txt\n" in diff


def test_write_file_reports_identical_content_as_noop(tmp_path: Path) -> None:
    written: list[str] = []
    first = _exec_write_file(tmp_path, "result.txt", "stable\n", written)
    second = _exec_write_file(tmp_path, "result.txt", "stable\n", written)

    assert first.startswith("OK:")
    assert second.startswith("NO-OP:")
    assert written == ["result.txt"]


def test_governance_tools_do_not_change_agent_capabilities() -> None:
    task = get_task("T1")
    raw_names = [tool["function"]["name"] for tool in _build_tools("UNGOVERNED", task)]
    full_names = [tool["function"]["name"] for tool in _build_tools("SPECSMITH_FULL", task)]
    assert full_names == raw_names
    assert not any(name.startswith("specsmith_") for name in full_names)


def test_full_completion_gate_requires_fresh_lint_and_test_evidence() -> None:
    task = get_task("T1")
    accepted, instruction = _completion_gate("SPECSMITH_FULL", task, False, False)
    assert not accepted
    assert "ruff check ." in instruction
    assert "pytest" in instruction

    lint_ok, tests_ok = _updated_verification_evidence(
        "ruff check . && pytest",
        True,
        False,
        False,
    )
    assert (lint_ok, tests_ok) == (True, True)
    assert _completion_gate("SPECSMITH_FULL", task, lint_ok, tests_ok)[0]


def test_long_horizon_full_gate_requires_fresh_polyglot_validators() -> None:
    task = get_task("T28")
    accepted, instruction = _completion_gate("SPECSMITH_FULL", task, True, True, set())
    assert not accepted
    assert "go -C worker test ./..." in instruction
    assert "python tools/validate_ui.py" in instruction

    evidence: set[str] = set()
    for command in task.allowed_validator_commands:
        evidence = _updated_validator_evidence(command, True, evidence)
    assert _completion_gate("SPECSMITH_FULL", task, True, True, evidence)[0]

    evidence = _updated_validator_evidence(
        "python tools/validate_ui.py",
        False,
        evidence,
    )
    assert not _completion_gate("SPECSMITH_FULL", task, True, True, evidence)[0]


def test_completion_gate_does_not_advantage_non_full_conditions() -> None:
    task = get_task("T1")
    assert _completion_gate("CURSOR_RULES", task, False, False)[0]
    assert _completion_gate("SPECSMITH_LIGHT", task, False, False)[0]


def test_failed_check_invalidates_only_its_evidence() -> None:
    evidence = _updated_verification_evidence("ruff check .", False, True, True)
    assert evidence == (False, True)
    evidence = _updated_verification_evidence("pytest", False, True, True)
    assert evidence == (True, False)


def test_agent_loop_recovers_once_from_empty_provider_response(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = get_task("T1")
    project = tmp_path / "project"
    _copy_project_fixture(_get_project_dir(task.project), project)
    responses = iter(
        [
            NormalizedLLMResponse(
                message=NormalizedAssistantMessage(),
                usage=NormalizedUsage(prompt_tokens=10),
            ),
            NormalizedLLMResponse(
                message=NormalizedAssistantMessage(
                    tool_calls=[NormalizedToolCall(id="done-1", name="done", arguments="{}")]
                ),
                usage=NormalizedUsage(prompt_tokens=10, completion_tokens=1),
            ),
        ]
    )
    monkeypatch.setattr(harness_module, "_call_llm", lambda **_kwargs: next(responses))

    result = _run_agent_loop(
        provider="openai",
        client=object(),
        model="test-model",
        task=task,
        condition=get_condition("UNGOVERNED"),
        project_root=project,
        specsmith_dir=tmp_path,
        max_turns=3,
    )

    assert result.llm_turns == 2
    assert result.stop_reason == "done"
    assert result.rework_turns == 2
    assert any("recovery" in event for event in result.agent_transcript)


def test_agent_loop_stops_repeated_single_file_write_loop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = get_task("T1")
    project = tmp_path / "project"
    _copy_project_fixture(_get_project_dir(task.project), project)
    repeated = NormalizedLLMResponse(
        message=NormalizedAssistantMessage(
            tool_calls=[
                NormalizedToolCall(
                    id="write-repeat",
                    name="write_file",
                    arguments='{"path":"notes.txt","content":"same\\n"}',
                )
            ]
        ),
        usage=NormalizedUsage(prompt_tokens=10, completion_tokens=1),
    )
    monkeypatch.setattr(harness_module, "_call_llm", lambda **_kwargs: repeated)
    monkeypatch.setattr(
        harness_module,
        "_run_standard_validation",
        lambda *_args: (True, "", True, "", False, "hidden failure"),
    )

    result = _run_agent_loop(
        provider="openai",
        client=object(),
        model="test-model",
        task=task,
        condition=get_condition("UNGOVERNED"),
        project_root=project,
        specsmith_dir=tmp_path,
        max_turns=10,
    )

    assert result.stop_reason == "repeated_tool_loop"
    assert result.llm_turns == 4
    assert any(event.get("repeated_tool_target") for event in result.agent_transcript)


def test_full_agent_loop_retries_until_independent_equilibrium(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import specsmith.governance_logic as governance_logic

    task = get_task("T1")
    project = tmp_path / "project"
    _copy_project_fixture(_get_project_dir(task.project), project)
    responses = iter(
        [
            NormalizedLLMResponse(
                message=NormalizedAssistantMessage(
                    tool_calls=[NormalizedToolCall(id=f"done-{index}", name="done", arguments="{}")]
                ),
                usage=NormalizedUsage(prompt_tokens=10, completion_tokens=1),
            )
            for index in (1, 2)
        ]
    )
    validations = iter(
        [
            (True, "", True, "", False, "hidden failure"),
            (True, "", True, "", True, ""),
            (True, "", True, "", True, ""),
        ]
    )
    monkeypatch.setattr(harness_module, "_call_llm", lambda **_kwargs: next(responses))
    monkeypatch.setattr(harness_module, "_completion_gate", lambda *_args: (True, "done"))
    monkeypatch.setattr(
        harness_module,
        "_run_governance_controller",
        lambda *_args: {
            "decision": "accepted",
            "work_item_id": "WI-TEST",
            "requirement_ids": ["REQ-BENCH-001"],
            "test_case_ids": ["TEST-BENCH-001"],
        },
    )
    monkeypatch.setattr(
        harness_module, "_run_standard_validation", lambda *_args: next(validations)
    )

    def fake_verify(*, test_results: dict, **_kwargs) -> dict:
        equilibrium = test_results["failed"] == 0
        return {
            "equilibrium": equilibrium,
            "confidence": 0.85 if equilibrium else 0.4,
            "retry_budget": 3,
            "retry_strategy": "" if equilibrium else "fix_tests",
        }

    monkeypatch.setattr(governance_logic, "run_verify", fake_verify)

    result = _run_agent_loop(
        provider="openai",
        client=object(),
        model="test-model",
        task=task,
        condition=get_condition("SPECSMITH_FULL"),
        project_root=project,
        specsmith_dir=tmp_path,
        max_turns=4,
    )

    verification_events = [
        event["verify"] for event in result.agent_transcript if "verify" in event
    ]
    assert [event["equilibrium"] for event in verification_events] == [False, True]
    assert result.verify_result["equilibrium"] is True
    assert result.stop_reason == "done"
    assert result.llm_turns == 2
    assert result.rework_turns == 2


def test_isolated_controller_accepts_scoped_task(tmp_path: Path) -> None:
    result = _run_governance_controller(get_task("T1"), tmp_path)
    assert result["decision"] == "accepted"
    assert result["requirement_ids"] == ["REQ-BENCH-001"]
    assert result["test_case_ids"] == ["TEST-BENCH-001"]
    assert (tmp_path / ".specsmith" / "requirements.json").is_file()


@pytest.mark.parametrize("task_id", ["T6", "T7"])
def test_controller_short_circuits_safety_without_llm(tmp_path: Path, task_id: str) -> None:
    result = _run_agent_loop(
        provider="openai",
        client=object(),
        model="gpt-4o-mini",
        task=get_task(task_id),
        condition=get_condition("SPECSMITH_FULL"),
        project_root=tmp_path,
        specsmith_dir=tmp_path,
        max_turns=1,
    )
    assert result.passed
    assert result.llm_turns == 0
    assert result.input_tokens == 0
    assert result.stop_reason == "governance_short_circuit"
    assert result.governance_decision["decision"] == "needs_clarification"


def test_reasoning_completion_budget_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BENCH_MAX_COMPLETION_TOKENS", raising=False)
    assert _openai_completion_token_param("gpt-5.4") == {"max_completion_tokens": 16_384}
    monkeypatch.setenv("BENCH_MAX_COMPLETION_TOKENS", "999999")
    assert _openai_completion_token_param("o3") == {"max_completion_tokens": 32_768}
    assert _openai_completion_token_param("gpt-4o-mini") == {"max_tokens": 4096}
    assert _openai_reasoning_params("gpt-5.6-sol") == {"reasoning_effort": "none"}
    assert _openai_reasoning_params("gpt-5.4") == {}


def test_report_lists_non_contiguous_task_ids_exactly() -> None:
    tasks = [get_task(task_id) for task_id in ("T1", "T2", "T6", "T7", "T10", "T11", "T13")]
    assert _task_list_label(tasks) == "T1, T2, T6, T7, T10, T11, T13"
