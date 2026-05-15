# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.

import re
from pathlib import Path


def parse_architecture_requirements(project_dir: Path) -> list[dict[str, str]]:
    """
    Scans ARCHITECTURE.md for discernible requirements.
    Requirements are identified by markdown headings (H2 or H3)
    within "Components" or "Features" sections, followed by bullet points
    describing purpose, interfaces, dependencies, or other specific functionalities.
    """
    arch_path = project_dir / "docs" / "ARCHITECTURE.md"
    if not arch_path.exists():
        return []

    content = arch_path.read_text(encoding="utf-8")
    requirements: list[dict[str, str]] = []
    req_counter = 1

    lines = content.splitlines()
    i = 0

    def _is_section_boundary(line: str) -> bool:
        # A section ends when we hit another `## ` heading that isn't itself
        # a Components / Features heading.
        return line.startswith("## ") and not (
            line.startswith("## Components") or line.startswith("## Features")
        )

    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("## Components") or line.startswith("## Features"):
            # Start of a section that might contain components/features
            i += 1
            while i < len(lines) and not _is_section_boundary(lines[i]):
                sub_line = lines[i].strip()
                component_match = re.match(r"###\s*(.+)", sub_line)
                if component_match:
                    current_component = component_match.group(1).strip()
                    i += 1
                    # Look for bullet points describing the component
                    while i < len(lines) and lines[i].strip().startswith("-"):
                        req_desc = lines[i].strip().lstrip("- ").strip()
                        if req_desc:
                            slug = current_component.upper().replace(" ", "-")
                            req_id = f"{slug}-REQ-{req_counter:03d}"
                            requirements.append(
                                {
                                    "id": req_id,
                                    "component": current_component,
                                    "description": req_desc,
                                    "status": "Draft",
                                    "priority": "Medium",
                                }
                            )
                            req_counter += 1
                        i += 1
                else:
                    i += 1
        else:
            i += 1

    return requirements


def define_test_cases(requirements: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Defines simple test cases based on a list of requirements.
    Each requirement typically gets at least one test case.
    """
    test_cases: list[dict[str, str]] = []
    test_counter = 1
    for req in requirements:
        test_id = f"TEST-{test_counter:03d}"
        test_cases.append(
            {
                "id": test_id,
                "requirement_id": req["id"],
                "description": f"Verify {req['description'].lower()}",
                "type": "Unit",
                "status": "Pending",
            }
        )
        test_counter += 1
    return test_cases
