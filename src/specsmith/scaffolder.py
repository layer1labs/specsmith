# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
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

    from specsmith.tools import get_tools

    tools = get_tools(config)
    ctx = {
        "project": config,
        "today": date.today().isoformat(),
        "package_name": config.package_name,
        "tools": tools,
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

    # Initialize credit tracking with unlimited budget
    from specsmith.credits import CreditBudget, save_budget

    save_budget(target, CreditBudget())  # unlimited by default
    created.append(target / ".specsmith" / "credit-budget.json")

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
        ("editorconfig.j2", ".editorconfig"),
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
        ("scripts/setup.cmd.j2", "scripts/setup.cmd"),
        ("scripts/setup.sh.j2", "scripts/setup.sh"),
        ("scripts/run.cmd.j2", "scripts/run.cmd"),
        ("scripts/run.sh.j2", "scripts/run.sh"),
    ]

    if config.exec_shims:
        files.extend(
            [
                ("scripts/exec.cmd.j2", "scripts/exec.cmd"),
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
        dirs.extend([target / "examples"])
    elif config.type == ProjectType.FPGA_RTL:
        dirs.extend(
            [
                target / "rtl/src",
                target / "rtl/testbenches",
                target / "constraints",
                target / "ip_cores",
                target / "simulation",
                target / ".work",
            ]
        )
    elif config.type == ProjectType.YOCTO_BSP:
        dirs.extend(
            [
                target / f"meta-{config.package_name}/recipes-core",
                target / f"meta-{config.package_name}/conf",
                target / "kas",
                target / "configs",
            ]
        )
    elif config.type == ProjectType.PCB_HARDWARE:
        dirs.extend(
            [
                target / "schematics",
                target / "layout",
                target / "bom",
                target / "fabrication",
                target / "3d-models",
            ]
        )
    elif config.type == ProjectType.EMBEDDED_HARDWARE:
        dirs.extend(
            [
                target / "firmware/src",
                target / "firmware/include",
                target / "firmware/drivers",
                target / "tools",
            ]
        )
    elif config.type == ProjectType.WEB_FRONTEND:
        dirs.extend(
            [target / "src/components", target / "src/pages", target / "public", target / "tests"]
        )
    elif config.type == ProjectType.FULLSTACK_JS:
        dirs.extend(
            [
                target / "client/src",
                target / "server/src",
                target / "shared",
                target / "tests/client",
                target / "tests/server",
            ]
        )
    elif config.type in (ProjectType.CLI_RUST, ProjectType.LIBRARY_RUST):
        dirs.extend([target / "src", target / "tests", target / "benches"])
    elif config.type in (ProjectType.CLI_GO,):
        dirs.extend([target / "cmd", target / "internal", target / "pkg", target / "tests"])
    elif config.type in (ProjectType.CLI_C, ProjectType.LIBRARY_C):
        dirs.extend(
            [
                target / "src",
                target / "include",
                target / "tests",
                target / "build",
            ]
        )
    elif config.type == ProjectType.DOTNET_APP:
        dirs.extend([target / "src", target / "tests", target / "Properties"])
    elif config.type == ProjectType.MOBILE_APP:
        dirs.extend(
            [
                target / "lib",
                target / "ios",
                target / "android",
                target / "tests",
                target / "assets",
            ]
        )
    elif config.type == ProjectType.DEVOPS_IAC:
        dirs.extend(
            [
                target / "modules",
                target / "environments/dev",
                target / "environments/staging",
                target / "environments/prod",
                target / "tests",
            ]
        )
    elif config.type == ProjectType.DATA_ML:
        dirs.extend(
            [
                target / "data/raw",
                target / "data/processed",
                target / "notebooks",
                target / "src/models",
                target / "src/pipelines",
                target / "tests",
            ]
        )
    elif config.type == ProjectType.MICROSERVICES:
        dirs.extend(
            [
                target / "services",
                target / "shared/proto",
                target / "deploy",
                target / "tests/integration",
            ]
        )
    # --- Document / Knowledge ---
    elif config.type == ProjectType.SPEC_DOCUMENT:
        dirs.extend(
            [
                target / "docs",
                target / "drafts",
                target / "figures",
                target / "references",
                target / "published",
            ]
        )
    elif config.type == ProjectType.USER_MANUAL:
        dirs.extend(
            [
                target / "chapters",
                target / "images",
                target / "api-ref",
                target / "build",
            ]
        )
    elif config.type == ProjectType.RESEARCH_PAPER:
        dirs.extend(
            [
                target / "paper",
                target / "data",
                target / "figures",
                target / "references",
                target / "supplementary",
            ]
        )
    # --- Business / Legal ---
    elif config.type == ProjectType.BUSINESS_PLAN:
        dirs.extend(
            [
                target / "plan",
                target / "financials",
                target / "market-research",
                target / "appendices",
            ]
        )
    elif config.type == ProjectType.PATENT_APPLICATION:
        dirs.extend(
            [
                target / "claims",
                target / "specification",
                target / "figures",
                target / "prior-art",
                target / "correspondence",
            ]
        )
    elif config.type == ProjectType.LEGAL_COMPLIANCE:
        dirs.extend(
            [
                target / "contracts",
                target / "policies",
                target / "templates",
                target / "evidence",
                target / "audit-trail",
            ]
        )
    # --- Project management ---
    elif config.type == ProjectType.REQUIREMENTS_MGMT:
        dirs.extend(
            [
                target / "requirements",
                target / "traces",
                target / "reports",
                target / "baselines",
            ]
        )
    elif config.type == ProjectType.API_SPECIFICATION:
        dirs.extend(
            [
                target / "specs",
                target / "schemas",
                target / "examples",
                target / "generated",
            ]
        )
    # --- More software ---
    elif config.type == ProjectType.MONOREPO:
        dirs.extend(
            [
                target / "packages",
                target / "services",
                target / "shared",
                target / "tools",
                target / "deploy",
            ]
        )
    elif config.type == ProjectType.BROWSER_EXTENSION:
        dirs.extend(
            [
                target / "src/popup",
                target / "src/content",
                target / "src/background",
                target / "icons",
                target / "tests",
            ]
        )

    return dirs


def _init_commands(config: ProjectConfig) -> None:
    """Placeholder for src/specsmith/commands/__init__.py."""
