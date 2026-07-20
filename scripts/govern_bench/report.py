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
    if n == float("inf"):
        return "∞"
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(int(n))


def _fmt_ci_pct(low: float, high: float) -> str:
    return f"{low * 100:.0f}%–{high * 100:.0f}%"


def _fmt_ci_cost(low: float, high: float) -> str:
    if low == float("inf") or high == float("inf"):
        return "∞"
    return f"${low:.4f}–${high:.4f}"


def _fmt_lift(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value * 100:+.0f}pp"


def _fmt_ratio(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.2f}×"


def render_scaffold_lift_matrix(
    report: BenchReport,
    conditions: list[Condition],
    tasks: list[BenchTask],
) -> str:
    """Render a task × condition scaffold lift table."""
    condition_ids = [c.id for c in conditions if c.id != "UNGOVERNED"]
    slices_by_task: dict[str, dict[str, SliceStats]] = {}
    for s in report.slices():
        slices_by_task.setdefault(s.task_id, {})[s.condition_id] = s

    lines = [
        "## Scaffold Lift Matrix (vs UNGOVERNED)",
        "",
    ]
    if not condition_ids:
        lines += ["No scaffold conditions available.", ""]
        return "\n".join(lines)

    header = "| Task | " + " | ".join(condition_ids) + " |"
    sep = "|" + "---|" * (len(condition_ids) + 1)
    lines += [header, sep]
    for task in tasks:
        task_slices = slices_by_task.get(task.id, {})
        row = [task.id]
        for cid in condition_ids:
            slice_stats = task_slices.get(cid)
            row.append(_fmt_lift(slice_stats.scaffold_lift if slice_stats else None))
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    return "\n".join(lines)


def render_democratization_table(report: BenchReport) -> str:
    """Render the cheapest model tier beating frontier+UNGOVERNED CoP per scaffold."""
    rows = report.democratization_table()
    lines = [
        "## Democratization Table",
        "",
    ]
    if not rows:
        lines += [
            "No frontier+UNGOVERNED baseline is available yet, so democratization metrics "
            + "are pending.",
            "",
        ]
        return "\n".join(lines)

    lines += [
        "| Scaffold | Frontier Baseline | Cheapest Model That Beats Frontier | Tier | "
        + "Cost Multiplier |",
        "|----------|-------------------|------------------------------------|------|-----------------|",
    ]
    for row in rows:
        baseline = _fmt_cost(float(row["frontier_cop_usd"]))
        winner = str(row["cheapest_model"]) if row["cheapest_model"] else "—"
        tier = str(row["cheapest_model_tier"]) if row["cheapest_model_tier"] else "—"
        multiplier = _fmt_ratio(
            float(row["cost_multiplier_vs_frontier"])
            if row["cost_multiplier_vs_frontier"] is not None
            else None
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["scaffold"]),
                    baseline,
                    winner,
                    tier,
                    multiplier,
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def render_pareto_scatter_data(report: BenchReport) -> str:
    """Render Pareto frontier data as JSON for chart pipelines."""
    lines = [
        "## Pareto Frontier Data",
        "",
        "```json",
        json.dumps(report.pareto_frontier_data(), indent=2),
        "```",
        "",
    ]
    return "\n".join(lines)


def render_key_claims(report: BenchReport) -> str:
    """Render guarded observations without overstating undersampled results."""
    summary = report.condition_summary()
    lines = [
        "## Key Claims",
        "",
    ]

    reps_by_slice: dict[tuple[str, str], int] = {}
    for run in report.runs:
        if not run.skipped:
            key = (run.task_id, run.condition_id)
            reps_by_slice[key] = reps_by_slice.get(key, 0) + 1
    minimum_reps = min(reps_by_slice.values(), default=0)
    if minimum_reps < 5:
        lines += [
            f"- No superiority claim: the minimum slice has {minimum_reps} repetition(s); "
            "at least 5 are required for screening evidence.",
            "",
        ]
        return "\n".join(lines)

    specsmith_rows = [
        (cid, s)
        for cid, s in summary.items()
        if cid.startswith("SPECSMITH") and s["mean_tokens_per_correct_answer"] < float("inf")
    ]
    non_specsmith_rows = [
        (cid, s)
        for cid, s in summary.items()
        if not cid.startswith("SPECSMITH") and s["mean_tokens_per_correct_answer"] < float("inf")
    ]
    if specsmith_rows and non_specsmith_rows:
        spec_id, best_specsmith = min(
            specsmith_rows,
            key=lambda item: float(item[1]["mean_tokens_per_correct_answer"]),
        )
        non_id, best_non_specsmith = min(
            non_specsmith_rows,
            key=lambda item: float(item[1]["mean_tokens_per_correct_answer"]),
        )
        spec_tpca = float(best_specsmith["mean_tokens_per_correct_answer"])
        non_tpca = float(best_non_specsmith["mean_tokens_per_correct_answer"])
        noninferior = float(best_specsmith["mean_pass_rate"]) >= float(
            best_non_specsmith["mean_pass_rate"]
        )
        if spec_tpca < non_tpca and noninferior:
            ratio = non_tpca / spec_tpca if spec_tpca > 0 else float("inf")
            lines.append(
                f"- Screening result: `{spec_id}` used {_fmt_ratio(ratio)} fewer tokens per "
                f"correct answer than `{non_id}` ({_fmt_tokens(spec_tpca)} vs "
                f"{_fmt_tokens(non_tpca)}) without a lower aggregate pass rate."
            )
        else:
            lines.append(
                "- No Specsmith token-efficiency advantage was observed under the "
                "non-inferior-correctness requirement."
            )
    else:
        lines.append("- Specsmith vs non-specsmith comparison: pending sufficient data.")

    democratization = [r for r in report.democratization_table() if r["cheapest_model"]]
    if democratization:
        best_row = min(
            democratization,
            key=lambda row: float(row["cheapest_cop_usd"]),
        )
        lines.append(
            "- Cheapest tier matching/beating frontier+UNGOVERNED is "
            f"`{best_row['cheapest_model_tier']}` via `{best_row['cheapest_model']}` "
            f"under `{best_row['scaffold']}`."
        )
    else:
        lines.append("- Cheapest tier matching frontier+UNGOVERNED CoP: not observed yet.")

    specsmith_full_lifts = [
        s.scaffold_lift
        for s in report.slices()
        if s.condition_id == "SPECSMITH_FULL" and s.scaffold_lift is not None
    ]
    if specsmith_full_lifts:
        mean_lift = sum(specsmith_full_lifts) / len(specsmith_full_lifts)
        lines.append(
            "- Average scaffold lift for `SPECSMITH_FULL` vs `UNGOVERNED` is "
            f"{_fmt_lift(mean_lift)}."
        )
    else:
        lines.append("- Average scaffold lift for `SPECSMITH_FULL`: pending baseline data.")

    lines.append("")
    return "\n".join(lines)


