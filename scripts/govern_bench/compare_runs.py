"""compare_runs.py — generate a cross-model comparison report.

Reads two (or more) bench-results-*.json files and produces a Markdown
report comparing cost-of-pass, pass rate, token usage, and quality
across all conditions, side-by-side for each model.

Usage:
    # Model label is read from each row's "model" field; FILE:MODEL overrides it.
    python -m govern_bench.compare_runs \\
        bench-results-llama8b.json \\
        bench-results-qwen30b.json \\
        --output docs/site/model-comparison.md
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from govern_bench.metrics import model_tier, strip_provider_route

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_results(path: str) -> list[dict]:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path}: benchmark result must be a non-empty JSON array")
    return rows


_REQUIRED_RESULT_FIELDS = {
    "task",
    "condition",
    "rep",
    "model",
    "tokens",
    "cost_usd",
    "passed",
    "quality",
    "rework_turns",
    "skipped",
    "error",
}


def validate_results(
    rows: list[dict], source: str = "benchmark results"
) -> set[tuple[str, str, int]]:
    """Reject incomplete, duplicate, or uneven benchmark cells.

    Provider failures are operationally unavailable observations, not model
    failures.  Treating them as zero-pass/zero-cost rows biases every aggregate,
    so comparison generation is deliberately fail-closed.
    """
    cells: set[tuple[str, str, int]] = set()
    reps_by_slice: dict[tuple[str, str], set[int]] = defaultdict(set)
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{source}: row {index} is not an object")
        missing = sorted(_REQUIRED_RESULT_FIELDS - row.keys())
        if missing:
            raise ValueError(f"{source}: row {index} is missing fields {missing}")
        if row["skipped"] or row["error"]:
            detail = row["error"] or "cell marked skipped"
            raise ValueError(
                f"{source}: incomplete cell {row['task']}/{row['condition']}/rep-{row['rep']}: "
                f"{detail}"
            )
        key = (str(row["task"]), str(row["condition"]), int(row["rep"]))
        if key in cells:
            raise ValueError(f"{source}: duplicate cell {key}")
        cells.add(key)
        reps_by_slice[key[:2]].add(key[2])

    expected_reps = next(iter(reps_by_slice.values()))
    uneven = {
        f"{task}/{condition}": sorted(reps)
        for (task, condition), reps in reps_by_slice.items()
        if reps != expected_reps
    }
    if uneven:
        raise ValueError(
            f"{source}: benchmark slices have uneven repetition sets; "
            f"expected {sorted(expected_reps)}, found {uneven}"
        )
    return cells


def validate_comparable(cell_sets: list[tuple[str, set[tuple[str, str, int]]]]) -> None:
    """Require every model file to contain the same task/condition/rep cells."""
    if not cell_sets:
        raise ValueError("no benchmark result sets supplied")
    reference_name, reference = cell_sets[0]
    for name, cells in cell_sets[1:]:
        if cells != reference:
            missing = sorted(reference - cells)[:10]
            extra = sorted(cells - reference)[:10]
            raise ValueError(
                f"{name}: cell set differs from {reference_name}; missing={missing}, extra={extra}"
            )


def rollup(rows: list[dict]) -> dict[str, dict[str, dict]]:
    """Return {task -> {condition -> stats}}."""
    validate_results(rows)
    by_tc: dict[tuple, list] = defaultdict(list)
    for r in rows:
        by_tc[(r["task"], r["condition"])].append(r)

    result: dict[str, dict[str, dict]] = defaultdict(dict)
    for (task, cond), reps in by_tc.items():
        passed = [r for r in reps if r["passed"]]
        pass_rate = len(passed) / len(reps)
        avg_tokens = sum(r["tokens"] for r in reps) / len(reps)
        avg_cost = sum(r["cost_usd"] for r in reps) / len(reps)
        avg_quality = sum(r["quality"] for r in reps) / len(reps)
        avg_turns = sum(r["rework_turns"] for r in reps) / len(reps)
        first_pass_rate = sum(1 for r in reps if r["rework_turns"] <= 1) / len(reps)
        pass_values = [1.0 if r["passed"] else 0.0 for r in reps]
        consistency_score = (
            1.0 if len(pass_values) < 2 else max(0.0, 1.0 - statistics.pstdev(pass_values))
        )
        cop = avg_cost / pass_rate if pass_rate > 0 else float("inf")
        result[task][cond] = {
            "pass_rate": pass_rate,
            "avg_tokens": avg_tokens,
            "avg_cost": avg_cost,
            "avg_quality": avg_quality,
            "avg_turns": avg_turns,
            "first_pass_rate": first_pass_rate,
            "consistency_score": consistency_score,
            "cost_of_pass": cop,
            "n_reps": len(reps),
        }

    for _task, conditions in result.items():
        baseline = conditions.get("UNGOVERNED", {}).get("pass_rate")
        for stats in conditions.values():
            stats["scaffold_lift"] = stats["pass_rate"] - baseline if baseline is not None else None
    return result


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

CONDITION_ORDER = [
    "UNGOVERNED",
    "CONTEXT_ONLY",
    "CURSOR_RULES",
    "COPILOT_INSTRUCTIONS",
    "CODEX_AGENTS_MD",
    "CLINE_RULES",
    "AIDER_CONVENTIONS",
    "BMAD_STYLE",
    "OPENSPEC_STYLE",
    "AGILE_TDD",
    "SPECSMITH_LIGHT",
    "SPECSMITH_FULL",
    "SPECSMITH_DISPATCH",
]

CONDITION_LABELS = {
    "UNGOVERNED": "Raw agent (ungoverned)",
    "CONTEXT_ONLY": "CLAUDE.md / AGENTS.md",
    "CURSOR_RULES": "Cursor .cursor/rules",
    "COPILOT_INSTRUCTIONS": "GitHub Copilot instructions",
    "CODEX_AGENTS_MD": "OpenAI Codex CLI AGENTS.md",
    "CLINE_RULES": "Cline .clinerules",
    "AIDER_CONVENTIONS": "Aider CONVENTIONS.md",
    "BMAD_STYLE": "BMAD Blueprint→Milestone",
    "OPENSPEC_STYLE": "OpenSpec REQUIREMENTS.md",
    "AGILE_TDD": "Agile BDD / TDD",
    "SPECSMITH_LIGHT": "specsmith LIGHT (preflight)",
    "SPECSMITH_FULL": "specsmith FULL (governed)",
    "SPECSMITH_DISPATCH": "specsmith DISPATCH (multi-agent)",
}

TASK_LABELS = {
    "T1": "T1 — Add paginated endpoint (feature add)",
    "T2": "T2 — Fix mutable-default bug",
    "T6": "T6 — Ambiguous optimisation request (clarification gate)",
    "T7": "T7 — Delete auth middleware (safety gate)",
    "T10": "T10 — Add filtering / query params (feature add)",
    "T11": "T11 — Refactor without behaviour change",
    "T13": "T13 — CLI tool feature (stdlib only)",
}

# Coding tasks in headline-preference order. The headline section uses the
# first one that has data, so a run that omits T1 still gets a sensible
# headline instead of an empty section.
CODING_TASK_ORDER = ["T1", "T2", "T10", "T11", "T13"]


def _derive_model_label(rows: list[dict], path: str) -> str:
    """Return the model label from row 'model' fields, else the file stem."""
    labels = [
        strip_provider_route(r["model"])
        for r in rows
        if isinstance(r, dict) and r.get("model") and r.get("model") != "unknown"
    ]
    if labels:
        return max(set(labels), key=labels.count)
    return Path(path).stem


def split_input_spec(spec: str) -> tuple[str, str | None]:
    """Split optional ``FILE:LABEL`` without corrupting Windows drive paths."""
    windows_drive_path = len(spec) >= 3 and spec[1] == ":" and spec[2] in "\\/"
    if ":" in spec and not windows_drive_path:
        path, label = spec.rsplit(":", 1)
        return path, label
    return spec, None


def _headline_task(
    models: list[tuple[str, dict[str, dict[str, dict]]]], all_tasks: list[str]
) -> str | None:
    """Pick the first coding task present in any model's data."""
    for task in CODING_TASK_ORDER:
        if any(task in data for _, data in models):
            return task
    return all_tasks[0] if all_tasks else None


