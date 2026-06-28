from __future__ import annotations

import json
from pathlib import Path

from specsmith.auditor import check_governance_yaml_content, check_req_test_consistency


def test_check_governance_yaml_content_fails_on_empty_rules_list(tmp_path: Path) -> None:
    gov_dir = tmp_path / ".specsmith" / "governance"
    gov_dir.mkdir(parents=True)
    (gov_dir / "rules.yaml").write_text("rules: []\n", encoding="utf-8")

    results = check_governance_yaml_content(tmp_path)

    assert len(results) == 1
    assert results[0].name == "governance-yaml:rules"
    assert not results[0].passed
    assert "empty 'rules' list" in results[0].message


def test_check_governance_yaml_content_fails_on_note_only_fallback(tmp_path: Path) -> None:
    gov_dir = tmp_path / ".specsmith" / "governance"
    gov_dir.mkdir(parents=True)
    (gov_dir / "rules.yaml").write_text(
        "rules:\n  - note: Could not parse rules — see source MD\n",
        encoding="utf-8",
    )

    results = check_governance_yaml_content(tmp_path)

    assert len(results) == 1
    assert results[0].name == "governance-yaml:rules"
    assert not results[0].passed
    assert "fallback note" in results[0].message


def test_check_governance_yaml_content_passes_with_real_entries(tmp_path: Path) -> None:
    gov_dir = tmp_path / ".specsmith" / "governance"
    gov_dir.mkdir(parents=True)
    (gov_dir / "rules.yaml").write_text(
        "rules:\n"
        "  - id: H1\n"
        "    name: Parse Inputs\n"
        "    description: Validate and normalize user input.\n",
        encoding="utf-8",
    )

    results = check_governance_yaml_content(tmp_path)

    assert len(results) == 1
    assert results[0].name == "governance-yaml:rules"
    assert results[0].passed


def test_check_governance_yaml_content_noop_when_governance_dir_missing(tmp_path: Path) -> None:
    results = check_governance_yaml_content(tmp_path)

    assert results == []


def test_check_governance_yaml_content_passes_m001_content_blob(tmp_path: Path) -> None:
    """m001 content-blob files (content + kind keys) should pass the check."""
    gov_dir = tmp_path / ".specsmith" / "governance"
    gov_dir.mkdir(parents=True)
    (gov_dir / "axioms.yaml").write_text(
        "content: '# Epistemic Axioms\\nAxiom 1: Observability\\n'\n"
        "generated_by: specsmith migrate (m001)\n"
        "kind: axioms\n"
        "source_md: docs/governance/EPISTEMIC-AXIOMS.md\n",
        encoding="utf-8",
    )

    results = check_governance_yaml_content(tmp_path)

    assert len(results) == 1
    assert results[0].name == "governance-yaml:axioms"
    assert results[0].passed, results[0].message
    assert "m001 content-blob" in results[0].message


def test_req_test_consistency_fails_with_zero_testcases_json_only(tmp_path: Path) -> None:
    state_dir = tmp_path / ".specsmith"
    state_dir.mkdir(parents=True)
    (state_dir / "requirements.json").write_text(
        json.dumps(
            [
                {"id": "REQ-001"},
                {"id": "REQ-002"},
            ]
        ),
        encoding="utf-8",
    )
    (state_dir / "testcases.json").write_text("[]", encoding="utf-8")

    results = check_req_test_consistency(tmp_path)
    coverage = [r for r in results if r.name == "req-test-coverage"]

    assert len(coverage) == 1
    assert not coverage[0].passed
    assert "REQ-001" in coverage[0].message
    assert "REQ-002" in coverage[0].message
