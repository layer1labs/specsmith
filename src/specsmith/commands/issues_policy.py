from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from specsmith.approvals import APPROVAL_TYPES, record_approval
from specsmith.dashboard import build_dashboard
from specsmith.governed_pr import evaluate_governed_pr, render_governance_comment
from specsmith.plugins import discover_manifest_plugins, discover_plugins, validate_plugin_manifest
from specsmith.policy import load_policy, simulate_policy_for_work_item
from specsmith.recover import recover_state
from specsmith.transcripts import import_transcript_json
from specsmith.wi_store import WorkItemStore


def register_issue_policy_commands(main: click.Group, console: Any) -> None:
    @main.group(name="governed-pr")
    def governed_pr_group() -> None:
        """Governed PR checks and comment helpers."""

    @governed_pr_group.command(name="check")
    @click.option("--project-dir", type=click.Path(exists=True), default=".")
    @click.option("--work-item", "work_item_id", default="")
    @click.option("--required-check", is_flag=True, default=False)
    @click.option("--comment-output", type=click.Path(), default="")
    @click.option("--json", "as_json", is_flag=True, default=False)
    def governed_pr_check(
        project_dir: str,
        work_item_id: str,
        required_check: bool,
        comment_output: str,
        as_json: bool,
    ) -> None:
        root = Path(project_dir).resolve()
        status = evaluate_governed_pr(root, work_item_id=work_item_id)
        comment = render_governance_comment(status)
        if comment_output:
            Path(comment_output).write_text(comment, encoding="utf-8")
        if as_json:
            click.echo(json.dumps(status, indent=2))
        else:
            console.print(comment)
        if required_check and status.get("governance_gaps"):
            raise SystemExit(1)

    @main.group(name="transcript")
    def transcript_group() -> None:
        """Transcript normalization and import."""

    @transcript_group.command(name="import")
    @click.option("--from", "from_path", type=click.Path(exists=True), required=True)
    @click.option("--format", "fmt", type=click.Choice(["json"]), default="json")
    @click.option("--work-item", "work_item_id", default="")
    @click.option("--project-dir", type=click.Path(exists=True), default=".")
    @click.option("--json", "as_json", is_flag=True, default=False)
    def transcript_import_cmd(
        from_path: str,
        fmt: str,
        work_item_id: str,
        project_dir: str,
        as_json: bool,
    ) -> None:
        _ = fmt
        root = Path(project_dir).resolve()
        wi_id = work_item_id.strip()
        if not wi_id:
            open_items = [
                i for i in WorkItemStore(root).load() if i.status in {"open", "implemented"}
            ]
            wi_id = open_items[0].id if open_items else "WI-UNSCOPED"
        actions = import_transcript_json(root, Path(from_path), wi_id)
        payload = {"imported": len(actions), "work_item_id": wi_id}
        if as_json:
            click.echo(json.dumps(payload, indent=2))
        else:
            console.print(
                f"[green]✓[/green] Imported {len(actions)} transcript actions for {wi_id}",
            )

    @main.command(name="approve")
    @click.argument("approval_type", type=click.Choice(list(APPROVAL_TYPES)))
    @click.option("--work-item", "work_item_id", required=True)
    @click.option("--rationale", required=True)
    @click.option("--scope", default="")
    @click.option("--requirement", "requirements", multiple=True)
    @click.option("--project-dir", type=click.Path(exists=True), default=".")
    @click.option("--json", "as_json", is_flag=True, default=False)
    def approve_cmd(
        approval_type: str,
        work_item_id: str,
        rationale: str,
        scope: str,
        requirements: tuple[str, ...],
        project_dir: str,
        as_json: bool,
    ) -> None:
        from specsmith.wi_store import _now_iso

        record = record_approval(
            Path(project_dir).resolve(),
            approval_type=approval_type,
            work_item_id=work_item_id,
            rationale=rationale,
            scope=scope,
            requirement_ids=list(requirements),
        )
        # Update human_review_status to 'approved' (REQ-434)
        try:
            store = WorkItemStore(Path(project_dir).resolve())
            item = store.get(work_item_id)
            if item is not None:
                item.human_review_status = "approved"
                item.updated_at = _now_iso()
                store.upsert(item)
        except Exception:  # noqa: BLE001
            pass
        if as_json:
            click.echo(json.dumps(record.to_dict(), indent=2))
        else:
            console.print(f"[green]✓[/green] Recorded {approval_type} approval for {work_item_id}")

    @main.group(name="policy")
    def policy_group() -> None:
        """Governance policy management and simulation."""

    @policy_group.command(name="validate")
    @click.option("--project-dir", type=click.Path(exists=True), default=".")
    @click.option("--json", "as_json", is_flag=True, default=False)
    def policy_validate_cmd(project_dir: str, as_json: bool) -> None:
        policy, errors = load_policy(Path(project_dir).resolve())
        payload = {
            "valid": len(errors) == 0,
            "errors": errors,
            "risk_threshold": policy.risk_threshold,
        }
        if as_json:
            click.echo(json.dumps(payload, indent=2))
        elif errors:
            for err in errors:
                console.print(f"[red]✗[/red] {err}")
        else:
            console.print("[green]✓[/green] policy.yml is valid")
        if errors:
            raise SystemExit(1)

    @policy_group.command(name="simulate")
    @click.option("--project-dir", type=click.Path(exists=True), default=".")
    @click.option("--work-item", "work_item_id", default="")
    @click.option("--json", "as_json", is_flag=True, default=False)
    def policy_simulate_cmd(project_dir: str, work_item_id: str, as_json: bool) -> None:
        root = Path(project_dir).resolve()
        store = WorkItemStore(root)
        item = store.get(work_item_id) if work_item_id else None
        if item is None:
            open_items = [i for i in store.load() if i.status in {"open", "implemented"}]
            item = open_items[0] if open_items else None
        if item is None:
            console.print("[red]No work item available for simulation.[/red]")
            raise SystemExit(1)
        diff_text = click.get_text_stream("stdin").read().strip()
        result = simulate_policy_for_work_item(root, item, diff_text=diff_text)
        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            console.print(
                f"Policy simulation for [bold]{result['work_item_id']}[/bold] "
                f"(risk={result['risk_level']})",
            )
            for issue in result["blocking_issues"]:
                console.print(f"  [red]✗[/red] {issue}")
            if not result["blocking_issues"]:
                console.print("  [green]✓[/green] No blocking issues")

    if "plugin" in main.commands:
        del main.commands["plugin"]

    @main.group(name="plugin", invoke_without_command=True)
    @click.pass_context
    def plugin_group(ctx: click.Context) -> None:
        """List or validate plugin manifests."""
        if ctx.invoked_subcommand is None:
            ctx.invoke(plugin_list_cmd)

    @plugin_group.command(name="list")
    @click.option("--project-dir", type=click.Path(exists=True), default=".")
    def plugin_list_cmd(project_dir: str) -> None:
        entry_plugins = discover_plugins()
        manifest_plugins = discover_manifest_plugins(Path(project_dir).resolve())
        if not entry_plugins and not manifest_plugins:
            console.print("No plugins installed.")
            return
        for p in entry_plugins:
            icon = "[green]✓[/green]" if p.loaded else "[red]✗[/red]"
            note = "" if p.loaded else f" — {p.error}"
            console.print(f"  {icon} {p.group}/{p.name} ({p.module}){note}")
        for path, manifest, errors in manifest_plugins:
            icon = "[green]✓[/green]" if not errors else "[red]✗[/red]"
            console.print(
                f"  {icon} manifest {manifest.name} ({manifest.plugin_type}) at {path}"
                + (f" — {errors[0]}" if errors else ""),
            )

    @plugin_group.command(name="validate")
    @click.argument("manifest_path", type=click.Path(exists=True))
    @click.option("--json", "as_json", is_flag=True, default=False)
    def plugin_validate_cmd(manifest_path: str, as_json: bool) -> None:
        errors = validate_plugin_manifest(manifest_path)
        payload = {"valid": len(errors) == 0, "errors": errors, "path": manifest_path}
        if as_json:
            click.echo(json.dumps(payload, indent=2))
        elif errors:
            for err in errors:
                console.print(f"[red]✗[/red] {err}")
        else:
            console.print(f"[green]✓[/green] {manifest_path} is valid")
        if errors:
            raise SystemExit(1)

    @main.command(name="recover")
    @click.option("--project-dir", type=click.Path(exists=True), default=".")
    @click.option("--work-item", "work_item_id", default="")
    @click.option("--git-diff", is_flag=True, default=False)
    @click.option("--test-results", "test_results", type=click.Path(exists=True), default="")
    @click.option("--json", "as_json", is_flag=True, default=False)
    def recover_cmd(
        project_dir: str,
        work_item_id: str,
        git_diff: bool,
        test_results: str,
        as_json: bool,
    ) -> None:
        root = Path(project_dir).resolve()
        diff_text = click.get_text_stream("stdin").read() if git_diff else ""
        summary = recover_state(
            root,
            work_item_id=work_item_id,
            git_diff=diff_text,
            test_results_path=Path(test_results) if test_results else None,
        )
        if as_json:
            click.echo(json.dumps(summary, indent=2))
        else:
            console.print(f"Work item: {summary['work_item_id'] or 'none'}")
            console.print(f"Failed step: {summary['failed_step']}")
            console.print(f"Recommended action: {summary['recommended_action']}")

    @main.group(name="dashboard")
    def dashboard_group() -> None:
        """Governance dashboard operations."""

    @dashboard_group.command(name="build")
    @click.option("--project-dir", type=click.Path(exists=True), default=".")
    @click.option("--out", "out_dir", type=click.Path(), required=True)
    def dashboard_build_cmd(project_dir: str, out_dir: str) -> None:
        target = build_dashboard(Path(project_dir).resolve(), Path(out_dir))
        console.print(f"[green]✓[/green] Dashboard built: {target}")
