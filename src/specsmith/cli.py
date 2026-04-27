# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""specsmith CLI — Forge governed project scaffolds."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import click
import yaml
from rich.console import Console

from specsmith import __version__
from specsmith.config import Platform, ProjectConfig, ProjectType
from specsmith.scaffolder import scaffold_project
from specsmith.requirements_parser import parse_architecture_requirements, define_test_cases

console = Console()

PROJECT_TYPE_CHOICES = {str(i + 1): t for i, t in enumerate(ProjectType)}
PROJECT_TYPE_LABELS = {
    str(i + 1): label
    for i, (t, label) in enumerate(
        __import__("specsmith.config", fromlist=["_TYPE_LABELS"])._TYPE_LABELS.items()
    )
}


class _AutoUpdateGroup(click.Group):
    """Click group that checks project spec_version on every command invocation.

    If the project's scaffold.yml spec_version doesn't match the installed
    specsmith version, prompts the user to migrate. Skippable with
    SPECSMITH_NO_AUTO_UPDATE=1 or when running meta-commands (update, version).
    """

    # Commands that should not trigger the version check
    _SKIP_COMMANDS = {
        "update",
        "self-update",
        "migrate-project",
        "verify-release",
        "plugin",
        "--version",
        "help",
    }

    def invoke(self, ctx: click.Context) -> object:
        import os

        # Skip if explicitly disabled or if this is a meta-command
        # ctx.protected_args is deprecated in Click 9.0; suppress the warning
        # on access (it still works in 8.x). In 9.0 the subcommand moves to args.
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            protected = list(ctx.protected_args)  # [subcommand] in 8.x, [] in 9.0
        subcommand = protected[0] if protected else (ctx.args[0] if ctx.args else "")
        skip = (
            os.environ.get("SPECSMITH_NO_AUTO_UPDATE", "").strip() in ("1", "true", "yes")
            or subcommand in self._SKIP_COMMANDS
        )

        if not skip:
            _maybe_prompt_project_update()
            _maybe_notify_pypi_update()

        return super().invoke(ctx)


def _maybe_prompt_project_update() -> None:
    """Check if the project's scaffold.yml is behind the installed version.

    If so, print a one-line prompt and offer Y/n to migrate.
    Runs in under 5ms for projects that are up to date (no network call).
    """
    import os
    from pathlib import Path

    # Look for scaffold.yml in CWD
    scaffold_path = Path(".") / "scaffold.yml"
    if not scaffold_path.exists():
        return  # Not a specsmith project — skip silently

    try:
        import yaml

        with open(scaffold_path) as f:
            raw = yaml.safe_load(f) or {}
        project_ver = raw.get("spec_version", "")
        if not project_ver or project_ver == __version__:
            return  # Up to date or no version recorded

        # Only prompt once per shell session (track via env var)
        session_key = f"SPECSMITH_CHECKED_{project_ver}_{__version__}"
        if os.environ.get(session_key):
            return
        os.environ[session_key] = "1"

        console.print(
            f"\n[yellow]⚠[/yellow] Project spec [bold]{project_ver}[/bold] → "
            f"specsmith [bold]{__version__}[/bold] installed. "
            rf"Migrate now? [bold]\[Y/n][/bold] ",
            end="",
        )
        try:
            answer = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            console.print()
            return

        if answer in ("", "y", "yes"):
            from specsmith.updater import run_migration

            console.print("[cyan]Migrating project...[/cyan]")
            actions = run_migration(Path("."))
            for a in actions:
                console.print(f"  [green]✓[/green] {a}")
        else:
            console.print(
                "  [dim]Skipped. Run [bold]specsmith migrate-project[/bold] when ready. "
                "Set SPECSMITH_NO_AUTO_UPDATE=1 to suppress this prompt.[/dim]"
            )
    except Exception:  # noqa: BLE001
        pass  # Never break the actual command on version check errors


def _maybe_notify_pypi_update() -> None:
    """Check PyPI for a newer specsmith version. Prints one-liner if outdated.

    Runs at most once per shell session (tracked via env var). Uses a 3-second
    timeout to avoid blocking the CLI. Only checks stable versions.
    """
    import os

    session_key = "SPECSMITH_PYPI_CHECKED"
    if os.environ.get(session_key):
        return
    os.environ[session_key] = "1"

    try:
        import json as _json  # noqa: PLC0415
        from urllib.request import urlopen  # noqa: PLC0415

        resp = urlopen("https://pypi.org/pypi/specsmith/json", timeout=3)  # noqa: S310
        data = _json.loads(resp.read())
        latest = data.get("info", {}).get("version", "")
        if not latest:
            return

        # Simple version comparison: split into tuples of ints
        def _ver(v: str) -> tuple[int, ...]:
            import re

            clean = re.match(r"(\d+\.\d+\.\d+)", v)
            return tuple(int(x) for x in clean.group(1).split(".")) if clean else (0,)

        if _ver(latest) > _ver(__version__):
            console.print(
                f"  [dim]specsmith [bold]{latest}[/bold] available "
                f"(you have {__version__}). "
                f"Run [bold]specsmith self-update[/bold] or "
                f"[bold]pipx upgrade specsmith[/bold].[/dim]"
            )
    except Exception:  # noqa: BLE001
        pass  # Never block the CLI on network errors


@click.group(cls=_AutoUpdateGroup)
@click.version_option(version=__version__, prog_name="specsmith")
def main() -> None:
    """specsmith — AEE toolkit. Forge epistemically-governed project scaffolds."""


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
    console.print('Project scaffolded. Review generated files.')

    # Save config as scaffold.yml for re-runs and upgrades
    config_out = target / "scaffold.yml"
    with open(config_out, "w") as fh:
        yaml.dump(cfg.model_dump(mode="json"), fh, default_flow_style=False, sort_keys=False)

    # Ensure AEE phase is set (write_phase appends to scaffold.yml)
    from specsmith.phase import write_phase

    write_phase(target, "inception")


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

    return ProjectConfig(
        name=name,
        type=project_type,
        platforms=platforms,
        language=language,
        description=description,
        git_init=not no_git,
        vcs_platform=vcs_platform,
        branching_strategy=branching_strategy,
        integrations=["agents-md"], # Keep AGENTS.md as a default, non-AI specific integration
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
@click.option(
    "--full",
    is_flag=True,
    default=False,
    help="Full sync: also regenerate exec shims, CI, agent files, create missing community files.",
)
def upgrade(spec_version: str | None, project_dir: str, full: bool) -> None:
    """Update governance files to match a newer spec version.

    With --full: also regenerates exec shims (PID tracking), CI configs,
    agent integrations, and creates missing community files. Safe: never
    overwrites AGENTS.md, LEDGER.md, or user documentation.
    """
    from specsmith.upgrader import run_upgrade

    root = Path(project_dir).resolve()
    result = run_upgrade(root, target_version=spec_version, full=full)
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
@click.option(
    "--yes",
    "-y",
    "auto_yes",
    is_flag=True,
    default=False,
    help="Skip confirmation prompt (non-interactive / CI mode).",
)
def import_project(
    project_dir: str, force: bool, guided: bool, dry_run: bool, auto_yes: bool
) -> None:
    """Import an existing project and generate governance overlay."""
    from specsmith.importer import detect_project, generate_import_config, generate_overlay

    root = Path(project_dir).resolve()
    console.print(f"[bold]Analyzing[/bold] {root}...\n")

    result = detect_project(root)

    console.print(f"  Files: {result.file_count}")
    lang_display = result.primary_language or "unknown"
    if result.secondary_languages:
        lang_display += f" + {', '.join(result.secondary_languages)}"
    console.print(f"  Languages: [cyan]{lang_display}[/cyan]")
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
            "docs/ARCHITECTURE.md",
            "scaffold.yml",
            "docs/governance/RULES.md",
            "docs/governance/SESSION-PROTOCOL.md",
            "docs/governance/LIFECYCLE.md",
            "docs/governance/ROLES.md",
            "docs/governance/CONTEXT-BUDGET.md",
            "docs/governance/VERIFICATION.md",
            "docs/governance/DRIFT-METRICS.md",
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

    # Allow override (skip in CI/non-interactive mode via --yes)
    if not auto_yes and not click.confirm("Proceed with these settings?", default=True):
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

    # Ensure AEE phase is set
    from specsmith.phase import write_phase

    write_phase(root, "inception")

    # Guided architecture definition after import
    if guided:
        guided_files = _run_guided_architecture(config, root)
        for path in guided_files:
            rel = path.relative_to(root)
            console.print(f"  [green]\u2713[/green] {rel} (guided)")
        created.extend(guided_files)

    console.print(f"\n[bold green]Done.[/bold green] {len(created)} governance files generated.")
    console.print('Governance files generated. Review project configuration.')


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


@main.command()
@click.option("--project-dir", type=click.Path(exists=True), default=".", help="Project root.")
@click.option("--non-interactive", is_flag=True, default=False, help="Skip prompts, auto-generate.")
def architect(project_dir: str, non_interactive: bool) -> None:
    """Generate or enrich architecture documentation.

    Scans the project for modules, languages, dependencies, git history,
    then optionally interviews you about components and data flow.
    """
    from specsmith.architect import generate_architecture, scan_project_structure

    root = Path(project_dir).resolve()
    console.print(f"[bold]Scanning[/bold] {root}...\n")
    scan = scan_project_structure(root)

    modules: list[str] = list(scan.get("modules", []) or [])  # type: ignore[call-overload]
    deps_list: list[str] = list(scan.get("dependencies", []) or [])  # type: ignore[call-overload]
    eps_list: list[str] = list(scan.get("entry_points", []) or [])  # type: ignore[call-overload]
    existing: list[str] = list(scan.get("existing_arch_docs", []) or [])  # type: ignore[call-overload]  # noqa: E501

    console.print(f"  Languages: {scan.get('primary_language', '?')}")
    console.print(f"  Modules: {', '.join(modules) or 'none'}")
    console.print(f"  Dependencies: {len(deps_list)}")
    console.print(f"  Entry points: {', '.join(eps_list) or 'none'}")
    if existing:
        console.print(f"  Existing arch docs: {', '.join(existing)}")
    console.print()

    components: list[dict[str, str]] | None = None
    data_flow = ""
    deployment = ""

    if not non_interactive:
        console.print("[bold]Architecture Interview[/bold]\n")
        comp_str = click.prompt(
            "Major components (comma-separated)",
            default=", ".join(modules or ["core"]),
        )
        components = []
        for name in [c.strip() for c in comp_str.split(",") if c.strip()]:
            purpose = click.prompt(f"  {name} purpose", default="")
            interfaces = click.prompt(f"  {name} interfaces", default="")
            components.append({"name": name, "purpose": purpose, "interfaces": interfaces})

        data_flow = click.prompt("\nData flow description", default="")
        deployment = click.prompt("Deployment notes", default="")

    path = generate_architecture(
        root, components=components, data_flow=data_flow, deployment=deployment, scan=scan
    )
    rel = path.relative_to(root)
    console.print(f"\n[green]\u2713[/green] Generated {rel}")
    if existing:
        console.print(
            f"  [yellow]Note:[/yellow] Existing docs at {', '.join(existing)} "
            "are referenced but not merged. Review manually."
        )
    console.print('  [dim]Run "specsmith audit --project-dir ." to verify governance health.[/dim]')


@main.command(name="parse-reqs")
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
    help="Write parsed requirements to a JSON file instead of stdout.",
)
def parse_reqs_cmd(project_dir: str, output: str | None) -> None:
    """Parse ARCHITECTURE.md for discernable requirements."""
    root = Path(project_dir).resolve()
    console.print(f"[bold]Parsing requirements from[/bold] {root / 'docs' / 'ARCHITECTURE.md'}...\n")
    requirements = parse_architecture_requirements(root)

    if not requirements:
        console.print("[yellow]No requirements found in ARCHITECTURE.md.[/yellow]")
        return

    if output:
        output_path = Path(output)
        import json
        output_path.write_text(json.dumps(requirements, indent=2), encoding="utf-8")
        console.print(f"[bold green]Parsed requirements written to {output_path}[/bold green]")
    else:
        for req in requirements:
            console.print(f"  [cyan]{req['id']}[/cyan] ({req['component']}): {req['description']}")
        console.print(f"\n[bold green]Found {len(requirements)} requirements.[/bold green]")


@main.command(name="generate-tests")
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory.",
)
@click.option(
    "--reqs-file",
    type=click.Path(exists=True),
    default=None,
    help="Path to a JSON file containing requirements (from parse-reqs).",
)
@click.option(
    "--output",
    type=click.Path(),
    default=None,
    help="Write generated test cases to a JSON file instead of stdout.",
)
def generate_tests_cmd(project_dir: str, reqs_file: str | None, output: str | None) -> None:
    """Generate test cases based on parsed requirements."""
    root = Path(project_dir).resolve()
    requirements = []

    if reqs_file:
        import json
        reqs_path = Path(reqs_file)
        requirements = json.loads(reqs_path.read_text(encoding="utf-8"))
        console.print(f"[bold]Loading requirements from[/bold] {reqs_path}...")
    else:
        console.print(f"[bold]Parsing requirements from[/bold] {root / 'docs' / 'ARCHITECTURE.md'}...")
        requirements = parse_architecture_requirements(root)

    if not requirements:
        console.print("[yellow]No requirements to generate test cases from.[/yellow]")
        return

    test_cases = define_test_cases(requirements)

    if not test_cases:
        console.print("[yellow]No test cases generated.[/yellow]")
        return

    if output:
        output_path = Path(output)
        import json
        output_path.write_text(json.dumps(test_cases, indent=2), encoding="utf-8")
        console.print(f"[bold green]Generated test cases written to {output_path}[/bold green]")
    else:
        for tc in test_cases:
            console.print(f"  [green]{tc['id']}[/green] (REQ: {tc['requirement_id']}): {tc['description']}")
        console.print(f"\n[bold green]Generated {len(test_cases)} test cases.[/bold green]")


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

    current, latest, channel = check_latest_version()
    if not latest:
        console.print("[yellow]Could not reach PyPI.[/yellow]")
        return

    if current == latest:
        console.print(f"[green]\u2713[/green] specsmith {current} is up to date ({channel}).")
    else:
        console.print(f"  Current: {current} ({channel})")
        console.print(f"  Latest:  {latest}")

        if check_only:
            console.print("[yellow]Update available.[/yellow] Run: specsmith update")
            return

        if auto_yes or click.confirm(f"Update to {latest}?", default=True):
            success, msg = run_self_update(channel=channel)
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


