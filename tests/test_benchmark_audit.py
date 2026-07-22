from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from specsmith.benchmark_audit import audit_benchmark_file, audit_benchmark_rows
from specsmith.cli import main

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def _row(
    *,
    condition: str,
    passed: bool,
    input_tokens: int,
    output_tokens: int = 100,
    tests_passed: bool = True,
    task: str = "T28",
    rep: int = 1,
    model: str = "gpt-5.6-sol",
    oracle_passed: bool | None = None,
) -> dict:
    return {
        "task": task,
        "condition": condition,
        "rep": rep,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "llm_turns": 4,
        "passed": passed,
        "tests_passed": tests_passed,
        "project_tests_passed": tests_passed,
        "acceptance_oracle_passed": passed if oracle_passed is None else oracle_passed,
        "skipped": False,
        "error": None,
    }


def test_audit_finds_acceptance_correctness_token_and_context_weaknesses() -> None:
    report = audit_benchmark_rows(
        [
            _row(condition="UNGOVERNED", passed=True, input_tokens=1_000),
            _row(condition="UNGOVERNED", passed=True, input_tokens=1_000, rep=2),
            _row(condition="SPECSMITH_FULL", passed=False, input_tokens=2_000),
            _row(condition="SPECSMITH_FULL", passed=True, input_tokens=2_000, rep=2),
        ]
    )
    codes = {item.code for item in report.weaknesses}

    assert report.complete
    assert report.high_or_critical == 2
    assert report.condition_metrics["SPECSMITH_FULL"]["tokens_per_correct_answer"] == 4_200
    assert {
        "undersampled",
        "acceptance_gap",
        "token_amplification",
        "correctness_regression",
        "context_dominance",
    } <= codes


def test_audit_fails_closed_on_missing_rows_and_bad_shape(tmp_path: Path) -> None:
    artifact = tmp_path / "results.json"
    artifact.write_text(
        json.dumps(
            [
                {
                    **_row(condition="UNGOVERNED", passed=False, input_tokens=0),
                    "skipped": True,
                    "error": "provider unavailable",
                }
            ]
        ),
        encoding="utf-8",
    )

    report = audit_benchmark_file(artifact)
    assert not report.complete
    assert report.valid_rows == 0
    assert report.weaknesses[0].code == "incomplete_evidence"

    with pytest.raises(ValueError, match="JSON list of objects"):
        audit_benchmark_rows(["not-a-row"])  # type: ignore[list-item]

    malformed_row = audit_benchmark_rows([{}])
    assert not malformed_row.complete
    assert malformed_row.weaknesses[0].code == "incomplete_evidence"

    zero_pass = audit_benchmark_rows(
        [_row(condition="SPECSMITH_FULL", passed=False, input_tokens=1_000)]
    )
    assert zero_pass.condition_metrics["SPECSMITH_FULL"]["tokens_per_correct_answer"] is None
    json.dumps(zero_pass.to_dict(), allow_nan=False)

    malformed_grid = audit_benchmark_rows(
        [
            _row(condition="UNGOVERNED", passed=True, input_tokens=100),
            _row(condition="UNGOVERNED", passed=True, input_tokens=100),
            _row(condition="SPECSMITH_LIGHT", passed=True, input_tokens=100),
        ]
    )
    malformed_codes = {item.code for item in malformed_grid.weaknesses}
    assert {"duplicate_cells", "uneven_repetitions"} <= malformed_codes

    missing_grid = audit_benchmark_rows(
        [
            _row(condition="UNGOVERNED", passed=True, input_tokens=100),
            _row(condition="SPECSMITH_FULL", passed=True, input_tokens=100),
            _row(
                condition="UNGOVERNED",
                passed=True,
                input_tokens=100,
                model="open-model",
            ),
        ]
    )
    assert not missing_grid.complete
    assert "missing_cells" in {item.code for item in missing_grid.weaknesses}


@pytest.mark.parametrize(
    "final_diff",
    [
        "--- a/a.txt\n+++ b/a.txt\n@@ -0,0 +1 @@\n+value--- a/b.txt\n",
        "--- a/a.txt\n+++ b/a.txt\n... [diff compacted]\n",
    ],
)
def test_audit_rejects_unreplayable_diff_evidence(final_diff: str) -> None:
    row = _row(condition="UNGOVERNED", passed=True, input_tokens=100)
    row["final_diff"] = final_diff

    report = audit_benchmark_rows([row])

    assert not report.complete
    weakness = next(item for item in report.weaknesses if item.code == "unreplayable_diff")
    assert weakness.severity == "critical"
    assert weakness.tasks == ["T28"]


def test_audit_reports_turn_tool_and_verification_exhaustion() -> None:
    max_turn = _row(condition="UNGOVERNED", passed=False, input_tokens=100)
    max_turn["stop_reason"] = "max_turns"
    repeated = _row(condition="SPECSMITH_LIGHT", passed=False, input_tokens=100)
    repeated["stop_reason"] = "repeated_tool_loop"
    repeated["agent_transcript"] = [
        {"role": "controller", "repeated_tool_target": "write_file:contract.json"}
    ]
    verify = _row(condition="SPECSMITH_FULL", passed=False, input_tokens=100)
    verify["stop_reason"] = "verification_exhausted"
    blank_write = _row(condition="CURSOR_RULES", passed=False, input_tokens=100)
    blank_write["agent_transcript"] = [
        {
            "role": "tool",
            "results": [
                "ERROR: refusing to replace non-empty file backend/main.py with blank content"
            ],
        }
    ]

    report = audit_benchmark_rows([max_turn, repeated, verify, blank_write])
    codes = {item.code for item in report.weaknesses}

    assert {
        "turn_budget_exhausted",
        "repeated_tool_loop",
        "verification_exhausted",
        "blank_overwrite_rejected",
    } <= codes


def test_default_run_bench_audit_path_tracks_json_output() -> None:
    from govern_bench.run_bench import _default_audit_path

    args = argparse.Namespace(
        audit_output=None,
        json_output="artifacts/bench-results.json",
        output="report.md",
    )
    assert _default_audit_path(args) == Path("artifacts/bench-results.audit.json")


def test_file_audit_infers_dry_run_provenance(tmp_path: Path) -> None:
    artifact = tmp_path / "dry.json"
    row = _row(condition="UNGOVERNED", passed=True, input_tokens=100)
    row["dry_run"] = True
    artifact.write_text(json.dumps([row]), encoding="utf-8")

    report = audit_benchmark_file(artifact)

    assert report.dry_run
    assert report.weaknesses[0].code == "synthetic_evidence"


def test_specsmith_audit_writes_combined_project_and_benchmark_report(tmp_path: Path) -> None:
    benchmark = tmp_path / "benchmark.json"
    benchmark.write_text(
        json.dumps(
            [
                _row(condition="UNGOVERNED", passed=True, input_tokens=1_000),
                _row(condition="SPECSMITH_FULL", passed=False, input_tokens=2_000),
            ]
        ),
        encoding="utf-8",
    )
    output = tmp_path / "audit.json"

    result = CliRunner().invoke(
        main,
        [
            "audit",
            "--project-dir",
            str(tmp_path),
            "--benchmark-results",
            str(benchmark),
            "--report",
            str(output),
        ],
        env={"SPECSMITH_ALLOW_NON_PIPX": "1", "SPECSMITH_NO_AUTO_UPDATE": "1"},
    )

    assert result.exit_code == 1
    assert "Benchmark outcome weaknesses" in result.output
    assert "acceptance_gap" in result.output
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["project"]["healthy"] is False
    assert payload["benchmark"]["high_or_critical"] == 2
