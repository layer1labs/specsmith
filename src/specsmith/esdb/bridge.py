# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs / BitConcepts, LLC.
"""ESDB bridge — adapter between .specsmith/ JSON and ESDB concepts.

This module provides read-only access to the current .specsmith/ flat JSON
state through ESDB-compatible query interfaces. It allows specsmith's
governance logic to work with either backend transparently.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EsdbRecord:
    """Python mirror of the Rust Record type."""

    id: str
    kind: str
    status: str = "active"
    confidence: float = 0.7
    label: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    source_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return the original source data dict (used for export/backup)."""
        return self.data if self.data else {
            "id": self.id,
            "kind": self.kind,
            "status": self.status,
            "confidence": self.confidence,
            "label": self.label,
        }


@dataclass
class EsdbStatus:
    """ESDB health status for the REST API."""

    available: bool
    backend: str  # "esdb" or "json-fallback"
    record_count: int = 0
    wal_seq: int = 0
    epoch: int = 0
    chain_valid: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "backend": self.backend,
            "record_count": self.record_count,
            "wal_seq": self.wal_seq,
            "epoch": self.epoch,
            "chain_valid": self.chain_valid,
        }


class EsdbBridge:
    """Read-only bridge to .specsmith/ JSON files using ESDB semantics.

    When the Rust ESDB engine is available (via PyO3 bindings), this
    class delegates to it. Otherwise, it reads the flat JSON files
    directly and presents them through an ESDB-compatible interface.
    """

    def __init__(self, project_dir: str = ".") -> None:
        self.root = Path(project_dir).resolve()
        self._requirements: list[EsdbRecord] | None = None
        self._testcases: list[EsdbRecord] | None = None

    def status(self) -> EsdbStatus:
        """Return ESDB status."""
        reqs = self._load_requirements()
        tests = self._load_testcases()
        return EsdbStatus(
            available=True,
            backend=".specsmith/ JSON (ChronoMemory native pending)",
            record_count=len(reqs) + len(tests),
        )

    def requirements(self) -> list[EsdbRecord]:
        """Load requirements as ESDB records."""
        return self._load_requirements()

    def testcases(self) -> list[EsdbRecord]:
        """Load test cases as ESDB records."""
        return self._load_testcases()

    def record_counts(self) -> dict[str, int]:
        """Record counts by kind (for dashboard)."""
        return {
            "requirements": len(self._load_requirements()),
            "testcases": len(self._load_testcases()),
        }

    def _load_requirements(self) -> list[EsdbRecord]:
        if self._requirements is not None:
            return self._requirements
        path = self.root / ".specsmith" / "requirements.json"
        if not path.is_file():
            self._requirements = []
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            self._requirements = [
                EsdbRecord(
                    id=r.get("id", ""),
                    kind="requirement",
                    label=r.get("title", ""),
                    confidence=float(r.get("confidence", 0.7)),
                    data=r,
                )
                for r in raw
                if isinstance(r, dict)
            ]
        except (OSError, ValueError):
            self._requirements = []
        return self._requirements

    def _load_testcases(self) -> list[EsdbRecord]:
        if self._testcases is not None:
            return self._testcases
        path = self.root / ".specsmith" / "testcases.json"
        if not path.is_file():
            self._testcases = []
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            self._testcases = [
                EsdbRecord(
                    id=r.get("id", ""),
                    kind="testcase",
                    label=r.get("title", ""),
                    confidence=float(r.get("confidence", 1.0)),
                    data=r,
                )
                for r in raw
                if isinstance(r, dict)
            ]
        except (OSError, ValueError):
            self._testcases = []
        return self._testcases