@main.command(name="self-update")
@click.option(
    "--channel",
    type=click.Choice(["stable", "dev"]),
    default=None,
    help="Force channel (default: auto-detect from installed version).",
)
@click.option("--version", "target_version", default="", help="Install a specific version.")
def self_update_cmd(channel: str | None, target_version: str) -> None:
    """Update specsmith to the latest version.

    Auto-detects channel: stable builds upgrade to latest stable,
    dev builds upgrade to latest dev. Use --channel to override.
    Use --version to pin a specific version.
    """
    from specsmith.updater import check_latest_version, get_update_channel, run_self_update

    current_channel = get_update_channel()
    effective_channel = channel or current_channel

    if target_version:
        console.print(f"[bold]Installing specsmith {target_version}...[/bold]")
        success, msg = run_self_update(target_version=target_version)
    else:
        current, latest, effective_channel = check_latest_version(channel=effective_channel)
        if not latest:
            console.print("[yellow]Could not reach PyPI.[/yellow]")
            return
        if current == latest:
            console.print(
                f"[green]\u2713[/green] specsmith {current} is up to date ({effective_channel})."
            )
            return
        console.print(f"  Current: {current} ({current_channel})")
        console.print(f"  Latest:  {latest} ({effective_channel})")
        success, msg = run_self_update(channel=effective_channel)

    if success:
        console.print("[green]\u2713[/green] Updated successfully.")
        console.print("  Restart your shell to use the new version.")
    else:
        console.print(f"[red]\u2717[/red] Update failed: {msg}")


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
# Credits
# ---------------------------------------------------------------------------


@main.group()
def credits() -> None:
    """AI credit/token spend tracking and analysis."""


@credits.command(name="summary")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--month", default="", help="Filter by month (YYYY-MM).")
def credits_summary(project_dir: str, month: str) -> None:
    """Show credit spend summary."""
    from specsmith.credits import get_summary

    root = Path(project_dir).resolve()
    s = get_summary(root, month=month)
    console.print(f"  Tokens in:  {s.total_tokens_in:,}")
    console.print(f"  Tokens out: {s.total_tokens_out:,}")
    console.print(f"  Cost:       ${s.total_cost_usd:.4f}")
    console.print(f"  Sessions:   {s.session_count}")
    console.print(f"  Entries:    {s.entry_count}")
    if s.by_model:
        console.print("\n  By model:")
        for model, cost in sorted(s.by_model.items(), key=lambda x: -x[1]):
            console.print(f"    {model}: ${cost:.4f}")
    if s.alerts:
        console.print()
        for alert in s.alerts:
            console.print(f"  [yellow]\u26a0[/yellow] {alert}")


@credits.command(name="record")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--model", default="unknown", help="AI model used.")
@click.option("--provider", default="unknown", help="AI provider (openai, anthropic, etc.).")
@click.option("--tokens-in", type=int, default=0, help="Input tokens.")
@click.option("--tokens-out", type=int, default=0, help="Output tokens.")
@click.option("--task", default="", help="Task description.")
@click.option("--cost", type=float, default=None, help="Actual cost in USD (overrides estimate).")
def credits_record(
    project_dir: str,
    model: str,
    provider: str,
    tokens_in: int,
    tokens_out: int,
    task: str,
    cost: float | None,
) -> None:
    """Record a credit usage entry."""
    from specsmith.credits import record_usage

    root = Path(project_dir).resolve()
    entry = record_usage(
        root,
        model=model,
        provider=provider,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        task=task,
        cost_usd=cost,
    )
    console.print(
        f"[green]\u2713[/green] Recorded: {entry.model} "
        f"{entry.tokens_in:,}+{entry.tokens_out:,} tokens "
        f"(${entry.estimated_cost_usd:.4f})"
    )


@credits.command(name="report")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--output", default="", help="Write to file instead of stdout.")
def credits_report(project_dir: str, output: str) -> None:
    """Generate credit spend report."""
    from specsmith.credits import generate_report

    root = Path(project_dir).resolve()
    report = generate_report(root)
    if output:
        Path(output).write_text(report, encoding="utf-8")
        console.print(f"[green]\u2713[/green] Report written to {output}")
    else:
        console.print(report)


@credits.command(name="analyze")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def credits_analyze(project_dir: str) -> None:
    """Analyze spend patterns and get optimization recommendations."""
    from specsmith.credit_analyzer import generate_analysis_report

    root = Path(project_dir).resolve()
    report = generate_analysis_report(root)
    console.print(report)


@credits.command(name="budget")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--cap", type=float, default=None, help="Monthly cap in USD (0=unlimited).")
@click.option("--alert-pct", type=int, default=None, help="Alert at this % of cap.")
@click.option(
    "--watermarks", default=None, help="Comma-separated USD watermark alerts (e.g. 5,10,25,50)."
)
@click.option(
    "--enforcement",
    type=click.Choice(["soft", "hard"]),
    default=None,
    help="soft=warn only, hard=block agent sessions when cap exceeded.",
)
def credits_budget(
    project_dir: str,
    cap: float | None,
    alert_pct: int | None,
    watermarks: str | None,
    enforcement: str | None,
) -> None:
    """View or set credit budget and alert thresholds.

    Enforcement modes:
      soft (default) — warn when cap is exceeded but allow work to continue
      hard           — block new agent sessions when monthly cap is exceeded
    """
    from specsmith.credits import load_budget, save_budget

    root = Path(project_dir).resolve()
    budget = load_budget(root)

    if cap is not None:
        budget.monthly_cap_usd = cap
    if alert_pct is not None:
        budget.alert_threshold_pct = alert_pct
    if watermarks is not None:
        budget.alert_watermarks_usd = [float(w.strip()) for w in watermarks.split(",") if w.strip()]
    if enforcement is not None:
        budget.enforcement_mode = enforcement

    if any(x is not None for x in (cap, alert_pct, watermarks, enforcement)):
        save_budget(root, budget)
        console.print("[green]\u2713[/green] Budget updated.")

    cap_note = " (unlimited)" if budget.monthly_cap_usd == 0 else ""
    console.print(f"  Monthly cap:   ${budget.monthly_cap_usd:.2f}{cap_note}")
    console.print(f"  Alert at:      {budget.alert_threshold_pct}%")
    console.print(f"  Watermarks:    {', '.join(f'${w:.2f}' for w in budget.alert_watermarks_usd)}")
    console.print(f"  Enforcement:   {getattr(budget, 'enforcement_mode', 'soft')}")
    console.print(f"  Enabled:       {budget.enabled}")


@credits.group(name="limits")
def credits_limits() -> None:
    """Manage persisted per-model RPM/TPM profiles."""


@credits_limits.command(name="list")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def credits_limits_list(project_dir: str) -> None:
    """List configured local model rate-limit profiles."""
    from specsmith.rate_limits import load_rate_limit_profiles

    root = Path(project_dir).resolve()
    profiles = sorted(
        load_rate_limit_profiles(root),
        key=lambda profile: (profile.provider, profile.model),
    )
    if not profiles:
        console.print("[yellow]No model rate-limit profiles configured.[/yellow]")
        return

    for profile in profiles:
        console.print(
            "  "
            f"{profile.provider}/{profile.model} "
            f"RPM={profile.rpm_limit} TPM={profile.tpm_limit} "
            f"target={profile.utilization_target:.2f} "
            f"concurrency={profile.concurrency_cap}"
        )


@credits_limits.command(name="set")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--provider", required=True, help="Provider key, such as openai or anthropic.")
@click.option("--model", required=True, help="Model key, such as gpt-5.4.")
@click.option("--rpm", "rpm_limit", type=int, required=True, help="Requests per minute limit.")
@click.option("--tpm", "tpm_limit", type=int, required=True, help="Tokens per minute limit.")
@click.option("--target", "utilization_target", type=float, default=0.7, show_default=True)
@click.option("--concurrency", "concurrency_cap", type=int, default=1, show_default=True)
def credits_limits_set(
    project_dir: str,
    provider: str,
    model: str,
    rpm_limit: int,
    tpm_limit: int,
    utilization_target: float,
    concurrency_cap: int,
) -> None:
    """Create or replace a local model rate-limit profile."""
    from specsmith.rate_limits import (
        ModelRateLimitProfile,
        load_rate_limit_profiles,
        save_rate_limit_profiles,
    )

    root = Path(project_dir).resolve()
    updated_profile = ModelRateLimitProfile(
        provider=provider,
        model=model,
        rpm_limit=rpm_limit,
        tpm_limit=tpm_limit,
        utilization_target=utilization_target,
        concurrency_cap=concurrency_cap,
        source="override",
    )
    profiles = {profile.key: profile for profile in load_rate_limit_profiles(root)}
    profiles[updated_profile.key] = updated_profile
    save_rate_limit_profiles(root, list(profiles.values()))
    console.print(
        "[green]✓[/green] "
        f"Saved {updated_profile.provider}/{updated_profile.model} "
        f"(RPM={updated_profile.rpm_limit}, TPM={updated_profile.tpm_limit}, "
        f"target={updated_profile.utilization_target:.2f}, "
        f"concurrency={updated_profile.concurrency_cap})"
    )


@credits_limits.command(name="status")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--provider", required=True, help="Provider key, such as openai or anthropic.")
@click.option("--model", required=True, help="Model key, such as gpt-5.4.")
def credits_limits_status(project_dir: str, provider: str, model: str) -> None:
    """Show rolling-window snapshot for a model (RPM, TPM, concurrency, moving averages)."""
    from specsmith.rate_limits import (
        BUILTIN_PROFILES,
        load_rate_limit_profiles,
        load_rate_limit_scheduler,
    )

    root = Path(project_dir).resolve()
    profiles = load_rate_limit_profiles(root, defaults=BUILTIN_PROFILES)
    scheduler = load_rate_limit_scheduler(root, profiles)

    try:
        snap = scheduler.snapshot(provider, model)
    except KeyError:
        console.print(
            f"[red]No profile found for {provider}/{model}.[/red] "
            "Use 'specsmith credits limits set' to configure one."
        )
        raise SystemExit(1) from None

    console.print(f"[bold]{snap.provider}/{snap.model}[/bold]")
    console.print(
        f"  RPM: {snap.rolling_request_count} / {snap.effective_rpm_limit} "
        f"(limit {snap.rpm_limit}, target {snap.effective_rpm_limit})"
    )
    console.print(
        f"  TPM: {snap.rolling_token_count:,} / {snap.effective_tpm_limit:,} "
        f"(limit {snap.tpm_limit:,})"
    )
    console.print(
        f"  Utilization: RPM {snap.request_utilization:.1%}  TPM {snap.token_utilization:.1%}"
    )
    console.print(
        f"  Concurrency: {snap.in_flight} in-flight / {snap.current_concurrency_cap} cap "
        f"(base {snap.base_concurrency_cap})"
    )
    console.print(
        f"  Moving avg:  {snap.moving_average_requests:.1f} req/window  "
        f"{snap.moving_average_tokens:,.0f} tok/window"
    )


@credits_limits.command(name="defaults")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option(
    "--install",
    is_flag=True,
    default=False,
    help="Merge built-in defaults into the local project config (existing overrides preserved).",
)
def credits_limits_defaults(project_dir: str, install: bool) -> None:
    """List (or install) built-in RPM/TPM profiles for common provider/model paths."""
    from specsmith.rate_limits import (
        BUILTIN_PROFILES,
        load_rate_limit_profiles,
        save_rate_limit_profiles,
    )

    console.print("[bold]Built-in model rate-limit profiles[/bold]")
    console.print("[dim](conservative defaults — local overrides take precedence)[/dim]\n")
    for profile in BUILTIN_PROFILES:
        console.print(
            f"  {profile.provider}/{profile.model:25s} "
            f"RPM={profile.rpm_limit:<6} TPM={profile.tpm_limit:>12,} "
            f"target={profile.utilization_target:.2f}"
        )

    if install:
        root = Path(project_dir).resolve()
        # Load existing local profiles; they take precedence over built-ins
        existing = {p.key: p for p in load_rate_limit_profiles(root)}
        merged = {p.key: p for p in BUILTIN_PROFILES}
        merged.update(existing)  # local overrides win
        save_rate_limit_profiles(root, list(merged.values()))
        added = len(merged) - len(existing)
        console.print(
            f"\n[green]\u2713[/green] Installed {added} new default(s) to "
            ".specsmith/model-rate-limits.json (existing profiles preserved)."
        )


main.add_command(credits)


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
# Process execution and abort
# ---------------------------------------------------------------------------


@main.command(name="exec")
@click.argument("command")
@click.option("--timeout", default=120, help="Timeout in seconds (default: 120).")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def exec_cmd(command: str, timeout: int, project_dir: str) -> None:
    """Execute a command with PID tracking and timeout enforcement.

    Tracks the process in .specsmith/pids/ so it can be listed (specsmith ps)
    or aborted (specsmith abort). Logs stdout/stderr to .specsmith/logs/.
    Works cross-platform: Windows, Linux, macOS.
    """
    from specsmith.executor import run_tracked

    root = Path(project_dir).resolve()
    console.print(f"[bold]exec[/bold] {command} (timeout={timeout}s)")

    result = run_tracked(root, command, timeout=timeout)

    if result.timed_out:
        console.print(f"[red]TIMEOUT[/red] after {timeout}s (PID {result.pid})")
    elif result.exit_code == 0:
        console.print(f"[green]OK[/green] ({result.duration:.1f}s) — exit code 0")
    else:
        console.print(f"[red]FAILED[/red] ({result.duration:.1f}s) — exit code {result.exit_code}")
    if result.stdout_file:
        console.print(f"  stdout: {result.stdout_file}")
    if result.stderr_file:
        console.print(f"  stderr: {result.stderr_file}")
    raise SystemExit(result.exit_code)


