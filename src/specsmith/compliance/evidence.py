# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""ESDB-backed evidence collection for compliance checking.

EvidenceCollector inspects a project's .specsmith/ directory and .chronomemory/
ESDB to gather evidence that governance controls are in place. Evidence is
returned as structured EvidenceItem objects that reference specific files
or ESDB record IDs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Evidence model
# ---------------------------------------------------------------------------


@dataclass
class EvidenceItem:
    """A single piece of evidence supporting a compliance control."""

    control_id: str                     # Regulation article ID (e.g. "Art.9")
    regulation_id: str                  # e.g. "eu-ai-act"
    description: str                    # Human-readable description
    source: str                         # File path, ESDB record ID, or CLI command
    source_type: str                    # "file" | "esdb" | "config" | "cli_output"
    confidence: float = 0.8             # 0.0-1.0
    present: bool = True                # Is the evidence present?
    detail: str = ""                    # Additional detail (e.g. record count)

    def to_dict(self) -> dict[str, Any]:
        return {
            "control_id": self.control_id,
            "regulation_id": self.regulation_id,
            "description": self.description,
            "source": self.source,
            "source_type": self.source_type,
            "confidence": self.confidence,
            "present": self.present,
            "detail": self.detail,
        }


# ---------------------------------------------------------------------------
# Evidence collector
# ---------------------------------------------------------------------------


