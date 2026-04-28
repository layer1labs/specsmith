# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Credits — AI token/cost spend tracking per project and session."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class CreditEntry:
    """Single credit usage record."""

    timestamp: str = ""
    session_id: str = ""
    model: str = ""
    provider: str = ""  # openai, anthropic, google, local, ollama, etc.
    tokens_in: int = 0
    tokens_out: int = 0
    estimated_cost_usd: float = 0.0
    task: str = ""  # what was being done
    duration_seconds: float = 0.0


@dataclass
class CreditBudget:
    """Budget/alert configuration for a project."""

    monthly_cap_usd: float = 0.0  # 0 = unlimited
    alert_threshold_pct: int = 80  # warn at this % of cap
    alert_watermarks_usd: list[float] = field(default_factory=lambda: [5.0, 10.0, 25.0, 50.0])
    enabled: bool = True
    enforcement_mode: str = "soft"  # soft (warn only) | hard (block when exceeded)

    def is_exceeded(self, current_spend_usd: float) -> bool:
        """True if the monthly cap is configured and exceeded."""
        return self.monthly_cap_usd > 0 and current_spend_usd >= self.monthly_cap_usd

    def should_block(self, current_spend_usd: float) -> bool:
        """True if this is a hard cap AND it is exceeded."""
        return self.enforcement_mode == "hard" and self.is_exceeded(current_spend_usd)


@dataclass
class CreditSummary:
    """Aggregate credit summary."""

    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost_usd: float = 0.0
    session_count: int = 0
    entry_count: int = 0
    by_model: dict[str, float] = field(default_factory=dict)
    by_provider: dict[str, float] = field(default_factory=dict)
    by_task: dict[str, float] = field(default_factory=dict)
    budget: CreditBudget | None = None
    alerts: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Cost estimation (per 1M tokens, approximate 2026 pricing)
# ---------------------------------------------------------------------------

_COST_PER_1M: dict[str, tuple[float, float]] = {
    # (input $/1M, output $/1M)
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "claude-sonnet": (3.00, 15.00),
    "claude-haiku": (0.25, 1.25),
    "claude-opus": (15.00, 75.00),
    "gemini-pro": (1.25, 5.00),
    "gemini-flash": (0.075, 0.30),
    "local": (0.0, 0.0),
    "unknown": (3.00, 15.00),  # conservative default
}


def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """Estimate USD cost for a token usage."""
    key = model.lower()
    # Fuzzy match: find the best matching model key
    for k in _COST_PER_1M:
        if k in key:
            rates = _COST_PER_1M[k]
            return (tokens_in * rates[0] + tokens_out * rates[1]) / 1_000_000
    rates = _COST_PER_1M["unknown"]
    return (tokens_in * rates[0] + tokens_out * rates[1]) / 1_000_000


# ---------------------------------------------------------------------------
# Storage — JSON file at .specsmith/credits.json
# ---------------------------------------------------------------------------

_CREDITS_DIR = ".specsmith"
_CREDITS_FILE = "credits.json"
_BUDGET_FILE = "credit-budget.json"


def _get_credits_path(root: Path) -> Path:
    """Get path to credits JSON file, creating dir if needed."""
    path = root / _CREDITS_DIR / _CREDITS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _get_budget_path(root: Path) -> Path:
    return root / _CREDITS_DIR / _BUDGET_FILE


