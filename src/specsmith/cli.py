# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""specsmith CLI — Forge governed project scaffolds."""

from __future__ import annotations

from pathlib import Path

import click
import yaml
from rich.console import Console

from specsmith import __version__
from specsmith.config import Platform, ProjectConfig, ProjectType
from specsmith.scaffolder import scaffold_project

console = Console()

PROJECT_TYPE_CHOICES = {str(i + 1): t for i, t in enumerate(ProjectType)}
PROJECT_TYPE_LABELS = {
    str(i + 1): label
    for i, (t, label) in enumerate(
        __import__("specsmith.config", fromlist=["_TYPE_LABELS"])._TYPE_LABELS.items()
    )
}


@click.group()
@click.version_option(version=__version__, prog_name="specsmith")
def main() -> None:
    """specsmith — Forge governed project scaffolds."""


@main.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True),
    default=None,
    help="Path to scaffold.yml config file (skips interactive prompts).",
)
@click.option(
    "--output-dir", type=click.Path(), default=".", help="Parent directory for the new project."
)
@click.option("--no-git", is_flag=True, default=False, help="Skip git repository initialization.")
@click.option("--guided", is_flag=True, default=False, help="Run guided architecture definition.")
def init(config_path: str | None, output_dir: str, no_git: bool, guided: bool) -> None:
    """Scaffold a new governed project."""
    if config_path:
        raw = _load_config_with_inheritance(config_path)
        cfg = ProjectConfig(**raw)  # type: ignore[arg-type]
        if no_git:
            cfg.git_init = False
    else:
        cfg = _interactive_config(no_git)

    target = Path(output_dir) / cfg.name
    if target.exists() and any(target.iterdir()):
        console.print(f"[red]Error:[/red] Directory {target} already exists and is not empty.")
        raise SystemExit(1)

    console.print(f"\n[bold]Scaffolding [cyan]{cfg.name}[/cyan] ({cfg.type_label})...[/bold]\n")
    created_files = scaffold_project(cfg, target)

    for created in created_files:
        rel = created.relative_to(target)
        console.print(f"  [green]\u2713[/green] {rel}")

    # Guided architecture definition
    if guided:
        guided_files = _run_guided_architecture(cfg, target)
        for path in guided_files:
            rel = path.relative_to(target)
            console.print(f"  [green]\u2713[/green] {rel} (guided)")
        created_files.extend(guided_files)

    console.print(
        f"\n[bold green]Done.[/bold green] {len(created_files)} files created in {target}"
    )
    console.print('Open this project in your AI agent and type [bold]"start"[/bold].')

    # Save config as scaffold.yml for re-runs and upgrades
    config_out = target / "scaffold.yml"
    with open(config_out, "w") as fh:
        yaml.dump(cfg.model_dump(mode="json"), fh, default_flow_style=False, sort_keys=False)


def _load_config_with_inheritance(config_path: str) -> dict[str, object]:
    """Load scaffold.yml, merging parent config if `extends` is set."""
    with open(config_path) as f:
        raw: dict[str, object] = yaml.safe_load(f)

    extends = raw.get("extends", "")
    if isinstance(extends, str) and extends and Path(extends).exists():
        with open(extends) as f:
            parent: dict[str, object] = yaml.safe_load(f) or {}
        # Parent provides defaults; child overrides
        merged: dict[str, object] = {
            **parent,
            **{k: v for k, v in raw.items() if k != "extends"},
        }
        return merged

    return raw


VCS_PLATFORM_CHOICES = {"1": "github", "2": "gitlab", "3": "bitbucket", "4": ""}
VCS_PLATFORM_LABELS = {"1": "GitHub", "2": "GitLab", "3": "Bitbucket", "4": "None"}

BRANCH_STRATEGY_CHOICES = {"1": "gitflow", "2": "trunk-based", "3": "github-flow"}
BRANCH_STRATEGY_LABELS = {"1": "Gitflow", "2": "Trunk-based", "3": "GitHub Flow"}

INTEGRATION_OPTIONS = [
    ("agents-md", "AGENTS.md (always included)"),
    ("warp", "Warp / Oz"),
    ("claude-code", "Claude Code"),
    ("copilot", "GitHub Copilot"),
    ("cursor", "Cursor"),
    ("gemini", "Gemini CLI"),
    ("windsurf", "Windsurf"),
    ("aider", "Aider"),
]


