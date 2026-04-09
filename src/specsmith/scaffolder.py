# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Core scaffold generation logic for specsmith."""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from specsmith.config import ProjectConfig, ProjectType
from specsmith.phase import PHASE_MAP


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
    phase_key = "inception"  # new projects always start at inception
    phase_obj = PHASE_MAP[phase_key]
    ctx = {
        "project": config,
        "today": date.today().isoformat(),
        "package_name": config.package_name,
        "tools": tools,
        "aee_phase": phase_key,
        "aee_phase_label": phase_obj.label,
        "aee_phase_emoji": phase_obj.emoji,
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

    # Set initial AEE phase in scaffold.yml
    from specsmith.phase import write_phase

    write_phase(target, "inception")

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
        ("governance/rules.md.j2", "docs/governance/RULES.md"),
        ("governance/session-protocol.md.j2", "docs/governance/SESSION-PROTOCOL.md"),
        ("governance/lifecycle.md.j2", "docs/governance/LIFECYCLE.md"),
        ("governance/roles.md.j2", "docs/governance/ROLES.md"),
        ("governance/context-budget.md.j2", "docs/governance/CONTEXT-BUDGET.md"),
        ("governance/verification.md.j2", "docs/governance/VERIFICATION.md"),
        ("governance/drift-metrics.md.j2", "docs/governance/DRIFT-METRICS.md"),
        # Project docs
        ("docs/architecture.md.j2", "docs/ARCHITECTURE.md"),
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

    # Community / compliance files
    files.extend(_build_community_files(config))

    # Language-specific project files (#41)
    if config.type in (
        ProjectType.CLI_PYTHON,
        ProjectType.LIBRARY_PYTHON,
        ProjectType.BACKEND_FRONTEND,
        ProjectType.BACKEND_FRONTEND_TRAY,
    ):
        files.append(("python/pyproject.toml.j2", "pyproject.toml"))
        files.append(("python/init.py.j2", f"src/{config.package_name}/__init__.py"))
        if config.type == ProjectType.CLI_PYTHON:
            files.append(("python/cli.py.j2", f"src/{config.package_name}/cli.py"))

    elif config.type in (ProjectType.CLI_RUST, ProjectType.LIBRARY_RUST):
        files.append(("rust/Cargo.toml.j2", "Cargo.toml"))
        if config.type == ProjectType.CLI_RUST:
            files.append(("rust/main.rs.j2", "src/main.rs"))

    elif config.type == ProjectType.CLI_GO:
        files.append(("go/go.mod.j2", "go.mod"))
        files.append(("go/main.go.j2", "cmd/main.go"))

    elif config.type in (
        ProjectType.WEB_FRONTEND,
        ProjectType.FULLSTACK_JS,
    ):
        files.append(("js/package.json.j2", "package.json"))

    # ReadTheDocs integration (#38) — Python and doc projects
    if config.type in (
        ProjectType.CLI_PYTHON,
        ProjectType.LIBRARY_PYTHON,
        ProjectType.SPEC_DOCUMENT,
        ProjectType.USER_MANUAL,
    ):
        files.append(("docs/readthedocs.yaml.j2", ".readthedocs.yaml"))
        files.append(("docs/mkdocs.yml.j2", "mkdocs.yml"))

    # Release workflow template (#44) — gitflow + GitHub projects
    if config.vcs_platform == "github" and config.branching_strategy == "gitflow":
        files.append(("workflows/release.yml.j2", ".github/workflows/release.yml"))

    # Epistemic governance layer — for AEE project types or enable_epistemic=True
    _EPISTEMIC_TYPES = {
        ProjectType.EPISTEMIC_PIPELINE,
        ProjectType.KNOWLEDGE_ENGINEERING,
        ProjectType.AEE_RESEARCH,
    }
    if config.type in _EPISTEMIC_TYPES or getattr(config, "enable_epistemic", False):
        files.extend(
            [
                ("governance/epistemic-axioms.md.j2", "docs/governance/EPISTEMIC-AXIOMS.md"),
                ("governance/belief-registry.md.j2", "docs/governance/BELIEF-REGISTRY.md"),
                ("governance/failure-modes.md.j2", "docs/governance/FAILURE-MODES.md"),
                ("governance/uncertainty-map.md.j2", "docs/governance/UNCERTAINTY-MAP.md"),
            ]
        )

    # ReadTheDocs for AEE research/knowledge projects (they produce docs)
    if config.type in {ProjectType.AEE_RESEARCH, ProjectType.KNOWLEDGE_ENGINEERING}:
        files.append(("docs/readthedocs.yaml.j2", ".readthedocs.yaml"))
        files.append(("docs/mkdocs.yml.j2", "mkdocs.yml"))

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
                target / "src",
                target / "icons",
                target / "tests",
            ]
        )
    # --- AEE / Epistemic project types ---
    elif config.type == ProjectType.EPISTEMIC_PIPELINE:
        dirs.extend(
            [
                target / "beliefs",
                target / "pipelines",
                target / "evidence",
                target / "reports",
                target / ".epistemic",
            ]
        )
    elif config.type == ProjectType.KNOWLEDGE_ENGINEERING:
        dirs.extend(
            [
                target / "ontology",
                target / "beliefs",
                target / "evidence",
                target / "queries",
                target / "reports",
            ]
        )
    elif config.type == ProjectType.AEE_RESEARCH:
        dirs.extend(
            [
                target / "hypotheses",
                target / "evidence",
                target / "experiments",
                target / "reports",
                target / ".epistemic",
            ]
        )

    return dirs


# License template mapping: SPDX ID → template filename
_LICENSE_TEMPLATES: dict[str, str] = {
    "MIT": "community/license-MIT.j2",
    "Apache-2.0": "community/license-Apache-2.0.j2",
}


def _build_community_files(config: ProjectConfig) -> list[tuple[str, str]]:
    """Build community/compliance file map based on config.community_files."""
    files: list[tuple[str, str]] = []
    cf = set(config.community_files)

    if "contributing" in cf:
        files.append(("community/contributing.md.j2", "CONTRIBUTING.md"))

    if "license" in cf:
        tmpl = _LICENSE_TEMPLATES.get(config.license)
        if tmpl:
            files.append((tmpl, "LICENSE"))
        # Unsupported license → skip (user provides their own)

    if "security" in cf:
        files.append(("community/security.md.j2", "SECURITY.md"))

    if "coc" in cf:
        files.append(("community/code_of_conduct.md.j2", "CODE_OF_CONDUCT.md"))

    if "pr-template" in cf and config.vcs_platform == "github":
        files.append(("community/pull_request_template.md.j2", ".github/PULL_REQUEST_TEMPLATE.md"))

    if "issue-templates" in cf and config.vcs_platform == "github":
        files.extend(
            [
                ("community/bug_report.md.j2", ".github/ISSUE_TEMPLATE/bug_report.md"),
                ("community/feature_request.md.j2", ".github/ISSUE_TEMPLATE/feature_request.md"),
            ]
        )

    return files


def _init_commands(config: ProjectConfig) -> None:
    """Placeholder for src/specsmith/commands/__init__.py."""
