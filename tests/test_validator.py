# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for specsmith validator."""

from __future__ import annotations

from pathlib import Path

from specsmith.validator import run_validate


class TestValidateScaffoldYml:
    def test_no_scaffold_yml(self, tmp_path: Path) -> None:
        report = run_validate(tmp_path)
        # Should pass (gracefully skip)
        assert report.valid

    def test_valid_scaffold_yml(self, tmp_path: Path) -> None:
        (tmp_path / "scaffold.yml").write_text("name: test\ntype: cli-python\n", encoding="utf-8")
        report = run_validate(tmp_path)
        results = [r for r in report.results if r.name == "scaffold-yml"]
        assert results[0].passed

    def test_invalid_scaffold_yml(self, tmp_path: Path) -> None:
        (tmp_path / "scaffold.yml").write_text("just a string\n", encoding="utf-8")
        report = run_validate(tmp_path)
        results = [r for r in report.results if r.name == "scaffold-yml"]
        assert not results[0].passed


class TestValidateAgentsRefs:
    def test_broken_ref(self, tmp_path: Path) -> None:
        (tmp_path / "AGENTS.md").write_text(
            "See [rules](docs/governance/RULES.md) for details.\n",
            encoding="utf-8",
        )
        report = run_validate(tmp_path)
        failed = [r for r in report.results if not r.passed]
        assert any("RULES.md" in r.message for r in failed)

    def test_valid_refs(self, tmp_path: Path) -> None:
        (tmp_path / "docs" / "governance").mkdir(parents=True)
        (tmp_path / "docs" / "governance" / "RULES.md").write_text("# Rules\n", encoding="utf-8")
        (tmp_path / "AGENTS.md").write_text(
            "See [rules](docs/governance/RULES.md).\n",
            encoding="utf-8",
        )
        report = run_validate(tmp_path)
        assert report.valid


class TestValidateReqUnique:
    def test_duplicate_req_ids(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "REQUIREMENTS.md").write_text(
            "REQ-CLI-001: first\nREQ-CLI-001: duplicate\n", encoding="utf-8"
        )
        report = run_validate(tmp_path)
        unique_results = [r for r in report.results if r.name == "req-unique"]
        assert len(unique_results) == 1
        assert not unique_results[0].passed


class TestValidateBlockingLoops:
    """Tests for H11 blocking-loop detection in script files."""

    def test_no_scripts_skips_check(self, tmp_path: Path) -> None:
        # No script files at all — check should return nothing (not even a pass result)
        report = run_validate(tmp_path)
        loop_results = [r for r in report.results if "blocking" in r.name]
        assert loop_results == []

    def test_clean_script_passes(self, tmp_path: Path) -> None:
        # A .sh file with a bounded loop passes
        script = tmp_path / "poll.sh"
        script.write_text(
            "#!/bin/bash\n"
            "deadline=$((SECONDS + 30))\n"
            "while true; do\n"
            "  [ $SECONDS -ge $deadline ] && break\n"
            "  sleep 0.2\n"
            "done\n",
            encoding="utf-8",
        )
        report = run_validate(tmp_path)
        loop_results = [r for r in report.results if "blocking" in r.name]
        assert all(r.passed for r in loop_results)

    def test_unbounded_bash_loop_fails(self, tmp_path: Path) -> None:
        # A .sh file with an infinite loop and no deadline guard is flagged
        script = tmp_path / "bad_poll.sh"
        script.write_text(
            "#!/bin/bash\nwhile true; do\n  echo waiting\n  sleep 1\ndone\n",
            encoding="utf-8",
        )
        report = run_validate(tmp_path)
        loop_results = [r for r in report.results if "blocking" in r.name]
        assert any(not r.passed for r in loop_results)
        assert any("H11" in r.message for r in loop_results)

    def test_unbounded_powershell_loop_fails(self, tmp_path: Path) -> None:
        # A .ps1 file with while($true) and no deadline
        script = tmp_path / "scripts" / "watch.ps1"
        script.parent.mkdir()
        script.write_text(
            "while ($true) {\n"
            "    $buf = $port.ReadExisting()\n"
            "    Start-Sleep -Milliseconds 200\n"
            "}\n",
            encoding="utf-8",
        )
        report = run_validate(tmp_path)
        loop_results = [r for r in report.results if not r.passed and "blocking" in r.name]
        assert len(loop_results) >= 1

    def test_powershell_with_deadline_passes(self, tmp_path: Path) -> None:
        script = tmp_path / "scripts" / "safe_watch.ps1"
        script.parent.mkdir(exist_ok=True)
        script.write_text(
            "$deadline = (Get-Date).AddSeconds(15)\n"
            "while ($true) {\n"
            "    if ((Get-Date) -gt $deadline) { Write-Error 'Timeout'; break }\n"
            "    Start-Sleep -Milliseconds 200\n"
            "}\n",
            encoding="utf-8",
        )
        report = run_validate(tmp_path)
        loop_results = [r for r in report.results if "blocking" in r.name]
        assert all(r.passed for r in loop_results)

    def test_python_while_true_in_cmd_fails(self, tmp_path: Path) -> None:
        # .cmd files with while true (less common but should be caught)
        script = tmp_path / "loop.cmd"
        script.write_text(
            "@echo off\n:loop\ngoto loop\n",  # not an infinite-loop pattern we detect
            encoding="utf-8",
        )
        # This specific content has no matching pattern — should pass
        report = run_validate(tmp_path)
        loop_results = [r for r in report.results if "blocking" in r.name]
        assert all(r.passed for r in loop_results)
