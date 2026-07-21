# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Focused tests for broker scope-threshold behavior."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "utterance",
    [
        (
            "Remove Dependabot configuration and enforce the approved main-only "
            "GitHub branch model while preserving full commit-pinned private CI actions."
        ),
        "Please configure repository branch protection",
        "Could you replace the stale workflow?",
        (
            "Finish cross-repository evidence-chain documentation, regenerate governed "
            "documents, and run validation checks"
        ),
        (
            "Harden deterministic private documentation packaging and align customer "
            "candidate version metadata"
        ),
        (
            "Require two uniquely identified KR260 boards and hash-bound raw lab "
            "evidence in the physical acceptance release gate"
        ),
        "Compress the governance ledger below its configured context budget",
        "I need you to ensure repository policy and documentation stay aligned",
        "You must regenerate the governed configuration",
    ],
)
def test_explicit_mutation_requests_are_not_read_only(utterance: str) -> None:
    """Regression for #357: imperative edits must enter governance."""
    from specsmith.agent.broker import Intent, classify_intent

    assert classify_intent(utterance) in {Intent.CHANGE, Intent.DESTRUCTIVE}


def test_informational_removal_question_remains_read_only() -> None:
    from specsmith.agent.broker import Intent, classify_intent

    assert classify_intent("How do I remove a stale workflow?") == Intent.READ_ONLY_ASK


@pytest.mark.parametrize(
    "utterance",
    [
        "How should I harden the release workflow?",
        "What does requiring two boards protect against?",
        "Explain how to compress the governance ledger",
    ],
)
def test_informational_mutation_questions_remain_read_only(utterance: str) -> None:
    from specsmith.agent.broker import Intent, classify_intent

    assert classify_intent(utterance) == Intent.READ_ONLY_ASK


def test_issue_357_explicit_test_ids_are_deduplicated(tmp_path: Path) -> None:
    import json

    from specsmith.governance_logic import run_preflight

    spec_dir = tmp_path / ".specsmith"
    spec_dir.mkdir()
    (spec_dir / "requirements.json").write_text(
        json.dumps(
            [
                {
                    "id": "REQ-057",
                    "title": "Deterministic documentation packaging",
                    "description": "Documentation packaging and candidate metadata stay aligned.",
                    "status": "implemented",
                }
            ]
        ),
        encoding="utf-8",
    )
    (spec_dir / "testcases.json").write_text(
        json.dumps(
            [
                {
                    "id": "TEST-057",
                    "requirement_id": "REQ-057",
                    "title": "Documentation packaging metadata",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = run_preflight(
        "Harden deterministic documentation packaging REQ-057 TEST-057 TEST-057",
        project_dir=str(tmp_path),
        predict_only=True,
    )

    assert result["intent"] == "change"
    assert result["decision"] == "accepted"
    assert result["requirement_ids"] == ["REQ-057"]
    assert result["test_case_ids"] == ["TEST-057"]


def _write_requirements(path: Path) -> None:
    path.write_text(
        "# Requirements\n\n"
        "## 1. Cleanup Flow Resilience\n"
        "- **ID:** REQ-200\n"
        "- **Title:** Cleanup flow resilience and validation strategy\n"
        "- **Description:** cleanup integrity parser validator scheduler telemetry "
        "metrics retries fallback safeguards checkpoints boundaries.\n\n"
        "## 2. UTF Console Stability\n"
        "- **ID:** REQ-201\n"
        "- **Title:** UTF console stability for cross platform terminals\n"
        "- **Description:** utf glyph rendering windows linux macos output "
        "handling reliability.\n\n",
        encoding="utf-8",
    )


def test_infer_scope_filters_out_low_overlap_below_default_threshold(tmp_path: Path) -> None:
    from specsmith.agent.broker import infer_scope

    req_md = tmp_path / "REQUIREMENTS.md"
    _write_requirements(req_md)
    utterance = (
        "cleanup expedition nebula lattice quantization stochastic harmonic "
        "cascading manifold vectors entropy synthesis"
    )
    proposal = infer_scope(utterance, req_md, min_score=0.15)
    assert not proposal.is_known
    assert proposal.confidence == 0.0


def test_infer_scope_keeps_strong_overlap_above_threshold(tmp_path: Path) -> None:
    from specsmith.agent.broker import infer_scope

    req_md = tmp_path / "REQUIREMENTS.md"
    _write_requirements(req_md)
    proposal = infer_scope(
        "fix cleanup validator retries fallback behavior",
        req_md,
        min_score=0.15,
    )
    assert proposal.is_known
    assert proposal.confidence >= 0.15


def test_infer_scope_min_score_zero_preserves_previous_behavior(tmp_path: Path) -> None:
    from specsmith.agent.broker import infer_scope

    req_md = tmp_path / "REQUIREMENTS.md"
    _write_requirements(req_md)
    utterance = (
        "cleanup expedition nebula lattice quantization stochastic harmonic "
        "cascading manifold vectors entropy synthesis"
    )
    proposal = infer_scope(utterance, req_md, min_score=0.0)
    assert proposal.is_known
    assert proposal.confidence > 0.0
