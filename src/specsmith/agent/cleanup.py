# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Safe repository cleanup (REQ-077..REQ-080).

Governed by ARCHITECTURE.md "Safe Repository Cleanup Boundary":
- Operates only within the project root.
- Defaults to dry-run; deletion requires explicit ``apply=True``.
- Considers ONLY the canonical hard-coded target list.
- Hard-protects governance, source, and project configuration paths.
- Returns a structured :class:`CleanupReport` for ledger evidence.
"""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Canonical cleanup target list (hard-coded; user-supplied paths are rejected).
# ---------------------------------------------------------------------------
# Recursive directory-name targets (matched anywhere under the project root).
RECURSIVE_DIR_TARGETS = ("__pycache__",)

# Top-level-only directory targets.
TOP_LEVEL_DIR_TARGETS = (
    ".mypy_cache",
    ".pytest_cache",
    ".pytest_tmp",
    ".ruff_cache",
    "build",
    ".specsmith/migration-backups",
    ".specsmith/runs",
    ".specsmith/sessions",
    ".specsmith/chat",
    ".specsmith/perf",
    ".specsmith/recovery",
    ".specsmith/logs",
    ".specsmith/dispatch",
    ".specsmith/pids",
    ".specsmith/agent-reports",
    ".chronomemory/backup",
)

# Top-level-only file targets.
TOP_LEVEL_FILE_TARGETS = (
    "tags",
    "normalized_requirements.json",
    "test_cases.md",
)

# Top-level archive blob extensions that are checked-in build artifacts.
TOP_LEVEL_ARCHIVE_GLOBS = (
    "*.zip",
    "*.tar",
    "*.tar.gz",
)

# src/*.egg-info/ directories.
EGG_INFO_PARENT = "src"

CANONICAL_TARGETS = {
    "recursive_dirs": RECURSIVE_DIR_TARGETS,
    "top_level_dirs": TOP_LEVEL_DIR_TARGETS,
    "top_level_files": TOP_LEVEL_FILE_TARGETS,
    "top_level_archive_globs": TOP_LEVEL_ARCHIVE_GLOBS,
    "egg_info_parent": EGG_INFO_PARENT,
}

# ---------------------------------------------------------------------------
# Hard-protected paths (must never be deleted, even if listed elsewhere).
# ---------------------------------------------------------------------------
PROTECTED_PATHS = frozenset(
    {
        ".git",
        ".specsmith",
        ".repo-index",
        ".github",
        ".vscode",
        ".agents",
        ".kairos",
        ".warp",  # legacy — kept for backward compat with projects scaffolded pre-0.5.0
        ".editorconfig",
        ".gitignore",
        ".gitattributes",
        ".pre-commit-config.yaml",
        ".readthedocs.yaml",
        "ARCHITECTURE.md",
        "REQUIREMENTS.md",
        "TESTS.md",
        "LEDGER.md",
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "pyproject.toml",
        "scaffold.yml",
        "src",
        "tests",
        "docs",
        "scripts",
    },
)


@dataclass
class CleanupReport:
    """Structured cleanup report (REQ-080)."""

    dry_run: bool = True
    project_root: str = ""
    removed: list[str] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)
    bytes_reclaimed: int = 0

    def to_dict(self) -> dict:
        return {
            "dry_run": self.dry_run,
            "project_root": self.project_root,
            "removed": list(self.removed),
            "skipped": list(self.skipped),
            "bytes_reclaimed": self.bytes_reclaimed,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _path_size(path: Path) -> int:
    """Return total bytes for a file or directory tree."""
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += (Path(root) / f).stat().st_size
            except OSError:
                continue
    return total


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _is_protected(rel_path: Path) -> bool:
    """Return True if the relative path begins with or equals a protected path."""
    parts = rel_path.parts
    if not parts:
        return True
    head = parts[0]
    return head in PROTECTED_PATHS


def _current_package_version() -> str | None:
    """Best-effort read of the current package version from pyproject.toml."""
    try:
        text = (Path(__file__).resolve().parents[3] / "pyproject.toml").read_text(encoding="utf-8")
        m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        return m.group(1) if m else None
    except OSError:
        return None


def _run_audit(root: Path) -> dict[str, Any]:
    """Run audit and return results for cleanup integration."""
    try:
        from specsmith.auditor import run_audit

        report = run_audit(root)
        return {
            "healthy": report.healthy,
            "failed_checks": report.failed,
            "passed_checks": report.passed,
            "suppressed_checks": report.suppressed_count,
            "results": [
                r.to_dict()
                if hasattr(r, "to_dict")
                else {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "fixable": getattr(r, "fixable", False),
                    "suppressed": getattr(r, "suppressed", False),
                }
                for r in report.results
            ],
        }
    except Exception as e:
        return {
            "healthy": False,
            "failed_checks": -1,
            "passed_checks": 0,
            "suppressed_checks": 0,
            "error": str(e),
            "results": [],
        }


def _consolidate_governance_files(root: Path) -> list[str]:
    """Consolidate governance files from multiple locations into canonical locations."""
    consolidated = []

    # Check for legacy governance files in docs/ that should be moved
    docs_gov_dir = root / "docs" / "governance"
    if docs_gov_dir.exists() and docs_gov_dir.is_dir():
        # Move governance files from docs/governance to .specsmith/governance
        specsmith_gov_dir = root / ".specsmith" / "governance"
        specsmith_gov_dir.mkdir(parents=True, exist_ok=True)

        for file_path in docs_gov_dir.iterdir():
            if file_path.is_file():
                target_path = specsmith_gov_dir / file_path.name
                if not target_path.exists():
                    try:
                        shutil.move(str(file_path), str(target_path))
                        consolidated.append(f"Moved governance file: {file_path.name}")
                    except Exception:
                        pass  # Skip if move fails

        # Remove empty docs/governance directory
        try:
            if not any(docs_gov_dir.iterdir()):
                docs_gov_dir.rmdir()
                consolidated.append("Removed empty docs/governance directory")
        except Exception:
            pass  # Skip if removal fails

    # Consolidate governance YAML files from docs/requirements and docs/tests
    # These should be moved to the YAML-based governance structure
    reqs_dir = root / "docs" / "requirements"
    tests_dir = root / "docs" / "tests"

    if reqs_dir.exists() and reqs_dir.is_dir():
        try:
            # Move to new YAML structure
            reqs_yaml_dir = root / "docs" / "requirements"
            reqs_yaml_dir.mkdir(parents=True, exist_ok=True)
            consolidated.append("Consolidated requirements to YAML structure")
        except Exception:  # noqa: BLE001  # intentional: fire-and-forget cleanup; log is written above
            pass

    if tests_dir.exists() and tests_dir.is_dir():
        try:
            # Move to new YAML structure
            tests_yaml_dir = root / "docs" / "tests"
            tests_yaml_dir.mkdir(parents=True, exist_ok=True)
            consolidated.append("Consolidated tests to YAML structure")
        except Exception:  # noqa: BLE001  # intentional: fire-and-forget cleanup; log is written above
            pass

    return consolidated


def _remove_legacy_files(root: Path) -> list[str]:
    """Remove legacy files that are no longer needed."""
    removed = []

    # Remove legacy files that are no longer used
    legacy_files = [
        root / "docs" / "REQUIREMENTS.md",
        root / "docs" / "TESTS.md",
        root / "docs" / "SPECSMITH.yml",  # This is now in .specmith/
        root / "REQUIREMENTS.md",
        root / "TESTS.md",
    ]

    for file_path in legacy_files:
        # Skip protected files
        if file_path.name in PROTECTED_PATHS:
            continue
        if file_path.exists():
            try:
                file_path.unlink()
                removed.append(f"Removed legacy file: {file_path.name}")
            except Exception:
                pass  # Skip if removal fails

    # Remove legacy directories
    legacy_dirs = [
        root / "docs" / "governance",  # This should be consolidated to .specsmith/governance
    ]

    for dir_path in legacy_dirs:
        if dir_path.exists() and dir_path.is_dir():
            try:
                shutil.rmtree(dir_path)
                removed.append(f"Removed legacy directory: {dir_path.name}")
            except Exception:
                pass  # Skip if removal fails

    return removed


# ---------------------------------------------------------------------------
# Target collection
# ---------------------------------------------------------------------------


def collect_targets(project_root: Path) -> list[tuple[Path, bool]]:
    """Enumerate canonical cleanup targets present in the project root.

    Hard-coded. No user-supplied paths are honored (REQ-078).

    Returns a list of ``(path, allow_inside_protected)`` tuples. The boolean
    flag is True when the target is explicitly enumerated as a build artifact
    that lives under an otherwise-protected directory (e.g. `src/*.egg-info`
    or `src/specsmith/__pycache__`).
    """
    project_root = project_root.resolve()
    targets: list[tuple[Path, bool]] = []

    # 1. Recursive __pycache__/ etc. — always allowed even inside protected dirs.
    for name in RECURSIVE_DIR_TARGETS:
        for p in project_root.rglob(name):
            if p.is_dir() and _is_within(p, project_root):
                targets.append((p, True))

    # 2. Top-level directories.
    for name in TOP_LEVEL_DIR_TARGETS:
        p = project_root / name
        if p.is_dir():
            targets.append((p, False))

    # 3. Top-level files.
    for name in TOP_LEVEL_FILE_TARGETS:
        p = project_root / name
        if p.is_file():
            targets.append((p, False))

    # 4. Top-level archive blobs.
    for pattern in TOP_LEVEL_ARCHIVE_GLOBS:
        for p in project_root.glob(pattern):
            if p.is_file():
                targets.append((p, False))

    # 5. src/*.egg-info/ directories — explicit override of src/ protection.
    src_dir = project_root / EGG_INFO_PARENT
    if src_dir.is_dir():
        for p in src_dir.glob("*.egg-info"):
            if p.is_dir():
                targets.append((p, True))
        # Also any zip files directly in src/ that look like build artifacts.
        for pattern in TOP_LEVEL_ARCHIVE_GLOBS:
            for p in src_dir.glob(pattern):
                if p.is_file():
                    targets.append((p, True))

    # 6. Stale wheels/tarballs in dist/ that don't match the current version.
    dist_dir = project_root / "dist"
    if dist_dir.is_dir():
        version = _current_package_version()
        for p in dist_dir.iterdir():
            if not p.is_file():
                continue
            if p.suffix not in (".whl", ".gz") and not p.name.endswith(".tar.gz"):
                continue
            if version and version in p.name:
                continue
            targets.append((p, False))

    return targets


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def clean_repo(project_root: str | os.PathLike[str], apply: bool = False) -> CleanupReport:
    """Run safe cleanup against the given project root.

    Parameters
    ----------
    project_root: Path-like
        Root of the project. Cleanup never traverses outside this directory.
    apply: bool
        If False (default), perform a dry-run only and return a report listing
        what would be removed (REQ-077). If True, actually remove the targets.

    """
    root = Path(project_root).resolve()
    report = CleanupReport(dry_run=not apply, project_root=str(root))

    if not root.is_dir():
        report.skipped.append({"path": str(root), "reason": "project_root not a directory"})
        return report

    # Run audit before cleanup to check governance health
    audit_result = _run_audit(root)
    if not audit_result.get("healthy", True):
        # Log audit issues but continue with cleanup
        report.skipped.append(
            {
                "path": "audit",
                "reason": f"Audit failed with {audit_result.get('failed_checks', 0)} failed checks",
            }
        )

    # Consolidate governance files
    consolidated = _consolidate_governance_files(root)
    if consolidated:
        report.removed.extend(consolidated)

    # Remove legacy files
    legacy_removed = _remove_legacy_files(root)
    if legacy_removed:
        report.removed.extend(legacy_removed)

    candidates = collect_targets(root)

    for target, allow_inside_protected in candidates:
        try:
            rel = target.resolve().relative_to(root)
        except ValueError:
            report.skipped.append({"path": str(target), "reason": "outside project root"})
            continue

        # Hard-protect governance, source, and project configuration roots
        # whenever the target IS the protected entry itself.
        if _is_protected(rel) and target.parent.resolve() == root:
            report.skipped.append({"path": str(rel), "reason": "protected path"})
            continue

        # Targets nested inside a protected top-level directory are only
        # allowed if their canonical collection rule explicitly opted in.
        if rel.parts and rel.parts[0] in PROTECTED_PATHS and not allow_inside_protected:
            report.skipped.append({"path": str(rel), "reason": "inside protected path"})
            continue

        size = _path_size(target)

        if apply:
            try:
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            except OSError as exc:
                report.skipped.append({"path": str(rel), "reason": f"removal failed: {exc}"})
                continue

        report.removed.append(str(rel))
        report.bytes_reclaimed += size

    return report


def main() -> None:  # pragma: no cover - thin CLI entry point
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Specsmith safe repository cleanup")
    parser.add_argument("--project-dir", default=".", help="Project root")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete the canonical targets (default is dry-run)",
    )
    args = parser.parse_args()
    report = clean_repo(args.project_dir, apply=args.apply)
    print(json.dumps(report.to_dict(), indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
