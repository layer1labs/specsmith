"""Core scaffold generation logic for specsmith."""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from specsmith.config import ProjectConfig, ProjectType


def scaffold_project(config: ProjectConfig, target: Path) -> list[Path]:
    """Generate a full governed project scaffold at the target directory.

    Returns a list of all created file paths.
    """
    env = Environment(
        loader=PackageLoader("specsmith", "templates"),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    ctx = {
        "project": config,
        "today": date.today().isoformat(),
        "package_name": config.package_name,
    }

    created: list[Path] = []

    # Determine which templates to render based on project type
    file_map = _build_file_map(config)

    for template_name, output_rel in file_map:
        output_path = target / output_rel
        output_path.parent.mkdir(parents=True, exist_ok=True)

        tmpl = env.get_template(template_name)
        content = tmpl.render(**ctx)

        output_path.write_text(content, encoding="utf-8")
        created.append(output_path)

    # Create .gitkeep files in empty directories
    for empty_dir in _get_empty_dirs(config, target):
        gitkeep = empty_dir / ".gitkeep"
        gitkeep.parent.mkdir(parents=True, exist_ok=True)
        gitkeep.write_text("", encoding="utf-8")
        created.append(gitkeep)

    # Agent integrations
    for integration_name in config.integrations:
        if integration_name == "agents-md":
            continue  # AGENTS.md is always generated via templates
        try:
            from specsmith.integrations import get_adapter

            adapter = get_adapter(integration_name)
            created.extend(adapter.generate(config, target))
        except ValueError:
            pass  # Unknown adapter — skip silently

    # VCS platform CI/CD, dependency, and security configs
    if config.vcs_platform:
        try:
            from specsmith.vcs import get_platform

            platform = get_platform(config.vcs_platform)
            created.extend(platform.generate_all(config, target))
        except ValueError:
            pass  # Unknown platform — skip silently

    # Git init
    if config.git_init:
        subprocess.run(  # noqa: S603
            ["git", "init", str(target)],
            capture_output=True,
            timeout=10,
        )

    return sorted(created)


def _build_file_map(config: ProjectConfig) -> list[tuple[str, str]]:
    """Build list of (template_name, output_relative_path) tuples."""
    files: list[tuple[str, str]] = [
        # Root governance
        ("agents.md.j2", "AGENTS.md"),
        ("ledger.md.j2", "LEDGER.md"),
        ("readme.md.j2", "README.md"),
        ("gitignore.j2", ".gitignore"),
        ("gitattributes.j2", ".gitattributes"),
        # Modular governance
        ("governance/rules.md.j2", "docs/governance/rules.md"),
        ("governance/workflow.md.j2", "docs/governance/workflow.md"),
        ("governance/roles.md.j2", "docs/governance/roles.md"),
        ("governance/context-budget.md.j2", "docs/governance/context-budget.md"),
        ("governance/verification.md.j2", "docs/governance/verification.md"),
        ("governance/drift-metrics.md.j2", "docs/governance/drift-metrics.md"),
        # Project docs
        ("docs/architecture.md.j2", "docs/architecture.md"),
        ("docs/workflow.md.j2", "docs/workflow.md"),
        ("docs/requirements.md.j2", "docs/REQUIREMENTS.md"),
        ("docs/test-spec.md.j2", "docs/TEST_SPEC.md"),
        # Scripts
        ("scripts/setup.ps1.j2", "scripts/setup.ps1"),
        ("scripts/setup.sh.j2", "scripts/setup.sh"),
        ("scripts/run.ps1.j2", "scripts/run.ps1"),
        ("scripts/run.sh.j2", "scripts/run.sh"),
    ]

    if config.exec_shims:
        files.extend(
            [
                ("scripts/exec.ps1.j2", "scripts/exec.ps1"),
                ("scripts/exec.sh.j2", "scripts/exec.sh"),
            ]
        )

    # Python project types get pyproject.toml and src layout
    if config.type in (
        ProjectType.CLI_PYTHON,
        ProjectType.LIBRARY_PYTHON,
        ProjectType.BACKEND_FRONTEND,
        ProjectType.BACKEND_FRONTEND_TRAY,
    ):
        files.append(("pyproject.toml.j2", "pyproject.toml"))
        files.append(("python/init.py.j2", f"src/{config.package_name}/__init__.py"))

        if config.type == ProjectType.CLI_PYTHON:
            files.append(("python/cli.py.j2", f"src/{config.package_name}/cli.py"))

    return files


def _get_empty_dirs(config: ProjectConfig, target: Path) -> list[Path]:
    """Return list of directories that need .gitkeep files."""
    dirs: list[Path] = [target / "tests"]

    if config.type == ProjectType.CLI_PYTHON:
        dirs.extend(
            [
                target / f"src/{config.package_name}/commands",
                target / f"src/{config.package_name}/utils",
            ]
        )
    elif config.type == ProjectType.LIBRARY_PYTHON:
        dirs.extend(
            [
                target / "examples",
            ]
        )

    return dirs


def _init_commands(config: ProjectConfig) -> None:
    """Placeholder for src/specsmith/commands/__init__.py."""
