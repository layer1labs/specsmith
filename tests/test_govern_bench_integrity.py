"""Regression tests for GovernanceBench result completeness (REQ-484 / TEST-510)."""

from __future__ import annotations

import io
import json
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
    _compact_completed_tool_exchange,
    _compact_superseded_read_history,
    _completion_gate,
    _copy_project_fixture,
    _exec_list_files,
    _exec_read_file,
    _exec_run_command,
    _exec_run_validator,
    _exec_write_file,
    _get_project_dir,
    _install_acceptance_oracle,
    _openai_completion_token_param,
    _openai_reasoning_params,
    _run_agent_loop,
    _run_governance_controller,
    _run_missing_completion_validators,
    _updated_validator_evidence,
    _updated_verification_evidence,
)
from govern_bench.metrics import estimate_cost, model_tier  # noqa: E402
from govern_bench.probe_models import (  # noqa: E402
    DEFAULT_PROBE_TIMEOUT_SECONDS,
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


def test_completed_write_compaction_keeps_tool_history_schema_valid() -> None:
    body = "VERY_SECRET_FILE_BODY\n"
    assistant = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "write-1",
                "type": "function",
                "function": {
                    "name": "write_file",
                    "arguments": '{"path":"main.py","content":"VERY_SECRET_FILE_BODY\\n"}',
                },
            },
            {
                "id": "read-1",
                "type": "function",
                "function": {"name": "read_file", "arguments": '{"path":"README.md"}'},
            },
        ],
    }
    calls = [
        NormalizedToolCall(
            id="write-1",
            name="write_file",
            arguments='{"path":"main.py","content":"VERY_SECRET_FILE_BODY\\n"}',
        ),
        NormalizedToolCall(
            id="read-1",
            name="read_file",
            arguments='{"path":"README.md"}',
        ),
    ]
    results = [
        {"role": "tool", "tool_call_id": "write-1", "content": "OK: wrote 22 bytes"},
        {"role": "tool", "tool_call_id": "read-1", "content": "README body"},
    ]

    history = _compact_completed_tool_exchange(assistant, calls, results)

    assert body.strip() not in str(history)
    assert history[0]["tool_calls"] == [assistant["tool_calls"][1]]
    assert history[1] == results[1]
    assert history[2]["role"] == "user"
    assert "main.py" in history[2]["content"]
    assert "requested_bytes=22" in history[2]["content"]
    assert "content_bytes" not in str(history)


def test_completed_composite_write_history_omits_every_file_body() -> None:
    bodies = ("FIRST_PRIVATE_BODY\n", "SECOND_PRIVATE_BODY\n")
    arguments = json.dumps(
        {
            "files": [
                {"path": "one.py", "content": bodies[0]},
                {"path": "two.py", "content": bodies[1]},
            ]
        }
    )
    assistant = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "write-many",
                "type": "function",
                "function": {"name": "write_files", "arguments": arguments},
            }
        ],
    }
    calls = [NormalizedToolCall(id="write-many", name="write_files", arguments=arguments)]
    results = [
        {
            "role": "tool",
            "tool_call_id": "write-many",
            "content": "OK: wrote 19 bytes\nOK: wrote 20 bytes",
        }
    ]

    history = _compact_completed_tool_exchange(assistant, calls, results)
    serialized = str(history)

    assert all(body.strip() not in serialized for body in bodies)
    assert "one.py" in serialized and "two.py" in serialized
    assert "requested_bytes=19" in serialized
    assert "requested_bytes=20" in serialized
    assert "write_files" not in serialized


