# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Quality Improvement Report — gathers all governance and metrics data and surfaces it.

The report can be rendered to stdout as Markdown or posted as a GitHub issue
labelled ``quality_improvement``.  Running it regularly (e.g. weekly) gives a
continuous improvement loop:

    specsmith quality-report                   # render to stdout
    specsmith quality-report --create-issue    # post to GitHub + print URL

Report sections
---------------
1. Project snapshot   — phase, readiness %, audit health
2. Lifetime metrics   — sessions, pass rate, cost, quality (all time)
3. Period metrics     — same, filtered to --since / --until window
4. Quality trend      — 7-day and 30-day rolling means
5. Bottlenecks        — top-5 sessions by rework_turns
6. Suggested actions  — auto-generated from audit failures + low quality
7. Raw JSON appendix  — machine-readable payload for downstream tooling
"""

from __future__ import annotations

import contextlib
import json
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class QualityReportData:
    """All data collected for a quality improvement report."""

    # Metadata
    project_name: str = ""
    generated_at: str = field(
        default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    since: str | None = None
    until: str | None = None

    # Phase
    phase: str = ""
    readiness_pct: float | None = None

    # Audit
    audit_checks_total: int = 0
    audit_checks_passed: int = 0
    audit_checks_failed: int = 0
    audit_checks_suppressed: int = 0
    audit_healthy: bool = True

    # Lifetime metrics
    lifetime: dict[str, Any] = field(default_factory=dict)

    # Period metrics (if since/until specified)
    period: dict[str, Any] = field(default_factory=dict)

    # Open GitHub issues
    open_issues_count: int | None = None
    oldest_open_issue_days: int | None = None

    # Suggested next actions
    suggestions: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def build_quality_report(
    root: Path | str,
    since: str | None = None,
    until: str | None = None,
) -> QualityReportData:
    """Gather all governance data and return a QualityReportData.

    Designed to be fault-tolerant: each data-gathering step catches its own
    exceptions and falls back gracefully so the report is always produced.
    """
    root = Path(root)
    data = QualityReportData(since=since, until=until)

    # ── Project name ────────────────────────────────────────────────────────
    data.project_name = _read_project_name(root)

    # ── Phase ───────────────────────────────────────────────────────────────
    data.phase, data.readiness_pct = _read_phase(root)

    # ── Audit ───────────────────────────────────────────────────────────────
    _fill_audit(root, data)

    # ── Metrics ─────────────────────────────────────────────────────────────
    _fill_metrics(root, since, until, data)

    # ── GitHub issues ────────────────────────────────────────────────────────
    _fill_github_issues(root, data)

    # ── Suggestions ─────────────────────────────────────────────────────────
    data.suggestions = _build_suggestions(data)

    return data


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------


def render_markdown(data: QualityReportData) -> str:
    """Render QualityReportData as a Markdown string suitable for GitHub issue body."""
    date_range = ""
    if data.since or data.until:
        date_range = f" ({data.since or ''}–{data.until or 'now'})"
    lines: list[str] = [
        f"# Quality Improvement Report — {data.project_name}{date_range}",
        "",
        f"**Generated:** {data.generated_at}",
        "",
        "---",
        "",
        "## 1. Project Snapshot",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Phase | `{data.phase or 'unknown'}` |",
        "| Readiness | "
        f"{f'{data.readiness_pct:.0f}%' if data.readiness_pct is not None else 'N/A'} |",
        f"| Audit health | {'✅ Healthy' if data.audit_healthy else '❌ Issues found'} |",
        f"| Audit checks | {data.audit_checks_passed} pass / {data.audit_checks_failed} fail"
        f" / {data.audit_checks_suppressed} suppressed |",
        "",
    ]

    # Lifetime metrics
    lines += _render_metrics_section("## 2. Lifetime Metrics", data.lifetime)

    # Period metrics
    if data.since or data.until:
        lines += _render_metrics_section(
            f"## 3. Period Metrics ({data.since or 'start'}–{data.until or 'now'})",
            data.period,
        )

    # Bottlenecks
    top_rework = data.lifetime.get("top_rework_sessions") or []
    if top_rework:
        lines += [
            "## 4. Bottleneck Sessions (highest rework turns)",
            "",
            "| Session | Work Item | Rework Turns | Date |",
            "|---|---|---|---|",
        ]
        for r in top_rework:
            lines.append(
                f"| `{r['session_id']}` | `{r.get('work_item_id') or '—'}` |"
                f" {r['rework_turns']} | {r['timestamp'][:10]} |",
            )
        lines.append("")

    # GitHub issues
    if data.open_issues_count is not None:
        lines += [
            "## 5. GitHub Issues",
            "",
            f"- Open issues: **{data.open_issues_count}**",
        ]
        if data.oldest_open_issue_days is not None:
            lines.append(f"- Oldest open issue: **{data.oldest_open_issue_days} days old**")
        lines.append("")

    # Suggested actions
    if data.suggestions:
        lines += ["## 6. Suggested Next Actions", ""]
        for i, s in enumerate(data.suggestions, 1):
            lines.append(f"{i}. {s}")
        lines.append("")

    # Raw JSON appendix
    lines += [
        "## 7. Raw Data (JSON)",
        "",
        "```json",
        json.dumps(
            {
                "lifetime": data.lifetime,
                "period": data.period if (data.since or data.until) else None,
                "audit": {
                    "total": data.audit_checks_total,
                    "passed": data.audit_checks_passed,
                    "failed": data.audit_checks_failed,
                    "suppressed": data.audit_checks_suppressed,
                },
            },
            indent=2,
            default=str,
        ),
        "```",
        "",
        "---",
        "",
        "*Generated by `specsmith quality-report`. "
        + "Run `specsmith metrics report` for session-level detail.*",
    ]

    return "\n".join(lines)


def _render_metrics_section(heading: str, m: dict[str, Any]) -> list[str]:
    if not m:
        return [heading, "", "_No metrics recorded._", ""]

    def _fmt(v: Any, suffix: str = "") -> str:
        if v is None:
            return "N/A"
        if isinstance(v, float):
            return f"{v:.4f}{suffix}"
        return f"{v}{suffix}"

    return [
        heading,
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Sessions | {m.get('n_sessions', 'N/A')} |",
        f"| Pass rate | {_fmt(m.get('pass_rate'), '%' if m.get('pass_rate') else '')} |",
        f"| Mean tokens | {_fmt(m.get('mean_tokens'))} |",
        f"| Mean cost | ${_fmt(m.get('mean_cost_usd'))} |",
        f"| Total cost | ${_fmt(m.get('total_cost_usd'))} |",
        f"| Cost-of-pass | ${_fmt(m.get('cost_of_pass'))} |",
        f"| Mean quality | {_fmt(m.get('mean_quality'))} |",
        f"| Quality (7-day) | {_fmt(m.get('quality_7d'))} |",
        f"| Mean rework turns | {_fmt(m.get('mean_rework'))} |",
        "",
    ]


# ---------------------------------------------------------------------------
# GitHub issue creator
# ---------------------------------------------------------------------------


def create_github_issue(
    data: QualityReportData,
    repo: str = "",
    label: str = "quality_improvement",
    project_root: Path | str | None = None,
) -> str:
    """Post the report as a GitHub issue using the ``gh`` CLI.

    Returns the URL of the created issue.
    Raises RuntimeError if ``gh`` is not available or the call fails.
    """
    if not shutil.which("gh"):
        raise RuntimeError(
            "gh CLI not found. Install it from https://cli.github.com/ and authenticate "
            "with `gh auth login`.",
        )

    root = Path(project_root or ".").resolve()
    body = render_markdown(data)
    title = f"Quality Improvement Report \u2014 {data.project_name} \u2014 {data.generated_at[:10]}"

    # Ensure the label exists (gh creates it if missing)
    _ensure_gh_label(repo, label, color="0075ca", description="Quality improvement tracking")

    cmd = ["gh", "issue", "create", "--title", title, "--body", body, "--label", label]
    if repo:
        cmd += ["--repo", repo]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(root),
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("gh issue create timed out after 30 seconds") from exc

    if result.returncode != 0:
        raise RuntimeError(
            f"gh issue create failed (exit {result.returncode}):\n{result.stderr.strip()}",
        )

    url = result.stdout.strip()
    return url


def _ensure_gh_label(repo: str, label: str, color: str, description: str) -> None:
    """Create the GitHub label if it does not already exist. Best-effort."""
    cmd = [
        "gh",
        "label",
        "create",
        label,
        "--color",
        color,
        "--description",
        description,
        "--force",  # no-op if already exists
    ]
    if repo:
        cmd += ["--repo", repo]
    with contextlib.suppress(Exception):  # intentional: best-effort, never blocks the report
        subprocess.run(cmd, capture_output=True, timeout=15)  # noqa: S603


# ---------------------------------------------------------------------------
# Internal data-gathering helpers
# ---------------------------------------------------------------------------


def _read_project_name(root: Path) -> str:
    """Read project name from scaffold.yml, pyproject.toml, or fallback to directory name."""
    try:
        import yaml

        cfg = root / "scaffold.yml"
        if not cfg.is_file():
            cfg = root / "docs" / "SPECSMITH.yml"
        if cfg.is_file():
            raw = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
            if isinstance(raw, dict):
                name = str(raw.get("name") or raw.get("project_name") or "")
                if name:
                    return name
    except Exception:  # noqa: BLE001
        pass

    # Try TOML-based pyproject.toml (tomllib is stdlib in 3.11+; fall back to regex
    # on older interpreters so CI stays green across all supported Python versions).
    pyp = root / "pyproject.toml"
    if pyp.is_file():
        try:
            try:
                import tomllib  # Python 3.11+
            except ImportError:
                import tomli as tomllib

            data = tomllib.loads(pyp.read_text(encoding="utf-8"))
            poetry_name = data.get("tool", {}).get("poetry", {}).get("name") or ""
            name = data.get("project", {}).get("name") or poetry_name
            if name:
                return str(name)
        except Exception:  # noqa: BLE001
            pass

        # Last-resort regex fallback: handles Python 3.10 without tomli installed.
        try:
            import re

            text = pyp.read_text(encoding="utf-8")
            # Match [project] section name field
            m = re.search(
                r'^\[project\].*?^name\s*=\s*["\']+)["\']',
                text,
                re.MULTILINE | re.DOTALL,
            )
            if m:
                return m.group(1).strip()
            # Match [tool.poetry] name field
            m2 = re.search(
                r'^\[tool\.poetry\].*?^name\s*=\s*["\']+)["\']',
                text,
                re.MULTILINE | re.DOTALL,
            )
            if m2:
                return m2.group(1).strip()
        except Exception:  # noqa: BLE001
            pass

    return root.name


def _read_phase(root: Path) -> tuple[str, float | None]:
    """Return (phase_name, readiness_pct) by running specsmith phase."""
    try:
        result = subprocess.run(
            ["specsmith", "phase", "--project-dir", str(root)],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            # Parse "Phase: construction (72% ready)" style output
            import re

            m_phase = re.search(r"(?:Phase:|phase:)\s*([a-z_]+)", output, re.IGNORECASE)
            m_pct = re.search(r"(\d+(?:\.\d+)?)\s*%", output)
            phase = m_phase.group(1) if m_phase else output.split()[0] if output else ""
            readiness = float(m_pct.group(1)) if m_pct else None
            return phase, readiness
    except Exception:  # noqa: BLE001
        pass
    return "", None


def _fill_audit(root: Path, data: QualityReportData) -> None:
    """Run specsmith audit and parse the check counts."""
    try:
        result = subprocess.run(
            ["specsmith", "audit", "--project-dir", str(root)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout + result.stderr
        import re

        m_pass = re.search(r"(\d+)\s+(?:PASS|pass)", output)
        m_fail = re.search(r"(\d+)\s+(?:FAIL|fail)", output)
        m_supp = re.search(r"(\d+)\s+(?:suppressed|SKIP)", output)
        m_warn = re.search(r"(\d+)\s+(?:WARN|warn)", output)
        passed = int(m_pass.group(1)) if m_pass else 0
        failed = int(m_fail.group(1)) if m_fail else 0
        suppressed = int(m_supp.group(1)) if m_supp else 0
        warned = int(m_warn.group(1)) if m_warn else 0
        data.audit_checks_passed = passed
        data.audit_checks_failed = failed + warned
        data.audit_checks_suppressed = suppressed
        data.audit_checks_total = passed + failed + warned + suppressed
        data.audit_healthy = (failed + warned) == 0
    except Exception:  # noqa: BLE001
        data.audit_healthy = False


def _fill_metrics(
    root: Path,
    since: str | None,
    until: str | None,
    data: QualityReportData,
) -> None:
    """Load project metrics and fill lifetime + period dicts."""
    try:
        from specsmith.project_metrics import MetricsStore

        store = MetricsStore(root)
        data.lifetime = store.report()
        if since or until:
            data.period = store.report(since=since, until=until)
    except Exception:  # noqa: BLE001
        data.lifetime = {}
        data.period = {}


def _fill_github_issues(root: Path, data: QualityReportData) -> None:
    """Fetch open issue count and oldest open issue age using gh CLI."""
    if not shutil.which("gh"):
        return
    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--state",
                "open",
                "--limit",
                "100",
                "--json",
                "number,createdAt",
            ],
            capture_output=True,
            text=True,
            cwd=str(root),
            timeout=20,
        )
        if result.returncode != 0:
            return
        issues = json.loads(result.stdout or "[]")
        if not isinstance(issues, list):
            return
        data.open_issues_count = len(issues)
        if issues:
            import datetime

            now = datetime.datetime.now(datetime.timezone.utc)
            oldest_delta = 0
            for issue in issues:
                created = issue.get("createdAt", "")
                if created:
                    with contextlib.suppress(ValueError):  # malformed createdAt — skip
                        dt = datetime.datetime.fromisoformat(created.replace("Z", "+00:00"))
                        days = (now - dt).days
                        oldest_delta = max(oldest_delta, days)
            data.oldest_open_issue_days = oldest_delta
    except Exception:  # noqa: BLE001
        pass


def _build_suggestions(data: QualityReportData) -> list[str]:
    """Generate human-readable suggested next actions from the gathered data."""
    suggestions: list[str] = []

    if not data.audit_healthy:
        suggestions.append(
            f"Fix {data.audit_checks_failed} audit failure(s): "
            "run `specsmith audit` to see details and `specsmith audit --fix` for auto-repair.",
        )

    m = data.lifetime
    pass_rate = m.get("pass_rate")
    if pass_rate is not None and pass_rate < 0.7:
        suggestions.append(
            f"Pass rate is {pass_rate:.0%} (target ≥70%). "
            "Review the bottleneck sessions above and improve preflight "
            "coverage for failing work items.",
        )

    mean_rework = m.get("mean_rework")
    if mean_rework is not None and mean_rework > 2.0:
        suggestions.append(
            f"Mean rework turns = {mean_rework:.1f} (target ≤2). "
            "High rework suggests unclear acceptance criteria or insufficient preflight scope. "
            "Consider running `specsmith preflight` with more precise utterances.",
        )

    q7d = m.get("quality_7d")
    mean_q = m.get("mean_quality")
    if q7d is not None and mean_q is not None and q7d < mean_q - 0.1:
        suggestions.append(
            f"Quality trending down: 7-day mean {q7d:.2f} vs lifetime mean {mean_q:.2f}. "
            "Review recent sessions for scope creep or incomplete implementations.",
        )

    cop = m.get("cost_of_pass")
    if cop is not None and cop > 0.01:
        suggestions.append(
            f"Cost-of-pass is ${cop:.4f}/correct answer. "
            "Consider using specsmith preflight to gate more aggressively on ambiguous tasks, "
            "which prevents expensive failed runs.",
        )

    if data.open_issues_count is not None and data.open_issues_count > 20:
        suggestions.append(
            f"{data.open_issues_count} open GitHub issues. "
            "Run `specsmith skill install issue-triage` to classify and prioritise.",
        )

    if data.oldest_open_issue_days is not None and data.oldest_open_issue_days > 30:
        suggestions.append(
            f"Oldest open issue is {data.oldest_open_issue_days} days old. "
            "Consider a triage session to resolve or close stale issues.",
        )

    if not suggestions:
        suggestions.append(
            "No critical improvements identified. Governance health looks good. "
            "Run `specsmith metrics report` to see session-level detail.",
        )

    return suggestions
