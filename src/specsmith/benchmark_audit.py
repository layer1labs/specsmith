"""Post-run weakness analysis for GovernanceBench result artifacts.

This module is intentionally provider-neutral.  It consumes the raw JSON rows
already emitted by GovernanceBench and turns failures, excess context, and
verification disagreements into structured evidence instead of another model
judgement.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from itertools import product
from pathlib import Path
from typing import Any

_REQUIRED_ROW_FIELDS = {
    "task",
    "condition",
    "rep",
    "model",
    "input_tokens",
    "output_tokens",
    "passed",
    "skipped",
    "error",
}


@dataclass(slots=True)
class BenchmarkWeakness:
    """One reproducible weakness found in benchmark evidence."""

    code: str
    severity: str
    title: str
    evidence: str
    recommendation: str
    tasks: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BenchmarkExperimentDecision:
    """Deterministic next step selected from measured benchmark evidence."""

    action: str
    ready_for_repetition: bool
    rationale: str
    evidence_codes: list[str] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BenchmarkWeaknessReport:
    """Structured post-run benchmark audit."""

    source: str
    dry_run: bool
    total_rows: int
    valid_rows: int
    complete: bool
    models: list[str]
    tasks: list[str]
    conditions: list[str]
    minimum_repetitions: int
    condition_metrics: dict[str, dict[str, float | int | None]]
    task_type_metrics: dict[str, dict[str, dict[str, float | int | None]]]
    weaknesses: list[BenchmarkWeakness]
    next_experiment: BenchmarkExperimentDecision

    @property
    def high_or_critical(self) -> int:
        return sum(1 for item in self.weaknesses if item.severity in {"high", "critical"})

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["high_or_critical"] = self.high_or_critical
        return payload


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _as_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _next_experiment_decision(
    weaknesses: list[BenchmarkWeakness],
    *,
    complete: bool,
    dry_run: bool,
    minimum_repetitions: int,
    tasks: list[str],
    conditions: list[str],
) -> BenchmarkExperimentDecision:
    """Select the next experiment without spending another model judgement."""
    codes = {item.code for item in weaknesses}

    def affects_governed_path(item: BenchmarkWeakness) -> bool:
        return not item.conditions or any(
            condition.startswith("SPECSMITH") for condition in item.conditions
        )

    artifact_blockers = {
        "synthetic_evidence",
        "incomplete_evidence",
        "unreplayable_diff",
        "duplicate_cells",
        "missing_cells",
        "uneven_repetitions",
    }
    correctness_blockers = {
        "acceptance_gap",
        "blank_overwrite_rejected",
        "correctness_regression",
        "cursor_correctness_regression",
        "premature_text_stop",
        "turn_budget_exhausted",
        "verification_exhausted",
    }
    efficiency_blockers = {
        "broad_reread_churn",
        "context_dominance",
        "cursor_efficiency_regression",
        "milestone_fragmentation",
        "repeated_tool_loop",
        "scope_expansion",
        "token_amplification",
        "tool_call_serialization",
        "verification_repair_outlier",
    }

    if dry_run or not complete or codes & artifact_blockers:
        selected = [item for item in weaknesses if item.code in artifact_blockers]
        rationale = (
            selected[0].recommendation
            if selected
            else "Repair the artifact and rerun the identical matched grid."
        )
        return BenchmarkExperimentDecision(
            action="reject_artifact",
            ready_for_repetition=False,
            rationale=rationale,
            evidence_codes=sorted(codes & artifact_blockers),
            tasks=tasks,
            conditions=conditions,
        )

    correctness = [
        item
        for item in weaknesses
        if item.code in correctness_blockers and affects_governed_path(item)
    ]
    if correctness:
        primary = correctness[0]
        return BenchmarkExperimentDecision(
            action="repair_and_rerun",
            ready_for_repetition=False,
            rationale=primary.recommendation,
            evidence_codes=sorted({item.code for item in correctness}),
            tasks=sorted({task for item in correctness for task in item.tasks}) or tasks,
            conditions=(
                sorted({condition for item in correctness for condition in item.conditions})
                or conditions
            ),
        )

    frontier_regressions = [
        item
        for item in weaknesses
        if item.code == "frontier_efficiency_regression" and affects_governed_path(item)
    ]
    if frontier_regressions:
        primary = frontier_regressions[0]
        return BenchmarkExperimentDecision(
            action="advance_candidate",
            ready_for_repetition=False,
            rationale=primary.recommendation,
            evidence_codes=["frontier_efficiency_regression"],
            tasks=primary.tasks or tasks,
            conditions=primary.conditions or conditions,
        )

    efficiency = [
        item
        for item in weaknesses
        if item.code in efficiency_blockers and affects_governed_path(item)
    ]
    if efficiency:
        primary = efficiency[0]
        return BenchmarkExperimentDecision(
            action="optimize_and_rerun",
            ready_for_repetition=False,
            rationale=primary.recommendation,
            evidence_codes=sorted({item.code for item in efficiency}),
            tasks=sorted({task for item in efficiency for task in item.tasks}) or tasks,
            conditions=(
                sorted({condition for item in efficiency for condition in item.conditions})
                or conditions
            ),
        )

    if minimum_repetitions < 5:
        return BenchmarkExperimentDecision(
            action="repeat_screen",
            ready_for_repetition=True,
            rationale="Correct diagnostic cells earned a matched five-repetition screen.",
            evidence_codes=["undersampled"] if "undersampled" in codes else [],
            tasks=tasks,
            conditions=conditions,
        )
    if minimum_repetitions < 10:
        return BenchmarkExperimentDecision(
            action="expand_release_sample",
            ready_for_repetition=True,
            rationale="Screening passed; expand the identical grid to ten repetitions.",
            tasks=tasks,
            conditions=conditions,
        )
    return BenchmarkExperimentDecision(
        action="publish_or_expand",
        ready_for_repetition=True,
        rationale="Release-sized evidence has no measured correctness or efficiency blocker.",
        tasks=tasks,
        conditions=conditions,
    )


def _condition_rollups(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, float | int | None]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("condition") or "unknown")].append(row)

    result: dict[str, dict[str, float | int | None]] = {}
    for condition, items in sorted(grouped.items()):
        count = len(items)
        passed = sum(bool(item.get("passed")) for item in items)
        mean_input = sum(_as_int(item.get("input_tokens")) for item in items) / count
        mean_output = sum(_as_int(item.get("output_tokens")) for item in items) / count
        mean_turns = sum(_as_int(item.get("llm_turns")) for item in items) / count
        mean_tokens = mean_input + mean_output
        pass_rate = passed / count
        result[condition] = {
            "rows": count,
            "passed": passed,
            "pass_rate": round(pass_rate, 6),
            "mean_input_tokens": round(mean_input, 3),
            "mean_output_tokens": round(mean_output, 3),
            "mean_total_tokens": round(mean_tokens, 3),
            "mean_llm_turns": round(mean_turns, 3),
            "tokens_per_correct_answer": (round(mean_tokens / pass_rate, 3) if pass_rate else None),
        }
    return result


def _task_type_rollups(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, dict[str, float | int | None]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        category = str(row.get("category") or "").strip()
        if not category:
            category = "long_horizon" if str(row.get("horizon") or "") == "long" else "standard"
        grouped[category].append(row)
    return {category: _condition_rollups(items) for category, items in sorted(grouped.items())}


def _tool_targets(row: dict[str, Any], prefix: str) -> list[str]:
    targets: list[str] = []
    for event in row.get("agent_transcript") or []:
        if not isinstance(event, dict) or event.get("role") != "assistant":
            continue
        for target in event.get("tool_targets") or []:
            value = str(target)
            if value.startswith(prefix):
                targets.append(value.removeprefix(prefix))
    return targets


def _assistant_tool_counts(row: dict[str, Any]) -> list[int]:
    """Return tool-call counts for assistant turns that issued at least one call."""
    counts: list[int] = []
    for event in row.get("agent_transcript") or []:
        if not isinstance(event, dict) or event.get("role") != "assistant":
            continue
        calls = event.get("tool_calls") or event.get("tool_targets") or []
        if isinstance(calls, list) and calls:
            counts.append(len(calls))
    return counts


def _normalized_path(value: Any) -> str:
    return str(value or "").replace("\\", "/").removeprefix("./").casefold()


def _top_level_components(paths: list[str]) -> set[str]:
    return {path.replace("\\", "/").removeprefix("./").partition("/")[0] for path in paths if path}


def _row_problem(row: dict[str, Any]) -> str | None:
    missing = sorted(_REQUIRED_ROW_FIELDS - row.keys())
    if missing:
        return f"missing fields: {', '.join(missing)}"
    if not str(row.get("task") or "").strip():
        return "task must be non-empty"
    if not str(row.get("condition") or "").strip():
        return "condition must be non-empty"
    if not str(row.get("model") or "").strip():
        return "model must be non-empty"
    if _as_int(row.get("rep")) < 1:
        return "rep must be a positive integer"
    if _as_int(row.get("input_tokens")) < 0 or _as_int(row.get("output_tokens")) < 0:
        return "token counts must be non-negative"
    return None


def _task_pass_rates(rows: list[dict[str, Any]]) -> dict[tuple[str, str], float]:
    grouped: dict[tuple[str, str], list[bool]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("task")), str(row.get("condition")))].append(bool(row.get("passed")))
    return {key: sum(values) / len(values) for key, values in grouped.items()}


def _unreplayable_diff(value: Any) -> bool:
    """Return whether stored patch evidence is known to be structurally incomplete."""
    if not isinstance(value, str) or not value:
        return False
    if "[diff compacted]" in value:
        return True
    marker = "--- a/"
    offset = value.find(marker, 1)
    while offset >= 0:
        if value[offset - 1] != "\n":
            return True
        offset = value.find(marker, offset + len(marker))
    return False


def load_benchmark_reference_envelopes(path: Path | None = None) -> dict[str, dict[str, Any]]:
    """Load valid screening anchors; malformed or non-screening entries fail closed."""
    target = path or Path(__file__).with_name("benchmark_reference_envelopes.json")
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    tasks = payload.get("tasks") if isinstance(payload, dict) else None
    if not isinstance(tasks, dict):
        return {}
    valid: dict[str, dict[str, Any]] = {}
    for task, envelope in tasks.items():
        if (
            isinstance(envelope, dict)
            and _as_float(envelope.get("tokens_per_correct_answer")) > 0
            and _as_int(envelope.get("repetitions")) >= 5
            and str(envelope.get("condition") or "").startswith("SPECSMITH")
            and bool(envelope.get("model"))
            and bool(envelope.get("commit"))
            and str(envelope.get("source") or "").startswith("https://")
        ):
            valid[str(task)] = envelope
    return valid


def audit_benchmark_rows(
    rows: list[dict[str, Any]],
    *,
    source: str = "memory",
    dry_run: bool = False,
    reference_envelopes: dict[str, dict[str, Any]] | None = None,
) -> BenchmarkWeaknessReport:
    """Analyze raw benchmark rows and return deterministic weakness evidence."""
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Benchmark results must be a JSON list of objects")

    weaknesses: list[BenchmarkWeakness] = []
    invalid_rows: list[tuple[int, dict[str, Any], str]] = []
    valid: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        problem = _row_problem(row)
        if row.get("skipped") or row.get("error"):
            problem = str(row.get("error") or "row was skipped")
        if problem:
            invalid_rows.append((index, row, problem))
        else:
            valid.append(row)
    complete = bool(rows) and not invalid_rows

    if dry_run:
        weaknesses.append(
            BenchmarkWeakness(
                code="synthetic_evidence",
                severity="info",
                title="Dry-run evidence cannot support product claims",
                evidence="The artifact was generated without provider calls.",
                recommendation=(
                    "Use dry runs only for harness integrity, then run matched live cells."
                ),
            )
        )
    if invalid_rows or not rows:
        examples = "; ".join(f"row {index}: {reason}" for index, _row, reason in invalid_rows[:3])
        weaknesses.append(
            BenchmarkWeakness(
                code="incomplete_evidence",
                severity="critical",
                title="Benchmark evidence is incomplete",
                evidence=(
                    f"{len(invalid_rows)} of {len(rows)} rows were unusable."
                    + (f" {examples}." if examples else "")
                ),
                recommendation=(
                    "Repair provider or harness failures and rerun the identical cell grid."
                ),
            )
        )

    unreplayable = [row for row in valid if _unreplayable_diff(row.get("final_diff"))]
    if unreplayable:
        complete = False
        affected_tasks = sorted({str(row.get("task")) for row in unreplayable})
        affected_conditions = sorted({str(row.get("condition")) for row in unreplayable})
        weaknesses.append(
            BenchmarkWeakness(
                code="unreplayable_diff",
                severity="critical",
                title="Stored project diff cannot be replayed",
                evidence=(
                    f"{len(unreplayable)} row(s) contain a compacted or malformed final_diff."
                ),
                recommendation=(
                    "Reject the artifact, repair diff serialization, and rerun the same cells."
                ),
                tasks=affected_tasks,
                conditions=affected_conditions,
            )
        )

    exhausted = [row for row in valid if row.get("stop_reason") == "max_turns"]
    if exhausted:
        weaknesses.append(
            BenchmarkWeakness(
                code="turn_budget_exhausted",
                severity="high",
                title="Agent exhausted the bounded turn budget",
                evidence=f"{len(exhausted)} row(s) stopped at max_turns before completion.",
                recommendation=(
                    "Inspect tool-target traces for loops, then reduce repeated work or split "
                    "the task without increasing the cap blindly."
                ),
                tasks=sorted({str(row.get("task")) for row in exhausted}),
                conditions=sorted({str(row.get("condition")) for row in exhausted}),
            )
        )

    premature_text_stops = [
        row for row in valid if not row.get("passed") and row.get("stop_reason") == "text_response"
    ]
    if premature_text_stops:
        weaknesses.append(
            BenchmarkWeakness(
                code="premature_text_stop",
                severity="high",
                title="Model narrated a next step without completing the tool workflow",
                evidence=(
                    f"{len(premature_text_stops)} failed row(s) ended on a text-only response."
                ),
                recommendation=(
                    "Use a bounded controller continuation only when narration promises another "
                    "action; otherwise fail closed rather than treating prose as completion."
                ),
                tasks=sorted({str(row.get("task")) for row in premature_text_stops}),
                conditions=sorted({str(row.get("condition")) for row in premature_text_stops}),
            )
        )

    serialized_tools: list[dict[str, Any]] = []
    for row in valid:
        counts = _assistant_tool_counts(row)
        if (
            not row.get("passed")
            and row.get("stop_reason") in {"max_turns", "text_response"}
            and sum(counts) >= 6
            and len(counts) >= 6
            and max(counts, default=0) == 1
        ):
            serialized_tools.append(row)
    if serialized_tools:
        total_calls = sum(sum(_assistant_tool_counts(row)) for row in serialized_tools)
        total_action_turns = sum(len(_assistant_tool_counts(row)) for row in serialized_tools)
        weaknesses.append(
            BenchmarkWeakness(
                code="tool_call_serialization",
                severity="high",
                title="Model spent one turn per independent tool action",
                evidence=(
                    f"{len(serialized_tools)} failed row(s) issued {total_calls} tool calls "
                    f"across {total_action_turns} separate action turns."
                ),
                recommendation=(
                    "Reduce the active tool schema, expose a controller-owned change map, and "
                    "use a serving route/scaffold that supports batched independent calls."
                ),
                tasks=sorted({str(row.get("task")) for row in serialized_tools}),
                conditions=sorted({str(row.get("condition")) for row in serialized_tools}),
            )
        )

    scope_expansions: list[tuple[dict[str, Any], list[str]]] = []
    for row in valid:
        expected = {
            _normalized_path(path) for path in row.get("expected_files_changed") or [] if path
        }
        if not expected:
            continue
        extras = [
            str(path)
            for path in row.get("files_written") or []
            if path and _normalized_path(path) not in expected
        ]
        if extras:
            scope_expansions.append((row, extras))
    if scope_expansions:
        extra_paths = sorted(
            {path for _row, paths in scope_expansions for path in paths},
            key=str.casefold,
        )
        weaknesses.append(
            BenchmarkWeakness(
                code="scope_expansion",
                severity="medium",
                title="Implementation wrote beyond declared requirement boundaries",
                evidence=(
                    f"{len(scope_expansions)} row(s) wrote {len(extra_paths)} undeclared path(s): "
                    + ", ".join(extra_paths[:8])
                ),
                recommendation=(
                    "Review whether each extra path is required; otherwise constrain retrieval "
                    "and edits to the requirement-linked change map."
                ),
                tasks=sorted({str(row.get("task")) for row, _paths in scope_expansions}),
                conditions=sorted({str(row.get("condition")) for row, _paths in scope_expansions}),
            )
        )

    repeated_loops = [
        row
        for row in valid
        if row.get("stop_reason") == "repeated_tool_loop"
        or any(
            isinstance(event, dict) and bool(event.get("repeated_tool_target"))
            for event in row.get("agent_transcript") or []
        )
    ]
    if repeated_loops:
        weaknesses.append(
            BenchmarkWeakness(
                code="repeated_tool_loop",
                severity=(
                    "high"
                    if any(row.get("stop_reason") == "repeated_tool_loop" for row in repeated_loops)
                    else "medium"
                ),
                title="Agent repeated one tool target without making progress",
                evidence=f"{len(repeated_loops)} row(s) triggered the deterministic loop guard.",
                recommendation=(
                    "Review the provider tool-call route and use the bounded controller recovery; "
                    "do not pay for additional identical turns."
                ),
                tasks=sorted({str(row.get("task")) for row in repeated_loops}),
                conditions=sorted({str(row.get("condition")) for row in repeated_loops}),
            )
        )

    reread_churn: list[dict[str, Any]] = []
    for row in valid:
        reads = _tool_targets(row, "read_file:")
        repeated_reads = len(reads) - len(set(reads))
        if len(reads) >= 10 and repeated_reads >= max(5, len(reads) // 2):
            reread_churn.append(row)
    if reread_churn:
        total_reads = sum(len(_tool_targets(row, "read_file:")) for row in reread_churn)
        total_repeats = sum(
            len(_tool_targets(row, "read_file:")) - len(set(_tool_targets(row, "read_file:")))
            for row in reread_churn
        )
        weaknesses.append(
            BenchmarkWeakness(
                code="broad_reread_churn",
                severity=(
                    "high"
                    if any(row.get("stop_reason") == "max_turns" for row in reread_churn)
                    else "medium"
                ),
                title="Agent repeatedly reread broad unchanged context",
                evidence=(
                    f"{len(reread_churn)} row(s) repeated {total_repeats} of "
                    f"{total_reads} file reads."
                ),
                recommendation=(
                    "Return content once per file version, replace unchanged rereads with "
                    "digest receipts, and retain only the latest compact progress state."
                ),
                tasks=sorted({str(row.get("task")) for row in reread_churn}),
                conditions=sorted({str(row.get("condition")) for row in reread_churn}),
            )
        )

    fragmented: list[dict[str, Any]] = []
    for row in valid:
        writes = _tool_targets(row, "write_file:")
        is_long = str(row.get("horizon") or "").casefold() == "long"
        if (
            is_long
            and not row.get("passed")
            and row.get("stop_reason") == "max_turns"
            and len(writes) >= 6
            and len(_top_level_components(writes)) >= 3
        ):
            fragmented.append(row)
    if fragmented:
        weaknesses.append(
            BenchmarkWeakness(
                code="milestone_fragmentation",
                severity="high",
                title="Long-horizon work advanced serially without reaching a milestone boundary",
                evidence=(
                    f"{len(fragmented)} row(s) changed at least three components but exhausted "
                    "the turn budget before completion."
                ),
                recommendation=(
                    "Expose a bounded controller-owned milestone map, batch independent edits "
                    "inside the active milestone, and validate only at milestone boundaries."
                ),
                tasks=sorted({str(row.get("task")) for row in fragmented}),
                conditions=sorted({str(row.get("condition")) for row in fragmented}),
            )
        )

    rejected_blank_writes = [
        row
        for row in valid
        if any(
            isinstance(event, dict)
            and any(
                isinstance(result, str) and "ERROR: refusing to replace non-empty file" in result
                for result in event.get("results") or []
            )
            for event in row.get("agent_transcript") or []
        )
    ]
    if rejected_blank_writes:
        weaknesses.append(
            BenchmarkWeakness(
                code="blank_overwrite_rejected",
                severity="medium",
                title="Tool guard rejected a destructive blank overwrite",
                evidence=(
                    f"{len(rejected_blank_writes)} row(s) attempted to replace a non-empty "
                    "project file with blank content."
                ),
                recommendation=(
                    "Inspect the model's write call and recovery trace; keep the guard enabled "
                    "and require the complete replacement body."
                ),
                tasks=sorted({str(row.get("task")) for row in rejected_blank_writes}),
                conditions=sorted({str(row.get("condition")) for row in rejected_blank_writes}),
            )
        )

    verification_exhausted = [
        row for row in valid if row.get("stop_reason") == "verification_exhausted"
    ]
    if verification_exhausted:
        weaknesses.append(
            BenchmarkWeakness(
                code="verification_exhausted",
                severity="high",
                title="Independent verification did not reach equilibrium",
                evidence=(
                    f"{len(verification_exhausted)} FULL row(s) used the bounded repair budget."
                ),
                recommendation=(
                    "Trace the remaining acceptance boundary; improve evidence or task "
                    "decomposition instead of weakening the oracle."
                ),
                tasks=sorted({str(row.get("task")) for row in verification_exhausted}),
                conditions=sorted({str(row.get("condition")) for row in verification_exhausted}),
            )
        )

    cell_keys = [
        (
            str(row.get("model") or "unknown"),
            str(row.get("task") or "unknown"),
            str(row.get("condition") or "unknown"),
            _as_int(row.get("rep")),
        )
        for row in valid
    ]
    duplicates = [key for key, count in Counter(cell_keys).items() if count > 1]
    if duplicates:
        complete = False
        weaknesses.append(
            BenchmarkWeakness(
                code="duplicate_cells",
                severity="critical",
                title="Benchmark contains duplicate model/task/condition repetitions",
                evidence=f"{len(duplicates)} duplicate cell key(s) were found.",
                recommendation="Reject the artifact and regenerate one row per requested cell.",
            )
        )

    repetition_counts = Counter((model, task, condition) for model, task, condition, _ in cell_keys)
    models = sorted({str(row["model"]) for row in valid})
    tasks = sorted({str(row["task"]) for row in valid})
    conditions = sorted({str(row["condition"]) for row in valid})
    expected_cells = list(product(models, tasks, conditions))
    missing_cells = [cell for cell in expected_cells if repetition_counts[cell] == 0]
    if missing_cells:
        complete = False
        preview = ", ".join("/".join(cell) for cell in missing_cells[:3])
        weaknesses.append(
            BenchmarkWeakness(
                code="missing_cells",
                severity="critical",
                title="Benchmark comparison grid is incomplete",
                evidence=(
                    f"{len(missing_cells)} model/task/condition cell(s) are absent: {preview}."
                ),
                recommendation="Rerun every missing cell with the same repetition set.",
            )
        )
    if repetition_counts and len(set(repetition_counts.values())) > 1:
        complete = False
        weaknesses.append(
            BenchmarkWeakness(
                code="uneven_repetitions",
                severity="critical",
                title="Compared cells have uneven repetition counts",
                evidence=(
                    f"Observed repetition counts: {sorted(set(repetition_counts.values()))}."
                ),
                recommendation="Rerun or filter to one identical repetition set for every cell.",
            )
        )

    minimum_reps = min(
        (repetition_counts[cell] for cell in expected_cells),
        default=0,
    )
    if valid and minimum_reps < 5:
        weaknesses.append(
            BenchmarkWeakness(
                code="undersampled",
                severity="medium",
                title="Result is diagnostic rather than screening evidence",
                evidence=(
                    "The smallest complete model/task/condition cell has "
                    f"{minimum_reps} repetition(s)."
                ),
                recommendation=(
                    "Use at least five repetitions for screening and ten for release claims."
                ),
            )
        )

    acceptance_gaps = [
        row
        for row in valid
        if row.get("project_tests_passed") is True and row.get("acceptance_oracle_passed") is False
    ]
    if acceptance_gaps:
        tasks = sorted({str(row.get("task")) for row in acceptance_gaps})
        conditions = sorted({str(row.get("condition")) for row in acceptance_gaps})
        weaknesses.append(
            BenchmarkWeakness(
                code="acceptance_gap",
                severity="high",
                title="Public tests passed while the independent oracle failed",
                evidence=f"{len(acceptance_gaps)} row(s) disagreed on tasks {', '.join(tasks)}.",
                recommendation=(
                    "Trace the hidden boundary back to a requirement and add an immutable "
                    "independent test."
                ),
                tasks=tasks,
                conditions=conditions,
            )
        )

    metrics = _condition_rollups(valid)
    raw = metrics.get("UNGOVERNED")
    if raw:
        raw_tpca = _as_float(raw.get("tokens_per_correct_answer"))
        for condition, item in metrics.items():
            if not condition.startswith("SPECSMITH"):
                continue
            tpca = _as_float(item.get("tokens_per_correct_answer"))
            if raw_tpca > 0 and tpca > raw_tpca * 1.10:
                weaknesses.append(
                    BenchmarkWeakness(
                        code="token_amplification",
                        severity="medium",
                        title=f"{condition} amplifies tokens per correct answer",
                        evidence=f"TPCA {tpca:.0f} vs ungoverned {raw_tpca:.0f} (>10% overhead).",
                        recommendation=(
                            "Remove repeated context or calls before adding prompt instructions."
                        ),
                        conditions=[condition, "UNGOVERNED"],
                    )
                )

        pass_rates = _task_pass_rates(valid)
        tasks = sorted({str(row.get("task")) for row in valid})
        for condition in sorted(c for c in metrics if c.startswith("SPECSMITH")):
            regressed = [
                task
                for task in tasks
                if (task, condition) in pass_rates
                and (task, "UNGOVERNED") in pass_rates
                and pass_rates[(task, condition)] < pass_rates[(task, "UNGOVERNED")]
            ]
            if regressed:
                weaknesses.append(
                    BenchmarkWeakness(
                        code="correctness_regression",
                        severity="high",
                        title=f"{condition} regresses task-level correctness",
                        evidence=f"Lower pass rate than ungoverned on {', '.join(regressed)}.",
                        recommendation=(
                            "Keep the lighter condition as default and repair each failing "
                            "boundary before rerun."
                        ),
                        tasks=regressed,
                        conditions=[condition, "UNGOVERNED"],
                    )
                )

    task_condition_metrics = {
        task: _condition_rollups([row for row in valid if str(row.get("task")) == task])
        for task in sorted({str(row.get("task")) for row in valid})
    }
    for task, envelope in (reference_envelopes or {}).items():
        condition = str(envelope.get("condition") or "")
        anchor_model = str(envelope.get("model") or "")
        anchor_tpca = _as_float(envelope.get("tokens_per_correct_answer"))
        if not condition.startswith("SPECSMITH") or not anchor_model or anchor_tpca <= 0:
            continue
        task_rows = [
            row
            for row in valid
            if str(row.get("task")) == task and str(row.get("condition")) == condition
        ]
        for model in sorted({str(row.get("model")) for row in task_rows} - {anchor_model}):
            candidate = _condition_rollups(
                [row for row in task_rows if str(row.get("model")) == model]
            ).get(condition)
            if not candidate or _as_float(candidate.get("pass_rate")) < 1:
                continue
            candidate_tpca = _as_float(candidate.get("tokens_per_correct_answer"))
            if candidate_tpca > anchor_tpca * 1.10:
                weaknesses.append(
                    BenchmarkWeakness(
                        code="frontier_efficiency_regression",
                        severity="medium",
                        title=f"{model} is correct but materially less efficient than the anchor",
                        evidence=(
                            f"{task} {condition} TPCA {candidate_tpca:.0f} vs "
                            f"{anchor_model} {anchor_tpca:.0f} "
                            f"({candidate_tpca / anchor_tpca:.2f}x)."
                        ),
                        recommendation=(
                            "Do not repeat this cell yet; advance to the next admitted candidate "
                            "or optimize the measured serving/controller boundary first."
                        ),
                        tasks=[task],
                        conditions=[condition],
                    )
                )

    cursor_correctness: dict[str, list[str]] = defaultdict(list)
    cursor_efficiency: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for task, task_metrics in task_condition_metrics.items():
        cursor = task_metrics.get("CURSOR_RULES")
        if not cursor:
            continue
        cursor_pass_rate = _as_float(cursor.get("pass_rate"))
        cursor_tpca = _as_float(cursor.get("tokens_per_correct_answer"))
        for condition, item in task_metrics.items():
            if not condition.startswith("SPECSMITH"):
                continue
            pass_rate = _as_float(item.get("pass_rate"))
            tpca = _as_float(item.get("tokens_per_correct_answer"))
            if pass_rate < cursor_pass_rate:
                cursor_correctness[condition].append(task)
            if cursor_tpca > 0 and tpca > cursor_tpca * 1.10:
                cursor_efficiency[condition].append((task, tpca / cursor_tpca))

    for condition, regressed_tasks in sorted(cursor_correctness.items()):
        weaknesses.append(
            BenchmarkWeakness(
                code="cursor_correctness_regression",
                severity="high",
                title=f"{condition} trails Cursor rules on task correctness",
                evidence=f"Lower pass rate than CURSOR_RULES on {', '.join(regressed_tasks)}.",
                recommendation=(
                    "Repair the independent acceptance boundary before optimizing token cost."
                ),
                tasks=regressed_tasks,
                conditions=[condition, "CURSOR_RULES"],
            )
        )
    for condition, regressions in sorted(cursor_efficiency.items()):
        evidence = ", ".join(f"{task} {ratio:.2f}x" for task, ratio in regressions)
        weaknesses.append(
            BenchmarkWeakness(
                code="cursor_efficiency_regression",
                severity="medium",
                title=f"{condition} spends more tokens per correct answer than Cursor rules",
                evidence=f"TPCA regression above 10%: {evidence}.",
                recommendation=(
                    "Remove task-class-specific rereads, planning turns, or verification churn "
                    "before making comparative claims."
                ),
                tasks=[task for task, _ratio in regressions],
                conditions=[condition, "CURSOR_RULES"],
            )
        )

    grouped_turns: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in valid:
        grouped_turns[
            (
                str(row.get("model")),
                str(row.get("task")),
                str(row.get("condition")),
            )
        ].append(row)
    repair_outliers: list[dict[str, Any]] = []
    for group in grouped_turns.values():
        if len(group) < 5:
            continue
        turns = sorted(_as_int(row.get("llm_turns")) for row in group)
        median_turns = turns[len(turns) // 2]
        repair_outliers.extend(
            row
            for row in group
            if _as_int(row.get("llm_turns")) > max(median_turns * 1.5, median_turns + 3)
        )
    if repair_outliers:
        weaknesses.append(
            BenchmarkWeakness(
                code="verification_repair_outlier",
                severity="medium",
                title="Verification repair created a high-turn cost outlier",
                evidence=f"{len(repair_outliers)} row(s) exceeded 1.5x the cell median turns.",
                recommendation=(
                    "Classify the failed boundary, return only its focused evidence, and cap "
                    "repair context instead of replaying the full task history."
                ),
                tasks=sorted({str(row.get("task")) for row in repair_outliers}),
                conditions=sorted({str(row.get("condition")) for row in repair_outliers}),
            )
        )

    for condition, item in metrics.items():
        mean_input = _as_float(item.get("mean_input_tokens"))
        mean_output = _as_float(item.get("mean_output_tokens"))
        if mean_output > 0 and mean_input / mean_output >= 10:
            weaknesses.append(
                BenchmarkWeakness(
                    code="context_dominance",
                    severity="medium",
                    title=f"Input history dominates {condition} spend",
                    evidence=f"Mean input/output ratio is {mean_input / mean_output:.1f}:1.",
                    recommendation=(
                        "Use just-in-time retrieval, stable cached prefixes, and compact "
                        "redundant tool output."
                    ),
                    conditions=[condition],
                )
            )

    report_tasks = sorted({str(row.get("task") or "unknown") for row in rows})
    report_conditions = sorted({str(row.get("condition") or "unknown") for row in rows})
    return BenchmarkWeaknessReport(
        source=source,
        dry_run=dry_run,
        total_rows=len(rows),
        valid_rows=len(valid),
        complete=complete,
        models=sorted({str(row.get("model") or "unknown") for row in rows}),
        tasks=report_tasks,
        conditions=report_conditions,
        minimum_repetitions=minimum_reps,
        condition_metrics=metrics,
        task_type_metrics=_task_type_rollups(valid),
        weaknesses=weaknesses,
        next_experiment=_next_experiment_decision(
            weaknesses,
            complete=complete,
            dry_run=dry_run,
            minimum_repetitions=minimum_reps,
            tasks=report_tasks,
            conditions=report_conditions,
        ),
    )


def audit_benchmark_file(
    path: Path,
    *,
    dry_run: bool | None = None,
) -> BenchmarkWeaknessReport:
    """Load and audit one GovernanceBench JSON artifact."""
    resolved = path.resolve()
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    rows = (
        payload
        if isinstance(payload, list) and all(isinstance(row, dict) for row in payload)
        else [{}]
    )
    inferred_dry_run = bool(rows) and all(row.get("dry_run") is True for row in rows)
    return audit_benchmark_rows(
        rows,
        source=str(resolved),
        dry_run=inferred_dry_run if dry_run is None else dry_run,
        reference_envelopes=load_benchmark_reference_envelopes(),
    )


def write_benchmark_audit(report: BenchmarkWeaknessReport, path: Path) -> None:
    """Write a machine-readable weakness report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2, allow_nan=False), encoding="utf-8")
