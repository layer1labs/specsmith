# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Filesystem tools — all via pathlib, no subprocess."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Annotated


def read_file(
    path: Annotated[str, "File path relative to project root"],
    project_dir: str = ".",
) -> str:
    """Read a file's contents. Returns the text or an error message."""
    target = (Path(project_dir) / path).resolve()
    root = Path(project_dir).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return f"[ERROR] Path '{path}' is outside the project directory."
    if not target.exists():
        return f"[ERROR] File not found: {path}"
    if not target.is_file():
        return f"[ERROR] Not a file: {path}"
    try:
        return target.read_text(encoding="utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001
        return f"[ERROR] {e}"


def write_file(
    path: Annotated[str, "File path relative to project root"],
    content: Annotated[str, "Full content to write"],
    project_dir: str = ".",
) -> str:
    """Write content to a file (creates or overwrites). Returns confirmation."""
    target = (Path(project_dir) / path).resolve()
    root = Path(project_dir).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return f"[ERROR] Path '{path}' is outside the project directory."
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} chars to {path}"
    except Exception as e:  # noqa: BLE001
        return f"[ERROR] {e}"


def patch_file(
    path: Annotated[str, "File path relative to project root"],
    old_text: Annotated[str, "Exact text to find"],
    new_text: Annotated[str, "Replacement text"],
    project_dir: str = ".",
) -> str:
    """Replace the first occurrence of old_text with new_text in a file."""
    target = (Path(project_dir) / path).resolve()
    root = Path(project_dir).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return f"[ERROR] Path '{path}' is outside the project directory."
    if not target.exists():
        return f"[ERROR] File not found: {path}"
    try:
        text = target.read_text(encoding="utf-8")
        if old_text not in text:
            return f"[ERROR] old_text not found in {path}"
        patched = text.replace(old_text, new_text, 1)
        target.write_text(patched, encoding="utf-8")
        return f"Patched {path}: replaced {len(old_text)} chars with {len(new_text)} chars"
    except Exception as e:  # noqa: BLE001
        return f"[ERROR] {e}"


def list_tree(
    directory: Annotated[str, "Directory relative to project root"] = ".",
    max_depth: Annotated[int, "Maximum depth to traverse"] = 3,
    project_dir: str = ".",
) -> str:
    """List directory tree up to max_depth. Returns formatted tree string."""
    root = Path(project_dir).resolve()
    target = (root / directory).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return f"[ERROR] Path '{directory}' is outside the project directory."
    if not target.exists():
        return f"[ERROR] Directory not found: {directory}"

    _SKIP = {".git", "__pycache__", "node_modules", ".venv", "venv", ".specsmith", ".pytest_cache"}
    lines: list[str] = []

    def _walk(p: Path, depth: int, prefix: str) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(p.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return
        for i, entry in enumerate(entries):
            if entry.name in _SKIP:
                continue
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{entry.name}{'/' if entry.is_dir() else ''}")
            if entry.is_dir() and depth < max_depth:
                extension = "    " if is_last else "│   "
                _walk(entry, depth + 1, prefix + extension)

    lines.append(f"{target.name}/")
    _walk(target, 1, "")
    return "\n".join(lines[:500])  # cap output


def search_content(
    pattern: Annotated[str, "Regex or literal string to search for"],
    directory: Annotated[str, "Directory relative to project root"] = ".",
    glob: Annotated[str, "File glob pattern, e.g. '*.py'"] = "",
    project_dir: str = ".",
) -> str:
    """Search file contents for a pattern. Returns matches with file:line context."""
    import fnmatch as _fnmatch

    root = Path(project_dir).resolve()
    target = (root / directory).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return f"[ERROR] Path '{directory}' is outside the project directory."

    _SKIP = {".git", "__pycache__", "node_modules", ".venv", "venv", ".specsmith"}
    _TEXT_EXT = {
        ".py",
        ".md",
        ".txt",
        ".yml",
        ".yaml",
        ".toml",
        ".json",
        ".js",
        ".ts",
        ".sh",
        ".cmd",
        ".cfg",
        ".ini",
    }
    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except re.error:
        compiled = re.compile(re.escape(pattern), re.IGNORECASE)

    results: list[str] = []
    files_searched = 0

    for dirpath_str, dirnames, filenames in os.walk(target):
        dirnames[:] = [d for d in dirnames if d not in _SKIP]
        for fname in sorted(filenames):
            fp = Path(dirpath_str) / fname
            if glob and not _fnmatch.fnmatch(fname, glob):
                continue
            if not glob and fp.suffix.lower() not in _TEXT_EXT:
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
                files_searched += 1
                rel = fp.relative_to(root)
                for i, line in enumerate(text.splitlines(), 1):
                    if compiled.search(line):
                        results.append(f"{rel}:{i}: {line.rstrip()}")
                        if len(results) >= 200:
                            break
            except Exception:  # noqa: BLE001
                pass
            if len(results) >= 200:
                break
        if len(results) >= 200:
            break

    if not results:
        return f"No matches for '{pattern}' in {files_searched} file(s)."
    header = f"{len(results)} match(es) in {files_searched} file(s):"
    return header + "\n" + "\n".join(results)
