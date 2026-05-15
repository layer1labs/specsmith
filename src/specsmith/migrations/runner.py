# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Migration runner — tracks applied versions and executes pending migrations.

Migration state is tracked in .specsmith/migration-state.json:
  {
    "applied": [1, 2, 3],
    "last_run": "2026-05-15T14:00:00Z"
  }

State is written atomically (temp-rename) to survive crashes.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from specsmith.migrations import Migration, MigrationRegistry, MigrationResult


_STATE_PATH = ".specsmith/migration-state.json"


class MigrationRunner:
    """Runs pending migrations for a project."""

    def __init__(self, root: Path) -> None:
        self.root = root

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def _state_path(self) -> Path:
        return self.root / _STATE_PATH

    def applied_versions(self) -> set[int]:
        """Return the set of already-applied migration versions."""
        p = self._state_path()
        if not p.is_file():
            return set()
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return set(int(v) for v in data.get("applied", []))
        except Exception:  # noqa: BLE001
            return set()

    def _save_state(self, applied: set[int]) -> None:
        """Atomically write migration state."""
        p = self._state_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "applied": sorted(applied),
            "last_run": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(str(tmp), str(p))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_pending(self, *, dry_run: bool = False) -> list[MigrationResult]:
        """Run all pending (unapplied) migrations in version order."""
        applied = self.applied_versions()
        all_migrations = MigrationRegistry.all()
        pending = [m for m in all_migrations if m.version not in applied]

        results: list[MigrationResult] = []
        for migration in pending:
            result = self._run_one(migration, applied, dry_run=dry_run)
            results.append(result)

        return results

    def run_one(self, version: int, *, dry_run: bool = False) -> MigrationResult:
        """Run a specific migration by version number."""
        migration = MigrationRegistry.get(version)
        if migration is None:
            return MigrationResult(
                version=version,
                title="unknown",
                success=False,
                error=f"No migration found with version {version}.",
            )
        applied = self.applied_versions()
        return self._run_one(migration, applied, dry_run=dry_run)

    def _run_one(
        self,
        migration: Migration,
        applied: set[int],
        *,
        dry_run: bool,
    ) -> MigrationResult:
        """Execute a single migration and update state."""
        try:
            result = migration.run(self.root, dry_run=dry_run)
        except Exception as exc:  # noqa: BLE001
            return MigrationResult(
                version=migration.version,
                title=migration.title,
                success=False,
                error=str(exc),
            )

        if result.success and not dry_run:
            applied.add(migration.version)
            try:
                self._save_state(applied)
            except Exception:  # noqa: BLE001
                pass  # State save failure is non-fatal

        return result