def write_hf_leaderboard(
    report: BenchReport,
    output_path: Path,
    task_suite: str = "governancebench-v1",
) -> None:
    """Write HF leaderboard JSON rows to disk."""
    payload = report.hf_leaderboard_json(task_suite=task_suite)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"HF leaderboard written to {output_path}")


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
        "> **Primary metric:** tokens per correct answer = mean_total_tokens ÷ pass_rate  ",
        "> **Secondary metric:** cost-of-pass = estimated mean_api_cost_usd ÷ pass_rate  ",
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
    rows: list[tuple[str, str, str, str, str, str, str, str, str, str]] = []
    for cid in cids:
        if cid not in summary:
            continue
        s = summary[cid]
        cname = next((c.name for c in conditions if c.id == cid), cid)
        rows.append(
            (
                cname,
                f"{_fmt_pct(s['mean_pass_rate'])} "
                f"({_fmt_ci_pct(s['ci_pass_rate_low'], s['ci_pass_rate_high'])})",
                _fmt_tokens(s["mean_total_tokens"]),
                _fmt_tokens(s["mean_tokens_per_correct_answer"]),
                _fmt_cost(s["mean_api_cost_usd"]),
                f"{s['mean_quality_score']:.2f}",
                f"{_fmt_cost(s['mean_cost_of_pass'])} "
                f"({_fmt_ci_cost(s['ci_cop_low'], s['ci_cop_high'])})",
                _fmt_pct(s["mean_first_pass_rate"]),
                f"{s['mean_consistency_score']:.2f}",
                _fmt_lift(s["mean_scaffold_lift"]),
            )
        )

    # Best-value variables reserved for future bolding logic (not yet applied)

    header = (
        "| Condition | Pass Rate (95% CI) | Mean Tokens | Tokens/Correct | Mean Cost | Quality | "
        "Cost-of-Pass (95% CI) | First Pass | Consistency | Scaffold Lift |"
    )
    sep = (
        "|-----------|---------------------|-------------|----------------|-----------|---------|"
        "------------------------|------------|-------------|---------------|"
    )
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

        lines.append(
            "| Condition | Pass Rate | Tokens | Tokens/Correct | Cost | Quality | "
            "CoP | First Pass | Lift |"
        )
        lines.append(
            "|-----------|-----------|--------|----------------|------|---------|-----|------------|------|"
        )

        def _slice_order(s: SliceStats) -> int:
            return cids.index(s.condition_id) if s.condition_id in cids else 99

        for s in sorted(task_slices, key=_slice_order):
            cname = next((c.name for c in conditions if c.id == s.condition_id), s.condition_id)
            lines.append(
                f"| {cname} "
                f"| {_fmt_pct(s.pass_rate)} "
                f"| {_fmt_tokens(s.mean_total_tokens)} "
                f"| {_fmt_tokens(s.tokens_per_correct_answer)} "
                f"| {_fmt_cost(s.mean_api_cost_usd)} "
                f"| {s.mean_quality_score:.2f} "
                f"| {_fmt_cost(s.cost_of_pass)} "
                f"| {_fmt_pct(s.first_pass_rate)} "
                f"| {_fmt_lift(s.scaffold_lift)} |"
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
    # Section 3: Key findings and leaderboard narrative
    # ------------------------------------------------------------------
    lines += [
        render_key_claims(report),
        render_scaffold_lift_matrix(report, conditions, tasks),
        render_democratization_table(report),
        render_pareto_scatter_data(report),
        "## HF Leaderboard JSON Preview",
        "",
        "```json",
        json.dumps(report.hf_leaderboard_json(), indent=2),
        "```",
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
        raw_rows.append(
            {
                "task": run.task_id,
                "condition": run.condition_id,
                "rep": run.rep,
                "tokens": run.total_tokens,
                "cost_usd": round(run.api_cost_usd, 6),
                "passed": run.passed,
                "quality": round(run.quality_score, 3),
                "rework_turns": run.rework_turns,
            }
        )
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