def _interactive_config(no_git: bool) -> ProjectConfig:
    """Gather project config interactively."""
    console.print("[bold]specsmith init[/bold] — interactive scaffold setup\n")

    name = click.prompt("Project name")
    console.print("\nProject type:")
    for k, v in PROJECT_TYPE_LABELS.items():
        console.print(f"  {k}. {v}")
    type_choice = click.prompt("Select type", type=click.Choice(list(PROJECT_TYPE_LABELS.keys())))
    project_type = PROJECT_TYPE_CHOICES[type_choice]

    platforms_str = click.prompt(
        "Target platforms (comma-separated)",
        default="windows, linux, macos",
    )
    platforms = [Platform(p.strip().lower()) for p in platforms_str.split(",")]

    language = click.prompt("Primary language", default="python")
    description = click.prompt("Short description", default="")

    # VCS platform
    console.print("\nVCS platform:")
    for k, v in VCS_PLATFORM_LABELS.items():
        console.print(f"  {k}. {v}")
    vcs_choice = click.prompt("Select platform", default="1")
    vcs_platform = VCS_PLATFORM_CHOICES.get(vcs_choice, "github")

    # Branching strategy
    console.print("\nBranching strategy:")
    for k, v in BRANCH_STRATEGY_LABELS.items():
        console.print(f"  {k}. {v}")
    branch_choice = click.prompt("Select strategy", default="1")
    branching_strategy = BRANCH_STRATEGY_CHOICES.get(branch_choice, "gitflow")

    # Agent integrations
    console.print("\nAgent integrations (comma-separated numbers):")
    for i, (_key, label) in enumerate(INTEGRATION_OPTIONS):
        console.print(f"  {i + 1}. {label}")
    int_input = click.prompt("Select integrations", default="1")
    integrations = ["agents-md"]
    for idx_str in int_input.split(","):
        idx = int(idx_str.strip()) - 1
        if 0 <= idx < len(INTEGRATION_OPTIONS):
            name_val = INTEGRATION_OPTIONS[idx][0]
            if name_val not in integrations:
                integrations.append(name_val)

    return ProjectConfig(
        name=name,
        type=project_type,
        platforms=platforms,
        language=language,
        description=description,
        git_init=not no_git,
        vcs_platform=vcs_platform,
        branching_strategy=branching_strategy,
        integrations=integrations,
    )


@main.command()
@click.option("--fix", is_flag=True, default=False, help="Attempt to fix simple issues.")
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory.",
)
def audit(fix: bool, project_dir: str) -> None:
    """Run drift and health checks (Section 23 + 26)."""
    from specsmith.auditor import run_audit

    root = Path(project_dir).resolve()
    console.print(f"[bold]Auditing[/bold] {root}\n")
    report = run_audit(root)

    for r in report.results:
        icon = "[green]✓[/green]" if r.passed else "[red]✗[/red]"
        console.print(f"  {icon} {r.message}")

    console.print()
    if report.healthy:
        console.print(f"[bold green]Healthy.[/bold green] {report.passed} checks passed.")
    else:
        console.print(
            f"[bold red]{report.failed} issue(s)[/bold red] found "
            f"({report.fixable} fixable). {report.passed} checks passed."
        )
        if fix:
            from specsmith.auditor import run_auto_fix

            fixed = run_auto_fix(root, report)
            if fixed:
                for msg in fixed:
                    console.print(f"  [cyan]⟳[/cyan] {msg}")
                console.print(
                    f"\n[bold cyan]{len(fixed)} issue(s) auto-fixed.[/bold cyan] "
                    f"Re-run audit to verify."
                )
            else:
                console.print("[yellow]No auto-fixable issues found.[/yellow]")
        raise SystemExit(1)


@main.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory.",
)
def validate(project_dir: str) -> None:
    """Check governance file consistency (req ↔ test ↔ arch)."""
    from specsmith.validator import run_validate

    root = Path(project_dir).resolve()
    console.print(f"[bold]Validating[/bold] {root}\n")
    report = run_validate(root)

    for r in report.results:
        icon = "[green]✓[/green]" if r.passed else "[red]✗[/red]"
        console.print(f"  {icon} {r.message}")

    console.print()
    if report.valid:
        console.print(f"[bold green]Valid.[/bold green] {report.passed} checks passed.")
    else:
        console.print(
            f"[bold red]{report.failed} issue(s)[/bold red] found. {report.passed} checks passed."
        )
        raise SystemExit(1)


@main.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory.",
)
@click.option(
    "--threshold",
    type=int,
    default=500,
    help="Only compress if ledger exceeds this many lines.",
)
@click.option(
    "--keep-recent",
    type=int,
    default=10,
    help="Number of recent entries to keep.",
)
def compress(project_dir: str, threshold: int, keep_recent: int) -> None:
    """Archive old ledger entries (Section 26.3)."""
    from specsmith.compressor import run_compress

    root = Path(project_dir).resolve()
    result = run_compress(root, threshold=threshold, keep_recent=keep_recent)
    console.print(result.message)


@main.command()
@click.option("--spec-version", default=None, help="Target spec version to upgrade to.")
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory.",
)
def upgrade(spec_version: str | None, project_dir: str) -> None:
    """Update governance files to match a newer spec version."""
    from specsmith.upgrader import run_upgrade

    root = Path(project_dir).resolve()
    result = run_upgrade(root, target_version=spec_version)
    console.print(result.message)

    if result.updated_files:
        for f in result.updated_files:
            console.print(f"  [green]✓[/green] {f}")
    if result.skipped_files:
        for f in result.skipped_files:
            console.print(f"  [yellow]—[/yellow] {f} (not found, skipped)")


