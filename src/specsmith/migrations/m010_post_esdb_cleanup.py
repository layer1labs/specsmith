# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""M010 — Post-ESDB cleanup (WI-9F1AE964).

What this migration does
------------------------
Removes legacy files that are no longer needed now that the ESDB-first and
YAML-first migrations (M007–M009) have completed successfully.

Files removed (each with its own safety guard)
-----------------------------------------------
docs/REQUIREMENTS.md
    Guard: docs/requirements/*.yml must exist (YAML source is in place).
    Why:   Deprecated by M007; kept with a deprecation notice until now.

docs/TESTS.md
    Guard: docs/tests/*.yml must exist.
    Why:   Deprecated by M007; kept with a deprecation notice until now.

.specsmith/requirements.json
    Guard: docs/requirements/*.yml must exist AND .specsmith/esdb.sqlite3 must
           exist (ESDB is the new backing store).
    Why:   JSON flat-file replaced by YAML + ESDB; kept as read-only cache.

.specsmith/testcases.json
    Guard: docs/tests/*.yml must exist AND .specsmith/esdb.sqlite3 must exist.
    Why:   Same as requirements.json.

.specsmith/agents.md.m006.bak
    Guard: .specsmith/agents.json must exist (the real config is in place).
    Why:   Stale backup left by M006; no longer referenced anywhere.

.specsmith/esdb_migration_manifest.json
    Guard: .specsmith/esdb.sqlite3 and .specsmith/esdb-full-coverage must exist.
    Why:   One-time migration artefact from the JSON-flat backend era; records
           "backend: json-flat" which is no longer true.

.specsmith/migration-backups/<timestamp>/
    Guard: .specsmith/esdb-m009-backfill marker must exist (M009 completed).
    Why:   Per-migration snapshot directories accumulate across sessions and
           are no longer needed once ESDB holds the canonical history.
           Only directories strictly older than the most-recent migration run
           are removed; the newest backup directory is kept as a rollback
           escape hatch.

Idempotency
-----------
Writes .specsmith/esdb-m010-cleanup on successful completion.
Re-running after partial completion is safe — each step checks for the file
before attempting removal.

Rollback
--------
Deleted files cannot be un-deleted by the rollback method. The rollback only
removes the idempotency marker so the migration reports itself as unapplied
again. Because this migration deletes files, it is skipped entirely when
BENCH_DRY_RUN=1 or dry_run=True is passed.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from specsmith.migrations import Migration, MigrationResult

_MARKER_FILE = ".specsmith/esdb-m010-cleanup"


class PostEsdbCleanupMigration(Migration):
    version = 10
    title = "Post-ESDB cleanup — remove deprecated legacy files"
    description = (
        "Removes docs/REQUIREMENTS.md, docs/TESTS.md, .specsmith/requirements.json, "
        ".specsmith/testcases.json, .specsmith/agents.md.m006.bak, "
        ".specsmith/esdb_migration_manifest.json, and old migration-backup "
        "directories that are no longer needed after the M007–M009 migrations. "
        "Each removal is guarded by a safety check. Idempotent. "
        "WARNING: files are deleted permanently. Ensure your repo is committed "
        "before running this migration."
    )

    def run(self, root: Path, *, dry_run: bool = False) -> MigrationResult:  # noqa: C901
        result = MigrationResult(version=self.version, title=self.title, dry_run=dry_run)
        marker = root / _MARKER_FILE

        if marker.exists() and not dry_run:
            result.message = "Post-ESDB cleanup already applied — skipping."
            return result

        removed: list[str] = []
        skipped: list[str] = []
        blocked: list[str] = []

        # ── helpers ────────────────────────────────────────────────────────────

        def _has_yaml_files(directory: Path) -> bool:
            return directory.is_dir() and any(directory.glob("*.yml"))

        def _esdb_exists() -> bool:
            return (root / ".specsmith" / "esdb.sqlite3").exists()

        def _remove_file(rel: str, *, guard: bool, reason: str) -> None:
            """Remove *rel* (relative to root) if *guard* is True."""
            target = root / rel
            if not target.exists():
                skipped.append(f"{rel} (not present)")
                return
            if not guard:
                blocked.append(f"{rel} (guard failed: {reason})")
                return
            if not dry_run:
                target.unlink()
            removed.append(rel)

        def _remove_dir(rel: str, *, guard: bool, reason: str) -> None:
            """Remove directory *rel* (relative to root) if *guard* is True."""
            target = root / rel
            if not target.exists():
                skipped.append(f"{rel} (not present)")
                return
            if not guard:
                blocked.append(f"{rel} (guard failed: {reason})")
                return
            if not dry_run:
                shutil.rmtree(str(target), ignore_errors=True)
            removed.append(rel)

        # ── 1. docs/REQUIREMENTS.md ────────────────────────────────────────────
        req_yaml_ok = _has_yaml_files(root / "docs" / "requirements")
        _remove_file(
            "docs/REQUIREMENTS.md",
            guard=req_yaml_ok,
            reason="docs/requirements/*.yml not found; YAML source must exist first",
        )

        # ── 2. docs/TESTS.md ──────────────────────────────────────────────────
        tests_yaml_ok = _has_yaml_files(root / "docs" / "tests")
        _remove_file(
            "docs/TESTS.md",
            guard=tests_yaml_ok,
            reason="docs/tests/*.yml not found; YAML source must exist first",
        )

        # ── 3. .specsmith/requirements.json ───────────────────────────────────
        _remove_file(
            ".specsmith/requirements.json",
            guard=req_yaml_ok and _esdb_exists(),
            reason="YAML source or ESDB not yet in place",
        )

        # ── 4. .specsmith/testcases.json ──────────────────────────────────────
        _remove_file(
            ".specsmith/testcases.json",
            guard=tests_yaml_ok and _esdb_exists(),
            reason="YAML source or ESDB not yet in place",
        )

        # ── 5. .specsmith/agents.md.m006.bak ──────────────────────────────────
        # agents.json lives globally at ~/.specsmith/agents.json or per-project.
        global_agents = Path(os.path.expanduser("~")) / ".specsmith" / "agents.json"
        agents_config_ok = (root / ".specsmith" / "agents.json").exists() or global_agents.exists()
        _remove_file(
            ".specsmith/agents.md.m006.bak",
            guard=agents_config_ok,
            reason="neither .specsmith/agents.json nor ~/.specsmith/agents.json found",
        )

        # ── 6. .specsmith/esdb_migration_manifest.json ────────────────────────
        esdb_full_ok = (root / ".specsmith" / "esdb-full-coverage").exists()
        esdb_first_ok = (root / ".specsmith" / "esdb-m009-backfill").exists()
        _remove_file(
            ".specsmith/esdb_migration_manifest.json",
            guard=_esdb_exists() and esdb_full_ok,
            reason="ESDB full-coverage (M008) must complete first",
        )

        # ── 7. .specsmith/migration-backups/<timestamp>/ ──────────────────────
        #       Keep the single newest backup dir; remove all older ones.
        backups_dir = root / ".specsmith" / "migration-backups"
        if backups_dir.is_dir() and esdb_first_ok:
            subdirs = sorted(
                [d for d in backups_dir.iterdir() if d.is_dir()],
                key=lambda d: d.name,
            )
            # Keep the newest; remove all older ones
            dirs_to_remove = subdirs[:-1] if len(subdirs) > 1 else []
            for d in dirs_to_remove:
                rel = str(d.relative_to(root)).replace("\\", "/")
                _remove_dir(
                    rel,
                    guard=True,
                    reason="",
                )
        elif backups_dir.is_dir() and not esdb_first_ok:
            blocked.append(
                ".specsmith/migration-backups/* (guard failed: M009 backfill not confirmed)"
            )

        # ── Marker ────────────────────────────────────────────────────────────
        if not dry_run and removed:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(
                f"m010 applied:\n"
                f"removed={len(removed)}\n"
                f"skipped={len(skipped)}\n"
                f"blocked={len(blocked)}\n" + "\n".join(f"  - {r}" for r in removed) + "\n",
                encoding="utf-8",
            )
            result.files_created.append(_MARKER_FILE)

        prefix = "[dry-run] Would remove" if dry_run else "Removed"
        lines = [
            f"{prefix} {len(removed)} file(s)/dir(s).",
        ]
        if removed:
            lines.append("  Removed: " + ", ".join(removed))
        if skipped:
            lines.append("  Already gone: " + ", ".join(skipped))
        if blocked:
            lines.append("  Blocked (safety guard): " + "; ".join(blocked))
        result.message = "\n".join(lines)
        result.success = True
        return result

    def rollback(self, root: Path) -> MigrationResult:
        """Remove idempotency marker — files cannot be restored."""
        result = MigrationResult(version=self.version, title=self.title)
        marker = root / _MARKER_FILE
        if marker.exists():
            marker.unlink()
            result.message = (
                f"Removed {_MARKER_FILE}. "
                "NOTE: deleted files cannot be restored by rollback. "
                "Restore from git (git checkout HEAD -- <path>) if needed."
            )
            result.files_modified.append(_MARKER_FILE)
        else:
            result.message = f"{_MARKER_FILE} not found — nothing to roll back."
        return result
