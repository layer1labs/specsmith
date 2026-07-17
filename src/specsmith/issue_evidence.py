"""Strict machine-readable issue/requirement/test evidence reports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class TestEvidence:
    __test__ = False

    issue_id: str
    requirement_id: str
    test_id: str
    status: str
    command: str
    detail: str = ""

    def validate(self) -> None:
        if self.status not in {"passed", "failed", "unavailable"}:
            raise ValueError(f"invalid binary evidence status: {self.status}")
        if not all((self.issue_id, self.requirement_id, self.test_id, self.command)):
            raise ValueError("issue evidence is missing traceability fields")
        if self.status == "unavailable" and not self.detail:
            raise ValueError("unavailable evidence requires an explicit reason")


@dataclass(frozen=True)
class IssueEvidenceReport:
    records: tuple[TestEvidence, ...]

    def validate(self, required_test_ids: set[str]) -> None:
        for record in self.records:
            record.validate()
        found = {record.test_id for record in self.records}
        missing = sorted(required_test_ids - found)
        if missing:
            raise ValueError(f"missing test evidence: {', '.join(missing)}")
        failed = sorted(record.test_id for record in self.records if record.status == "failed")
        if failed:
            raise ValueError(f"failed test evidence: {', '.join(failed)}")

    def write(self, path: Path) -> None:
        payload = {
            "schema": "specsmith-issue-evidence-v1",
            "records": [asdict(r) for r in self.records],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