@main.command(name="ps")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def ps_cmd(project_dir: str) -> None:
    """List tracked running processes."""
    from specsmith.executor import list_processes

    root = Path(project_dir).resolve()
    procs = list_processes(root)
    if not procs:
        console.print("No tracked processes running.")
        return
    for p in procs:
        elapsed = p.elapsed
        remaining = max(0, p.timeout - elapsed)
        status = "[red]EXPIRED[/red]" if p.is_expired else f"{remaining:.0f}s left"
        console.print(f"  PID {p.pid}  {status}  {p.command}")
    console.print(f"\n  {len(procs)} process(es)")


@main.command(name="abort")
@click.option("--pid", type=int, default=None, help="Abort a specific PID.")
@click.option("--all", "abort_all_flag", is_flag=True, default=False, help="Abort all tracked.")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def abort_cmd(pid: int | None, abort_all_flag: bool, project_dir: str) -> None:
    """Abort tracked process(es). Sends SIGTERM then SIGKILL (POSIX) or taskkill (Windows)."""
    from specsmith.executor import abort_all, abort_process, list_processes

    root = Path(project_dir).resolve()

    if abort_all_flag:
        killed = abort_all(root)
        if killed:
            console.print(f"[green]Aborted {len(killed)} process(es): {killed}[/green]")
        else:
            console.print("No tracked processes to abort.")
    elif pid:
        if abort_process(root, pid):
            console.print(f"[green]Aborted PID {pid}[/green]")
        else:
            console.print(f"[red]Could not abort PID {pid}[/red]")
    else:
        procs = list_processes(root)
        if not procs:
            console.print("No tracked processes. Use --pid or --all.")
            return
        console.print("Tracked processes:")
        for p in procs:
            console.print(f"  PID {p.pid}  {p.command}")
        console.print("\nUse --pid <N> or --all to abort.")


# ---------------------------------------------------------------------------
# Agentic client commands
# ---------------------------------------------------------------------------


@main.command(name="run")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option(
    "--task",
    "task",
    default="",
    help="Run a single task non-interactively and exit.",
)
@click.option(
    "--provider",
    "provider_name",
    default=None,
    help="LLM provider: anthropic, openai, gemini, ollama (default: auto-detect)",
)
@click.option("--model", default=None, help="Model name override.")
@click.option(
    "--tier",
    type=click.Choice(["fast", "balanced", "powerful"]),
    default="balanced",
    help="Model capability tier (default: balanced).",
)
@click.option(
    "--no-stream", "no_stream", is_flag=True, default=False, help="Disable streaming output."
)
@click.option(
    "--optimize",
    "optimize",
    is_flag=True,
    default=False,
    help="Enable token optimization (caching, routing, context trim, tool filtering).",
)
@click.option(
    "--json-events",
    "json_events",
    is_flag=True,
    default=False,
    help="Emit structured JSONL events to stdout (used by IDE clients like the VS Code extension).",
)
def run_cmd(
    project_dir: str,
    task: str,
    provider_name: str | None,
    model: str | None,
    tier: str,
    no_stream: bool,
    optimize: bool,
    json_events: bool,
) -> None:
    """Start the AEE-integrated agentic client REPL.

    Auto-detects LLM provider from environment:
      ANTHROPIC_API_KEY → Claude
      OPENAI_API_KEY    → GPT/O-series
      GOOGLE_API_KEY    → Gemini
      Ollama running    → local LLMs (zero config)
      SPECSMITH_PROVIDER=<name> → explicit override

    Install a provider:
      pipx inject specsmith anthropic             # Claude
      pipx inject specsmith openai               # GPT/O-series
    """
    from specsmith.agent.core import ModelTier
    from specsmith.agent.runner import AgentRunner

    tier_map = {
        "fast": ModelTier.FAST,
        "balanced": ModelTier.BALANCED,
        "powerful": ModelTier.POWERFUL,
    }

    try:
        runner = AgentRunner(
            project_dir=project_dir,
            provider_name=provider_name,
            model=model,
            tier=tier_map[tier],
            stream=not no_stream,
            optimize=optimize,
            json_events=json_events,
        )
        if task:
            result = runner.run_task(task)
            console.print(result)
        else:
            runner.run_interactive()
        if optimize and runner._optimizer:
            report = runner._optimizer.report()
            console.print(f"\n[dim]{report.summary()}[/dim]")
    except Exception as e:  # noqa: BLE001
        console.print(f"[red]{e}[/red]")
        console.print(
            "\nInstall a provider (pipx recommended):\n"
            "  pipx inject specsmith anthropic             # Claude\n"
            "  pipx inject specsmith openai               # GPT\n"
            "  pipx inject specsmith google-generativeai  # Gemini\n"
            "  # Ollama: install locally from https://ollama.ai"
        )
        raise SystemExit(1) from None


@main.command(name="serve")
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory.",
)
@click.option("--provider", default="ollama", help="LLM provider.")
@click.option("--model", default="", help="Model name (blank = provider default).")
@click.option("--port", type=int, default=8421, help="HTTP port to listen on.")
@click.option("--host", default="127.0.0.1", help="Bind address (use 0.0.0.0 for network access).")
def serve_cmd(
    project_dir: str,
    provider: str,
    model: str,
    port: int,
    host: str,
) -> None:
    """Start a persistent HTTP server for agent sessions.

    Faster than `specsmith run` — keeps the Python process and Ollama
    model warm between turns.  Connect via SSE (GET /api/events) and
    POST /api/send.

    Example:
      specsmith serve --port 8421 --provider ollama --model qwen2.5:14b
    """
    from specsmith.serve import run_server

    run_server(
        project_dir=project_dir,
        provider=provider,
        model=model,
        port=port,
        host=host,
    )


@main.group(name="agent")
def agent_group() -> None:
    """Manage the specsmith agentic client configuration."""


@agent_group.command(name="providers")
def agent_providers_cmd() -> None:
    """Show available LLM providers and their status."""
    from specsmith.agent.providers import list_providers

    console.print("[bold]LLM Providers[/bold]\n")
    for p in list_providers():
        configured = "configured" in p["status"] or "available" in p["status"]
        icon = "[green]\u2713[/green]" if configured else "[yellow]\u2014[/yellow]"
        console.print(f"  {icon} {p['name']:12s} {p['status']}")

    console.print("\nInstall providers (pipx recommended):")
    console.print("  pipx inject specsmith anthropic             # Claude")
    console.print("  pipx inject specsmith openai               # GPT/O-series")
    console.print("  pipx inject specsmith google-generativeai  # Gemini")
    console.print("  # Ollama: install from https://ollama.ai (no extra needed)")


@agent_group.command(name="tools")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def agent_tools_cmd(project_dir: str) -> None:
    """List all available agent tools."""
    from specsmith.agent.tools import build_tool_registry

    tools = build_tool_registry(project_dir)
    console.print(f"[bold]Agent Tools[/bold] ({len(tools)})\n")
    for t in tools:
        claims = f" [{', '.join(t.epistemic_claims[:1])}]" if t.epistemic_claims else ""
        console.print(f"  {t.name:25s} {t.description[:60]}{claims}")


@agent_group.command(name="skills")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def agent_skills_cmd(project_dir: str) -> None:
    """List loaded skills from the project and built-in profiles."""
    from specsmith.agent.skills import load_skills

    skills = load_skills(__import__("pathlib").Path(project_dir).resolve())
    if not skills:
        console.print("[yellow]No skills found.[/yellow]")
        return
    console.print(f"[bold]Loaded Skills[/bold] ({len(skills)})\n")
    for s in skills:
        console.print(f"  [{s.domain:12s}] {s.name}: {s.description[:60]}")


main.add_command(agent_group)


# ---------------------------------------------------------------------------
# Applied Epistemic Engineering commands
# ---------------------------------------------------------------------------


@main.command(name="stress-test")
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory.",
)
@click.option(
    "--accepted-only",
    is_flag=True,
    default=False,
    help="Only stress-test accepted requirements (skip drafts).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "mermaid"]),
    default="text",
    help="Output format.",
)
def stress_test_cmd(project_dir: str, accepted_only: bool, output_format: str) -> None:
    """Run AEE stress-tests against requirements (Frame → Disassemble → Stress-Test).

    Parses docs/REQUIREMENTS.md as BeliefArtifacts, applies 8 adversarial
    challenge functions, detects Logic Knots, and emits recovery proposals.
    """
    from specsmith.epistemic.belief import parse_requirements_as_beliefs
    from specsmith.epistemic.failure_graph import FailureModeGraph
    from specsmith.epistemic.recovery import RecoveryOperator
    from specsmith.epistemic.stress_tester import StressTester

    root = Path(project_dir).resolve()
    req_path = root / "docs" / "REQUIREMENTS.md"
    test_path = root / "docs" / "TEST_SPEC.md"

    if not req_path.exists():
        console.print("[red]docs/REQUIREMENTS.md not found.[/red]")
        raise SystemExit(1)

    artifacts = parse_requirements_as_beliefs(req_path)
    if accepted_only:
        artifacts = [a for a in artifacts if a.is_accepted]

    console.print(f"[bold]Stress-testing[/bold] {len(artifacts)} belief artifacts\n")

    tester = StressTester(req_path=req_path, test_path=test_path)
    result = tester.run(artifacts)

    console.print(f"  Artifacts tested:   {result.artifacts_tested}")
    console.print(f"  Failure modes:      {result.total_failures}")
    console.print(f"  Critical failures:  {result.critical_count}")
    console.print(f"  Logic knots:        {len(result.logic_knots)}")
    eq_icon = "[green]✓[/green]" if result.equilibrium else "[red]✗[/red]"
    console.print(f"  Equilibrium:        {eq_icon}")
    console.print()

    graph = FailureModeGraph()
    graph.build(artifacts, result)

    if output_format == "mermaid":
        console.print(graph.render_mermaid())
    else:
        all_fms = [fm for a in artifacts for fm in a.failure_modes]
        console.print(graph.render_text(all_failure_modes=all_fms))
        console.print()

        operator = RecoveryOperator()
        proposals = operator.propose(artifacts, result)
        console.print(operator.format_proposals(proposals))

    if not result.equilibrium:
        raise SystemExit(1)


@main.command(name="belief-graph")
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "mermaid"]),
    default="text",
    help="Output format (text tree or Mermaid diagram).",
)
@click.option(
    "--component",
    default="",
    help="Filter by component code (e.g. CLI, AEE, TRC).",
)
def belief_graph_cmd(project_dir: str, output_format: str, component: str) -> None:
    """Render the belief artifact dependency graph.

    Shows all requirements as BeliefArtifacts with their inferential links,
    confidence levels, and failure mode counts.
    """
    from specsmith.epistemic.belief import parse_requirements_as_beliefs
    from specsmith.epistemic.certainty import CertaintyEngine
    from specsmith.epistemic.stress_tester import _extract_covered_reqs

    root = Path(project_dir).resolve()
    req_path = root / "docs" / "REQUIREMENTS.md"
    test_path = root / "docs" / "TEST_SPEC.md"

    if not req_path.exists():
        console.print("[red]docs/REQUIREMENTS.md not found.[/red]")
        raise SystemExit(1)

    artifacts = parse_requirements_as_beliefs(req_path)
    if component:
        artifacts = [a for a in artifacts if a.component.upper() == component.upper()]

    covered = _extract_covered_reqs(test_path) if test_path.exists() else set()
    engine = CertaintyEngine(threshold=0.7)
    report = engine.run(artifacts, covered_reqs=covered)
    score_map = {s.artifact_id: s for s in report.scores}

    if output_format == "mermaid":
        from specsmith.epistemic.failure_graph import FailureModeGraph
        from specsmith.epistemic.stress_tester import StressTestResult

        graph = FailureModeGraph()
        graph.build(artifacts, StressTestResult())
        console.print(graph.render_mermaid())
    else:
        console.print(f"[bold]Belief Graph[/bold] — {len(artifacts)} artifacts\n")
        by_comp: dict[str, list[Any]] = {}
        for a in artifacts:
            by_comp.setdefault(a.component or "OTHER", []).append(a)

        for comp, group in sorted(by_comp.items()):
            console.print(f"  [bold cyan]{comp}[/bold cyan]")
            for a in group:
                sc = score_map.get(a.artifact_id)
                score_str = f"{sc.propagated_score:.2f}" if sc else "?"
                icon = "[green]✓[/green]" if (sc and sc.above_threshold) else "[red]✗[/red]"
                console.print(
                    f"    {icon} {a.artifact_id:25s} [{a.status.value:15s}] "
                    f"C={score_str}  {a.source_text[:50]}"
                )
        console.print()
        console.print(f"  Overall certainty: {report.overall_score:.2f}")
        console.print(f"  Below threshold ({report.threshold:.2f}): {len(report.below_threshold)}")