@main.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory.",
)
def status(project_dir: str) -> None:
    """Show VCS platform status (CI, alerts, PRs)."""
    root = Path(project_dir).resolve()
    scaffold_path = root / "scaffold.yml"

    if scaffold_path.exists():
        with open(scaffold_path) as f:
            raw = yaml.safe_load(f)
        platform_name = raw.get("vcs_platform", "github")
    else:
        platform_name = "github"

    if not platform_name:
        console.print("[yellow]No VCS platform configured.[/yellow]")
        return

    from specsmith.vcs import get_platform

    try:
        platform = get_platform(platform_name)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise SystemExit(1) from e

    if not platform.is_cli_available():
        console.print(
            f"[red]{platform.cli_name} CLI not found.[/red] Install it to use status checks."
        )
        raise SystemExit(1)

    console.print(f"[bold]Status[/bold] via {platform.cli_name}\n")
    ps = platform.check_status()
    for detail in ps.details:
        console.print(f"  {detail}")

    if ps.ci_passing is not None:
        icon = "[green]✓[/green]" if ps.ci_passing else "[red]✗[/red]"
        console.print(f"\n  CI: {icon}")


@main.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory.",
)
@click.option(
    "--html", "html_output", type=click.Path(), default=None, help="Generate HTML diff report."
)
def diff(project_dir: str, html_output: str | None) -> None:
    """Compare governance files against spec templates."""
    from specsmith.differ import run_diff

    root = Path(project_dir).resolve()
    results = run_diff(root)

    if html_output:
        from specsmith.differ import run_diff_html

        html = run_diff_html(root)
        Path(html_output).write_text(html, encoding="utf-8")
        console.print(f"[bold green]HTML diff written to {html_output}[/bold green]")
        return

    if not results:
        console.print("[bold green]All governance files match templates.[/bold green]")
        return

    for name, status in results:
        if status == "match":
            console.print(f"  [green]\u2713[/green] {name}")
        elif status == "missing":
            console.print(f"  [red]\u2717[/red] {name} \u2014 missing")
        else:
            console.print(f"  [yellow]~[/yellow] {name} \u2014 differs from template")


@main.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory.",
)
def doctor(project_dir: str) -> None:
    """Check if verification tools are installed locally."""
    from specsmith.doctor import run_doctor

    root = Path(project_dir).resolve()
    report = run_doctor(root)

    if not report.checks:
        console.print("[yellow]No scaffold.yml found — cannot determine tools.[/yellow]")
        return

    console.print(f"[bold]Doctor[/bold] — checking {len(report.checks)} tools\n")
    for check in report.checks:
        if check.installed:
            ver = f" ({check.version})" if check.version else ""
            console.print(f"  [green]✓[/green] {check.category}: {check.name}{ver}")
        else:
            console.print(f"  [red]✗[/red] {check.category}: {check.name} — not found")

    console.print()
    if report.missing_count == 0:
        console.print(f"[bold green]All {report.installed_count} tools available.[/bold green]")
    else:
        console.print(
            f"[bold red]{report.missing_count} tool(s) missing.[/bold red] "
            f"{report.installed_count} installed."
        )


@main.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory.",
)
@click.option(
    "--output",
    type=click.Path(),
    default=None,
    help="Write report to file instead of stdout.",
)
def export(project_dir: str, output: str | None) -> None:
    """Generate a compliance and coverage report."""
    from specsmith.exporter import run_export

    root = Path(project_dir).resolve()
    report = run_export(root)

    if output:
        out_path = Path(output)
        out_path.write_text(report, encoding="utf-8")
        console.print(f"[bold green]Report written to {out_path}[/bold green]")
    else:
        console.print(report)


