# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Architect — scan project and generate architecture documentation."""

from __future__ import annotations

from pathlib import Path


def scan_project_structure(root: Path) -> dict[str, object]:  # noqa: C901
    """Scan a project and extract architecture-relevant information.

    Returns a dict with modules, entry_points, languages, dependencies,
    git_summary, and existing_docs.
    """
    from specsmith.importer import (
        _extract_git_commits,
        _extract_git_contributors,
        _extract_readme_summary,
        _parse_dependencies,
        detect_project,
    )

    result = detect_project(root)
    commits = _extract_git_commits(root)
    contributors = _extract_git_contributors(root)
    readme = _extract_readme_summary(root)
    deps = _parse_dependencies(root)

    # Find existing architecture docs
    existing_arch: list[str] = []
    docs_dir = root / "docs"
    if docs_dir.is_dir():
        for p in docs_dir.rglob("*"):
            if p.is_file() and "architecture" in p.name.lower():
                existing_arch.append(str(p.relative_to(root)))

    return {
        "name": root.name,
        "languages": result.languages,
        "primary_language": result.primary_language,
        "secondary_languages": result.secondary_languages,
        "build_system": result.build_system,
        "test_framework": result.test_framework,
        "modules": result.modules,
        "entry_points": result.entry_points,
        "dependencies": deps,
        "readme_summary": readme,
        "recent_commits": commits[:10],
        "contributors": contributors,
        "existing_arch_docs": existing_arch,
        "file_count": result.file_count,
        "inferred_type": result.inferred_type.value if result.inferred_type else "unknown",
    }


def generate_architecture(
    root: Path,
    *,
    components: list[dict[str, str]] | None = None,
    data_flow: str = "",
    deployment: str = "",
    scan: dict[str, object] | None = None,
) -> Path:
    """Generate docs/architecture.md from scan data + user input.

    Returns the path to the generated file.
    """
    if scan is None:
        scan = scan_project_structure(root)

    name = str(scan.get("name", root.name))
    langs: dict[str, int] = dict(scan.get("languages", {}) or {})  # type: ignore[call-overload]
    primary = str(scan.get("primary_language", "unknown"))
    secondary: list[str] = list(scan.get("secondary_languages", []) or [])  # type: ignore[call-overload]
    lang_list = [primary] + secondary
    lang_display = ", ".join(str(l) for l in lang_list if l)  # noqa: E741

    doc = f"# Architecture — {name}\n\n"

    # Overview
    doc += "## Overview\n\n"
    readme = scan.get("readme_summary", "")
    if readme:
        doc += f"{readme}\n\n"
    doc += f"- **Languages**: {lang_display}\n"
    doc += f"- **Build system**: {scan.get('build_system', 'not detected')}\n"
    doc += f"- **Test framework**: {scan.get('test_framework', 'not detected')}\n"
    doc += f"- **Project type**: {scan.get('inferred_type', 'unknown')}\n"
    doc += f"- **Files**: {scan.get('file_count', 0)}\n\n"

    # Components
    if components:
        doc += "## Components\n\n"
        for comp in components:
            doc += f"### {comp.get('name', 'unnamed')}\n"
            if comp.get("purpose"):
                doc += f"- **Purpose**: {comp['purpose']}\n"
            if comp.get("interfaces"):
                doc += f"- **Interfaces**: {comp['interfaces']}\n"
            if comp.get("dependencies"):
                doc += f"- **Dependencies**: {comp['dependencies']}\n"
            doc += "\n"
    elif scan.get("modules"):
        doc += "## Modules\n\n"
        for mod in list(scan.get("modules", []) or []):  # type: ignore[call-overload]
            doc += f"### {mod}\n- **Purpose**: [Describe {mod} purpose]\n\n"

    # Data flow
    if data_flow:
        doc += f"## Data Flow\n\n{data_flow}\n\n"
    else:
        doc += "## Data Flow\n\n[Describe how data flows between components]\n\n"

    # Dependencies
    deps: list[str] = list(scan.get("dependencies", []) or [])  # type: ignore[call-overload]
    if deps:
        doc += "## External Dependencies\n\n"
        for dep in deps[:30]:
            doc += f"- `{dep}`\n"
        doc += "\n"

    # Entry points
    eps: list[str] = list(scan.get("entry_points", []) or [])  # type: ignore[call-overload]
    if eps:
        doc += "## Entry Points\n\n"
        for ep in eps:
            doc += f"- `{ep}`\n"
        doc += "\n"

    # Language distribution
    if langs and len(langs) > 1:
        doc += "## Language Distribution\n\n"
        for lang_name, count in sorted(langs.items(), key=lambda x: -x[1]):
            doc += f"- {lang_name}: {count} files\n"
        doc += "\n"

    # Deployment
    if deployment:
        doc += f"## Deployment\n\n{deployment}\n\n"

    # Existing architecture references
    existing: list[str] = list(scan.get("existing_arch_docs", []) or [])  # type: ignore[call-overload]
    if existing:
        doc += "## Related Documents\n\n"
        for ref in existing:
            doc += f"- [{ref}]({ref})\n"
        doc += "\n"

    # Write
    arch_path = root / "docs" / "ARCHITECTURE.md"
    arch_path.parent.mkdir(parents=True, exist_ok=True)
    arch_path.write_text(doc, encoding="utf-8")
    return arch_path


