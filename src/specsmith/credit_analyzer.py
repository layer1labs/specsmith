# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Credit analyzer — spend analysis and closed-loop optimization."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CreditInsight:
    """Single optimization insight."""

    category: str  # "waste", "model", "governance", "batch"
    severity: str  # "info", "warn", "critical"
    message: str
    recommendation: str
    estimated_savings_pct: float = 0.0


@dataclass
class AnalysisReport:
    """Full credit analysis report."""

    insights: list[CreditInsight] = field(default_factory=list)
    total_cost: float = 0.0
    estimated_optimized_cost: float = 0.0
    cost_trend: str = ""  # "increasing", "decreasing", "stable"


def analyze_spend(root: Path) -> AnalysisReport:
    """Analyze credit spend and generate optimization insights."""
    from specsmith.credits import _load_entries

    entries = _load_entries(root)
    report = AnalysisReport()

    if not entries:
        report.insights.append(
            CreditInsight(
                category="info",
                severity="info",
                message="No credit data yet.",
                recommendation=(
                    "Record usage with `specsmith credits record` or integrate with your AI agent."
                ),
            ),
        )
        return report

    report.total_cost = sum(e.estimated_cost_usd for e in entries)

    # --- Analysis 1: Model efficiency ---
    model_costs: dict[str, list[float]] = {}
    for e in entries:
        model_costs.setdefault(e.model, []).append(e.estimated_cost_usd)

    if len(model_costs) > 1:
        avg_by_model = {m: sum(c) / len(c) for m, c in model_costs.items() if c}
        most_expensive = max(avg_by_model, key=avg_by_model.get)  # type: ignore[arg-type]
        cheapest = min(avg_by_model, key=avg_by_model.get)  # type: ignore[arg-type]
        if avg_by_model[most_expensive] > avg_by_model[cheapest] * 3:
            report.insights.append(
                CreditInsight(
                    category="model",
                    severity="warn",
                    message=(
                        f"{most_expensive} costs {avg_by_model[most_expensive]:.4f}/task avg "
                        f"vs {cheapest} at {avg_by_model[cheapest]:.4f}/task"
                    ),
                    recommendation=(
                        f"Use {cheapest} for routine tasks (audit, lint, simple edits). "
                        f"Reserve {most_expensive} for complex architecture/design work."
                    ),
                    estimated_savings_pct=30.0,
                ),
            )

    # --- Analysis 2: Token waste (high input, low output) ---
    high_input_sessions = [e for e in entries if e.tokens_in > 0 and e.tokens_out > 0]
    for e in high_input_sessions:
        ratio = e.tokens_in / max(e.tokens_out, 1)
        if ratio > 10 and e.tokens_in > 5000:
            report.insights.append(
                CreditInsight(
                    category="waste",
                    severity="warn",
                    message=(
                        f"Task '{e.task or 'unknown'}': {e.tokens_in:,} tokens in, "
                        f"only {e.tokens_out:,} out (ratio {ratio:.0f}:1)"
                    ),
                    recommendation=(
                        "High input/output ratio suggests large file reads for small changes. "
                        "Use targeted reads (line ranges) and grep over full file reads."
                    ),
                    estimated_savings_pct=20.0,
                ),
            )
            break  # One example is enough

    # --- Analysis 3: Governance file size vs cost ---
    gov_dir = root / "docs" / "governance"
    gov_files = list(gov_dir.glob("*.md")) if gov_dir.is_dir() else []
    total_gov_lines = 0
    for gf in gov_files:
        total_gov_lines += len(gf.read_text(encoding="utf-8").splitlines())
    if total_gov_lines > 500:
        report.insights.append(
            CreditInsight(
                category="governance",
                severity="info",
                message=(
                    f"Governance files total {total_gov_lines} lines across {len(gov_files)} files."
                ),
                recommendation=(
                    "Ensure agents lazy-load governance files. Only rules.md + workflow.md "
                    "should load at session start. Others on demand."
                ),
                estimated_savings_pct=15.0,
            ),
        )

    # --- Analysis 4: Cost trend ---
    if len(entries) >= 5:
        first_half = entries[: len(entries) // 2]
        second_half = entries[len(entries) // 2 :]
        avg_first = sum(e.estimated_cost_usd for e in first_half) / len(first_half)
        avg_second = sum(e.estimated_cost_usd for e in second_half) / len(second_half)
        if avg_second > avg_first * 1.2:
            report.cost_trend = "increasing"
            report.insights.append(
                CreditInsight(
                    category="batch",
                    severity="warn",
                    message="Cost per task is trending upward.",
                    recommendation=(
                        "Review recent tasks for scope creep. Consider batching "
                        "related changes into fewer sessions."
                    ),
                    estimated_savings_pct=10.0,
                ),
            )
        elif avg_second < avg_first * 0.8:
            report.cost_trend = "decreasing"
        else:
            report.cost_trend = "stable"

    # Estimate optimized cost
    total_savings_pct = sum(i.estimated_savings_pct for i in report.insights) / max(
        len(report.insights),
        1,
    )
    report.estimated_optimized_cost = report.total_cost * (1 - total_savings_pct / 100)

    return report


def generate_analysis_report(root: Path) -> str:
    """Generate a markdown analysis report."""
    report = analyze_spend(root)

    md = "# Credit Analysis Report\n\n"
    md += f"- **Total spend**: ${report.total_cost:.4f}\n"
    if report.estimated_optimized_cost < report.total_cost:
        savings = report.total_cost - report.estimated_optimized_cost
        md += (
            f"- **Estimated optimized**: ${report.estimated_optimized_cost:.4f}"
            f" (save ${savings:.4f})\n"
        )
    if report.cost_trend:
        md += f"- **Trend**: {report.cost_trend}\n"
    md += "\n"

    if report.insights:
        md += "## Insights\n\n"
        for i, insight in enumerate(report.insights, 1):
            icon = {"info": "ℹ️", "warn": "⚠️", "critical": "🔴"}.get(insight.severity, "•")
            md += f"### {i}. {icon} {insight.message}\n\n"
            md += f"**Recommendation**: {insight.recommendation}\n"
            if insight.estimated_savings_pct > 0:
                md += f"**Estimated savings**: {insight.estimated_savings_pct:.0f}%\n"
            md += "\n"

    return md
