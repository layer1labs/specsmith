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

PROJECT_TYPE_CHOICES = {
    "1": ProjectType.BACKEND_FRONTEND,
    "2": ProjectType.BACKEND_FRONTEND_TRAY,
    "3": ProjectType.CLI_PYTHON,
    "4": ProjectType.LIBRARY_PYTHON,
    "5": ProjectType.EMBEDDED_HARDWARE,
    "6": ProjectType.FPGA_RTL,
    "7": ProjectType.YOCTO_BSP,
    "8": ProjectType.PCB_HARDWARE,
}

PROJECT_TYPE_LABELS = {
    "1": "Python backend + web frontend",
    "2": "Python backend + web frontend + tray",
    "3": "CLI tool (Python)",
    "4": "Library / SDK (Python)",
    "5": "Embedded / hardware",
    "6": "FPGA / RTL",
    "7": "Yocto / embedded Linux BSP",
    "8": "PCB / hardware design",
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
def init(config_path: str | None, output_dir: str, no_git: bool) -> None:
    """Scaffold a new governed project."""
    if config_path:
        with open(config_path) as f:
            raw = yaml.safe_load(f)
        cfg = ProjectConfig(**raw)
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
        console.print(f"  [green]✓[/green] {rel}")

    console.print(
        f"\n[bold green]Done.[/bold green] {len(created_files)} files created in {target}"
    )
    console.print('Open this project in your AI agent and type [bold]"start"[/bold].')

    # Save config as scaffold.yml for re-runs and upgrades
    config_out = target / "scaffold.yml"
    with open(config_out, "w") as fh:
        yaml.dump(cfg.model_dump(mode="json"), fh, default_flow_style=False, sort_keys=False)


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

    return ProjectConfig(
        name=name,
        type=project_type,
        platforms=platforms,
        language=language,
        description=description,
        git_init=not no_git,
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
            console.print("[yellow]Auto-fix not yet implemented.[/yellow]")
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


if __name__ == "__main__":
    main()
