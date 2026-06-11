# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Architect — scan project and generate architecture documentation."""

from __future__ import annotations

from pathlib import Path


def scan_project_structure(root: Path) -> dict[str, object]:  # noqa: C901
    """Scan a project and extract architecture-relevant information.

    Returns a dict with modules, entry_points, languages, dependencies,
    git_summary, and existing_docs.
    """
    from specsmith.importer import (
        _extract_git_commits,
        _extract_git_contributors,
        _extract_readme_summary,
        _parse_dependencies,
        detect_project,
    )

    result = detect_project(root)
    commits = _extract_git_commits(root)
    contributors = _extract_git_contributors(root)
    readme = _extract_readme_summary(root)
    deps = _parse_dependencies(root)

    # Find existing architecture docs
    existing_arch: list[str] = []
    docs_dir = root / "docs"
    if docs_dir.is_dir():
        for p in docs_dir.rglob("*"):
            if p.is_file() and "architecture" in p.name.lower():
                existing_arch.append(str(p.relative_to(root)))

    return {
        "name": root.name,
        "languages": result.languages,
        "primary_language": result.primary_language,
        "secondary_languages": result.secondary_languages,
        "build_system": result.build_system,
        "test_framework": result.test_framework,
        "modules": result.modules,
        "entry_points": result.entry_points,
        "dependencies": deps,
        "readme_summary": readme,
        "recent_commits": commits[:10],
        "contributors": contributors,
        "existing_arch_docs": existing_arch,
        "file_count": result.file_count,
        "inferred_type": result.inferred_type.value if result.inferred_type else "unknown",
    }


def generate_architecture(
    root: Path,
    *,
    components: list[dict[str, str]] | None = None,
    data_flow: str = "",
    deployment: str = "",
    scan: dict[str, object] | None = None,
) -> Path:
    """Generate docs/architecture.md from scan data + user input.

    Returns the path to the generated file.
    """
    if scan is None:
        scan = scan_project_structure(root)

    name = str(scan.get("name", root.name))
    langs: dict[str, int] = dict(scan.get("languages", {}) or {})  # type: ignore[call-overload]
    primary = str(scan.get("primary_language", "unknown"))
    secondary: list[str] = list(scan.get("secondary_languages", []) or [])  # type: ignore[call-overload]
    lang_list = [primary] + secondary
    lang_display = ", ".join(str(l) for l in lang_list if l)  # noqa: E741

    doc = f"# Architecture — {name}\n\n"

    # Overview
    doc += "## Overview\n\n"
    readme = scan.get("readme_summary", "")
    if readme:
        doc += f"{readme}\n\n"
    doc += f"- **Languages**: {lang_display}\n"
    doc += f"- **Build system**: {scan.get('build_system', 'not detected')}\n"
    doc += f"- **Test framework**: {scan.get('test_framework', 'not detected')}\n"
    doc += f"- **Project type**: {scan.get('inferred_type', 'unknown')}\n"
    doc += f"- **Files**: {scan.get('file_count', 0)}\n\n"

    # Components
    if components:
        doc += "## Components\n\n"
        for comp in components:
            doc += f"### {comp.get('name', 'unnamed')}\n"
            if comp.get("purpose"):
                doc += f"- **Purpose**: {comp['purpose']}\n"
            if comp.get("interfaces"):
                doc += f"- **Interfaces**: {comp['interfaces']}\n"
            if comp.get("dependencies"):
                doc += f"- **Dependencies**: {comp['dependencies']}\n"
            doc += "\n"
    elif scan.get("modules"):
        doc += "## Modules\n\n"
        for mod in list(scan.get("modules", []) or []):  # type: ignore[call-overload]
            doc += f"### {mod}\n- **Purpose**: [Describe {mod} purpose]\n\n"

    # Data flow
    if data_flow:
        doc += f"## Data Flow\n\n{data_flow}\n\n"
    else:
        doc += "## Data Flow\n\n[Describe how data flows between components]\n\n"

    # Dependencies
    deps: list[str] = list(scan.get("dependencies", []) or [])  # type: ignore[call-overload]
    if deps:
        doc += "## External Dependencies\n\n"
        for dep in deps[:30]:
            doc += f"- `{dep}`\n"
        doc += "\n"

    # Entry points
    eps: list[str] = list(scan.get("entry_points", []) or [])  # type: ignore[call-overload]
    if eps:
        doc += "## Entry Points\n\n"
        for ep in eps:
            doc += f"- `{ep}`\n"
        doc += "\n"

    # Language distribution
    if langs and len(langs) > 1:
        doc += "## Language Distribution\n\n"
        for lang_name, count in sorted(langs.items(), key=lambda x: -x[1]):
            doc += f"- {lang_name}: {count} files\n"
        doc += "\n"

    # Deployment
    if deployment:
        doc += f"## Deployment\n\n{deployment}\n\n"

    # Existing architecture references
    existing: list[str] = list(scan.get("existing_arch_docs", []) or [])  # type: ignore[call-overload]
    if existing:
        doc += "## Related Documents\n\n"
        for ref in existing:
            doc += f"- [{ref}]({ref})\n"
        doc += "\n"

    # Write
    arch_path = root / "docs" / "ARCHITECTURE.md"
    arch_path.parent.mkdir(parents=True, exist_ok=True)
    arch_path.write_text(doc, encoding="utf-8")
    return arch_path