class EvidenceCollector:
    """Collects compliance evidence from a specsmith-governed project.

    Queries the ChronoStore (when available) and flat .specsmith/ files
    to gather evidence for each regulation control category.
    """

    def __init__(self, project_dir: str | Path) -> None:
        self.root = Path(project_dir).resolve()
        self._esdb_available: bool | None = None
        self._esdb_records: list[Any] | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def collect_all(self) -> list[EvidenceItem]:
        """Collect all evidence items for all regulation categories."""
        items: list[EvidenceItem] = []
        items.extend(self._evidence_logging())
        items.extend(self._evidence_human_oversight())
        items.extend(self._evidence_risk_management())
        items.extend(self._evidence_transparency())
        items.extend(self._evidence_data_governance())
        items.extend(self._evidence_security())
        return items

    def collect_for_regulation(self, regulation_id: str) -> list[EvidenceItem]:
        """Collect evidence items relevant to a specific regulation."""
        all_items = self.collect_all()
        return [i for i in all_items if i.regulation_id in ("*", regulation_id)]

    def esdb_available(self) -> bool:
        """Return True if ChronoStore WAL is present."""
        if self._esdb_available is None:
            self._esdb_available = (
                self.root / ".chronomemory" / "events.wal"
            ).is_file()
        return self._esdb_available

    def esdb_record_count(self) -> int:
        """Count ESDB records."""
        if not self.esdb_available():
            return 0
        try:
            from specsmith.esdb.store import ChronoStore

            with ChronoStore(self.root) as store:
                return store.record_count()
        except Exception:  # noqa: BLE001
            return 0

    def esdb_chain_valid(self) -> bool:
        """Return True if the ESDB WAL chain is intact."""
        if not self.esdb_available():
            return True  # No WAL = no chain to verify
        try:
            from specsmith.esdb.store import ChronoStore

            with ChronoStore(self.root) as store:
                return store.chain_valid()
        except Exception:  # noqa: BLE001
            return False

    def compliance_records_in_esdb(self) -> int:
        """Count compliance_result records stored in ESDB."""
        if not self.esdb_available():
            return 0
        try:
            from specsmith.esdb.store import ChronoStore

            with ChronoStore(self.root) as store:
                return len(store.query(kind="compliance_result"))
        except Exception:  # noqa: BLE001
            return 0

    # ------------------------------------------------------------------
    # Evidence categories
    # ------------------------------------------------------------------

    def _evidence_logging(self) -> list[EvidenceItem]:
        """Evidence for logging / record-keeping controls (EU Art.12, NIST MANAGE-2)."""
        items = []

        # ESDB WAL
        wal = self.root / ".chronomemory" / "events.wal"
        items.append(EvidenceItem(
            control_id="Art.12",
            regulation_id="*",
            description="ChronoStore WAL — tamper-evident append-only event log",
            source=".chronomemory/events.wal",
            source_type="file",
            confidence=0.95 if wal.exists() else 0.0,
            present=wal.exists(),
            detail=f"WAL chain valid: {self.esdb_chain_valid()}" if wal.exists() else "WAL not initialized",
        ))

        # Ledger JSONL
        ledger_jsonl = self.root / ".specsmith" / "ledger.jsonl"
        items.append(EvidenceItem(
            control_id="Art.12",
            regulation_id="*",
            description="Append-only session ledger (JSONL)",
            source=".specsmith/ledger.jsonl",
            source_type="file",
            confidence=0.9 if ledger_jsonl.exists() else 0.0,
            present=ledger_jsonl.exists(),
        ))

        # Trace vault
        trace = self.root / ".specsmith" / "trace.jsonl"
        items.append(EvidenceItem(
            control_id="Art.12",
            regulation_id="*",
            description="SHA-256 chained trace vault (decision seals)",
            source=".specsmith/trace.jsonl",
            source_type="file",
            confidence=0.9 if trace.exists() else 0.1,
            present=trace.exists(),
        ))

        # LEDGER.md (human-readable view)
        ledger_md = (
            (self.root / "docs" / "LEDGER.md")
            if (self.root / "docs" / "LEDGER.md").exists()
            else (self.root / "LEDGER.md")
        )
        items.append(EvidenceItem(
            control_id="MANAGE-2",
            regulation_id="*",
            description="Human-readable LEDGER.md (session records)",
            source=str(ledger_md.relative_to(self.root)) if ledger_md.exists() else "LEDGER.md",
            source_type="file",
            confidence=0.8 if ledger_md.exists() else 0.0,
            present=ledger_md.exists(),
        ))

        return items

    def _evidence_human_oversight(self) -> list[EvidenceItem]:
        """Evidence for human oversight controls (EU Art.14, NIST MANAGE-1)."""
        items = []

        # Kill switch: specsmith kill-session command exists
        items.append(EvidenceItem(
            control_id="Art.14",
            regulation_id="*",
            description="Kill-switch (specsmith kill-session) halts all agent sessions",
            source="specsmith kill-session CLI command",
            source_type="cli_output",
            confidence=0.9,
            present=True,  # Always available as a CLI command
        ))

        # Config: escalation threshold
        config = self.root / ".specsmith" / "config.yml"
        has_escalation = False
        if config.exists():
            try:
                import yaml
                raw = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
                has_escalation = bool(
                    raw.get("epistemic", {}).get("confidence_threshold")
                )
            except Exception:  # noqa: BLE001
                pass

        items.append(EvidenceItem(
            control_id="Art.14",
            regulation_id="*",
            description="Escalation threshold configured in .specsmith/config.yml",
            source=".specsmith/config.yml",
            source_type="config",
            confidence=0.85 if has_escalation else 0.4,
            present=has_escalation,
            detail="epistemic.confidence_threshold is set" if has_escalation else "not configured",
        ))

        # Permission profiles
        items.append(EvidenceItem(
            control_id="Art.14",
            regulation_id="*",
            description="Permission profiles (read_only/standard/extended/admin)",
            source="specsmith agent permissions CLI command",
            source_type="cli_output",
            confidence=0.9,
            present=True,
        ))

        # Preflight gate
        items.append(EvidenceItem(
            control_id="Art.14",
            regulation_id="*",
            description="Preflight gate: all governed actions require human approval",
            source="specsmith preflight CLI command",
            source_type="cli_output",
            confidence=0.95,
            present=True,
        ))

        return items

    def _evidence_risk_management(self) -> list[EvidenceItem]:
        """Evidence for risk management controls (EU Art.9, NIST GOVERN/MAP/MEASURE)."""
        items = []

        # Requirements exist
        req_path = (
            (self.root / "docs" / "REQUIREMENTS.md")
            if (self.root / "docs" / "REQUIREMENTS.md").exists()
            else (self.root / "REQUIREMENTS.md")
        )
        items.append(EvidenceItem(
            control_id="Art.9",
            regulation_id="*",
            description="Requirements documentation (risk identification)",
            source=str(req_path.relative_to(self.root)) if req_path.exists() else "docs/REQUIREMENTS.md",
            source_type="file",
            confidence=0.85 if req_path.exists() else 0.0,
            present=req_path.exists(),
        ))

        # Governance rules
        rules_yaml = self.root / ".specsmith" / "governance" / "rules.yaml"
        rules_md = self.root / "docs" / "governance" / "RULES.md"
        has_rules = rules_yaml.exists() or rules_md.exists()
        rules_src = (
            ".specsmith/governance/rules.yaml" if rules_yaml.exists()
            else "docs/governance/RULES.md" if rules_md.exists()
            else "not found"
        )
        items.append(EvidenceItem(
            control_id="GOVERN-1",
            regulation_id="*",
            description="Governance rules (H1-H22) — risk management policies",
            source=rules_src,
            source_type="file",
            confidence=0.9 if has_rules else 0.0,
            present=has_rules,
        ))

        # ESDB confidence scoring
        esdb_count = self.esdb_record_count()
        items.append(EvidenceItem(
            control_id="MEASURE-1",
            regulation_id="*",
            description="ESDB records with confidence scoring (ChronoStore)",
            source=".chronomemory/events.wal",
            source_type="esdb",
            confidence=0.9 if esdb_count > 0 else 0.3,
            present=esdb_count > 0,
            detail=f"{esdb_count} records" if esdb_count > 0 else "0 records (run: specsmith esdb migrate)",
        ))

        # scaffold.yml / SPECSMITH.yml
        scaffold_present = (
            (self.root / "docs" / "SPECSMITH.yml").exists()
            or (self.root / "scaffold.yml").exists()
        )
        items.append(EvidenceItem(
            control_id="GOVERN-1",
            regulation_id="*",
            description="Project governance configuration (scaffold.yml / SPECSMITH.yml)",
            source="scaffold.yml or docs/SPECSMITH.yml",
            source_type="file",
            confidence=0.9 if scaffold_present else 0.0,
            present=scaffold_present,
        ))

        return items

    def _evidence_transparency(self) -> list[EvidenceItem]:
        """Evidence for transparency controls (EU Art.13/52, Colorado Sec.6(2)(a))."""
        items = []

        # AI disclosure field in preflight
        items.append(EvidenceItem(
            control_id="Art.13",
            regulation_id="*",
            description="ai_disclosure field in every preflight response (provider + model)",
            source="specsmith preflight --json (ai_disclosure key)",
            source_type="cli_output",
            confidence=0.95,
            present=True,
        ))

        # AGENTS.md governance hub
        agents_md = self.root / "AGENTS.md"
        items.append(EvidenceItem(
            control_id="Art.52",
            regulation_id="*",
            description="AGENTS.md — governance hub (agent instructions + specsmith delegation)",
            source="AGENTS.md",
            source_type="file",
            confidence=0.85 if agents_md.exists() else 0.0,
            present=agents_md.exists(),
        ))

        # Architecture doc
        arch = self.root / "docs" / "ARCHITECTURE.md"
        items.append(EvidenceItem(
            control_id="Art.13",
            regulation_id="*",
            description="System architecture documentation (capabilities/limitations)",
            source="docs/ARCHITECTURE.md",
            source_type="file",
            confidence=0.85 if arch.exists() else 0.0,
            present=arch.exists(),
        ))

        return items

    def _evidence_data_governance(self) -> list[EvidenceItem]:
        """Evidence for data governance / anti-discrimination controls."""
        items = []

        # source_type tagging in ESDB
        items.append(EvidenceItem(
            control_id="MEASURE-2",
            regulation_id="*",
            description="ESDB records tagged with source_type (observed/synthetic) per H19",
            source=".chronomemory/events.wal (ChronoRecord.source_type field)",
            source_type="esdb",
            confidence=0.9 if self.esdb_available() else 0.2,
            present=self.esdb_available(),
            detail=(
                "ChronoStore records carry source_type field per REQ-310 / H19"
                if self.esdb_available()
                else "ESDB not initialized — run: specsmith esdb migrate"
            ),
        ))

        # Validate strict runs in CI
        ci_path = self.root / ".github" / "workflows"
        ci_has_validate = False
        if ci_path.is_dir():
            for yml in ci_path.glob("*.yml"):
                try:
                    content = yml.read_text(encoding="utf-8")
                    if "validate --strict" in content:
                        ci_has_validate = True
                        break
                except Exception:  # noqa: BLE001
                    pass

        items.append(EvidenceItem(
            control_id="MEASURE-2",
            regulation_id="*",
            description="specsmith validate --strict runs in CI (data quality gate)",
            source=".github/workflows/ci.yml",
            source_type="config",
            confidence=0.9 if ci_has_validate else 0.3,
            present=ci_has_validate,
        ))

        return items

    def _evidence_security(self) -> list[EvidenceItem]:
        """Evidence for security / robustness controls (EU Art.15, NIST)."""
        items = []

        # cargo audit / pip-audit in CI
        ci_path = self.root / ".github" / "workflows"
        has_security_scan = False
        if ci_path.is_dir():
            for yml in ci_path.glob("*.yml"):
                try:
                    content = yml.read_text(encoding="utf-8")
                    if "pip-audit" in content or "cargo audit" in content:
                        has_security_scan = True
                        break
                except Exception:  # noqa: BLE001
                    pass

        items.append(EvidenceItem(
            control_id="Art.15",
            regulation_id="*",
            description="Dependency security scan in CI (pip-audit / cargo audit)",
            source=".github/workflows/ci.yml",
            source_type="config",
            confidence=0.9 if has_security_scan else 0.2,
            present=has_security_scan,
        ))

        # Trace chain integrity
        items.append(EvidenceItem(
            control_id="Art.15",
            regulation_id="*",
            description="Tamper detection via SHA-256 WAL chain (specsmith trace verify)",
            source="specsmith trace verify + ChronoStore chain_valid()",
            source_type="cli_output",
            confidence=0.9 if self.esdb_available() else 0.5,
            present=True,
            detail=(
                f"Chain valid: {self.esdb_chain_valid()}"
                if self.esdb_available()
                else "ESDB not initialized"
            ),
        ))

        return items