# ---------------------------------------------------------------------------
# Epistemic BA Interview system (REQ-375)
# ---------------------------------------------------------------------------

from dataclasses import dataclass  # noqa: E402 — kept near usage
from dataclasses import field as _field  # noqa: E402 — kept near usage


@dataclass
class ArchitecturalDimension:
    """A single tracked dimension of the architecture belief state."""

    key: str
    question: str
    hint: str
    confidence: float = 0.0
    answer: str = ""


# ---------------------------------------------------------------------------
# specsmith feature gap catalog (REQ-382)
# ---------------------------------------------------------------------------


@dataclass
class FeatureGap:
    """A detected gap between project needs and specsmith's current feature set."""

    title: str
    description: str
    project_type: str
    severity: str = "enhancement"  # "enhancement" | "bug" | "question"
    labels: list[str] = _field(default_factory=list)


#: Maps ProjectType.value → list[FeatureGap] for known project categories.
SPECSMITH_FEATURE_CATALOG: dict[str, list[FeatureGap]] = {
    "embedded-hardware": [
        FeatureGap(
            title="CAN bus governance templates for embedded projects",
            description=(
                "specsmith has no built-in governance templates for CAN bus interface "
                "definitions, CANopen object dictionary validation, or SocketCAN integration "
                "tests. Embedded projects using CAN (e.g. dart-mx8m-plus, automotive ECUs) need "
                "pre-built requirement patterns for message IDs, timing SLAs, and bus-off recovery."
            ),
            project_type="embedded-hardware",
            severity="enhancement",
            labels=["embedded", "can-bus", "governance-template"],
        ),
        FeatureGap(
            title="MISRA-C / CERT-C compliance checker integration",
            description=(
                "specsmith has no built-in MISRA-C or CERT-C rule checking. Safety-critical "
                "embedded projects need compliance scan results surfaced as governance events."
            ),
            project_type="embedded-hardware",
            severity="enhancement",
            labels=["embedded", "safety-critical", "compliance"],
        ),
        FeatureGap(
            title="Hardware-in-loop (HIL) test integration",
            description=(
                "specsmith verify does not integrate with HIL test rigs (renode, QEMU boards, "
                "dSPACE). Embedded projects need HIL pass/fail results to record ledger events "
                "and drive REQ coverage."
            ),
            project_type="embedded-hardware",
            severity="enhancement",
            labels=["embedded", "testing", "hil"],
        ),
    ],
    "yocto-bsp": [
        FeatureGap(
            title="Yocto layer governance templates",
            description=(
                "specsmith has no requirement templates for Yocto layers, recipes, or MACHINE "
                "configurations. BSP projects need governance patterns for layer compatibility "
                "matrices, recipe license audits, and image manifests."
            ),
            project_type="yocto-bsp",
            severity="enhancement",
            labels=["yocto", "embedded", "governance-template"],
        ),
        FeatureGap(
            title="OTA firmware update governance",
            description=(
                "specsmith has no support for OTA update governance (signing keys, rollback "
                "requirements, A/B partition requirements). Yocto BSP projects deploying "
                "mender, swupdate, or RAUC need these tracked as REQs."
            ),
            project_type="yocto-bsp",
            severity="enhancement",
            labels=["yocto", "ota", "firmware"],
        ),
    ],
    "cli-python": [
        FeatureGap(
            title="PyPI release governance workflow",
            description=(
                "specsmith save does not integrate with PyPI publishing. CLI Python projects need "
                "a governed release workflow that records the PyPI upload as a ledger event "
                "and links it to a work item."
            ),
            project_type="cli-python",
            severity="enhancement",
            labels=["python", "release", "pypi"],
        ),
    ],
    "web-frontend": [
        FeatureGap(
            title="Accessibility (WCAG) compliance tracking",
            description=(
                "specsmith has no WCAG requirement templates or axe/Lighthouse integration. "
                "Web frontend projects need accessibility REQs tracked alongside functional "
                "requirements."
            ),
            project_type="web-frontend",
            severity="enhancement",
            labels=["web", "accessibility", "compliance"],
        ),
    ],
    "data-ml": [
        FeatureGap(
            title="ML model card governance",
            description=(
                "specsmith has no support for ML model cards (accuracy, bias, data lineage). "
                "Data/ML projects need model performance metrics tracked as REQs and recorded "
                "in the ESDB ledger at training time."
            ),
            project_type="data-ml",
            severity="enhancement",
            labels=["ml", "model-card", "data-governance"],
        ),
    ],
    "safety-critical": [
        FeatureGap(
            title="IEC 61508 / ISO 26262 safety lifecycle integration",
            description=(
                "specsmith has no support for functional safety standards (IEC 61508, ISO 26262, "
                "IEC 62443). Safety-critical projects need SIL/ASIL classification on requirements "
                "and hazard analysis traces."
            ),
            project_type="safety-critical",
            severity="enhancement",
            labels=["safety-critical", "iec61508", "iso26262"],
        ),
    ],
    "llm-app": [
        FeatureGap(
            title="LLM evaluation governance (evals)",
            description=(
                "specsmith has no support for LLM evaluation harnesses (promptfoo, inspect, "
                "evals). LLM app projects need eval run results tracked as governance events "
                "and linked to prompt requirement REQs."
            ),
            project_type="llm-app",
            severity="enhancement",
            labels=["llm", "evals", "ai-governance"],
        ),
    ],
    "mcp-server": [
        FeatureGap(
            title="MCP tool compliance checking",
            description=(
                "specsmith has an MCP governance_req_list tool but no MCP compliance checker "
                "that validates tool schemas against requirements. MCP server projects need "
                "automated MCP tool contract testing."
            ),
            project_type="mcp-server",
            severity="enhancement",
            labels=["mcp", "compliance", "testing"],
        ),
    ],
    "fpga-rtl": [
        FeatureGap(
            title="RTL simulation result governance integration",
            description=(
                "specsmith has no integration with RTL simulators (Verilator, GHDL, ModelSim). "
                "FPGA/RTL projects need simulation pass/fail results captured as ledger events "
                "and linked to requirement coverage."
            ),
            project_type="fpga-rtl",
            severity="enhancement",
            labels=["fpga", "rtl", "simulation"],
        ),
    ],
}

