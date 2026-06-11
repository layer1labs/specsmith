# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Belief Artifact model — core AEE primitive.

This module is part of the standalone ``epistemic`` library and has
**zero dependencies outside Python's stdlib**. It can be imported by any
Python 3.10+ project, independent of specsmith.

    pip install specsmith       # installs both specsmith and epistemic
    from epistemic import BeliefArtifact, StressTester, CertaintyEngine

Applied Epistemic Engineering (AEE) treats belief systems like code:
codable, testable, and deployable. A BeliefArtifact is the fundamental
unit — a structured claim about what a system does, should do, or must not
do, with an explicit epistemic boundary (the assumptions within which it holds)
and a confidence level.

Five foundational AEE axioms
-----------------------------
1. Observability      — Every belief must be inspectable. Hidden assumptions
                        are a stop condition.
2. Falsifiability     — Every belief must be challengeable. Unchallenged claims
                        are dogma, not engineering.
3. Irreducibility     — Decompose beliefs to atomic primitives. Compound claims
                        often hide Logic Knots.
4. Reconstructability — Every failed belief can be reconstructed. Recovery is
                        always possible; scope may need to narrow.
5. Convergence        — Systematic S+R application always converges to an
                        Equilibrium Point E where S(G) yields no new failures.

Real-world applications
-----------------------
- **Software engineering**: Requirements as BeliefArtifacts, test gaps as
  stress-test failures, conflicting specs as Logic Knots.
- **Research**: Hypotheses as BeliefArtifacts, experimental results as
  evidence, competing theories as Logic Knots.
- **AI alignment**: Model assumptions as BeliefArtifacts, red-teaming as
  stress-testing, hallucinations as confidence failures.
- **Policy / compliance**: Regulatory claims as BeliefArtifacts, audit
  findings as failure modes, contradictory requirements as Logic Knots.

References
----------
- AEE: https://appliedepistemicengineering.com/
- ARE framework: https://github.com/organvm-i-theoria/auto-revision-epistemic-engine
- VERITAS/CERTUS: https://github.com/AionSystem/VERITAS
- AI as Epistemic Technology (Springer): https://doi.org/10.1007/s11948-023-00451-3
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ConfidenceLevel(str, Enum):
    """Epistemic confidence assigned to a BeliefArtifact.

    Maps to a numeric score used by CertaintyEngine:
      UNKNOWN  → 0.0   (no evidence, new claim)
      LOW      → 0.25  (asserted but not stress-tested)
      MEDIUM   → 0.55  (stress-tested with minor failures resolved)
      HIGH     → 0.85  (stress-tested, equilibrium reached, evidence present)
    """

    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def score(self) -> float:
        """Numeric score for propagation calculations."""
        return _CONFIDENCE_SCORES[self]


_CONFIDENCE_SCORES: dict[ConfidenceLevel, float] = {
    ConfidenceLevel.UNKNOWN: 0.0,
    ConfidenceLevel.LOW: 0.25,
    ConfidenceLevel.MEDIUM: 0.55,
    ConfidenceLevel.HIGH: 0.85,
}


class BeliefStatus(str, Enum):
    """Lifecycle status of a BeliefArtifact."""

    DRAFT = "draft"
    ACCEPTED = "accepted"
    STRESS_TESTED = "stress-tested"
    RECONSTRUCTED = "reconstructed"
    DEPRECATED = "deprecated"


