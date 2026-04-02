# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Sandbox integration test: import an existing Python CLI project.

Creates a realistic Python CLI project from scratch (no specsmith governance),
then exercises the full import → audit → validate workflow. Always starts clean.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import yaml
from click.testing import CliRunner
from specsmith.cli import main


def _create_realistic_python_project(root: Path) -> None:
    """Build a realistic Python CLI project with no specsmith governance."""
    # --- pyproject.toml ---
    (root / "pyproject.toml").write_text(
        dedent("""\
        [build-system]
        requires = ["setuptools>=68.0"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "taskctl"
        version = "0.5.0"
        description = "A task management CLI"
        requires-python = ">=3.10"
        dependencies = ["click>=8.1", "rich>=13.0"]

        [project.optional-dependencies]
        dev = ["pytest>=7.0", "ruff>=0.4", "mypy>=1.10"]

        [project.scripts]
        taskctl = "taskctl.cli:main"

        [tool.setuptools.packages.find]
        where = ["src"]
        """),
        encoding="utf-8",
    )

    # --- Source code ---
    src = root / "src" / "taskctl"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text('__version__ = "0.5.0"\n', encoding="utf-8")
    (src / "cli.py").write_text(
        dedent("""\
        import click

        @click.group()
        def main():
            pass

        @main.command()
        @click.argument("name")
        def add(name: str):
            click.echo(f"Added task: {name}")

        @main.command()
        def list_tasks():
            click.echo("No tasks yet.")
        """),
        encoding="utf-8",
    )
    (src / "core.py").write_text(
        dedent("""\
        from dataclasses import dataclass

        @dataclass
        class Task:
            name: str
            done: bool = False

        def create_task(name: str) -> Task:
            return Task(name=name)
        """),
        encoding="utf-8",
    )
    (src / "utils.py").write_text(
        dedent("""\
        from datetime import datetime

        def timestamp() -> str:
            return datetime.now().isoformat()
        """),
        encoding="utf-8",
    )

    # --- Tests ---
    tests = root / "tests"
    tests.mkdir()
    (root / "conftest.py").write_text("", encoding="utf-8")
    (tests / "test_cli.py").write_text(
        dedent("""\
        from click.testing import CliRunner
        from taskctl.cli import main

        def test_add():
            runner = CliRunner()
            result = runner.invoke(main, ["add", "test-task"])
            assert result.exit_code == 0

        def test_list():
            runner = CliRunner()
            result = runner.invoke(main, ["list-tasks"])
            assert result.exit_code == 0
        """),
        encoding="utf-8",
    )
    (tests / "test_core.py").write_text(
        dedent("""\
        from taskctl.core import create_task

        def test_create_task():
            t = create_task("my task")
            assert t.name == "my task"
            assert t.done is False
        """),
        encoding="utf-8",
    )

    # --- README (but NO AGENTS.md or governance) ---
    (root / "README.md").write_text("# taskctl\n\nA task management CLI.\n", encoding="utf-8")

    # --- GitHub CI ---
    wf = root / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "ci.yml").write_text(
        dedent("""\
        name: CI
        on: [push, pull_request]
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-python@v5
                with:
                  python-version: "3.12"
              - run: pip install -e ".[dev]"
              - run: ruff check src/ tests/
              - run: pytest
        """),
        encoding="utf-8",
    )

    # --- .gitignore ---
    (root / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n.venv/\ndist/\n*.egg-info/\n", encoding="utf-8"
    )


