# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Compliance scoring and reporting (REQ-224).

Provides compliance summary, requirement gaps, test coverage, and
traceability matrix. Used by both CLI commands and REST endpoints.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ComplianceSummary:
    """Overall compliance status for a project."""

    total_requirements: int = 0
    covered_requirements: int = 0
    uncovered_requirements: list[str] = field(default_factory=list)
    total_tests: int = 0
    orphaned_tests: list[str] = field(default_factory=list)
    compliance_score: int = 0  # 0-100
    requirement_coverage_pct: int = 0
    trace_matrix: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_requirements": self.total_requirements,
            "covered_requirements": self.covered_requirements,
            "uncovered_requirements": self.uncovered_requirements,
            "total_tests": self.total_tests,
            "orphaned_tests": self.orphaned_tests,
            "compliance_score": self.compliance_score,
            "requirement_coverage_pct": self.requirement_coverage_pct,
            "trace_count": len(self.trace_matrix),
        }


def _parse_requirements(root: Path) -> dict[str, dict[str, str]]:
    """Parse REQUIREMENTS.md into {req_id: {title, status, ...}}."""
    req_path = root / "docs" / "REQUIREMENTS.md"
    if not req_path.is_file():
        req_path = root / "REQUIREMENTS.md"
    if not req_path.is_file():
        return {}

    text = req_path.read_text(encoding="utf-8", errors="replace")
    reqs: dict[str, dict[str, str]] = {}

    # Parse markdown sections: ## N. Title\n- **ID:** REQ-NNN
    blocks = re.split(r"\n## ", text)
    for block in blocks:
        id_match = re.search(r"\*\*ID:\*\*\s*(REQ-\d+)", block)
        if not id_match:
            # Try alternate format: ## REQ-NNN
            id_match = re.search(r"^(REQ-\d+)", block.strip())
        if id_match:
            req_id = id_match.group(1)
            title_match = re.search(r"\*\*Title:\*\*\s*(.+)", block)
            status_match = re.search(r"\*\*Status:\*\*\s*(.+)", block)
            reqs[req_id] = {
                "id": req_id,
                "title": title_match.group(1).strip() if title_match else "",
                "status": status_match.group(1).strip() if status_match else "draft",
            }

    return reqs


def _parse_tests(root: Path) -> dict[str, dict[str, str]]:
    """Parse TESTS.md into {test_id: {title, requirement_id, ...}}."""
    test_path = root / "docs" / "TESTS.md"
    if not test_path.is_file():
        test_path = root / "TESTS.md"
    if not test_path.is_file():
        return {}

    text = test_path.read_text(encoding="utf-8", errors="replace")
    tests: dict[str, dict[str, str]] = {}

    blocks = re.split(r"\n## ", text)
    for block in blocks:
        id_match = re.search(r"\*\*ID:\*\*\s*(TEST-\d+)", block)
        if not id_match:
            id_match = re.search(r"^(TEST-\d+)", block.strip())
        if id_match:
            test_id = id_match.group(1)
            req_match = re.search(r"\*\*Requirement(?:\s+ID)?:\*\*\s*(REQ-\d+)", block)
            title_match = re.search(r"\*\*Title:\*\*\s*(.+)", block)
            tests[test_id] = {
                "id": test_id,
                "title": title_match.group(1).strip() if title_match else "",
                "requirement_id": req_match.group(1) if req_match else "",
            }

    return tests


def get_compliance_summary(project_dir: str | Path = ".") -> ComplianceSummary:
    """Compute full compliance summary for a project."""
    root = Path(project_dir).resolve()
    reqs = _parse_requirements(root)
    tests = _parse_tests(root)

    # Build coverage map
    covered_req_ids: set[str] = set()
    for test in tests.values():
        req_id = test.get("requirement_id", "")
        if req_id and req_id in reqs:
            covered_req_ids.add(req_id)

    uncovered = [r for r in reqs if r not in covered_req_ids]

    # Find orphaned tests (reference non-existent requirements)
    orphaned = []
    for test in tests.values():
        req_id = test.get("requirement_id", "")
        if req_id and req_id not in reqs:
            orphaned.append(f"{test['id']} -> {req_id}")

    total = len(reqs)
    covered = len(covered_req_ids)
    coverage_pct = int(covered / total * 100) if total > 0 else 0

    # Build trace matrix
    trace: list[dict[str, Any]] = []
    for req_id, req in sorted(reqs.items()):
        linked_tests = [t["id"] for t in tests.values() if t.get("requirement_id") == req_id]
        trace.append(
            {
                "requirement_id": req_id,
                "title": req.get("title", ""),
                "status": req.get("status", ""),
                "tests": linked_tests,
                "covered": len(linked_tests) > 0,
            }
        )

    return ComplianceSummary(
        total_requirements=total,
        covered_requirements=covered,
        uncovered_requirements=uncovered,
        total_tests=len(tests),
        orphaned_tests=orphaned,
        compliance_score=coverage_pct,
        requirement_coverage_pct=coverage_pct,
        trace_matrix=trace,
    )


