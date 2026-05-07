# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Sandbox lifecycle test: new project walks through all 7 AEE phases.

Exercises: init → audit → phase show → phase next (through all phases with --force).
Verifies phase tracking, gating, and artifact creation at each stage.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from specsmith.cli import main


def _write_scaffold_config(config_path: Path) -> None:
    config = {
        "name": "lifecycle-test",
        "type": "cli-python",
        "platforms": ["windows", "linux", "macos"],
        "language": "python",
        "vcs_platform": "github",
        "git_init": False,
    }
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


class TestLifecycleNew:
    """Walk a new project through the entire 7-phase lifecycle."""

    def test_full_lifecycle_phases(self, tmp_path: Path) -> None:
        config_path = tmp_path / "scaffold.yml"
        _write_scaffold_config(config_path)
        out = tmp_path / "out"
        out.mkdir()

        runner = CliRunner()

        # ---- Step 1: Scaffold ----
        result = runner.invoke(
            main,
            ["init", "--config", str(config_path), "--output-dir", str(out), "--no-git"],
        )
        assert result.exit_code == 0, f"Init failed: {result.output}"
        project = out / "lifecycle-test"

        # ---- Step 2: Verify initial phase is inception ----
        scaffold_file = project / "docs" / "SPECSMITH.yml"
        if not scaffold_file.exists():
            scaffold_file = project / "scaffold.yml"
        with open(scaffold_file) as f:
            cfg = yaml.safe_load(f)
        assert cfg.get("aee_phase") == "inception"

        # ---- Step 3: Phase show works ----
        r = runner.invoke(main, ["phase", "show", "--project-dir", str(project)])
        assert r.exit_code == 0
        assert "Inception" in r.output

        # ---- Step 4: Phase list shows all phases with current marker ----
        r = runner.invoke(main, ["phase", "list", "--project-dir", str(project)])
        assert r.exit_code == 0
        assert "inception" in r.output
        assert "release" in r.output

        # ---- Step 5: Audit passes at inception ----
        r = runner.invoke(main, ["audit", "--project-dir", str(project)])
        assert r.exit_code == 0
        assert "phase-readiness" in r.output.lower() or "Phase" in r.output

        # ---- Step 6: Advance through all phases with --force ----
        phases = [
            "architecture",
            "requirements",
            "test_spec",
            "implementation",
            "verification",
            "release",
        ]
        for phase_key in phases:
            r = runner.invoke(
                main,
                ["phase", "next", "--force", "--project-dir", str(project)],
            )
            assert r.exit_code == 0, f"phase next to {phase_key} failed: {r.output}"
            assert "Advanced" in r.output or "final phase" in r.output

            # Verify scaffold reflects the new phase (check canonical location first)
            _sf = project / "docs" / "SPECSMITH.yml"
            if not _sf.exists():
                _sf = project / "scaffold.yml"
            with open(_sf) as f:
                cfg = yaml.safe_load(f)
            assert cfg.get("aee_phase") == phase_key

        # ---- Step 7: At release, phase next should indicate final phase ----
        r = runner.invoke(
            main,
            ["phase", "next", "--force", "--project-dir", str(project)],
        )
        assert r.exit_code == 0
        assert "final phase" in r.output

        # ---- Step 8: Phase set can jump back ----
        r = runner.invoke(
            main,
            ["phase", "set", "inception", "--force", "--project-dir", str(project)],
        )
        assert r.exit_code == 0
        _sf2 = project / "docs" / "SPECSMITH.yml"
        if not _sf2.exists():
            _sf2 = project / "scaffold.yml"
        with open(_sf2) as f:
            cfg = yaml.safe_load(f)
        assert cfg["aee_phase"] == "inception"

    def test_phase_gating_without_force(self, tmp_path: Path) -> None:
        """Verify phase advancement is blocked when checks fail (no --force)."""
        config_path = tmp_path / "scaffold.yml"
        _write_scaffold_config(config_path)
        out = tmp_path / "out"
        out.mkdir()

        runner = CliRunner()
        runner.invoke(
            main,
            ["init", "--config", str(config_path), "--output-dir", str(out), "--no-git"],
        )
        project = out / "lifecycle-test"

        # Force to architecture phase
        runner.invoke(
            main,
            ["phase", "set", "architecture", "--force", "--project-dir", str(project)],
        )

        # Try to advance without --force — should fail (ARCHITECTURE.md is stub)
        r = runner.invoke(
            main,
            ["phase", "next", "--project-dir", str(project)],
        )
        assert r.exit_code == 1
        assert "check" in r.output.lower()

    def test_governance_files_present(self, tmp_path: Path) -> None:
        """Verify all governance files are present after scaffold."""
        config_path = tmp_path / "scaffold.yml"
        _write_scaffold_config(config_path)
        out = tmp_path / "out"
        out.mkdir()

        runner = CliRunner()
        runner.invoke(
            main,
            ["init", "--config", str(config_path), "--output-dir", str(out), "--no-git"],
        )
        project = out / "lifecycle-test"
        gov = project / "docs" / "governance"

        expected = [
            "RULES.md",
            "SESSION-PROTOCOL.md",
            "LIFECYCLE.md",
            "ROLES.md",
            "CONTEXT-BUDGET.md",
            "VERIFICATION.md",
            "DRIFT-METRICS.md",
        ]
        for f in expected:
            assert (gov / f).exists(), f"Missing governance file: {f}"

        # WORKFLOW.md should NOT exist
        assert not (gov / "WORKFLOW.md").exists()
        assert not (project / "docs" / "WORKFLOW.md").exists()

        # LIFECYCLE.md should reference phases
        lifecycle = (gov / "LIFECYCLE.md").read_text(encoding="utf-8")
        assert "Inception" in lifecycle
        assert "specsmith phase" in lifecycle

        # AGENTS.md should mention current phase
        agents = (project / "AGENTS.md").read_text(encoding="utf-8")
        assert "Current Phase" in agents
        assert "inception" in agents.lower()

        # README.md should have dynamic phase
        readme = (project / "README.md").read_text(encoding="utf-8")
        assert "Inception" in readme
