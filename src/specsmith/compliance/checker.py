# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Per-regulation compliance checking against collected evidence.

ComplianceChecker runs each regulation's articles against the evidence
collected by EvidenceCollector and returns structured ComplianceResult
objects with status, findings, and evidence references.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from specsmith.compliance.evidence import EvidenceCollector, EvidenceItem
from specsmith.compliance.regulations import REGULATIONS, Article, Regulation

# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    """A single compliance finding (gap or confirmation)."""

    article_id: str
    severity: str  # "gap" | "partial" | "compliant" | "n_a"
    message: str
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "article_id": self.article_id,
            "severity": self.severity,
            "message": self.message,
            "recommendation": self.recommendation,
        }


@dataclass
class ArticleResult:
    """Compliance result for one article/control."""

    article_id: str
    title: str
    status: str  # "compliant" | "partial" | "gap" | "n_a"
    confidence: float  # aggregate evidence confidence
    findings: list[Finding] = field(default_factory=list)
    evidence: list[EvidenceItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "article_id": self.article_id,
            "title": self.title,
            "status": self.status,
            "confidence": round(self.confidence, 3),
            "findings": [f.to_dict() for f in self.findings],
            "evidence_count": len(self.evidence),
        }


@dataclass
class ComplianceResult:
    """Full compliance check result for one regulation."""

    regulation_id: str
    regulation_name: str
    jurisdiction: str
    checked_at: str  # ISO-8601 timestamp
    overall_status: str  # "compliant" | "partial" | "gap" | "n_a"
    overall_confidence: float
    article_results: list[ArticleResult] = field(default_factory=list)
    project_dir: str = ""
    notes: str = ""

    @property
    def gap_count(self) -> int:
        return sum(1 for a in self.article_results if a.status == "gap")

    @property
    def partial_count(self) -> int:
        return sum(1 for a in self.article_results if a.status == "partial")

    @property
    def compliant_count(self) -> int:
        return sum(1 for a in self.article_results if a.status == "compliant")

    def to_dict(self) -> dict[str, Any]:
        return {
            "regulation_id": self.regulation_id,
            "regulation_name": self.regulation_name,
            "jurisdiction": self.jurisdiction,
            "checked_at": self.checked_at,
            "overall_status": self.overall_status,
            "overall_confidence": round(self.overall_confidence, 3),
            "compliant": self.compliant_count,
            "partial": self.partial_count,
            "gaps": self.gap_count,
            "n_a": sum(1 for a in self.article_results if a.status == "n_a"),
            "article_results": [a.to_dict() for a in self.article_results],
            "project_dir": self.project_dir,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------


class ComplianceChecker:
    """Runs compliance checks for one or more regulations."""

    # Minimum evidence confidence to consider an article "compliant"
    _COMPLIANT_THRESHOLD = 0.75
    # Minimum confidence to consider "partial" (below is "gap")
    _PARTIAL_THRESHOLD = 0.35

    def __init__(self, project_dir: str | Path) -> None:
        self.root = Path(project_dir).resolve()
        self._collector = EvidenceCollector(project_dir)
        self._all_evidence: list[EvidenceItem] | None = None

    def _get_evidence(self) -> list[EvidenceItem]:
        if self._all_evidence is None:
            self._all_evidence = self._collector.collect_all()
        return self._all_evidence

    def check_all(self) -> list[ComplianceResult]:
        """Run checks for all regulations."""
        return [self.check_regulation(reg_id) for reg_id in REGULATIONS]

    def check_regulation(self, regulation_id: str) -> ComplianceResult:
        """Run compliance check for a single regulation."""
        if regulation_id not in REGULATIONS:
            raise KeyError(f"Unknown regulation: {regulation_id}")

        reg = REGULATIONS[regulation_id]
        evidence = self._get_evidence()
        checked_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        article_results: list[ArticleResult] = []
        for article in reg.articles:
            article_result = self._check_article(article, evidence, reg)
            article_results.append(article_result)

        # Aggregate overall status
        if not article_results:
            overall_status = "n_a"
            overall_confidence = 1.0
        else:
            non_na = [a for a in article_results if a.status != "n_a"]
            if not non_na:
                overall_status = "n_a"
                overall_confidence = 1.0
            else:
                overall_confidence = sum(a.confidence for a in non_na) / len(non_na)
                if all(a.status == "compliant" for a in non_na):
                    overall_status = "compliant"
                elif any(a.status == "gap" for a in non_na):
                    overall_status = "gap"
                else:
                    overall_status = "partial"

        return ComplianceResult(
            regulation_id=regulation_id,
            regulation_name=reg.name,
            jurisdiction=reg.jurisdiction,
            checked_at=checked_at,
            overall_status=overall_status,
            overall_confidence=overall_confidence,
            article_results=article_results,
            project_dir=str(self.root),
            notes=reg.notes,
        )

    def _check_article(
        self,
        article: Article,
        all_evidence: list[EvidenceItem],
        reg: Regulation,
    ) -> ArticleResult:
        """Check a single article against the collected evidence."""
        # Match evidence items by control_id
        relevant = [e for e in all_evidence if e.control_id == article.id]

        if not relevant:
            # No direct evidence — use indirect category-based evidence
            relevant = self._find_indirect_evidence(article, all_evidence)

        findings: list[Finding] = []

        if not relevant:
            # No evidence at all
            findings.append(
                Finding(
                    article_id=article.id,
                    severity="gap",
                    message=f"No evidence found for {article.id}: {article.title}",
                    recommendation=(
                        f"Implement: {', '.join(article.specsmith_controls[:2])}"
                        if article.specsmith_controls
                        else "Review regulation requirements and implement governance controls."
                    ),
                )
            )
            return ArticleResult(
                article_id=article.id,
                title=article.title,
                status="gap",
                confidence=0.0,
                findings=findings,
                evidence=relevant,
            )

        # Calculate aggregate confidence from present evidence
        present = [e for e in relevant if e.present]
        absent = [e for e in relevant if not e.present]

        avg_confidence = 0.0 if not present else sum(e.confidence for e in present) / len(present)

        # Generate findings for absent evidence
        for ev in absent:
            findings.append(
                Finding(
                    article_id=article.id,
                    severity="gap",
                    message=f"Missing: {ev.description}",
                    recommendation=f"Enable: {ev.source}",
                )
            )

        # Determine status
        if avg_confidence >= self._COMPLIANT_THRESHOLD and not absent:
            status = "compliant"
        elif avg_confidence >= self._PARTIAL_THRESHOLD or (present and absent):
            status = "partial"
            if absent:
                findings.append(
                    Finding(
                        article_id=article.id,
                        severity="partial",
                        message=f"{len(present)}/{len(relevant)} evidence items present",
                        recommendation=(f"Complete: {', '.join(e.source for e in absent[:2])}"),
                    )
                )
        else:
            status = "gap"

        return ArticleResult(
            article_id=article.id,
            title=article.title,
            status=status,
            confidence=avg_confidence,
            findings=findings,
            evidence=relevant,
        )

    def _find_indirect_evidence(
        self,
        article: Article,
        all_evidence: list[EvidenceItem],
    ) -> list[EvidenceItem]:
        """Find evidence by category when no direct article match exists."""
        category_map: dict[str, list[str]] = {
            "logging": ["Art.12", "MANAGE-2"],
            "human_oversight": ["Art.14", "MANAGE-1"],
            "risk_management": ["Art.9", "GOVERN-1", "MAP-1", "MEASURE-1"],
            "transparency": ["Art.13", "Art.52", "GOVERN-2"],
            "discrimination": ["MEASURE-2"],
            "security": ["Art.15"],
        }

        target_controls = category_map.get(article.category, [])
        return [e for e in all_evidence if e.control_id in target_controls]

    def store_results_to_esdb(self, results: list[ComplianceResult]) -> int:
        """Store compliance check results to ChronoStore ESDB.

        Returns the number of records written.
        """
        wal = self.root / ".chronomemory" / "events.wal"
        if not wal.exists():
            return 0  # ESDB not initialized — skip silently

        try:
            from specsmith.esdb.store import ChronoRecord, ChronoStore

            written = 0
            with ChronoStore(self.root) as store:
                for result in results:
                    record = ChronoRecord(
                        id=f"compliance-{result.regulation_id}-{result.checked_at}",
                        kind="compliance_result",
                        label=f"{result.regulation_name} compliance check",
                        status="active",
                        confidence=result.overall_confidence,
                        source_type="observed",
                        evidence=[f"checked_at:{result.checked_at}"],
                        data=result.to_dict(),
                        is_hypothesis=False,
                    )
                    store.upsert(record)
                    written += 1

            return written
        except Exception:  # noqa: BLE001
            return 0