# Aliases — map related project types to the closest gap list
for _alias, _src in [
    ("embedded-python-hmi", "embedded-hardware"),
    ("fpga-rtl-amd", "fpga-rtl"),
    ("fpga-rtl-intel", "fpga-rtl"),
    ("fpga-rtl-lattice", "fpga-rtl"),
    ("mixed-fpga-embedded", "fpga-rtl"),
    ("mixed-fpga-firmware", "embedded-hardware"),
    ("agent-orchestration", "llm-app"),
    ("rag-pipeline", "llm-app"),
    ("mlops-platform", "data-ml"),
]:
    SPECSMITH_FEATURE_CATALOG[_alias] = SPECSMITH_FEATURE_CATALOG[_src]


# ---------------------------------------------------------------------------
# Feature gap analysis (REQ-382, REQ-383)
# ---------------------------------------------------------------------------


def run_feature_gap_analysis(
    root: Path,
    dims: list[ArchitecturalDimension] | None = None,
) -> list[FeatureGap]:
    """Cross-reference interview answers against the feature catalog (REQ-382).

    Returns a list of :class:`FeatureGap` objects for the detected project type.
    If no project_type dimension answer is available, falls back to the
    inferred_type from ``scan_project_structure``.
    """
    project_type = ""

    # 1. Try interview state
    if dims is None:
        dims = _load_interview_state(root)
    for d in dims:
        if d.key == "project_type" and d.answer:
            project_type = d.answer.strip().lower().replace(" ", "-")
            break

    # 2. Fall back to scan
    if not project_type:
        try:
            scan = scan_project_structure(root)
            project_type = str(scan.get("inferred_type", ""))
        except Exception:  # noqa: BLE001
            pass

    return list(SPECSMITH_FEATURE_CATALOG.get(project_type, []))


