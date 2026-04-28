# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Real verifier signal for the Nexus orchestrator (REQ-108).

Replaces the hardcoded ``0.85 / 0.4 / 0.0`` confidence in
``Orchestrator._build_task_result`` with a real signal derived from:

* test_results (failures > 0  -> confidence <= 0.5)
* ruff_errors  (>= 1          -> confidence x 0.7)
* mypy_errors  (>= 1          -> confidence x 0.8)

Equilibrium is reached only when all three gates are clean **and** the
measured confidence meets or exceeds the preflight ``confidence_target``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VerifierReport:
    """Inputs to the verifier; produced by parsing the orchestrator output."""

    test_passed: int = 0
    test_failed: int = 0
    ruff_errors: int = 0
    mypy_errors: int = 0
    has_changes: bool = False


@dataclass
class VerifierVerdict:
    """Outputs of the verifier; consumed by the harness."""

    confidence: float
    equilibrium: bool
    summary: str


def score(
    report: VerifierReport,
    *,
    confidence_target: float = 0.7,
) -> VerifierVerdict:
    """Score a :class:`VerifierReport` into a :class:`VerifierVerdict`.

    Deterministic, pure function so the harness behaviour is reproducible.
    """
    base = 1.0 if report.has_changes else 0.0
    if report.test_failed > 0:
        base = min(base, 0.5)
    if report.ruff_errors > 0:
        base *= 0.7
    if report.mypy_errors > 0:
        base *= 0.8
    base = round(max(0.0, min(1.0, base)), 3)

    clean = report.test_failed == 0 and report.ruff_errors == 0 and report.mypy_errors == 0
    equilibrium = clean and report.has_changes and base >= confidence_target

    parts: list[str] = []
    if report.has_changes:
        parts.append(f"{report.test_passed} passed / {report.test_failed} failed")
    else:
        parts.append("no changes detected")
    if report.ruff_errors:
        parts.append(f"{report.ruff_errors} ruff error(s)")
    if report.mypy_errors:
        parts.append(f"{report.mypy_errors} mypy error(s)")
    summary = "; ".join(parts) + (" — equilibrium" if equilibrium else " — retry recommended")

    return VerifierVerdict(confidence=base, equilibrium=equilibrium, summary=summary)


def report_from_chat_sections(
    sections: dict[str, str],
    *,
    files_changed: list[str] | None = None,
) -> VerifierReport:
    """Build a :class:`VerifierReport` from parsed Nexus output-contract sections.

    The orchestrator's ``_parse_output_contract`` produces a dict keyed by
    ``plan``, ``commands_to_run``, ``files_changed``, ``diff``,
    ``test_results``, and ``next_action``. We extract structured signals
    from the free-form ``test_results`` text. This is deliberately
    forgiving: passes/failures are counted by simple regex.
    """
    import re

    raw = sections.get("test_results", "") or ""
    test_passed = 0
    test_failed = 0
    m_pass = re.search(r"(\d+)\s+passed", raw, re.IGNORECASE)
    if m_pass:
        test_passed = int(m_pass.group(1))
    m_fail = re.search(r"(\d+)\s+failed", raw, re.IGNORECASE)
    if m_fail:
        test_failed = int(m_fail.group(1))

    diff_text = sections.get("diff", "") or ""
    has_changes = bool(diff_text.strip()) or bool(files_changed)

    # ruff/mypy signals are not in the standard contract; scan the raw test
    # output for the canonical error markers.
    ruff_errors = len(re.findall(r"^\s*[A-Z]\d{3,4}\s", raw, re.MULTILINE))
    mypy_errors = len(re.findall(r"\berror:", raw))

    return VerifierReport(
        test_passed=test_passed,
        test_failed=test_failed,
        ruff_errors=ruff_errors,
        mypy_errors=mypy_errors,
        has_changes=has_changes,
    )


__all__ = [
    "VerifierReport",
    "VerifierVerdict",
    "report_from_chat_sections",
    "score",
]
