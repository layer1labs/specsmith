# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Plugin system — discover entry-point and manifest-defined plugins."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from specsmith import __version__

if sys.version_info >= (3, 12):
    from importlib.metadata import entry_points
else:
    from importlib.metadata import entry_points


@dataclass
class PluginInfo:
    """Metadata about a discovered plugin."""

    name: str
    group: str
    module: str
    loaded: bool = False
    error: str = ""


PLUGIN_TYPES = (
    "verifier",
    "requirement_importer",
    "test_linker",
    "compliance_mapper",
    "agent_adapter",
    "policy_rule",
    "exporter",
)


@dataclass
class PluginManifest:
    name: str
    version: str
    plugin_type: str
    entrypoint: str
    specsmith_version: str = ""
    description: str = ""


def _parse_version(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for token in version.split("."):
        try:
            parts.append(int(token))
        except ValueError:
            break
    return tuple(parts or [0])


def is_version_compatible(required: str, current: str) -> bool:
    if not required:
        return True
    return _parse_version(current) >= _parse_version(required)


def load_plugin_manifest(path: str | Path) -> PluginManifest:
    manifest_path = Path(path)
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        msg = "manifest must be a mapping"
        raise ValueError(msg)
    missing = [key for key in ("name", "version", "plugin_type", "entrypoint") if key not in raw]
    if missing:
        msg = f"manifest missing required keys: {', '.join(missing)}"
        raise ValueError(msg)
    plugin_type = str(raw["plugin_type"])
    if plugin_type not in PLUGIN_TYPES:
        msg = f"plugin_type must be one of {PLUGIN_TYPES}"
        raise ValueError(msg)
    return PluginManifest(
        name=str(raw["name"]),
        version=str(raw["version"]),
        plugin_type=plugin_type,
        entrypoint=str(raw["entrypoint"]),
        specsmith_version=str(raw.get("specsmith_version", "")),
        description=str(raw.get("description", "")),
    )


def validate_plugin_manifest(path: str | Path) -> list[str]:
    errors: list[str] = []
    try:
        manifest = load_plugin_manifest(path)
    except Exception as exc:  # noqa: BLE001
        return [str(exc)]
    if not is_version_compatible(manifest.specsmith_version, __version__):
        errors.append(
            "specsmith version "
            f"{__version__} does not satisfy plugin requirement "
            f"{manifest.specsmith_version}",
        )
    if ":" not in manifest.entrypoint:
        errors.append("entrypoint must use module:function syntax")
    return errors


def discover_manifest_plugins(root: Path) -> list[tuple[Path, PluginManifest, list[str]]]:
    results: list[tuple[Path, PluginManifest, list[str]]] = []
    for manifest_path in root.rglob("specsmith.plugin.yml"):
        try:
            manifest = load_plugin_manifest(manifest_path)
            errors = validate_plugin_manifest(manifest_path)
            results.append((manifest_path, manifest, errors))
        except Exception as exc:  # noqa: BLE001
            fake = PluginManifest(
                name=manifest_path.parent.name,
                version="",
                plugin_type="exporter",
                entrypoint="",
            )
            results.append((manifest_path, fake, [str(exc)]))
    return results


def discover_plugins() -> list[PluginInfo]:
    """Discover specsmith plugins via entry points.

    Plugins register via pyproject.toml:
        [project.entry-points."specsmith.types"]
        my-type = "my_plugin:register_type"

        [project.entry-points."specsmith.tools"]
        my-type = "my_plugin:register_tools"
    """
    plugins: list[PluginInfo] = []

    for group in ("specsmith.types", "specsmith.tools", "specsmith.templates"):
        eps = entry_points(group=group)
        for ep in eps:
            info = PluginInfo(
                name=ep.name,
                group=group,
                module=f"{ep.value}",
            )
            try:
                ep.load()
                info.loaded = True
            except Exception as e:  # noqa: BLE001
                info.error = str(e)
            plugins.append(info)

    return plugins


def load_type_plugins() -> dict[str, object]:
    """Load and return all custom type plugins."""
    loaded: dict[str, object] = {}
    eps = entry_points(group="specsmith.types")
    for ep in eps:
        try:
            loaded[ep.name] = ep.load()
        except Exception:  # noqa: BLE001
            continue
    return loaded


def load_tool_plugins() -> dict[str, object]:
    """Load and return all custom tool plugins."""
    loaded: dict[str, object] = {}
    eps = entry_points(group="specsmith.tools")
    for ep in eps:
        try:
            loaded[ep.name] = ep.load()
        except Exception:  # noqa: BLE001
            continue
    return loaded
