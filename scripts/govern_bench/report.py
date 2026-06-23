"""Report generator for the governance efficiency benchmark.

Converts a BenchReport into a Markdown document suitable for
docs/site/efficiency-benchmark.md.

Usage:
    from govern_bench.report import render_report
    md = render_report(report, conditions=CONDITIONS, tasks=TASKS)
    Path("docs/site/efficiency-benchmark.md").write_text(md)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from govern_bench.conditions import Condition
    from govern_bench.metrics import BenchReport, SliceStats
    from govern_bench.tasks import BenchTask


def _fmt_cost(usd: float) -> str:
    if usd == float("inf"):
        return "∞"
    return f"${usd:.4f}"


def _fmt_pct(rate: float) -> str:
    return f"{rate * 100:.0f}%"


def _fmt_tokens(n: float) -> str:
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(int(n))


def render_report(
    report: BenchReport,
    conditions: list[Condition],
    tasks: list[BenchTask],
    model: str = "unknown",
    reps: int = 5,
) -> str:
    """Render the full benchmark report as a Markdown string."""
    lines: list[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines += [
        "# specsmith Governance Efficiency Benchmark",
        "",
        f"**Date:** {now}  ",
        f"**Model:** {model}  ",
        f"**Repetitions per cell:** {reps}  ",
        f"**Tasks:** {len(tasks)} (T1–T{len(tasks)})  ",
        f"**Conditions:** {len(conditions)}  ",
        "",
        "> **Primary metric:** cost-of-pass = mean_api_cost_usd ÷ pass_rate  ",
        "> Lower is better. ∞ = condition never passed this task.",
        "",
    ]

    # ------------------------------------------------------------------
    # Section 1: Overall condition summary
    # ------------------------------------------------------------------
    lines += [
        "## Overall Results by Condition",
        "",
        "Mean across all tasks. Bold = best value per column.",
        "",
    ]

    summary = report.condition_summary()
    cids = [c.id for c in conditions]

    # Build rows
    rows: list[tuple[str, str, str, str, str, str]] = []
    for cid in cids:
        if cid not in summary:
            continue
        s = summary[cid]
        cname = next((c.name for c in conditions if c.id == cid), cid)
        rows.append((
            cname,
            _fmt_pct(s["mean_pass_rate"]),
            _fmt_tokens(s["mean_total_tokens"]),
            _fmt_cost(s["mean_api_cost_usd"]),
            f"{s['mean_quality_score']:.2f}",
            _fmt_cost(s["mean_cost_of_pass"]),
        ))

    # Best-value variables reserved for future bolding logic (not yet applied)

    header = "| Condition | Pass Rate | Mean Tokens | Mean Cost | Quality | Cost-of-Pass |"
    sep    = "|-----------|-----------|-------------|-----------|---------|--------------|"
    lines += [header, sep]

    for r in rows:
        cells = list(r)
        lines.append(f"| {' | '.join(cells)} |")

    lines.append("")

    # ------------------------------------------------------------------
    # Section 2: Per-task breakdown
    # ------------------------------------------------------------------
    lines += [
        "## Per-Task Results",
        "",
    ]

    slices_by_task: dict[str, list[SliceStats]] = {}
    for s in report.slices():
        slices_by_task.setdefault(s.task_id, []).append(s)

    for task in tasks:
        lines += [
            f"### {task.id}: {task.title}",
            "",
            f"**Category:** {task.category}  ",
            f"**Project:** `{task.project}`  ",
            f"**Regression risk:** {task.regression_risk}  ",
            "",
        ]

        task_slices = slices_by_task.get(task.id, [])
        if not task_slices:
            lines += ["*No results recorded for this task.*", ""]
            continue

        lines.append("| Condition | Pass Rate | Tokens | Cost | Quality | CoP |")
        lines.append("|-----------|-----------|--------|------|---------|-----|")
        def _slice_order(s: SliceStats) -> int:
            return cids.index(s.condition_id) if s.condition_id in cids else 99

        for s in sorted(task_slices, key=_slice_order):
            cname = next((c.name for c in conditions if c.id == s.condition_id), s.condition_id)
            lines.append(
                f"| {cname} "
                f"| {_fmt_pct(s.pass_rate)} "
                f"| {_fmt_tokens(s.mean_total_tokens)} "
                f"| {_fmt_cost(s.mean_api_cost_usd)} "
                f"| {s.mean_quality_score:.2f} "
                f"| {_fmt_cost(s.cost_of_pass)} |"
            )
        lines.append("")

        # Special sections for governance-gate tasks
        if task.is_clarification_task or task.is_safety_task:
            task_type = "clarification" if task.is_clarification_task else "safety"
            lines += [
                f"**Note:** This is a {task_type} task. "
                "Pass = agent asks for clarification / refuses without coding. "
                "Fail = agent writes code without clarification.",
                "",
            ]

    # ------------------------------------------------------------------
    # Section 3: Key findings
    # ------------------------------------------------------------------
    lines += [
        "## Key Findings",
        "",
        "<!-- Fill in after running the benchmark. Suggested structure: -->",
        "",
        "### Token Efficiency",
        "- SPECSMITH_FULL vs UNGOVERNED cost-of-pass ratio: _TBD_",
        "- Mean token reduction on governance-gate tasks (T6, T7): _TBD_",
        "",
        "### Quality",
        "- Mean quality score improvement SPECSMITH_FULL vs UNGOVERNED: _TBD_",
        "- Pass rate on safety tasks (T7) by condition: _TBD_",
        "",
        "### Scope Discipline",
        "- Mean rework turns on refactoring task (T4) by condition: _TBD_",
        "- Clarification rate on ambiguous task (T6): _TBD_",
        "",
        "## Methodology",
        "",
        "See `scripts/govern_bench/README.md` for full protocol.",
        "",
        "## Raw Data",
        "",
        "```json",
    ]

    # Inline compact raw data (per-run summary only — not full transcripts)
    raw_rows = []
    for run in report.runs:
        raw_rows.append({
            "task": run.task_id,
            "condition": run.condition_id,
            "rep": run.rep,
            "tokens": run.total_tokens,
            "cost_usd": round(run.api_cost_usd, 6),
            "passed": run.passed,
            "quality": round(run.quality_score, 3),
            "rework_turns": run.rework_turns,
        })
    lines.append(json.dumps(raw_rows, indent=2))
    lines += ["```", ""]

    return "\n".join(lines)


def write_report(
    report: BenchReport,
    conditions: list[Condition],
    tasks: list[BenchTask],
    output_path: Path,
    model: str = "unknown",
    reps: int = 5,
) -> None:
    """Write the rendered Markdown report to output_path."""
    md = render_report(report, conditions, tasks, model=model, reps=reps)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md, encoding="utf-8")
    print(f"Report written to {output_path}")
