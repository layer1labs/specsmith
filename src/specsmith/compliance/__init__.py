# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""specsmith compliance — EU and North American AI regulation compliance.

Provides structured regulation definitions, ESDB-backed evidence collection,
per-regulation compliance checking, and report generation.

Supported regulations (May 2026):
  EU:
    - EU AI Act 2024/1689 (Arts. 5, 9, 12, 13, 14, 15, 52, 72)
  US Federal:
    - NIST AI RMF 1.0 (Jan 2023) + AI 600-1 GenAI Profile (Jul 2024)
    - OMB M-24-10 (Mar 2024)
  US State:
    - Colorado SB24-205 / AI Act (effective Feb 1, 2026)
    - Texas HB 1709 / AI Transparency Act (effective Sep 1, 2025)
    - Illinois AI Employment Transparency Act (2023)
    - California AB 2930 / CPPA ADMT (2026)
    - NYC Local Law 144 (2023)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from specsmith.compliance.regulations import Regulation

__all__ = [
    "ComplianceChecker",
    "ComplianceResult",
    "EvidenceCollector",
    "ComplianceReporter",
    "REGULATIONS",
    "get_regulation",
    # Legacy re-exports (from original compliance.py)
    "ComplianceSummary",
    "get_compliance_summary",
    "get_governance_rules_status",
]

# Re-export legacy functions from _compat.py so existing code continues to work.
# These were previously in specsmith/compliance.py before it became a package.
from specsmith.compliance._compat import (  # noqa: E402
    ComplianceSummary,
    get_compliance_summary,
    get_governance_rules_status,
)


def get_regulation(regulation_id: str) -> Regulation:
    """Return a Regulation by ID (e.g. 'eu-ai-act', 'nist-rmf', 'colorado')."""
    from specsmith.compliance.regulations import REGULATIONS

    reg = REGULATIONS.get(regulation_id)
    if reg is None:
        raise KeyError(
            f"Unknown regulation '{regulation_id}'. "
            f"Valid IDs: {', '.join(REGULATIONS)}"
        )
    return reg