# ---------------------------------------------------------------------------
# Dimension list (REQ-375, REQ-381)
# ---------------------------------------------------------------------------

#: The nine base dimensions (no project_type prepended yet)
_ARCH_DIMENSIONS_BASE: list[ArchitecturalDimension] = [
    ArchitecturalDimension(
        key="problem_domain",
        question="What problem does this system solve?",
        hint="Describe the core value proposition and the pain point being addressed.",
    ),
    ArchitecturalDimension(
        key="user_types",
        question="Who are the users or personas that interact with this system?",
        hint="List roles, personas, or user types. Include external systems if applicable.",
    ),
    ArchitecturalDimension(
        key="key_integrations",
        question="What external systems, APIs, or data sources does this system integrate with?",
        hint="List APIs, databases, message queues, hardware, third-party services.",
    ),
    ArchitecturalDimension(
        key="technical_constraints",
        question="What are the technical constraints (platform, language, budget, license)?",
        hint="Examples: must run on Python 3.11+, GPLv3, no cloud dependencies, \u20acK budget.",
    ),
    ArchitecturalDimension(
        key="deployment_target",
        question="Where will this system be deployed?",
        hint="Examples: AWS Lambda, on-prem bare-metal, Raspberry Pi, Docker, Windows desktop.",
    ),
    ArchitecturalDimension(
        key="scale_expectations",
        question="What are the scale expectations?",
        hint="Users, transactions/day, data volume, latency SLA — be as specific as possible.",
    ),
    ArchitecturalDimension(
        key="data_model",
        question="What are the primary data entities and how is data persisted?",
        hint="Core models, database type (SQL/NoSQL/event-sourced), retention and archival policy.",
    ),
    ArchitecturalDimension(
        key="security_model",
        question="What are the security and compliance requirements?",
        hint="Auth (OAuth2, LDAP, API key), encryption at rest/transit, GDPR, SOC 2, etc.",
    ),
    ArchitecturalDimension(
        key="failure_modes",
        question="What must NEVER fail, and what is acceptable degradation?",
        hint="Hard SLAs, disaster recovery, graceful degradation scenarios.",
    ),
]


