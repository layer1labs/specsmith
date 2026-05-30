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
        # Canonical: docs/REQUIREMENTS.md first; legacy root fallback
        for candidate in ["docs/REQUIREMENTS.md", "REQUIREMENTS.md"]:
            p = root / candidate
            if p.exists():
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    # Support H2/H3 headings (## REQ-NNN, ### REQ-NNN, ## REQ-BE-001) (REQ-359)
                    count = len(re.findall(r"^#{2,3}\s+REQ-", text, re.MULTILINE))
                    if count == 0:
                        count = len(re.findall(r"- \*\*ID:\*\* REQ-", text))
                    if count == 0:
                        count = len(re.findall(r"^## \d+\.", text, re.MULTILINE))
                    return count >= min_count
                except OSError:
                    pass
        return False

    return _check


def _test_spec_covers_reqs(threshold_pct: int) -> Callable[[Path], bool]:
    """Check that at least threshold_pct% of REQ IDs appear in TESTS.md."""

    def _check(root: Path) -> bool:
        # Canonical locations first, legacy root fallback
        candidates_req = ["docs/REQUIREMENTS.md", "REQUIREMENTS.md"]
        candidates_test = ["docs/TESTS.md", "TESTS.md"]
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
    """Check docs/SPECSMITH.yml (or legacy scaffold.yml) has a non-empty value for key."""

    def _check(root: Path) -> bool:
        from specsmith.paths import find_scaffold

        p = find_scaffold(root)
        if not p:
            return False
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
            m = re.search(rf"^{key}:\s*(.+)$", text, re.MULTILINE)
            return bool(m and m.group(1).strip())
        except OSError:
            return False

    return _check


def _trace_vault_exists() -> Callable[[Path], bool]:
    """Return True if the trace vault has at least 1 seal."""

    def _check(root: Path) -> bool:
        for name in ("trace-vault.jsonl", "trace.jsonl"):
            vault = root / ".specsmith" / name
            if vault.exists():
                try:
                    lines = vault.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
                    return len(lines) >= 1
                except OSError:
                    pass
        return False

    return _check


def _trace_vault_min_seals(min_count: int) -> Callable[[Path], bool]:
    """Return True if the trace vault has at least `min_count` seals."""

    def _check(root: Path) -> bool:
        for name in ("trace-vault.jsonl", "trace.jsonl"):
            vault = root / ".specsmith" / name
            if vault.exists():
                try:
                    lines = [
                        ln
                        for ln in vault.read_text(encoding="utf-8", errors="ignore").splitlines()
                        if ln.strip()
                    ]
                    return len(lines) >= min_count
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
            PhaseCheck(
                "docs/SPECSMITH.yml exists",
                lambda root: bool(
                    __import__("specsmith.paths", fromlist=["find_scaffold"]).find_scaffold(root)
                ),
            ),
            PhaseCheck("AGENTS.md exists", _file_exists("AGENTS.md")),
            PhaseCheck(
                "docs/LEDGER.md exists",
                lambda root: bool(
                    __import__("specsmith.paths", fromlist=["find_ledger"]).find_ledger(root)
                ),
            ),
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
            PhaseCheck(
                "docs/SPECSMITH.yml exists",
                lambda root: bool(
                    __import__("specsmith.paths", fromlist=["find_scaffold"]).find_scaffold(root)
                ),
            ),
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
                "docs/REQUIREMENTS.md exists",
                lambda root: bool(
                    __import__("specsmith.paths", fromlist=["find_requirements"]).find_requirements(
                        root
                    )
                ),
            ),
            PhaseCheck("At least 5 requirements defined", _req_count(5)),
            PhaseCheck("docs/TESTS.md exists", _file_exists("docs/TESTS.md")),
            PhaseCheck("docs/ARCHITECTURE.md exists", _file_exists("docs/ARCHITECTURE.md")),
            PhaseCheck(
                "docs/REQUIREMENTS.md has content",
                lambda root: (
                    (
                        p := __import__(
                            "specsmith.paths", fromlist=["find_requirements"]
                        ).find_requirements(root)
                    )
                    is not None
                    and p.exists()
                    and len(p.read_text(encoding="utf-8", errors="ignore").splitlines()) >= 10
                ),
            ),
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
            PhaseCheck("docs/TESTS.md exists", _file_exists("docs/TESTS.md")),
            PhaseCheck(
                "docs/TESTS.md has content",
                _file_min_lines("docs/TESTS.md", 15),
            ),
            PhaseCheck("TEST coverage \u2265 80 %", _test_spec_covers_reqs(80)),
            PhaseCheck("docs/REQUIREMENTS.md has \u2265 5 REQs", _req_count(5)),
            PhaseCheck(
                "docs/LEDGER.md exists",
                lambda root: bool(
                    __import__("specsmith.paths", fromlist=["find_ledger"]).find_ledger(root)
                ),
            ),
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
            PhaseCheck(
                "docs/LEDGER.md has content",
                lambda root: (
                    (p := __import__("specsmith.paths", fromlist=["find_ledger"]).find_ledger(root))
                    is not None
                    and p.exists()
                    and len(p.read_text(encoding="utf-8", errors="ignore").splitlines()) >= 10
                ),
            ),
            PhaseCheck("Audit passes", _file_exists("AGENTS.md")),
            PhaseCheck("docs/TESTS.md exists", _file_exists("docs/TESTS.md")),
            # #127: use a permissive file-exists check, not _req_count, so Draft-only
            # projects aren't blocked by the misleading "REQUIREMENTS.md exists" message.
            # The actual count check is advisory and belongs in check_req_test_consistency.
            PhaseCheck(
                "docs/REQUIREMENTS.md has content",
                lambda root: any(
                    (root / c).exists()
                    and len((root / c).read_text(encoding="utf-8", errors="ignore").strip()) > 0
                    for c in ["docs/REQUIREMENTS.md", "REQUIREMENTS.md"]
                ),
            ),
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
            PhaseCheck("TEST coverage \u2265 80 %", _test_spec_covers_reqs(80)),
            PhaseCheck("Trace vault has seals", _trace_vault_exists()),
            PhaseCheck("Trace vault has \u2265 2 seals", _trace_vault_min_seals(2)),
            PhaseCheck(
                "docs/LEDGER.md has content",
                lambda root: (
                    (p := __import__("specsmith.paths", fromlist=["find_ledger"]).find_ledger(root))
                    is not None
                    and p.exists()
                    and len(p.read_text(encoding="utf-8", errors="ignore").splitlines()) >= 10
                ),
            ),
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
# IP Prosecution phases  (patent-prosecution project type — issue #177)
# ---------------------------------------------------------------------------

