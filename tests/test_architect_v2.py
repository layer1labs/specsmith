# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for BA interview v2: project type dimension, feature gap catalog,
specsmith architect issues CLI, session_init YAML-first fix, specsmith resume CLI.

REQ-380, REQ-381, REQ-382, REQ-383, REQ-384
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

# ---------------------------------------------------------------------------
# REQ-381 — project_type dimension
# ---------------------------------------------------------------------------


class TestProjectTypeDimension:
    def test_arch_dimensions_first_key_is_project_type(self) -> None:
        from specsmith.architect import ARCH_DIMENSIONS

        assert ARCH_DIMENSIONS[0].key == "project_type"

    def test_arch_dimensions_has_ten_entries(self) -> None:
        from specsmith.architect import ARCH_DIMENSIONS

        assert len(ARCH_DIMENSIONS) == 10

    def test_make_dimensions_unknown_type_generic_hint(self) -> None:
        from specsmith.architect import _make_dimensions

        dims = _make_dimensions("unknown")
        pt = dims[0]
        assert pt.key == "project_type"
        assert "auto-detected" not in pt.hint.lower()

    def test_make_dimensions_known_type_includes_detected_in_hint(self) -> None:
        from specsmith.architect import _make_dimensions

        dims = _make_dimensions("cli-python")
        pt = dims[0]
        assert "cli-python" in pt.hint

    def test_make_dimensions_does_not_mutate_base_list(self) -> None:
        from specsmith.architect import _ARCH_DIMENSIONS_BASE, _make_dimensions

        before = [d.key for d in _ARCH_DIMENSIONS_BASE]
        _make_dimensions("embedded-hardware")
        after = [d.key for d in _ARCH_DIMENSIONS_BASE]
        assert before == after

    def test_non_interactive_interview_sets_project_type(self, tmp_path: Path) -> None:
        from specsmith.architect import _run_non_interactive_interview

        with patch(
            "specsmith.architect.scan_project_structure",
            return_value={
                "name": "myproj",
                "primary_language": "python",
                "inferred_type": "cli-python",
            },
        ):
            result = _run_non_interactive_interview(tmp_path)

        dims = result["dimensions"]
        pt_dim = next((d for d in dims if d.key == "project_type"), None)
        assert pt_dim is not None
        assert "cli-python" in pt_dim.answer


# ---------------------------------------------------------------------------
# REQ-382 — feature gap catalog
# ---------------------------------------------------------------------------


class TestFeatureGapCatalog:
    def test_catalog_has_embedded_hardware(self) -> None:
        from specsmith.architect import SPECSMITH_FEATURE_CATALOG

        gaps = SPECSMITH_FEATURE_CATALOG.get("embedded-hardware", [])
        assert len(gaps) > 0

    def test_embedded_hardware_gap_has_can_bus_entry(self) -> None:
        from specsmith.architect import SPECSMITH_FEATURE_CATALOG

        gaps = SPECSMITH_FEATURE_CATALOG["embedded-hardware"]
        titles = [g.title for g in gaps]
        assert any("CAN" in t or "can" in t.lower() for t in titles)

    def test_catalog_has_yocto_bsp(self) -> None:
        from specsmith.architect import SPECSMITH_FEATURE_CATALOG

        gaps = SPECSMITH_FEATURE_CATALOG.get("yocto-bsp", [])
        assert len(gaps) > 0

    def test_catalog_has_llm_app(self) -> None:
        from specsmith.architect import SPECSMITH_FEATURE_CATALOG

        gaps = SPECSMITH_FEATURE_CATALOG.get("llm-app", [])
        assert len(gaps) > 0

    def test_alias_embedded_python_hmi_maps_to_embedded_hardware(self) -> None:
        from specsmith.architect import SPECSMITH_FEATURE_CATALOG

        assert SPECSMITH_FEATURE_CATALOG.get("embedded-python-hmi") is not None

    def test_alias_rag_pipeline_maps_to_llm_app(self) -> None:
        from specsmith.architect import SPECSMITH_FEATURE_CATALOG

        assert SPECSMITH_FEATURE_CATALOG.get("rag-pipeline") is not None

    def test_unknown_project_type_returns_empty_list(self) -> None:
        from specsmith.architect import SPECSMITH_FEATURE_CATALOG

        assert SPECSMITH_FEATURE_CATALOG.get("totally-unknown-type", []) == []

    def test_feature_gap_has_required_fields(self) -> None:
        from specsmith.architect import SPECSMITH_FEATURE_CATALOG

        for gaps in SPECSMITH_FEATURE_CATALOG.values():
            for gap in gaps:
                assert gap.title
                assert gap.description
                assert gap.project_type
                assert gap.severity in ("enhancement", "bug", "question")