@main.command(name="import")
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory to import.",
)
@click.option("--force", is_flag=True, default=False, help="Overwrite existing governance files.")
@click.option("--guided", is_flag=True, default=False, help="Run guided architecture after import.")
@click.option(
    "--dry-run", is_flag=True, default=False, help="Show what would be done without writing."
)
def import_project(project_dir: str, force: bool, guided: bool, dry_run: bool) -> None:
    """Import an existing project and generate governance overlay."""
    from specsmith.importer import detect_project, generate_import_config, generate_overlay

    root = Path(project_dir).resolve()
    console.print(f"[bold]Analyzing[/bold] {root}...\n")

    result = detect_project(root)

    console.print(f"  Files: {result.file_count}")
    console.print(f"  Language: [cyan]{result.primary_language or 'unknown'}[/cyan]")
    console.print(f"  Build system: {result.build_system or 'not detected'}")
    console.print(f"  Test framework: {result.test_framework or 'not detected'}")
    console.print(f"  CI: {result.existing_ci or 'not detected'}")
    console.print(f"  VCS: {result.vcs_platform or 'not detected'}")
    inferred = result.inferred_type.value if result.inferred_type else "unknown"
    console.print(f"  Inferred type: [cyan]{inferred}[/cyan]")

    if result.modules:
        console.print(f"  Modules: {', '.join(result.modules)}")
    if result.existing_governance:
        console.print(f"  Existing governance: {', '.join(result.existing_governance)}")
    if result.test_files:
        console.print(f"  Test files: {len(result.test_files)}")
    if result.dependencies:
        console.print(f"  Dependencies: {len(result.dependencies)}")
    if result.readme_summary:
        console.print(f"  README: {result.readme_summary[:80]}...")
    if result.detected_ci_tools:
        tools_str = ", ".join(
            f"{cat}: {'/'.join(t)}" for cat, t in result.detected_ci_tools.items()
        )
        console.print(f"  CI tools: {tools_str}")
    if result.ci_tool_gaps:
        console.print(f"  [yellow]CI gaps: {', '.join(result.ci_tool_gaps)}[/yellow]")
    if result.git_contributors:
        console.print(f"  Contributors: {len(result.git_contributors)}")
    console.print()

    if dry_run:
        console.print("[bold]Dry run — no files will be written.[/bold]\n")
        overlay_files = [
            "AGENTS.md",
            "LEDGER.md",
            "docs/REQUIREMENTS.md",
            "docs/TEST_SPEC.md",
            "docs/architecture.md",
            "scaffold.yml",
            "docs/governance/rules.md",
            "docs/governance/workflow.md",
            "docs/governance/roles.md",
            "docs/governance/context-budget.md",
            "docs/governance/verification.md",
            "docs/governance/drift-metrics.md",
        ]
        for f in overlay_files:
            exists = (root / f).exists()
            action = "SKIP (exists)" if exists and not force else "CREATE"
            icon = "[yellow]—[/yellow]" if exists and not force else "[green]\u2713[/green]"
            console.print(f"  {icon} {action:14s} {f}")
        ci_msg = "SKIP (CI exists)" if result.existing_ci else "GENERATE"
        ci_icon = "[yellow]\u2014[/yellow]" if result.existing_ci else "[green]\u2713[/green]"
        console.print(f"  {ci_icon} {ci_msg:14s} CI config")
        return

    # Allow override
    if not click.confirm("Proceed with these settings?", default=True):
        console.print("\nProject type:")
        for k, v in PROJECT_TYPE_LABELS.items():
            console.print(f"  {k}. {v}")
        type_choice = click.prompt(
            "Select type", type=click.Choice(list(PROJECT_TYPE_LABELS.keys()))
        )
        result.inferred_type = PROJECT_TYPE_CHOICES[type_choice]
        result.primary_language = click.prompt("Primary language", default=result.primary_language)

    config = generate_import_config(result)
    created = generate_overlay(result, root, force=force)

    for path in created:
        rel = path.relative_to(root)
        console.print(f"  [green]\u2713[/green] {rel}")

    # Save scaffold.yml
    config_out = root / "scaffold.yml"
    if not config_out.exists() or force:
        with open(config_out, "w") as fh:
            yaml.dump(config.model_dump(mode="json"), fh, default_flow_style=False, sort_keys=False)
        console.print("  [green]\u2713[/green] scaffold.yml")

    # Guided architecture definition after import
    if guided:
        guided_files = _run_guided_architecture(config, root)
        for path in guided_files:
            rel = path.relative_to(root)
            console.print(f"  [green]\u2713[/green] {rel} (guided)")
        created.extend(guided_files)

    console.print(f"\n[bold green]Done.[/bold green] {len(created)} governance files generated.")
    console.print('Open this project in your AI agent and type [bold]"start"[/bold].')


def _run_guided_architecture(cfg: ProjectConfig, target: Path) -> list[Path]:
    """Run interactive architecture definition and generate REQ/TEST stubs."""
    created: list[Path] = []

    console.print("\n[bold]Guided Architecture Definition[/bold]\n")
    console.print("Define your project's major components/modules (comma-separated):")
    components_str = click.prompt("Components", default="core")
    components = [c.strip() for c in components_str.split(",") if c.strip()]

    # Generate REQUIREMENTS.md with REQ stubs
    reqs_path = target / "docs" / "REQUIREMENTS.md"
    reqs_content = "# Requirements\n\n"
    for comp in components:
        comp_upper = comp.upper().replace(" ", "-")
        reqs_content += (
            f"## REQ-{comp_upper}-001\n"
            f"- **Component**: {comp}\n"
            f"- **Status**: Draft\n"
            f"- **Description**: [Core functionality for {comp}]\n\n"
            f"## REQ-{comp_upper}-002\n"
            f"- **Component**: {comp}\n"
            f"- **Status**: Draft\n"
            f"- **Description**: [Error handling for {comp}]\n\n"
        )
    reqs_path.write_text(reqs_content, encoding="utf-8")
    created.append(reqs_path)

    # Generate TEST_SPEC.md with TEST stubs
    tests_path = target / "docs" / "TEST_SPEC.md"
    tests_content = "# Test Specification\n\n"
    test_num = 1
    for comp in components:
        comp_upper = comp.upper().replace(" ", "-")
        tests_content += (
            f"## TEST-{test_num:03d}\n"
            f"- **Requirement**: REQ-{comp_upper}-001\n"
            f"- **Type**: Unit\n"
            f"- **Description**: Verify core {comp} functionality\n\n"
        )
        test_num += 1
        tests_content += (
            f"## TEST-{test_num:03d}\n"
            f"- **Requirement**: REQ-{comp_upper}-002\n"
            f"- **Type**: Unit\n"
            f"- **Description**: Verify {comp} error handling\n\n"
        )
        test_num += 1
    tests_path.write_text(tests_content, encoding="utf-8")
    created.append(tests_path)

    # Generate architecture.md
    arch_path = target / "docs" / "architecture.md"
    arch_content = f"# Architecture \u2014 {cfg.name}\n\n## Components\n\n"
    for comp in components:
        arch_content += (
            f"### {comp}\n"
            f"- **Purpose**: [Describe {comp} purpose]\n"
            f"- **Interfaces**: [Define {comp} interfaces]\n"
            f"- **Dependencies**: [List {comp} dependencies]\n\n"
        )
    arch_content += (
        "## Data Flow\n\n"
        "[Describe how data flows between components]\n\n"
        "## Deployment\n\n"
        f"- **Language**: {cfg.language}\n"
        f"- **Platforms**: {', '.join(cfg.platform_names)}\n"
    )
    arch_path.write_text(arch_content, encoding="utf-8")
    created.append(arch_path)

    return created


