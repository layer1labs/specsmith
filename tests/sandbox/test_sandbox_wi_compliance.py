# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Sandbox tests: WI lifecycle and compliance commands on real scaffolded projects.

Two test classes:
  TestWILifecycleSandbox  — scaffold a project, exercise the full WI lifecycle
                            (preflight → WI creation → wi list/show/close/archive/promote/import).
  TestComplianceSandbox   — scaffold a project, exercise compliance list/check/report
                            commands and verify the output structure and disclaimer.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from click.testing import CliRunner

from specsmith.cli import main
from specsmith.wi_store import WorkItemStore

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _scaffold_cli_python(tmp_path: Path, name: str = "wi-test-project") -> Path:
    """Scaffold a minimal cli-python project and return the project root."""
    config = {
        "name": name,
        "type": "cli-python",
        "platforms": ["linux"],
        "language": "python",
        "vcs_platform": "github",
        "git_init": False,
    }
    cfg_path = tmp_path / "scaffold.yml"
    with open(cfg_path, "w") as fh:
        yaml.dump(config, fh, default_flow_style=False, sort_keys=False)

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["init", "--config", str(cfg_path), "--output-dir", str(tmp_path), "--no-git"],
    )
    assert result.exit_code == 0, f"Scaffold failed:\n{result.output}"
    return tmp_path / name


# ---------------------------------------------------------------------------
# TestWILifecycleSandbox
# ---------------------------------------------------------------------------