class FailureSeverity(str, Enum):
    """Severity of a failure mode in the Failure-Mode Graph."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class FailureMode:
    """A single failure mode discovered by the StressTester.

    Represents a stress-test → breakpoint relation in the Failure-Mode Graph G.
    """

    artifact_id: str
    challenge: str
    breakpoint: str
    severity: FailureSeverity = FailureSeverity.MEDIUM
    recovery_hint: str = ""
    resolved: bool = False


@dataclass
class BeliefArtifact:
    """A codable, testable, deployable unit of knowledge.

    The fundamental unit of AEE. Can represent:
    - A software requirement (REQ-CLI-001)
    - A research hypothesis (HYP-IND-001)
    - An architectural decision (DEC-001)
    - A compliance claim (COMP-GDPR-001)
    - Any structured belief that must be Observable and Falsifiable

    Examples
    --------
    Software requirement::

        req = BeliefArtifact(
            artifact_id="REQ-API-001",
            propositions=["The API must return HTTP 200 for valid requests"],
            epistemic_boundary=["Platform: all", "Auth: JWT required"],
            confidence=ConfidenceLevel.ACCEPTED,
            status=BeliefStatus.ACCEPTED,
        )

    Research hypothesis::

        hyp = BeliefArtifact(
            artifact_id="HYP-IND-001",
            propositions=["Indus script uses logosyllabic encoding",
                          "Sign frequency distribution follows Zipf's law"],
            epistemic_boundary=["Corpus: Mahadevan 2977 inscriptions, 1977"],
            confidence=ConfidenceLevel.LOW,
            status=BeliefStatus.ACCEPTED,
        )
    """

    artifact_id: str
    propositions: list[str] = field(default_factory=list)
    epistemic_boundary: list[str] = field(default_factory=list)
    inferential_links: list[str] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    status: BeliefStatus = BeliefStatus.DRAFT
    failure_modes: list[FailureMode] = field(default_factory=list)
    source_text: str = ""
    component: str = ""
    priority: str = ""
    # Optional metadata for non-specsmith uses
    domain: str = ""  # e.g., "linguistics", "software", "policy"
    evidence: list[str] = field(default_factory=list)  # evidence citations

    @property
    def is_accepted(self) -> bool:
        return self.status in (
            BeliefStatus.ACCEPTED,
            BeliefStatus.STRESS_TESTED,
            BeliefStatus.RECONSTRUCTED,
        )

    @property
    def has_failures(self) -> bool:
        return any(not fm.resolved for fm in self.failure_modes)

    @property
    def unresolved_failures(self) -> list[FailureMode]:
        return [fm for fm in self.failure_modes if not fm.resolved]

    @property
    def critical_failures(self) -> list[FailureMode]:
        return [
            fm
            for fm in self.failure_modes
            if not fm.resolved and fm.severity == FailureSeverity.CRITICAL
        ]

    def add_evidence(self, citation: str) -> BeliefArtifact:
        """Add an evidence citation and elevate confidence if appropriate.

        Returns self for chaining.
        """
        self.evidence.append(citation)
        if self.confidence == ConfidenceLevel.UNKNOWN and self.evidence:
            self.confidence = ConfidenceLevel.LOW
        return self

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dict (JSON-compatible)."""
        return {
            "artifact_id": self.artifact_id,
            "propositions": self.propositions,
            "epistemic_boundary": self.epistemic_boundary,
            "inferential_links": self.inferential_links,
            "confidence": self.confidence.value,
            "status": self.status.value,
            "source_text": self.source_text,
            "component": self.component,
            "priority": self.priority,
            "domain": self.domain,
            "evidence": self.evidence,
            "failure_count": len(self.failure_modes),
            "critical_count": len(self.critical_failures),
        }


# ---------------------------------------------------------------------------
# Markdown parser — converts REQUIREMENTS.md entries to BeliefArtifacts
# ---------------------------------------------------------------------------

_REQ_HEADING = re.compile(r"^#{1,3}\s+(REQ-([A-Z0-9_]+)-(\d+))\s*(?:—\s*(.+))?$")
_FIELD_LINE = re.compile(r"^\s*-\s+\*\*(.+?)\*\*:\s*(.+)$")