# ---------------------------------------------------------------------------
# REQ-382 — run_feature_gap_analysis
# ---------------------------------------------------------------------------


class TestRunFeatureGapAnalysis:
    def test_returns_gaps_for_embedded_project(self, tmp_path: Path) -> None:
        from specsmith.architect import ArchitecturalDimension, run_feature_gap_analysis

        # Provide interview state with project_type = embedded-hardware
        dims = [
            ArchitecturalDimension(
                key="project_type",
                question="What type?",
                hint="",
                answer="embedded-hardware",
                confidence=0.9,
            )
        ]
        gaps = run_feature_gap_analysis(tmp_path, dims=dims)
        assert len(gaps) > 0
        assert all(g.project_type == "embedded-hardware" for g in gaps)

    def test_falls_back_to_scan_when_no_interview(self, tmp_path: Path) -> None:
        from specsmith.architect import run_feature_gap_analysis

        with patch(
            "specsmith.architect.scan_project_structure",
            return_value={"inferred_type": "llm-app"},
        ):
            gaps = run_feature_gap_analysis(tmp_path, dims=[])

        assert len(gaps) > 0

    def test_returns_empty_for_unknown_type(self, tmp_path: Path) -> None:
        from specsmith.architect import ArchitecturalDimension, run_feature_gap_analysis

        dims = [
            ArchitecturalDimension(
                key="project_type",
                question="What type?",
                hint="",
                answer="completely-unknown-xyz",
                confidence=0.9,
            )
        ]
        with patch(
            "specsmith.architect.scan_project_structure", return_value={"inferred_type": ""}
        ):
            gaps = run_feature_gap_analysis(tmp_path, dims=dims)
        assert gaps == []


# ---------------------------------------------------------------------------
# REQ-383 — specsmith architect issues CLI
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# REQ-380 — session_init YAML-first fix
# ---------------------------------------------------------------------------


class TestSessionInitYamlFirst:
    def test_count_requirements_reads_json_in_yaml_mode(self, tmp_path: Path) -> None:
        from specsmith.session_init import _count_requirements

        # Set up YAML-first mode
        specsmith_dir = tmp_path / ".specsmith"
        specsmith_dir.mkdir()
        (specsmith_dir / "governance-mode").write_text("yaml", encoding="utf-8")

        # Write mock requirements.json (5 reqs) and testcases.json (3 linked)
        reqs = [{"id": f"REQ-{i:03d}"} for i in range(1, 6)]
        tests = [{"id": f"TEST-{i:03d}", "requirement_id": f"REQ-{i:03d}"} for i in range(1, 4)]
        (specsmith_dir / "requirements.json").write_text(json.dumps(reqs), encoding="utf-8")
        (specsmith_dir / "testcases.json").write_text(json.dumps(tests), encoding="utf-8")

        total, covered = _count_requirements(tmp_path)
        assert total == 5
        assert covered == 3

    def test_count_requirements_no_json_yaml_mode(self, tmp_path: Path) -> None:
        from specsmith.session_init import _count_requirements

        specsmith_dir = tmp_path / ".specsmith"
        specsmith_dir.mkdir()
        (specsmith_dir / "governance-mode").write_text("yaml", encoding="utf-8")

        total, covered = _count_requirements(tmp_path)
        assert total == 0
        assert covered == 0

    def test_count_tests_reads_json_in_yaml_mode(self, tmp_path: Path) -> None:
        from specsmith.session_init import _count_tests

        specsmith_dir = tmp_path / ".specsmith"
        specsmith_dir.mkdir()
        (specsmith_dir / "governance-mode").write_text("yaml", encoding="utf-8")

        tests = [{"id": f"TEST-{i:03d}"} for i in range(1, 8)]
        (specsmith_dir / "testcases.json").write_text(json.dumps(tests), encoding="utf-8")

        assert _count_tests(tmp_path) == 7

    def test_is_yaml_first_mode_true(self, tmp_path: Path) -> None:
        from specsmith.session_init import _is_yaml_first_mode

        specsmith_dir = tmp_path / ".specsmith"
        specsmith_dir.mkdir()
        (specsmith_dir / "governance-mode").write_text("yaml", encoding="utf-8")
        assert _is_yaml_first_mode(tmp_path) is True

    def test_is_yaml_first_mode_false_when_missing(self, tmp_path: Path) -> None:
        from specsmith.session_init import _is_yaml_first_mode

        assert _is_yaml_first_mode(tmp_path) is False
