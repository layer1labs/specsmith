from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from specsmith.auditor import run_audit
from specsmith.risk import assess_all_work_items
from specsmith.wi_store import WorkItemStore


def build_dashboard(root: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    audit = run_audit(root)
    store = WorkItemStore(root)
    items = store.load()
    risk_rows = assess_all_work_items(root)
    risk_by_id = {wi_id: risk.level for wi_id, risk in risk_rows}

    open_items = [
        i for i in items if i.status not in {"closed", "promoted", "archived", "rejected"}
    ]
    traceability_score = _traceability_score(items)
    html_doc = _render_html(
        {
            "open_items": [item.id for item in open_items],
            "risk_by_item": risk_by_id,
            "audit_health": "healthy" if audit.healthy else "unhealthy",
            "audit_failures": audit.failed,
            "requirements_coverage": _requirements_coverage(items),
            "verification_status": _verification_status(items),
            "compliance_evidence_status": _compliance_evidence_status(root),
            "traceability_score": traceability_score,
        }
    )
    target = out_dir / "index.html"
    target.write_text(html_doc, encoding="utf-8")
    return target


def _traceability_score(items: list[Any]) -> int:
    if not items:
        return 100
    linked = sum(1 for item in items if item.requirement_ids and item.test_case_ids)
    return int((linked / len(items)) * 100)


def _requirements_coverage(items: list[Any]) -> str:
    if not items:
        return "0/0"
    with_reqs = sum(1 for item in items if item.requirement_ids)
    return f"{with_reqs}/{len(items)}"


def _verification_status(items: list[Any]) -> str:
    if not items:
        return "0 verified"
    verified = sum(1 for item in items if item.verified)
    return f"{verified}/{len(items)} verified"


def _compliance_evidence_status(root: Path) -> str:
    approvals = root / ".specsmith" / "approvals.json"
    transcripts = root / ".specsmith" / "transcripts.jsonl"
    if approvals.is_file() and transcripts.is_file():
        return "present"
    if approvals.is_file() or transcripts.is_file():
        return "partial"
    return "missing"


def _render_html(data: dict[str, Any]) -> str:
    payload = html.escape(json.dumps(data, ensure_ascii=False))
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<title>Specsmith Governance Dashboard</title>",
        "<style>",
        (
            "body{font-family:Segoe UI,Arial,sans-serif;margin:24px;background:#0f172a;"
            "color:#e2e8f0;}"
        ),
        (
            ".card{background:#111827;border:1px solid #334155;border-radius:8px;"
            "padding:14px;margin-bottom:12px;}"
        ),
        "h1,h2{margin:0 0 8px 0;} ul{margin:0;padding-left:18px;}",
        "</style></head><body>",
        "<h1>Governance Dashboard</h1>",
        "<div class='card'><h2>Open work items</h2><div id='open-items'></div></div>",
        "<div class='card'><h2>Risk levels</h2><div id='risk-levels'></div></div>",
        "<div class='card'><h2>Traceability score</h2><div id='traceability'></div></div>",
        "<div class='card'><h2>Audit health</h2><div id='audit-health'></div></div>",
        (
            "<div class='card'><h2>Requirements coverage</h2>"
            "<div id='requirements-coverage'></div></div>"
        ),
        (
            "<div class='card'><h2>Verification status</h2>"
            "<div id='verification-status'></div></div>"
        ),
        (
            "<div class='card'><h2>Compliance evidence status</h2>"
            "<div id='compliance-status'></div></div>"
        ),
        f"<script>const data=JSON.parse('{payload}');",
        (
            "document.getElementById('open-items').textContent="
            "(data.open_items||[]).join(', ')||'none';"
        ),
        (
            "document.getElementById('risk-levels').textContent="
            "JSON.stringify(data.risk_by_item||{});"
        ),
        "document.getElementById('traceability').textContent=String(data.traceability_score)+'%';",
        (
            "document.getElementById('audit-health').textContent="
            "data.audit_health+' ('+String(data.audit_failures)+' failures)';"
        ),
        "document.getElementById('requirements-coverage').textContent=data.requirements_coverage;",
        "document.getElementById('verification-status').textContent=data.verification_status;",
        "document.getElementById('compliance-status').textContent=data.compliance_evidence_status;",
        "</script></body></html>",
    ]
    return "".join(parts)