def _load_entries(root: Path) -> list[CreditEntry]:
    """Load all credit entries from storage."""
    path = _get_credits_path(root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [CreditEntry(**e) for e in data]
    except Exception:  # noqa: BLE001
        return []


def _save_entries(root: Path, entries: list[CreditEntry]) -> None:
    """Save credit entries to storage."""
    path = _get_credits_path(root)
    path.write_text(
        json.dumps([asdict(e) for e in entries], indent=2),
        encoding="utf-8",
    )


def load_budget(root: Path) -> CreditBudget:
    """Load budget configuration."""
    path = _get_budget_path(root)
    if not path.exists():
        return CreditBudget()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return CreditBudget(**data)
    except Exception:  # noqa: BLE001
        return CreditBudget()


def save_budget(root: Path, budget: CreditBudget) -> None:
    """Save budget configuration."""
    path = _get_budget_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(budget), indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def record_usage(
    root: Path,
    *,
    model: str = "unknown",
    provider: str = "unknown",
    tokens_in: int = 0,
    tokens_out: int = 0,
    task: str = "",
    session_id: str = "",
    duration_seconds: float = 0.0,
    cost_usd: float | None = None,
) -> CreditEntry:
    """Record a credit usage entry."""
    entry = CreditEntry(
        timestamp=datetime.now().isoformat(),
        session_id=session_id or datetime.now().strftime("%Y%m%d-%H%M"),
        model=model,
        provider=provider,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        estimated_cost_usd=cost_usd
        if cost_usd is not None
        else estimate_cost(model, tokens_in, tokens_out),
        task=task,
        duration_seconds=duration_seconds,
    )
    entries = _load_entries(root)
    entries.append(entry)
    _save_entries(root, entries)
    return entry


def get_summary(
    root: Path,
    *,
    since: str = "",
    month: str = "",
) -> CreditSummary:
    """Get aggregate credit summary with budget alerts."""
    entries = _load_entries(root)

    if since:
        entries = [e for e in entries if e.timestamp >= since]
    if month:
        entries = [e for e in entries if e.timestamp[:7] == month]

    summary = CreditSummary(entry_count=len(entries))
    sessions: set[str] = set()

    for e in entries:
        summary.total_tokens_in += e.tokens_in
        summary.total_tokens_out += e.tokens_out
        summary.total_cost_usd += e.estimated_cost_usd
        sessions.add(e.session_id)

        # By model
        summary.by_model[e.model] = summary.by_model.get(e.model, 0.0) + e.estimated_cost_usd
        # By provider
        summary.by_provider[e.provider] = (
            summary.by_provider.get(e.provider, 0.0) + e.estimated_cost_usd
        )
        # By task
        if e.task:
            summary.by_task[e.task] = summary.by_task.get(e.task, 0.0) + e.estimated_cost_usd

    summary.session_count = len(sessions)

    # Budget alerts
    budget = load_budget(root)
    summary.budget = budget
    if budget.enabled and budget.monthly_cap_usd > 0:
        current_month = datetime.now().strftime("%Y-%m")
        month_entries = [e for e in _load_entries(root) if e.timestamp[:7] == current_month]
        month_cost = sum(e.estimated_cost_usd for e in month_entries)

        pct = (month_cost / budget.monthly_cap_usd) * 100 if budget.monthly_cap_usd else 0
        if pct >= 100:
            summary.alerts.append(
                f"BUDGET EXCEEDED: ${month_cost:.2f} / ${budget.monthly_cap_usd:.2f} ({pct:.0f}%)"
            )
        elif pct >= budget.alert_threshold_pct:
            summary.alerts.append(
                f"Budget warning: ${month_cost:.2f} / ${budget.monthly_cap_usd:.2f} "
                f"({pct:.0f}%) — approaching cap"
            )

        # Watermark alerts
        for watermark in sorted(budget.alert_watermarks_usd):
            if month_cost >= watermark:
                summary.alerts.append(f"Watermark: ${watermark:.2f} spend reached this month")

    return summary


def generate_report(root: Path, *, since: str = "") -> str:
    """Generate a markdown credit report."""
    summary = get_summary(root, since=since)

    report = "# AI Credit Report\n\n"
    report += f"- **Total tokens in**: {summary.total_tokens_in:,}\n"
    report += f"- **Total tokens out**: {summary.total_tokens_out:,}\n"
    report += f"- **Estimated cost**: ${summary.total_cost_usd:.4f}\n"
    report += f"- **Sessions**: {summary.session_count}\n"
    report += f"- **Entries**: {summary.entry_count}\n\n"

    if summary.alerts:
        report += "## Alerts\n\n"
        for alert in summary.alerts:
            report += f"- ⚠️ {alert}\n"
        report += "\n"

    if summary.by_model:
        report += "## Cost by Model\n\n"
        for model, cost in sorted(summary.by_model.items(), key=lambda x: -x[1]):
            report += f"- {model}: ${cost:.4f}\n"
        report += "\n"

    if summary.by_provider:
        report += "## Cost by Provider\n\n"
        for provider, cost in sorted(summary.by_provider.items(), key=lambda x: -x[1]):
            report += f"- {provider}: ${cost:.4f}\n"
        report += "\n"

    if summary.by_task:
        report += "## Cost by Task\n\n"
        for task, cost in sorted(summary.by_task.items(), key=lambda x: -x[1]):
            report += f"- {task}: ${cost:.4f}\n"
        report += "\n"

    if summary.budget and summary.budget.monthly_cap_usd > 0:
        report += "## Budget\n\n"
        report += f"- Monthly cap: ${summary.budget.monthly_cap_usd:.2f}\n"
        report += f"- Alert at: {summary.budget.alert_threshold_pct}%\n"
        wm = ", ".join(f"${w:.2f}" for w in summary.budget.alert_watermarks_usd)
        report += f"- Watermarks: {wm}\n"

    return report
