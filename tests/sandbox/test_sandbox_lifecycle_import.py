# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Sandbox lifecycle test: import existing project and walk lifecycle.

Creates a realistic project, imports it, then verifies governance files
and phase tracking work correctly for imported projects.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import yaml
from click.testing import CliRunner

from specsmith.cli import main


def _create_test_project(root: Path) -> None:
    """Build a minimal Python project with no governance."""
    (root / "pyproject.toml").write_text(
        dedent("""\
        [build-system]
        requires = ["setuptools>=68.0"]
        build-backend = "setuptools.build_meta"
        [project]
        name = "importme"
        version = "1.0.0"
        requires-python = ">=3.10"
        dependencies = ["click>=8.1"]
        [project.scripts]
        importme = "importme.cli:main"
        [tool.setuptools.packages.find]
        where = ["src"]
        """),
        encoding="utf-8",
    )
    src = root / "src" / "importme"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text('__version__ = "1.0.0"\n', encoding="utf-8")
    (src / "cli.py").write_text(
        dedent("""\
        import click

        @click.command()
        def main():
            click.echo("hello")
        """),
        encoding="utf-8",
    )
    tests = root / "tests"
    tests.mkdir()
    (tests / "test_cli.py").write_text(
        dedent("""\
        from importme.cli import main
        from click.testing import CliRunner

        def test_main():
            r = CliRunner().invoke(main)
            assert r.exit_code == 0
        """),
        encoding="utf-8",
    )
    (root / "README.md").write_text("# importme\nA test project.\n", encoding="utf-8")
    (root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")


class TestLifecycleImport:
    """Import an existing project and verify lifecycle setup."""

    def test_import_sets_inception_phase(self, tmp_path: Path) -> None:
        root = tmp_path / "importme"
        root.mkdir()
        _create_test_project(root)

        runner = CliRunner()
        r = runner.invoke(main, ["import", "--project-dir", str(root), "--yes"])
        assert r.exit_code == 0, f"Import failed: {r.output}"

        # Phase should be inception
        assert (root / "scaffold.yml").exists()
        with open(root / "scaffold.yml") as f:
            cfg = yaml.safe_load(f)
        assert cfg.get("aee_phase") == "inception"

    def test_import_creates_governance_files(self, tmp_path: Path) -> None:
        root = tmp_path / "importme"
        root.mkdir()
        _create_test_project(root)

        runner = CliRunner()
        runner.invoke(main, ["import", "--project-dir", str(root), "--yes"])

        # New governance files
        gov = root / "docs" / "governance"
        assert (gov / "SESSION-PROTOCOL.md").exists()
        assert (gov / "LIFECYCLE.md").exists()
        assert (gov / "RULES.md").exists()

        # Old names should NOT exist
        assert not (gov / "WORKFLOW.md").exists()
        assert not (root / "docs" / "WORKFLOW.md").exists()

    def test_import_then_phase_operations(self, tmp_path: Path) -> None:
        root = tmp_path / "importme"
        root.mkdir()
        _create_test_project(root)

        runner = CliRunner()
        runner.invoke(main, ["import", "--project-dir", str(root), "--yes"])

        # Phase show
        r = runner.invoke(main, ["phase", "show", "--project-dir", str(root)])
        assert r.exit_code == 0, f"phase show failed: {r.output}\n{r.exception}"
        assert "Inception" in r.output

        # Phase list
        r = runner.invoke(main, ["phase", "list", "--project-dir", str(root)])
        assert r.exit_code == 0, f"phase list failed: {r.output}\n{r.exception}"
        assert "inception" in r.output

        # Advance with --force
        r = runner.invoke(main, ["phase", "next", "--force", "--project-dir", str(root)])
        assert r.exit_code == 0
        assert "Architecture" in r.output

        with open(root / "scaffold.yml") as f:
            cfg = yaml.safe_load(f)
        assert cfg["aee_phase"] == "architecture"

    def test_import_audit_includes_phase_readiness(self, tmp_path: Path) -> None:
        root = tmp_path / "importme"
        root.mkdir()
        _create_test_project(root)

        runner = CliRunner()
        runner.invoke(main, ["import", "--project-dir", str(root), "--yes"])

        r = runner.invoke(main, ["audit", "--project-dir", str(root)])
        # Audit may exit 1 (issues found) but must not crash
        assert r.exit_code in (0, 1), f"audit crashed: {r.exception}"
        # Audit should include phase readiness info
        assert "Phase" in r.output or "phase" in r.output
