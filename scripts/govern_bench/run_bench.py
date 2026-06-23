"""run_bench.py — CLI entry point for the governance efficiency benchmark.

Usage:
    # List all tasks and conditions (dry-run):
    python -m govern_bench.run_bench --list

    # Run a single task × condition (one rep) for development:
    python -m govern_bench.run_bench --task T1 --condition UNGOVERNED --reps 1 --dry-run

    # Run the full benchmark (7 tasks × 6 conditions × 5 reps = 210 runs):
    python -m govern_bench.run_bench --reps 5 --output docs/site/efficiency-benchmark.md

    # Run only governance-gate tasks (T6, T7) across all conditions:
    python -m govern_bench.run_bench --task T6 --task T7 --reps 3

    # Run a specific subset of conditions for quick comparison:
    python -m govern_bench.run_bench --condition UNGOVERNED --condition SPECSMITH_FULL --reps 3

Environment variables:
    BENCH_JUDGE_MODEL     LLM judge model (default: claude-haiku-4-5)
    BENCH_JUDGE_PROVIDER  LLM judge provider: anthropic|openai (default: anthropic)
    ANTHROPIC_API_KEY     Required for Anthropic judge
    OPENAI_API_KEY        Required for OpenAI judge
    BENCH_DRY_RUN         Set to '1' to skip actual agent calls (for CI)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure govern_bench is importable when run as a script  # noqa: E402
_HERE = Path(__file__).parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from govern_bench.conditions import CONDITION_MAP, CONDITIONS  # noqa: E402
from govern_bench.metrics import BenchReport, RunResult  # noqa: E402
from govern_bench.report import write_report  # noqa: E402
from govern_bench.tasks import load_all_tasks  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the specsmith governance efficiency benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--task", "-t",
        action="append",
        metavar="ID",
        help="Task ID to run (e.g. T1). Repeat for multiple. Default: all tasks.",
    )
    parser.add_argument(
        "--condition", "-c",
        action="append",
        metavar="ID",
        help=(
            "Condition ID to run. Repeat for multiple. "
            "Default: all conditions. "
            f"Available: {', '.join(CONDITION_MAP)}"
        ),
    )
    parser.add_argument(
        "--reps", "-r",
        type=int,
        default=5,
        help="Number of repetitions per task × condition cell (default: 5)",
    )
    parser.add_argument(
        "--output", "-o",
        default="docs/site/efficiency-benchmark.md",
        help="Output path for the Markdown report (default: docs/site/efficiency-benchmark.md)",
    )
    parser.add_argument(
        "--model", "-m",
        default="claude-sonnet-4-5",
        help="Agent model to use for task runs (default: claude-sonnet-4-5)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=os.environ.get("BENCH_DRY_RUN") == "1",
        help="Skip actual agent calls; generate a report with dummy data",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all tasks and conditions, then exit",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        metavar="PATH",
        help="Write raw RunResult data as JSON to this path",
    )
    return parser.parse_args()


def _list_all() -> None:
    """Print all tasks and conditions to stdout."""
    tasks = load_all_tasks()
    print("\n=== BENCHMARK TASKS ===\n")
    for t in tasks:
        flags = []
        if t.is_safety_task:
            flags.append("[SAFETY]")
        if t.is_clarification_task:
            flags.append("[CLARIFY]")
        if t.scope_discipline_metric:
            flags.append("[SCOPE]")
        flag_str = " ".join(flags)
        print(f"  {t.id:4}  {t.title}  {flag_str}")
        print(f"        category={t.category}  project={t.project}  risk={t.regression_risk}")
        print()

    print("=== CONDITIONS ===\n")
    for c in CONDITIONS:
        print(f"  {c.id:20}  overhead_turns={c.overhead_turns}  tags={c.tags}")
        print(f"        {c.description[:80]}...")
        print()


def _make_dummy_run(task_id: str, condition_id: str, rep: int, model: str) -> RunResult:
    """Generate a plausible dummy RunResult for dry-run mode."""
    import random
    rng = random.Random(f"{task_id}:{condition_id}:{rep}")

    # Governance conditions use more tokens but pass more often
    governance_overhead = {
        "UNGOVERNED": 0,
        "CONTEXT_ONLY": 200,
        "BMAD_STYLE": 500,
        "OPENSPEC_STYLE": 400,
        "SPECSMITH_LIGHT": 800,
        "SPECSMITH_FULL": 1500,
    }
    base_pass_rates = {
        "UNGOVERNED": 0.44,
        "CONTEXT_ONLY": 0.55,
        "BMAD_STYLE": 0.65,
        "OPENSPEC_STYLE": 0.70,
        "SPECSMITH_LIGHT": 0.80,
        "SPECSMITH_FULL": 0.95,
    }
    base_quality = {
        "UNGOVERNED": 0.55,
        "CONTEXT_ONLY": 0.65,
        "BMAD_STYLE": 0.72,
        "OPENSPEC_STYLE": 0.75,
        "SPECSMITH_LIGHT": 0.82,
        "SPECSMITH_FULL": 0.91,
    }

    overhead = governance_overhead.get(condition_id, 0)
    pass_rate = base_pass_rates.get(condition_id, 0.5)
    quality_base = base_quality.get(condition_id, 0.6)

    inp = rng.randint(2000, 4000) + overhead
    out = rng.randint(800, 2000) + overhead // 2
    passed = rng.random() < pass_rate
    quality = min(1.0, max(0.0, rng.gauss(quality_base, 0.1)))

    from govern_bench.metrics import estimate_cost
    cost = estimate_cost(model, inp, out)

    return RunResult(
        task_id=task_id,
        condition_id=condition_id,
        rep=rep,
        input_tokens=inp,
        output_tokens=out,
        model=model,
        api_cost_usd=cost,
        lint_passed=passed,
        tests_passed=passed,
        quality_score=quality,
        rework_turns=1 if passed else rng.randint(2, 4),
        governance_turns=overhead // 500,
        wall_clock_s=rng.uniform(15.0, 90.0),
    )


def main() -> int:
    args = _parse_args()

    if args.list:
        _list_all()
        return 0

    # Resolve tasks and conditions
    all_tasks = load_all_tasks()
    task_map = {t.id: t for t in all_tasks}

    if args.task:
        unknown = [t for t in args.task if t not in task_map]
        if unknown:
            print(f"Error: Unknown task IDs: {unknown}", file=sys.stderr)
            return 1
        tasks = [task_map[t] for t in args.task]
    else:
        tasks = all_tasks

    if args.condition:
        unknown = [c for c in args.condition if c not in CONDITION_MAP]
        if unknown:
            print(f"Error: Unknown condition IDs: {unknown}", file=sys.stderr)
            return 1
        conditions = [CONDITION_MAP[c] for c in args.condition]
    else:
        conditions = CONDITIONS

    total_runs = len(tasks) * len(conditions) * args.reps
    print(
        f"Benchmark: {len(tasks)} tasks × {len(conditions)} conditions × {args.reps} reps "
        f"= {total_runs} total runs"
    )
    if args.dry_run:
        print("DRY RUN — generating dummy data (no agent calls)")

    report = BenchReport()
    run_num = 0

    for task in tasks:
        for condition in conditions:
            for rep in range(1, args.reps + 1):
                run_num += 1
                print(
                    f"  [{run_num:>3}/{total_runs}] {task.id} × {condition.id} rep={rep}",
                    end="",
                    flush=True,
                )

                if args.dry_run:
                    result = _make_dummy_run(task.id, condition.id, rep, args.model)
                else:
                    from govern_bench.harness import run_task  # noqa: E402, PLC0415
                    try:
                        result = run_task(task, condition, rep=rep, model=args.model)
                    except RuntimeError as exc:
                        print(f"\n  [ERROR] {exc}", file=sys.stderr)
                        return 1
                    except Exception as exc:  # noqa: BLE001
                        print(f"\n  [RUN ERROR] {exc}", file=sys.stderr)
                        from govern_bench.metrics import RunResult
                        result = RunResult(
                            task_id=task.id, condition_id=condition.id, rep=rep,
                            model=args.model, error=str(exc), skipped=True,
                        )

                status = "PASS" if result.passed else "FAIL"
                cost_str = f"${result.api_cost_usd:.4f}"
                print(f"  → {status}  tokens={result.total_tokens}  cost={cost_str}")
                report.runs.append(result)

    # Write JSON output if requested
    if args.json_output:
        json_path = Path(args.json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        rows = [
            {
                "task": r.task_id,
                "condition": r.condition_id,
                "rep": r.rep,
                "tokens": r.total_tokens,
                "cost_usd": round(r.api_cost_usd, 6),
                "passed": r.passed,
                "quality": round(r.quality_score, 3),
                "rework_turns": r.rework_turns,
                "lint_passed": r.lint_passed,
                "tests_passed": r.tests_passed,
            }
            for r in report.runs
        ]
        json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"Raw JSON written to {json_path}")

    # Write Markdown report
    output_path = Path(args.output)
    write_report(report, conditions, tasks, output_path, model=args.model, reps=args.reps)

    # Print summary
    print("\n=== SUMMARY ===")
    summary = report.condition_summary()
    print(f"{'Condition':<30} {'Pass%':>6} {'Tokens':>8} {'Cost':>10} {'Quality':>8} {'CoP':>12}")
    print("-" * 80)
    def _sort_by_pass(item: tuple) -> float:
        return -item[1]["mean_pass_rate"]

    for cid, s in sorted(summary.items(), key=_sort_by_pass):
        cop = s["mean_cost_of_pass"]
        cop_str = f"${cop:.4f}" if cop < float("inf") else "∞"
        print(
            f"{cid:<30} "
            f"{s['mean_pass_rate']*100:>5.0f}% "
            f"{s['mean_total_tokens']:>8.0f} "
            f"${s['mean_api_cost_usd']:>9.4f} "
            f"{s['mean_quality_score']:>8.2f} "
            f"{cop_str:>12}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