# ---------------------------------------------------------------------------
# Ledger subcommands
# ---------------------------------------------------------------------------


@main.group()
def ledger() -> None:
    """Manage the change ledger."""


@ledger.command(name="add")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--type", "entry_type", default="task", help="Entry type (task, feature, fix, etc.)")
@click.option("--author", default="agent")
@click.option("--reqs", default="", help="Affected REQ IDs (comma-separated).")
@click.argument("description")
def ledger_add(project_dir: str, entry_type: str, author: str, reqs: str, description: str) -> None:
    """Add a structured entry to LEDGER.md."""
    from specsmith.ledger import add_entry

    root = Path(project_dir).resolve()
    entry = add_entry(
        root, description=description, entry_type=entry_type, author=author, reqs=reqs
    )
    console.print(f"[green]Added:[/green] {entry.splitlines()[0]}")


@ledger.command(name="list")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--since", default="", help="Show entries since date (YYYY-MM-DD).")
def ledger_list(project_dir: str, since: str) -> None:
    """List ledger entries."""
    from specsmith.ledger import list_entries

    root = Path(project_dir).resolve()
    entries = list_entries(root, since=since)
    if not entries:
        console.print("[yellow]No entries found.[/yellow]")
        return
    for e in entries:
        heading = e.get("heading", "")
        status = e.get("status", "")
        console.print(f"  {heading}" + (f" [{status}]" if status else ""))


@ledger.command(name="stats")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def ledger_stats(project_dir: str) -> None:
    """Show ledger statistics."""
    from specsmith.ledger import get_stats

    root = Path(project_dir).resolve()
    stats = get_stats(root)
    console.print(f"  Entries: {stats['total_entries']}")
    authors = stats.get("authors", {})
    if isinstance(authors, dict):
        for name, count in authors.items():
            console.print(f"  {name}: {count} entries")


main.add_command(ledger)


# ---------------------------------------------------------------------------
# Requirements subcommands
# ---------------------------------------------------------------------------


@main.group()
def req() -> None:
    """Manage requirements."""


@req.command(name="list")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def req_list(project_dir: str) -> None:
    """List all requirements."""
    from specsmith.requirements import list_reqs

    reqs = list_reqs(Path(project_dir).resolve())
    if not reqs:
        console.print("[yellow]No requirements found.[/yellow]")
        return
    for r in reqs:
        status = r.get("status", "")
        priority = r.get("priority", "")
        desc = r.get("description", "")[:60]
        console.print(f"  {r['id']:20s} {status:12s} {priority:8s} {desc}")
    console.print(f"\n  {len(reqs)} requirement(s)")


@req.command(name="add")
@click.argument("req_id")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--component", default="")
@click.option("--priority", default="medium")
@click.option("--description", default="")
def req_add(req_id: str, project_dir: str, component: str, priority: str, description: str) -> None:
    """Add a new requirement."""
    from specsmith.requirements import add_req

    add_req(
        Path(project_dir).resolve(),
        req_id,
        component=component,
        priority=priority,
        description=description,
    )
    console.print(f"[green]Added {req_id}[/green]")


@req.command(name="trace")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def req_trace(project_dir: str) -> None:
    """Show REQ → TEST traceability."""
    from specsmith.requirements import trace_reqs

    traces = trace_reqs(Path(project_dir).resolve())
    for t in traces:
        icon = "[green]\u2713[/green]" if t["covered"] else "[red]\u2717[/red]"
        tests = ", ".join(t["tests"]) if t["tests"] else "(none)"  # type: ignore[arg-type]
        console.print(f"  {icon} {t['req']:20s} \u2192 {tests}")


@req.command(name="gaps")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def req_gaps(project_dir: str) -> None:
    """List requirements without test coverage."""
    from specsmith.requirements import get_gaps

    gaps = get_gaps(Path(project_dir).resolve())
    if not gaps:
        console.print("[bold green]All requirements have test coverage.[/bold green]")
        return
    for g in gaps:
        console.print(f"  [red]\u2717[/red] {g}")
    console.print(f"\n  {len(gaps)} uncovered requirement(s)")


@req.command(name="orphans")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def req_orphans(project_dir: str) -> None:
    """List tests referencing non-existent requirements."""
    from specsmith.requirements import get_orphan_tests

    orphans = get_orphan_tests(Path(project_dir).resolve())
    if not orphans:
        console.print("[bold green]No orphaned test references.[/bold green]")
        return
    for o in orphans:
        console.print(f"  [yellow]\u26a0[/yellow] {o}")


main.add_command(req)


# ---------------------------------------------------------------------------
# Migrate command
# ---------------------------------------------------------------------------


