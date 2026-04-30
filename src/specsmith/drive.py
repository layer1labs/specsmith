# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Specsmith Drive (REQ-133) — sync rules/workflows/notebooks across machines.

Backend agnostic: the default backend is a local filesystem mirror under
``~/.specsmith/drive/`` which the user can ``git push`` themselves. An
HTTP backend is documented but not bundled (see ``examples/drive_http_server.py``
once it exists).

Supported artifact kinds:
* ``rules`` — files under ``docs/governance/*_RULES.md``
* ``workflows`` — files under ``.specsmith/workflows/*.yml``
* ``notebooks`` — files under ``docs/notebooks/*.md``

Each project's artifacts go into ``<drive>/<project_name>/<kind>/<file>``.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

KINDS = ("rules", "workflows", "notebooks")


def default_drive_dir() -> Path:
    return Path.home() / ".specsmith" / "drive"


def _kind_sources(project_dir: Path) -> dict[str, list[Path]]:
    return {
        "rules": sorted((project_dir / "docs" / "governance").glob("*_RULES.md"))
        if (project_dir / "docs" / "governance").is_dir()
        else [],
        "workflows": sorted((project_dir / ".specsmith" / "workflows").glob("*.yml"))
        if (project_dir / ".specsmith" / "workflows").is_dir()
        else [],
        "notebooks": sorted((project_dir / "docs" / "notebooks").glob("*.md"))
        if (project_dir / "docs" / "notebooks").is_dir()
        else [],
    }


def _kind_dest(drive_dir: Path, project_name: str, kind: str) -> Path:
    return drive_dir / project_name / kind


@dataclass
class DriveResult:
    pushed: list[str]
    pulled: list[str]
    skipped: list[str]
    errors: list[str]


def push(project_dir: Path, drive_dir: Path | None = None) -> DriveResult:
    """Mirror project artifacts into the drive directory."""
    drive_dir = drive_dir or default_drive_dir()
    project_name = project_dir.name
    pushed: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []
    for kind, files in _kind_sources(project_dir).items():
        dest = _kind_dest(drive_dir, project_name, kind)
        dest.mkdir(parents=True, exist_ok=True)
        for src in files:
            try:
                shutil.copy2(src, dest / src.name)
                pushed.append(f"{kind}/{src.name}")
            except OSError as exc:
                errors.append(f"{kind}/{src.name}: {exc}")
        if not files:
            skipped.append(f"{kind} (no source files)")
    return DriveResult(pushed=pushed, pulled=[], skipped=skipped, errors=errors)


def pull(project_dir: Path, drive_dir: Path | None = None) -> DriveResult:
    """Mirror drive artifacts back into the project."""
    drive_dir = drive_dir or default_drive_dir()
    project_name = project_dir.name
    pulled: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []
    project_targets = {
        "rules": project_dir / "docs" / "governance",
        "workflows": project_dir / ".specsmith" / "workflows",
        "notebooks": project_dir / "docs" / "notebooks",
    }
    for kind, target in project_targets.items():
        src_dir = _kind_dest(drive_dir, project_name, kind)
        if not src_dir.is_dir():
            skipped.append(f"{kind} (no drive entry)")
            continue
        target.mkdir(parents=True, exist_ok=True)
        for src in sorted(src_dir.iterdir()):
            if not src.is_file():
                continue
            try:
                shutil.copy2(src, target / src.name)
                pulled.append(f"{kind}/{src.name}")
            except OSError as exc:
                errors.append(f"{kind}/{src.name}: {exc}")
    return DriveResult(pushed=[], pulled=pulled, skipped=skipped, errors=errors)


def listing(drive_dir: Path | None = None) -> dict[str, dict[str, list[str]]]:
    """Return ``{project: {kind: [filenames]}}`` for everything in the drive."""
    drive_dir = drive_dir or default_drive_dir()
    out: dict[str, dict[str, list[str]]] = {}
    if not drive_dir.is_dir():
        return out
    for project_path in sorted(drive_dir.iterdir()):
        if not project_path.is_dir():
            continue
        kinds: dict[str, list[str]] = {}
        for kind in KINDS:
            d = project_path / kind
            if d.is_dir():
                kinds[kind] = sorted(p.name for p in d.iterdir() if p.is_file())
        if kinds:
            out[project_path.name] = kinds
    return out


__all__ = ["DriveResult", "KINDS", "default_drive_dir", "listing", "pull", "push"]
