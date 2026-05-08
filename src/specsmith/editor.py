# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Cross-platform $EDITOR auto-detection for specsmith.

Resolution order (highest to lowest priority):
  1. ``$EDITOR`` environment variable
  2. ``editor`` key in ``~/.specsmith/config.toml`` or project ``.specsmith/config.yml``
  3. Auto-detection: probe PATH + well-known install locations per platform

Usage::

    from specsmith.editor import resolve_editor, list_detected_editors, set_editor_preference

    # What will specsmith use to open files?
    editor = resolve_editor()          # e.g. "code", "notepad++", "nvim"

    # Show all detected editors on this machine:
    editors = list_detected_editors()  # list of (name, path) tuples

    # Persist a preference:
    set_editor_preference("code")      # writes to ~/.specsmith/config.toml
"""

from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path
from typing import NamedTuple

__all__ = [
    "EditorCandidate",
    "list_detected_editors",
    "resolve_editor",
    "set_editor_preference",
]

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


class EditorCandidate(NamedTuple):
    """A discovered editor."""

    name: str
    """Short display name (e.g. 'VS Code', 'Notepad++')."""
    command: str
    """The executable / command to invoke (e.g. 'code', 'notepad++')."""
    path: str | None
    """Resolved absolute path, or None if only found via PATH probe."""


# ---------------------------------------------------------------------------
# Platform-specific candidate lists
# ---------------------------------------------------------------------------

#: Ordered list of (display_name, command) pairs for each platform.
#: The first entry that resolves wins for auto-detection.
_WINDOWS_CANDIDATES: list[tuple[str, str | list[str]]] = [
    # VS Code (most popular cross-platform)
    ("VS Code", "code"),
    # Cursor (AI-first VS Code fork)
    ("Cursor", "cursor"),
    # Notepad++ — check common install paths since it's not always on PATH
    ("Notepad++", r"%LOCALAPPDATA%\Programs\Notepad++\notepad++.exe"),
    ("Notepad++", r"%PROGRAMFILES%\Notepad++\notepad++.exe"),
    ("Notepad++", r"%PROGRAMFILES(X86)%\Notepad++\notepad++.exe"),
    ("Notepad++", "notepad++"),
    # Neovim (scoop / choco)
    ("Neovim", "nvim"),
    # Vim (git-bash / scoop / choco)
    ("Vim", "vim"),
    # Sublime Text
    ("Sublime Text", r"%PROGRAMFILES%\Sublime Text\subl.exe"),
    ("Sublime Text", r"%PROGRAMFILES%\Sublime Text 4\subl.exe"),
    ("Sublime Text", "subl"),
    # Built-in last resort
    ("Notepad", "notepad"),
]

_MACOS_CANDIDATES: list[tuple[str, str | list[str]]] = [
    ("VS Code", "code"),
    ("Cursor", "cursor"),
    ("Neovim", "nvim"),
    ("Vim", "vim"),
    ("BBEdit", "/Applications/BBEdit.app/Contents/OS X Resources/bbedit"),
    ("BBEdit", "bbedit"),
    ("Nano", "nano"),
    # TextEdit — open -e opens the file in TextEdit
    ("TextEdit", ["/usr/bin/open", "-e"]),
]

_LINUX_CANDIDATES: list[tuple[str, str | list[str]]] = [
    ("VS Code", "code"),
    ("Cursor", "cursor"),
    ("Neovim", "nvim"),
    ("Vim", "vim"),
    ("Nano", "nano"),
    ("Kate", "kate"),
    ("gedit", "gedit"),
    ("xed", "xed"),
    ("Mousepad", "mousepad"),
    ("Geany", "geany"),
    ("Micro", "micro"),
    ("Helix", "hx"),
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _expand(path_str: str) -> str:
    """Expand environment variables in a path string (Windows-style %VAR%)."""
    return os.path.expandvars(path_str)


def _probe_command(cmd: str | list[str]) -> str | None:
    """Return the resolved path for *cmd* if it is runnable, else None."""
    if isinstance(cmd, list):
        # Multi-token command (e.g. ["open", "-e"]) — probe the first token
        executable = cmd[0]
    else:
        executable = cmd

    # Expand env vars in Windows-style paths (%PROGRAMFILES%\...)
    expanded = _expand(executable)
    if os.sep in expanded or "/" in expanded:
        # Looks like an absolute/relative path — check if the file exists
        p = Path(expanded)
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
        return None

    # Plain command name — search PATH
    found = shutil.which(executable)
    return found if found else None


def _platform_candidates() -> list[tuple[str, str | list[str]]]:
    system = platform.system()
    if system == "Windows":
        return _WINDOWS_CANDIDATES
    if system == "Darwin":
        return _MACOS_CANDIDATES
    return _LINUX_CANDIDATES  # Linux / BSD / WSL


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_detected_editors() -> list[EditorCandidate]:
    """Return all editor candidates that are runnable on this machine.

    Each ``EditorCandidate`` is unique by *command* (the first token for
    multi-token commands). Duplicates (e.g. multiple Notepad++ paths) are
    deduplicated to the first match.

    Returns:
        Ordered list of :class:`EditorCandidate`, best-first.
    """
    seen_commands: set[str] = set()
    result: list[EditorCandidate] = []

    for display_name, cmd in _platform_candidates():
        cmd_key = cmd[0] if isinstance(cmd, list) else cmd
        if cmd_key in seen_commands:
            continue

        resolved = _probe_command(cmd)
        if resolved is None and isinstance(cmd, str):
            # For plain command names that aren't found, skip
            continue
        if resolved is not None:
            seen_commands.add(cmd_key)
            result.append(
                EditorCandidate(
                    name=display_name,
                    command=cmd_key,
                    path=resolved if resolved != cmd_key else None,
                )
            )

    return result


def resolve_editor() -> str | None:
    """Return the editor command specsmith should use, or ``None`` if unresolvable.

    Resolution order:
    1. ``$EDITOR`` environment variable (user's explicit choice)
    2. ``editor`` key in ``~/.specsmith/config.toml``
    3. First auto-detected editor on this machine

    Returns:
        The command string (e.g. ``"code"``, ``"notepad++"``, ``"nvim"``),
        or ``None`` if nothing was found.
    """
    # Priority 1: $EDITOR env var
    env_editor = os.environ.get("EDITOR", "").strip()
    if env_editor:
        return env_editor

    # Priority 2: ~/.specsmith/config.toml
    config_editor = _read_config_editor()
    if config_editor:
        return config_editor

    # Priority 3: auto-detect
    candidates = list_detected_editors()
    return candidates[0].command if candidates else None


def set_editor_preference(command: str) -> Path:
    """Persist *command* as the preferred editor in ``~/.specsmith/config.toml``.

    Creates the file and directory if they do not exist.

    Args:
        command: The editor command to save (e.g. ``"code"``, ``"nvim"``).

    Returns:
        The path of the written config file.
    """
    config_path = _global_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing content (if any) and update/insert the editor key
    existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    lines = existing.splitlines()

    # Find and replace an existing `editor = ...` line, or append
    new_lines: list[str] = []
    found = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("editor") and "=" in stripped:
            new_lines.append(f'editor = "{command}"')
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f'editor = "{command}"')

    config_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return config_path


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _global_config_path() -> Path:
    """Return ``~/.specsmith/config.toml``."""
    return Path.home() / ".specsmith" / "config.toml"


def _read_config_editor() -> str | None:
    """Read the ``editor`` key from ``~/.specsmith/config.toml``."""
    config_path = _global_config_path()
    if not config_path.is_file():
        return None
    try:
        # Minimal TOML parser for the editor key — avoids a tomllib dependency on 3.10
        for line in config_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("editor") and "=" in stripped:
                _, _, value = stripped.partition("=")
                value = value.strip().strip('"').strip("'")
                if value:
                    return value
    except OSError:
        pass
    return None
