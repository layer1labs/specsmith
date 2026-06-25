# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Updater — version check, self-update, and project migration."""

from __future__ import annotations

import subprocess
from pathlib import Path

from specsmith import __version__


def get_update_channel() -> str:
    """Return the effective update channel (persistent preference or version inference).

    Delegates to :func:`specsmith.channel.effective_channel` so that a user's
    ``specsmith channel set`` preference is respected.
    """
    from specsmith.channel import effective_channel

    return effective_channel()


def check_latest_version(
    *,
    channel: str = "",
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


def is_pipx_install() -> bool:
    """Return True if specsmith was installed via pipx.

    Checks sys.executable path against known pipx venv locations and the
    PIPX_HOME / PIPX_LOCAL_VENVS env vars.  Robust on Windows where pipx
    stores venvs in ``~/pipx/venvs/`` without setting PIPX_HOME.
    """
    import os
    import sys
    from pathlib import Path

    exe = sys.executable.replace("\\", "/").lower()

    # 1. Executable path contains 'pipx' (catches most OS defaults)
    if "pipx" in exe:
        return True

    # 2. Explicit pipx env vars (set by some CI / pipx versions)
    if os.environ.get("PIPX_HOME") or os.environ.get("PIPX_LOCAL_VENVS"):
        return True

    # 3. Windows default: ~/pipx/venvs/<pkg>/Scripts/python.exe
    win_pipx = (Path.home() / "pipx" / "venvs").as_posix().lower()
    if exe.startswith(win_pipx):
        return True

    # 4. Linux/macOS default: ~/.local/pipx/venvs/<pkg>/bin/python
    unix_pipx = (Path.home() / ".local" / "pipx" / "venvs").as_posix().lower()
    return bool(exe.startswith(unix_pipx))


def run_self_update(
    *,
    channel: str = "",
    target_version: str = "",
) -> tuple[bool, str]:
    """Update specsmith.

    Detects whether running under pipx and uses the appropriate command:
      - pipx: ``pipx upgrade specsmith`` (or ``pipx install specsmith==X.Y.Z``)
      - pip: ``pip install --upgrade specsmith``

    If target_version is set, installs that exact version.
    Otherwise uses --pre flag for dev channel, plain upgrade for stable.
    """
    if is_pipx_install():
        if target_version:
            cmd = ["pipx", "install", f"specsmith=={target_version}", "--force"]
        else:
            cmd = ["pipx", "upgrade", "specsmith"]
    else:
        if target_version:
            cmd = ["pip", "install", f"specsmith=={target_version}"]
        else:
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
    """Compare scaffold config spec_version to installed version.

    Checks ``docs/SPECSMITH.yml`` (canonical) then ``scaffold.yml`` (legacy).
    Returns (project_version, installed_version).
    """
    import yaml

    from specsmith.paths import find_scaffold

    scaffold_path = find_scaffold(root)
    if scaffold_path is None:
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

    Checks ``docs/SPECSMITH.yml`` (canonical) then ``scaffold.yml`` (legacy).
    Returns list of actions taken (or that would be taken for dry_run).
    """
    import yaml

    from specsmith.ledger import add_entry
    from specsmith.paths import find_scaffold

    scaffold_path = find_scaffold(root)
    if scaffold_path is None:
        return [
            "No scaffold config found (docs/SPECSMITH.yml or scaffold.yml) — nothing to migrate"
        ]

    with open(scaffold_path) as f:
        raw = yaml.safe_load(f) or {}

    old_version = raw.get("spec_version", "unknown")
    actions: list[str] = []

    if old_version == __version__:
        return [f"Already at version {__version__}"]

    # Reject backward migration (downgrade) unconditionally — REQ-370 / I16.
    def _ver(v: str) -> tuple[int, ...]:
        import re

        m = re.match(r"(\d+)[.](\d+)(?:[.](\d+))?", v or "")
        if not m:
            return (0,)
        return tuple(int(x) for x in m.groups() if x is not None)

    if old_version != "unknown" and _ver(__version__) < _ver(old_version):
        return [
            f"ERROR: Backward migration is not supported. "
            f"Project spec_version is {old_version!r} but installed specsmith is "
            f"{__version__!r} (older). Upgrade specsmith first: pipx upgrade specsmith"
        ]

    actions.append(f"Migrate spec_version: {old_version} → {__version__}")

    # Update scaffold.yml version
    if not dry_run:
        raw["spec_version"] = __version__
        with open(scaffold_path, "w") as f:
            yaml.dump(raw, f, default_flow_style=False, sort_keys=False)
    actions.append(f"Updated {scaffold_path.name}")

    # Regenerate governance templates
    from specsmith.config import ProjectConfig, _normalize_scaffold_raw
    from specsmith.upgrader import run_upgrade

    try:
        ProjectConfig(**_normalize_scaffold_raw(raw))  # Validate config
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
