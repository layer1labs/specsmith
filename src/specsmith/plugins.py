# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Plugin system — discover and register custom project types and tools."""

from __future__ import annotations

import sys
from dataclasses import dataclass

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
