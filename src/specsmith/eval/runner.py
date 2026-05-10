# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Eval suite runner — executes eval cases and collects results."""

from __future__ import annotations

import time

from specsmith.eval import EvalCase, EvalReport, EvalResult, EvalSuite


def score_output(output: str, expected_keywords: list[str]) -> float:
    """Score an output against expected keywords (0.0–1.0)."""
    if not expected_keywords:
        return 1.0 if output.strip() else 0.0
    lower = output.lower()
    matched = sum(1 for kw in expected_keywords if kw.lower() in lower)
    return matched / len(expected_keywords)


def run_case_stub(case: EvalCase) -> EvalResult:
    """Run a single eval case in stub mode (no real LLM).

    Returns a synthetic result for testing the eval framework itself.
    """
    start = time.monotonic()
    # Stub: generate a fake output that includes expected keywords
    output = f"[stub response for {case.id}] " + " ".join(case.expected_keywords)
    latency = (time.monotonic() - start) * 1000
    sc = score_output(output, case.expected_keywords)
    return EvalResult(
        case_id=case.id,
        passed=sc >= 0.5,
        score=sc,
        latency_ms=latency,
        model="stub",
        provider="local",
        output_preview=output[:200],
    )


def run_suite(
    suite: EvalSuite,
    *,
    model: str = "stub",
    provider: str = "local",
    stub: bool = True,
) -> EvalReport:
    """Run all cases in a suite and return an aggregated report.

    Args:
        suite: The eval suite to run.
        model: Model identifier.
        provider: Provider name.
        stub: If True, use stub runner (no real LLM calls).
    """
    results: list[EvalResult] = []
    for case in suite.cases:
        # Real LLM execution path will replace run_case_stub when
        # provider integration is wired. For now, always use stub.
        result = run_case_stub(case)
        results.append(result)

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    avg_score = sum(r.score for r in results) / total if total else 0.0
    avg_latency = sum(r.latency_ms for r in results) / total if total else 0.0

    return EvalReport(
        suite_id=suite.id,
        total=total,
        passed=passed,
        failed=total - passed,
        avg_score=avg_score,
        avg_latency_ms=avg_latency,
        results=results,
    )


def generate_markdown_report(report: EvalReport) -> str:
    """Generate a markdown report from eval results."""
    lines = [
        f"# Eval Report: {report.suite_id}",
        "",
        f"- **Total**: {report.total}",
        f"- **Passed**: {report.passed}",
        f"- **Failed**: {report.failed}",
        f"- **Avg Score**: {report.avg_score:.1%}",
        f"- **Avg Latency**: {report.avg_latency_ms:.0f}ms",
        "",
        "## Results",
        "",
    ]
    for r in report.results:
        icon = "\u2713" if r.passed else "\u2717"
        lines.append(f"- {icon} **{r.case_id}** — score={r.score:.1%}, {r.latency_ms:.0f}ms")
        if r.error:
            lines.append(f"  - Error: {r.error}")
    return "\n".join(lines)


__all__ = ["generate_markdown_report", "run_case_stub", "run_suite", "score_output"]