PROSECUTION_PHASES: list[Phase] = [
    Phase(
        key="provisional-draft",
        label="Provisional Draft",
        emoji="\U0001f4dd",
        description="Invention disclosure and provisional specification being written.",
        checks=[
            PhaseCheck("AGENTS.md exists", _file_exists("AGENTS.md")),
            PhaseCheck("docs/ip/specs/ exists", _file_exists("docs/ip/specs")),
            PhaseCheck("scaffold.yml has ip_families field", _scaffold_field("ip_families")),
        ],
        commands=["specsmith audit", 'specsmith ledger add "Provisional draft in progress"'],
        next_phase="filing",
    ),
    Phase(
        key="filing",
        label="Filing",
        emoji="\U0001f4e8",
        description="Provisional application prepared and submitted to USPTO.",
        checks=[
            PhaseCheck("docs/ip/filings/ exists", _file_exists("docs/ip/filings")),
            PhaseCheck(
                "scaffold.yml has provisional_app_number",
                _scaffold_field("provisional_app_number"),
            ),
            PhaseCheck(
                "scaffold.yml has provisional_filed_date",
                _scaffold_field("provisional_filed_date"),
            ),
        ],
        commands=[
            'specsmith ledger add "Provisional filed at USPTO — App. <number>"',
            'specsmith trace seal milestone "Provisional filed"',
        ],
        next_phase="prior-art-search",
    ),
    Phase(
        key="prior-art-search",
        label="Prior-Art Search",
        emoji="\U0001f50e",
        description="Systematic prior-art protocol executed across all claim themes.",
        checks=[
            PhaseCheck(
                "scaffold.yml has provisional_app_number",
                _scaffold_field("provisional_app_number"),
            ),
            PhaseCheck(
                "LEDGER.md has PAR run entry",
                lambda root: any(
                    "PAR-" in (root / c).read_text(encoding="utf-8", errors="ignore")
                    for c in ["docs/LEDGER.md", "LEDGER.md"]
                    if (root / c).exists()
                ),
            ),
            PhaseCheck("docs/ip/prosecution/ exists", _file_exists("docs/ip/prosecution")),
        ],
        commands=[
            "prior-art protocol: start Themes A-H (USPTO MCP)",
            'specsmith ledger add "PAR-YYYY-MM-DD-001 complete — Themes A-H"',
        ],
        next_phase="claim-hardening",
    ),
    Phase(
        key="claim-hardening",
        label="Claim Hardening",
        emoji="\U0001f527",
        description="Claim language refined based on prior-art findings; §101/§102/§103 addressed.",
        checks=[
            PhaseCheck(
                "LEDGER.md has PAR run entry",
                lambda root: any(
                    "PAR-" in (root / c).read_text(encoding="utf-8", errors="ignore")
                    for c in ["docs/LEDGER.md", "LEDGER.md"]
                    if (root / c).exists()
                ),
            ),
            PhaseCheck("docs/ip/specs/ has content", _file_min_lines("docs/ip/specs", 1)),
            PhaseCheck("docs/ip/strategy/ exists", _file_exists("docs/ip/strategy")),
        ],
        commands=[
            'specsmith ledger add "Claim hardening session — Theme <X> hardened"',
            'specsmith trace seal decision "Claim strategy approved by counsel"',
        ],
        next_phase="non-provisional-draft",
    ),
    Phase(
        key="non-provisional-draft",
        label="Non-Provisional Draft",
        emoji="\U0001f4c4",
        description="Anchor non-provisional and continuation drafts being prepared by counsel.",
        checks=[
            PhaseCheck(
                "scaffold.yml has non_provisional_deadline",
                _scaffold_field("non_provisional_deadline"),
            ),
            PhaseCheck("docs/ip/filings/ exists", _file_exists("docs/ip/filings")),
            PhaseCheck("docs/ip/strategy/ exists", _file_exists("docs/ip/strategy")),
        ],
        commands=[
            'specsmith ledger add "Non-provisional draft v<N> submitted to counsel"',
        ],
        next_phase="examination",
    ),
    Phase(
        key="examination",
        label="Examination",
        emoji="\U0001f50d",
        description="Application under examination at USPTO. Responding to office actions.",
        checks=[
            PhaseCheck("docs/ip/filings/ exists", _file_exists("docs/ip/filings")),
            PhaseCheck(
                "scaffold.yml has provisional_app_number",
                _scaffold_field("provisional_app_number"),
            ),
        ],
        commands=[
            'specsmith ledger add "OA response filed — <date>"',
            'specsmith trace seal milestone "Office action response submitted"',
        ],
        next_phase="allowance",
    ),
    Phase(
        key="allowance",
        label="Allowance",
        emoji="\u2705",
        description="Patent allowed or continuation strategy in execution.",
        checks=[
            PhaseCheck("docs/ip/filings/ exists", _file_exists("docs/ip/filings")),
            PhaseCheck("Trace vault has seals", _trace_vault_exists()),
        ],
        commands=[
            'specsmith ledger add "NOA received — patent allowed"',
            'specsmith trace seal milestone "Patent allowed"',
        ],
        next_phase=None,
    ),
]

