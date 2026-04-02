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
def diff(project_dir: str) -> None:
    """Compare governance files against spec templates."""
    from specsmith.differ import run_diff

    root = Path(project_dir).resolve()
    results = run_diff(root)

    if not results:
        console.print("[bold green]All governance files match templates.[/bold green]")
        return

    for name, status in results:
        if status == "match":
            console.print(f"  [green]✓[/green] {name}")
        elif status == "missing":
            console.print(f"  [red]✗[/red] {name} — missing")
        else:
            console.print(f"  [yellow]~[/yellow] {name} — differs from template")


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


if __name__ == "__main__":
    main()
