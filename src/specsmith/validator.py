# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Validator — governance file consistency checks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationResult:
    """Result of a single validation check."""

    name: str
    passed: bool
    message: str


@dataclass
class ValidationReport:
    """Aggregate validation report."""

    results: list[ValidationResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def valid(self) -> bool:
        return self.failed == 0


_REQ_PATTERN = re.compile(r"\b(REQ-[A-Z]+-\d+)\b")

# Infinite-loop patterns (Python, PowerShell, shell)
_INFINITE_LOOP_PATTERNS = (
    re.compile(r"while\s+True\s*:"),  # Python
    re.compile(r"while\s*\(\s*\$true\s*\)", re.IGNORECASE),  # PowerShell
    re.compile(r"while\s+true\s*[;{]", re.IGNORECASE),  # bash/sh
    re.compile(r"while\s+:\s*[;{\n]"),  # bash/sh `while :`
    re.compile(r"for\s*\(\s*;;\s*\)"),  # C-style for(;;)
)

# Deadline/timeout guard keywords — presence anywhere in the file suppresses the warning
_DEADLINE_GUARD_PATTERNS = (
    re.compile(r"deadline", re.IGNORECASE),
    re.compile(r"timeout", re.IGNORECASE),
    re.compile(r"max_iter", re.IGNORECASE),
    re.compile(r"max_attempt", re.IGNORECASE),
    re.compile(r"time\.monotonic\("),
    re.compile(r"time\.time\("),
    re.compile(r"Get-Date", re.IGNORECASE),
    re.compile(r"\$SECONDS"),
)

# Script file extensions to scan (exclude general source dirs to avoid false positives)
_SCRIPT_EXTENSIONS = {".sh", ".cmd", ".ps1", ".bash"}

# Bare-sleep patterns: standalone timing delays that block indefinitely (H23)
# Applies to scripts only — NOT to general source code.
_BARE_SLEEP_PATTERNS = (
    re.compile(r"^\s*sleep\s+\d", re.MULTILINE | re.IGNORECASE),  # bash: sleep N
    re.compile(r"^\s*Start-Sleep\b", re.MULTILINE | re.IGNORECASE),  # PowerShell
)

# Loop / retry constructs that justify a sleep — if any are present the sleep
# is inside a polling loop and should not be flagged.
_SLEEP_LOOP_CONTEXT = (
    re.compile(r"\bfor\b"),
    re.compile(r"\bwhile\b"),
    re.compile(r"\buntil\b"),
    re.compile(r"max_retries", re.IGNORECASE),
    re.compile(r"max_attempts", re.IGNORECASE),
    re.compile(r"\bretry\b", re.IGNORECASE),
    re.compile(r"\bseq\s+\d"),  # bash `for i in $(seq N)`
)


def _check_scaffold_yml(root: Path) -> list[ValidationResult]:
    """Check that the scaffold config exists and is valid YAML."""
    from specsmith.config import _normalize_scaffold_raw
    from specsmith.paths import find_scaffold

    results: list[ValidationResult] = []
    scaffold_path = find_scaffold(root)

    if not scaffold_path or not scaffold_path.exists():
        results.append(
            ValidationResult(
                name="scaffold-yml",
                passed=True,
                message="No scaffold config found (project may not have been created by specsmith)",
            ),
        )
        return results

    cfg_name = scaffold_path.name
    try:
        import yaml

        with open(scaffold_path) as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            results.append(
                ValidationResult(
                    name="scaffold-yml",
                    passed=False,
                    message=f"{cfg_name} is not a valid YAML mapping",
                ),
            )
        else:
            data = _normalize_scaffold_raw(data)
            if "name" not in data or "type" not in data:
                results.append(
                    ValidationResult(
                        name="scaffold-yml",
                        passed=False,
                        message=f"{cfg_name} missing required fields: name, type",
                    ),
                )
            else:
                results.append(
                    ValidationResult(
                        name="scaffold-yml",
                        passed=True,
                        message=f"{cfg_name} valid: project={data['name']}, type={data['type']}",
                    ),
                )
    except Exception as e:  # noqa: BLE001
        results.append(
            ValidationResult(
                name="scaffold-yml",
                passed=False,
                message=f"{cfg_name} parse error: {e}",
            ),
        )

    return results


def _check_agents_md_refs(root: Path) -> list[ValidationResult]:
    """Check that AGENTS.md references governance files that exist."""
    results: list[ValidationResult] = []
    agents_path = root / "AGENTS.md"

    if not agents_path.exists():
        return results

    text = agents_path.read_text(encoding="utf-8")

    # Look for markdown links to local files
    link_pattern = re.compile(r"\[.*?\]\((?!https?://)(.*?)\)")
    for match in link_pattern.finditer(text):
        ref = match.group(1).split("#")[0].strip()
        if not ref:
            continue
        ref_path = root / ref
        if not ref_path.exists():
            results.append(
                ValidationResult(
                    name=f"agents-ref:{ref}",
                    passed=False,
                    message=f"AGENTS.md references {ref} but file does not exist",
                ),
            )

    if not results:
        results.append(
            ValidationResult(
                name="agents-refs",
                passed=True,
                message="All AGENTS.md local references resolve",
            ),
        )

    return results


def _check_req_ids_unique(root: Path) -> list[ValidationResult]:
    """Check that requirement IDs are unique within REQUIREMENTS.md.

    Uses only the canonical **ID:** field to count each REQ once (#171).
    The generated REQUIREMENTS.md repeats each ID in both the section heading
    and the '**ID:** REQ-XXX' field — a raw findall would double-count every ID.
    """
    results: list[ValidationResult] = []
    req_path = root / "docs" / "REQUIREMENTS.md"

    if not req_path.exists():
        return results

    text = req_path.read_text(encoding="utf-8")
    # Match only canonical ID declarations, not heading or cross-references (#171).
    # Pattern matches '- **ID:** REQ-XXX' or '**ID:** REQ-XXX' lines.
    _ID_FIELD = re.compile(r"\*\*ID:\*\*\s*(REQ-(?:[A-Z]+-)*\d+)")
    id_field_matches = _ID_FIELD.findall(text)
    # Fall back to full scan if the markdown has no **ID:** fields (legacy format).
    req_ids = id_field_matches or _REQ_PATTERN.findall(text)

    seen: dict[str, int] = {}
    for rid in req_ids:
        seen[rid] = seen.get(rid, 0) + 1

    duplicates = {k: v for k, v in seen.items() if v > 1}
    if duplicates:
        dup_str = ", ".join(f"{k}(×{v})" for k, v in sorted(duplicates.items()))
        results.append(
            ValidationResult(
                name="req-unique",
                passed=False,
                message=f"Duplicate requirement IDs: {dup_str}",
            ),
        )
    else:
        results.append(
            ValidationResult(
                name="req-unique",
                passed=True,
                message=f"{len(seen)} unique requirement IDs found",
            ),
        )

    return results


def _check_architecture_reqs(root: Path) -> list[ValidationResult]:
    """Check that architecture.md references requirements."""
    results: list[ValidationResult] = []

    # Accept both ARCHITECTURE.md and architecture.md
    arch_path = next(
        (
            root / "docs" / f
            for f in ("ARCHITECTURE.md", "architecture.md")
            if (root / "docs" / f).exists()
        ),
        None,
    )
    req_path = root / "docs" / "REQUIREMENTS.md"

    if arch_path is None or not req_path.exists():
        return results

    req_text = req_path.read_text(encoding="utf-8")
    arch_text = arch_path.read_text(encoding="utf-8")

    req_ids = set(_REQ_PATTERN.findall(req_text))
    arch_refs = set(_REQ_PATTERN.findall(arch_text))

    # If all requirements are Draft stubs (e.g. auto-generated by import),
    # don't require architecture to reference them yet — they haven't been
    # accepted or enriched. The check is only meaningful for accepted requirements.
    all_draft = (
        bool(req_ids)
        and bool(re.search(r"\*\*Status\*\*:\s*[Dd]raft", req_text))
        and not re.search(r"\*\*Status\*\*:\s*(?!Draft|draft)[A-Za-z]", req_text)
    )

    if req_ids and not arch_refs and not all_draft:
        results.append(
            ValidationResult(
                name="arch-req-refs",
                passed=False,
                message=(
                    f"architecture.md references no REQ IDs, but REQUIREMENTS.md has {len(req_ids)}"
                ),
            ),
        )
    else:
        msg = (
            f"architecture.md references {len(arch_refs)} REQ IDs"
            if arch_refs
            else f"REQs are all Draft \u2014 architecture linkage not yet required ({len(req_ids)} REQs)"  # noqa: E501
        )
        results.append(
            ValidationResult(
                name="arch-req-refs",
                passed=True,
                message=msg,
            ),
        )

    return results


def _check_blocking_loops(root: Path) -> list[ValidationResult]:
    """Scan script files for unbounded loops without a deadline/timeout guard.

    Checks .sh, .cmd, .ps1, .bash files under scripts/ and the project root.
    A file is flagged only when it contains an infinite-loop pattern AND lacks
    any recognised deadline/timeout guard anywhere in the file body.
    This is a heuristic check; results are warnings rather than hard failures.
    """
    results: list[ValidationResult] = []

    # Collect script files: root-level + scripts/ subdirectory
    candidates: list[Path] = []
    for path in root.iterdir():
        if path.is_file() and path.suffix.lower() in _SCRIPT_EXTENSIONS:
            candidates.append(path)
    scripts_dir = root / "scripts"
    if scripts_dir.is_dir():
        for path in scripts_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in _SCRIPT_EXTENSIONS:
                candidates.append(path)

    if not candidates:
        return results

    flagged: list[str] = []
    for script_path in candidates:
        try:
            text = script_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        has_infinite_loop = any(p.search(text) for p in _INFINITE_LOOP_PATTERNS)
        if not has_infinite_loop:
            continue

        has_deadline_guard = any(p.search(text) for p in _DEADLINE_GUARD_PATTERNS)
        if not has_deadline_guard:
            try:
                rel = script_path.relative_to(root)
            except ValueError:
                rel = script_path
            flagged.append(str(rel))

    if flagged:
        for name in flagged:
            results.append(
                ValidationResult(
                    name=f"blocking-loop:{name}",
                    passed=False,
                    message=(
                        f"{name}: unbounded loop detected without a deadline/timeout guard "
                        "(H11 violation). Add an explicit deadline, iteration cap, and "
                        "fallback exit path."
                    ),
                ),
            )
    else:
        results.append(
            ValidationResult(
                name="blocking-loops",
                passed=True,
                message=f"{len(candidates)} script file(s) checked — no unbounded loops found",
            ),
        )

    return results


def _check_bare_sleep(root: Path) -> list[ValidationResult]:
    """Scan script files for bare sleep delays without a loop/retry context (H23).

    A bare sleep is a ``sleep N`` / ``Start-Sleep`` line that appears in a script
    file that contains NO loop or retry constructs.  This is a timing anti-pattern
    that blocks indefinitely when the awaited condition never arrives.

    Files with a loop/retry context (``for``, ``while``, ``until``, ``max_retries``)
    are skipped — the sleep is part of a legitimate polling loop in those cases.

    Emits a warning (not a hard error) to allow gradual adoption.
    """
    results: list[ValidationResult] = []

    candidates: list[Path] = []
    for path in root.iterdir():
        if path.is_file() and path.suffix.lower() in _SCRIPT_EXTENSIONS:
            candidates.append(path)
    scripts_dir = root / "scripts"
    if scripts_dir.is_dir():
        for path in scripts_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in _SCRIPT_EXTENSIONS:
                candidates.append(path)

    if not candidates:
        return results

    flagged: list[str] = []
    for script_path in candidates:
        try:
            text = script_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        has_sleep = any(p.search(text) for p in _BARE_SLEEP_PATTERNS)
        if not has_sleep:
            continue

        # Sleep inside a loop/retry context is acceptable
        has_loop_context = any(p.search(text) for p in _SLEEP_LOOP_CONTEXT)
        if not has_loop_context:
            try:
                rel = script_path.relative_to(root)
            except ValueError:
                rel = script_path
            flagged.append(str(rel))

    if flagged:
        for name in flagged:
            results.append(
                ValidationResult(
                    name=f"bare-sleep:{name}",
                    passed=False,
                    message=(
                        f"{name}: bare sleep delay without a polling loop (H23 warning). "
                        "Replace with a retry loop that has a max iteration count and "
                        "non-zero exit on timeout."
                    ),
                ),
            )
    else:
        results.append(
            ValidationResult(
                name="bare-sleep",
                passed=True,
                message=f"{len(candidates)} script file(s) checked — no bare sleep delays found",
            ),
        )

    return results


def run_validate(root: Path) -> ValidationReport:
    """Run all validation checks and return a report."""
    report = ValidationReport()
    report.results.extend(_check_scaffold_yml(root))
    report.results.extend(_check_agents_md_refs(root))
    report.results.extend(_check_req_ids_unique(root))
    report.results.extend(_check_architecture_reqs(root))
    report.results.extend(_check_blocking_loops(root))
    report.results.extend(_check_bare_sleep(root))
    return report
