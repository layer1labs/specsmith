"""Regression tests for GovernanceBench result completeness (REQ-484 / TEST-510)."""

from __future__ import annotations

import io
import sys
import urllib.error
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from govern_bench.compare_runs import (  # noqa: E402
    rollup,
    split_input_spec,
    validate_comparable,
    validate_results,
)
from govern_bench.conditions import get_condition  # noqa: E402
from govern_bench.harness import (  # noqa: E402
    _build_project_diff,
    _build_tools,
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
    _updated_verification_evidence,
)
from govern_bench.metrics import estimate_cost, model_tier  # noqa: E402
from govern_bench.probe_models import (  # noqa: E402
    _chat_probe_payload,
    _http_error_message,
    _probe_chat_endpoint,
)
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


@pytest.mark.parametrize("task_id", ["T1", "T2", "T10", "T11", "T13"])
def test_default_coding_task_oracle_rejects_clean_noop(tmp_path: Path, task_id: str) -> None:
    task = get_task(task_id)
    project_root = tmp_path / "project"
    _copy_project_fixture(_get_project_dir(task.project), project_root)
    oracle_dir = _install_acceptance_oracle(task, project_root)

    assert oracle_dir.is_dir()
    passed, output = _exec_run_command(project_root, "pytest .governancebench_oracle")
    assert not passed, f"{task_id} clean fixture unexpectedly satisfied its oracle:\n{output}"


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


def test_completion_gate_does_not_advantage_non_full_conditions() -> None:
    task = get_task("T1")
    assert _completion_gate("CURSOR_RULES", task, False, False)[0]
    assert _completion_gate("SPECSMITH_LIGHT", task, False, False)[0]


def test_failed_check_invalidates_only_its_evidence() -> None:
    evidence = _updated_verification_evidence("ruff check .", False, True, True)
    assert evidence == (False, True)
    evidence = _updated_verification_evidence("pytest", False, True, True)
    assert evidence == (True, False)


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
