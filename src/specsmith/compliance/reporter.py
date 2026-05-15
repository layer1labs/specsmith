# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Compliance report generation — JSON, Markdown, and self-contained HTML.

ComplianceReporter converts ComplianceResult objects into formatted reports
suitable for regulatory submission, audit documentation, or dashboard display.
"""

from __future__ import annotations

import json
import time
from typing import Any

from specsmith.compliance.checker import ComplianceResult

_STATUS_EMOJI = {
    "compliant": "\u2714",  # ✔
    "partial": "\u26a0",  # ⚠
    "gap": "\u2717",  # ✗
    "n_a": "\u2014",  # —
}

_STATUS_COLOR = {
    "compliant": "#22c55e",  # green
    "partial": "#f59e0b",  # amber
    "gap": "#ef4444",  # red
    "n_a": "#9ca3af",  # grey
}


class ComplianceReporter:
    """Generates compliance reports in multiple formats."""

    def __init__(self, results: list[ComplianceResult]) -> None:
        self.results = results
        self.generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------

    def to_json(self, indent: int = 2) -> str:
        payload = {
            "specsmith_compliance_report": True,
            "generated_at": self.generated_at,
            "regulations": [r.to_dict() for r in self.results],
            "summary": self._summary_dict(),
        }
        return json.dumps(payload, indent=indent, ensure_ascii=False)

    def _summary_dict(self) -> dict[str, Any]:
        total = len(self.results)
        compliant = sum(1 for r in self.results if r.overall_status == "compliant")
        partial = sum(1 for r in self.results if r.overall_status == "partial")
        gaps = sum(1 for r in self.results if r.overall_status == "gap")
        return {
            "total_regulations": total,
            "compliant": compliant,
            "partial": partial,
            "gaps": gaps,
            "overall_status": (
                "compliant" if gaps == 0 and partial == 0 else "gap" if gaps > 0 else "partial"
            ),
        }

    # ------------------------------------------------------------------
    # Markdown
    # ------------------------------------------------------------------

    def to_markdown(self) -> str:
        lines: list[str] = []
        summary = self._summary_dict()

        lines.append("# AI Compliance Report")
        lines.append(f"\n**Generated:** {self.generated_at}  ")
        lines.append(
            f"**Overall status:** "
            f"{_STATUS_EMOJI.get(summary['overall_status'], '?')} "
            f"{summary['overall_status'].upper()}"
        )
        lines.append(
            f"**Regulations checked:** {summary['total_regulations']}  "
            f"Compliant: {summary['compliant']} | "
            f"Partial: {summary['partial']} | "
            f"Gaps: {summary['gaps']}\n"
        )

        lines.append("---\n")

        for result in self.results:
            icon = _STATUS_EMOJI.get(result.overall_status, "?")
            lines.append(f"## {icon} {result.regulation_name}  *({result.jurisdiction})*")
            lines.append(
                f"**Status:** {result.overall_status}  "
                f"**Confidence:** {result.overall_confidence:.0%}  "
                f"**Checked:** {result.checked_at}"
            )
            if result.notes:
                lines.append(f"\n> {result.notes}\n")

            lines.append("\n| Article | Title | Status | Confidence |")
            lines.append("| --- | --- | --- | --- |")
            for ar in result.article_results:
                a_icon = _STATUS_EMOJI.get(ar.status, "?")
                lines.append(
                    f"| `{ar.article_id}` | {ar.title} | "
                    f"{a_icon} {ar.status} | "
                    f"{ar.confidence:.0%} |"
                )

            # Findings
            all_findings = [
                f
                for ar in result.article_results
                for f in ar.findings
                if f.severity in ("gap", "partial")
            ]
            if all_findings:
                lines.append("\n### Findings\n")
                for finding in all_findings[:10]:
                    sev_icon = _STATUS_EMOJI.get(finding.severity, "?")
                    lines.append(f"- {sev_icon} **{finding.article_id}**: {finding.message}")
                    if finding.recommendation:
                        lines.append(f"  - *Recommendation:* {finding.recommendation}")

            lines.append("\n---\n")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # HTML (self-contained, no external deps)
    # ------------------------------------------------------------------

    def to_html(self) -> str:
        summary = self._summary_dict()

        reg_html = ""
        for result in self.results:
            status_color = _STATUS_COLOR.get(result.overall_status, "#9ca3af")

            rows = ""
            for ar in result.article_results:
                ar_color = _STATUS_COLOR.get(ar.status, "#9ca3af")
                rows += (
                    f"<tr>"
                    f"<td><code>{ar.article_id}</code></td>"
                    f"<td>{ar.title}</td>"
                    f"<td style='color:{ar_color};font-weight:bold'>"
                    f"{_STATUS_EMOJI.get(ar.status, '?')} {ar.status}</td>"
                    f"<td>{ar.confidence:.0%}</td>"
                    f"</tr>"
                )

            findings_html = ""
            all_findings = [
                f
                for ar in result.article_results
                for f in ar.findings
                if f.severity in ("gap", "partial")
            ]
            if all_findings:
                items = ""
                for finding in all_findings[:10]:
                    sev_color = _STATUS_COLOR.get(finding.severity, "#9ca3af")
                    items += (
                        f"<li><strong style='color:{sev_color}'>"
                        f"{finding.article_id}</strong>: {finding.message}"
                    )
                    if finding.recommendation:
                        items += (
                            f"<br><em style='color:#6b7280'>\u2192 {finding.recommendation}</em>"
                        )
                    items += "</li>"
                findings_html = (
                    f"<details><summary>Findings ({len(all_findings)})</summary>"
                    f"<ul>{items}</ul></details>"
                )

            reg_html += f"""