def test_superseded_read_compaction_preserves_other_tool_linkage() -> None:
    messages = [
        {"role": "system", "content": "stable prefix"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "read-old",
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "arguments": '{"path":"./src/app.py"}',
                    },
                },
                {
                    "id": "read-keep",
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "arguments": '{"path":"README.md"}',
                    },
                },
                {
                    "id": "lint-keep",
                    "type": "function",
                    "function": {
                        "name": "run_command",
                        "arguments": '{"command":"ruff check ."}',
                    },
                },
            ],
        },
        {"role": "tool", "tool_call_id": "read-old", "content": "OBSOLETE_SECRET"},
        {"role": "tool", "tool_call_id": "read-keep", "content": "README body"},
        {"role": "tool", "tool_call_id": "lint-keep", "content": "All checks passed"},
    ]

    compacted = _compact_superseded_read_history(messages, ["src\\app.py"])
    serialized = str(compacted)

    assert "OBSOLETE_SECRET" not in serialized
    assert "read-old" not in serialized
    assert "README body" in serialized
    assert "All checks passed" in serialized
    assert [call["id"] for call in compacted[1]["tool_calls"]] == [
        "read-keep",
        "lint-keep",
    ]


def test_fully_superseded_composite_read_is_removed_but_partial_read_remains() -> None:
    messages = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "read-all-replaced",
                    "type": "function",
                    "function": {
                        "name": "read_files",
                        "arguments": '{"paths":["one.py","two.py"]}',
                    },
                },
                {
                    "id": "read-partial",
                    "type": "function",
                    "function": {
                        "name": "read_files",
                        "arguments": '{"paths":["two.py","README.md"]}',
                    },
                },
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "read-all-replaced",
            "content": "OBSOLETE_COMPOSITE_CONTENT",
        },
        {
            "role": "tool",
            "tool_call_id": "read-partial",
            "content": "MIXED_CURRENT_CONTENT",
        },
    ]

    compacted = _compact_superseded_read_history(messages, ["one.py", "two.py"])
    serialized = str(compacted)

    assert "OBSOLETE_COMPOSITE_CONTENT" not in serialized
    assert "read-all-replaced" not in serialized
    assert "MIXED_CURRENT_CONTENT" in serialized
    assert compacted[0]["tool_calls"][0]["id"] == "read-partial"


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
    qwen = _chat_probe_payload("Qwen/Qwen3-Coder-Next:novita")
    assert regular["max_tokens"] == 32
    assert regular["temperature"] == 0.2
    assert reasoning["max_completion_tokens"] == 32
    assert reasoning["reasoning_effort"] == "none"
    assert "temperature" not in reasoning
    assert qwen["temperature"] == 1.0
    assert qwen["top_p"] == 0.95
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
    framework_architecture = (
        "FastAPI Go React schema components. End-to-end flow and failures. " + "decision " * 95
    )
    assert has_architecture_record(framework_architecture)


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


def test_model_file_tools_hide_and_protect_controller_state(tmp_path: Path) -> None:
    state = tmp_path / ".specsmith"
    state.mkdir()
    requirement = state / "requirements.json"
    requirement.write_text('[{"id":"REQ-SECRET"}]', encoding="utf-8")

    assert ".specsmith" not in _exec_list_files(tmp_path)
    assert "not model-visible" in _exec_read_file(tmp_path, ".specsmith/requirements.json")
    assert "cannot be changed" in _exec_write_file(
        tmp_path,
        ".specsmith/requirements.json",
        "[]",
        [],
    )
    assert requirement.read_text(encoding="utf-8") == '[{"id":"REQ-SECRET"}]'


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