@main.command(name="epistemic-audit")
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory.",
)
@click.option(
    "--threshold",
    type=float,
    default=0.7,
    help="Certainty threshold (default: 0.7).",
)
@click.option(
    "--mermaid",
    "emit_mermaid",
    is_flag=True,
    default=False,
    help="Emit Mermaid failure-mode graph alongside text output.",
)
def epistemic_audit_cmd(project_dir: str, threshold: float, emit_mermaid: bool) -> None:
    """Full AEE epistemic audit: certainty scores, logic knots, failure modes.

    Runs the full AEE pipeline:\n
    1. Parse REQUIREMENTS.md as BeliefArtifacts\n
    2. Stress-test all accepted artifacts (apply S operator)\n
    3. Build Failure-Mode Graph (G)\n
    4. Check equilibrium S(G)\n
    5. Compute certainty scores and propagate through dependency links\n
    6. Emit recovery proposals (R operator) ranked by priority
    """
    from specsmith.epistemic.belief import parse_requirements_as_beliefs
    from specsmith.epistemic.certainty import CertaintyEngine
    from specsmith.epistemic.failure_graph import FailureModeGraph
    from specsmith.epistemic.recovery import RecoveryOperator
    from specsmith.epistemic.stress_tester import StressTester, _extract_covered_reqs

    root = Path(project_dir).resolve()
    req_path = root / "docs" / "REQUIREMENTS.md"
    test_path = root / "docs" / "TEST_SPEC.md"

    if not req_path.exists():
        console.print("[red]docs/REQUIREMENTS.md not found.[/red]")
        raise SystemExit(1)

    artifacts = parse_requirements_as_beliefs(req_path)
    covered = _extract_covered_reqs(test_path) if test_path.exists() else set()

    console.print(f"[bold]Epistemic Audit[/bold] — {len(artifacts)} belief artifacts\n")

    # Stress-test phase
    tester = StressTester(req_path=req_path, test_path=test_path)
    result = tester.run(artifacts)

    # Failure-mode graph
    graph = FailureModeGraph()
    graph.build(artifacts, result)

    # Certainty scoring
    engine = CertaintyEngine(threshold=threshold)
    certainty = engine.run(artifacts, covered_reqs=covered)

    # Recovery proposals
    operator = RecoveryOperator()
    proposals = operator.propose(artifacts, result)

    # Output
    eq_icon = "[green]✓[/green]" if result.equilibrium else "[red]✗[/red]"
    console.print(f"  Equilibrium:        {eq_icon} {'YES' if result.equilibrium else 'NO'}")
    console.print(f"  Failure modes:      {result.total_failures}")
    console.print(f"  Critical failures:  {result.critical_count}")
    console.print(f"  Logic knots:        {len(result.logic_knots)}")
    console.print(  # noqa: E501
        f"  Overall certainty:  {certainty.overall_score:.2f} (threshold {threshold:.2f})"
    )
    console.print(f"  Below threshold:    {len(certainty.below_threshold)}")
    console.print()

    if result.logic_knots:
        console.print("[bold red]⚠ Logic Knots (stop condition per H13):[/bold red]")
        for id1, id2, reason in result.logic_knots:
            console.print(f"  ✗ {id1} ⇔ {id2}")
            console.print(f"    {reason}")
        console.print()

    console.print(certainty.format_text())
    console.print()

    if emit_mermaid:
        console.print("[bold]Mermaid Failure-Mode Graph:[/bold]")
        console.print(graph.render_mermaid())
        console.print()

    if proposals:
        console.print(operator.format_proposals(proposals[:10]))  # Top 10

    if not result.equilibrium or certainty.overall_score < threshold:
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# Trace vault commands
# ---------------------------------------------------------------------------


@main.group(name="trace")
def trace_group() -> None:
    """Manage the cryptographic trace vault (STP-inspired decision sealing)."""


@trace_group.command(name="seal")
@click.argument(
    "seal_type",
    type=click.Choice(
        ["decision", "milestone", "audit-gate", "logic-knot", "stress-test", "epistemic"]
    ),
)
@click.argument("description")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--author", default="agent", help="Author of this seal.")
@click.option("--artifacts", default="", help="Comma-separated artifact IDs.")
def trace_seal_cmd(
    seal_type: str,
    description: str,
    project_dir: str,
    author: str,
    artifacts: str,
) -> None:
    """Create a cryptographic seal for a decision, milestone, or audit gate."""
    from specsmith.trace import TraceVault

    root = Path(project_dir).resolve()
    vault = TraceVault(root)
    artifact_ids = [a.strip() for a in artifacts.split(",") if a.strip()]
    record = vault.seal(
        seal_type=seal_type,
        description=description,
        author=author,
        artifact_ids=artifact_ids or None,
    )
    console.print(f"[green]✓[/green] Sealed as [bold]{record.seal_id}[/bold]")
    console.print(f"  Type:  {record.seal_type}")
    console.print(f"  Hash:  {record.entry_hash[:32]}...")
    console.print(f"  Total seals: {vault.count()}")


@trace_group.command(name="verify")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def trace_verify_cmd(project_dir: str) -> None:
    """Verify cryptographic integrity of the trace chain."""
    from specsmith.trace import TraceVault

    vault = TraceVault(Path(project_dir).resolve())
    if vault.count() == 0:
        console.print("[yellow]Trace vault is empty.[/yellow]")
        return

    valid, errors = vault.verify()
    if valid:
        console.print(f"[bold green]✓ Chain intact[/bold green] — {vault.count()} seals verified.")
    else:
        console.print("[bold red]✗ Chain integrity violation![/bold red]")
        for err in errors:
            console.print(f"  [red]✗[/red] {err}")
        raise SystemExit(1)


@trace_group.command(name="log")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--limit", default=20, help="Number of recent seals to show.")
@click.option("--type", "filter_type", default="", help="Filter by seal type.")
def trace_log_cmd(project_dir: str, limit: int, filter_type: str) -> None:
    """Show the trace vault log."""
    from specsmith.trace import TraceVault

    vault = TraceVault(Path(project_dir).resolve())
    console.print(vault.format_log(limit=limit))


main.add_command(trace_group)


# ---------------------------------------------------------------------------
# Integrate command (epistemic tool analysis)
# ---------------------------------------------------------------------------


@main.command(name="integrate")
@click.argument("tool_name")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Emit impact report without generating adapter files.",
)
def integrate_cmd(tool_name: str, project_dir: str, dry_run: bool) -> None:
    """Analyze epistemic impact of integrating a tool, then scaffold its adapter.

    Before generating an adapter file, emits an epistemic impact report:
    what belief artifacts this tool provides evidence for, what its
    uncertainty bounds are, and what failure modes it might introduce.
    """
    root = Path(project_dir).resolve()
    req_path = root / "docs" / "REQUIREMENTS.md"

    console.print(f"[bold]Epistemic Impact Analysis[/bold]: {tool_name}\n")

    if req_path.exists():
        from specsmith.epistemic.belief import parse_requirements_as_beliefs

        artifacts = parse_requirements_as_beliefs(req_path)
        # Find relevant artifacts by matching tool name to component/description
        relevant = [
            a
            for a in artifacts
            if tool_name.lower() in a.source_text.lower()
            or tool_name.lower() in a.component.lower()
        ]
        if relevant:
            console.print(f"  Relevant belief artifacts ({len(relevant)}):")
            for a in relevant[:10]:
                console.print(f"    {a.artifact_id}: {a.source_text[:70]}")
        else:
            console.print("  No directly linked belief artifacts found.")
            console.print(
                "  [dim]Tip: Add requirements that reference this tool to docs/REQUIREMENTS.md.[/dim]"  # noqa: E501
            )

    console.print()
    console.print("  [bold]Epistemic Contract[/bold] for this integration:")
    console.print(f"    Tool:             {tool_name}")
    console.print("    Claims:           [to be defined in adapter template]")
    console.print("    Uncertainty:      [to be defined — what can this tool NOT detect?]")
    console.print("    Evidence type:    [static analysis | runtime | human review | mixed]")
    console.print("    Failure modes:    [what happens when this tool fails silently?]")
    console.print()

    if dry_run:
        console.print("[dim](dry-run — no files written)[/dim]")
        return

    # Check if adapter already exists
    try:
        from specsmith.integrations import get_adapter

        adapter = get_adapter(tool_name)
        scaffold_path = root / "scaffold.yml"
        if scaffold_path.exists():
            import yaml

            with open(scaffold_path) as f:
                raw = yaml.safe_load(f)
            config = ProjectConfig(**raw)
            created = adapter.generate(config, root)
            for path in created:
                console.print(f"  [green]✓[/green] {path.relative_to(root)}")
            console.print(f"\n[bold green]{len(created)} adapter file(s) generated.[/bold green]")
        else:
            console.print("[yellow]No scaffold.yml found. Run specsmith import first.[/yellow]")
    except ValueError:
        console.print(
            f"[yellow]No built-in adapter for '{tool_name}'.[/yellow] "
            "You can create a custom adapter by implementing BaseAdapter."
        )


# ---------------------------------------------------------------------------
# Auth — secure API key management (#37)
# ---------------------------------------------------------------------------


@main.group()
def auth() -> None:
    """Manage API keys and tokens for platform integrations."""


@auth.command(name="set")
@click.argument("platform")
@click.option("--token", default="", help="Token value (if not provided, prompted securely).")
def auth_set(platform: str, token: str) -> None:
    """Store an API token for a platform (readthedocs, pypi, github, gitlab, uspto).

    Token is stored in OS keyring (preferred) or encrypted file fallback.
    NEVER passed as a log message or written to governance files.
    """
    from specsmith.auth import PLATFORMS, set_token

    if not token:
        import getpass

        info = PLATFORMS.get(platform.lower(), {})
        desc = info.get("description", platform)
        url = info.get("url", "")
        if url:
            console.print(f"Get token from: [link]{url}[/link]")
        token = getpass.getpass(f"Enter {desc}: ")

    if not token.strip():
        console.print("[yellow]No token provided. Cancelled.[/yellow]")
        return

    method = set_token(platform, token.strip())
    console.print(f"[green]\u2713[/green] Token for [bold]{platform}[/bold] stored in {method}.")


@auth.command(name="list")
def auth_list() -> None:
    """Show all configured platform credentials (masked)."""
    from specsmith.auth import list_configured

    entries = list_configured()
    console.print("[bold]Platform Credentials[/bold]\n")
    for e in entries:
        if e["status"] == "configured":
            console.print(
                f"  [green]\u2713[/green] {e['platform']:14s} {e['masked']:20s} "
                f"[dim]{e['source']}[/dim]"
            )
        else:
            console.print(f"  [dim]\u2014[/dim] {e['platform']:14s} [dim]not set[/dim]")


@auth.command(name="remove")
@click.argument("platform")
def auth_remove(platform: str) -> None:
    """Remove a stored token for a platform."""
    from specsmith.auth import remove_token

    if remove_token(platform):
        console.print(f"[green]\u2713[/green] Token for [bold]{platform}[/bold] removed.")
    else:
        console.print(f"[yellow]No token found for [bold]{platform}[/bold].[/yellow]")


@auth.command(name="check")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def auth_check(project_dir: str) -> None:
    """Check which platform tokens are available for this project."""
    import yaml

    from specsmith.auth import PLATFORMS, get_token

    root = Path(project_dir).resolve()
    scaffold_path = root / "scaffold.yml"

    # Determine which platforms are needed
    needed: list[str] = []
    if scaffold_path.exists():
        with open(scaffold_path) as f:
            raw = yaml.safe_load(f) or {}
        vcs = raw.get("vcs_platform", "")
        if vcs:
            needed.append(vcs)
        needed.append("readthedocs")
        needed.append("pypi")
    else:
        needed = list(PLATFORMS.keys())

    console.print("[bold]Token Check[/bold]\n")
    all_ok = True
    for platform in needed:
        token = get_token(platform)
        if token:
            console.print(f"  [green]\u2713[/green] {platform:14s} configured")
        else:
            console.print(f"  [red]\u2717[/red] {platform:14s} [red]not set[/red]")
            info = PLATFORMS.get(platform, {})
            if info.get("url"):
                console.print(f"              Get it: {info['url']}")
            all_ok = False

    console.print()
    if all_ok:
        console.print("[bold green]All required tokens configured.[/bold green]")
    else:
        console.print(  # noqa: E501
            "[yellow]Some tokens missing. Run [bold]specsmith auth set <platform>[/bold].[/yellow]"
        )


main.add_command(auth)


# ---------------------------------------------------------------------------
# Workspace — multi-project management (#17)
# ---------------------------------------------------------------------------


@main.group()
def workspace() -> None:
    """Manage multi-project workspaces."""


@workspace.command(name="init")
@click.option("--name", default="", help="Workspace name.")
@click.option("--dir", "workspace_dir", type=click.Path(), default=".", help="Workspace root.")
@click.argument("projects", nargs=-1)
def workspace_init(name: str, workspace_dir: str, projects: tuple[str, ...]) -> None:
    """Create workspace.yml governing multiple projects.

    PROJECTS: relative paths to project directories.

    Example: specsmith workspace init my-org ./backend ./frontend ./shared-lib
    """
    from specsmith.workspace import init_workspace

    root = Path(workspace_dir).resolve()
    ws_name = name or root.name
    project_list = list(projects) if projects else []

    if not project_list:
        console.print("[yellow]No projects specified. Creating empty workspace.[/yellow]")

    ws_path = init_workspace(root, ws_name, project_list)
    console.print(f"[green]\u2713[/green] Created [bold]{ws_path.relative_to(root)}[/bold]")
    console.print(f"  Projects: {len(project_list)}")
    console.print("  Edit workspace.yml to add/configure projects.")


@workspace.command(name="audit")
@click.option("--dir", "workspace_dir", type=click.Path(exists=True), default=".")
def workspace_audit(workspace_dir: str) -> None:
    """Run specsmith audit across all workspace projects."""
    from specsmith.workspace import audit_workspace

    root = Path(workspace_dir).resolve()
    results = audit_workspace(root)

    healthy = sum(1 for r in results if r.healthy)
    console.print(f"[bold]Workspace Audit[/bold] — {healthy}/{len(results)} healthy\n")

    for r in results:
        icon = "[green]\u2713[/green]" if r.healthy else "[red]\u2717[/red]"
        console.print(f"  {icon} [bold]{r.name}[/bold] ({r.path})")
        if r.error:
            console.print(f"      [red]Error: {r.error}[/red]")
        else:
            console.print(f"      {r.passed} passed, {r.failed} failed")
            for issue in r.issues[:3]:
                console.print(f"      [yellow]⚠[/yellow] {issue}")

    if healthy == len(results):
        console.print(f"\n[bold green]All {len(results)} projects healthy.[/bold green]")
    else:
        console.print(f"\n[bold red]{len(results) - healthy} project(s) need attention.[/bold red]")
        raise SystemExit(1)


@workspace.command(name="export")
@click.option("--dir", "workspace_dir", type=click.Path(exists=True), default=".")
@click.option("--output", default="", help="Write to file instead of stdout.")
def workspace_export(workspace_dir: str, output: str) -> None:
    """Generate combined compliance report for all workspace projects."""
    from specsmith.workspace import export_workspace

    root = Path(workspace_dir).resolve()
    report = export_workspace(root)

    if output:
        Path(output).write_text(report, encoding="utf-8")
        console.print(f"[green]\u2713[/green] Report written to {output}")
    else:
        console.print(report)