def parse_requirements_as_beliefs(path: Path) -> list[BeliefArtifact]:
    """Parse a REQUIREMENTS.md file and return a list of BeliefArtifacts.

    Works with both specsmith-generated REQUIREMENTS.md files and
    any markdown file that uses REQ-COMPONENT-NNN heading format.
    """
    if not path.exists():
        return []

    content = path.read_text(encoding="utf-8")
    artifacts: list[BeliefArtifact] = []
    current: BeliefArtifact | None = None
    current_desc = ""

    for line in content.splitlines():
        m = _REQ_HEADING.match(line)
        if m:
            if current is not None:
                _finalise(current, current_desc)
                artifacts.append(current)
            req_id = m.group(1)
            component = m.group(2)
            desc_inline = m.group(4) or ""
            current = BeliefArtifact(
                artifact_id=req_id,
                component=component,
                source_text=desc_inline,
            )
            current_desc = desc_inline
            continue

        if current is None:
            continue

        fm = _FIELD_LINE.match(line)
        if fm:
            key = fm.group(1).lower()
            val = fm.group(2).strip()
            if key in ("description", "desc"):
                current_desc = val
                current.source_text = val
            elif key == "priority":
                current.priority = val
            elif key == "status":
                current.status = _map_status(val)
                current.confidence = _infer_confidence(current.status)
            elif key in ("platform", "platforms", "boundary"):
                current.epistemic_boundary.append(f"{key.capitalize()}: {val}")
            elif key == "domain":
                current.domain = val
            elif key == "evidence":
                current.evidence.append(val)
        else:
            stripped = line.strip().lstrip("-").strip()
            if stripped and not stripped.startswith("#") and not current_desc:
                current_desc = stripped

    if current is not None:
        _finalise(current, current_desc)
        artifacts.append(current)

    return artifacts


def beliefs_from_dicts(data: list[dict[str, object]]) -> list[BeliefArtifact]:
    """Construct BeliefArtifacts from a list of plain dicts.

    Useful when loading from JSON, YAML, or a database::

        import yaml
        data = yaml.safe_load(open("hypotheses.yml"))
        artifacts = beliefs_from_dicts(data["beliefs"])
    """
    artifacts = []
    for d in data:
        a = BeliefArtifact(
            artifact_id=str(d.get("artifact_id", "")),
            propositions=list(d.get("propositions", [])),  # type: ignore[arg-type]
            epistemic_boundary=list(d.get("epistemic_boundary", [])),  # type: ignore[arg-type]
            inferential_links=list(d.get("inferential_links", [])),  # type: ignore[arg-type]
            confidence=ConfidenceLevel(d.get("confidence", "unknown")),
            status=BeliefStatus(d.get("status", "draft")),
            source_text=str(d.get("source_text", "")),
            component=str(d.get("component", "")),
            priority=str(d.get("priority", "")),
            domain=str(d.get("domain", "")),
            evidence=list(d.get("evidence", [])),  # type: ignore[arg-type]
        )
        artifacts.append(a)
    return artifacts


def _finalise(artifact: BeliefArtifact, desc: str) -> None:
    if not desc:
        return
    artifact.source_text = artifact.source_text or desc
    parts = re.split(r";|\band\b(?=\s+[A-Z])", desc)
    artifact.propositions = artifact.propositions or [p.strip() for p in parts if p.strip()]
    if not artifact.epistemic_boundary:
        artifact.epistemic_boundary = ["Assumed correct project environment"]


def _map_status(val: str) -> BeliefStatus:
    val_lower = val.lower()
    if "accept" in val_lower:
        return BeliefStatus.ACCEPTED
    if "stress" in val_lower:
        return BeliefStatus.STRESS_TESTED
    if "reconstruct" in val_lower:
        return BeliefStatus.RECONSTRUCTED
    if "deprecat" in val_lower:
        return BeliefStatus.DEPRECATED
    return BeliefStatus.DRAFT


def _infer_confidence(status: BeliefStatus) -> ConfidenceLevel:
    return {
        BeliefStatus.DRAFT: ConfidenceLevel.UNKNOWN,
        BeliefStatus.ACCEPTED: ConfidenceLevel.LOW,
        BeliefStatus.STRESS_TESTED: ConfidenceLevel.MEDIUM,
        BeliefStatus.RECONSTRUCTED: ConfidenceLevel.HIGH,
        BeliefStatus.DEPRECATED: ConfidenceLevel.LOW,
    }.get(status, ConfidenceLevel.UNKNOWN)


__all__ = [
    "BeliefArtifact",
    "BeliefStatus",
    "ConfidenceLevel",
    "FailureMode",
    "FailureSeverity",
    "parse_requirements_as_beliefs",
    "beliefs_from_dicts",
]