def _make_dimensions(inferred_type: str = "") -> list[ArchitecturalDimension]:
    """Build the full 10-dimension list, prepending project_type (REQ-381)."""
    import copy

    hint = "Describe the kind of project (e.g. CLI tool, web app, embedded firmware, ML pipeline)."
    if inferred_type and inferred_type != "unknown":
        hint = (
            f"Auto-detected: '{inferred_type}'. Confirm or describe more specifically. "
            "E.g. 'Yocto BSP for i.MX8M Plus with Wayland kiosk' or 'FastAPI microservice'."
        )
    project_type_dim = ArchitecturalDimension(
        key="project_type",
        question="What type of project is this?",
        hint=hint,
    )
    return [project_type_dim] + copy.deepcopy(_ARCH_DIMENSIONS_BASE)


#: Public alias — 10 dimensions (project_type first, then the original 9)
ARCH_DIMENSIONS: list[ArchitecturalDimension] = _make_dimensions()

_INTERVIEW_STATE_FILE = ".specsmith/arch-interview.json"
_ARCH_SNAPSHOT_FILE = ".specsmith/arch-snapshot.md"
_CONFIDENCE_THRESHOLD = 0.75


def score_answer(answer: str) -> float:
    """Score an answer string and return the confidence increment.

    Rubric (REQ-375):
    - Empty or whitespace: +0.05
    - 1–15 chars (vague): +0.10
    - 16–60 chars (general): +0.25
    - 61–200 chars (specific): +0.40
    - 200+ chars OR contains metrics/constraints: +0.50
    """
    if not answer or not answer.strip():
        return 0.05
    stripped = answer.strip()
    length = len(stripped)
    # Bonus: contains metric-like tokens (numbers with units, %, SLA keywords)
    import re

    _metrics_re = re.compile(
        r"\d+\s*(?:ms|s|req|tps|rps|gb|tb|mb|%|user|k|m|\$|\xe2\x82\xac|eur|usd|"
        r"sla|slo|rto|rpo|tls|ssl|oauth|gdpr|soc|hipaa|pci)",
        re.IGNORECASE,
    )
    has_metrics = bool(_metrics_re.search(stripped))

    if length > 200 or (length > 60 and has_metrics):
        return 0.50
    if length > 60:
        return 0.40
    if length > 15:
        return 0.25
    return 0.10


def _load_interview_state(root: Path) -> list[ArchitecturalDimension]:
    """Load a previously-saved interview state from JSON, or return fresh dimensions.

    In YAML-first mode the project_type hint is pre-populated from
    ``scan_project_structure`` so the user sees the auto-detected type
    immediately (REQ-381).
    """
    import contextlib
    import json

    # Auto-detect project type for the hint
    inferred = ""
    with contextlib.suppress(Exception):
        scan = scan_project_structure(root)
        inferred = str(scan.get("inferred_type", ""))

    state_path = root / _INTERVIEW_STATE_FILE
    dims = _make_dimensions(inferred)
    if state_path.exists():
        with contextlib.suppress(Exception):
            data = json.loads(state_path.read_text(encoding="utf-8"))
            by_key = {d.key: d for d in dims}
            for entry in data:
                key = entry.get("key", "")
                if key in by_key:
                    by_key[key].confidence = float(entry.get("confidence", 0.0))
                    by_key[key].answer = str(entry.get("answer", ""))
    return dims


def _save_interview_state(root: Path, dims: list[ArchitecturalDimension]) -> None:
    """Persist interview state to JSON (crash-safe)."""
    import json

    state_path = root / _INTERVIEW_STATE_FILE
    state_path.parent.mkdir(parents=True, exist_ok=True)
    data = [{"key": d.key, "confidence": d.confidence, "answer": d.answer} for d in dims]
    state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _render_architecture_md(
    root: Path, dims: list[ArchitecturalDimension], project_name: str
) -> str:
    """Render docs/ARCHITECTURE.md from interview dimensions."""
    lines = [
        f"# Architecture \u2014 {project_name}",
        "",
        "<!-- specsmith: generated by architect interview -->",
        "<!-- Confidence annotations: each section has a [confidence] score 0.0–1.0 -->",
        "",
    ]
    for dim in dims:
        conf = dim.confidence
        conf_bar = "█" * int(conf * 10) + "░" * (10 - int(conf * 10))
        lines.append(f"## {dim.key.replace('_', ' ').title()}")
        lines.append(f"<!-- confidence: {conf:.2f} [{conf_bar}] -->")
        if dim.answer:
            lines.append(dim.answer)
        else:
            lines.append(f"[No answer provided for: {dim.question}]")
        lines.append("")
    return "\n".join(lines)


