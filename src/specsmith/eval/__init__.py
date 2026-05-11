# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Eval-Driven Development framework (ARCHITECTURE.md §13 Phase 1).

Provides structured eval suites that test AI model capabilities against
concrete tasks. Used for model intelligence scoring, regression testing,
and provider qualification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvalCase:
    """A single evaluation case — one prompt + expected behavior."""

    id: str
    name: str
    role: str  # which agent role this tests
    prompt: str
    expected_keywords: list[str] = field(default_factory=list)
    max_tokens: int = 1024
    timeout_seconds: int = 30
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "prompt": self.prompt,
            "expected_keywords": self.expected_keywords,
            "max_tokens": self.max_tokens,
            "tags": self.tags,
        }


@dataclass
class EvalResult:
    """Result of running a single eval case."""

    case_id: str
    passed: bool
    score: float  # 0.0–1.0
    latency_ms: float
    model: str
    provider: str
    output_preview: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "passed": self.passed,
            "score": round(self.score, 3),
            "latency_ms": round(self.latency_ms, 1),
            "model": self.model,
            "provider": self.provider,
            "output_preview": self.output_preview[:200],
            "error": self.error,
        }


@dataclass
class EvalSuite:
    """A named collection of eval cases."""

    id: str
    name: str
    description: str
    cases: list[EvalCase] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "case_count": len(self.cases),
            "tags": self.tags,
        }


@dataclass
class EvalReport:
    """Aggregated results from running an eval suite."""

    suite_id: str
    total: int
    passed: int
    failed: int
    avg_score: float
    avg_latency_ms: float
    results: list[EvalResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite_id": self.suite_id,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "avg_score": round(self.avg_score, 3),
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "results": [r.to_dict() for r in self.results],
        }


__all__ = ["EvalCase", "EvalReport", "EvalResult", "EvalSuite"]
