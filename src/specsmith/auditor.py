# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Auditor — drift detection and health checks (Spec Sections 23 + 26)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from specsmith.console_utils import make_console

console = make_console()


@dataclass
class AuditResult:
    """Result of a single audit check."""

    name: str
    passed: bool
    message: str
    fixable: bool = False


@dataclass
class AuditReport:
    """Aggregate audit report."""

    results: list[AuditResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def fixable(self) -> int:
        return sum(1 for r in self.results if not r.passed and r.fixable)

    @property
    def healthy(self) -> bool:
        return self.failed == 0


# ---------------------------------------------------------------------------
# Governance file existence checks
# ---------------------------------------------------------------------------

REQUIRED_FILES = [
    "AGENTS.md",
    "LEDGER.md",
]

GOVERNANCE_FILES = [
    "docs/governance/RULES.md",
    "docs/governance/SESSION-PROTOCOL.md",
    "docs/governance/LIFECYCLE.md",
    "docs/governance/ROLES.md",
    "docs/governance/CONTEXT-BUDGET.md",
    "docs/governance/VERIFICATION.md",
    "docs/governance/DRIFT-METRICS.md",
]

RECOMMENDED_FILES = [
    "docs/REQUIREMENTS.md",
    "docs/TESTS.md",
    "docs/ARCHITECTURE.md",
    "docs/SPECSMITH.yml",  # canonical scaffold config (uppercase, like peer governance files)
    "CONTRIBUTING.md",
    "LICENSE",
]

#: Root-level files that should be in docs/ — flagged by check_no_root_copies()
_ROOT_GOVERNANCE_FILES = [
    "REQUIREMENTS.md",
    "TESTS.md",
    "LEDGER.md",
    "scaffold.yml",
]


def check_governance_files(root: Path) -> list[AuditResult]:
    """Check that all required governance files exist."""
    results: list[AuditResult] = []

    for f in REQUIRED_FILES:
        path = root / f
        found = path.exists()
        # LEDGER.md: also check docs/LEDGER.md (some imported projects place it there)
        if not found and f == "LEDGER.md":
            found = (root / "docs" / "LEDGER.md").exists()
        results.append(
            AuditResult(
                name=f"file-exists:{f}",
                passed=found,
                message=f"Required file {f} {'exists' if found else 'MISSING'}",
            )
        )

    # Modular governance: either all exist or AGENTS.md is self-contained (>200 lines)
    agents_path = root / "AGENTS.md"
    agents_lines = 0
    if agents_path.exists():
        agents_lines = len(agents_path.read_text(encoding="utf-8").splitlines())

    if agents_lines > 200:
        # Modular governance is REQUIRED
        for f in GOVERNANCE_FILES:
            path = root / f
            results.append(
                AuditResult(
                    name=f"file-exists:{f}",
                    passed=path.exists(),
                    message=(
                        f"Governance file {f} {'exists' if path.exists() else 'MISSING'}"
                        f" (AGENTS.md is {agents_lines} lines — modular split required)"
                    ),
                )
            )
    else:
        # Recommended but not required
        for f in GOVERNANCE_FILES:
            path = root / f
            if path.exists():
                results.append(
                    AuditResult(
                        name=f"file-exists:{f}",
                        passed=True,
                        message=f"Governance file {f} exists",
                    )
                )

    # Read scaffold.yml once for LICENSE exception logic
    _proprietary_license = False
    _scaffold_path = root / "scaffold.yml"
    if not _scaffold_path.exists():
        _scaffold_path = root / "docs" / "SPECSMITH.yml"
    if _scaffold_path.exists():
        try:
            import yaml as _yaml
            _raw = _yaml.safe_load(_scaffold_path.read_text(encoding="utf-8")) or {}
            _proprietary_license = str(_raw.get("license", "")).lower() in (
                "proprietary", "closed-source", "commercial", "all-rights-reserved",
            )
        except Exception:  # noqa: BLE001
            pass

    for f in RECOMMENDED_FILES:
        path = root / f
        found = path.exists()
        # For ARCHITECTURE.md, also search subdirectories (e.g. docs/architecture/*.md)
        if not found and "architecture" in f.lower():
            found = (
                bool(
                    list((root / "docs").glob("**/architecture*"))
                    + list((root / "docs").glob("**/ARCHITECTURE*"))
                )
                if (root / "docs").is_dir()
                else False
            )
        # docs/SPECSMITH.yml is the canonical config, but scaffold.yml at root is also acceptable
        # (legacy projects are not penalized for not yet having migrated)
        if not found and f == "docs/SPECSMITH.yml":
            found = (root / "scaffold.yml").exists()
        # LICENSE: skip the missing-file warning for proprietary projects (#143)
        if not found and f == "LICENSE" and _proprietary_license:
            results.append(
                AuditResult(
                    name=f"recommended:{f}",
                    passed=True,
                    message="LICENSE: proprietary project — no open-source license file required",
                )
            )
            continue
        results.append(
            AuditResult(
                name=f"recommended:{f}",
                passed=found,
                message=f"Recommended file {f} {'exists' if found else 'missing'}",
                fixable=not found,
            )
        )

    # Enforcement: flag root-level governance files ONLY when a canonical docs/ copy
    # also exists (true duplicate). Legacy projects with only a root copy are not
    # flagged here — they should migrate when ready.
    _docs_canonical_names = {
        "scaffold.yml": "docs/SPECSMITH.yml",
        "REQUIREMENTS.md": "docs/REQUIREMENTS.md",
        "TESTS.md": "docs/TESTS.md",
        "LEDGER.md": "docs/LEDGER.md",
    }
    for fname in _ROOT_GOVERNANCE_FILES:
        root_copy = root / fname
        canonical_rel = _docs_canonical_names.get(fname, f"docs/{fname}")
        canonical_copy = root / canonical_rel
        if root_copy.exists() and canonical_copy.exists():
            results.append(
                AuditResult(
                    name=f"no-root-copy:{fname}",
                    passed=False,
                    message=(
                        f"Duplicate: {fname} exists at both root and {canonical_rel}. "
                        f"Delete the root copy — {canonical_rel} is canonical."
                    ),
                    fixable=True,
                )
            )

    return results


# ---------------------------------------------------------------------------
# Requirement ↔ Test consistency
# ---------------------------------------------------------------------------

# REQ/TEST IDs: support both numeric-only (REQ-001) and namespaced (REQ-CTT-001).
# Pattern: REQ- followed by zero or more UPPERCASE- prefix segments, then digits.
# Examples: REQ-001, REQ-CTT-001, REQ-AUTH-023, TEST-042, TEST-CORE-007
_REQ_PATTERN = re.compile(r"\b(REQ-(?:[A-Z]+-)*\d+)\b")
_TEST_PATTERN = re.compile(r"\b(TEST-(?:[A-Z]+-)*\d+)\b")
# Match 'Covers: REQ-xxx', '**Requirement:** REQ-xxx', '**Requirement ID:** REQ-xxx',
# 'Requirement: REQ-xxx', 'Requirement ID: REQ-xxx'
# Also handles numeric-only IDs (REQ-001) via the updated _REQ_PATTERN.
_TEST_COVERS_PATTERN = re.compile(
    r"(?:Covers|\*\*Requirement(?:\s+ID)?:?\*\*|Requirement(?:\s+ID)?):?\s*"
    r"(REQ-(?:[A-Z]+-)*\d+(?:\s*,\s*REQ-(?:[A-Z]+-)*\d+)*)"
)


def check_req_test_consistency(root: Path) -> list[AuditResult]:
    """Check that every REQ has at least one TEST and vice versa."""
    results: list[AuditResult] = []

    req_path = root / "docs" / "REQUIREMENTS.md"
    # Use configurable test_spec_file path (#148)
    test_candidates = _get_test_spec_paths(root)
    test_path = next((p for p in test_candidates if p.exists()), None)

    if not req_path.exists() or test_path is None:
        results.append(
            AuditResult(
                name="req-test-consistency",
                passed=True,
                message="Skipped: REQUIREMENTS.md or test spec file not found",
            )
        )
        return results

    req_text = req_path.read_text(encoding="utf-8")
    test_text = test_path.read_text(encoding="utf-8")

    # Only check coverage for non-Draft requirements.
    # Draft requirements are stubs (e.g. auto-generated by import) and don't
    # need tests yet — checking them would produce noise on freshly imported projects.
    all_req_ids = set(_REQ_PATTERN.findall(req_text))
    draft_req_ids: set[str] = set()
    for block in re.split(r"(?=^## REQ-)", req_text, flags=re.MULTILINE):
        ids_in_block = set(_REQ_PATTERN.findall(block))
        if ids_in_block and re.search(r"\*\*Status\*\*:\s*[Dd]raft", block):
            draft_req_ids |= ids_in_block
    # Requirements that need coverage = all REQs minus those explicitly marked Draft
    req_ids = all_req_ids - draft_req_ids

    # Find which REQs are covered by tests
    covered_reqs: set[str] = set()
    for match in _TEST_COVERS_PATTERN.finditer(test_text):
        for req_id in _REQ_PATTERN.findall(match.group(0)):
            covered_reqs.add(req_id)

    uncovered = req_ids - covered_reqs
    if uncovered:
        results.append(
            AuditResult(
                name="req-test-coverage",
                passed=False,
                message=(
                    f"{len(uncovered)} REQ(s) without test coverage: {', '.join(sorted(uncovered))}"
                ),
            )
        )
    elif draft_req_ids and not req_ids:
        # All requirements are Draft — coverage is not yet required
        results.append(
            AuditResult(
                name="req-test-coverage",
                passed=True,
                message=(
                    f"{len(all_req_ids)} REQ(s) are Draft (coverage not required until accepted)"
                ),
            )
        )
    else:
        results.append(
            AuditResult(
                name="req-test-coverage",
                passed=True,
                message=f"All {len(req_ids)} accepted REQ(s) have test coverage",
            )
        )

    # Orphaned tests: use all_req_ids so tests covering Draft requirements
    # are not incorrectly flagged as orphaned.
    orphaned = covered_reqs - all_req_ids
    if orphaned:
        results.append(
            AuditResult(
                name="orphaned-tests",
                passed=False,
                message=(
                    f"{len(orphaned)} TEST(s) reference non-existent REQ(s): "
                    f"{', '.join(sorted(orphaned))}"
                ),
            )
        )

    return results


# ---------------------------------------------------------------------------
# Ledger health
# ---------------------------------------------------------------------------


def check_ledger_health(root: Path) -> list[AuditResult]:
    """Check ledger quality and staleness."""
    results: list[AuditResult] = []
    ledger_path = root / "LEDGER.md"
    if not ledger_path.exists():
        # Also check docs/LEDGER.md (some imported projects place it there)
        alt = root / "docs" / "LEDGER.md"
        if alt.exists():
            ledger_path = alt
        else:
            results.append(
                AuditResult(
                    name="ledger-exists",
                    passed=False,
                    message="LEDGER.md not found",
                )
            )
            return results

    text = ledger_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    line_count = len(lines)

    # Size check — uses configurable threshold (#145)
    threshold = _get_ledger_threshold(root)
    # Check audit_suppressions for opt-out
    raw = _read_scaffold_raw(root)
    suppressed = "ledger_size" in (raw.get("audit_suppressions") or [])
    if not suppressed and line_count > threshold:
        results.append(
            AuditResult(
                name="ledger-size",
                passed=False,
                message=(
                    f"LEDGER.md has {line_count} lines (threshold: {threshold}). "
                    f"Consider `specsmith compress`."
                ),
                fixable=True,
            )
        )
    else:
        results.append(
            AuditResult(
                name="ledger-size",
                passed=True,
                message=f"LEDGER.md has {line_count} lines (within {threshold} threshold)",
            )
        )

    # Open TODOs
    open_todos = sum(1 for line in lines if "- [ ]" in line)
    closed_todos = sum(1 for line in lines if "- [x]" in line)
    if open_todos > 20:
        results.append(
            AuditResult(
                name="ledger-open-todos",
                passed=False,
                message=f"{open_todos} open TODOs in ledger (may indicate stale items)",
            )
        )
    else:
        results.append(
            AuditResult(
                name="ledger-open-todos",
                passed=True,
                message=f"{open_todos} open, {closed_todos} closed TODOs",
            )
        )

    return results


# ---------------------------------------------------------------------------
# Context size (governance bloat detection)
# ---------------------------------------------------------------------------


# Default thresholds (used when no project type is detected)
_DEFAULT_THRESHOLDS: dict[str, int] = {
    "AGENTS.md": 200,
    "docs/governance/RULES.md": 800,
    "docs/governance/SESSION-PROTOCOL.md": 400,
    "docs/governance/LIFECYCLE.md": 200,
    "docs/governance/ROLES.md": 300,
    "docs/governance/CONTEXT-BUDGET.md": 300,
    "docs/governance/VERIFICATION.md": 400,
    "docs/governance/DRIFT-METRICS.md": 300,
}

# Type-specific overrides — hardware/embedded projects have denser rules.
_TYPE_THRESHOLD_OVERRIDES: dict[str, dict[str, int]] = {
    "fpga-rtl": {
        "AGENTS.md": 350,  # FPGA sessions need more board context
        "docs/governance/RULES.md": 1000,
        "docs/governance/SESSION-PROTOCOL.md": 500,
        "docs/governance/VERIFICATION.md": 600,
    },
    "fpga-rtl-amd": {
        "AGENTS.md": 350,
        "docs/governance/RULES.md": 1000,
        "docs/governance/SESSION-PROTOCOL.md": 500,
        "docs/governance/VERIFICATION.md": 600,
    },
    "yocto-bsp": {
        "AGENTS.md": 350,
        "docs/governance/RULES.md": 1000,
        "docs/governance/SESSION-PROTOCOL.md": 500,
        "docs/governance/VERIFICATION.md": 500,
    },
    "embedded-hardware": {
        "AGENTS.md": 350,
        "docs/governance/RULES.md": 1000,
        "docs/governance/VERIFICATION.md": 500,
    },
    "pcb-hardware": {
        "AGENTS.md": 300,
        "docs/governance/RULES.md": 900,
        "docs/governance/VERIFICATION.md": 500,
    },
}

# Type-specific LEDGER line thresholds (fpga-rtl hardware projects have long entries)
_DEFAULT_LEDGER_THRESHOLD = 500
_TYPE_LEDGER_THRESHOLDS: dict[str, int] = {
    "fpga-rtl": 5000,
    "fpga-rtl-amd": 5000,
    "fpga-rtl-intel": 5000,
    "fpga-rtl-lattice": 5000,
    "mixed-fpga-embedded": 3000,
    "mixed-fpga-firmware": 3000,
    "embedded-hardware": 2000,
    "yocto-bsp": 2000,
}


def _read_scaffold_raw(root: Path) -> dict:
    """Read scaffold.yml (or docs/SPECSMITH.yml) as a raw dict."""
    from specsmith.paths import find_scaffold
    scaffold_path = find_scaffold(root)
    if scaffold_path and scaffold_path.exists():
        try:
            import yaml
            with open(scaffold_path) as f:
                return yaml.safe_load(f) or {}
        except Exception:  # noqa: BLE001
            pass
    return {}


def _get_thresholds(root: Path) -> dict[str, int]:
    """Get governance size thresholds, scaled by project type and scaffold config.

    scaffold.yml overrides (#124):
      agents_md_line_threshold: N  -- override AGENTS.md limit
    """
    thresholds = dict(_DEFAULT_THRESHOLDS)
    raw = _read_scaffold_raw(root)
    ptype = raw.get("type", "")
    overrides = _TYPE_THRESHOLD_OVERRIDES.get(ptype, {})
    thresholds.update(overrides)

    # Allow per-project scaffold.yml override (#124)
    custom_agents = int(raw.get("agents_md_line_threshold", 0) or 0)
    if custom_agents > 0:
        thresholds["AGENTS.md"] = custom_agents

    return thresholds


def _get_ledger_threshold(root: Path) -> int:
    """Get LEDGER.md line-count audit threshold, scaled by project type.

    scaffold.yml override (#145):
      ledger_line_threshold: N  -- override LEDGER line limit
    Also supports audit_suppressions: [ledger_size] to silence entirely.
    """
    raw = _read_scaffold_raw(root)
    # scaffold.yml explicit override (#145)
    custom = int(raw.get("ledger_line_threshold", 0) or 0)
    if custom > 0:
        return custom
    ptype = raw.get("type", "")
    return _TYPE_LEDGER_THRESHOLDS.get(ptype, _DEFAULT_LEDGER_THRESHOLD)


def _get_test_spec_paths(root: Path) -> list[Path]:
    """Return candidate test spec paths, honouring scaffold.yml test_spec_file (#148)."""
    raw = _read_scaffold_raw(root)
    custom = raw.get("test_spec_file", "") or ""
    if custom:
        candidates = [root / custom.strip(), root / "docs" / "TESTS.md"]
    else:
        candidates = [root / "docs" / "TESTS.md", root / "TESTS.md"]
    return candidates


def check_context_size(root: Path) -> list[AuditResult]:
    """Check governance file sizes against type-aware thresholds."""
    results: list[AuditResult] = []
    thresholds = _get_thresholds(root)

    for rel_path, max_lines in thresholds.items():
        path = root / rel_path
        if not path.exists():
            continue
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        ok = line_count <= max_lines
        results.append(
            AuditResult(
                name=f"context-size:{rel_path}",
                passed=ok,
                message=(
                    f"{rel_path}: {line_count} lines"
                    + ("" if ok else f" (exceeds {max_lines} threshold)")
                ),
            )
        )

    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_tool_configuration(root: Path) -> list[AuditResult]:
    """Check that CI config references the expected verification tools."""
    results: list[AuditResult] = []
    scaffold_path = root / "scaffold.yml"
    if not scaffold_path.exists():
        return results  # Not a specsmith project — skip silently

    import yaml

    from specsmith.config import ProjectConfig
    from specsmith.tools import get_tools

    try:
        with open(scaffold_path) as f:
            raw = yaml.safe_load(f)
        config = ProjectConfig(**raw)
    except Exception:  # noqa: BLE001
        return results  # Malformed config — other checks will catch this

    tools = get_tools(config)
    if not any([tools.lint, tools.typecheck, tools.test, tools.security]):
        return results  # No tools registered for this type

    # Check CI configs for expected tool references
    ci_files = list(root.glob(".github/workflows/*.yml")) + [
        root / ".gitlab-ci.yml",
        root / "bitbucket-pipelines.yml",
    ]
    ci_content = ""
    for ci_file in ci_files:
        if ci_file.exists():
            ci_content += ci_file.read_text(encoding="utf-8")

    if not ci_content:
        results.append(
            AuditResult(
                name="tool-ci-config",
                passed=True,
                message="No CI config found — tool verification skipped",
            )
        )
        return results

    lint_missing: list[str] = []
    test_missing: list[str] = []

    # Check primary test tool (critical — hard fail if absent)
    for cmd in tools.test[:1]:
        tool_name = cmd.split()[0]
        if tool_name not in ci_content:
            test_missing.append(f"test:{tool_name}")

    # Check primary lint tool (advisory — projects may use a different linter
    # or none at all, especially when imported with existing CI)
    for cmd in tools.lint[:1]:
        tool_name = cmd.split()[0]
        if tool_name not in ci_content:
            lint_missing.append(f"lint:{tool_name}")

    all_missing = test_missing + lint_missing

    if test_missing:
        # Test tool missing — hard failure (tests are non-negotiable)
        results.append(
            AuditResult(
                name="tool-ci-config",
                passed=False,
                message=f"CI config missing expected tools: {', '.join(all_missing)}",
            )
        )
    elif lint_missing:
        # Only lint missing — fixable warning (test tool is present; lint is advisory)
        results.append(
            AuditResult(
                name="tool-ci-config",
                passed=True,  # Pass — test tool is there; lint is a recommendation
                message=(
                    f"CI config missing lint tool ({', '.join(lint_missing)}); "
                    f"test tool is present. Consider adding {lint_missing[0].split(':')[1]}."
                ),
                fixable=True,
            )
        )
    else:
        results.append(
            AuditResult(
                name="tool-ci-config",
                passed=True,
                message=f"CI config references expected verification tools for {config.type}",
            )
        )

    return results


def check_type_mismatch(root: Path) -> list[AuditResult]:
    """Check if scaffold.yml type matches actual detected project type."""
    results: list[AuditResult] = []
    scaffold_path = root / "scaffold.yml"
    if not scaffold_path.exists():
        return results

    import yaml

    from specsmith.config import ProjectConfig
    from specsmith.importer import detect_project

    try:
        with open(scaffold_path) as f:
            raw = yaml.safe_load(f)
        config = ProjectConfig(**raw)
        detected = detect_project(root)
        if detected.inferred_type and detected.inferred_type != config.type:
            results.append(
                AuditResult(
                    name="type-mismatch",
                    passed=False,
                    message=(
                        f"scaffold.yml type is {config.type} but detected "
                        f"{detected.inferred_type.value} from project files"
                    ),
                )
            )
        else:
            results.append(
                AuditResult(
                    name="type-mismatch",
                    passed=True,
                    message=f"Project type {config.type} matches detected structure",
                )
            )
    except Exception:  # noqa: BLE001
        pass

    return results


def check_trace_chain_integrity(root: Path) -> list[AuditResult]:
    """Check trace vault chain integrity if it exists."""
    trace_path = root / ".specsmith" / "trace.jsonl"
    if not trace_path.exists():
        return []  # No trace vault configured — skip silently

    try:
        from epistemic.trace import TraceVault

        vault = TraceVault(root / ".specsmith")
        valid, errors = vault.verify()
        if valid:
            return [
                AuditResult(
                    name="trace-chain-integrity",
                    passed=True,
                    message=f"Trace vault intact ({vault.count()} seals)",
                )
            ]
        else:
            return [
                AuditResult(
                    name="trace-chain-integrity",
                    passed=False,
                    message=f"Trace vault integrity failure: {'; '.join(errors[:2])}",
                )
            ]
    except ImportError:
        return []  # epistemic package not installed
    except Exception:  # noqa: BLE001
        return []


def check_phase_readiness(root: Path) -> list[AuditResult]:
    """Check AEE phase readiness (advisory — failed checks are warnings)."""
    results: list[AuditResult] = []
    from specsmith.paths import find_scaffold

    if not find_scaffold(root):
        return results

    from specsmith.phase import PHASE_MAP, evaluate_phase, read_phase

    phase_key = read_phase(root)
    phase = PHASE_MAP.get(phase_key)
    if not phase:
        return results

    passed, failed = evaluate_phase(phase, root)
    pct = int(len(passed) / len(phase.checks) * 100) if phase.checks else 100

    if failed:
        results.append(
            AuditResult(
                name="phase-readiness",
                passed=True,  # advisory — don't fail the audit
                message=(
                    f"Phase {phase.emoji} {phase.label}: {pct}% ready "
                    f"({len(failed)} check(s) remaining: {', '.join(failed[:3])})"
                ),
            )
        )
    else:
        msg = f"Phase {phase.emoji} {phase.label}: 100% ready"
        if phase.next_phase:
            msg += f" — run `specsmith phase next` to advance to {phase.next_phase}"
        results.append(AuditResult(name="phase-readiness", passed=True, message=msg))

    return results


def check_supplementary_rules(root: Path) -> list[AuditResult]:
    """Check that *_RULES.md files are referenced in AGENTS.md (#71).

    Scans the project tree for supplementary rule files (e.g.
    YOCTO_BUILD_RULES.md, VIVADO_RULES.md) and warns if they are not
    listed in the AGENTS.md governance registry.
    """
    results: list[AuditResult] = []
    agents_path = root / "AGENTS.md"
    if not agents_path.exists():
        return results

    agents_text = agents_path.read_text(encoding="utf-8")

    # Find all *_RULES.md or *_BUILD_RULES.md files outside docs/governance/
    rule_files: list[Path] = []
    skip_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__", ".specsmith"}
    for p in root.rglob("*_RULES.md"):
        if any(part in skip_dirs for part in p.parts):
            continue
        # Skip the standard governance files
        rel = str(p.relative_to(root)).replace("\\\\", "/")
        if rel.startswith("docs/governance/"):
            continue
        rule_files.append(p)

    if not rule_files:
        return results  # No supplementary rules found

    unreferenced: list[str] = []
    for rf in rule_files:
        rel = str(rf.relative_to(root)).replace("\\\\", "/")
        fname = rf.name
        # Check if the file is mentioned in AGENTS.md (by name or path)
        if fname not in agents_text and rel not in agents_text:
            unreferenced.append(rel)

    if unreferenced:
        results.append(
            AuditResult(
                name="supplementary-rules",
                passed=False,
                message=(
                    f"{len(unreferenced)} supplementary rule file(s) not in AGENTS.md: "
                    + ", ".join(unreferenced[:5])
                    + (
                        ". Add them to the auto-load registry."
                        if len(unreferenced) <= 5
                        else f" (+{len(unreferenced) - 5} more)"
                    )
                ),
                fixable=True,
            )
        )
    else:
        results.append(
            AuditResult(
                name="supplementary-rules",
                passed=True,
                message=f"All {len(rule_files)} supplementary rule file(s) referenced in AGENTS.md",
            )
        )

    return results


def check_hardware_gated_tests(root: Path) -> list[AuditResult]:
    """Check hardware-gated test status (#159).

    Hardware-gated Pending tests (marked Hardware-gated: true / hardware_gated: true
    in TESTS.md) are expected to be Pending until a hardware test session runs.
    They should NOT be flagged as coverage drift.
    """
    results: list[AuditResult] = []
    raw = _read_scaffold_raw(root)
    attr = raw.get("hardware_gated_test_attr", "hardware_gated") or "hardware_gated"
    # Read test spec
    test_candidates = _get_test_spec_paths(root)
    test_path = next((p for p in test_candidates if p.exists()), None)
    if test_path is None:
        return results  # No test spec
    try:
        text = test_path.read_text(encoding="utf-8")
    except OSError:
        return results
    # Count hardware-gated Pending tests
    _HW_GATED_RE = re.compile(
        r"(?i)" + re.escape(attr.replace("_", "[_-]").lower()) + r"[:\s]*true"
    )
    _PENDING_RE = re.compile(r"(?i)\bpending\b")
    gated_count = 0
    pending_gated = 0
    # Split by test header blocks
    for block in re.split(r"(?=^### TEST-)", text, flags=re.MULTILINE):
        if _HW_GATED_RE.search(block):
            gated_count += 1
            if _PENDING_RE.search(block):
                pending_gated += 1
    if gated_count > 0:
        results.append(
            AuditResult(
                name="hardware-gated-tests",
                passed=True,
                message=(
                    f"{gated_count} hardware-gated test(s) found; "
                    f"{pending_gated} Pending (awaiting hardware session — not counted as drift)"
                ),
            )
        )
    return results


def check_secrets_templates(root: Path) -> list[AuditResult]:
    """Check secrets_templates governance (#162).

    For each declared secrets_templates entry:
    - Warn if the secrets file is tracked by git (security issue)
    - Warn if no .example file exists (onboarding issue)
    - Warn if the path isn't in .gitignore
    """
    results: list[AuditResult] = []
    raw = _read_scaffold_raw(root)
    templates: list[dict] = raw.get("secrets_templates", []) or []
    if not templates:
        return results
    # Load .gitignore for checking
    gitignore_content = ""
    gitignore_path = root / ".gitignore"
    if gitignore_path.exists():
        try:
            gitignore_content = gitignore_path.read_text(encoding="utf-8")
        except OSError:
            pass
    for entry in templates:
        if not isinstance(entry, dict):
            continue
        path_rel = entry.get("path", "")
        if not path_rel:
            continue
        secrets_path = root / path_rel
        never_commit = entry.get("never_commit", False)
        # Check 1: is the secrets file tracked by git?
        if secrets_path.exists() and never_commit:
            import subprocess
            try:
                r = subprocess.run(
                    ["git", "-C", str(root), "ls-files", "--error-unmatch", path_rel],
                    capture_output=True, timeout=5,
                )
                if r.returncode == 0:  # file IS tracked
                    results.append(AuditResult(
                        name=f"secrets-tracked:{path_rel}",
                        passed=False,
                        message=(
                            f"SECURITY: {path_rel} is tracked by git but declared "
                            f"never_commit: true. Run `git rm --cached {path_rel}` and "
                            "add it to .gitignore."
                        ),
                    ))
            except Exception:  # noqa: BLE001
                pass
        # Check 2: .example file exists?
        example_path = root / (path_rel + ".example")
        template_path = root / (path_rel + ".template")
        has_example = example_path.exists() or template_path.exists()
        if not has_example:
            results.append(AuditResult(
                name=f"secrets-no-example:{path_rel}",
                passed=False,
                message=(
                    f"No {path_rel}.example found. Create one with placeholder values "
                    f"so new developers know which secrets are required."
                ),
                fixable=True,
            ))
        else:
            results.append(AuditResult(
                name=f"secrets-example:{path_rel}",
                passed=True,
                message=f"Secrets template {path_rel}.example exists",
            ))
        # Check 3: .gitignore covers the secrets file?
        if never_commit and path_rel not in gitignore_content:
            results.append(AuditResult(
                name=f"secrets-gitignore:{path_rel}",
                passed=False,
                message=(
                    f"{path_rel} is declared never_commit but is not in .gitignore. "
                    "Add it to .gitignore to prevent accidental commits."
                ),
                fixable=True,
            ))
    return results


def check_industrial_artifacts(root: Path) -> list[AuditResult]:
    """Check CANopen EDS/XDD and other industrial artifacts (#163).

    If .eds or .xdd files are present but not declared in scaffold.yml
    industrial_artifacts, suggest adding traceability.
    """
    results: list[AuditResult] = []
    raw = _read_scaffold_raw(root)
    declared: dict = raw.get("industrial_artifacts", {}) or {}
    declared_eds = declared.get("canopen_eds", []) or []
    declared_paths = {e.get("path", "") for e in declared_eds if isinstance(e, dict)}

    # Scan for .eds and .xdd files
    skip_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__"}
    found_eds: list[Path] = []
    for ext in (".eds", ".xdd"):
        for f in root.rglob(f"*{ext}"):
            if not any(p in skip_dirs for p in f.parts):
                found_eds.append(f)

    if not found_eds:
        return results  # No industrial artifacts found

    undeclared = [
        f for f in found_eds
        if str(f.relative_to(root)).replace("\\\\", "/") not in declared_paths
    ]

    if undeclared:
        results.append(AuditResult(
            name="industrial-artifacts-undeclared",
            passed=False,
            message=(
                f"{len(undeclared)} CANopen EDS/XDD file(s) found but not declared in "
                f"scaffold.yml industrial_artifacts: "
                + ", ".join(str(f.name) for f in undeclared[:5])
                + ". Add them to industrial_artifacts.canopen_eds for traceability."
            ),
        ))
    else:
        results.append(AuditResult(
            name="industrial-artifacts",
            passed=True,
            message=f"{len(found_eds)} industrial artifact(s) declared in scaffold.yml",
        ))
    return results


def check_derived_artifacts(root: Path) -> list[AuditResult]:
    """Check that code-generated derived artifacts haven't been hand-edited (#126).

    For each entry in scaffold.yml derived_artifacts, checks whether the output
    files have been modified without their source also being modified (using git).
    """
    results: list[AuditResult] = []
    raw = _read_scaffold_raw(root)
    entries: list[dict] = raw.get("derived_artifacts", []) or []
    if not entries:
        return results

    import subprocess

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        source = entry.get("source", "")
        outputs: list[str] = entry.get("outputs", []) or []
        do_not_edit = entry.get("do_not_edit", False)
        if not source or not do_not_edit:
            continue
        # Check if outputs were modified without source being modified (git diff)
        try:
            src_diff = subprocess.run(
                ["git", "-C", str(root), "diff", "HEAD", "--name-only", "--", source],
                capture_output=True, text=True, timeout=5,
            )
            out_diffs = subprocess.run(
                ["git", "-C", str(root), "diff", "HEAD", "--name-only", "--"] + outputs,
                capture_output=True, text=True, timeout=5,
            )
            src_changed = bool(src_diff.stdout.strip())
            outputs_changed = [o for o in outputs if o in (out_diffs.stdout or "")]
            if outputs_changed and not src_changed:
                results.append(AuditResult(
                    name=f"derived-artifact-manual-edit:{source}",
                    passed=False,
                    message=(
                        f"Hand-edit detected in derived artifact(s) generated from {source}: "
                        + ", ".join(outputs_changed[:3])
                        + f". These files are generated by: {entry.get('generator', 'unknown')}"
                    ),
                ))
        except Exception:  # noqa: BLE001
            pass  # git not available or other error — skip silently
    return results


def check_cross_repo_dependencies(root: Path) -> list[AuditResult]:
    """Informational check for cross-repo requirement traceability (#161).

    Lists cross-repo dependencies declared in scaffold.yml and notes which
    REQ prefixes trace to external repositories.
    """
    results: list[AuditResult] = []
    raw = _read_scaffold_raw(root)
    deps: list[dict] = raw.get("cross_repo_dependencies", []) or []
    if not deps:
        return results
    msgs = []
    for dep in deps:
        if not isinstance(dep, dict):
            continue
        repo = dep.get("repo", "?")
        role = dep.get("role", "dependency")
        prefixes = dep.get("req_prefixes", [])
        if prefixes:
            msgs.append(f"{repo} ({role}): handles {', '.join(prefixes)}")       
        else:
            msgs.append(f"{repo} ({role})")
    if msgs:
        results.append(AuditResult(
            name="cross-repo-dependencies",
            passed=True,
            message="Cross-repo dependencies declared: " + "; ".join(msgs),
        ))
    return results


def run_audit(root: Path) -> AuditReport:
    """Run all audit checks and return a report."""
    report = AuditReport()
    report.results.extend(check_governance_files(root))
    report.results.extend(check_req_test_consistency(root))
    report.results.extend(check_ledger_health(root))
    report.results.extend(check_context_size(root))
    report.results.extend(check_tool_configuration(root))
    report.results.extend(check_type_mismatch(root))
    report.results.extend(check_trace_chain_integrity(root))
    report.results.extend(check_phase_readiness(root))
    report.results.extend(check_supplementary_rules(root))
    report.results.extend(check_hardware_gated_tests(root))
    report.results.extend(check_secrets_templates(root))
    report.results.extend(check_industrial_artifacts(root))
    report.results.extend(check_derived_artifacts(root))
    report.results.extend(check_cross_repo_dependencies(root))
    return report


def run_auto_fix(root: Path, report: AuditReport) -> list[str]:
    """Attempt to auto-fix issues found by audit.

    Returns list of human-readable fix descriptions.
    """
    fixed: list[str] = []

    for result in report.results:
        if result.passed:
            continue

        # Fix missing required files with minimal stubs
        if result.name == "file-exists:AGENTS.md":
            path = root / "AGENTS.md"
            path.write_text(
                "# AGENTS.md\n\nGovernance hub. Populate with project details.\n",
                encoding="utf-8",
            )
            fixed.append("Created stub AGENTS.md")

        elif result.name == "file-exists:LEDGER.md":
            path = root / "LEDGER.md"
            path.write_text("# Ledger\n\nNo entries yet.\n", encoding="utf-8")
            fixed.append("Created stub LEDGER.md")

        elif result.name.startswith("file-exists:docs/governance/"):
            rel = result.name.split(":", 1)[1]
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            fname = path.stem.replace("-", " ").title()
            path.write_text(f"# {fname}\n\nPopulate per spec.\n", encoding="utf-8")
            fixed.append(f"Created stub {rel}")

        # Compress oversized ledger
        elif result.name == "ledger-size" and result.fixable:
            from specsmith.compressor import run_compress

            compress_result = run_compress(root)
            if compress_result.archived_entries > 0:
                fixed.append(compress_result.message)

        # Generate missing CI config from tool registry
        elif result.name == "tool-ci-config" and not result.passed:
            scaffold_path = root / "scaffold.yml"
            if scaffold_path.exists():
                import yaml

                from specsmith.config import ProjectConfig

                try:
                    with open(scaffold_path) as f:
                        raw = yaml.safe_load(f)
                    config = ProjectConfig(**raw)
                    if config.vcs_platform:
                        from specsmith.vcs import get_platform

                        platform = get_platform(config.vcs_platform)
                        platform.generate_all(config, root)
                        fixed.append(
                            f"Generated {config.vcs_platform} CI config "
                            f"with tools for {config.type}"
                        )
                except Exception:  # noqa: BLE001
                    pass  # Best-effort

        # Fix missing recommended files
        elif result.name == "recommended:docs/ARCHITECTURE.md" and not result.passed:
            from specsmith.architect import generate_architecture

            try:
                generate_architecture(root)
                fixed.append("Generated docs/ARCHITECTURE.md from project scan")
            except Exception:  # noqa: BLE001
                # Fallback stub
                path = root / "docs" / "ARCHITECTURE.md"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    f"# Architecture — {root.name}\n\n[Run `specsmith architect` to populate]\n",
                    encoding="utf-8",
                )
                fixed.append("Created stub docs/ARCHITECTURE.md")

        elif result.name == "recommended:docs/REQUIREMENTS.md" and not result.passed:
            path = root / "docs" / "REQUIREMENTS.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "# Requirements\n\nNo requirements defined yet.\n\n"
                "## REQ-CORE-001\n- **Component**: core\n"
                "- **Status**: Draft\n- **Description**: [Define]\n",
                encoding="utf-8",
            )
            fixed.append("Created stub docs/REQUIREMENTS.md")

        elif result.name == "recommended:docs/TESTS.md" and not result.passed:
            path = root / "docs" / "TESTS.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "# Test Specification\n\nNo tests defined yet.\n",
                encoding="utf-8",
            )
            fixed.append("Created stub docs/TESTS.md")

    return fixed