<div class='regulation' style='border-left:4px solid {status_color};padding-left:16px;margin-bottom:24px'>
  <h2 style='color:{status_color}'>{_STATUS_EMOJI.get(result.overall_status, "?")} {result.regulation_name}
    <span style='font-size:0.7em;color:#6b7280'> {result.jurisdiction}</span>
  </h2>
  <p><strong>Status:</strong> {result.overall_status}
  &nbsp;&nbsp;<strong>Confidence:</strong> {result.overall_confidence:.0%}
  &nbsp;&nbsp;<strong>Checked:</strong> {result.checked_at}</p>
  {f'<blockquote style="color:#6b7280">{result.notes}</blockquote>' if result.notes else ""}
  <table style='border-collapse:collapse;width:100%;font-size:0.9em'>
    <thead><tr style='background:#f3f4f6'>
      <th style='text-align:left;padding:8px'>Article</th>
      <th style='text-align:left;padding:8px'>Title</th>
      <th style='text-align:left;padding:8px'>Status</th>
      <th style='text-align:left;padding:8px'>Confidence</th>
    </tr></thead>
    <tbody>{rows}</tbody>
  </table>
  {findings_html}
</div>"""

        overall_color = _STATUS_COLOR.get(summary["overall_status"], "#9ca3af")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Compliance Report — specsmith</title>
<style>
  body{{font-family:system-ui,sans-serif;max-width:900px;margin:40px auto;padding:20px;color:#1f2937}}
  h1{{border-bottom:2px solid #e5e7eb;padding-bottom:12px}}
  .summary-card{{background:#f9fafb;border-radius:8px;padding:20px;margin-bottom:32px;
    display:flex;gap:24px;flex-wrap:wrap}}
  .stat{{text-align:center}}
  .stat .num{{font-size:2em;font-weight:bold}}
  .stat .label{{font-size:0.8em;color:#6b7280}}
  table td,table th{{padding:8px;border-bottom:1px solid #e5e7eb}}
  details summary{{cursor:pointer;color:#4b5563;margin:8px 0}}
  code{{background:#f3f4f6;padding:2px 4px;border-radius:3px;font-size:0.85em}}
  blockquote{{border-left:3px solid #e5e7eb;margin:0;padding-left:12px}}
</style>
</head>
<body>
<h1>AI Compliance Report</h1>
<p style='color:#6b7280'>Generated by <strong>specsmith</strong> &mdash; {self.generated_at}</p>

<div class='summary-card'>
  <div class='stat'>
    <div class='num' style='color:{overall_color}'>{_STATUS_EMOJI.get(summary["overall_status"], "?")}</div>
    <div class='label'>Overall</div>
  </div>
  <div class='stat'>
    <div class='num'>{summary["total_regulations"]}</div>
    <div class='label'>Regulations</div>
  </div>
  <div class='stat'>
    <div class='num' style='color:#22c55e'>{summary["compliant"]}</div>
    <div class='label'>Compliant</div>
  </div>
  <div class='stat'>
    <div class='num' style='color:#f59e0b'>{summary["partial"]}</div>
    <div class='label'>Partial</div>
  </div>
  <div class='stat'>
    <div class='num' style='color:#ef4444'>{summary["gaps"]}</div>
    <div class='label'>Gaps</div>
  </div>
</div>

{reg_html}

<hr>
<p style='color:#9ca3af;font-size:0.8em'>
This report was generated by specsmith and reflects the governance controls
present in the project directory at the time of the check. It is provided
for informational purposes. For legal compliance, consult qualified counsel.
</p>
</body>
</html>"""
