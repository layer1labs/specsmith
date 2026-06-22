from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RiskAssessment:
    score: int
    level: str
    factors: list[str]
    required_gates: list[str]
    overridden: bool = False
    override_reason: str = ""


_RISK_GATES: dict[str, list[str]] = {
    "low": ["audit_clean"],
    "medium": ["audit_clean", "tests_required"],
    "high": ["audit_clean", "tests_required", "human_approval:implementation"],
    "critical": [
        "audit_clean",
        "tests_required",
        "human_approval:plan",
        "human_approval:implementation",
        "human_approval:verification",
    ],
}

_SECURITY_PATH_HINTS = (
    "security",
    "auth",
    "token",
    "secret",
    "credential",
    "policy",
    ".github/workflows",
)


def risk_level_from_score(score: int) -> str:
    if score <= 2:
        return "low"
    if score <= 5:
        return "medium"
    if score <= 8:
        return "high"
    return "critical"


def assess_work_item_risk(work_item: Any, project_type: str = "") -> RiskAssessment:
    score = 0
    factors: list[str] = []

    files_touched = list(getattr(work_item, "files_touched", []) or [])
    if len(files_touched) >= 10:
        score += 3
        factors.append("large_file_footprint")
    elif len(files_touched) >= 4:
        score += 2
        factors.append("moderate_file_footprint")
    elif len(files_touched) >= 1:
        score += 1

    if any(any(hint in path.lower() for hint in _SECURITY_PATH_HINTS) for path in files_touched):
        score += 3
        factors.append("security_sensitive_paths")

    requirement_ids = list(getattr(work_item, "requirement_ids", []) or [])
    if any(("REG-" in req or "SEC" in req or "COMP" in req) for req in requirement_ids):
        score += 2
        factors.append("compliance_sensitive_requirements")

    test_case_ids = list(getattr(work_item, "test_case_ids", []) or [])
    if not test_case_ids:
        score += 2
        factors.append("no_linked_tests")

    blast_radius = str(getattr(work_item, "blast_radius_estimate", "") or "").lower()
    if blast_radius == "global":
        score += 3
        factors.append("global_blast_radius")
    elif blast_radius in ("service", "subsystem"):
        score += 2
        factors.append("service_blast_radius")

    confidence = float(getattr(work_item, "agent_confidence", 0.0) or 0.0)
    if confidence and confidence < 0.5:
        score += 2
        factors.append("low_agent_confidence")
    elif confidence and confidence < 0.75:
        score += 1

    human_review_status = str(getattr(work_item, "human_review_status", "") or "").lower()
    if human_review_status in ("none", "pending", ""):
        score += 1
        factors.append("human_review_pending")

    if project_type in {"yocto-bsp", "embedded-hardware", "fpga-rtl", "fpga-rtl-amd"}:
        score += 1
        factors.append("safety_critical_project_type")

    level = risk_level_from_score(score)
    overridden = False
    override_reason = ""
    override_level = str(getattr(work_item, "risk_override_level", "") or "").lower()
    if override_level in _RISK_GATES:
        level = override_level
        overridden = True
        override_reason = str(getattr(work_item, "risk_override_reason", "") or "").strip()

    return RiskAssessment(
        score=score,
        level=level,
        factors=factors,
        required_gates=list(_RISK_GATES[level]),
        overridden=overridden,
        override_reason=override_reason,
    )


def assess_all_work_items(root: Path) -> list[tuple[str, RiskAssessment]]:
    from specsmith.wi_store import WorkItemStore

    project_type = _read_project_type(root)
    store = WorkItemStore(root)
    out: list[tuple[str, RiskAssessment]] = []
    for item in store.load():
        out.append((item.id, assess_work_item_risk(item, project_type=project_type)))
    return out


def _read_project_type(root: Path) -> str:
    import yaml

    cfg = root / "scaffold.yml"
    if not cfg.is_file():
        cfg = root / "docs" / "SPECSMITH.yml"
    if not cfg.is_file():
        return ""
    try:
        raw = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001
        return ""
    if not isinstance(raw, dict):
        return ""
    return str(raw.get("type", "") or "")
