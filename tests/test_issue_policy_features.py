from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from specsmith.cli import main
from specsmith.dashboard import build_dashboard
from specsmith.governed_pr import evaluate_governed_pr
from specsmith.plugins import validate_plugin_manifest
from specsmith.policy import load_policy, simulate_policy_for_work_item
from specsmith.recover import recover_state
from specsmith.transcripts import import_transcript_json, normalize_transcript_payload
from specsmith.wi_store import WorkItemStore


def _seed_project(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (tmp_path / "LEDGER.md").write_text("# Ledger\n", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "REQUIREMENTS.md").write_text("# Requirements\n", encoding="utf-8")
    (docs / "TESTS.md").write_text("# Tests\n", encoding="utf-8")
    (docs / "ARCHITECTURE.md").write_text("# Architecture\n", encoding="utf-8")
    (tmp_path / "scaffold.yml").write_text(
        "name: test\ntype: cli-python\nspec_version: 0.11.6\nvcs_platform: github\n",
        encoding="utf-8",
    )


def test_normalize_transcript_payload() -> None:
    payload = [{"action": "read", "path": "a.txt"}, {"action": "retry", "retries": 2}]
    actions = normalize_transcript_payload(payload, "WI-1")
    assert actions[0]["action_type"] == "read_file"
    assert actions[1]["action_type"] == "retry"
    assert actions[1]["retry_count"] == 2


def test_import_transcript_json(tmp_path: Path) -> None:
    transcript = tmp_path / "transcript.json"
    transcript.write_text(json.dumps([{"action": "write_file", "path": "x.py"}]), encoding="utf-8")
    actions = import_transcript_json(tmp_path, transcript, "WI-TRANSCRIPT")
    assert len(actions) == 1
    out = (tmp_path / ".specsmith" / "transcripts.jsonl").read_text(encoding="utf-8")
    assert "WI-TRANSCRIPT" in out


def test_policy_load_and_simulate(tmp_path: Path) -> None:
    _seed_project(tmp_path)
    policy_path = tmp_path / ".specsmith" / "policy.yml"
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(
        "required_tests: true\nrequired_human_approval:\n  - implementation\n",
        encoding="utf-8",
    )
    store = WorkItemStore(tmp_path)
    item = store.create(
        "WI-POLICY01", intent="test policy", requirement_ids=["REQ-1"], test_case_ids=[]
    )
    policy, errors = load_policy(tmp_path)
    assert errors == []
    assert policy.required_tests
    sim = simulate_policy_for_work_item(tmp_path, item)
    assert any("linked tests" in issue for issue in sim["blocking_issues"])
    assert any("implementation" in issue for issue in sim["blocking_issues"])


def test_approve_command_and_policy_simulate_cli(tmp_path: Path) -> None:
    _seed_project(tmp_path)
    store = WorkItemStore(tmp_path)
    store.create(
        "WI-APPROVE01", intent="needs approval", requirement_ids=["REQ-1"], test_case_ids=["TEST-1"]
    )
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "approve",
            "implementation",
            "--work-item",
            "WI-APPROVE01",
            "--rationale",
            "Reviewed implementation",
            "--project-dir",
            str(tmp_path),
        ],
        env={"SPECSMITH_ALLOW_NON_PIPX": "1"},
    )
    assert result.exit_code == 0
    sim = runner.invoke(
        main,
        [
            "policy",
            "simulate",
            "--work-item",
            "WI-APPROVE01",
            "--project-dir",
            str(tmp_path),
            "--json",
        ],
        env={"SPECSMITH_ALLOW_NON_PIPX": "1"},
    )
    assert sim.exit_code == 0
    payload = json.loads(sim.output)
    assert payload["work_item_id"] == "WI-APPROVE01"


def test_plugin_manifest_validation() -> None:
    manifest = Path("examples/plugins/example-verifier/specsmith.plugin.yml")
    errors = validate_plugin_manifest(manifest)
    assert errors == []


def test_plugin_validate_cli(tmp_path: Path) -> None:
    runner = CliRunner()
    manifest = Path("examples/plugins/example-verifier/specsmith.plugin.yml").resolve()
    result = runner.invoke(
        main,
        ["plugin", "validate", str(manifest), "--json"],
        env={"SPECSMITH_ALLOW_NON_PIPX": "1"},
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["valid"] is True


def test_governed_pr_evaluation(tmp_path: Path) -> None:
    _seed_project(tmp_path)
    store = WorkItemStore(tmp_path)
    item = store.create(
        "WI-PR01",
        intent="governed pr",
        requirement_ids=["REQ-1"],
        test_case_ids=["TEST-1"],
    )
    item.verified = True
    store.upsert(item)
    status = evaluate_governed_pr(tmp_path, "WI-PR01")
    assert status["linked_work_item"] is True
    assert status["linked_requirement"] is True


def test_recover_state(tmp_path: Path) -> None:
    _seed_project(tmp_path)
    store = WorkItemStore(tmp_path)
    store.create(
        "WI-RECOVER01", intent="recover me", requirement_ids=["REQ-1"], test_case_ids=["TEST-1"]
    )
    tests = tmp_path / "test_results.json"
    tests.write_text('{"failed": 2, "errors": 0}', encoding="utf-8")
    summary = recover_state(tmp_path, "WI-RECOVER01", git_diff="a\nb", test_results_path=tests)
    assert summary["failed_step"] == "verification"
    assert summary["test_failures"] == 2
    log_path = tmp_path / ".specsmith" / "recovery-log.jsonl"
    assert log_path.is_file()


def test_dashboard_build(tmp_path: Path) -> None:
    _seed_project(tmp_path)
    store = WorkItemStore(tmp_path)
    store.create(
        "WI-DASH01", intent="dashboard", requirement_ids=["REQ-1"], test_case_ids=["TEST-1"]
    )
    out = build_dashboard(tmp_path, tmp_path / "dash")
    text = out.read_text(encoding="utf-8").lower()
    assert "<html" in text
    assert "open work items" in text
    assert "risk levels" in text
    assert "traceability score" in text
