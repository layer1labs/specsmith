# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""specsmith.epistemic — compatibility shim.

The canonical AEE library now lives in the ``epistemic`` package.
This module re-exports everything for backward compatibility.

    # Preferred (standalone, no specsmith coupling):
    from epistemic import BeliefArtifact, AEESession

    # Also works (same objects, backward-compatible):
    from specsmith.epistemic import BeliefArtifact
"""

from __future__ import annotations

# Re-export the entire epistemic public API
from epistemic import (
    AEEResult,
    AEESession,
    ArtifactCertainty,
    BeliefArtifact,
    BeliefStatus,
    CertaintyEngine,
    CertaintyReport,
    ConfidenceLevel,
    FailureMode,
    FailureModeGraph,
    FailureSeverity,
    GraphNode,
    RecoveryOperator,
    RecoveryProposal,
    RecoveryStrategy,
    StressTester,
    StressTestResult,
    beliefs_from_dicts,
    parse_requirements_as_beliefs,
)

# AEEResult and AEESession already imported via `from epistemic import (...)` above

__all__ = [
    "AEEResult",
    "AEESession",
    "ArtifactCertainty",
    "BeliefArtifact",
    "BeliefStatus",
    "CertaintyEngine",
    "CertaintyReport",
    "ConfidenceLevel",
    "FailureMode",
    "FailureModeGraph",
    "FailureSeverity",
    "GraphNode",
    "RecoveryOperator",
    "RecoveryProposal",
    "RecoveryStrategy",
    "StressTestResult",
    "StressTester",
    "beliefs_from_dicts",
    "parse_requirements_as_beliefs",
]