def _reps_label(models: list[tuple[str, dict[str, dict[str, dict]]]]) -> str:
    """Describe how many reps underlie the means (dynamic, not hardcoded)."""
    reps_seen = {
        stats["n_reps"] for _, data in models for conds in data.values() for stats in conds.values()
    }
    if len(reps_seen) == 1:
        return f"{next(iter(reps_seen))} reps"
    if reps_seen:
        return f"{min(reps_seen)}–{max(reps_seen)} reps"
    return "all reps"


def _cop(v: float) -> str:
    return f"${v:.5f}" if v < float("inf") else "∞"


def _pct(v: float) -> str:
    return f"{v * 100:.0f}%"


def _tok(v: float) -> str:
    return f"{v / 1000:.1f}k"


def _usd(v: float) -> str:
    if v < 0.001:
        return f"${v * 1000:.3f}m"  # micro-dollars as milli-dollars
    return f"${v:.4f}"


def _quality(v: float) -> str:
    return f"{v:.2f}"


def _delta(a: float, b: float) -> str:
    """Show cost delta: how many × more expensive is b vs a."""
    if a <= 0 or b <= 0:
        return "—"
    ratio = b / a
    if ratio < 1:
        return f"**{1 / ratio:.1f}× cheaper**"
    return f"{ratio:.1f}× costlier"


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def render_comparison(
    models: list[tuple[str, dict[str, dict[str, dict]]]],
    tasks: list[str] | None = None,
) -> str:
    lines: list[str] = []
    all_tasks = tasks or sorted({t for _, d in models for t in d})
    reps_label = _reps_label(models)

    lines += [
        "# specsmith Governance Efficiency — Model Comparison",
        "",
        "**Models compared:** " + " · ".join(f"{m} ({model_tier(m)})" for m, _ in models),
        "",
        "> **Cost-of-pass (CoP)** = mean_cost_per_run ÷ pass_rate.",
        "> Lower = cheaper per correct answer. ∞ = condition never passed.",
        "",
    ]

    # ── Per-task tables ────────────────────────────────────────────────────
    for task in all_tasks:
        label = TASK_LABELS.get(task, task)
        lines += [f"## {label}", ""]

        # Build header: Condition | Model-A pass% | tokens | CoP | Model-B pass% | ...
        header_parts = ["| Condition"]
        sep_parts = ["|----------"]
        for mname, _ in models:
            header_parts += [f" {mname} Pass%", "Tokens", "Cost/run", "CoP"]
            sep_parts += ["------:", "------:", "--------:", "--------:"]
        header_parts.append("")
        sep_parts.append("")
        lines.append("|".join(header_parts))
        lines.append("|".join(sep_parts))

        for cond in CONDITION_ORDER:
            label_c = CONDITION_LABELS.get(cond, cond)
            row = [f"| {label_c}"]
            for _mname, data in models:
                task_data = data.get(task, {})
                s = task_data.get(cond)
                if s is None:
                    row += [" —", " —", " —", " —"]
                else:
                    bold_s = "**" if cond.startswith("SPECSMITH") else ""
                    bold_e = "**" if cond.startswith("SPECSMITH") else ""
                    row.append(f" {bold_s}{_pct(s['pass_rate'])}{bold_e}")
                    row.append(f" {_tok(s['avg_tokens'])}")
                    row.append(f" {_usd(s['avg_cost'])}")
                    row.append(f" {bold_s}{_cop(s['cost_of_pass'])}{bold_e}")
            row.append("")
            lines.append("|".join(row))
        lines.append("")

    # ── Cross-task summary ─────────────────────────────────────────────────
    lines += [
        "## Cross-task summary",
        "",
        "Mean across all tasks shown above.",
        "",
    ]
    header_parts = ["| Condition"]
    sep_parts = ["|----------"]
    for mname, _ in models:
        header_parts += [f" {mname} Pass%", "Mean CoP", "$/mo @20/day"]
        sep_parts += ["------:", "--------:", "-----------:"]
    header_parts.append("")
    sep_parts.append("")
    lines.append("|".join(header_parts))
    lines.append("|".join(sep_parts))

    for cond in CONDITION_ORDER:
        label_c = CONDITION_LABELS.get(cond, cond)
        row = [f"| {label_c}"]
        for _mname, data in models:
            cops = []
            pass_rates = []
            costs = []
            for task in all_tasks:
                s = data.get(task, {}).get(cond)
                if s:
                    pass_rates.append(s["pass_rate"])
                    costs.append(s["avg_cost"])
                    if s["cost_of_pass"] < float("inf"):
                        cops.append(s["cost_of_pass"])
            if not pass_rates:
                row += [" —", " —", " —"]
                continue
            mean_pr = sum(pass_rates) / len(pass_rates)
            mean_cop = sum(cops) / len(cops) if cops else float("inf")
            mean_cost = sum(costs) / len(costs)
            monthly = mean_cost * 20 * 22  # 20 tasks/day, 22 days/month
            bold_s = "**" if cond.startswith("SPECSMITH") else ""
            bold_e = "**" if cond.startswith("SPECSMITH") else ""
            row.append(f" {bold_s}{_pct(mean_pr)}{bold_e}")
            row.append(f" {bold_s}{_cop(mean_cop)}{bold_e}")
            row.append(f" {bold_s}${monthly:.2f}{bold_e}")
        row.append("")
        lines.append("|".join(row))
    lines.append("")

    # ── Headline findings ──────────────────────────────────────────────────
    lines += [
        "## Headline findings",
        "",
    ]

    # Headline uses the first available coding task (T1, T2, T10, T11, T13) so
    # an open-model run that omits T1 still produces a meaningful headline.
    headline_task = _headline_task(models, all_tasks)
    if headline_task is not None:
        best: list[tuple[float, str, str]] = []
        for mname, data in models:
            for cond in CONDITION_ORDER:
                s = data.get(headline_task, {}).get(cond)
                if s and s["cost_of_pass"] < float("inf"):
                    best.append((s["cost_of_pass"], mname, cond))
        best.sort()

        if best:
            cheapest_cop, cheapest_model, cheapest_cond = best[0]
            lines.append(
                f"**Cheapest cost-of-pass on {headline_task}:** "
                f"`{cheapest_model}` + `{CONDITION_LABELS.get(cheapest_cond, cheapest_cond)}` "
                f"at {_cop(cheapest_cop)}"
            )
            lines.append("")

            for mname, data in models:
                s = data.get(headline_task, {}).get("UNGOVERNED")
                sf = data.get(headline_task, {}).get("SPECSMITH_FULL")
                if s and sf and s["cost_of_pass"] < float("inf") and sf["cost_of_pass"] > 0:
                    ratio = s["cost_of_pass"] / sf["cost_of_pass"]
                    lines.append(
                        f"**`{mname}`: SPECSMITH_FULL vs UNGOVERNED on {headline_task}** — "
                        f"governance is {ratio:.1f}× cheaper per correct answer "
                        f"({_cop(sf['cost_of_pass'])} vs {_cop(s['cost_of_pass'])})"
                    )
            lines.append("")

        # Ungoverned vs governed pass rates (the governance value story)
        lines += [
            f"### Governance gate performance ({headline_task} coding task pass rates)",
            "",
        ]
        for mname, data in models:
            ug = data.get(headline_task, {}).get("UNGOVERNED")
            sf = data.get(headline_task, {}).get("SPECSMITH_FULL")
            if ug and sf:
                lines.append(
                    f"- **{mname}** — ungoverned: {_pct(ug['pass_rate'])} pass / "
                    f"specsmith FULL: {_pct(sf['pass_rate'])} pass"
                )
        lines += [
            "",
            f"### Key model comparison ({headline_task}, mean across {reps_label})",
            "",
        ]
        for mname, data in models:
            sf = data.get(headline_task, {}).get("SPECSMITH_FULL")
            ug = data.get(headline_task, {}).get("UNGOVERNED")
            if sf:
                lines.append(
                    f"- **{mname} + SPECSMITH_FULL**: {_pct(sf['pass_rate'])} pass, "
                    f"{_tok(sf['avg_tokens'])} tokens, {_usd(sf['avg_cost'])}/run, "
                    f"CoP {_cop(sf['cost_of_pass'])}"
                )
            if ug:
                lines.append(
                    f"- **{mname} + UNGOVERNED**: {_pct(ug['pass_rate'])} pass, "
                    f"{_tok(ug['avg_tokens'])} tokens, {_usd(ug['avg_cost'])}/run, "
                    f"CoP {_cop(ug['cost_of_pass'])}"
                )
    lines += ["", "---", "", "_Generated by `scripts/govern_bench/compare_runs.py`_", ""]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate cross-model benchmark comparison report")
    parser.add_argument(
        "inputs",
        nargs="+",
        metavar="FILE[:MODEL]",
        help=(
            "JSON result file(s). The model label is read from each row's "
            "'model' field; append ':LABEL' to override (e.g. results.json:my-label)."
        ),
    )
    parser.add_argument(
        "--output",
        "-o",
        default="docs/site/model-comparison.md",
        help="Output Markdown path",
    )
    parser.add_argument(
        "--tasks",
        "-t",
        nargs="*",
        help="Restrict to specific task IDs (default: all)",
    )
    args = parser.parse_args()

    models: list[tuple[str, dict]] = []
    cell_sets: list[tuple[str, set[tuple[str, str, int]]]] = []
    try:
        for spec in args.inputs:
            # Accept bare FILE (label auto-derived from the JSON 'model' field) or
            # an explicit FILE:LABEL override.
            path, label = split_input_spec(spec)
            rows = load_results(path)
            if label is None:
                label = _derive_model_label(rows, path)
            cells = validate_results(rows, path)
            data = rollup(rows)
            models.append((label, data))
            cell_sets.append((label, cells))
            print(f"Loaded {len(rows)} runs for {label!r} from {path}")
        validate_comparable(cell_sets)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"[FATAL] Invalid benchmark comparison input: {exc}", file=sys.stderr)
        return 1

    md = render_comparison(models, tasks=args.tasks)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"Report written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
