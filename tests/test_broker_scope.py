# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Focused tests for broker scope-threshold behavior."""

from __future__ import annotations

from pathlib import Path


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
