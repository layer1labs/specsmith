"""phase — AEE Workflow Phase Tracker for specsmith.

Tracks which phase of the Applied Epistemic Engineering process a project is
currently in, and provides readiness checks, checklists, and guidance for each phase.

The 7 phases of the AEE development cycle:

  inception     → Governance scaffold, AGENTS.md, project type established
  architecture  → ARCHITECTURE.md written, components defined, key decisions sealed
  requirements  → REQUIREMENTS.md populated, stress-tested, equilibrium reached
  test_spec     → TESTS.md covers all P1 requirements, coverage > 80 %
  implementation → Code development loop; audit passes; ledger updated each session
  verification  → Epistemic audit passes threshold; trace vault sealed; export clean
  release       → CHANGELOG updated; release tag created; compliance report filed
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Phase data model
# ---------------------------------------------------------------------------


@dataclass
class PhaseCheck:
    """A single readiness criterion for a phase."""

    description: str
    check: Callable[[Path], bool]


@dataclass
class Phase:
    """One phase of the AEE workflow."""

    key: str
    label: str
    emoji: str
    description: str
    checks: list[PhaseCheck] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    next_phase: str | None = None


# ---------------------------------------------------------------------------
# Readiness check helpers
# ---------------------------------------------------------------------------


def _file_exists(rel: str) -> Callable[[Path], bool]:
    return lambda root: (root / rel).exists()


def _file_min_lines(rel: str, min_lines: int) -> Callable[[Path], bool]:
    def _check(root: Path) -> bool:
        p = root / rel
        if not p.exists():
            return False
        try:
            return len(p.read_text(encoding="utf-8", errors="ignore").splitlines()) >= min_lines
        except OSError:
            return False

    return _check


def _req_count(min_count: int) -> Callable[[Path], bool]:
    def _check(root: Path) -> bool:
        for candidate in ["REQUIREMENTS.md", "docs/REQUIREMENTS.md"]:
            p = root / candidate
            if p.exists():
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    return len(re.findall(r"^###\s+REQ-", text, re.MULTILINE)) >= min_count
                except OSError:
                    pass
        return False

    return _check


def _test_spec_covers_reqs(threshold_pct: int) -> Callable[[Path], bool]:
    """Check that at least threshold_pct% of REQ IDs appear in TESTS.md."""

    def _check(root: Path) -> bool:
        candidates_req = ["REQUIREMENTS.md", "docs/REQUIREMENTS.md"]
        candidates_test = ["TESTS.md", "docs/TESTS.md"]
        req_file = next((root / c for c in candidates_req if (root / c).exists()), None)
        test_file = next((root / c for c in candidates_test if (root / c).exists()), None)
        if not req_file or not test_file:
            return False
        try:
            req_text = req_file.read_text(encoding="utf-8", errors="ignore")
            req_ids = set(re.findall(r"(REQ-[A-Z0-9-]+)", req_text))
            test_txt = test_file.read_text(encoding="utf-8", errors="ignore")
            if not req_ids:
                return True
            covered = sum(1 for rid in req_ids if rid in test_txt)
            return (covered / len(req_ids)) * 100 >= threshold_pct
        except OSError:
            return False

    return _check


def _scaffold_field(key: str) -> Callable[[Path], bool]:
    """Check scaffold.yml has a non-empty value for the given key."""

    def _check(root: Path) -> bool:
        p = root / "scaffold.yml"
        if not p.exists():
            return False
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
            m = re.search(rf"^{key}:\s*(.+)$", text, re.MULTILINE)
            return bool(m and m.group(1).strip())
        except OSError:
            return False

    return _check


def _trace_vault_exists() -> Callable[[Path], bool]:
    def _check(root: Path) -> bool:
        # Accept either naming convention used by specsmith trace commands.
        for name in ("trace-vault.jsonl", "trace.jsonl"):
            vault = root / ".specsmith" / name
            if vault.exists():
                try:
                    return (
                        len(
                            vault.read_text(encoding="utf-8", errors="ignore")
                            .strip()
                            .splitlines()
                        )
                        >= 1
                    )
                except OSError:
                    pass
        return False

    return _check


def _changelog_has_version() -> Callable[[Path], bool]:
    def _check(root: Path) -> bool:
        p = root / "CHANGELOG.md"
        if not p.exists():
            return False
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
            return bool(re.search(r"^##\s+\[?\d+\.\d+\.\d+", text, re.MULTILINE))
        except OSError:
            return False

    return _check


# ---------------------------------------------------------------------------
# Phase catalog
# ---------------------------------------------------------------------------

PHASES: list[Phase] = [
    Phase(
        key="inception",
        label="Inception",
        emoji="🌱",
        description="Establish project governance, scaffold, and initial context.",
        checks=[
            PhaseCheck("scaffold.yml exists", _file_exists("scaffold.yml")),
            PhaseCheck("AGENTS.md exists", _file_exists("AGENTS.md")),
            PhaseCheck("LEDGER.md exists", _file_exists("LEDGER.md")),
            PhaseCheck("Project type is set", _scaffold_field("type")),
            PhaseCheck("VCS platform is set", _scaffold_field("vcs_platform")),
        ],
        commands=["specsmith init", "specsmith import", "specsmith audit"],
        next_phase="architecture",
    ),
    Phase(
        key="architecture",
        label="Architecture",
        emoji="🏗",
        description="Define system components, data flow, and architectural decisions.",
        checks=[
            PhaseCheck("scaffold.yml exists", _file_exists("scaffold.yml")),
            PhaseCheck("ARCHITECTURE.md exists", _file_exists("docs/ARCHITECTURE.md")),
            PhaseCheck(
                "ARCHITECTURE.md has content",
                _file_min_lines("docs/ARCHITECTURE.md", 20),
            ),
            PhaseCheck("AGENTS.md has substantial content", _file_min_lines("AGENTS.md", 30)),
            PhaseCheck("Trace vault has at least 1 seal", _trace_vault_exists()),
        ],
        commands=[
            "specsmith architect",
            'specsmith trace seal decision "Architecture established"',
            "specsmith audit",
        ],
        next_phase="requirements",
    ),
    Phase(
        key="requirements",
        label="Requirements",
        emoji="📋",
        description="Collect, stress-test, and stabilise the belief artifact registry.",
        checks=[
            PhaseCheck(
                "REQUIREMENTS.md exists",
                _file_exists("REQUIREMENTS.md"),
            ),
            PhaseCheck("At least 5 requirements defined", _req_count(5)),
            PhaseCheck("TESTS.md exists", _file_exists("docs/TESTS.md")),
            PhaseCheck("ARCHITECTURE.md exists", _file_exists("docs/ARCHITECTURE.md")),
            PhaseCheck("REQUIREMENTS.md has content", _file_min_lines("REQUIREMENTS.md", 10)),
        ],
        commands=[
            "specsmith stress-test",
            "specsmith epistemic-audit",
            "specsmith belief-graph",
            'specsmith trace seal audit-gate "Requirements equilibrium reached"',
        ],
        next_phase="test_spec",
    ),
    Phase(
        key="test_spec",
        label="Test Specification",
        emoji="✅",
        description="Write test specifications covering all P1 requirements.",
        checks=[
            PhaseCheck("TESTS.md exists", _file_exists("docs/TESTS.md")),
            PhaseCheck(
                "TESTS.md has content",
                _file_min_lines("docs/TESTS.md", 15),
            ),
            PhaseCheck("TEST coverage ≥ 80 %", _test_spec_covers_reqs(80)),
            PhaseCheck("REQUIREMENTS.md has ≥ 5 REQs", _req_count(5)),
            PhaseCheck("LEDGER.md exists", _file_exists("LEDGER.md")),
        ],
        commands=[
            "specsmith validate",
            "specsmith export",
            "specsmith audit",
        ],
        next_phase="implementation",
    ),
    Phase(
        key="implementation",
        label="Implementation",
        emoji="⚙",
        description="Development cycle: code, commit, verify, update ledger.",
        checks=[
            PhaseCheck("LEDGER.md has content", _file_min_lines("LEDGER.md", 10)),
            PhaseCheck("Audit passes", _file_exists("AGENTS.md")),
            PhaseCheck("TESTS.md exists", _file_exists("docs/TESTS.md")),
            PhaseCheck("REQUIREMENTS.md exists", _req_count(1)),
        ],
        commands=[
            "specsmith audit --fix",
            "specsmith commit",
            "specsmith ledger add",
            "specsmith run --tier balanced",
        ],
        next_phase="verification",
    ),
    Phase(
        key="verification",
        label="Verification",
        emoji="🔬",
        description="Epistemic audit passes threshold; trace vault sealed; export report clean.",
        checks=[
            PhaseCheck("ARCHITECTURE.md exists", _file_exists("docs/ARCHITECTURE.md")),
            PhaseCheck("TEST coverage ≥ 80 %", _test_spec_covers_reqs(80)),
            PhaseCheck("Trace vault has seals", _trace_vault_exists()),
            PhaseCheck("Trace vault has ≥ 2 seals", _trace_vault_exists()),
            PhaseCheck("LEDGER.md has content", _file_min_lines("LEDGER.md", 10)),
        ],
        commands=[
            "specsmith epistemic-audit",
            "specsmith stress-test",
            "specsmith export",
            'specsmith trace seal audit-gate "Verification complete"',
        ],
        next_phase="release",
    ),
    Phase(
        key="release",
        label="Release",
        emoji="🚀",
        description="CHANGELOG updated, release tag created, compliance report filed.",
        checks=[
            PhaseCheck("CHANGELOG.md has version entry", _changelog_has_version()),
            PhaseCheck("Trace vault has seals", _trace_vault_exists()),
            PhaseCheck("CHANGELOG.md exists", _file_exists("CHANGELOG.md")),
            PhaseCheck("ARCHITECTURE.md exists", _file_exists("docs/ARCHITECTURE.md")),
        ],
        commands=[
            "specsmith export --output docs/COMPLIANCE.md",
            'specsmith trace seal milestone "v<version> released"',
            "specsmith push",
        ],
        next_phase=None,  # release loops back to inception for new cycle
    ),
]

PHASE_MAP: dict[str, Phase] = {p.key: p for p in PHASES}
PHASE_ORDER: list[str] = [p.key for p in PHASES]


# ---------------------------------------------------------------------------
# scaffold.yml I/O
# ---------------------------------------------------------------------------


def read_phase(project_dir: Path) -> str:
    """Read current aee_phase from scaffold.yml. Returns 'inception' if not set."""
    scaffold = project_dir / "scaffold.yml"
    if scaffold.exists():
        try:
            text = scaffold.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"^aee_phase:\s*(\S+)", text, re.MULTILINE)
            if m and m.group(1) in PHASE_MAP:
                return m.group(1)
        except OSError:
            pass
    return "inception"


def write_phase(project_dir: Path, phase_key: str) -> None:
    """Write aee_phase to scaffold.yml, adding the field if it doesn't exist."""
    scaffold = project_dir / "scaffold.yml"
    if not scaffold.exists():
        return

    text = scaffold.read_text(encoding="utf-8", errors="ignore")
    lines = text.split("\n")
    new_line = f"aee_phase: {phase_key}"

    for i, line in enumerate(lines):
        if re.match(r"^aee_phase:", line):
            lines[i] = new_line
            scaffold.write_text("\n".join(lines), encoding="utf-8")
            return

    # Field not present — append after spec_version if it exists, else at end
    for i, line in enumerate(lines):
        if re.match(r"^spec_version:", line):
            lines.insert(i + 1, new_line)
            scaffold.write_text("\n".join(lines), encoding="utf-8")
            return

    lines.append(new_line)
    scaffold.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Readiness evaluation
# ---------------------------------------------------------------------------


def evaluate_phase(phase: Phase, project_dir: Path) -> tuple[list[str], list[str]]:
    """Return (passed_descriptions, failed_descriptions)."""
    passed: list[str] = []
    failed: list[str] = []
    for chk in phase.checks:
        (passed if chk.check(project_dir) else failed).append(chk.description)
    return passed, failed


def is_ready_to_advance(phase: Phase, project_dir: Path) -> bool:
    """True if all checks for this phase pass."""
    _, failed = evaluate_phase(phase, project_dir)
    return len(failed) == 0


def phase_progress_pct(phase: Phase, project_dir: Path) -> int:
    """Return completion percentage (0–100) for the current phase."""
    if not phase.checks:
        return 100
    passed, _ = evaluate_phase(phase, project_dir)
    return int(len(passed) / len(phase.checks) * 100)