def test_long_horizon_final_validation_runs_public_boundaries_before_oracle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = get_task("T28")
    oracle_dir = tmp_path / ".governancebench_oracle"
    events: list[str] = []

    def fake_command(_root: Path, command: str) -> tuple[bool, str]:
        events.append(command)
        return True, command

    def fake_validator(_root: Path, _task: object, command: str) -> tuple[bool, str]:
        assert not oracle_dir.exists()
        events.append(command)
        return True, command

    def fake_install(_task: object, _root: Path) -> Path:
        events.append("install")
        oracle_dir.mkdir()
        return oracle_dir

    monkeypatch.setattr(harness_module, "_exec_run_command", fake_command)
    monkeypatch.setattr(harness_module, "_exec_run_validator", fake_validator)
    monkeypatch.setattr(harness_module, "_install_acceptance_oracle", fake_install)

    result = harness_module._run_standard_validation(task, tmp_path)

    assert result[0] and result[2] and result[4]
    assert events == [
        "ruff check .",
        "pytest",
        *task.allowed_validator_commands,
        "install",
        "pytest .governancebench_oracle",
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


def test_write_file_rejects_blank_overwrite_of_non_empty_file(tmp_path: Path) -> None:
    target = tmp_path / "result.txt"
    target.write_text("stable\n", encoding="utf-8")
    written: list[str] = []

    result = _exec_write_file(tmp_path, "result.txt", "\n", written)

    assert result.startswith("ERROR: refusing to replace non-empty file")
    assert target.read_text(encoding="utf-8") == "stable\n"
    assert written == []


def test_governance_tools_do_not_change_agent_capabilities() -> None:
    task = get_task("T1")
    raw_names = [tool["function"]["name"] for tool in _build_tools("UNGOVERNED", task)]
    full_names = [tool["function"]["name"] for tool in _build_tools("SPECSMITH_FULL", task)]
    assert full_names == raw_names
    assert not any(name.startswith("specsmith_") for name in full_names)


def test_full_prompt_delegates_initial_validation_to_controller() -> None:
    prompt = get_condition("SPECSMITH_FULL").system_prompt_template

    assert "validation is controller-owned" in prompt
    assert "run_command" not in prompt
    assert "run_validator" not in prompt
    assert "Repair any failures" in prompt


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
    assert "python tools/validate_contract.py" in instruction
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


def test_t28_visible_contract_validator_rejects_incomplete_starter(tmp_path: Path) -> None:
    task = get_task("T28")
    project = tmp_path / "project"
    _copy_project_fixture(_get_project_dir(task.project), project)

    passed, output = _exec_run_validator(
        project,
        task,
        "python tools/validate_contract.py",
    )

    assert not passed
    assert "Schema properties missing" in output
    assert "acknowledged_at" in output


def test_full_controller_runs_only_missing_completion_validators(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = get_task("T28")
    commands: list[str] = []

    def fake_standard(_root: Path, command: str) -> tuple[bool, str]:
        commands.append(command)
        return True, "passed"

    def fake_scoped(_root: Path, _task: object, command: str) -> tuple[bool, str]:
        commands.append(command)
        return True, "passed"

    monkeypatch.setattr(harness_module, "_exec_run_command", fake_standard)
    monkeypatch.setattr(harness_module, "_exec_run_validator", fake_scoped)
    existing = {task.allowed_validator_commands[0]}
    lint_ok, tests_ok, evidence, failures = _run_missing_completion_validators(
        tmp_path, task, True, False, existing
    )

    assert lint_ok and tests_ok
    assert failures == []
    assert commands == ["pytest", *task.allowed_validator_commands[1:]]
    assert evidence == set(task.allowed_validator_commands)


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


def test_agent_loop_replays_compact_valid_history_after_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = get_task("T1")
    project = tmp_path / "project"
    _copy_project_fixture(_get_project_dir(task.project), project)
    responses = iter(
        [
            NormalizedLLMResponse(
                message=NormalizedAssistantMessage(
                    tool_calls=[
                        NormalizedToolCall(
                            id="write-1",
                            name="write_file",
                            arguments=(
                                '{"path":"notes.txt","content":"VERY_SECRET_PROVIDER_BODY\\n"}'
                            ),
                        )
                    ]
                ),
                usage=NormalizedUsage(prompt_tokens=10, completion_tokens=1),
            ),
            NormalizedLLMResponse(
                message=NormalizedAssistantMessage(content="stop"),
                usage=NormalizedUsage(prompt_tokens=10, completion_tokens=1),
            ),
        ]
    )
    provider_histories: list[str] = []

    def fake_call(**kwargs: object) -> NormalizedLLMResponse:
        provider_histories.append(repr(kwargs["messages"]))  # type: ignore[index]
        return next(responses)

    monkeypatch.setattr(harness_module, "_call_llm", fake_call)
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
        max_turns=2,
    )

    assert result.stop_reason == "text_response"
    assert len(provider_histories) == 2
    assert "VERY_SECRET_PROVIDER_BODY" not in provider_histories[1]
    assert "Completed write_file state summary" in provider_histories[1]
    assert "content_bytes" not in provider_histories[1]


def test_agent_loop_drops_superseded_reads_after_successful_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = get_task("T1")
    project = tmp_path / "project"
    _copy_project_fixture(_get_project_dir(task.project), project)
    (project / "notes.txt").write_text("OBSOLETE_READ_BODY\n", encoding="utf-8")
    responses = iter(
        [
            NormalizedLLMResponse(
                message=NormalizedAssistantMessage(
                    tool_calls=[
                        NormalizedToolCall(
                            id="read-old",
                            name="read_file",
                            arguments='{"path":"notes.txt"}',
                        )
                    ]
                ),
                usage=NormalizedUsage(prompt_tokens=10, completion_tokens=1),
            ),
            NormalizedLLMResponse(
                message=NormalizedAssistantMessage(
                    tool_calls=[
                        NormalizedToolCall(
                            id="write-new",
                            name="write_file",
                            arguments='{"path":"notes.txt","content":"CURRENT_BODY\\n"}',
                        )
                    ]
                ),
                usage=NormalizedUsage(prompt_tokens=10, completion_tokens=1),
            ),
            NormalizedLLMResponse(
                message=NormalizedAssistantMessage(content="stop"),
                usage=NormalizedUsage(prompt_tokens=10, completion_tokens=1),
            ),
        ]
    )
    provider_histories: list[str] = []

    def fake_call(**kwargs: object) -> NormalizedLLMResponse:
        provider_histories.append(repr(kwargs["messages"]))  # type: ignore[index]
        return next(responses)

    monkeypatch.setattr(harness_module, "_call_llm", fake_call)
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
        max_turns=3,
    )

    assert result.stop_reason == "text_response"
    assert "OBSOLETE_READ_BODY" in provider_histories[1]
    assert "OBSOLETE_READ_BODY" not in provider_histories[2]
    assert "read-old" not in provider_histories[2]
    assert "Completed write_file state summary" in provider_histories[2]


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