# Merge prosecution phases into PHASE_MAP so read_phase() can find them.
# Prosecution phases are intentionally NOT in PHASE_ORDER (the AEE sequence).
PROSECUTION_PHASE_MAP: dict[str, Phase] = {p.key: p for p in PROSECUTION_PHASES}
PHASE_MAP.update(PROSECUTION_PHASE_MAP)


# ---------------------------------------------------------------------------
# scaffold.yml I/O
# ---------------------------------------------------------------------------


def read_phase(project_dir: Path) -> str:
    """Read current aee_phase from docs/SPECSMITH.yml (or legacy scaffold.yml).

    Returns 'inception' if not set or scaffold not found.
    """
    from specsmith.paths import find_scaffold

    scaffold = find_scaffold(project_dir)
    if scaffold and scaffold.exists():
        try:
            text = scaffold.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"^aee_phase:\s*(\S+)", text, re.MULTILINE)
            if m and m.group(1) in PHASE_MAP:
                return m.group(1)
        except OSError:
            pass
    return "inception"


def write_phase(project_dir: Path, phase_key: str) -> None:
    """Write aee_phase to docs/SPECSMITH.yml (or legacy scaffold.yml)."""
    from specsmith.paths import find_scaffold, scaffold_path

    scaffold = find_scaffold(project_dir) or scaffold_path(project_dir)
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
