# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Coverage for newly added reporting/import-export governance commands."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from click.testing import CliRunner

from specsmith.cli import main


def _invoke(args: list[str]):
    runner = CliRunner()
    return runner.invoke(
        main,
        args,
        env={
            "SPECSMITH_NO_AUTO_UPDATE": "1",
            "SPECSMITH_PYPI_CHECKED": "1",
            "SPECSMITH_ALLOW_NON_PIPX": "1",
        },
        catch_exceptions=False,
    )


def test_quickstart_non_interactive_creates_state(tmp_path: Path) -> None:
    result = _invoke(
        [
            "quickstart",
            "--project-dir",
            str(tmp_path),
            "--project-type",
            "python-cli",
            "--mode",
            "lite",
            "--no-interactive",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Running doctor automatically" in result.output
    assert (tmp_path / ".specsmith" / "quickstart.json").exists()
    assert (tmp_path / "docs" / "REQUIREMENTS.md").exists()
    assert (tmp_path / "docs" / "TESTS.md").exists()


def test_expand_to_regulated_creates_governance_files(tmp_path: Path) -> None:
    _invoke(
        [
            "quickstart",
            "--project-dir",
            str(tmp_path),
            "--project-type",
            "python-cli",
            "--mode",
            "lite",
            "--no-interactive",
        ],
    )
    result = _invoke(["expand", "--project-dir", str(tmp_path), "--to", "regulated"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "docs" / "governance" / "RULES.md").exists()
    assert (tmp_path / "docs" / "governance" / "DRIFT-METRICS.md").exists()


def test_import_spec_kit_dry_run_reports_without_writing(tmp_path: Path) -> None:
    (tmp_path / "specs").mkdir(parents=True)
    (tmp_path / "specs" / "alpha.md").write_text(
        "# Alpha\n\nREQ-SPEC-001\n\nTEST-SPEC-001\n",
        encoding="utf-8",
    )
    result = _invoke(
        [
            "import",
            "spec-kit",
            "--project-dir",
            str(tmp_path),
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["dry_run"] is True
    assert not (tmp_path / ".specsmith" / "requirements.json").exists()


def test_import_bmad_writes_mappings_and_report(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "bmad-notes.md").write_text("REQ-BMAD-001\n", encoding="utf-8")
    result = _invoke(
        ["import", "bmad", "--project-dir", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / ".specsmith" / "requirements.json").exists()
    assert (tmp_path / ".specsmith" / "testcases.json").exists()
    assert (tmp_path / ".specsmith" / "import-report-bmad.json").exists()


def test_export_json_and_evidence_pack(tmp_path: Path) -> None:
    (tmp_path / ".specsmith").mkdir()
    (tmp_path / ".specsmith" / "requirements.json").write_text(
        json.dumps([{"id": "REQ-1", "title": "A"}]),
        encoding="utf-8",
    )
    (tmp_path / ".specsmith" / "testcases.json").write_text(
        json.dumps([{"id": "TEST-1", "requirement_id": "REQ-1"}]),
        encoding="utf-8",
    )
    (tmp_path / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (tmp_path / "LEDGER.md").write_text("# LEDGER\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "REQUIREMENTS.md").write_text("# R\n", encoding="utf-8")
    (tmp_path / "docs" / "TESTS.md").write_text("# T\n", encoding="utf-8")

    json_out = tmp_path / "out.json"
    zip_out = tmp_path / "pack.zip"
    result_json = _invoke(
        ["export", "json", "--project-dir", str(tmp_path), "--out", str(json_out)],
    )
    assert result_json.exit_code == 0, result_json.output
    assert json_out.exists()

    result_zip = _invoke(
        ["export", "evidence-pack", "--project-dir", str(tmp_path), "--out", str(zip_out)],
    )
    assert result_zip.exit_code == 0, result_zip.output
    assert zip_out.exists()
    with zipfile.ZipFile(zip_out) as archive:
        names = set(archive.namelist())
    assert ".specsmith/requirements.json" in names


def test_github_issue_plan_and_create_dry_run(tmp_path: Path) -> None:
    issue_md = tmp_path / "issues.md"
    issue_md.write_text("# Plan\n\n- [ ] Drift fix\n- [ ] Coverage fix\n", encoding="utf-8")
    plan_res = _invoke(
        ["github", "issue-plan", "--project-dir", str(tmp_path), "--output", str(issue_md)],
    )
    assert plan_res.exit_code == 0, plan_res.output
    create_res = _invoke(
        ["github", "issue-create", "--from", str(issue_md), "--dry-run"],
    )
    assert create_res.exit_code == 0, create_res.output
    assert "dry-run create" in create_res.output


def test_verify_integrations_json_pass(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("# C\n", encoding="utf-8")
    (tmp_path / ".cursor" / "rules").mkdir(parents=True)
    (tmp_path / ".cursor" / "rules" / "governance.mdc").write_text("alwaysApply: true\n")
    (tmp_path / ".agents" / "skills").mkdir(parents=True)
    (tmp_path / ".agents" / "skills" / "SKILL.md").write_text("# S\n", encoding="utf-8")
    (tmp_path / ".github").mkdir(parents=True)
    (tmp_path / ".github" / "copilot-instructions.md").write_text("# C\n", encoding="utf-8")
    (tmp_path / ".specsmith").mkdir(parents=True)
    (tmp_path / ".specsmith" / "mcp.json").write_text(
        json.dumps({"servers": [{"id": "x", "command": "python"}]}),
        encoding="utf-8",
    )

    result = _invoke(
        ["verify-integrations", "--project-dir", str(tmp_path), "--json"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["passed"] is True


def test_trace_score_and_drift_check_json(tmp_path: Path) -> None:
    state = tmp_path / ".specsmith"
    state.mkdir()
    (state / "requirements.json").write_text(
        json.dumps([{"id": "REQ-1", "status": "defined"}]),
        encoding="utf-8",
    )
    (state / "testcases.json").write_text(
        json.dumps([{"id": "TEST-1", "requirement_id": "REQ-1"}]),
        encoding="utf-8",
    )
    (state / "workitems.json").write_text(
        json.dumps([{"id": "WI-1", "requirement_ids": ["REQ-1"], "verified": True}]),
        encoding="utf-8",
    )

    score_res = _invoke(["trace", "score", "--project-dir", str(tmp_path), "--json"])
    assert score_res.exit_code == 0, score_res.output
    score_payload = json.loads(score_res.output)
    assert "score" in score_payload
    assert "recommendations" in score_payload

    drift_res = _invoke(["drift-check", "--project-dir", str(tmp_path), "--json"])
    assert drift_res.exit_code == 0, drift_res.output
    drift_payload = json.loads(drift_res.output)
    assert "findings" in drift_payload
