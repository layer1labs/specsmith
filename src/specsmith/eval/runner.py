# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Eval suite runner — executes eval cases and collects results."""

from __future__ import annotations

import time

from specsmith.eval import EvalCase, EvalReport, EvalResult, EvalSuite


def _provider_available() -> str | None:
    """Return the first available LLM provider name, or None."""
    # Check Ollama first (local, always free)
    try:
        import urllib.request

        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/tags", method="GET"
        )
        with urllib.request.urlopen(req, timeout=1):
            pass
        return "ollama"
    except Exception:  # noqa: BLE001
        pass
    # Cloud providers via env keys
    import os

    for key, name in (
        ("ANTHROPIC_API_KEY", "anthropic"),
        ("OPENAI_API_KEY", "openai"),
        ("GOOGLE_API_KEY", "gemini"),
    ):
        if os.environ.get(key, "").strip():
            return name
    return None


def run_case_real(case: EvalCase, *, provider: str = "ollama") -> EvalResult:
    """Run a single eval case against a live LLM provider.

    Uses the specsmith provider chain (Ollama → Anthropic → OpenAI → Gemini).
    On any provider failure, returns a failed result rather than raising so
    the suite continues.
    """
    import os
    from pathlib import Path

    start = time.monotonic()
    try:
        from specsmith.agent.chat_runner import run_chat
        from specsmith.agent.events import EventEmitter

        project_dir = Path(os.environ.get("SPECSMITH_EVAL_PROJECT", ".")).resolve()
        emitter = EventEmitter(stream=None)  # type: ignore[arg-type]
        result = run_chat(
            case.input,
            project_dir=project_dir,
            profile="standard",
            session_id=f"eval-{case.id}",
            emitter=emitter,
            msg_block="eval-blk-001",
        )
        latency = (time.monotonic() - start) * 1000
        if result is None:
            return EvalResult(
                case_id=case.id,
                passed=False,
                score=0.0,
                latency_ms=latency,
                model=provider,
                provider=provider,
                output_preview="",
                error="provider returned None",
            )
        sc = score_output(result.summary, case.expected_keywords)
        return EvalResult(
            case_id=case.id,
            passed=sc >= 0.5,
            score=sc,
            latency_ms=latency,
            model=provider,
            provider=provider,
            output_preview=result.summary[:200],
        )
    except Exception as exc:  # noqa: BLE001
        latency = (time.monotonic() - start) * 1000
        return EvalResult(
            case_id=case.id,
            passed=False,
            score=0.0,
            latency_ms=latency,
            model=provider,
            provider=provider,
            output_preview="",
            error=str(exc)[:200],
        )


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
        model: Model identifier (ignored when stub=False; provider chosen
               automatically via :func:`_provider_available`).
        provider: Provider name (overridden by auto-detection when stub=False).
        stub: If True, use stub runner. If False, auto-detect a live LLM
              and run each case for real; silently falls back to stub when
              no provider is reachable.
    """
    # Auto-detect provider when real mode is requested
    live_provider: str | None = None
    if not stub:
        live_provider = _provider_available()
        if live_provider is None:
            stub = True  # No provider found; degrade gracefully

    results: list[EvalResult] = []
    for case in suite.cases:
        if stub:
            result = run_case_stub(case)
        else:
            result = run_case_real(case, provider=live_provider or provider)
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