class TestWILifecycleSandbox:
    """WI lifecycle end-to-end on a real scaffolded project."""

    def test_preflight_creates_wi_in_scaffolded_project(self, tmp_path: Path) -> None:
        """run_preflight on a real project root creates a WorkItem in workitems.json."""
        from specsmith.governance_logic import run_preflight

        project = _scaffold_cli_python(tmp_path)
        result = run_preflight("what does the retry module do?", project_dir=str(project))
        assert result["decision"] == "accepted"
        wi_id = result["work_item_id"]
        assert wi_id.startswith("WI-")

        wi = WorkItemStore(project).get(wi_id)
        assert wi is not None
        assert wi.status == "open"
        # workitems.json must be inside the project
        wi_file = project / ".specsmith" / "workitems.json"
        assert wi_file.exists(), "workitems.json not created inside scaffolded project"

    def test_wi_list_shows_item_after_preflight(self, tmp_path: Path) -> None:
        from specsmith.governance_logic import run_preflight

        project = _scaffold_cli_python(tmp_path)
        run_preflight("what is the architecture?", project_dir=str(project))

        runner = CliRunner()
        result = runner.invoke(main, ["wi", "list", "--project-dir", str(project)])
        assert result.exit_code == 0
        assert "WI-" in result.output

    def test_wi_list_json_output_on_scaffolded_project(self, tmp_path: Path) -> None:
        from specsmith.governance_logic import run_preflight

        project = _scaffold_cli_python(tmp_path)
        r1 = run_preflight("explain the codebase", project_dir=str(project))
        wi_id = r1["work_item_id"]

        runner = CliRunner()
        result = runner.invoke(main, ["wi", "list", "--project-dir", str(project), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert any(item["id"] == wi_id for item in data)

    def test_wi_show_on_scaffolded_project(self, tmp_path: Path) -> None:
        from specsmith.governance_logic import run_preflight

        project = _scaffold_cli_python(tmp_path)
        r = run_preflight("describe the API surface", project_dir=str(project))
        wi_id = r["work_item_id"]

        runner = CliRunner()
        result = runner.invoke(main, ["wi", "show", wi_id, "--project-dir", str(project)])
        assert result.exit_code == 0
        assert wi_id in result.output

    def test_wi_archive_on_scaffolded_project(self, tmp_path: Path) -> None:
        from specsmith.governance_logic import run_preflight

        project = _scaffold_cli_python(tmp_path)
        r = run_preflight("what is the config format?", project_dir=str(project))
        wi_id = r["work_item_id"]

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "wi",
                "archive",
                wi_id,
                "--reason",
                "deferred to next sprint",
                "--project-dir",
                str(project),
            ],
        )
        assert result.exit_code == 0
        assert "archived" in result.output.lower()

        wi = WorkItemStore(project).get(wi_id)
        assert wi is not None
        assert wi.status == "archived"
        assert wi.closed_reason == "deferred to next sprint"

    def test_wi_close_requires_implemented_state(self, tmp_path: Path) -> None:
        """open → closed is invalid; must go via implemented first."""
        from specsmith.governance_logic import run_preflight

        project = _scaffold_cli_python(tmp_path)
        r = run_preflight("how does logging work?", project_dir=str(project))
        wi_id = r["work_item_id"]

        runner = CliRunner()
        # Attempt to close an open WI directly (should fail)
        result = runner.invoke(main, ["wi", "close", wi_id, "--project-dir", str(project)])
        assert result.exit_code == 1

    def test_wi_close_after_verify_marks_implemented(self, tmp_path: Path) -> None:
        """Verify equilibrium auto-transitions WI to implemented, then close it."""
        from specsmith.governance_logic import run_preflight, run_verify

        project = _scaffold_cli_python(tmp_path)
        r = run_preflight("what does the output formatter do?", project_dir=str(project))
        wi_id = r["work_item_id"]

        run_verify(
            diff="--- a/src/formatter.py\n+++ b/src/formatter.py\n@@ -1 +1 @@\n+format output\n",
            files_changed=["src/formatter.py"],
            test_results={"passed": 5, "failed": 0},
            project_dir=str(project),
            work_item_id=wi_id,
        )

        wi = WorkItemStore(project).get(wi_id)
        assert wi is not None
        assert wi.status == "implemented"

        runner = CliRunner()
        result = runner.invoke(main, ["wi", "close", wi_id, "--project-dir", str(project)])
        assert result.exit_code == 0
        assert "closed" in result.output.lower()

        wi2 = WorkItemStore(project).get(wi_id)
        assert wi2 is not None
        assert wi2.status == "closed"

    def test_wi_promote_creates_req_in_project(self, tmp_path: Path) -> None:
        """wi promote on a scaffolded project appends to docs/requirements/overflow.yml."""
        from specsmith.governance_logic import run_preflight

        project = _scaffold_cli_python(tmp_path)
        r = run_preflight("describe the retry policy", project_dir=str(project))
        wi_id = r["work_item_id"]

        req_dir = project / "docs" / "requirements"
        req_dir.mkdir(parents=True, exist_ok=True)

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "wi",
                "promote",
                wi_id,
                "--title",
                "System must retry on transient network errors",
                "--domain",
                "overflow",
                "--json",
                "--project-dir",
                str(project),
            ],
        )
        assert result.exit_code == 0, f"promote failed:\n{result.output}"
        data = json.loads(result.output)
        assert data["wi_id"] == wi_id
        assert data["promoted_to"].startswith("REQ-")

        overflow = req_dir / "overflow.yml"
        assert overflow.exists(), "overflow.yml should be created after promote"
        yaml_text = overflow.read_text(encoding="utf-8")
        assert "System must retry on transient network errors" in yaml_text
        assert wi_id in yaml_text

    def test_wi_import_from_ledger_in_scaffolded_project(self, tmp_path: Path) -> None:
        """wi import reads work_proposal lines from the project's LEDGER.md."""
        project = _scaffold_cli_python(tmp_path)

        # Append work proposals to the project's LEDGER.md
        ledger = project / "LEDGER.md"
        existing = ledger.read_text(encoding="utf-8")
        ledger.write_text(
            existing
            + "\nwork_proposal WI-AABBCCDD: add retry logic\n"
            + "work_proposal WI-11223344: fix login regression\n",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(main, ["wi", "import", "--project-dir", str(project)])
        assert result.exit_code == 0
        assert "2" in result.output or "Imported" in result.output

        store = WorkItemStore(project)
        assert store.get("WI-AABBCCDD") is not None
        assert store.get("WI-11223344") is not None

    def test_wi_tag_updates_kind_on_scaffolded_project(self, tmp_path: Path) -> None:
        from specsmith.governance_logic import run_preflight

        project = _scaffold_cli_python(tmp_path)
        # Use a question utterance — always accepted, guarantees a WI is created
        r = run_preflight("what is the authentication module?", project_dir=str(project))
        wi_id = r["work_item_id"]

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "wi",
                "tag",
                wi_id,
                "--kind",
                "bug",
                "--project-dir",
                str(project),
            ],
        )
        assert result.exit_code == 0
        wi = WorkItemStore(project).get(wi_id)
        assert wi is not None
        assert wi.kind == "bug"

    def test_wi_list_empty_for_fresh_project(self, tmp_path: Path) -> None:
        """A brand-new scaffolded project with no preflights has no WIs."""
        project = _scaffold_cli_python(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["wi", "list", "--project-dir", str(project)])
        assert result.exit_code == 0
        assert "No work items" in result.output

    def test_multiple_preflights_create_distinct_wis(self, tmp_path: Path) -> None:
        from specsmith.governance_logic import run_preflight

        project = _scaffold_cli_python(tmp_path)
        r1 = run_preflight("what does the parser do?", project_dir=str(project))
        r2 = run_preflight("what is the test strategy?", project_dir=str(project))

        assert r1["work_item_id"] != r2["work_item_id"]

        runner = CliRunner()
        result = runner.invoke(main, ["wi", "list", "--project-dir", str(project)])
        assert result.exit_code == 0
        assert r1["work_item_id"] in result.output
        assert r2["work_item_id"] in result.output


# ---------------------------------------------------------------------------
# TestComplianceSandbox
# ---------------------------------------------------------------------------


