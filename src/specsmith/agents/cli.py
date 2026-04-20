# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""CLI commands for the AG2 agent shell.

Wired into the main specsmith CLI as the ``agent`` command group.
"""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

console = Console()


@click.group()
def agent() -> None:
    """AG2 agent shell — Planner/Builder/Verifier over Ollama."""


@agent.command()
@click.argument("task")
@click.option("--project-dir", default=".", help="Project root directory.")
@click.option("--max-turns", default=6, help="Maximum conversation turns per agent.")
def run(task: str, project_dir: str, max_turns: int) -> None:
    """Execute a task through the full Planner → Builder → Verifier pipeline."""
    try:
        from autogen import ConversableAgent  # noqa: F401 — verify AG2 is installed
    except ImportError:
        console.print("[red]AG2 is not installed.[/red] Run: pip install ag2[ollama]")
        raise SystemExit(1)  # noqa: B904

    from specsmith.agents.config import load_agent_config
    from specsmith.agents.roles import create_builder, create_planner, create_verifier

    project_dir = str(Path(project_dir).resolve())
    config = load_agent_config(project_dir)

    console.print(
        f"\n[bold cyan]specsmith agent shell[/bold cyan] — {config.primary_model} via Ollama"
    )
    console.print(f"Task: [bold]{task}[/bold]\n")

    # Phase 1: Plan
    console.print("[dim]─── Phase 1: Planning ───[/dim]")
    planner = create_planner(config, project_dir)
    plan_result = planner.run(message=f"Plan this task:\n{task}", max_turns=max_turns)
    plan_result.process()

    plan_text = ""
    for msg in plan_result.messages:
        if msg.get("role") == "assistant" and msg.get("content"):
            plan_text = msg["content"]

    if not plan_text:
        console.print("[yellow]Planner produced no output.[/yellow]")
        return

    # Phase 2: Build
    console.print("\n[dim]─── Phase 2: Building ───[/dim]")
    builder = create_builder(config, project_dir)
    build_result = builder.run(
        message=f"Execute this plan:\n\n{plan_text}",
        max_turns=max_turns,
    )
    build_result.process()

    build_text = ""
    for msg in build_result.messages:
        if msg.get("role") == "assistant" and msg.get("content"):
            build_text = msg["content"]

    # Phase 3: Verify
    console.print("\n[dim]─── Phase 3: Verifying ───[/dim]")
    verifier = create_verifier(config, project_dir)
    verify_result = verifier.run(
        message=(
            f"Verify the following changes:\n\n{build_text}"
            "\n\nRun the relevant tests and report ACCEPT or REJECT."
        ),
        max_turns=max_turns,
    )
    verify_result.process()

    # Summary
    console.print("\n[bold cyan]─── Done ───[/bold cyan]")
    for msg in verify_result.messages:
        if msg.get("role") == "assistant" and msg.get("content"):
            content = msg["content"]
            if "ACCEPT" in content.upper():
                console.print("[bold green]✓ ACCEPTED[/bold green]")
            elif "REJECT" in content.upper():
                console.print("[bold red]✗ REJECTED[/bold red]")
            break


@agent.command()
@click.argument("task")
@click.option("--project-dir", default=".", help="Project root directory.")
@click.option("--max-turns", default=6, help="Maximum conversation turns.")
def plan(task: str, project_dir: str, max_turns: int) -> None:
    """Generate a plan without executing it."""
    try:
        from autogen import ConversableAgent  # noqa: F401
    except ImportError:
        console.print("[red]AG2 is not installed.[/red] Run: pip install ag2[ollama]")
        raise SystemExit(1)  # noqa: B904

    from specsmith.agents.config import load_agent_config
    from specsmith.agents.roles import create_planner

    project_dir = str(Path(project_dir).resolve())
    config = load_agent_config(project_dir)

    console.print(f"\n[bold cyan]specsmith agent plan[/bold cyan] — {config.primary_model}")
    planner = create_planner(config, project_dir)
    result = planner.run(message=f"Plan this task:\n{task}", max_turns=max_turns)
    result.process()


@agent.command()
@click.option("--project-dir", default=".", help="Project root directory.")
def status(project_dir: str) -> None:
    """Show agent configuration and Ollama status."""
    from specsmith.agents.config import load_agent_config

    config = load_agent_config(project_dir)
    console.print("[bold]Agent Configuration[/bold]")
    console.print(f"  Primary model:  {config.primary_model}")
    console.print(f"  Utility model:  {config.utility_model}")
    console.print(f"  Ollama URL:     {config.ollama_base_url}")
    console.print(f"  Max iterations: {config.max_iterations}")
    console.print(f"  Context length: {config.num_ctx}")
    console.print(f"  Tools enabled:  {', '.join(config.tools_enabled)}")

    # Check Ollama
    try:
        from specsmith.agent.providers.ollama import OllamaProvider

        p = OllamaProvider(base_url=config.ollama_base_url)
        if p.is_available():
            console.print("  Ollama:         [green]running[/green]")
        else:
            console.print("  Ollama:         [red]not available[/red]")
    except Exception:  # noqa: BLE001
        console.print("  Ollama:         [yellow]unknown[/yellow]")


@agent.command()
@click.option("--project-dir", default=".", help="Project root directory.")
@click.option("--max-turns", default=4, help="Maximum conversation turns.")
def verify(project_dir: str, max_turns: int) -> None:
    """Run the Verifier agent on the current project state."""
    try:
        from autogen import ConversableAgent  # noqa: F401
    except ImportError:
        console.print("[red]AG2 is not installed.[/red] Run: pip install ag2[ollama]")
        raise SystemExit(1)  # noqa: B904

    from specsmith.agents.config import load_agent_config
    from specsmith.agents.roles import create_verifier

    project_dir = str(Path(project_dir).resolve())
    config = load_agent_config(project_dir)

    console.print(f"\n[bold cyan]specsmith agent verify[/bold cyan] — {config.utility_model}")
    verifier = create_verifier(config, project_dir)
    result = verifier.run(
        message=(
            "Run the full test suite and report the current project health."
            " Report ACCEPT or REJECT."
        ),
        max_turns=max_turns,
    )
    result.process()


@agent.command()
@click.argument("task")
@click.option("--project-dir", default=".", help="Project root directory.")
@click.option("--max-turns", default=6, help="Maximum conversation turns.")
def improve(task: str, project_dir: str, max_turns: int) -> None:
    """Run the self-improvement workflow (Plan → Build → Verify → Report)."""
    try:
        from autogen import ConversableAgent  # noqa: F401
    except ImportError:
        console.print("[red]AG2 is not installed.[/red] Run: pip install ag2[ollama]")
        raise SystemExit(1)  # noqa: B904

    from specsmith.agents.workflows.improve import run_improvement

    project_dir = str(Path(project_dir).resolve())
    console.print("\n[bold cyan]specsmith agent improve[/bold cyan]")
    console.print(f"Task: [bold]{task}[/bold]\n")

    report = run_improvement(task, project_dir, max_turns=max_turns)

    console.print(f"\n[bold]Report:[/bold] {report.summary}")
    if report.verdict == "ACCEPT":
        console.print("[bold green]✓ ACCEPTED[/bold green]")
    elif report.verdict == "REJECT":
        console.print("[bold red]✗ REJECTED[/bold red]")
    else:
        console.print(f"[yellow]Verdict: {report.verdict}[/yellow]")

    if report.follow_up_tasks:
        console.print("\n[bold]Follow-up tasks:[/bold]")
        for ft in report.follow_up_tasks:
            console.print(f"  - {ft}")

    console.print(f"\n[dim]Report saved to .specsmith/agent-reports/{report.task_id}.json[/dim]")


@agent.command()
@click.option("--project-dir", default=".", help="Project root directory.")
def reports(project_dir: str) -> None:
    """List recent improvement reports."""
    from specsmith.agents.reports import list_reports

    all_reports = list_reports(project_dir)
    if not all_reports:
        console.print("[yellow]No improvement reports found.[/yellow]")
        return

    for r in all_reports[:10]:
        icon = {
            "accepted": "[green]✓[/green]",
            "rejected": "[red]✗[/red]",
            "failed": "[red]![/red]",
        }.get(r.status, "[yellow]?[/yellow]")
        console.print(f"  {icon} {r.task_id} — {r.summary}")
