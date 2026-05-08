# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""CLI commands for the AI Provider & Model Intelligence system.

Adds these command groups to specsmith:
  specsmith providers  — manage AI provider registry
  specsmith profiles   — manage execution profiles
  specsmith datasources — manage USPTO data sources
  specsmith models     — model intelligence and scoring
"""

from __future__ import annotations

import json
import sys
from typing import Any

import click


# ---------------------------------------------------------------------------
# specsmith providers
# ---------------------------------------------------------------------------


@click.group("providers")
def providers_group() -> None:
    """Manage the AI provider registry."""


@providers_group.command("list")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON.")
@click.option("--enabled-only", is_flag=True, help="Show only enabled providers.")
def providers_list(as_json: bool, enabled_only: bool) -> None:
    """List all registered AI providers."""
    from specsmith.agent.provider_registry import ProviderRegistry

    reg = ProviderRegistry.load()
    entries = reg.enabled() if enabled_only else reg.providers
    if as_json:
        click.echo(json.dumps([e.to_public_dict() for e in entries], indent=2))
    else:
        if not entries:
            click.echo("No providers registered. Use 'specsmith providers add' to add one.")
            return
        for e in entries:
            status = {"reachable": "✓", "unreachable": "✗", "untested": "?"}.get(e.status, "?")
            models = len(e.available_models)
            click.echo(f"  {status} {e.id:<20} {e.provider_type:<8} {e.name:<25} {models} models")


@providers_group.command("add")
@click.argument("provider_id")
@click.option("--name", default="", help="Display name.")
@click.option("--type", "provider_type", default="byoe", help="Provider type (cloud/ollama/vllm/byoe/huggingface).")
@click.option("--cloud-id", default="", help="Cloud provider ID (openai/anthropic/etc).")
@click.option("--url", "base_url", default="", help="Base URL.")
@click.option("--key", "api_key", default="", help="API key.")
@click.option("--tag", "tags", multiple=True, help="Tags (repeatable).")
def providers_add(
    provider_id: str, name: str, provider_type: str, cloud_id: str,
    base_url: str, api_key: str, tags: tuple[str, ...],
) -> None:
    """Register a new AI provider."""
    from specsmith.agent.provider_registry import ProviderEntry, ProviderRegistry

    reg = ProviderRegistry.load()
    entry = ProviderEntry(
        id=provider_id,
        name=name or provider_id,
        provider_type=provider_type,
        provider_id=cloud_id or provider_id,
        base_url=base_url,
        api_key=api_key,
        tags=list(tags),
    )
    try:
        reg.add(entry)
        click.echo(f"Added provider: {provider_id}")
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@providers_group.command("test")
@click.argument("provider_id")
def providers_test(provider_id: str) -> None:
    """Test a provider's connection and list available models."""
    from specsmith.agent.provider_registry import ProviderRegistry

    reg = ProviderRegistry.load()
    try:
        result = reg.test(provider_id)
        if result["valid"]:
            click.echo(f"✓ {result['message']}")
            for m in result.get("models", [])[:20]:
                click.echo(f"  · {m}")
        else:
            click.echo(f"✗ {result['message']}")
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@providers_group.command("remove")
@click.argument("provider_id")
def providers_remove(provider_id: str) -> None:
    """Remove a provider from the registry."""
    from specsmith.agent.provider_registry import ProviderRegistry

    reg = ProviderRegistry.load()
    try:
        reg.remove(provider_id)
        click.echo(f"Removed: {provider_id}")
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# specsmith profiles (execution profiles)
# ---------------------------------------------------------------------------


@click.group("exec-profiles")
def profiles_group() -> None:
    """Manage execution profiles (provider constraints)."""


@profiles_group.command("list")
@click.option("--json-output", "as_json", is_flag=True)
def profiles_list(as_json: bool) -> None:
    """List all execution profiles."""
    from specsmith.agent.execution_profiles import ExecutionProfileStore

    store = ExecutionProfileStore.load()
    if as_json:
        click.echo(json.dumps([p.to_dict() for p in store.profiles], indent=2))
    else:
        for p in store.profiles:
            default = " (default)" if p.is_default else ""
            builtin = " [built-in]" if p.is_builtin else ""
            types = ", ".join(p.allowed_provider_types) if p.allowed_provider_types else "all"
            click.echo(f"  {'→' if p.is_default else ' '} {p.id:<15} {p.name:<20} types={types}{builtin}{default}")


