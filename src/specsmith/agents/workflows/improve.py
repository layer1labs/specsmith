# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""improve_specsmith workflow — self-improvement loop.

Executes: inspect repo → plan changes → edit code/docs → run tests →
summarize → produce follow-up tasks.

Constraints:
- No silent edits (all changes produce artifacts)
- No skipping tests
- No accepting unclear failures
- Verifier must approve before changes are accepted
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from specsmith.agents.config import AgentConfig, load_agent_config
from specsmith.agents.reports import ChangeReport, save_report


def run_improvement(
    task: str,
    project_dir: str,
    max_turns: int = 6,
    config: AgentConfig | None = None,
) -> ChangeReport:
    """Run the full improvement workflow on the specsmith codebase.

    Returns a ChangeReport with results and follow-up tasks.
    """
    from specsmith.agents.roles import (
        create_builder,
        create_planner,
        create_verifier,
    )

    if config is None:
        config = load_agent_config(project_dir)

    report = ChangeReport(
        task_id=datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S"),
        task_description=task,
        project_dir=project_dir,
    )

    # ── Phase 1: Plan ──────────────────────────────────────────────
    planner = create_planner(config, project_dir)
    plan_result = planner.run(
        message=f"Plan this improvement task for the specsmith codebase:\n{task}",
        max_turns=max_turns,
    )
    plan_result.process()

    plan_text = _extract_last_assistant_message(plan_result.messages)
    report.plan = plan_text

    if not plan_text:
        report.status = "failed"
        report.summary = "Planner produced no output."
        save_report(report)
        return report

    # ── Phase 2: Build ─────────────────────────────────────────────
    builder = create_builder(config, project_dir)
    build_result = builder.run(
        message=f"Execute this plan on the specsmith codebase:\n\n{plan_text}",
        max_turns=max_turns,
    )
    build_result.process()

    build_text = _extract_last_assistant_message(build_result.messages)
    report.build_output = build_text

    # Extract files changed from build output
    report.files_changed = _extract_files_from_output(build_text)

    # ── Phase 3: Verify ────────────────────────────────────────────
    verifier = create_verifier(config, project_dir)
    verify_result = verifier.run(
        message=(
            f"Verify these changes to the specsmith codebase:\n\n"
            f"{build_text}\n\n"
            "Run the relevant tests. Report ACCEPT or REJECT with reasoning."
        ),
        max_turns=max_turns,
    )
    verify_result.process()

    verify_text = _extract_last_assistant_message(verify_result.messages)
    report.verify_output = verify_text

    # Parse verdict
    if "ACCEPT" in verify_text.upper():
        report.status = "accepted"
        report.verdict = "ACCEPT"
    elif "REJECT" in verify_text.upper():
        report.status = "rejected"
        report.verdict = "REJECT"
    else:
        report.status = "unclear"
        report.verdict = "UNCLEAR"

    # Extract test results
    report.tests_run, report.tests_passed, report.tests_failed = _extract_test_counts(verify_text)

    # Generate follow-up tasks
    report.follow_up_tasks = _extract_follow_ups(verify_text, build_text)
    report.summary = _generate_summary(report)

    save_report(report)
    return report


def _extract_last_assistant_message(messages: list[dict[str, Any]]) -> str:
    """Get the last assistant message content from a conversation."""
    for msg in reversed(messages):
        if msg.get("role") == "assistant" and msg.get("content"):
            return str(msg["content"])
    return ""


def _extract_files_from_output(text: str) -> list[str]:
    """Heuristically extract file paths from builder output."""
    import re

    files: list[str] = []
    # Match patterns like "Wrote X chars to path" or "Patched path"
    pattern = r"(?:Wrote|Patched|Created|Modified)\s+.*?\s+(?:to\s+)?(\S+\.\w+)"
    for match in re.finditer(pattern, text):
        files.append(match.group(1))
    # Match patterns like "- path/to/file.py" in lists
    for match in re.finditer(r"^-\s+`?([a-zA-Z0-9_/\\.]+\.\w+)`?", text, re.MULTILINE):
        if match.group(1) not in files:
            files.append(match.group(1))
    return files


def _extract_test_counts(text: str) -> tuple[int, int, int]:
    """Extract test run/pass/fail counts from verifier output."""
    import re

    # Match "N passed" pattern
    passed_match = re.search(r"(\d+)\s+passed", text)
    failed_match = re.search(r"(\d+)\s+failed", text)
    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    return passed + failed, passed, failed


def _extract_follow_ups(verify_text: str, build_text: str) -> list[str]:
    """Extract follow-up tasks from agent output."""
    follow_ups: list[str] = []
    for text in [verify_text, build_text]:
        for line in text.splitlines():
            lower = line.lower().strip()
            if lower.startswith(("- todo:", "- follow-up:", "- next:")):
                follow_ups.append(line.strip().lstrip("- "))
            elif "TODO" in line and ":" in line:
                follow_ups.append(line.strip())
    return follow_ups


def _generate_summary(report: ChangeReport) -> str:
    """Generate a human-readable summary of the improvement run."""
    parts = [f"Task: {report.task_description}"]
    parts.append(f"Verdict: {report.verdict}")
    if report.files_changed:
        parts.append(f"Files changed: {', '.join(report.files_changed)}")
    if report.tests_run > 0:
        parts.append(
            f"Tests: {report.tests_passed}/{report.tests_run} passed"
            + (f", {report.tests_failed} failed" if report.tests_failed else "")
        )
    if report.follow_up_tasks:
        parts.append(f"Follow-ups: {len(report.follow_up_tasks)}")
    return " | ".join(parts)