def test_full_agent_loop_uses_public_equilibrium_and_runs_hidden_oracle_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import specsmith.governance_logic as governance_logic

    task = get_task("T1")
    project = tmp_path / "project"
    _copy_project_fixture(_get_project_dir(task.project), project)
    response = NormalizedLLMResponse(
        message=NormalizedAssistantMessage(
            tool_calls=[NormalizedToolCall(id="done-1", name="done", arguments="{}")]
        ),
        usage=NormalizedUsage(prompt_tokens=10, completion_tokens=1),
    )
    validation_calls = 0
    final_repair_checks = 0

    def fake_standard_validation(*_args: object) -> tuple[bool, str, bool, str, bool, str]:
        nonlocal validation_calls
        validation_calls += 1
        return True, "", True, "", True, ""

    def fake_final_repair(*_args: object, **kwargs: object) -> tuple[bool, str, str]:
        nonlocal final_repair_checks
        final_repair_checks += 1
        assert kwargs["phase"] == "final scoring"
        return True, "", ""

    monkeypatch.setattr(harness_module, "_call_llm", lambda **_kwargs: response)
    monkeypatch.setattr(harness_module, "_completion_gate", lambda *_args: (True, "done"))
    monkeypatch.setattr(
        harness_module,
        "_run_missing_completion_validators",
        lambda *_args, **_kwargs: (True, True, set(), []),
    )
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
    monkeypatch.setattr(harness_module, "_run_standard_validation", fake_standard_validation)
    monkeypatch.setattr(
        harness_module,
        "_run_ruff_with_bounded_safe_fix",
        fake_final_repair,
    )

    def fake_verify(*, test_results: dict, **_kwargs) -> dict:
        assert test_results == {"passed": 1, "failed": 0}
        return {
            "equilibrium": True,
            "confidence": 0.85,
            "retry_budget": 3,
            "retry_strategy": "",
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
        max_turns=2,
    )

    verification_events = [
        event["verify"] for event in result.agent_transcript if "verify" in event
    ]
    assert [event["equilibrium"] for event in verification_events] == [True]
    assert result.verify_result["equilibrium"] is True
    assert result.stop_reason == "done"
    assert result.llm_turns == 1
    assert result.rework_turns == 1
    assert validation_calls == 1
    assert final_repair_checks == 1