def get_governance_rules_status(project_dir: str | Path = ".") -> list[dict[str, Any]]:
    """Return status of hard governance rules (H1-H22)."""
    root = Path(project_dir).resolve()

    rules = [
        {"id": "H1", "name": "Ledger required", "description": "No ledger entry = work not done"},
        {"id": "H2", "name": "Proposal required", "description": "No proposal = no execution"},
        {
            "id": "H3",
            "name": "Cross-platform awareness",
            "description": "All work must consider every target platform",
        },
        {
            "id": "H4",
            "name": "Environment isolation",
            "description": "No system-dependent assumptions",
        },
        {"id": "H5", "name": "Explicit startup", "description": "No hidden service logic"},
        {
            "id": "H6",
            "name": "No silent scope expansion",
            "description": "If task grows, stop and re-propose",
        },
        {
            "id": "H7",
            "name": "No undocumented state changes",
            "description": "Every change must be traceable",
        },
        {
            "id": "H8",
            "name": "Documentation is implementation",
            "description": "Architecture changes MUST update docs",
        },
        {
            "id": "H9",
            "name": "Execution timeout required",
            "description": "All agent commands must have timeouts",
        },
        {
            "id": "H10",
            "name": "No hardcoded versions",
            "description": "Use importlib.metadata at runtime",
        },
        {
            "id": "H11",
            "name": "No unbounded loops",
            "description": "Every loop must have a deadline",
        },
        {
            "id": "H12",
            "name": "Platform-aware automation",
            "description": "Use sh/bash on Unix/macOS; .cmd/.ps1 on Windows; never assume a single platform",
        },
        {
            "id": "H13",
            "name": "Epistemic boundaries required",
            "description": "Proposals must state assumptions",
        },
        {
            "id": "H14",
            "name": "Documentation freshness",
            "description": "Docs updated in same commit as code",
        },
        # H15-H22: Anti-hallucination / OEA recursive generative stability (derived from research)
        {
            "id": "H15",
            "name": "Epistemic scope bounding",
            "description": "Agent must not make claims outside verified knowledge; say 'unknown' rather than fabricate",
        },
        {
            "id": "H16",
            "name": "Anti-drift recursion guard",
            "description": "Multi-step generation chains must have a finite iteration limit; no recursive output-as-input without a checkpoint",
        },
        {
            "id": "H17",
            "name": "Calibration direction",
            "description": "Express uncertainty rather than false confidence; output confidence must not exceed evidence quality",
        },
        {
            "id": "H18",
            "name": "RAG retrieval filtering",
            "description": "Retrieved context must pass relevance validation before inclusion; low-confidence chunks must be discarded",
        },
        {
            "id": "H19",
            "name": "Synthetic contamination prevention",
            "description": "Synthetically generated data must not be silently mixed with real ground-truth data in eval or training pipelines",
        },
        {
            "id": "H20",
            "name": "Falsifiability required",
            "description": "All factual agent claims must cite verifiable sources or be explicitly marked as unverified hypotheses",
        },
        {
            "id": "H21",
            "name": "No undisclosed model assumptions",
            "description": "Any model-specific behaviour relied upon (context window, format) must be explicitly stated in the proposal",
        },
        {
            "id": "H22",
            "name": "Cross-platform CI enforcement",
            "description": "CI pipelines must run on Linux/macOS and Windows; single-platform green is not cross-platform coverage",
        },
    ]

    # Quick checks for common violations
    ledger_exists = (root / "docs" / "LEDGER.md").is_file() or (root / "LEDGER.md").is_file()
    agents_exists = (root / "AGENTS.md").is_file()
    ci_path = root / ".github" / "workflows"
    ci_exists = ci_path.is_dir() and any(ci_path.glob("*.yml"))

    for rule in rules:
        rule["status"] = "ok"  # default

    if not ledger_exists:
        rules[0]["status"] = "violation"
    if not agents_exists:
        rules[1]["status"] = "warning"
    # H22: warn if no CI workflows directory exists
    if not ci_exists:
        for rule in rules:
            if rule["id"] == "H22":
                rule["status"] = "warning"
                break

    return rules
