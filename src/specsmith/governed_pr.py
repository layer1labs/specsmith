from __future__ import annotations

from pathlib import Path
from typing import Any

from specsmith.auditor import run_audit
from specsmith.policy import load_policy
from specsmith.risk import assess_work_item_risk
from specsmith.wi_store import WorkItemStore


def evaluate_governed_pr(root: Path, work_item_id: str = "") -> dict[str, Any]:
    store = WorkItemStore(root)
    item = store.get(work_item_id) if work_item_id else None
    if item is None:
        open_items = [i for i in store.load() if i.status in {"open", "implemented"}]
        item = open_items[0] if open_items else None

    audit = run_audit(root)
    policy, policy_errors = load_policy(root)
    linked_work_item = item is not None
    requirement_linked = bool(item and item.requirement_ids)
    tests_linked = bool(item and item.test_case_ids)
    verification_status = bool(item and item.verified)
    audit_chain_ok = (
        all(r.passed for r in audit.results if r.name in {"trace-chain-integrity", "audit-chain"})
        if audit.results
        else True
    )
    risk = assess_work_item_risk(item) if item else None
    risk_level = risk.level if risk else "unknown"

    governance_gaps: list[str] = []
    if not linked_work_item:
        governance_gaps.append("No linked work item")
    if not requirement_linked:
        governance_gaps.append("No linked requirement")
    if not tests_linked and policy.required_tests:
        governance_gaps.append("No linked tests")
    if not verification_status:
        governance_gaps.append("Verification not marked complete")
    if not audit_chain_ok:
        governance_gaps.append("Audit chain integrity check failed")
    if not audit.healthy:
        governance_gaps.append(f"Audit unhealthy ({audit.failed} failed checks)")
    governance_gaps.extend(policy_errors)

    return {
        "work_item_id": item.id if item else "",
        "linked_work_item": linked_work_item,
        "linked_requirement": requirement_linked,
        "linked_tests": tests_linked,
        "verification_status": verification_status,
        "audit_chain_status": audit_chain_ok,
        "risk_score": risk.score if risk else -1,
        "risk_level": risk_level,
        "governance_gaps": governance_gaps,
        "audit_failed_checks": audit.failed,
    }


def render_governance_comment(status: dict[str, Any]) -> str:
    gaps = status.get("governance_gaps") or []
    gap_lines = "\n".join(f"- {g}" for g in gaps) if gaps else "- None"
    return (
        "## Specsmith Governance Status\n\n"
        f"- Linked work item: {'✅' if status.get('linked_work_item') else '❌'} "
        f"`{status.get('work_item_id', '') or 'none'}`\n"
        f"- Linked requirement: {'✅' if status.get('linked_requirement') else '❌'}\n"
        f"- Linked tests: {'✅' if status.get('linked_tests') else '❌'}\n"
        f"- Verification status: {'✅' if status.get('verification_status') else '❌'}\n"
        f"- Audit chain status: {'✅' if status.get('audit_chain_status') else '❌'}\n"
        f"- Risk level: `{status.get('risk_level', 'unknown')}`\n\n"
        "### Governance gaps\n"
        f"{gap_lines}\n"
    )
