# SPDX-License-Identifier: MIT
"""Tests for the improvement tracking functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from specsmith.improvement_tracker import ImprovementRecord, SessionAnalysis, ImprovementTracker


def test_improvement_record_serialization():
    """Test that ImprovementRecord can be properly serialized and deserialized."""
    record = ImprovementRecord(
        timestamp="2026-01-01T00:00:00Z",
        type="bug",
        description="Fix memory leak in cleanup module",
        severity="high",
        status="pending",
        metrics={"lines_fixed": 15, "test_coverage": 0.95}
    )

    # Test serialization
    data = record.model_dump()
    assert data["timestamp"] == "2026-01-01T00:00:00Z"
    assert data["type"] == "bug"
    assert data["description"] == "Fix memory leak in cleanup module"
    assert data["severity"] == "high"
    assert data["status"] == "pending"
    assert data["metrics"]["lines_fixed"] == 15
    assert data["metrics"]["test_coverage"] == 0.95


def test_session_analysis_serialization():
    """Test that SessionAnalysis can be properly serialized and deserialized."""
    analysis = SessionAnalysis(
        session_id="test-session-123",
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-01T01:00:00Z",
        duration_seconds=3600,
        work_items_completed=["WI-ABC123", "WI-DEF456"],
        cost_per_correct_solution=0.05,
        efficiency_metrics={"code_quality": 0.85, "speed": 0.92},
        improvements=[
            ImprovementRecord(
                timestamp="2026-01-01T00:30:00Z",
                type="efficiency",
                description="Optimize database queries",
                severity="medium",
                status="implemented"
            )
        ],
        session_notes="Session completed successfully with no major issues"
    )

    # Test serialization
    data = analysis.model_dump()
    assert data["session_id"] == "test-session-123"
    assert data["start_time"] == "2026-01-01T00:00:00Z"
    assert data["end_time"] == "2026-01-01T01:00:00Z"
    assert data["duration_seconds"] == 3600
    assert data["work_items_completed"] == ["WI-ABC123", "WI-DEF456"]
    assert data["cost_per_correct_solution"] == 0.05
    assert data["efficiency_metrics"]["code_quality"] == 0.85
    assert data["efficiency_metrics"]["speed"] == 0.92
    assert len(data["improvements"]) == 1
    assert data["improvements"][0]["description"] == "Optimize database queries"


def test_improvement_tracker_initialization():
    """Test that ImprovementTracker initializes correctly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tracker = ImprovementTracker(Path(tmp_dir))

        # Check that improvements directory was created
        assert (Path(tmp_dir) / ".specsmith" / "improvements").exists()

        # Check that logger is set up
        assert tracker.logger is not None


def test_record_session_analysis():
    """Test recording session analysis."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tracker = ImprovementTracker(Path(tmp_dir))

        analysis = SessionAnalysis(
            session_id="test-session-123",
            start_time="2026-01-01T00:00:00Z",
            end_time="2026-01-01T01:00:00Z",
            duration_seconds=3600,
            work_items_completed=["WI-ABC123"],
            cost_per_correct_solution=0.05,
            efficiency_metrics={"code_quality": 0.85},
            improvements=[],
            session_notes="Test session"
        )

        tracker.record_session_analysis(analysis)

        # Check that file was created
        session_file = Path(tmp_dir) / ".specsmith" / "improvements" / "session_test-session-123.json"
        assert session_file.exists()

        # Check file content
        with open(session_file, 'r') as f:
            data = json.load(f)
            assert data["session_id"] == "test-session-123"
            assert data["duration_seconds"] == 3600


def test_record_improvement():
    """Test recording an improvement."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tracker = ImprovementTracker(Path(tmp_dir))

        improvement = ImprovementRecord(
            timestamp="2026-01-01T00:00:00Z",
            type="bug",
            description="Fix memory leak in cleanup module",
            severity="high",
            status="pending"
        )

        tracker.record_improvement(improvement)

        # Check that file was created
        improvement_file = Path(tmp_dir) / ".specsmith" / "improvements" / "improvement_2026-01-01T00:00:00Z.json"
        assert improvement_file.exists()

        # Check file content
        with open(improvement_file, 'r') as f:
            data = json.load(f)
            assert data["description"] == "Fix memory leak in cleanup module"
            assert data["severity"] == "high"


def test_get_session_analysis():
    """Test retrieving session analysis."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tracker = ImprovementTracker(Path(tmp_dir))

        analysis = SessionAnalysis(
            session_id="test-session-123",
            start_time="2026-01-01T00:00:00Z",
            end_time="2026-01-01T01:00:00Z",
            duration_seconds=3600,
            work_items_completed=["WI-ABC123"],
            cost_per_correct_solution=0.05,
            efficiency_metrics={"code_quality": 0.85},
            improvements=[],
            session_notes="Test session"
        )

        tracker.record_session_analysis(analysis)

        # Retrieve the analysis
        retrieved = tracker.get_session_analysis("test-session-123")
        assert retrieved is not None
        assert retrieved.session_id == "test-session-123"
        assert retrieved.duration_seconds == 3600


def test_get_recent_improvements():
    """Test retrieving recent improvements."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tracker = ImprovementTracker(Path(tmp_dir))

        # Record two improvements
        improvement1 = ImprovementRecord(
            timestamp="2026-01-01T00:00:00Z",
            type="bug",
            description="Fix memory leak in cleanup module",
            severity="high",
            status="pending"
        )

        improvement2 = ImprovementRecord(
            timestamp="2026-01-01T01:00:00Z",
            type="efficiency",
            description="Optimize database queries",
            severity="medium",
            status="implemented"
        )

        tracker.record_improvement(improvement1)
        tracker.record_improvement(improvement2)

        # Retrieve recent improvements
        recent = tracker.get_recent_improvements(5)
        assert len(recent) == 2
        assert recent[0].description == "Optimize database queries"  # Newest first
        assert recent[1].description == "Fix memory leak in cleanup module"


def test_generate_session_report():
    """Test generating a session report."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tracker = ImprovementTracker(Path(tmp_dir))

        analysis = SessionAnalysis(
            session_id="test-session-123",
            start_time="2026-01-01T00:00:00Z",
            end_time="2026-01-01T01:00:00Z",
            duration_seconds=3600,
            work_items_completed=["WI-ABC123", "WI-DEF456"],
            cost_per_correct_solution=0.05,
            efficiency_metrics={"code_quality": 0.85, "speed": 0.92},
            improvements=[
                ImprovementRecord(
                    timestamp="2026-01-01T00:30:00Z",
                    type="efficiency",
                    description="Optimize database queries",
                    severity="medium",
                    status="implemented"
                )
            ],
            session_notes="Test session with improvements"
        )

        tracker.record_session_analysis(analysis)

        # Generate report
        report = tracker.generate_session_report("test-session-123")
        assert "Session Report: test-session-123" in report
        assert "Duration: 3600 seconds" in report
        assert "Work Items Completed: 2" in report
        assert "Cost per Correct Solution: 0.05" in report
        assert "Optimize database queries" in report