@main.command()
@click.option("--to", "new_type", required=True, help="Target project type.")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def migrate(new_type: str, project_dir: str) -> None:
    """Change the project type and regenerate type-dependent files."""
    root = Path(project_dir).resolve()
    scaffold_path = root / "scaffold.yml"

    if not scaffold_path.exists():
        console.print("[red]No scaffold.yml found.[/red]")
        raise SystemExit(1)

    with open(scaffold_path) as f:
        raw = yaml.safe_load(f)

    old_type = raw.get("type", "unknown")
    raw["type"] = new_type

    # Validate new type
    try:
        config = ProjectConfig(**raw)
    except Exception as e:
        console.print(f"[red]Invalid type '{new_type}': {e}[/red]")
        raise SystemExit(1) from e

    # Save updated scaffold.yml
    with open(scaffold_path, "w") as f:
        yaml.dump(raw, f, default_flow_style=False, sort_keys=False)
    console.print(f"  [green]\u2713[/green] scaffold.yml: {old_type} \u2192 {new_type}")

    # Add missing directories for new type
    from specsmith.scaffolder import _get_empty_dirs

    for empty_dir in _get_empty_dirs(config, root):
        gitkeep = empty_dir / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.parent.mkdir(parents=True, exist_ok=True)
            gitkeep.write_text("", encoding="utf-8")
            console.print(f"  [green]\u2713[/green] {empty_dir.relative_to(root)}/")

    # Regenerate CI + agent files
    from specsmith.cli import apply as apply_cmd

    ctx = click.Context(apply_cmd, info_name="apply")
    ctx.invoke(apply_cmd, project_dir=project_dir)

    # Ledger entry
    from specsmith.ledger import add_entry

    add_entry(
        root, description=f"Migrated type: {old_type} \u2192 {new_type}", entry_type="migration"
    )
    console.print(f"\n[bold green]Migrated to {config.type_label}.[/bold green]")


@main.command()
@click.argument("version")
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory.",
)
def release(version: str, project_dir: str) -> None:
    """Bump version in all locations and scan for stale refs."""
    from specsmith.releaser import bump_version, scan_stale_refs

    root = Path(project_dir).resolve()

    console.print(f"[bold]Bumping to {version}[/bold]\n")
    updated = bump_version(root, version)
    for f in updated:
        console.print(f"  [green]\u2713[/green] {f}")

    console.print("\n[bold]Scanning for stale references...[/bold]\n")
    issues = scan_stale_refs(root, version)
    if issues:
        for issue in issues:
            console.print(f"  [yellow]\u26a0[/yellow] {issue}")
        console.print(f"\n[bold yellow]{len(issues)} issue(s) found.[/bold yellow]")
    else:
        console.print("  No stale references found.")

    console.print(
        f"\n[bold]Next steps:[/bold]\n"
        f"  1. Update CHANGELOG.md with [{version}] section\n"
        f"  2. git add -A && git commit -m 'release: v{version}'\n"
        f"  3. git checkout main && git merge develop\n"
        f"  4. git tag -a v{version} -m 'v{version}'\n"
        f"  5. git push origin main develop --tags"
    )


