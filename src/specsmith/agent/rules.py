# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Project rules auto-injection for the Nexus orchestrator (REQ-119).

Combines `docs/governance/*_RULES.md` files and the H-rules from
`AGENTS.md` into a single deterministic system-prompt prefix that the
orchestrator prepends to every AG2 agent's `system_message`.
"""

from __future__ import annotations

import re
from pathlib import Path


def load_rules(project_dir: Path) -> str:
    """Return the combined rules prefix for ``project_dir``.

    The returned string is empty when no governance rule files are present
    (so older projects keep working unchanged). When rules exist, they are
    rendered as a single compact block so AG2 token costs stay reasonable.
    """
    project_dir = Path(project_dir)
    sections: list[str] = []

    governance_dir = project_dir / "docs" / "governance"
    if governance_dir.is_dir():
        for path in sorted(governance_dir.glob("*_RULES.md")):
            try:
                text = path.read_text(encoding="utf-8").strip()
            except OSError:
                continue
            if text:
                sections.append(f"# {path.stem}\n{text}")

    agents_md = project_dir / "AGENTS.md"
    if agents_md.is_file():
        try:
            agents_text = agents_md.read_text(encoding="utf-8")
        except OSError:
            agents_text = ""
        h_rules = _extract_h_rules(agents_text)
        if h_rules:
            sections.append("# AGENTS.md hard rules\n" + h_rules)

    if not sections:
        return ""

    return "## Project Governance Rules (auto-loaded)\n" + "\n\n".join(sections) + "\n"


def _extract_h_rules(text: str) -> str:
    """Extract numbered hard-rules (`H1`, `H2`, ...) from AGENTS.md."""
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^[*\-]?\s*\*?\*?H\d+\b", stripped):
            lines.append(stripped.lstrip("*-").lstrip())
    return "\n".join(lines)


__all__ = ["load_rules"]
