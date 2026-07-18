import json

import pytest

from specsmith.issue_evidence import IssueEvidenceReport, TestEvidence


def test_strict_evidence_mapping_and_machine_readable_report(tmp_path) -> None:
    record = TestEvidence("#337", "REQ-475", "TEST-501", "passed", "pytest test.py")
    report = IssueEvidenceReport((record,))
    report.validate({"TEST-501"})
    path = tmp_path / "report.json"
    report.write(path)
    assert json.loads(path.read_text())["records"][0]["issue_id"] == "#337"


def test_missing_failed_and_silent_unavailable_evidence_are_rejected() -> None:
    with pytest.raises(ValueError, match="missing"):
        IssueEvidenceReport(()).validate({"TEST-X"})
    with pytest.raises(ValueError, match="failed"):
        IssueEvidenceReport((TestEvidence("#1", "REQ-1", "T", "failed", "pytest"),)).validate({"T"})
    with pytest.raises(ValueError, match="explicit reason"):
        TestEvidence("#1", "REQ-1", "T", "unavailable", "pytest").validate()
