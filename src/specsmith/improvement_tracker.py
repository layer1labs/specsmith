# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Improvement tracking and session analysis for development mode."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from pydantic import BaseModel


class ImprovementRecord(BaseModel):
    """Record of an improvement suggestion or session analysis."""

    timestamp: str
    type: str  # "session", "bug", "efficiency", "skill"
    description: str
    severity: str  # "low", "medium", "high", "critical"
    status: str  # "pending", "implemented", "rejected"
    metrics: Optional[Dict[str, Any]] = None


class SessionAnalysis(BaseModel):
    """Analysis of a session including what worked, what didn't, and improvements."""

    session_id: str
    start_time: str
    end_time: str
    duration_seconds: int
    work_items_completed: List[str]
    cost_per_correct_solution: float
    efficiency_metrics: Dict[str, float]
    improvements: List[ImprovementRecord]
    session_notes: str


class ImprovementTracker:
    """Tracks improvements, session analysis, and development metrics."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.improvements_dir = project_dir / ".specsmith" / "improvements"
        self.improvements_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging for development mode
        self.logger = logging.getLogger("specsmith.improvement")
        self.logger.setLevel(logging.DEBUG if self._is_development_mode() else logging.INFO)

        # Create file handler for improvement logs
        log_file = self.improvements_dir / "improvements.log"
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _is_development_mode(self) -> bool:
        """Check if development mode is enabled in project config."""
        try:
            config_file = self.project_dir / ".specsmith" / "config.yml"
            if config_file.exists():
                import yaml
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    return config.get('enable_development_mode', False)
        except Exception:
            pass
        return False

    def record_session_analysis(self, analysis: SessionAnalysis) -> None:
        """Record session analysis to file and log."""
        # Save to JSON file
        session_file = self.improvements_dir / f"session_{analysis.session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(analysis.model_dump(), f, indent=2)

        # Log the session analysis
        self.logger.info(f"Session analysis recorded: {analysis.session_id}")
        self.logger.info(f"Duration: {analysis.duration_seconds}s")
        self.logger.info(f"Work items completed: {len(analysis.work_items_completed)}")
        self.logger.info(f"Cost per correct solution: {analysis.cost_per_correct_solution}")

        # Log improvements
        for improvement in analysis.improvements:
            self.logger.info(f"Improvement: {improvement.description} ({improvement.severity})")

    def record_improvement(self, improvement: ImprovementRecord) -> None:
        """Record an improvement suggestion."""
        # Save to JSON file
        improvement_file = self.improvements_dir / f"improvement_{improvement.timestamp}.json"
        with open(improvement_file, 'w') as f:
            json.dump(improvement.model_dump(), f, indent=2)

        # Log the improvement
        self.logger.info(f"Improvement recorded: {improvement.description}")
        self.logger.info(f"Severity: {improvement.severity}, Status: {improvement.status}")

    def get_session_analysis(self, session_id: str) -> Optional[SessionAnalysis]:
        """Retrieve session analysis by session ID."""
        session_file = self.improvements_dir / f"session_{session_id}.json"
        if session_file.exists():
            with open(session_file, 'r') as f:
                data = json.load(f)
                return SessionAnalysis(**data)
        return None

    def get_recent_improvements(self, limit: int = 10) -> List[ImprovementRecord]:
        """Get recent improvement records."""
        improvements = []
        for file_path in self.improvements_dir.glob("improvement_*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    improvements.append(ImprovementRecord(**data))
            except Exception:
                continue

        # Sort by timestamp (newest first)
        improvements.sort(key=lambda x: x.timestamp, reverse=True)
        return improvements[:limit]

    def generate_session_report(self, session_id: str) -> str:
        """Generate a human-readable session report."""
        analysis = self.get_session_analysis(session_id)
        if not analysis:
            return "No session analysis found."

        report = [
            f"Session Report: {session_id}",
            f"Start Time: {analysis.start_time}",
            f"End Time: {analysis.end_time}",
            f"Duration: {analysis.duration_seconds} seconds",
            f"Work Items Completed: {len(analysis.work_items_completed)}",
            f"Cost per Correct Solution: {analysis.cost_per_correct_solution}",
            "",
            "Efficiency Metrics:",
        ]

        for metric, value in analysis.efficiency_metrics.items():
            report.append(f"  {metric}: {value}")

        report.append("")
        report.append("Improvements:")

        if not analysis.improvements:
            report.append("  No improvements recorded.")
        else:
            for improvement in analysis.improvements:
                report.append(f"  - {improvement.description} ({improvement.severity})")

        return "\n".join(report)
