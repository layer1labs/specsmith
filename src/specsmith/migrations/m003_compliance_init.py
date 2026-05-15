# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""M003 — Compliance structure initialization.

Creates .specsmith/compliance/ with skeleton regulation YAML files
that projects can customize to override compliance status for their
specific jurisdiction and use case.
"""

from __future__ import annotations

from pathlib import Path

from specsmith.migrations import Migration, MigrationResult


_COMPLIANCE_README = """\
# .specsmith/compliance/

Project-specific compliance overlays for AI regulation.

## Structure

Each file overrides the built-in regulation status for this project:
  eu-ai-act.yaml        — EU AI Act (Regulation 2024/1689)
  nist-rmf.yaml         — NIST AI RMF 1.0 + AI 600-1
  omb-m-24-10.yaml      — OMB M-24-10
  colorado-sb24-205.yaml — Colorado AI Act (effective Feb 2026)
  texas-hb1709.yaml     — Texas AI Transparency Act
  etc.

## Usage

  # Check compliance for all regulations
  specsmith compliance check

  # Generate compliance report
  specsmith compliance report --format html --output compliance-report.html

  # Store results to ESDB audit trail
  specsmith compliance audit

See: https://specsmith.readthedocs.io/en/stable/compliance/
"""

_EU_OVERLAY = """\
# EU AI Act (Regulation 2024/1689) — project overlay
#
# This file allows overriding compliance status for this specific project.
# Leave fields empty to use specsmith's auto-detection.
#
# regulation_id: eu-ai-act
# project notes:

risk_tier: minimal_risk   # prohibited | high_risk | gpai | minimal_risk
is_gpai: false            # true if this is a General Purpose AI model
gpai_systemic_risk: false # true if > 10^25 FLOP training compute

# Override specific article status (auto-detected if absent):
# article_overrides:
#   Art.9:
#     status: compliant
#     notes: "Risk management system via specsmith AEE pipeline"
"""


class ComplianceInitMigration(Migration):
    version = 3
    title = "Initialize .specsmith/compliance/ structure"
    description = (
        "Creates .specsmith/compliance/ with skeleton regulation overlay files "
        "and a README. Projects can customize these to document their specific "
        "jurisdiction, risk tier, and compliance status."
    )

    def run(self, root: Path, *, dry_run: bool = False) -> MigrationResult:
        result = MigrationResult(version=self.version, title=self.title, dry_run=dry_run)

        compliance_dir = root / ".specsmith" / "compliance"
        if compliance_dir.is_dir() and any(compliance_dir.iterdir()):
            result.message = ".specsmith/compliance/ already exists — nothing to do."
            return result

        files = {
            "README.md": _COMPLIANCE_README,
            "eu-ai-act.yaml": _EU_OVERLAY,
        }

        for filename, content in files.items():
            path = compliance_dir / filename
            if dry_run:
                result.files_created.append(f".specsmith/compliance/{filename}")
            else:
                compliance_dir.mkdir(parents=True, exist_ok=True)
                if not path.exists():
                    path.write_text(content, encoding="utf-8")
                    result.files_created.append(f".specsmith/compliance/{filename}")

        if dry_run:
            result.message = f"Would create .specsmith/compliance/ with {len(files)} file(s)."
        elif result.files_created:
            result.message = (
                f"Created .specsmith/compliance/ with {len(result.files_created)} file(s). "
                "Edit eu-ai-act.yaml to set your project's risk tier."
            )
        else:
            result.message = "Compliance files already present."

        return result