def _render_proposed_reqs(dims: list[ArchitecturalDimension]) -> str:
    """Render docs/requirements/proposed.yml from interview dimensions."""
    lines = [
        "# Proposed requirements derived from architect interview",
        "# Status: proposed — review and promote to 'defined' when validated",
    ]
    req_num = 900  # Start at REQ-900 to avoid collisions with existing REQs
    for dim in dims:
        if not dim.answer or not dim.answer.strip():
            continue
        req_num += 1
        conf = min(dim.confidence, 1.0)
        lines.append(f"- id: REQ-{req_num}")
        lines.append(f"  title: {dim.key.replace('_', ' ').title()} Requirement")
        lines.append(
            f"  description: >-\n"
            f"    Derived from architect interview ({dim.key}): {dim.answer[:200]}"
        )
        lines.append("  status: proposed")
        lines.append(f"  confidence: {conf:.2f}")
        lines.append("")
    return "\n".join(lines)


def run_interview(
    root: Path,
    *,
    non_interactive: bool = False,
) -> dict[str, object]:
    """Run the epistemic BA interview and produce ARCHITECTURE.md.

    Non-interactive mode (when stdin is not a TTY or non_interactive=True) auto-generates
    synthetic answers from existing project scan so the command never blocks in CI.

    Returns a summary dict with keys: arch_path, proposed_reqs_path, dimensions, all_confident.
    """
    import sys

    if non_interactive or not sys.stdin.isatty():
        return _run_non_interactive_interview(root)

    dims = _load_interview_state(root)
    project_name = root.name

    # Interview loop: max-uncertainty-first ordering
    while True:
        incomplete = [d for d in dims if d.confidence < _CONFIDENCE_THRESHOLD]
        if not incomplete:
            break

        # Ask about lowest-confidence dimension first
        target = min(incomplete, key=lambda d: d.confidence)

        print(f"\n[{target.confidence:.0%}] {target.question}")  # noqa: T201
        print(f"  Hint: {target.hint}")  # noqa: T201
        if target.answer:
            print(f"  Previous: {target.answer[:80]}...")  # noqa: T201
        try:
            answer = input("  Your answer (or 'done' to finish): ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if answer.lower() in ("done", "exit", "quit"):
            break

        if answer:
            increment = score_answer(answer)
            target.confidence = min(1.0, target.confidence + increment)
            target.answer = answer

        # Persist after each answer (crash-safe)
        _save_interview_state(root, dims)

    return _finalise_interview(root, dims, project_name)


def _run_non_interactive_interview(root: Path) -> dict[str, object]:
    """Auto-generate synthetic answers from project scan (for CI/non-interactive mode)."""
    try:
        scan = scan_project_structure(root)
    except Exception:  # noqa: BLE001
        scan = {"name": root.name, "primary_language": "unknown"}

    project_name = str(scan.get("name", root.name))
    primary_lang = str(scan.get("primary_language", "unknown"))
    inferred_type = str(scan.get("inferred_type", "unknown"))

    dims = _make_dimensions(inferred_type)

    # Assign synthetic answers so every dimension has some content
    synthetic = {
        "project_type": inferred_type,
        "problem_domain": f"A {inferred_type} system developed in {primary_lang}.",
        "user_types": "Developers and end-users of the system.",
        "key_integrations": "File system, standard library, and project dependencies.",
        "technical_constraints": f"Language: {primary_lang}. See pyproject.toml for constraints.",
        "deployment_target": "Standard operating system environment.",
        "scale_expectations": "Small to medium scale; exact SLAs to be defined.",
        "data_model": "Project-specific data model; see source code for entity definitions.",
        "security_model": "Standard security practices; compliance requirements TBD.",
        "failure_modes": "Graceful degradation; specific SLAs to be defined by stakeholders.",
    }
    for dim in dims:
        answer = synthetic.get(dim.key, "[auto-generated placeholder]")
        dim.answer = answer
        dim.confidence = score_answer(answer)

    return _finalise_interview(root, dims, project_name)


def _finalise_interview(
    root: Path, dims: list[ArchitecturalDimension], project_name: str
) -> dict[str, object]:
    """Write ARCHITECTURE.md and proposed.yml, return summary dict."""
    arch_md = _render_architecture_md(root, dims, project_name)
    arch_path = root / "docs" / "ARCHITECTURE.md"
    arch_path.parent.mkdir(parents=True, exist_ok=True)
    arch_path.write_text(arch_md, encoding="utf-8")

    proposed_yml = _render_proposed_reqs(dims)
    req_dir = root / "docs" / "requirements"
    req_dir.mkdir(parents=True, exist_ok=True)
    proposed_path = req_dir / "proposed.yml"
    proposed_path.write_text(proposed_yml, encoding="utf-8")

    all_confident = all(d.confidence >= _CONFIDENCE_THRESHOLD for d in dims)
    _save_interview_state(root, dims)

    return {
        "arch_path": arch_path,
        "proposed_reqs_path": proposed_path,
        "dimensions": dims,
        "all_confident": all_confident,
    }


def run_gap_analysis(root: Path) -> dict[str, object]:
    """Diff current ARCHITECTURE.md against stored snapshot; produce arch-gap.yml files.

    Returns a dict with: new_reqs, stale_reqs, proposed_tests, gap_reqs_path, gap_tests_path.
    """
    arch_path = root / "docs" / "ARCHITECTURE.md"
    snapshot_path = root / _ARCH_SNAPSHOT_FILE

    if not arch_path.exists():
        return {
            "new_reqs": [],
            "stale_reqs": [],
            "proposed_tests": [],
            "gap_reqs_path": None,
            "gap_tests_path": None,
            "message": "No ARCHITECTURE.md found. Run 'specsmith architect interview' first.",
        }

    current = arch_path.read_text(encoding="utf-8")

    # Save snapshot if not present
    if not snapshot_path.exists():
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(current, encoding="utf-8")
        return {
            "new_reqs": [],
            "stale_reqs": [],
            "proposed_tests": [],
            "gap_reqs_path": None,
            "gap_tests_path": None,
            "message": "Snapshot saved. Run again to compare changes.",
        }

    snapshot = snapshot_path.read_text(encoding="utf-8")

    import difflib
    import re

    # Extract section headings from both versions
    _heading_re = re.compile(r"^## (.+)$", re.MULTILINE)
    current_sections = set(_heading_re.findall(current))
    snapshot_sections = set(_heading_re.findall(snapshot))

    added = current_sections - snapshot_sections
    removed = snapshot_sections - current_sections

    # Unified diff for detecting changed content
    diff_lines = list(
        difflib.unified_diff(snapshot.splitlines(), current.splitlines(), lineterm="")
    )
    changed_sections: list[str] = []
    for line in diff_lines:
        if line.startswith("+ ## ") or line.startswith("- ## "):
            section = line[5:].strip()
            if section and section not in added and section not in removed:
                changed_sections.append(section)

    # Propose REQs for added sections
    new_reqs: list[dict[str, str]] = []
    req_num = 950
    for section in sorted(added):
        req_num += 1
        new_reqs.append(
            {
                "id": f"REQ-{req_num}",
                "title": f"New Architecture Component: {section}",
                "description": (
                    f"New architectural component '{section}' identified via gap analysis."
                ),
                "status": "proposed",
            }
        )

    # Flag stale REQs for removed/changed sections
    stale_reqs: list[dict[str, str]] = []
    try:
        import json as _json

        reqs_json = root / ".specsmith" / "requirements.json"
        if reqs_json.exists():
            existing_reqs = _json.loads(reqs_json.read_text(encoding="utf-8"))
            for req in existing_reqs:
                title = str(req.get("title", "")).lower()
                for section in removed | set(changed_sections):
                    if any(kw in title for kw in section.lower().split() if len(kw) > 4):
                        stale_reqs.append(
                            {
                                "id": str(req.get("id", "")),
                                "reason": f"Architecture section '{section}' removed/changed",
                            }
                        )
                        break
    except Exception:  # noqa: BLE001
        pass

    # Propose test stubs for new reqs
    proposed_tests: list[dict[str, str]] = []
    test_num = 950
    for req in new_reqs:
        test_num += 1
        proposed_tests.append(
            {
                "id": f"TEST-{test_num}",
                "title": f"Test for {req['title']}",
                "requirement_id": req["id"],
                "type": "integration",
                "status": "proposed",
            }
        )

    # Write gap files
    req_dir = root / "docs" / "requirements"
    test_dir = root / "docs" / "tests"
    req_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)

    gap_reqs_path: Path | None = None
    gap_tests_path: Path | None = None

    if new_reqs or stale_reqs:
        gap_reqs_path = req_dir / "arch-gap.yml"
        lines = ["# Architecture gap analysis \u2014 proposed requirements"]
        for req in new_reqs:
            lines.append(f"- id: {req['id']}")
            lines.append(f"  title: {req['title']}")
            lines.append(f"  description: {req['description']}")
            lines.append(f"  status: {req['status']}")
            lines.append("")
        for req in stale_reqs:
            lines.append(f"# REVIEW: {req['id']} \u2014 {req['reason']}")
        gap_reqs_path.write_text("\n".join(lines), encoding="utf-8")

    if proposed_tests:
        gap_tests_path = test_dir / "arch-gap.yml"
        lines = ["# Architecture gap analysis \u2014 proposed tests"]
        for test in proposed_tests:
            lines.append(f"- id: {test['id']}")
            lines.append(f"  title: {test['title']}")
            lines.append(f"  requirement_id: {test['requirement_id']}")
            lines.append(f"  type: {test['type']}")
            lines.append("")
        gap_tests_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "new_reqs": new_reqs,
        "stale_reqs": stale_reqs,
        "proposed_tests": proposed_tests,
        "gap_reqs_path": gap_reqs_path,
        "gap_tests_path": gap_tests_path,
        "message": (
            f"{len(added)} section(s) added, {len(removed)} removed, "
            f"{len(changed_sections)} changed."
        ),
    }


