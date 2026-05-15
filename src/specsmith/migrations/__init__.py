# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""specsmith migrations — versioned project migration framework.

Design principles:
  - Each migration is in its own file (m001_*.py, m002_*.py, ...)
  - Migrations are isolated and can be dropped cleanly before public release
  - Migration state is tracked in .specsmith/migration-state.json
  - No migration depends on another — each is independently runnable
  - All migrations are non-destructive by default (they add, not delete)

To drop the migration framework at 1.0 release:
  1. Delete src/specsmith/migrations/ entirely
  2. Remove the MigrationRunner.run_pending() call from upgrader.py
  3. Done — no other code imports from this package

REQ-318: Migration framework — isolated, versionable, droppable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Base classes
# ---------------------------------------------------------------------------


@dataclass
class MigrationResult:
    """Result of running a single migration."""

    version: int
    title: str
    success: bool = True
    dry_run: bool = False
    message: str = ""
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "title": self.title,
            "success": self.success,
            "dry_run": self.dry_run,
            "message": self.message,
            "files_created": self.files_created,
            "files_modified": self.files_modified,
            "error": self.error,
        }


class Migration(ABC):
    """Base class for all specsmith project migrations."""

    #: Integer version — must be unique across all migrations.
    version: int = 0
    #: Human-readable title shown in `specsmith migrate list`.
    title: str = ""
    #: Description of what this migration does.
    description: str = ""

    @abstractmethod
    def run(self, root: Path, *, dry_run: bool = False) -> MigrationResult:
        """Execute the migration.

        Args:
            root: Project root directory.
            dry_run: If True, describe what would change without writing.

        Returns:
            MigrationResult with details of what was done.
        """

    def rollback(self, root: Path) -> MigrationResult:
        """Roll back this migration (best-effort).

        Default implementation returns a no-op result. Override in
        migrations that have a meaningful rollback path.
        """
        return MigrationResult(
            version=self.version,
            title=self.title,
            success=True,
            message="No rollback available for this migration.",
        )


# ---------------------------------------------------------------------------
# Registry — lazily populated on first access
# ---------------------------------------------------------------------------


class _MigrationRegistry:
    """Registry of all available migrations."""

    def __init__(self) -> None:
        self._migrations: list[Migration] | None = None

    def _load(self) -> list[Migration]:
        """Lazily import all migration modules and collect Migration instances."""
        if self._migrations is not None:
            return self._migrations

        from specsmith.migrations import (
            m001_governance_yaml,
            m002_agents_slim,
            m003_compliance_init,
            m004_ledger_esdb,
        )

        instances: list[Migration] = [
            m001_governance_yaml.GovernanceYamlMigration(),
            m002_agents_slim.AgentsSlimMigration(),
            m003_compliance_init.ComplianceInitMigration(),
            m004_ledger_esdb.LedgerEsdbMigration(),
        ]
        instances.sort(key=lambda m: m.version)
        self._migrations = instances
        return instances

    def all(self) -> list[Migration]:
        return self._load()

    def get(self, version: int) -> Migration | None:
        return next((m for m in self._load() if m.version == version), None)


MigrationRegistry = _MigrationRegistry()
