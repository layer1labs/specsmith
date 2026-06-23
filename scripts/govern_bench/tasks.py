"""Task registry for the governance efficiency benchmark.

Loads task definitions from tasks/*.yml and exposes them as BenchTask objects.
Each BenchTask corresponds to one YAML file in scripts/govern_bench/tasks/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:  # noqa: BLE001  # intentional: soft import, raise clearly below
    yaml = None  # type: ignore[assignment]

TASKS_DIR = Path(__file__).parent / "tasks"


@dataclass
class BenchTask:
    """A single benchmark task definition loaded from a YAML file."""

    id: str
    title: str
    category: str
    difficulty: str
    project: str
    task_prompt: str
    acceptance_criteria: str

    # Optional metadata
    estimated_tokens_ungoverned: int = 0
    estimated_tokens_specsmith_full: int = 0
    expected_files_changed: list[str] = field(default_factory=list)
    regression_risk: str = "unknown"
    known_failure_modes: list[str] = field(default_factory=list)
    governance_signals: dict = field(default_factory=dict)
    scoring_override: dict | None = None

    # Task-type flags
    scope_discipline_metric: bool = False
    clarification_rate_task: bool = False
    destructive_intent_task: bool = False
    safety_gate_task: bool = False
    exit_code_discipline_metric: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> BenchTask:
        """Construct a BenchTask from a parsed YAML dict."""
        # Required fields
        required = ("id", "title", "category", "difficulty", "project",
                    "task_prompt", "acceptance_criteria")
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"Task YAML missing required fields: {missing}")

        return cls(
            id=data["id"],
            title=data["title"],
            category=data["category"],
            difficulty=data["difficulty"],
            project=data["project"],
            task_prompt=data["task_prompt"].strip(),
            acceptance_criteria=data["acceptance_criteria"].strip(),
            estimated_tokens_ungoverned=data.get("estimated_tokens_ungoverned", 0),
            estimated_tokens_specsmith_full=data.get("estimated_tokens_specsmith_full", 0),
            expected_files_changed=data.get("expected_files_changed") or [],
            regression_risk=str(data.get("regression_risk", "unknown")),
            known_failure_modes=data.get("known_failure_modes") or [],
            governance_signals=data.get("governance_signals") or {},
            scoring_override=data.get("scoring_override"),
            scope_discipline_metric=bool(data.get("scope_discipline_metric", False)),
            clarification_rate_task=bool(data.get("clarification_rate_task", False)),
            destructive_intent_task=bool(data.get("destructive_intent_task", False)),
            safety_gate_task=bool(data.get("safety_gate_task", False)),
            exit_code_discipline_metric=bool(data.get("exit_code_discipline_metric", False)),
        )

    @property
    def is_safety_task(self) -> bool:
        return self.destructive_intent_task or self.safety_gate_task

    @property
    def is_clarification_task(self) -> bool:
        return self.clarification_rate_task

    @property
    def uses_todo_api(self) -> bool:
        return self.project == "agentic-todo-api"

    @property
    def uses_cli_tool(self) -> bool:
        return self.project == "agentic-cli-tool"


def load_all_tasks(tasks_dir: Path | None = None) -> list[BenchTask]:
    """Load all benchmark tasks from tasks/*.yml.

    Returns tasks sorted by ID (T1, T2, ..., T7).
    """
    if yaml is None:
        raise ImportError(
            "PyYAML is required to load task definitions. "
            "Install it with: pip install pyyaml"
        )

    directory = tasks_dir or TASKS_DIR
    if not directory.exists():
        raise FileNotFoundError(f"Tasks directory not found: {directory}")

    tasks: list[BenchTask] = []
    for yml_file in sorted(directory.glob("T*.yml")):
        with yml_file.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        try:
            task = BenchTask.from_dict(data)
            tasks.append(task)
        except ValueError as exc:
            raise ValueError(f"Error loading {yml_file.name}: {exc}") from exc

    return tasks


def get_task(task_id: str, tasks_dir: Path | None = None) -> BenchTask:
    """Return a single task by ID (e.g. 'T1'), raising KeyError if not found."""
    all_tasks = load_all_tasks(tasks_dir)
    task_map = {t.id: t for t in all_tasks}
    if task_id not in task_map:
        raise KeyError(
            f"Task {task_id!r} not found. Available: {sorted(task_map)}"
        )
    return task_map[task_id]


def task_summary() -> None:  # pragma: no cover
    """Print a summary table of all tasks (for development use)."""
    tasks = load_all_tasks()
    print(f"{'ID':<4} {'Category':<25} {'Difficulty':<25} {'Project':<22} Title")
    print("-" * 110)
    for t in tasks:
        flags = []
        if t.is_safety_task:
            flags.append("SAFETY")
        if t.is_clarification_task:
            flags.append("CLARIFY")
        if t.scope_discipline_metric:
            flags.append("SCOPE")
        flag_str = f"[{','.join(flags)}]" if flags else ""
        print(f"{t.id:<4} {t.category:<25} {t.difficulty:<25} {t.project:<22} {t.title} {flag_str}")


if __name__ == "__main__":
    task_summary()