def run_arch_update(root: Path, *, non_interactive: bool = False) -> dict[str, object]:
    """Re-engage BA interview for a project with existing ARCHITECTURE.md.

    1. Reads existing ARCHITECTURE.md and restores confidence from annotations.
    2. Saves old version as arch-snapshot.md.
    3. Runs interview for low-confidence dimensions only.
    4. Calls run_gap_analysis() to produce diff report.
    """
    import re

    arch_path = root / "docs" / "ARCHITECTURE.md"
    snapshot_path = root / _ARCH_SNAPSHOT_FILE

    # Save current arch as snapshot before overwriting
    if arch_path.exists():
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(arch_path.read_text(encoding="utf-8"), encoding="utf-8")

    # Restore confidence from annotations in existing ARCHITECTURE.md
    dims = _load_interview_state(root)
    if arch_path.exists():
        arch_text = arch_path.read_text(encoding="utf-8")
        import contextlib

        _conf_re = re.compile(r"<!-- confidence: (\d+\.\d+)", re.MULTILINE)
        matches = _conf_re.findall(arch_text)
        for dim, match in zip(dims, matches, strict=False):
            with contextlib.suppress(ValueError):
                dim.confidence = float(match)

    # Run interview (which skips dimensions already above threshold)
    result = run_interview(root, non_interactive=non_interactive)

    # Run gap analysis
    gap_result = run_gap_analysis(root)
    result["gap"] = gap_result
    return result
