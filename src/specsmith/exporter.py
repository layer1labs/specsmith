# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Exporter — generate compliance and coverage reports."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from specsmith.auditor import run_audit
from specsmith.config import ProjectConfig
from specsmith.tools import get_tools


def run_export(root: Path) -> str:
    """Generate a compliance report as Markdown.

    Includes: project summary, REQ↔TEST coverage matrix, audit summary,
    tool configuration status.
    """
    scaffold_path = root / "scaffold.yml"
    sections: list[str] = [f"# Compliance Report — {root.name}\n"]
    sections.append(f"**Generated:** {date.today().isoformat()}\n")

    # --- Project summary ---
    if scaffold_path.exists():
        import yaml

        with open(scaffold_path) as f:
            raw = yaml.safe_load(f)
        try:
            config = ProjectConfig(**raw)
            tools = get_tools(config)
            sections.append("## Project Summary\n")
            sections.append(f"- **Name**: {config.name}")
            sections.append(f"- **Type**: {config.type_label}")
            sections.append(f"- **Language**: {config.language}")
            sections.append(f"- **VCS Platform**: {config.vcs_platform or 'none'}")
            sections.append(f"- **Spec Version**: {config.spec_version}\n")

            sections.append("## Verification Tools\n")
            sections.append(f"- **Lint**: {', '.join(tools.lint) or 'none'}")
            sections.append(f"- **Typecheck**: {', '.join(tools.typecheck) or 'none'}")
            sections.append(f"- **Test**: {', '.join(tools.test) or 'none'}")
            sections.append(f"- **Security**: {', '.join(tools.security) or 'none'}")
            sections.append(f"- **Build**: {', '.join(tools.build) or 'none'}")
            sections.append(f"- **Format**: {', '.join(tools.format) or 'none'}")
            if tools.compliance:
                sections.append(f"- **Compliance**: {', '.join(tools.compliance)}")
            sections.append("")
        except Exception:  # noqa: BLE001
            sections.append("## Project Summary\n")
            sections.append("*Could not parse scaffold.yml*\n")

    # --- REQ↔TEST coverage matrix ---
    import re

    req_path = root / "docs" / "REQUIREMENTS.md"
    test_path = root / "docs" / "TESTS.md"

    if req_path.exists() and test_path.exists():
        req_text = req_path.read_text(encoding="utf-8")
        test_text = test_path.read_text(encoding="utf-8")

        req_pattern = re.compile(r"\b(REQ-[A-Z]+-\d+)\b")
        covers_pattern = re.compile(r"Covers:\s*(REQ-[A-Z]+-\d+(?:\s*,\s*REQ-[A-Z]+-\d+)*)")

        req_ids = sorted(set(req_pattern.findall(req_text)))
        covered: set[str] = set()
        for match in covers_pattern.finditer(test_text):
            for rid in req_pattern.findall(match.group(0)):
                covered.add(rid)

        sections.append("## Requirements Coverage Matrix\n")
        total = len(req_ids)
        covered_count = len(covered & set(req_ids))
        pct = (covered_count / total * 100) if total else 0
        sections.append(f"**Coverage**: {covered_count}/{total} ({pct:.0f}%)\n")

        for rid in req_ids:
            status = "✓" if rid in covered else "✗"
            sections.append(f"- {status} {rid}")
        sections.append("")

    # --- Audit summary ---
    report = run_audit(root)
    sections.append("## Audit Summary\n")
    sections.append(f"- **Passed**: {report.passed}")
    sections.append(f"- **Failed**: {report.failed}")
    sections.append(f"- **Fixable**: {report.fixable}")
    sections.append(f"- **Status**: {'Healthy' if report.healthy else 'Issues found'}\n")

    for r in report.results:
        icon = "✓" if r.passed else "✗"
        sections.append(f"- {icon} {r.message}")
    sections.append("")

    # --- Git activity ---
    git_dir = root / ".git"
    if git_dir.exists():
        import subprocess

        sections.append("## Recent Activity\n")
        try:
            log = subprocess.run(
                ["git", "-C", str(root), "log", "--oneline", "-10"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if log.returncode == 0 and log.stdout.strip():
                for line in log.stdout.strip().splitlines():
                    sections.append(f"- `{line}`")
                sections.append("")

            # Contributors
            contribs = subprocess.run(
                ["git", "-C", str(root), "shortlog", "-sn", "--no-merges", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if contribs.returncode == 0 and contribs.stdout.strip():
                sections.append("**Contributors:**")
                for line in contribs.stdout.strip().splitlines()[:10]:
                    sections.append(f"- {line.strip()}")
                sections.append("")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            sections.append("*Could not read git history*\n")

    # --- Governance file inventory ---
    sections.append("## Governance File Inventory\n")
    gov_files = [
        "AGENTS.md",
        "LEDGER.md",
        "scaffold.yml",
        "docs/REQUIREMENTS.md",
        "docs/TESTS.md",
        "docs/ARCHITECTURE.md",
        "docs/governance/RULES.md",
        "docs/governance/SESSION-PROTOCOL.md",
        "docs/governance/LIFECYCLE.md",
        "docs/governance/ROLES.md",
        "docs/governance/VERIFICATION.md",
    ]
    for gf in gov_files:
        exists = (root / gf).exists()
        icon = "✓" if exists else "✗"
        sections.append(f"- {icon} `{gf}`")

    return "\n".join(sections) + "\n"