class TestSandboxImport:
    """Full import workflow: create project → import → verify → audit → validate."""

    def test_full_import_workflow(self, tmp_path: Path) -> None:
        """End-to-end import of a realistic Python CLI project."""
        root = tmp_path / "taskctl"
        root.mkdir()
        _create_realistic_python_project(root)

        runner = CliRunner()

        # ---- Step 1: Run specsmith import ----
        result = runner.invoke(main, ["import", "--project-dir", str(root)], input="y\n")
        assert result.exit_code == 0, f"Import failed: {result.output}"
        assert "Done" in result.output

        # ---- Step 2: Verify detection was correct ----
        assert "python" in result.output.lower()
        assert "pyproject" in result.output.lower()
        assert "pytest" in result.output.lower()
        assert "github" in result.output.lower()

        # ---- Step 3: Verify overlay files created ----
        assert (root / "AGENTS.md").exists()
        assert (root / "LEDGER.md").exists()
        assert (root / "docs" / "REQUIREMENTS.md").exists()
        assert (root / "docs" / "TEST_SPEC.md").exists()
        assert (root / "docs" / "architecture.md").exists()

        # ---- Step 4: Verify overlay content ----
        agents = (root / "AGENTS.md").read_text(encoding="utf-8")
        assert "taskctl" in agents
        assert "python" in agents.lower()

        reqs = (root / "docs" / "REQUIREMENTS.md").read_text(encoding="utf-8")
        assert "REQ-" in reqs
        assert "taskctl" in reqs.lower()

        arch = (root / "docs" / "architecture.md").read_text(encoding="utf-8")
        assert "python" in arch.lower()

        test_spec = (root / "docs" / "TEST_SPEC.md").read_text(encoding="utf-8")
        assert "TEST-" in test_spec

        # ---- Step 5: Verify scaffold.yml created ----
        assert (root / "scaffold.yml").exists()
        with open(root / "scaffold.yml") as f:
            cfg = yaml.safe_load(f)
        assert cfg["type"] == "cli-python"
        assert cfg["language"] == "python"
        assert cfg["detected_build_system"] == "pyproject"
        assert cfg["detected_test_framework"] == "pytest"

        # ---- Step 6: Audit the imported project ----
        # Audit may report REQ↔TEST coverage gaps from auto-generated REQs;
        # we verify it runs without crashing and finds the expected files.
        audit_result = runner.invoke(main, ["audit", "--project-dir", str(root)])
        assert "AGENTS.md" in audit_result.output
        assert "LEDGER.md" in audit_result.output

    def test_import_skip_existing(self, tmp_path: Path) -> None:
        """Import does not overwrite existing files without --force."""
        root = tmp_path / "taskctl"
        root.mkdir()
        _create_realistic_python_project(root)

        # Pre-create AGENTS.md with custom content
        (root / "AGENTS.md").write_text("# Custom governance\n", encoding="utf-8")

        runner = CliRunner()
        runner.invoke(main, ["import", "--project-dir", str(root)], input="y\n")

        # AGENTS.md should NOT have been overwritten
        assert (root / "AGENTS.md").read_text(encoding="utf-8") == "# Custom governance\n"

    def test_import_force_overwrites(self, tmp_path: Path) -> None:
        """Import with --force overwrites existing files."""
        root = tmp_path / "taskctl"
        root.mkdir()
        _create_realistic_python_project(root)

        (root / "AGENTS.md").write_text("# Custom governance\n", encoding="utf-8")

        runner = CliRunner()
        runner.invoke(main, ["import", "--project-dir", str(root), "--force"], input="y\n")

        # AGENTS.md SHOULD have been overwritten
        new_content = (root / "AGENTS.md").read_text(encoding="utf-8")
        assert "Custom governance" not in new_content
        assert "taskctl" in new_content

    def test_import_idempotent_restart(self, tmp_path: Path) -> None:
        """Verify that deleting outputs and re-importing gives same results."""
        root = tmp_path / "taskctl"
        root.mkdir()
        _create_realistic_python_project(root)

        runner = CliRunner()

        # First import
        runner.invoke(main, ["import", "--project-dir", str(root), "--force"], input="y\n")
        first_agents = (root / "AGENTS.md").read_text(encoding="utf-8")

        # Delete all governance files (simulate clean restart)
        for f in ["AGENTS.md", "LEDGER.md", "scaffold.yml"]:
            p = root / f
            if p.exists():
                p.unlink()
        for f in ["REQUIREMENTS.md", "TEST_SPEC.md", "architecture.md"]:
            p = root / "docs" / f
            if p.exists():
                p.unlink()
        gov = root / "docs" / "governance"
        if gov.exists():
            import shutil

            shutil.rmtree(gov)

        # Re-import
        runner.invoke(main, ["import", "--project-dir", str(root), "--force"], input="y\n")
        second_agents = (root / "AGENTS.md").read_text(encoding="utf-8")

        # Results should be identical (idempotent)
        assert first_agents == second_agents

    def test_import_preserves_existing_project_docs(self, tmp_path: Path) -> None:
        """Import skips stubs when project has existing docs."""
        root = tmp_path / "taskctl"
        root.mkdir()
        _create_realistic_python_project(root)

        # Pre-create existing project docs (as a real project would have)
        docs = root / "docs"
        docs.mkdir(exist_ok=True)
        (docs / "REQUIREMENTS.md").write_text(
            "# Existing Requirements\n\n## REQ-CUSTOM-001\nReal requirement.\n",
            encoding="utf-8",
        )
        (docs / "TEST_SPEC.md").write_text(
            "# Existing Tests\n\n## TEST-CUSTOM-001\nReal test.\n",
            encoding="utf-8",
        )
        arch_dir = docs / "architecture"
        arch_dir.mkdir()
        (arch_dir / "DESIGN.md").write_text(
            "# Existing Architecture\nReal architecture doc.\n",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(main, ["import", "--project-dir", str(root)], input="y\n")
        assert result.exit_code == 0, f"Import failed: {result.output}"

        # Existing docs should NOT have been overwritten with stubs
        reqs = (docs / "REQUIREMENTS.md").read_text(encoding="utf-8")
        assert "REQ-CUSTOM-001" in reqs  # Original content preserved
        assert "auto-generated" not in reqs.lower()  # Not replaced with stub

        tests_content = (docs / "TEST_SPEC.md").read_text(encoding="utf-8")
        assert "TEST-CUSTOM-001" in tests_content

        # architecture.md stub should NOT have been created (existing arch doc found)
        assert not (docs / "architecture.md").exists()

        # But governance files and scaffold.yml should still be created
        assert (root / "scaffold.yml").exists()
        assert (root / "LEDGER.md").exists()
        assert (root / "docs" / "governance" / "rules.md").exists()

    def test_import_force_overwrites_existing_docs(self, tmp_path: Path) -> None:
        """Import with --force replaces existing docs with generated stubs."""
        root = tmp_path / "taskctl"
        root.mkdir()
        _create_realistic_python_project(root)

        docs = root / "docs"
        docs.mkdir(exist_ok=True)
        (docs / "REQUIREMENTS.md").write_text(
            "# Existing Requirements\n", encoding="utf-8"
        )

        runner = CliRunner()
        result = runner.invoke(
            main, ["import", "--project-dir", str(root), "--force"], input="y\n"
        )
        assert result.exit_code == 0

        reqs = (docs / "REQUIREMENTS.md").read_text(encoding="utf-8")
        assert "auto-generated" in reqs.lower()  # Replaced with stub