@main.command(name="verify-release")
def verify_release() -> None:
    """Check PyPI, RTD, and GitHub release status after a release."""
    import subprocess
    import urllib.request

    from specsmith import __version__

    console.print(f"[bold]Verifying release v{__version__}[/bold]\n")
    checks_passed = 0
    checks_failed = 0

    # PyPI
    try:
        url = "https://pypi.org/pypi/specsmith/json"
        resp = urllib.request.urlopen(url, timeout=10)  # noqa: S310
        import json

        data = json.loads(resp.read())
        pypi_version = data["info"]["version"]
        if pypi_version == __version__:
            console.print(f"  [green]\u2713[/green] PyPI: v{pypi_version}")
            checks_passed += 1
        else:
            console.print(f"  [red]\u2717[/red] PyPI: v{pypi_version} (expected {__version__})")
            checks_failed += 1
    except Exception:  # noqa: BLE001
        console.print("  [red]\u2717[/red] PyPI: could not reach pypi.org")
        checks_failed += 1

    # RTD
    try:
        resp = urllib.request.urlopen(  # noqa: S310
            "https://specsmith.readthedocs.io/en/latest/", timeout=10
        )
        if resp.status == 200:
            console.print("  [green]\u2713[/green] RTD: site is live")
            checks_passed += 1
        else:
            console.print(f"  [red]\u2717[/red] RTD: status {resp.status}")
            checks_failed += 1
    except Exception:  # noqa: BLE001
        console.print("  [red]\u2717[/red] RTD: could not reach readthedocs.io")
        checks_failed += 1

    # GitHub release
    try:
        result = subprocess.run(
            ["gh", "release", "view", f"v{__version__}", "--json", "tagName"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            console.print(f"  [green]\u2713[/green] GitHub Release: v{__version__}")
            checks_passed += 1
        else:
            console.print(f"  [red]\u2717[/red] GitHub Release: v{__version__} not found")
            checks_failed += 1
    except Exception:  # noqa: BLE001
        console.print("  [yellow]\u2014[/yellow] GitHub Release: gh CLI not available")

    console.print()
    if checks_failed == 0:
        console.print(f"[bold green]All {checks_passed} checks passed.[/bold green]")
    else:
        console.print(
            f"[bold red]{checks_failed} check(s) failed.[/bold red] {checks_passed} passed."
        )


@main.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory.",
)
def apply(project_dir: str) -> None:
    """Regenerate CI and agent files from current scaffold.yml."""
    root = Path(project_dir).resolve()
    scaffold_path = root / "scaffold.yml"

    if not scaffold_path.exists():
        console.print("[red]No scaffold.yml found.[/red]")
        raise SystemExit(1)

    with open(scaffold_path) as f:
        raw = yaml.safe_load(f)

    config = ProjectConfig(**raw)
    created: list[Path] = []

    # Regenerate VCS platform files
    if config.vcs_platform:
        from specsmith.vcs import get_platform

        try:
            platform = get_platform(config.vcs_platform)
            created.extend(platform.generate_all(config, root))
        except ValueError:
            pass

    # Regenerate agent integration files
    for integration_name in config.integrations:
        if integration_name == "agents-md":
            continue
        try:
            from specsmith.integrations import get_adapter

            adapter = get_adapter(integration_name)
            created.extend(adapter.generate(config, root))
        except ValueError:
            pass

    if created:
        for path in created:
            rel = path.relative_to(root)
            console.print(f"  [green]\u2713[/green] {rel}")
        console.print(f"\n[bold green]{len(created)} file(s) regenerated.[/bold green]")
    else:
        console.print("[yellow]Nothing to regenerate.[/yellow]")


# ---------------------------------------------------------------------------
# VCS commands
# ---------------------------------------------------------------------------


@main.command(name="commit")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--message", "-m", default="", help="Override commit message.")
@click.option("--no-audit", is_flag=True, default=False, help="Skip pre-commit audit.")
@click.option("--auto-push", is_flag=True, default=False, help="Push after commit.")
def commit_cmd(project_dir: str, message: str, no_audit: bool, auto_push: bool) -> None:
    """Stage, audit, and commit with governance-aware message."""
    from specsmith.vcs_commands import (
        has_uncommitted_changes,
        is_ledger_modified_since_last_commit,
        run_commit,
    )

    root = Path(project_dir).resolve()

    if not has_uncommitted_changes(root):
        console.print("[yellow]Nothing to commit.[/yellow]")
        return

    if not is_ledger_modified_since_last_commit(root):
        console.print("[yellow]\u26a0 LEDGER.md not updated since last commit.[/yellow]")
        if not click.confirm("Commit anyway?", default=False):
            return

    if not no_audit:
        from specsmith.auditor import run_audit

        report = run_audit(root)
        if not report.healthy:
            console.print(f"[yellow]\u26a0 Audit: {report.failed} issue(s)[/yellow]")

    result = run_commit(root, message=message, auto_push=auto_push)
    if result.success:
        console.print(f"[green]\u2713[/green] {result.message}")
    else:
        console.print(f"[red]\u2717[/red] {result.message}")


@main.command(name="push")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--force", is_flag=True, default=False, help="Override safety checks.")
def push_cmd(project_dir: str, force: bool) -> None:
    """Push current branch with safety checks."""
    from specsmith.vcs_commands import run_push

    result = run_push(Path(project_dir).resolve(), force=force)
    if result.success:
        console.print(f"[green]\u2713[/green] {result.message}")
    else:
        console.print(f"[red]\u2717[/red] {result.message}")


@main.group(name="branch")
def branch_group() -> None:
    """Branch management."""


@branch_group.command(name="create")
@click.argument("name")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def branch_create(name: str, project_dir: str) -> None:
    """Create a branch following the branching strategy."""
    root = Path(project_dir).resolve()
    scaffold_path = root / "scaffold.yml"
    strategy = "gitflow"
    main_branch = "main"
    if scaffold_path.exists():
        with open(scaffold_path) as f:
            raw = yaml.safe_load(f) or {}
        strategy = raw.get("branching_strategy", "gitflow")
        main_branch = raw.get("default_branch", "main")

    from specsmith.vcs_commands import create_branch

    result = create_branch(root, name, strategy=strategy, main_branch=main_branch)
    if result.success:
        console.print(f"[green]\u2713[/green] {result.message}")
    else:
        console.print(f"[red]\u2717[/red] {result.message}")


@branch_group.command(name="list")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def branch_list(project_dir: str) -> None:
    """List branches with strategy context."""
    from specsmith.vcs_commands import list_branches

    branches = list_branches(Path(project_dir).resolve())
    for b in branches:
        marker = "*" if b["current"] else " "
        role = f" ({b['role']})" if b["role"] else ""
        console.print(f"  {marker} {b['name']}{role}")


main.add_command(branch_group)


@main.command(name="pr")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--title", default="", help="PR title.")
@click.option("--draft", is_flag=True, default=False, help="Create as draft.")
def pr_cmd(project_dir: str, title: str, draft: bool) -> None:
    """Create a PR with governance context."""
    from specsmith.exporter import run_export
    from specsmith.vcs_commands import create_pr

    root = Path(project_dir).resolve()
    summary = run_export(root)[:2000]  # Cap for PR body
    result = create_pr(root, title=title, draft=draft, governance_summary=summary)
    if result.success:
        console.print(f"[green]\u2713[/green] {result.message}")
    else:
        console.print(f"[red]\u2717[/red] {result.message}")


@main.command(name="sync")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def sync_cmd(project_dir: str) -> None:
    """Pull latest and check for governance conflicts."""
    from specsmith.vcs_commands import run_sync

    result = run_sync(Path(project_dir).resolve())
    if result.success:
        console.print(f"[green]\u2713[/green] {result.message}")
    else:
        console.print(f"[red]\u2717[/red] {result.message}")


# ---------------------------------------------------------------------------
# Update and migration
# ---------------------------------------------------------------------------


@main.command(name="update")
@click.option("--check", "check_only", is_flag=True, default=False, help="Check only.")
@click.option("--yes", "auto_yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def update_cmd(check_only: bool, auto_yes: bool, project_dir: str) -> None:
    """Check for updates and optionally install + migrate."""
    from specsmith.updater import (
        check_latest_version,
        needs_migration,
        run_migration,
        run_self_update,
    )

    current, latest = check_latest_version()
    if not latest:
        console.print("[yellow]Could not reach PyPI.[/yellow]")
        return

    if current == latest:
        console.print(f"[green]\u2713[/green] specsmith {current} is up to date.")
    else:
        console.print(f"  Current: {current}")
        console.print(f"  Latest:  {latest}")

        if check_only:
            console.print("[yellow]Update available.[/yellow] Run: specsmith update")
            return

        if auto_yes or click.confirm(f"Update to {latest}?", default=True):
            success, msg = run_self_update()
            if success:
                console.print(f"[green]\u2713[/green] Updated to {latest}")
            else:
                console.print(f"[red]\u2717[/red] Update failed: {msg}")
                return

    # Check project migration
    root = Path(project_dir).resolve()
    if needs_migration(root):
        console.print("\n[yellow]Project needs migration.[/yellow]")
        if auto_yes or click.confirm("Run migrate-project?", default=True):
            actions = run_migration(root)
            for a in actions:
                console.print(f"  [green]\u2713[/green] {a}")


@main.command(name="migrate-project")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--dry-run", is_flag=True, default=False, help="Show changes without writing.")
def migrate_project_cmd(project_dir: str, dry_run: bool) -> None:
    """Migrate project to current specsmith version."""
    from specsmith.updater import run_migration

    root = Path(project_dir).resolve()
    actions = run_migration(root, dry_run=dry_run)
    prefix = "[dim](dry run)[/dim] " if dry_run else ""
    for a in actions:
        console.print(f"  {prefix}{a}")


@main.command(name="session-end")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def session_end_cmd(project_dir: str) -> None:
    """Run session-end checklist."""
    from specsmith.session import run_session_end

    root = Path(project_dir).resolve()
    report = run_session_end(root)

    console.print("[bold]Session End Checklist[/bold]\n")
    for check in report.checks:
        if check.status == "ok":
            console.print(f"  [green]\u2713[/green] {check.message}")
        elif check.status == "warn":
            console.print(f"  [yellow]\u26a0[/yellow] {check.message}")
        else:
            console.print(f"  [red]\u2717[/red] {check.message}")

    console.print()
    if report.action_count > 0:
        console.print(
            f"[bold red]{report.action_count} action(s) needed before ending session.[/bold red]"
        )
    elif report.warn_count > 0:
        console.print(f"[bold yellow]{report.warn_count} warning(s).[/bold yellow]")
    else:
        console.print("[bold green]Session clean. Ready to end.[/bold green]")


# ---------------------------------------------------------------------------
# Plugin system
# ---------------------------------------------------------------------------


@main.command(name="plugin")
def plugin_list() -> None:
    """List installed specsmith plugins."""
    from specsmith.plugins import discover_plugins

    plugins = discover_plugins()
    if not plugins:
        console.print("No plugins installed.")
        console.print(
            "\nPlugins register via pyproject.toml entry points:"
            "\n  [project.entry-points.'specsmith.types']\n"
            "  my-type = 'my_plugin:register_type'"
        )
        return

    for p in plugins:
        if p.loaded:
            console.print(f"  [green]\u2713[/green] {p.group}/{p.name} ({p.module})")
        else:
            console.print(f"  [red]\u2717[/red] {p.group}/{p.name} \u2014 {p.error}")
    console.print(f"\n  {len(plugins)} plugin(s)")


# ---------------------------------------------------------------------------
# Serve (API for React dashboard)
# ---------------------------------------------------------------------------


@main.command()
@click.option("--port", default=8910, help="Port to serve on.")
def serve(port: int) -> None:
    """Start local API server for the web dashboard."""
    console.print(f"[bold]Starting specsmith API server on port {port}...[/bold]")
    console.print("[yellow]Not yet implemented. See issue #14.[/yellow]")
    console.print(
        "\nPlanned endpoints:\n"
        "  GET  /api/projects          \u2014 list governed projects\n"
        "  POST /api/projects/init     \u2014 scaffold new project\n"
        "  POST /api/projects/import   \u2014 import existing project\n"
        "  GET  /api/projects/:id/audit   \u2014 run audit\n"
        "  GET  /api/projects/:id/export  \u2014 generate report\n"
        "  GET  /api/types             \u2014 list all 30 project types\n"
        "  GET  /api/tools/:type       \u2014 tool registry for a type"
    )


if __name__ == "__main__":
    main()