@profiles_group.command("set-default")
@click.argument("profile_id")
def profiles_set_default(profile_id: str) -> None:
    """Set the default execution profile."""
    from specsmith.agent.execution_profiles import ExecutionProfileStore

    store = ExecutionProfileStore.load()
    try:
        store.set_default(profile_id)
        click.echo(f"Default profile set to: {profile_id}")
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# specsmith datasources
# ---------------------------------------------------------------------------


@click.group("datasources")
def datasources_group() -> None:
    """Manage built-in data sources (USPTO patent APIs)."""


@datasources_group.command("list")
def datasources_list() -> None:
    """List all available data sources."""
    from specsmith.datasources.citations import CitationsClient
    from specsmith.datasources.fpd import FPDClient
    from specsmith.datasources.odp import ODPClient
    from specsmith.datasources.patentsview import PatentsViewClient
    from specsmith.datasources.pfw import PFWClient
    from specsmith.datasources.ppubs import PPUBSClient
    from specsmith.datasources.ptab import PTABClient

    sources = [PatentsViewClient(), PPUBSClient(), ODPClient(), PFWClient(), CitationsClient(), FPDClient(), PTABClient()]
    for s in sources:
        click.echo(f"  {s.source_id:<15} {s.name}")


@datasources_group.command("test")
@click.argument("source_id", default="all")
def datasources_test(source_id: str) -> None:
    """Test connectivity to data sources."""
    from specsmith.datasources.citations import CitationsClient
    from specsmith.datasources.fpd import FPDClient
    from specsmith.datasources.odp import ODPClient
    from specsmith.datasources.patentsview import PatentsViewClient
    from specsmith.datasources.pfw import PFWClient
    from specsmith.datasources.ppubs import PPUBSClient
    from specsmith.datasources.ptab import PTABClient

    all_sources = {
        "patentsview": PatentsViewClient(),
        "ppubs": PPUBSClient(),
        "odp": ODPClient(),
        "pfw": PFWClient(),
        "citations": CitationsClient(),
        "fpd": FPDClient(),
        "ptab": PTABClient(),
    }

    targets = all_sources if source_id == "all" else {source_id: all_sources.get(source_id)}
    for sid, client in targets.items():
        if client is None:
            click.echo(f"  ? {sid:<15} unknown source")
            continue
        result = client.test_connection()
        icon = "✓" if result.get("available") else "✗"
        latency = f" ({result.get('latency_ms', 0)}ms)" if result.get("available") else ""
        click.echo(f"  {icon} {sid:<15} {result.get('message', '')}{latency}")


# ---------------------------------------------------------------------------
# specsmith models
# ---------------------------------------------------------------------------


@click.group("models")
def models_group() -> None:
    """Model intelligence — scores, rankings, auto-configure."""


@models_group.command("scores")
@click.option("--role", default="coder", help="Role to rank for.")
@click.option("--json-output", "as_json", is_flag=True)
def models_scores(role: str, as_json: bool) -> None:
    """Show model scores for a role."""
    from specsmith.agent.model_intelligence import BASELINE_SCORES, rank_models_for_role

    models = list(BASELINE_SCORES.keys())
    ranked = rank_models_for_role(role, models)

    if as_json:
        click.echo(json.dumps([{"model": m, "score": s} for m, s in ranked], indent=2))
    else:
        click.echo(f"Model scores for role '{role}':")
        for i, (model, score) in enumerate(ranked):
            star = "★" if i == 0 else " "
            click.echo(f"  {star} {score:5.1f}  {model}")


@models_group.command("rank")
@click.argument("role")
@click.option("--provider-type", default="", help="Filter by provider type.")
def models_rank(role: str, provider_type: str) -> None:
    """Rank available models for a specific role."""
    from specsmith.agent.model_intelligence import ModelScoreStore, rank_models_for_role
    from specsmith.agent.provider_registry import ProviderRegistry

    reg = ProviderRegistry.load()
    providers = reg.by_type(provider_type) if provider_type else reg.enabled()
    all_models: list[str] = []
    for p in providers:
        all_models.extend(p.available_models)
    if not all_models:
        click.echo("No models available. Run 'specsmith providers test <id>' to probe models.")
        return

    store = ModelScoreStore()
    ranked = store.rank_for_role(role, all_models)
    click.echo(f"Top models for '{role}':")
    for model, score in ranked[:10]:
        click.echo(f"  {score:5.1f}  {model}")
