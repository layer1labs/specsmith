# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Updater — version check, self-update, and project migration."""

from __future__ import annotations

import subprocess
from pathlib import Path

from specsmith import __version__


def get_update_channel() -> str:
    """Determine update channel from installed version.

    Returns 'dev' if current version has .dev suffix, else 'stable'.
    """
    return "dev" if ".dev" in __version__ else "stable"


def check_latest_version(
    *, channel: str = "",
) -> tuple[str, str, str]:
    """Check PyPI for the latest specsmith version.

    Returns (current_version, latest_version, channel).
    Channel is auto-detected from installed version if not specified.
    """
    if not channel:
        channel = get_update_channel()

    latest = ""
    try:
        import json
        import urllib.request

        url = "https://pypi.org/pypi/specsmith/json"
        resp = urllib.request.urlopen(url, timeout=10)  # noqa: S310
        data = json.loads(resp.read())

        if channel == "dev":
            # Find highest version including pre-releases
            all_versions = sorted(data["releases"].keys())
            if all_versions:
                latest = all_versions[-1]
        else:
            # Stable: use the default (non-pre) version
            latest = data["info"]["version"]
    except Exception:  # noqa: BLE001
        pass
    return __version__, latest, channel


def is_outdated() -> bool:
    """Check if current specsmith is outdated."""
    current, latest, _channel = check_latest_version()
    if not latest:
        return False
    return current != latest


def run_self_update(*, channel: str = "") -> tuple[bool, str]:
    """Update specsmith via pip.

    Uses --pre flag for dev channel.
    """
    if not channel:
        channel = get_update_channel()

    cmd = ["pip", "install", "--upgrade", "specsmith"]
    if channel == "dev":
        cmd.insert(2, "--pre")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, result.stderr.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, str(e)


def check_project_version(root: Path) -> tuple[str, str]:
    """Compare scaffold.yml spec_version to installed version.

    Returns (project_version, installed_version).
    """
    import yaml

    scaffold_path = root / "scaffold.yml"
    if not scaffold_path.exists():
        return "", __version__

    with open(scaffold_path) as f:
        raw = yaml.safe_load(f) or {}

    return raw.get("spec_version", ""), __version__


def needs_migration(root: Path) -> bool:
    """Check if the project needs migration to current specsmith version."""
    project_ver, installed_ver = check_project_version(root)
    if not project_ver:
        return False
    return project_ver != installed_ver


def run_migration(root: Path, *, dry_run: bool = False) -> list[str]:
    """Migrate a project to the current specsmith version.

    Returns list of actions taken (or that would be taken for dry_run).
    """
    import yaml

    from specsmith.ledger import add_entry

    scaffold_path = root / "scaffold.yml"
    if not scaffold_path.exists():
        return ["No scaffold.yml found — nothing to migrate"]

    with open(scaffold_path) as f:
        raw = yaml.safe_load(f) or {}

    old_version = raw.get("spec_version", "unknown")
    actions: list[str] = []

    if old_version == __version__:
        return [f"Already at version {__version__}"]

    actions.append(f"Migrate spec_version: {old_version} → {__version__}")

    # Update scaffold.yml version
    if not dry_run:
        raw["spec_version"] = __version__
        with open(scaffold_path, "w") as f:
            yaml.dump(raw, f, default_flow_style=False, sort_keys=False)
    actions.append("Updated scaffold.yml")

    # Regenerate governance templates
    from specsmith.config import ProjectConfig
    from specsmith.upgrader import run_upgrade

    try:
        ProjectConfig(**raw)  # Validate config
        if not dry_run:
            result = run_upgrade(root, target_version=__version__)
            for updated_file in result.updated_files:
                actions.append(f"Regenerated {updated_file}")
        else:
            actions.append("Would regenerate governance templates")
    except Exception:  # noqa: BLE001
        actions.append("Could not regenerate templates (config error)")

    # Ledger entry
    if not dry_run:
        add_entry(
            root,
            description=f"specsmith migration: {old_version} → {__version__}",
            entry_type="migration",
            author="specsmith",
        )
        actions.append("Added migration entry to LEDGER.md")

    return actions