def test_full_repair_write_forces_controller_owned_revalidation(
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
                    tool_calls=[NormalizedToolCall(id="done-1", name="done", arguments="{}")]
                ),
                usage=NormalizedUsage(prompt_tokens=10, completion_tokens=1),
            ),
            NormalizedLLMResponse(
                message=NormalizedAssistantMessage(
                    tool_calls=[
                        NormalizedToolCall(
                            id="read-repair",
                            name="read_file",
                            arguments='{"path":"app/main.py"}',
                        )
                    ]
                ),
                usage=NormalizedUsage(prompt_tokens=10, completion_tokens=1),
            ),
            NormalizedLLMResponse(
                message=NormalizedAssistantMessage(
                    tool_calls=[
                        NormalizedToolCall(
                            id="write-repair",
                            name="write_file",
                            arguments='{"path":"app/main.py","content":"VALUE = 1\\n"}',
                        )
                    ]
                ),
                usage=NormalizedUsage(prompt_tokens=10, completion_tokens=1),
            ),
            NormalizedLLMResponse(
                message=NormalizedAssistantMessage(
                    tool_calls=[NormalizedToolCall(id="done-2", name="done", arguments="{}")]
                ),
                usage=NormalizedUsage(prompt_tokens=10, completion_tokens=1),
            ),
        ]
    )
    tool_surfaces: list[set[str]] = []

    def fake_call(**kwargs: object) -> NormalizedLLMResponse:
        tool_surfaces.append(
            {
                str(tool["function"]["name"])
                for tool in kwargs["tools"]  # type: ignore[index, union-attr]
            }
        )
        return next(responses)

    completion_checks = iter(
        [
            (False, True, set(), ["ruff check . FAILED:\nrepair app/main.py"]),
            (True, True, set(), []),
        ]
    )
    monkeypatch.setattr(harness_module, "_call_llm", fake_call)
    monkeypatch.setattr(
        harness_module,
        "_run_missing_completion_validators",
        lambda *_args, **_kwargs: next(completion_checks),
    )
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
        harness_module,
        "_run_ruff_with_bounded_safe_fix",
        lambda *_args, **_kwargs: (True, "", ""),
    )
    monkeypatch.setattr(
        harness_module,
        "_run_standard_validation",
        lambda *_args: (True, "", True, "", True, ""),
    )
    monkeypatch.setattr(
        governance_logic,
        "run_verify",
        lambda **_kwargs: {
            "equilibrium": True,
            "confidence": 0.85,
            "retry_budget": 3,
            "retry_strategy": "",
        },
    )

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

    assert result.stop_reason == "done"
    assert result.llm_turns == 4
    assert "read_file" in tool_surfaces[2]
    assert tool_surfaces[3] == {"write_files", "write_file", "done"}, (
        tool_surfaces,
        result.agent_transcript,
    )
    assert any(
        event.get("adaptive_tool_surface", {}).get("reason") == "repair_write_ready_for_validation"
        for event in result.agent_transcript
    )


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


def test_live_probe_timeout_allows_measured_tool_route_latency() -> None:
    assert DEFAULT_PROBE_TIMEOUT_SECONDS == 60.0
