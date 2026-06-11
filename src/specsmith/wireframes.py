# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Wireframe artifact helpers for UI-oriented projects."""

from __future__ import annotations

import re
from pathlib import Path

from specsmith.requirements import list_reqs

_WF_ID_RE = re.compile(r"^(WF-[A-Z0-9-]+)")


def _wireframes_dir(root: Path) -> Path:
    return root / "docs" / "wireframes"


def list_wireframes(root: Path) -> list[dict[str, str]]:
    """List wireframe files and any directly linked requirements."""
    wf_dir = _wireframes_dir(root)
    reqs = list_reqs(root)
    refs: dict[str, list[str]] = {}
    for req in reqs:
        wf = req.get("wireframe", "").strip()
        if wf:
            refs.setdefault(Path(wf).name, []).append(req["id"])

    items: list[dict[str, str]] = []
    if not wf_dir.exists():
        return items
    for fp in sorted(p for p in wf_dir.iterdir() if p.is_file()):
        match = _WF_ID_RE.match(fp.stem)
        items.append(
            {
                "id": match.group(1) if match else fp.stem,
                "file": str(fp.relative_to(root)),
                "refs": ", ".join(refs.get(fp.name, [])),
            }
        )
    return items


def check_wireframe_refs(root: Path) -> list[str]:
    """Return missing wireframe references from REQUIREMENTS.md."""
    missing: list[str] = []
    for req in list_reqs(root):
        wf = req.get("wireframe", "").strip()
        if not wf:
            continue
        target = (root / wf).resolve()
        if not target.exists():
            missing.append(f"{req['id']} → {wf}")
    return missing


def read_wireframe(root: Path, wireframe_id: str) -> str:
    """Return metadata and best-effort content for a wireframe artifact."""
    wf_dir = _wireframes_dir(root)
    if not wf_dir.exists():
        return "[NOT FOUND] docs/wireframes/"

    needle = wireframe_id.lower()
    candidates = [
        fp
        for fp in wf_dir.iterdir()
        if fp.is_file() and (fp.name.lower() == needle or fp.stem.lower().startswith(needle))
    ]
    if not candidates:
        return f"[NOT FOUND] {wireframe_id}"

    target = candidates[0]
    size = target.stat().st_size
    rel = target.relative_to(root)
    suffix = target.suffix.lower()
    header = f"{rel} ({size:,} bytes)"
    if suffix in {".svg", ".md", ".txt"}:
        content = target.read_text(encoding="utf-8", errors="ignore")
        if len(content) > 8000:
            content = content[:8000] + "\n...(truncated)"
        return f"{header}\n\n{content}"
    return (
        f"{header}\n\n"
        "Binary wireframe asset. Use a vision-capable client or open the file directly. "
        "For traceability, reference it from REQUIREMENTS.md via a `Wireframe` field."
    )