main.add_command(workspace)


# ---------------------------------------------------------------------------
# Watch — live governance daemon (#16)
# ---------------------------------------------------------------------------


@main.command(name="watch")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--interval", default=5, help="Polling interval in seconds (default: 5).")
@click.option(
    "--no-notify",
    is_flag=True,
    default=False,
    help="Suppress desktop notifications (always just prints to terminal).",
)
def watch_cmd(project_dir: str, interval: int, no_notify: bool) -> None:
    """Watch for governance drift and alert in real time.

    Polls the project directory and alerts when:
    - LEDGER.md hasn't been updated after code changes
    - REQ\u2194TEST coverage drops
    - CI config diverges from tool registry

    Press Ctrl+C to stop.
    """
    import time

    root = Path(project_dir).resolve()
    console.print(f"[bold]specsmith watch[/bold] — monitoring {root}")
    console.print(f"  Interval: {interval}s | Press Ctrl+C to stop\n")

    # Check if watchdog is available (optional dep)
    try:
        import importlib.util as _iutil  # noqa: F401

        _has_watchdog = _iutil.find_spec("watchdog") is not None
    except Exception:  # noqa: BLE001
        _has_watchdog = False
    if not _has_watchdog:
        console.print(
            "[dim]watchdog not installed — using polling mode. "
            "For faster detection: pip install watchdog[/dim]\n"
        )

    from specsmith.auditor import run_audit

    last_alert: dict[str, str] = {}
    ledger_mtime: float = 0.0
    code_mtime: float = 0.0

    ledger_path = root / "LEDGER.md"
    if ledger_path.exists():
        ledger_mtime = ledger_path.stat().st_mtime

    def _check() -> None:
        nonlocal ledger_mtime, code_mtime

        # Check for code changes without ledger update
        src_dirs = [root / d for d in ["src", "lib", "backend", "frontend", "app"]]
        for src_dir in src_dirs:
            if src_dir.exists():
                for f in src_dir.rglob("*.py"):
                    mt = f.stat().st_mtime
                    if mt > code_mtime:
                        code_mtime = mt

        current_ledger_mtime = ledger_path.stat().st_mtime if ledger_path.exists() else 0.0
        if code_mtime > current_ledger_mtime and code_mtime > 0:
            msg = "\u26a0 Code changed but LEDGER.md not updated."
            if last_alert.get("ledger") != msg:
                console.print(f"  [yellow]{msg}[/yellow] Run [bold]specsmith ledger add[/bold].")
                last_alert["ledger"] = msg
        elif current_ledger_mtime > ledger_mtime:
            ledger_mtime = current_ledger_mtime
            console.print("  [green]\u2713[/green] LEDGER.md updated.")
            last_alert.pop("ledger", None)

        # Quick governance audit
        try:
            report = run_audit(root)
            if not report.healthy:
                msg = f"\u26a0 {report.failed} governance issue(s) detected."
                if last_alert.get("audit") != msg:
                    console.print(f"  [red]{msg}[/red] Run [bold]specsmith audit --fix[/bold].")
                    last_alert["audit"] = msg
            elif last_alert.get("audit"):
                console.print("  [green]\u2713[/green] Governance healthy.")
                last_alert.pop("audit", None)
        except Exception:  # noqa: BLE001
            pass

    try:
        while True:
            _check()
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[dim]watch stopped.[/dim]")


# ---------------------------------------------------------------------------
# Patent — USPTO prior art analysis (#10)
# ---------------------------------------------------------------------------


@main.group(name="patent")
def patent_group() -> None:
    """USPTO patent search and prior art analysis."""


@patent_group.command(name="search")
@click.argument("query")
@click.option("--max-results", default=10, help="Maximum results (default: 10).")
@click.option("--output", default="", help="Save results to file.")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def patent_search_cmd(query: str, max_results: int, output: str, project_dir: str) -> None:
    """Search USPTO patent database.

    Requires USPTO_API_KEY env var or: specsmith auth set uspto
    Get a key at: https://developer.uspto.gov/
    """
    from specsmith.patent import search_patents

    console.print(f"[bold]Searching USPTO[/bold]: {query}\n")
    try:
        results = search_patents(query, max_results=max_results)
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        raise SystemExit(1) from e

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    lines = []
    for i, r in enumerate(results, 1):
        console.print(f"  [bold]{i}. {r.patent_number}[/bold] — {r.title[:70]}")
        if r.filing_date:
            console.print(f"     Filed: {r.filing_date}  Assignee: {r.assignee[:40]}")
        lines.append(r.short_summary)

    if output:
        Path(output).write_text("\n".join(lines), encoding="utf-8")
        console.print(f"\n[green]\u2713[/green] Results saved to {output}")


@patent_group.command(name="prior-art")
@click.argument("claim")
@click.option("--max-results", default=10, help="Maximum results (default: 10).")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option(
    "--save",
    "save_report",
    is_flag=True,
    default=False,
    help="Save report to prior-art/ directory.",
)
def patent_prior_art_cmd(claim: str, max_results: int, project_dir: str, save_report: bool) -> None:
    """Analyze prior art for a patent claim.

    Extracts key terms, searches USPTO, and generates a prior art report.
    """
    from specsmith.patent import analyze_prior_art, save_prior_art_report

    root = Path(project_dir).resolve()
    console.print("[bold]Prior Art Analysis[/bold]\n")
    console.print(f"  Claim: {claim[:100]}..." if len(claim) > 100 else f"  Claim: {claim}")

    try:
        report = analyze_prior_art(claim, max_results=max_results)
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        raise SystemExit(1) from e

    if report.error:
        console.print(f"\n[yellow]\u26a0 {report.error}[/yellow]")
    elif not report.has_results:
        console.print("\n[green]No prior art found for this claim.[/green]")
    else:
        console.print(f"\n  Found {len(report.results)} prior art reference(s):")
        for r in report.results:
            console.print(f"  • {r.patent_number}: {r.title[:70]}")

    if save_report:
        prior_art_dir = root / "prior-art"
        out = save_prior_art_report(report, prior_art_dir)
        console.print(f"\n[green]\u2713[/green] Report saved to {out.relative_to(root)}")
    else:
        console.print("\n" + report.to_markdown()[:2000])


main.add_command(patent_group)


# ---------------------------------------------------------------------------
# Ollama — local model management
# ---------------------------------------------------------------------------


@main.group(name="ollama")
def ollama_group() -> None:
    """Manage Ollama local LLM models."""


@ollama_group.command(name="list")
def ollama_list_cmd() -> None:
    """List locally installed Ollama models."""
    from specsmith.ollama_cmds import get_installed_models, is_running

    if not is_running():
        console.print(
            "[red]\u2717[/red] Ollama is not running. Start it with: [bold]ollama serve[/bold]"
        )
        raise SystemExit(1)

    models = get_installed_models()
    if not models:
        console.print(
            "[yellow]No models installed.[/yellow] Pull one with: specsmith ollama pull <model>"
        )
        return

    console.print(f"[bold]Installed Ollama Models[/bold] ({len(models)})\n")
    for m in models:
        console.print(f"  [green]\u2713[/green] {m}")


@ollama_group.command(name="available")
@click.option(
    "--task",
    default="",
    help="Filter by task type: code, requirements, architecture, chat, analysis, reasoning.",
)
def ollama_available_cmd(task: str) -> None:
    """Show models available to download from the curated catalog."""
    from specsmith.ollama_cmds import get_installed_models, get_vram_gb, recommend_models

    vram = get_vram_gb()
    installed = set(get_installed_models())
    recs = recommend_models(vram_gb=vram, task=task)

    header = "[bold]Available Ollama Models[/bold]"
    if task:
        header += f" (task: {task})"
    if vram > 0:
        header += f" [dim]— GPU VRAM: {vram:.1f} GB[/dim]"
    else:
        header += " [dim]— no GPU detected (CPU mode)[/dim]"
    console.print(header + "\n")

    # Show catalog entries that fit VRAM budget
    for e in recs:
        is_inst = any(m.startswith(e.id.split(":")[0]) or m == e.id for m in installed)
        if is_inst:
            status = "[green]installed[/green]"
        else:
            status = f"[dim]{e.size_gb}GB \u2014 pull to install[/dim]"
        console.print(f"  {('[bold]' + e.tier + '[/bold]'):30s}  {e.name:28s}  {status}")
        console.print(f"  [dim]{'':<30s}  {', '.join(e.best_for[:2]):<28s}  {e.notes}[/dim]")
        console.print()

    if not recs:
        console.print("[yellow]No models fit within the detected VRAM budget.[/yellow]")
        console.print("Use a smaller model or run on CPU (all models listed without GPU).")

    console.print("[dim]Pull a model: specsmith ollama pull <model-id>[/dim]")


@ollama_group.command(name="gpu")
def ollama_gpu_cmd() -> None:
    """Detect GPU and available VRAM."""
    from specsmith.ollama_cmds import get_vram_gb

    vram = get_vram_gb()
    if vram > 0:
        console.print(
            f"[green]\u2713[/green] GPU detected \u2014 [bold]{vram:.1f} GB[/bold] VRAM available"
        )
        # Tier suggestions
        if vram >= 20:
            console.print("  Tier: [bold]Powerful[/bold] — all models supported (Qwen 2.5 32B+)")
        elif vram >= 9:
            console.print("  Tier: [bold]Capable[/bold] — 14B models (Phi-4, Qwen 14B, Gemma 12B)")
        elif vram >= 5:
            console.print("  Tier: [bold]Balanced[/bold] — 7B models (Qwen 7B, Mistral, Coder 7B)")
        else:
            console.print("  Tier: [bold]Tiny[/bold] — small models only (Llama 3.2 3B)")
    else:
        console.print("[yellow]\u2014[/yellow] No GPU detected — models will run on CPU (slow)")
        console.print("  Recommend: llama3.2:latest or mistral:latest for CPU use")


@ollama_group.command(name="pull")
@click.argument("model_id")
def ollama_pull_cmd(model_id: str) -> None:
    """Download a model via Ollama (streams progress).

    MODEL_ID: Ollama model tag, e.g. qwen2.5:14b

    Examples:\n
      specsmith ollama pull qwen2.5:14b\n
      specsmith ollama pull phi4:latest
    """
    from specsmith.ollama_cmds import is_running, pull_model

    if not is_running():
        console.print(
            "[red]\u2717[/red] Ollama is not running.\n"
            "  Start it: [bold]ollama serve[/bold]\n"
            "  Or open the Ollama desktop app."
        )
        raise SystemExit(1)

    console.print(f"[bold]Pulling[/bold] {model_id} …")
    last_status = ""
    for chunk in pull_model(model_id):
        status = chunk.get("status", "")
        if chunk.get("status") == "error":
            console.print(f"[red]\u2717 {chunk.get('message', 'unknown error')}[/red]")
            raise SystemExit(1)
        completed = chunk.get("completed", 0)
        total = chunk.get("total", 0)
        if total and completed:
            pct = int(completed / total * 100)
            mb = completed // (1024 * 1024)
            total_mb = total // (1024 * 1024)
            line = f"  {status}: {pct}% ({mb}/{total_mb} MB)"
        elif status and status != last_status:
            line = f"  {status}"
        else:
            continue
        last_status = status
        console.print(line)

    console.print(f"[green]\u2713[/green] {model_id} ready.")


@ollama_group.command(name="suggest")
@click.argument(
    "task",
    type=click.Choice(["code", "requirements", "architecture", "chat", "analysis", "reasoning"]),
)
def ollama_suggest_cmd(task: str) -> None:
    """Suggest the best installed Ollama models for a task.

    TASK: code | requirements | architecture | chat | analysis | reasoning
    """
    from specsmith.ollama_cmds import get_installed_models, get_vram_gb, recommend_models

    vram = get_vram_gb()
    installed = set(get_installed_models())
    recs = recommend_models(vram_gb=vram, task=task)

    inst_recs = [
        e for e in recs if any(m.startswith(e.id.split(":")[0]) or m == e.id for m in installed)
    ]
    not_inst = [e for e in recs if e not in inst_recs]

    console.print(f"[bold]Model Suggestions[/bold] for task: [bold]{task}[/bold]\n")

    if inst_recs:
        console.print("[green]Ready to use:[/green]")
        for e in inst_recs[:3]:
            console.print(f"  [green]\u2713[/green] {e.name:28s} {e.notes}")
        console.print()

    if not_inst:
        console.print("[dim]Available to download:[/dim]")
        for e in not_inst[:3]:
            console.print(
                f"  [dim]\u21d3[/dim] {e.name:28s} "
                f"{e.size_gb}GB \u2014 specsmith ollama pull {e.id}"
            )

    if not inst_recs and not not_inst:
        console.print("[yellow]No matching models found.[/yellow]")
        console.print(
            f"  Run [bold]specsmith ollama available --task {task}[/bold] to see options."
        )


main.add_command(ollama_group)


# ---------------------------------------------------------------------------
# Credits check + hard cap (#52)
# ---------------------------------------------------------------------------


