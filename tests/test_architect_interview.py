# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for the epistemic BA interview system (REQ-375–REQ-379).

Covers:
  - score_answer() rubric for confidence increments.
  - ARCH_DIMENSIONS has exactly 9 dimensions with required keys.
  - run_interview() in non-interactive mode produces ARCHITECTURE.md + proposed.yml.
  - Interview state persisted to .specsmith/arch-interview.json.
  - run_gap_analysis() snapshots and diffs ARCHITECTURE.md.
  - run_arch_update() saves snapshot and runs gap analysis.
  - CLI: specsmith architect interview --non-interactive.
  - CLI: specsmith architect gap.
  - CLI: specsmith architect update --non-interactive.
"""

from __future__ import annotations

from pathlib import Path

from specsmith.architect import (
    _ARCH_SNAPSHOT_FILE,
    _INTERVIEW_STATE_FILE,
    ARCH_DIMENSIONS,
    ArchitecturalDimension,
    run_arch_update,
    run_gap_analysis,
    run_interview,
    score_answer,
)


class TestScoreAnswer:
    """score_answer() must return confidence increments matching the rubric."""

    def test_empty_answer_returns_small_increment(self) -> None:
        assert score_answer("") == 0.05

    def test_whitespace_only_returns_small_increment(self) -> None:
        assert score_answer("   ") == 0.05

    def test_short_vague_answer(self) -> None:
        # "Fixes bugs." is 11 chars (≤15) → +0.10
        score = score_answer("Fixes bugs.")
        assert len("Fixes bugs.") <= 15
        assert score == 0.10

    def test_medium_general_answer(self) -> None:
        answer = "A CLI tool for managing Python project governance workflows."
        assert len(answer) > 15 and len(answer) <= 60
        score = score_answer(answer)
        assert score == 0.25

    def test_specific_long_answer(self) -> None:
        answer = (
            "A distributed event-sourcing platform for real-time IoT telemetry "
            "ingestion and analytics, serving industrial automation clients."
        )
        assert len(answer) > 60
        score = score_answer(answer)
        assert score == 0.40

    def test_answer_with_metrics_gets_bonus(self) -> None:
        answer = (
            "Must handle 10000 tps with 99.9% SLA, 500ms p99 latency. "
            "Data retention 90 days, GDPR compliant."
        )
        score = score_answer(answer)
        assert score >= 0.40  # metrics bonus

    def test_very_long_answer_gets_max_increment(self) -> None:
        answer = "x" * 250  # Over 200 chars
        score = score_answer(answer)
        assert score == 0.50

    def test_score_is_float(self) -> None:
        assert isinstance(score_answer("some answer"), float)

    def test_score_is_non_negative(self) -> None:
        for text in ["", "a", "short", "a" * 100, "a" * 300]:
            assert score_answer(text) >= 0.0


class TestArchDimensions:
    """ARCH_DIMENSIONS must have exactly 10 well-formed dimensions (project_type + 9 technical)."""

    def test_exactly_ten_dimensions(self) -> None:
        # REQ-381: project_type added as first dimension; 9 technical + 1 type = 10
        assert len(ARCH_DIMENSIONS) == 10, f"Expected 10 dimensions, got {len(ARCH_DIMENSIONS)}"

    def test_first_dimension_is_project_type(self) -> None:
        # REQ-381: project_type is first so users confirm the auto-detected type immediately
        assert ARCH_DIMENSIONS[0].key == "project_type"

    def test_all_dimensions_have_required_fields(self) -> None:
        required_keys = {
            "project_type",
            "problem_domain",
            "user_types",
            "key_integrations",
            "technical_constraints",
            "deployment_target",
            "scale_expectations",
            "data_model",
            "security_model",
            "failure_modes",
        }
        actual_keys = {d.key for d in ARCH_DIMENSIONS}
        assert actual_keys == required_keys, (
            f"Missing keys: {required_keys - actual_keys}\n"
            f"Extra keys: {actual_keys - required_keys}"
        )

    def test_all_dimensions_have_question_and_hint(self) -> None:
        for dim in ARCH_DIMENSIONS:
            assert dim.question, f"Dimension {dim.key} missing question"
            assert dim.hint, f"Dimension {dim.key} missing hint"

    def test_initial_confidence_is_zero(self) -> None:
        for dim in ARCH_DIMENSIONS:
            assert dim.confidence == 0.0, (
                f"Dimension {dim.key} should have 0.0 confidence initially"
            )

    def test_architectural_dimension_is_dataclass(self) -> None:
        dim = ArchitecturalDimension(key="test", question="Test question?", hint="Test hint")
        assert dim.key == "test"
        assert dim.confidence == 0.0
        assert dim.answer == ""


class TestRunInterviewNonInteractive:
    """run_interview() in non-interactive mode must complete without TTY."""

    def test_produces_architecture_md(self, tmp_path: Path) -> None:
        result = run_interview(tmp_path, non_interactive=True)
        arch_path = result["arch_path"]
        assert arch_path is not None
        assert Path(arch_path).exists(), "docs/ARCHITECTURE.md must be created"

    def test_produces_proposed_reqs_yml(self, tmp_path: Path) -> None:
        result = run_interview(tmp_path, non_interactive=True)
        proposed_path = result["proposed_reqs_path"]
        assert proposed_path is not None
        assert Path(proposed_path).exists(), "docs/requirements/proposed.yml must be created"

    def test_architecture_md_has_confidence_annotations(self, tmp_path: Path) -> None:
        run_interview(tmp_path, non_interactive=True)
        arch_path = tmp_path / "docs" / "ARCHITECTURE.md"
        content = arch_path.read_text(encoding="utf-8")
        assert "confidence:" in content, "ARCHITECTURE.md should have confidence annotations"

    def test_interview_state_is_persisted(self, tmp_path: Path) -> None:
        run_interview(tmp_path, non_interactive=True)
        state_file = tmp_path / _INTERVIEW_STATE_FILE
        assert state_file.exists(), f"{_INTERVIEW_STATE_FILE} must be persisted"

    def test_state_file_is_valid_json(self, tmp_path: Path) -> None:
        import json

        run_interview(tmp_path, non_interactive=True)
        state_file = tmp_path / _INTERVIEW_STATE_FILE
        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert len(data) == 10  # One entry per dimension (project_type + 9 technical)

    def test_dimensions_have_non_zero_confidence(self, tmp_path: Path) -> None:
        result = run_interview(tmp_path, non_interactive=True)
        dims = result["dimensions"]
        assert all(d.confidence > 0.0 for d in dims), (
            "All dimensions should have non-zero confidence after non-interactive run"
        )

    def test_result_has_all_confident_flag(self, tmp_path: Path) -> None:
        result = run_interview(tmp_path, non_interactive=True)
        assert "all_confident" in result
        assert isinstance(result["all_confident"], bool)

    def test_proposed_reqs_has_req_ids(self, tmp_path: Path) -> None:
        run_interview(tmp_path, non_interactive=True)
        proposed = tmp_path / "docs" / "requirements" / "proposed.yml"
        content = proposed.read_text(encoding="utf-8")
        assert "id: REQ-" in content, "proposed.yml should contain REQ IDs"


class TestRunGapAnalysis:
    """run_gap_analysis() must correctly snapshot and diff ARCHITECTURE.md."""

    def test_first_call_saves_snapshot(self, tmp_path: Path) -> None:
        arch_path = tmp_path / "docs" / "ARCHITECTURE.md"
        arch_path.parent.mkdir(parents=True, exist_ok=True)
        arch_path.write_text("# Architecture\n\n## Overview\nBasic system.\n", encoding="utf-8")

        result = run_gap_analysis(tmp_path)

        snapshot = tmp_path / _ARCH_SNAPSHOT_FILE
        assert snapshot.exists(), "Snapshot should be created on first call"
        assert "Snapshot saved" in result.get("message", "") or result.get("gap_reqs_path") is None

    def test_second_call_detects_new_sections(self, tmp_path: Path) -> None:
        arch_path = tmp_path / "docs" / "ARCHITECTURE.md"
        arch_path.parent.mkdir(parents=True, exist_ok=True)

        # First version (becomes snapshot)
        arch_path.write_text("# Architecture\n\n## Overview\nBasic system.\n", encoding="utf-8")
        run_gap_analysis(tmp_path)  # Save snapshot

        # Updated version with new section
        arch_path.write_text(
            "# Architecture\n\n## Overview\nBasic system.\n\n## Caching Layer\nRedis.\n",
            encoding="utf-8",
        )
        result = run_gap_analysis(tmp_path)

        assert len(result["new_reqs"]) >= 1, "Gap analysis should propose REQs for new sections"

    def test_gap_writes_arch_gap_yml(self, tmp_path: Path) -> None:
        arch_path = tmp_path / "docs" / "ARCHITECTURE.md"
        arch_path.parent.mkdir(parents=True, exist_ok=True)
        arch_path.write_text("# Architecture\n\n## Overview\nBasic.\n", encoding="utf-8")
        run_gap_analysis(tmp_path)  # Save snapshot

        arch_path.write_text(
            "# Architecture\n\n## Overview\nBasic.\n\n## New Feature\nDetails.\n",
            encoding="utf-8",
        )
        result = run_gap_analysis(tmp_path)

        if result["gap_reqs_path"]:
            gap_path = Path(result["gap_reqs_path"])
            assert gap_path.exists(), "arch-gap.yml should be created"

    def test_gap_no_change_returns_empty_new_reqs(self, tmp_path: Path) -> None:
        arch_path = tmp_path / "docs" / "ARCHITECTURE.md"
        arch_path.parent.mkdir(parents=True, exist_ok=True)
        arch_path.write_text("# Architecture\n\n## Overview\nBasic system.\n", encoding="utf-8")
        run_gap_analysis(tmp_path)  # Save snapshot

        # No change to arch
        result = run_gap_analysis(tmp_path)
        assert len(result["new_reqs"]) == 0

    def test_missing_architecture_md_returns_message(self, tmp_path: Path) -> None:
        result = run_gap_analysis(tmp_path)
        assert result["gap_reqs_path"] is None
        assert result["gap_tests_path"] is None
        assert "message" in result


class TestRunArchUpdate:
    """run_arch_update() saves snapshot, runs interview, and calls gap analysis."""

    def test_saves_snapshot_of_existing_arch(self, tmp_path: Path) -> None:
        arch_path = tmp_path / "docs" / "ARCHITECTURE.md"
        arch_path.parent.mkdir(parents=True, exist_ok=True)
        arch_path.write_text("# Architecture\n\n## Overview\nExisting content.\n", encoding="utf-8")

        run_arch_update(tmp_path, non_interactive=True)

        snapshot = tmp_path / _ARCH_SNAPSHOT_FILE
        assert snapshot.exists(), "arch-snapshot.md should be saved"

    def test_produces_updated_architecture_md(self, tmp_path: Path) -> None:
        arch_path = tmp_path / "docs" / "ARCHITECTURE.md"
        arch_path.parent.mkdir(parents=True, exist_ok=True)
        arch_path.write_text("# Architecture\n\n## Overview\nOld content.\n", encoding="utf-8")

        result = run_arch_update(tmp_path, non_interactive=True)
        assert result["arch_path"] is not None
        assert Path(result["arch_path"]).exists()

    def test_result_includes_gap(self, tmp_path: Path) -> None:
        arch_path = tmp_path / "docs" / "ARCHITECTURE.md"
        arch_path.parent.mkdir(parents=True, exist_ok=True)
        arch_path.write_text("# Architecture\n\n## Overview\nOld content.\n", encoding="utf-8")

        result = run_arch_update(tmp_path, non_interactive=True)
        assert "gap" in result, "result should include gap analysis output"
