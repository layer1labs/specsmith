"""compare_runs.py — generate a cross-model comparison report.

Reads two (or more) bench-results-*.json files and produces a Markdown
report comparing cost-of-pass, pass rate, token usage, and quality
across all conditions, side-by-side for each model.

Usage:
    python -m govern_bench.compare_runs \\
        bench-results-4omini.json:gpt-4o-mini \\
        bench-results-gpt55.json:gpt-5.5 \\
        --output docs/site/model-comparison.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_results(path: str) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rollup(rows: list[dict]) -> dict[str, dict[str, dict]]:
    """Return {task -> {condition -> stats}}."""
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
        cop = avg_cost / pass_rate if pass_rate > 0 else float("inf")
        result[task][cond] = {
            "pass_rate": pass_rate,
            "avg_tokens": avg_tokens,
            "avg_cost": avg_cost,
            "avg_quality": avg_quality,
            "avg_turns": avg_turns,
            "cost_of_pass": cop,
            "n_reps": len(reps),
        }
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
]

CONDITION_LABELS = {
    "UNGOVERNED":           "Raw agent (ungoverned)",
    "CONTEXT_ONLY":         "CLAUDE.md / AGENTS.md",
    "CURSOR_RULES":         "Cursor .cursor/rules",
    "COPILOT_INSTRUCTIONS": "GitHub Copilot instructions",
    "CODEX_AGENTS_MD":      "OpenAI Codex CLI AGENTS.md",
    "CLINE_RULES":          "Cline .clinerules",
    "AIDER_CONVENTIONS":    "Aider CONVENTIONS.md",
    "BMAD_STYLE":           "BMAD Blueprint→Milestone",
    "OPENSPEC_STYLE":       "OpenSpec REQUIREMENTS.md",
    "AGILE_TDD":            "Agile BDD / TDD",
    "SPECSMITH_LIGHT":      "specsmith LIGHT (preflight)",
    "SPECSMITH_FULL":       "specsmith FULL (governed)",
}

TASK_LABELS = {
    "T1": "T1 — Add paginated endpoint (feature add)",
    "T2": "T2 — Fix mutable-default bug",
    "T6": "T6 — Ambiguous optimisation request (clarification gate)",
    "T7": "T7 — Delete auth middleware (safety gate)",
}


def _cop(v: float) -> str:
    return f"${v:.5f}" if v < float("inf") else "∞"


def _pct(v: float) -> str:
    return f"{v * 100:.0f}%"


def _tok(v: float) -> str:
    return f"{v / 1000:.1f}k"


def _usd(v: float) -> str:
    if v < 0.001:
        return f"${v * 1000:.3f}m"   # micro-dollars as milli-dollars
    return f"${v:.4f}"


def _quality(v: float) -> str:
    return f"{v:.2f}"


def _delta(a: float, b: float) -> str:
    """Show cost delta: how many × more expensive is b vs a."""
    if a <= 0 or b <= 0:
        return "—"
    ratio = b / a
    if ratio < 1:
        return f"**{1/ratio:.1f}× cheaper**"
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

    lines += [
        "# specsmith Governance Efficiency — Model Comparison",
        "",
        "**Models compared:** " + " · ".join(m for m, _ in models),
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

    # Find cheapest CoP for T1 across all model×condition combos
    best: list[tuple[float, str, str]] = []
    for mname, data in models:
        for cond in CONDITION_ORDER:
            s = data.get("T1", {}).get(cond)
            if s and s["cost_of_pass"] < float("inf"):
                best.append((s["cost_of_pass"], mname, cond))
    best.sort()

    if best:
        cheapest_cop, cheapest_model, cheapest_cond = best[0]
        lines.append(
            f"**Cheapest cost-of-pass on T1:** "
            f"`{cheapest_model}` + `{CONDITION_LABELS.get(cheapest_cond, cheapest_cond)}` "
            f"at {_cop(cheapest_cop)}"
        )
        lines.append("")

        # Find gpt-5.5 UNGOVERNED T1
        for mname, data in models:
            s = data.get("T1", {}).get("UNGOVERNED")
            sf = data.get("T1", {}).get("SPECSMITH_FULL")
            if s and sf and s["cost_of_pass"] < float("inf"):
                ratio = s["cost_of_pass"] / sf["cost_of_pass"] if sf["cost_of_pass"] > 0 else 0
                lines.append(
                    f"**`{mname}`: SPECSMITH_FULL vs UNGOVERNED on T1** — "
                    f"governance is {ratio:.1f}× cheaper per correct answer "
                    f"({_cop(sf['cost_of_pass'])} vs {_cop(s['cost_of_pass'])})"
                )
        lines.append("")

    # Ungoverned pass rates (the governance value story)
    lines += [
        "### Governance gate performance (T1 coding task pass rates)",
        "",
    ]
    for mname, data in models:
        ug = data.get("T1", {}).get("UNGOVERNED")
        sf = data.get("T1", {}).get("SPECSMITH_FULL")
        if ug and sf:
            lines.append(
                f"- **{mname}** — ungoverned: {_pct(ug['pass_rate'])} pass / "
                f"specsmith FULL: {_pct(sf['pass_rate'])} pass"
            )
    lines += [
        "",
        "### Key model comparison (T1, mean across 2 reps)",
        "",
    ]
    for mname, data in models:
        sf = data.get("T1", {}).get("SPECSMITH_FULL")
        ug = data.get("T1", {}).get("UNGOVERNED")
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
    parser = argparse.ArgumentParser(
        description="Generate cross-model benchmark comparison report"
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        metavar="FILE:MODEL",
        help="JSON result files with model label (e.g. bench-results-4omini.json:gpt-4o-mini)",
    )
    parser.add_argument(
        "--output", "-o",
        default="docs/site/model-comparison.md",
        help="Output Markdown path",
    )
    parser.add_argument(
        "--tasks", "-t",
        nargs="*",
        help="Restrict to specific task IDs (default: all)",
    )
    args = parser.parse_args()

    models: list[tuple[str, dict]] = []
    for spec in args.inputs:
        if ":" not in spec:
            print(f"Error: expected FILE:MODEL, got {spec!r}", file=sys.stderr)
            return 1
        path, label = spec.rsplit(":", 1)
        rows = load_results(path)
        data = rollup(rows)
        models.append((label, data))
        print(f"Loaded {len(rows)} runs for {label!r} from {path}")

    md = render_comparison(models, tasks=args.tasks)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"Report written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
