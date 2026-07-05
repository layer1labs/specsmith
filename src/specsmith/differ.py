# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Differ — compare governance files against spec templates."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml
from jinja2 import Environment, PackageLoader, select_autoescape

from specsmith.config import ProjectConfig, _normalize_scaffold_raw
from specsmith.paths import find_scaffold

_GOVERNANCE_FILES: list[tuple[str, str]] = [
    ("governance/rules.md.j2", "docs/governance/RULES.md"),
    ("governance/session-protocol.md.j2", "docs/governance/SESSION-PROTOCOL.md"),
    ("governance/lifecycle.md.j2", "docs/governance/LIFECYCLE.md"),
    ("governance/roles.md.j2", "docs/governance/ROLES.md"),
    ("governance/context-budget.md.j2", "docs/governance/CONTEXT-BUDGET.md"),
    ("governance/verification.md.j2", "docs/governance/VERIFICATION.md"),
    ("governance/drift-metrics.md.j2", "docs/governance/DRIFT-METRICS.md"),
]


def run_diff(root: Path) -> list[tuple[str, str]]:
    """Compare governance files against what templates would generate.

    Returns list of (relative_path, status) where status is 'match', 'differs', or 'missing'.
    """
    scaffold_path = find_scaffold(root)
    if not scaffold_path or not scaffold_path.exists():
        return [("docs/SPECSMITH.yml", "missing")]

    with open(scaffold_path) as f:
        raw = yaml.safe_load(f)

    raw = _normalize_scaffold_raw(raw or {})
    try:
        config = ProjectConfig(**raw)
    except Exception as e:  # noqa: BLE001
        return [(scaffold_path.name, f"invalid: {e}")]

    env = Environment(
        loader=PackageLoader("specsmith", "templates"),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    from specsmith.phase import PHASE_MAP, read_phase
    from specsmith.tools import get_tools

    phase_key = read_phase(root)
    phase_obj = PHASE_MAP.get(phase_key, PHASE_MAP["inception"])
    ctx = {
        "project": config,
        "today": date.today().isoformat(),
        "package_name": config.package_name,
        "tools": get_tools(config),
        "aee_phase": phase_key,
        "aee_phase_label": phase_obj.label,
        "aee_phase_emoji": phase_obj.emoji,
    }

    results: list[tuple[str, str]] = []

    # Check for files migrated by applied migrations (#136).
    # If migration-state.json records v001 as applied, files under docs/governance/
    # that it consumed are now in .specsmith/governance/ — don't flag them as missing.
    _migrated_files: set[str] = set()
    migration_state = root / ".specsmith" / "migration-state.json"
    if migration_state.exists():
        try:
            import json

            state = json.loads(migration_state.read_text(encoding="utf-8"))
            # v001 migrates docs/governance/*.md files
            v001 = next((m for m in state if m.get("version") == "001" and m.get("success")), None)
            if v001:
                _migrated_files = {
                    "docs/governance/RULES.md",
                    "docs/governance/SESSION-PROTOCOL.md",
                    "docs/governance/LIFECYCLE.md",
                    "docs/governance/ROLES.md",
                    "docs/governance/CONTEXT-BUDGET.md",
                    "docs/governance/VERIFICATION.md",
                    "docs/governance/DRIFT-METRICS.md",
                }
        except Exception:  # noqa: BLE001
            pass

    for template_name, output_rel in _GOVERNANCE_FILES:
        output_path = root / output_rel
        if not output_path.exists():
            # Skip files intentionally migrated by applied migrations (#136)
            if output_rel in _migrated_files:
                results.append((output_rel, "migrated"))
                continue
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

    scaffold_path = find_scaffold(root)
    if not scaffold_path or not scaffold_path.exists():
        return (
            "<html><body><p>No scaffold config found"
            " (docs/SPECSMITH.yml or scaffold.yml).</p></body></html>"
        )

    with open(scaffold_path) as f:
        raw = yaml.safe_load(f)

    raw = _normalize_scaffold_raw(raw or {})
    try:
        config = ProjectConfig(**raw)
    except Exception as e:  # noqa: BLE001
        return f"<html><body><p>Invalid scaffold config: {e}.</p></body></html>"

    from specsmith.tools import get_tools

    env = Environment(
        loader=PackageLoader("specsmith", "templates"),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    from specsmith.phase import PHASE_MAP, read_phase

    phase_key = read_phase(root)
    phase_obj = PHASE_MAP.get(phase_key, PHASE_MAP["inception"])
    ctx = {
        "project": config,
        "today": date.today().isoformat(),
        "package_name": config.package_name,
        "tools": get_tools(config),
        "aee_phase": phase_key,
        "aee_phase_label": phase_obj.label,
        "aee_phase_emoji": phase_obj.emoji,
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