@credits.command(name="check")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def credits_check_cmd(project_dir: str) -> None:
    """Check current credit spend against budget (hard cap enforcement)."""
    from specsmith.credits import get_summary, load_budget

    root = Path(project_dir).resolve()
    budget = load_budget(root)
    summary = get_summary(root)

    cap = budget.monthly_cap_usd
    enforcement = getattr(budget, "enforcement_mode", "soft")

    console.print("[bold]Credit Budget Status[/bold]\n")
    console.print(f"  Monthly spend:   ${summary.total_cost_usd:.4f}")
    console.print(f"  Monthly cap:     {'unlimited' if cap == 0 else f'${cap:.2f}'}")
    console.print(f"  Mode:            {enforcement}")

    if cap > 0:
        pct = (summary.total_cost_usd / cap) * 100
        bar_filled = int(pct / 5)  # 20-char bar
        bar = "\u2588" * bar_filled + "\u2591" * (20 - bar_filled)
        color = "red" if pct >= 100 else ("yellow" if pct >= 80 else "green")
        console.print(f"  Usage:           [{color}]{bar}[/{color}] {pct:.1f}%")

        if pct >= 100 and enforcement == "hard":
            console.print(
                f"\n[bold red]HARD CAP EXCEEDED[/bold red] — "
                f"${summary.total_cost_usd:.4f} / ${cap:.2f}. "
                f"New agent sessions blocked. Raise cap or reset billing period."
            )
            raise SystemExit(2)
        elif pct >= budget.alert_threshold_pct:
            pct_threshold = budget.alert_threshold_pct
            console.print(f"\n[yellow]\u26a0 Alert threshold ({pct_threshold}%) reached.[/yellow]")
        else:
            console.print("\n[green]\u2713 Within budget.[/green]")
    else:
        console.print("\n[dim]No cap configured — unlimited spending.[/dim]")

    for alert in summary.alerts:
        console.print(f"  [yellow]\u26a0[/yellow] {alert}")


# ---------------------------------------------------------------------------
# Token Optimization
# ---------------------------------------------------------------------------


@main.command(name="optimize")
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory.",
)
@click.option(
    "--provider",
    "provider_name",
    default="anthropic",
    help="Provider to estimate savings for (anthropic, openai, gemini, mistral).",
)
@click.option(
    "--model",
    default="",
    help="Model to estimate savings for (default: provider default).",
)
def optimize_cmd(project_dir: str, provider_name: str, model: str) -> None:
    """Analyse token usage and estimate monthly credit savings.

    Reads .specsmith/credits.json usage history, applies optimization
    model, and prints a report with projected savings and recommendations.

    Strategies modelled: response caching (30-70%), model routing (40-60%),
    context trimming (20%), prompt caching (50-90% on Anthropic).
    """
    from specsmith.agent.optimizer import (
        ComplexityTier,
        ModelRouter,
        estimate_session_savings,
    )
    from specsmith.credits import get_summary

    root = Path(project_dir).resolve()
    summary = get_summary(root)

    # Derive session-level averages from credit history
    sessions = max(1, summary.session_count)
    total_in = summary.total_tokens_in or 1000
    total_out = summary.total_tokens_out or 300
    avg_in = total_in // sessions
    avg_out = total_out // sessions

    # Pick best model name
    router = ModelRouter()
    resolved_model = model or router.suggest_model(provider_name, ComplexityTier.BALANCED)

    est = estimate_session_savings(
        provider=provider_name,
        model=resolved_model,
        total_calls=sessions,
        avg_input_tokens=avg_in,
        avg_output_tokens=avg_out,
    )

    console.print("\n[bold]Token & Credit Optimization Report[/bold]\n")
    console.print(f"  Provider:            {provider_name} / {resolved_model}")
    console.print(f"  Sessions analysed:   {sessions}")
    console.print(f"  Avg input tokens:    {avg_in:,}")
    console.print(f"  Avg output tokens:   {avg_out:,}")
    console.print()
    console.print(f"  Baseline / month:    [yellow]${est['baseline_usd']:.2f}[/yellow]")
    console.print()
    console.print("  [bold]Projected savings:[/bold]")
    console.print(
        f"    Response caching (30%+ hit rate):  [green]+${est['cache_savings_usd']:.2f}/mo[/green]"
    )
    routing_val = est["routing_savings_usd"]
    console.print(f"    Model routing (40% FAST tasks):    [green]+${routing_val:.2f}/mo[/green]")
    console.print(
        f"    Context trimming (~20% reduction): [green]+${est['trim_savings_usd']:.2f}/mo[/green]"
    )
    if provider_name == "anthropic":
        prompt_cache_savings = est["baseline_usd"] * 0.45  # 90% on cached reads, ~50% of calls
        console.print(
            f"    Anthropic prompt caching (90%):    [green]+${prompt_cache_savings:.2f}/mo[/green]"
        )
        est["total_savings_usd"] = round(est["total_savings_usd"] + prompt_cache_savings, 2)
        est["savings_pct"] = min(
            95, round(est["total_savings_usd"] / max(est["baseline_usd"], 0.01) * 100, 1)
        )

    console.print()
    console.print(
        f"  [bold green]Total estimated saving:  "
        f"${est['total_savings_usd']:.2f}/mo ({est['savings_pct']:.0f}%)[/bold green]"
    )

    # Recommendations
    console.print("\n[bold]Recommendations:[/bold]")
    console.print("  1. Run specsmith with --optimize flag: [bold]specsmith run --optimize[/bold]")
    console.print("  2. Anthropic users get 90% discount on cached system prompts (auto-enabled).")
    console.print(
        "  3. Use [bold]specsmith run --provider anthropic --model claude-haiku-4-5[/bold]"
        " for simple governance queries."
    )
    console.print(
        "  4. Run [bold]/clear[/bold] every 20-30 turns to reset context and avoid "
        "compounding history costs."
    )
    console.print(
        "  5. Batch tool calls where possible — one audit + validate + doctor costs less"
        " than three separate calls."
    )


# ---------------------------------------------------------------------------
# GUI Workbench
# ---------------------------------------------------------------------------


@main.command(name="gui")
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root to open as the first tab.",
)
@click.option(
    "--provider",
    "provider_name",
    default=None,
    help="Default LLM provider for new sessions.",
)
@click.option("--model", default=None, help="Default model for new sessions.")
def gui_cmd(project_dir: str, provider_name: str | None, model: str | None) -> None:
    """Launch the AEE Workbench — multi-tab epistemic engineering GUI.

    Requires: pip install specsmith[gui]
    """
    try:
        from specsmith.gui.app import launch
    except ImportError:
        console.print(
            "[red]PySide6 is required for the GUI.[/red]\n"
            "Install it: [bold]pip install specsmith[gui][/bold]"
        )
        raise SystemExit(1) from None

    launch(
        project_dir=str(Path(project_dir).resolve()),
        provider_name=provider_name,
        model=model,
    )


# ---------------------------------------------------------------------------
# Phase — AEE Workflow Phase Tracker
# ---------------------------------------------------------------------------


@main.group(name="phase")
def phase_group() -> None:
    """Track and advance the AEE workflow phase for a project.

    The 7 phases of the AEE development cycle:\n
      inception → architecture → requirements → test_spec → implementation → verification → release
    """


@phase_group.command(name="show", hidden=False)
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project root (default: current directory).",
)
def phase_show(project_dir: str) -> None:
    """Show the current AEE workflow phase and its readiness checklist."""
    from specsmith.phase import PHASE_MAP, evaluate_phase, phase_progress_pct, read_phase

    root = Path(project_dir).resolve()
    phase_key = read_phase(root)
    phase = PHASE_MAP[phase_key]
    passed, failed = evaluate_phase(phase, root)
    pct = phase_progress_pct(phase, root)

    console.print(f"\n  {phase.emoji} [bold]{phase.label}[/bold] ({phase_key})")
    console.print(f"  {phase.description}")
    console.print()
    console.print(f"  Readiness: {pct}% ({len(passed)}/{len(phase.checks)} checks pass)")
    console.print()

    for desc in passed:
        console.print(f"  [green]\u2713[/green] {desc}")
    for desc in failed:
        console.print(f"  [red]\u2717[/red] {desc}")

    if phase.commands:
        console.print("\n  [bold]Recommended commands:[/bold]")
        for cmd in phase.commands:
            console.print(f"    {cmd}")

    if phase.next_phase and not failed:
        console.print(
            f"\n  [green]\u2713 Ready to advance[/green] — "
            f"run [bold]specsmith phase next[/bold] to move to [bold]{phase.next_phase}[/bold]."
        )
    elif phase.next_phase and failed:
        console.print(
            f"\n  [yellow]\u26a0 {len(failed)} check(s) remaining[/yellow] before advancing to"
            f" [bold]{phase.next_phase}[/bold]."
        )
    console.print()


@phase_group.command(name="set")
@click.argument("phase_key")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Set phase without readiness check.",
)
def phase_set(phase_key: str, project_dir: str, force: bool) -> None:
    """Explicitly set the AEE workflow phase.

    PHASE_KEY: inception | architecture | requirements | test_spec
    PHASE_KEY: implementation | verification | release
    """
    from specsmith.phase import PHASE_MAP, evaluate_phase, write_phase

    if phase_key not in PHASE_MAP:
        console.print(f"[red]Unknown phase: {phase_key}[/red]")
        console.print("Valid: " + " | ".join(PHASE_MAP.keys()))
        raise SystemExit(1)

    root = Path(project_dir).resolve()
    phase = PHASE_MAP[phase_key]
    _, failed = evaluate_phase(phase, root)

    if failed and not force:
        console.print(
            f"[yellow]\u26a0 {len(failed)} check(s) not yet passing for {phase.label}:[/yellow]"
        )
        for desc in failed:
            console.print(f"  [dim]\u2717 {desc}[/dim]")
        console.print(
            "\n  Use [bold]--force[/bold] to set the phase anyway, or fix the checks first."
        )
        raise SystemExit(1)

    write_phase(root, phase_key)
    console.print(
        f"[green]\u2713[/green] Phase set to "
        f"[bold]{phase.emoji} {phase.label}[/bold] for {root.name}."
    )


@phase_group.command(name="next")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Advance even if readiness checks have not all passed.",
)
def phase_next(project_dir: str, force: bool) -> None:
    """Advance to the next AEE workflow phase.

    Performs readiness checks on the current phase first.
    Use --force to skip checks.
    """
    from specsmith.phase import PHASE_MAP, evaluate_phase, read_phase, write_phase

    root = Path(project_dir).resolve()
    phase_key = read_phase(root)
    phase = PHASE_MAP[phase_key]
    _, failed = evaluate_phase(phase, root)

    if failed and not force:
        console.print(
            f"[yellow]\u26a0 {len(failed)} check(s) must pass before advancing "
            f"from {phase.label}:[/yellow]"
        )
        for desc in failed:
            console.print(f"  [dim]\u2717 {desc}[/dim]")
        console.print("\n  Fix the checks above, or use [bold]--force[/bold] to advance anyway.")
        raise SystemExit(1)

    if not phase.next_phase:
        console.print(
            f"[bold]{phase.emoji} {phase.label}[/bold] is the final phase. "
            "After release, the cycle restarts with [bold]inception[/bold] for the next version."
        )
        return

    write_phase(root, phase.next_phase)
    next_phase = PHASE_MAP[phase.next_phase]
    console.print(
        f"[green]\u2713[/green] Advanced from [bold]{phase.label}[/bold] "
        f"to [bold]{next_phase.emoji} {next_phase.label}[/bold]."
    )
    console.print(f"  {next_phase.description}")
    if next_phase.commands:
        console.print("\n  [bold]Next steps:[/bold]")
        for cmd in next_phase.commands:
            console.print(f"    {cmd}")


@phase_group.command(name="status")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def phase_status(project_dir: str) -> None:
    """Print a compact one-line phase status (for IDE/CI integration).

    Output format: <phase_key> <emoji> <label> <pct>%  e.g. 'requirements 📋 Requirements 60%'
    """
    from specsmith.phase import PHASE_MAP, phase_progress_pct, read_phase

    root = Path(project_dir).resolve()
    phase_key = read_phase(root)
    phase = PHASE_MAP[phase_key]
    pct = phase_progress_pct(phase, root)
    console.print(f"{phase_key} {phase.emoji} {phase.label} {pct}%")


@phase_group.command(name="list")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def phase_list(project_dir: str) -> None:
    """List all AEE lifecycle phases with current position highlighted."""
    from specsmith.phase import PHASES, read_phase

    root = Path(project_dir).resolve()
    current = read_phase(root)

    console.print("[bold]AEE Project Lifecycle[/bold]\n")
    console.print(
        "  inception \u2192 architecture \u2192 requirements \u2192 test_spec "
        "\u2192 implementation \u2192 verification \u2192 release\n"
    )
    for i, p in enumerate(PHASES, 1):
        is_cur = p.key == current
        marker = "[bold cyan]\u25b6[/bold cyan]" if is_cur else " "
        label = f"[bold cyan]{p.label:<20s}[/bold cyan]" if is_cur else f"{p.label:<20s}"
        console.print(f"  {marker} {i}. {p.emoji} {label} {p.description}")
    console.print(f"\n  Current: [bold]{current}[/bold]")


main.add_command(phase_group)


# ---------------------------------------------------------------------------
# specsmith info — capability report
# ---------------------------------------------------------------------------


