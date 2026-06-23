from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from specsmith.approvals import approvals_by_work_item
from specsmith.risk import assess_work_item_risk


@dataclass
class GovernancePolicy:
    required_preflight: bool = True
    required_tests: bool = True
    required_human_approval: list[str] = field(default_factory=list)
    risk_threshold: str = "medium"
    file_rules: dict[str, dict[str, Any]] = field(default_factory=dict)
    agent_allowlist: list[str] = field(default_factory=list)
    command_allowlist: list[str] = field(default_factory=list)
    command_denylist: list[str] = field(default_factory=list)
    evidence_requirements: list[str] = field(default_factory=list)


def _policy_path(root: Path) -> Path:
    return root / ".specsmith" / "policy.yml"


def validate_policy_dict(raw: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(raw, dict):
        return ["policy root must be a mapping"]
    bool_fields = ("required_preflight", "required_tests")
    for name in bool_fields:
        if name in raw and not isinstance(raw[name], bool):
            errors.append(f"{name} must be a boolean")
    list_fields = (
        "required_human_approval",
        "agent_allowlist",
        "command_allowlist",
        "command_denylist",
        "evidence_requirements",
    )
    for name in list_fields:
        if name in raw and not isinstance(raw[name], list):
            errors.append(f"{name} must be a list")
    if "file_rules" in raw and not isinstance(raw["file_rules"], dict):
        errors.append("file_rules must be a mapping of path pattern -> rule override")
    threshold = str(raw.get("risk_threshold", "medium"))
    if threshold not in {"low", "medium", "high", "critical"}:
        errors.append("risk_threshold must be one of low|medium|high|critical")
    required_approvals = raw.get("required_human_approval", []) or []
    if isinstance(required_approvals, list):
        allowed = {"requirement", "plan", "implementation", "verification", "release"}
        for value in required_approvals:
            if str(value) not in allowed:
                errors.append(f"required_human_approval contains invalid type: {value}")
    return errors


def load_policy(root: Path) -> tuple[GovernancePolicy, list[str]]:
    path = _policy_path(root)
    if not path.is_file():
        return GovernancePolicy(), []
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        return GovernancePolicy(), [f"failed to parse policy.yml: {exc}"]
    errors = validate_policy_dict(raw)
    if errors:
        return GovernancePolicy(), errors
    assert isinstance(raw, dict)
    return (
        GovernancePolicy(
            required_preflight=bool(raw.get("required_preflight", True)),
            required_tests=bool(raw.get("required_tests", True)),
            required_human_approval=[str(v) for v in raw.get("required_human_approval", []) or []],
            risk_threshold=str(raw.get("risk_threshold", "medium")),
            file_rules=raw.get("file_rules", {}) or {},
            agent_allowlist=[str(v) for v in raw.get("agent_allowlist", []) or []],
            command_allowlist=[str(v) for v in raw.get("command_allowlist", []) or []],
            command_denylist=[str(v) for v in raw.get("command_denylist", []) or []],
            evidence_requirements=[str(v) for v in raw.get("evidence_requirements", []) or []],
        ),
        [],
    )


def simulate_policy_for_work_item(
    root: Path, work_item: Any, diff_text: str = ""
) -> dict[str, Any]:
    policy, policy_errors = load_policy(root)
    risk = assess_work_item_risk(work_item)
    approvals = approvals_by_work_item(root, getattr(work_item, "id", ""))
    approval_types = {a.approval_type for a in approvals}

    required_approvals = set(policy.required_human_approval)
    blocking_issues: list[str] = []
    if policy_errors:
        blocking_issues.extend(policy_errors)

    if policy.required_tests and not list(getattr(work_item, "test_case_ids", []) or []):
        blocking_issues.append("required_tests enabled but no linked tests")

    for approval in sorted(required_approvals):
        if approval not in approval_types:
            blocking_issues.append(f"missing required approval: {approval}")

    if risk.level in {"high", "critical"} and "implementation" not in approval_types:
        blocking_issues.append(f"risk level {risk.level} requires implementation approval")

    required_evidence = list(policy.evidence_requirements)
    if diff_text:
        required_evidence.append("diff")
    return {
        "work_item_id": getattr(work_item, "id", ""),
        "risk_level": risk.level,
        "risk_required_gates": risk.required_gates,
        "policy_required_human_approval": sorted(required_approvals),
        "provided_approvals": sorted(approval_types),
        "required_evidence": sorted(set(required_evidence)),
        "blocking_issues": blocking_issues,
        "policy_errors": policy_errors,
    }
