# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Differ — compare governance files against spec templates."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml
from jinja2 import Environment, PackageLoader, select_autoescape

from specsmith.config import ProjectConfig

_GOVERNANCE_FILES: list[tuple[str, str]] = [
    ("governance/rules.md.j2", "docs/governance/rules.md"),
    ("governance/workflow.md.j2", "docs/governance/workflow.md"),
    ("governance/roles.md.j2", "docs/governance/roles.md"),
    ("governance/context-budget.md.j2", "docs/governance/context-budget.md"),
    ("governance/verification.md.j2", "docs/governance/verification.md"),
    ("governance/drift-metrics.md.j2", "docs/governance/drift-metrics.md"),
]


def run_diff(root: Path) -> list[tuple[str, str]]:
    """Compare governance files against what templates would generate.

    Returns list of (relative_path, status) where status is 'match', 'differs', or 'missing'.
    """
    scaffold_path = root / "scaffold.yml"
    if not scaffold_path.exists():
        return [("scaffold.yml", "missing")]

    with open(scaffold_path) as f:
        raw = yaml.safe_load(f)

    try:
        config = ProjectConfig(**raw)
    except Exception:
        return [("scaffold.yml", "invalid")]

    env = Environment(
        loader=PackageLoader("specsmith", "templates"),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    from specsmith.tools import get_tools

    ctx = {
        "project": config,
        "today": date.today().isoformat(),
        "package_name": config.package_name,
        "tools": get_tools(config),
    }

    results: list[tuple[str, str]] = []

    for template_name, output_rel in _GOVERNANCE_FILES:
        output_path = root / output_rel
        if not output_path.exists():
            results.append((output_rel, "missing"))
            continue

        tmpl = env.get_template(template_name)
        expected = tmpl.render(**ctx)
        actual = output_path.read_text(encoding="utf-8")

        if _normalize(actual) == _normalize(expected):
            results.append((output_rel, "match"))
        else:
            results.append((output_rel, "differs"))

    return results


def run_diff_html(root: Path) -> str:
    """Generate an HTML diff report with side-by-side views."""
    import difflib

    scaffold_path = root / "scaffold.yml"
    if not scaffold_path.exists():
        return "<html><body><p>No scaffold.yml found.</p></body></html>"

    with open(scaffold_path) as f:
        raw = yaml.safe_load(f)

    try:
        config = ProjectConfig(**raw)
    except Exception:
        return "<html><body><p>Invalid scaffold.yml.</p></body></html>"

    from specsmith.tools import get_tools

    env = Environment(
        loader=PackageLoader("specsmith", "templates"),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    ctx = {
        "project": config,
        "today": date.today().isoformat(),
        "package_name": config.package_name,
        "tools": get_tools(config),
    }

    differ = difflib.HtmlDiff(wrapcolumn=80)
    sections: list[str] = []
    sections.append("<html><head><title>Governance Diff Report</title></head><body>")
    sections.append(f"<h1>Governance Diff — {config.name}</h1>")

    match_count = 0
    diff_count = 0
    missing_count = 0

    for template_name, output_rel in _GOVERNANCE_FILES:
        output_path = root / output_rel
        if not output_path.exists():
            sections.append(f'<h3 style="color:red">✗ {output_rel} — MISSING</h3>')
            missing_count += 1
            continue

        tmpl = env.get_template(template_name)
        expected = tmpl.render(**ctx)
        actual = output_path.read_text(encoding="utf-8")

        if _normalize(actual) == _normalize(expected):
            sections.append(f'<h3 style="color:green">✓ {output_rel} — matches</h3>')
            match_count += 1
        else:
            sections.append(f'<h3 style="color:orange">~ {output_rel} — differs</h3>')
            table = differ.make_table(
                expected.splitlines(),
                actual.splitlines(),
                fromdesc="Template",
                todesc="Current",
            )
            sections.append(table)
            diff_count += 1

    summary = (
        f"<p><b>Summary:</b> {match_count} match, {diff_count} differ, {missing_count} missing</p>"
    )
    sections.insert(2, summary)
    sections.append("</body></html>")
    return "\n".join(sections)


def _normalize(text: str) -> str:
    """Normalize whitespace for comparison."""
    return "\n".join(line.rstrip() for line in text.strip().splitlines())