@main.command(name="info")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
@click.option(
    "--section",
    type=click.Choice(["languages", "types", "tools", "backends", "phases", "all"]),
    default="all",
    help="Which section to show (default: all).",
)
def info_cmd(as_json: bool, section: str) -> None:
    """Report all specsmith capabilities: languages, project types, tools, LLM backends."""
    import json as json_mod  # noqa: PLC0415

    from specsmith.config import _TYPE_LABELS, ProjectType  # noqa: PLC0415
    from specsmith.languages import EXT_LANG, LANG_CATEGORY, LANG_DISPLAY  # noqa: PLC0415
    from specsmith.ollama_cmds import CATALOG as OLLAMA_CATALOG  # noqa: PLC0415
    from specsmith.phase import PHASES  # noqa: PLC0415

    result: dict = {}

    if section in ("languages", "all"):
        # Group display names by category
        cats: dict[str, list[str]] = {}
        seen_langs: set[str] = set()
        for lang_key, display in sorted(LANG_DISPLAY.items(), key=lambda x: x[1]):
            cat = LANG_CATEGORY.get(lang_key, "Other")
            exts = [e for e, lk in EXT_LANG.items() if lk == lang_key]
            if lang_key not in seen_langs:
                seen_langs.add(lang_key)
                cats.setdefault(cat, []).append(
                    {"key": lang_key, "name": display, "extensions": sorted(exts)}
                )
        result["languages"] = cats
        if not as_json:
            console.print("[bold]Languages[/bold]\n")
            for cat, langs in sorted(cats.items()):
                console.print(f"  [teal]{cat}[/teal]")
                for l_info in langs:
                    exts_str = "  ".join(l_info["extensions"][:6]) or "(filename)"
                    console.print(f"    {l_info['name']:<28s} {exts_str}")
            console.print()

    if section in ("types", "all"):
        type_groups: dict[str, list[dict]] = {}
        categories = {
            "python": "Python",
            "rust": "Rust / Go",
            "go": "Rust / Go",
            "c": "C / C++",
            "cpp": "C / C++",
            "fpga": "Hardware / FPGA",
            "embedded": "Hardware / FPGA",
            "mixed": "Hardware / FPGA",
            "yocto": "Hardware / FPGA",
            "pcb": "Hardware / FPGA",
            "web": "Web / JS",
            "fullstack": "Web / JS",
            "browser": "Web / JS",
            "mobile": "Mobile",
            "dotnet": ".NET / C#",
            "devops": "DevOps / Data",
            "data": "DevOps / Data",
            "microservices": "DevOps / Data",
            "spec": "Documents",
            "user": "Documents",
            "research": "Documents",
            "api": "Documents",
            "requirements": "Documents",
            "business": "Business / Legal",
            "patent": "Business / Legal",
            "legal": "Business / Legal",
            "monorepo": "Other",
            "epistemic": "AEE",
            "knowledge": "AEE",
            "aee": "AEE",
        }
        for pt in ProjectType:
            label = _TYPE_LABELS.get(pt, pt.value)
            key_prefix = pt.value.split("-")[0]
            cat = categories.get(key_prefix, "Other")
            type_groups.setdefault(cat, []).append({"key": pt.value, "label": label})
        result["project_types"] = type_groups
        if not as_json:
            console.print("[bold]Project Types[/bold]\n")
            for cat, types in sorted(type_groups.items()):
                console.print(f"  [teal]{cat}[/teal]")
                for t in types:
                    console.print(f"    {t['key']:<35s} {t['label']}")
            console.print()

    if section in ("tools", "all"):
        fpga_tools = [
            {
                "id": e.id,
                "name": e.name,
                "vram_gb": e.vram_gb,
                "tier": e.tier,
                "best_for": e.best_for,
                "notes": e.notes,
            }
            for e in OLLAMA_CATALOG
        ]
        result["ollama_catalog"] = fpga_tools
        if not as_json:
            console.print("[bold]Ollama Model Catalog[/bold]  (GPU-aware)\n")
            for e in OLLAMA_CATALOG:
                console.print(
                    f"  {e.name:<32s} {e.vram_gb:4.1f}GB  [dim]{', '.join(e.best_for[:2])}[/dim]"
                )
            console.print()

    if section in ("backends", "all"):
        providers = [
            {"name": "anthropic", "env": "ANTHROPIC_API_KEY", "models": "Claude 3/4 series"},
            {"name": "openai", "env": "OPENAI_API_KEY", "models": "GPT-4o, o3, o4-mini"},
            {"name": "gemini", "env": "GOOGLE_API_KEY", "models": "Gemini 2.5 Pro/Flash"},
            {"name": "mistral", "env": "MISTRAL_API_KEY", "models": "Mistral, Codestral, Pixtral"},
            {"name": "ollama", "env": "(none — local)", "models": "Local models via Ollama"},
        ]
        import os

        for p in providers:
            p["configured"] = bool(os.environ.get(p["env"])) or p["name"] == "ollama"
        result["llm_backends"] = providers
        if not as_json:
            console.print("[bold]LLM Backends[/bold]\n")
            for p in providers:
                icon = "[green]\u2713[/green]" if p["configured"] else "[dim]\u2014[/dim]"
                console.print(f"  {icon} {p['name']:<12s} {p['env']:<28s} {p['models']}")
            console.print()

    if section in ("phases", "all"):
        phases_info = [
            {
                "key": p.key,
                "label": p.label,
                "emoji": p.emoji,
                "description": p.description,
                "commands": p.commands,
            }
            for p in PHASES
        ]
        result["aee_phases"] = phases_info
        if not as_json:
            console.print("[bold]AEE Workflow Phases[/bold]\n")
            for p in PHASES:
                console.print(f"  {p.emoji} [bold]{p.label:<22s}[/bold] {p.description}")
            console.print()

    if as_json:
        console.print(json_mod.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# specsmith scan — project scanner
# ---------------------------------------------------------------------------


@main.command(name="scan")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Print only the suggested scaffold.yml block.",
)
def scan_cmd(project_dir: str, as_json: bool, quiet: bool) -> None:
    """Scan a project and suggest language, type, name, and scaffold configuration.

    Reads file extensions, build system files, git remote, and existing governance
    to produce ready-to-use scaffold.yml suggestions.
    """
    import json as json_mod  # noqa: PLC0415

    from specsmith.config import _TYPE_LABELS, ProjectType  # noqa: PLC0415
    from specsmith.importer import (  # noqa: PLC0415
        detect_project,
        suggest_auxiliary,
        suggest_name,
        suggest_type,
    )
    from specsmith.languages import LANG_DISPLAY  # noqa: PLC0415

    root = Path(project_dir).resolve()
    result = detect_project(root)
    name = suggest_name(root)
    ptype = suggest_type(result)
    aux = suggest_auxiliary(result)

    # Detect FPGA tools from languages
    fpga_langs = {"vhdl", "verilog", "systemverilog"}
    fpga_tools: list[str] = []
    if any(lang in fpga_langs for lang in result.languages):
        if any(f.suffix == ".xpr" or f.suffix == ".xdc" for f in root.rglob("*")):
            fpga_tools = ["vivado"]
        elif any(f.suffix == ".qpf" or f.suffix == ".qsf" for f in root.rglob("*")):
            fpga_tools = ["quartus"]
        else:
            fpga_tools = ["ghdl", "gtkwave"]

    # Language display names (top 5)
    top_langs = [LANG_DISPLAY.get(lk, lk) for lk in list(result.languages.keys())[:5]]
    valid_vals = {t.value for t in ProjectType}
    type_label = _TYPE_LABELS.get(ProjectType(ptype), ptype) if ptype in valid_vals else ptype

    if as_json:
        console.print(
            json_mod.dumps(
                {
                    "name": name,
                    "type": ptype,
                    "type_label": type_label,
                    "languages": top_langs,
                    "fpga_tools": fpga_tools,
                    "auxiliary_disciplines": aux,
                    "vcs_platform": result.vcs_platform or "github",
                    "build_system": result.build_system,
                },
                indent=2,
            )
        )
        return

    if not quiet:
        console.print(f"[bold]specsmith scan[/bold] — {root}\n")
        console.print(f"  Name          : [bold]{name}[/bold]")
        console.print(f"  Primary type  : [bold]{type_label}[/bold] [dim]({ptype})[/dim]")
        if aux:
            console.print(f"  Aux disciplines: {', '.join(aux)}")
        if top_langs:
            console.print(f"  Languages     : {', '.join(top_langs)}")
        if fpga_tools:
            console.print(f"  FPGA tools    : {', '.join(fpga_tools)}")
        if result.build_system:
            console.print(f"  Build system  : {result.build_system}")
        if result.vcs_platform:
            console.print(f"  VCS platform  : {result.vcs_platform}")
        console.print()
        console.print("[bold]Suggested scaffold.yml[/bold]\n")

    # Build YAML block
    lines = [
        f"name: {name}",
        f"type: {ptype}",
        f"vcs_platform: {result.vcs_platform or 'github'}",
    ]
    if top_langs:
        lines.append("languages:")
        for l_name in top_langs[:6]:
            lines.append(f"  - {l_name}")
    if fpga_tools:
        lines.append("fpga_tools:")
        for t in fpga_tools:
            lines.append(f"  - {t}")
    if aux:
        lines.append("auxiliary_disciplines:")
        for a in aux:
            lines.append(f"  - {a}")

    console.print("\n".join(lines))


# ---------------------------------------------------------------------------
# Ollama — model manager additions (remove, update, version, check-updates, upgrade)
# ---------------------------------------------------------------------------


@ollama_group.command(name="remove")
@click.argument("model_id")
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation prompt.")
def ollama_remove_cmd(model_id: str, yes: bool) -> None:
    """Remove an installed Ollama model."""
    from specsmith.ollama_cmds import delete_model, is_running

    if not is_running():
        console.print("[red]\u2717[/red] Ollama is not running.")
        raise SystemExit(1)

    if not yes:
        ans = click.confirm(f"Remove model '{model_id}'?")
        if not ans:
            console.print("[dim]Cancelled.[/dim]")
            return

    ok = delete_model(model_id)
    if ok:
        console.print(f"[green]\u2713[/green] {model_id} removed.")
    else:
        console.print(
            f"[red]\u2717[/red] Could not remove {model_id} (not installed or API error)."
        )
        raise SystemExit(1)


@ollama_group.command(name="update")
@click.argument("model_id", required=False, default="")
@click.option(
    "--all",
    "update_all",
    is_flag=True,
    default=False,
    help="Update all installed models.",
)
def ollama_update_cmd(model_id: str, update_all: bool) -> None:
    """Re-pull a model to get the latest version.

    MODEL_ID: specific model to update, or use --all for every installed model.
    """
    from specsmith.ollama_cmds import get_installed_models, is_running, pull_model

    if not is_running():
        console.print("[red]\u2717[/red] Ollama is not running.")
        raise SystemExit(1)

    if not model_id and not update_all:
        console.print("[yellow]Specify a MODEL_ID or use --all.[/yellow]")
        raise SystemExit(1)

    targets = get_installed_models() if update_all else [model_id]
    if not targets:
        console.print("[yellow]No models installed.[/yellow]")
        return

    for mid in targets:
        console.print(f"\n[bold]Updating[/bold] {mid} …")
        last = ""
        for chunk in pull_model(mid):
            status = chunk.get("status", "")
            if chunk.get("status") == "error":
                console.print(f"[red]\u2717 {chunk.get('message', 'error')}[/red]")
                break
            completed = chunk.get("completed", 0)
            total = chunk.get("total", 0)
            if total and completed:
                pct = int(completed / total * 100)
                mb = completed // (1024 * 1024)
                tmb = total // (1024 * 1024)
                console.print(f"  {status}: {pct}% ({mb}/{tmb} MB)")
            elif status and status != last:
                console.print(f"  {status}")
                last = status
        else:
            console.print(f"[green]\u2713[/green] {mid} up to date.")


@ollama_group.command(name="version")
def ollama_version_cmd() -> None:
    """Show installed Ollama server version and check for updates."""
    from specsmith.ollama_cmds import check_ollama_update, upgrade_ollama_cmd

    installed, latest = check_ollama_update()
    if installed:
        console.print(f"  Installed : [bold]{installed}[/bold]")
    else:
        console.print("  Installed : [red]Ollama not running[/red]")
    if latest:
        if installed and latest != installed:
            console.print(f"  Latest    : [green]{latest}[/green]  ← update available")
            console.print(
                f"\n  Upgrade: [bold]{upgrade_ollama_cmd()}[/bold]\n"
                "  Or: [bold]specsmith ollama upgrade[/bold]"
            )
        elif installed:
            console.print(f"  Latest    : {latest}  [green]\u2713 up to date[/green]")
    else:
        console.print("  Latest    : [dim](could not reach GitHub)[/dim]")


@ollama_group.command(name="check-updates")
def ollama_check_updates_cmd() -> None:
    """Check if model updates are available for installed models.

    Re-pulling a model is the only way to know if a newer digest exists; this
    command just shows installed models and prompts to update individually.
    Use 'specsmith ollama update --all' to pull the latest version for all.
    """
    from specsmith.ollama_cmds import get_installed_models_detail, is_running

    if not is_running():
        console.print("[red]\u2717[/red] Ollama is not running.")
        raise SystemExit(1)

    models = get_installed_models_detail()
    if not models:
        console.print("[yellow]No models installed.[/yellow]")
        return

    console.print(f"[bold]Installed Models[/bold] ({len(models)})\n")
    for m in models:
        name = m.get("name", "?")
        size = m.get("size", 0)
        gb = size / (1024**3) if size else 0
        mod = m.get("modified_at", "")[:10]
        console.print(f"  [green]\u2713[/green] {name:<40s} {gb:5.1f}GB  [{mod}]")

    console.print(
        "\n[dim]Ollama tags are not versioned like Docker — re-pulling is the update check.\n"
        "  Run: [bold]specsmith ollama update --all[/bold] to pull latest digests.[/dim]"
    )


@ollama_group.command(name="upgrade")
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Run the upgrade command directly; otherwise just prints it.",
)
def ollama_upgrade_cmd(yes: bool) -> None:
    """Upgrade Ollama itself to the latest version."""
    from specsmith.ollama_cmds import upgrade_ollama_cmd

    cmd = upgrade_ollama_cmd()
    if yes:
        import subprocess

        console.print(f"[bold]Running:[/bold] {cmd}")
        subprocess.run(cmd, shell=True, check=False)  # noqa: S602
    else:
        console.print(f"[bold]Upgrade command:[/bold] {cmd}")
        console.print(
            "\n  Run it directly or use [bold]specsmith ollama upgrade --yes[/bold] "
            "to execute automatically."
        )


# ---------------------------------------------------------------------------
# Tools — tool registry scan
# ---------------------------------------------------------------------------


@main.group(name="tools")
def tools_group() -> None:
    """Inspect and scan development tools for a project."""