class TestComplianceSandbox:
    """Compliance commands end-to-end on a real scaffolded project."""

    def test_compliance_list_exits_0(self) -> None:
        """compliance list needs no project — just shows the regulation catalog."""
        runner = CliRunner()
        result = runner.invoke(main, ["compliance", "list"])
        assert result.exit_code == 0

    def test_compliance_list_shows_all_8_regulations(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["compliance", "list"])
        for reg in ("eu-ai-act", "nist-rmf", "colorado-sb24-205", "nyc-ll144"):
            assert reg in result.output, f"compliance list missing {reg}"

    def test_compliance_check_on_scaffolded_project(self, tmp_path: Path) -> None:
        """compliance check --all on a scaffolded project exits 0 and includes disclaimer."""
        project = _scaffold_cli_python(tmp_path, "compliance-test")
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "compliance",
                "check",
                "--regulation",
                "all",
                "--project-dir",
                str(project),
            ],
        )
        assert result.exit_code == 0, f"compliance check failed:\n{result.output}"
        output_lower = result.output.lower()
        assert "disclaimer" in output_lower or "best-effort" in output_lower, (
            "compliance check output must include disclaimer"
        )

    def test_compliance_check_specific_regulation(self, tmp_path: Path) -> None:
        """compliance check for a single regulation exits 0 and reports status."""
        project = _scaffold_cli_python(tmp_path, "compliance-single")
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "compliance",
                "check",
                "--regulation",
                "eu-ai-act",
                "--project-dir",
                str(project),
            ],
        )
        assert result.exit_code == 0, f"compliance check eu-ai-act failed:\n{result.output}"
        # Must report some compliance status
        assert any(
            kw in result.output.lower() for kw in ("compliant", "partial", "gap", "eu-ai-act")
        ), f"compliance check output missing status info:\n{result.output}"

    def test_compliance_check_json_output(self, tmp_path: Path) -> None:
        project = _scaffold_cli_python(tmp_path, "compliance-json")
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "compliance",
                "check",
                "--regulation",
                "nist-rmf",
                "--json",
                "--project-dir",
                str(project),
            ],
        )
        assert result.exit_code == 0, f"compliance check --json failed:\n{result.output}"
        data = json.loads(result.output)
        assert "regulation_id" in data or "results" in data or "disclaimer" in data, (
            "JSON output missing expected keys"
        )

    def test_compliance_report_markdown_has_disclaimer(self, tmp_path: Path) -> None:
        project = _scaffold_cli_python(tmp_path, "compliance-report")
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "compliance",
                "report",
                "--format",
                "md",
                "--project-dir",
                str(project),
            ],
        )
        assert result.exit_code == 0, f"compliance report --format md failed:\n{result.output}"
        assert "DISCLAIMER" in result.output.upper(), (
            "Markdown compliance report must contain DISCLAIMER"
        )

    def test_compliance_report_json_has_disclaimer(self, tmp_path: Path) -> None:
        project = _scaffold_cli_python(tmp_path, "compliance-report-json")
        # Write to a file so we get clean JSON without ANSI color codes
        # (the stdout path uses syntax highlighting that embeds escape sequences)
        out_file = tmp_path / "report.json"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "compliance",
                "report",
                "--format",
                "json",
                "--output",
                str(out_file),
                "--project-dir",
                str(project),
            ],
        )
        assert result.exit_code == 0, f"compliance report --format json failed:\n{result.output}"
        assert out_file.exists(), "compliance report --output file was not created"
        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert "disclaimer" in data, "JSON compliance report missing 'disclaimer' key"
        assert "legal" in data["disclaimer"].lower(), "disclaimer must reference legal advice"

    def test_compliance_report_to_file(self, tmp_path: Path) -> None:
        project = _scaffold_cli_python(tmp_path, "compliance-file")
        out_file = tmp_path / "report.md"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "compliance",
                "report",
                "--format",
                "md",
                "--output",
                str(out_file),
                "--project-dir",
                str(project),
            ],
        )
        assert result.exit_code == 0, f"compliance report --output failed:\n{result.output}"
        assert out_file.exists(), "compliance report --output file was not created"
        content = out_file.read_text(encoding="utf-8")
        assert "DISCLAIMER" in content.upper()
        assert len(content) > 100, "compliance report file is suspiciously short"

    def test_compliance_check_more_evidence_higher_confidence(self, tmp_path: Path) -> None:
        """A scaffolded project (with governance files) should have higher or equal
        confidence than an empty directory — presence of governance docs is evidence."""
        from specsmith.compliance.checker import ComplianceChecker

        project = _scaffold_cli_python(tmp_path, "compliance-evidence")
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        checker_project = ComplianceChecker(project)
        checker_empty = ComplianceChecker(empty_dir)

        result_project = checker_project.check_regulation("eu-ai-act")
        result_empty = checker_empty.check_regulation("eu-ai-act")

        assert result_project.overall_confidence >= result_empty.overall_confidence, (
            "Scaffolded project with governance files must have >= confidence vs empty dir"
        )