@tools_group.command(name="scan")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
@click.option(
    "--fpga",
    is_flag=True,
    default=False,
    help="Include FPGA/HDL tool checks from fpga_tools in scaffold.yml.",
)
def tools_scan_cmd(project_dir: str, as_json: bool, fpga: bool) -> None:
    """Scan the project and check which tools are installed on PATH.

    Reads scaffold.yml to determine the project type and required tools,
    then checks each tool against PATH, reporting installed (with version)
    or missing for each.

    Also checks any tools listed in ``fpga_tools`` when --fpga is given.
    """
    import json as json_mod
    import re
    import shutil
    import subprocess

    import yaml

    from specsmith.config import ProjectConfig
    from specsmith.doctor import _check_tool

    root = Path(project_dir).resolve()
    scaffold_path = root / "scaffold.yml"

    checks: list[dict] = []

    # Standard project tools via doctor
    if scaffold_path.exists():
        try:
            with open(scaffold_path) as f:
                raw = yaml.safe_load(f) or {}
            config = ProjectConfig(**raw)
            from specsmith.tools import get_tools

            tools = get_tools(config)
            for category, cmds in [
                ("lint", tools.lint),
                ("typecheck", tools.typecheck),
                ("test", tools.test),
                ("security", tools.security),
                ("build", tools.build),
                ("format", tools.format),
                ("compliance", tools.compliance),
            ]:
                seen: set[str] = set()
                for cmd in cmds:
                    tool_name = cmd.split()[0]
                    if tool_name in seen:
                        continue
                    seen.add(tool_name)
                    chk = _check_tool(tool_name, category, root=root)
                    checks.append(
                        {
                            "name": chk.name,
                            "category": chk.category,
                            "installed": chk.installed,
                            "version": chk.version,
                        }
                    )
        except Exception as e:  # noqa: BLE001
            if not as_json:
                console.print(f"[yellow]Could not read scaffold.yml: {e}[/yellow]")

    # FPGA/HDL tools from scaffold.yml fpga_tools list
    if fpga and scaffold_path.exists():
        try:
            with open(scaffold_path) as f:
                raw = yaml.safe_load(f) or {}
            fpga_tool_list: list[str] = raw.get("fpga_tools", [])

            # Well-known FPGA tool executables
            FPGA_TOOL_EXES: dict[str, str] = {
                "vivado": "vivado",
                "quartus": "quartus_sh",
                "radiant": "radiantlsp",
                "diamond": "diamondc",
                "gowin": "gw_sh",
                "ghdl": "ghdl",
                "iverilog": "iverilog",
                "verilator": "verilator",
                "modelsim": "vsim",
                "questasim": "vsim",
                "xsim": "xsim",
                "gtkwave": "gtkwave",
                "surfer": "surfer",
                "vsg": "vsg",
                "verible": "verible-verilog-lint",
                "svlint": "svlint",
                "symbiyosys": "sby",
                "yosys": "yosys",
                "nextpnr": "nextpnr-ecp5",
                "openFPGALoader": "openFPGALoader",
            }
            for tool_key in fpga_tool_list:
                exe = FPGA_TOOL_EXES.get(tool_key, tool_key)
                path_found = shutil.which(exe)
                version = ""
                if path_found:
                    try:
                        r = subprocess.run(
                            [exe, "--version"], capture_output=True, text=True, timeout=5
                        )
                        ver_out = (r.stdout + r.stderr).strip().splitlines()
                        if ver_out:
                            m = re.search(r"[0-9]+\.[0-9.]+", ver_out[0])
                            version = m.group(0) if m else ver_out[0][:30]
                    except Exception:  # noqa: BLE001
                        pass
                checks.append(
                    {
                        "name": exe,
                        "category": "fpga",
                        "installed": bool(path_found),
                        "version": version,
                    }
                )
        except Exception as e:  # noqa: BLE001
            if not as_json:
                console.print(f"[yellow]Could not read fpga_tools: {e}[/yellow]")

    if as_json:
        console.print(json_mod.dumps({"tools": checks}, indent=2))
        return

    if not checks:
        console.print("[yellow]No tools found. Does scaffold.yml exist?[/yellow]")
        return

    installed_count = sum(1 for c in checks if c["installed"])
    console.print(
        f"[bold]Tool Scan[/bold] — {root.name}  "
        f"[green]{installed_count}[/green]/[dim]{len(checks)}[/dim] installed\n"
    )

    # Group by category
    cats: dict[str, list[dict]] = {}
    for c in checks:
        cats.setdefault(c["category"], []).append(c)

    for cat, items in sorted(cats.items()):
        console.print(f"  [teal]{cat}[/teal]")
        for item in items:
            icon = "[green]\u2713[/green]" if item["installed"] else "[red]\u2717[/red]"
            ver = f" [dim]{item['version']}[/dim]" if item["version"] else ""
            console.print(f"    {icon} {item['name']}{ver}")
    console.print()
    if installed_count < len(checks):
        missing = [c["name"] for c in checks if not c["installed"]]
        console.print(
            f"  [yellow]Missing:[/yellow] {', '.join(missing[:8])}"
            + (" and more..." if len(missing) > 8 else "")
        )


@tools_group.command(name="install")
@click.argument("tool", required=False, default="")
@click.option(
    "--list",
    "list_all",
    is_flag=True,
    default=False,
    help="List all known installable tools.",
)
@click.option(
    "--category",
    default="",
    help="Filter by category (fpga, python, c, rust, go, devops, linux, doc, js, other).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Print the install command without running it.",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Run the install command without prompting.",
)
def tools_install_cmd(tool: str, list_all: bool, category: str, dry_run: bool, yes: bool) -> None:
    """Show or run the install command for a development tool.

    TOOL is the tool key (e.g. ghdl, ruff, verilator). Run with --list to see
    all available tools.  The best install method for the current platform is
    selected automatically (winget on Windows, brew on macOS, apt/dnf on Linux).
    """
    import subprocess

    from specsmith.tool_installer import (
        KNOWN_TOOLS,
        ToolInstallInfo,
        get_install_command,
        list_tools,
    )

    if list_all or not tool:
        items: list[ToolInstallInfo] = list_tools(category=category or None)
        console.print(f"[bold]Known installable tools[/bold] ({len(items)})\n")
        cats: dict[str, list[ToolInstallInfo]] = {}
        for t in items:
            cats.setdefault(t.category, []).append(t)
        for cat, ts in sorted(cats.items()):
            console.print(f"  [teal]{cat}[/teal]")
            for t in ts:
                console.print(f"    [dim]{t.key:<25s}[/dim]  {t.display_name}")
        console.print()
        console.print(
            "  Run [bold]specsmith tools install <key>[/bold] to get the install command."
        )
        return

    info = KNOWN_TOOLS.get(tool)
    if info is None:
        # Fuzzy fallback: substring match
        matches = [k for k in KNOWN_TOOLS if tool.lower() in k.lower()]
        if matches:
            console.print(
                f"[yellow]Unknown tool '{tool}'. Did you mean: {', '.join(matches[:5])}?[/yellow]"
            )
        else:
            console.print(
                f"[red]Unknown tool '{tool}'.[/red] "
                "Run [bold]specsmith tools install --list[/bold] "
                "to see available tools."
            )
        raise SystemExit(1)

    cmd = get_install_command(tool)
    if cmd is None:
        if info.manual:
            console.print(
                f"[yellow]No automatic install for '{info.display_name}' on this platform.[/yellow]"
            )
            console.print(f"  Manual install: {info.manual}")
        else:
            console.print(f"[red]No install method known for '{tool}'.[/red]")
        return

    if info.notes:
        console.print(f"[dim]Note:[/dim] {info.notes}")

    if dry_run or not yes:
        console.print(f"\n[bold]Install command for {info.display_name}:[/bold]")
        console.print(f"  [teal]{cmd}[/teal]")
        if not dry_run and not yes:
            confirmed = console.input("\nRun this command now? [[bold]y[/bold]/N] ").strip().lower()
            if confirmed not in ("y", "yes"):
                console.print("[dim]Aborted.[/dim]")
                return
    if not dry_run:
        console.print(f"[bold]Running:[/bold] {cmd}")
        result = subprocess.run(cmd, shell=True, check=False)  # noqa: S602
        if result.returncode != 0:
            console.print(f"[red]Install failed (exit {result.returncode}).[/red]")
            raise SystemExit(result.returncode)
        console.print("[green]\u2713[/green] Done.")


@tools_group.command(name="rules")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option(
    "--tool",
    "tool_key",
    default="",
    help="Show rules for a specific tool key (e.g. ghdl, ruff).",
)
@click.option(
    "--list",
    "list_all",
    is_flag=True,
    default=False,
    help="List all tools that have AI context rules.",
)
def tools_rules_cmd(project_dir: str, tool_key: str, list_all: bool) -> None:
    """Show the AI context rules injected into the agent system prompt.

    Without options, shows rules for the current project type (from scaffold.yml).
    Use --tool to show rules for a specific tool, or --list to see all available.
    """
    from specsmith.toolrules import TOOL_RULES, get_rules_for_project

    if list_all:
        console.print(f"[bold]Tool rules available[/bold] ({len(TOOL_RULES)} tools):\n")
        for key in sorted(TOOL_RULES):
            first_line = TOOL_RULES[key].strip().splitlines()[0].lstrip("# ").strip()
            console.print(f"  [teal]{key:<25s}[/teal]  {first_line}")
        console.print("\n  Use [bold]specsmith tools rules --tool <key>[/bold] to view full rules.")
        return

    if tool_key:
        if tool_key not in TOOL_RULES:
            matches = [k for k in TOOL_RULES if tool_key.lower() in k.lower()]
            if matches:
                console.print(
                    f"[yellow]No rules for '{tool_key}'. Similar: {', '.join(matches[:5])}[/yellow]"
                )
            else:
                console.print(f"[red]No rules for '{tool_key}'.[/red]")
            raise SystemExit(1)
        console.print(TOOL_RULES[tool_key])
        return

    # Project-level rules from scaffold.yml
    import yaml

    root = Path(project_dir).resolve()
    scaffold_path = root / "scaffold.yml"
    if not scaffold_path.exists():
        console.print(
            "[yellow]No scaffold.yml found. "
            "Run specsmith init or use --tool to view a specific tool.[/yellow]"
        )
        raise SystemExit(1)

    with open(scaffold_path) as f:
        raw = yaml.safe_load(f) or {}
    project_type = str(raw.get("type", "cli-python"))
    fpga_tools: list[str] = raw.get("fpga_tools", []) or []

    rules = get_rules_for_project(project_type, fpga_tools, max_chars=20000)
    if not rules:
        console.print(
            f"[yellow]No tool rules configured for project type '{project_type}'.[/yellow]"
        )
        return

    console.print(f"[bold]Tool rules for project type:[/bold] [teal]{project_type}[/teal]\n")
    console.print(rules)


main.add_command(tools_group)


# ---------------------------------------------------------------------------
# Wireframes — UI wireframe artifact management
# ---------------------------------------------------------------------------


@main.group(name="wireframes")
def wireframes_group() -> None:
    """Manage wireframe artifacts under docs/wireframes/."""


@wireframes_group.command(name="list")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def wireframes_list_cmd(project_dir: str) -> None:
    """List wireframe files and their requirement references."""
    from specsmith.wireframes import list_wireframes

    root = Path(project_dir).resolve()
    items = list_wireframes(root)
    if not items:
        console.print("[yellow]No wireframes found in docs/wireframes/.[/yellow]")
        console.print("  Create wireframe files there (SVG, PNG, PDF, etc.) and reference them")
        console.print("  from REQUIREMENTS.md via a `Wireframe` field in each requirement.")
        return
    console.print(f"[bold]Wireframes[/bold] ({len(items)})\n")
    for wf in items:
        refs_str = wf.get("refs", "")
        refs_note = f"  ← {refs_str}" if refs_str else "  [dim](unreferenced)[/dim]"
        console.print(f"  [cyan]{wf['id']:20s}[/cyan]  {wf['file']}{refs_note}")


@wireframes_group.command(name="check")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
def wireframes_check_cmd(project_dir: str) -> None:
    """Check for missing wireframe files referenced in REQUIREMENTS.md."""
    from specsmith.wireframes import check_wireframe_refs

    root = Path(project_dir).resolve()
    missing = check_wireframe_refs(root)
    if not missing:
        console.print("[bold green]✓ All wireframe references are valid.[/bold green]")
        return
    console.print(f"[bold red]{len(missing)} missing wireframe reference(s):[/bold red]\n")
    for m in missing:
        console.print(f"  [red]✗[/red] {m}")
    raise SystemExit(1)


main.add_command(wireframes_group)


# ---------------------------------------------------------------------------
# Index — opt-in local retrieval index (RAG foundation)
# ---------------------------------------------------------------------------


@main.group(name="index")
def index_group() -> None:
    """Manage the local retrieval index (explicit opt-in context retrieval).

    This builds a keyword-searchable index of project docs and source files
    stored at .specsmith/retrieval-index.json.  The agent tool `retrieve_context`
    queries this index — it is never searched automatically.
    """


@index_group.command(name="build")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option(
    "--include-ledger",
    is_flag=True,
    default=False,
    help="Also index LEDGER.md (often large — only useful for long-running projects).",
)
@click.option(
    "--external",
    default="",
    help="Path to an additional file or directory to include in the index.",
)
def index_build_cmd(project_dir: str, include_ledger: bool, external: str) -> None:
    """Build or refresh the local retrieval index.

    Indexes governance docs (AGENTS.md, REQUIREMENTS.md, ARCHITECTURE.md, TEST_SPEC.md)
    and source files under src/, client/, server/, and shared/.
    Use --external to add external reference material.
    """
    from specsmith.retrieval import build_index

    root = Path(project_dir).resolve()
    result = build_index(root, include_ledger=include_ledger, external=external)
    console.print(f"[green]✓[/green] {result}")
    console.print(
        "\n  Agent tool: [bold]retrieve_context[/bold] now available in this project.\n"
        "  Usage example: ask the agent 'search for requirements about authentication'."
    )


@index_group.command(name="search")
@click.argument("query")
@click.option("--project-dir", type=click.Path(exists=True), default=".")
@click.option("--limit", default=5, help="Maximum results to return (default: 5).")
def index_search_cmd(query: str, project_dir: str, limit: int) -> None:
    """Search the local retrieval index.

    QUERY: keyword search query

    The index must be built first with `specsmith index build`.
    """
    from specsmith.retrieval import search_index

    root = Path(project_dir).resolve()
    result = search_index(root, query, limit=limit)
    console.print(result)


main.add_command(index_group)


# ---------------------------------------------------------------------------
# AG2 Agent Shell
# ---------------------------------------------------------------------------

try:
    from specsmith.agents.cli import agent as agent_group

    main.add_command(agent_group)
except Exception:  # noqa: BLE001
    pass  # AG2 not installed — agent commands unavailable


if __name__ == "__main__":
    main()
