# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""M004 — Ledger ESDB migration.

Ensures the project's governance data (requirements.json, testcases.json)
is migrated into the ChronoStore WAL at .chronomemory/events.wal.

This is the same operation as `specsmith esdb migrate` but packaged as
an auto-running migration so projects get ESDB backing automatically.
"""

from __future__ import annotations

from pathlib import Path

from specsmith.migrations import Migration, MigrationResult


class LedgerEsdbMigration(Migration):
    version = 4
    title = "Migrate .specsmith/ JSON → ChronoStore ESDB WAL"
    description = (
        "Imports requirements.json and testcases.json from .specsmith/ into the "
        "ChronoStore WAL at .chronomemory/events.wal. Records carry OEA "
        "anti-hallucination fields (source_type, confidence, evidence) per REQ-310."
    )

    def run(self, root: Path, *, dry_run: bool = False) -> MigrationResult:
        result = MigrationResult(version=self.version, title=self.title, dry_run=dry_run)

        specsmith_dir = root / ".specsmith"
        wal = root / ".chronomemory" / "events.wal"

        # Check if there's anything to migrate
        reqs = specsmith_dir / "requirements.json"
        tests = specsmith_dir / "testcases.json"
        if not reqs.exists() and not tests.exists():
            result.message = (
                "No .specsmith/requirements.json or testcases.json found — nothing to migrate."
            )
            return result

        if wal.exists():
            # Already migrated — check if new records need to be added
            result.message = (
                "ChronoStore WAL already exists. "
                "Run `specsmith esdb migrate` to import any new records."
            )
            return result

        if dry_run:
            req_count = 0
            test_count = 0
            try:
                import json

                if reqs.exists():
                    req_count = len(json.loads(reqs.read_text(encoding="utf-8")))
                if tests.exists():
                    test_count = len(json.loads(tests.read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001
                pass
            result.message = (
                f"Would migrate {req_count} requirements + {test_count} test cases "
                "to ChronoStore WAL at .chronomemory/events.wal"
            )
            result.files_created.append(".chronomemory/events.wal")
            return result

        # Run migration
        try:
            from specsmith.esdb.store import ChronoStore

            with ChronoStore(root) as store:
                counts = store.migrate_from_json(specsmith_dir)

            reqs_m = counts.get("requirements", 0)
            tests_m = counts.get("testcases", 0)
            skipped = counts.get("skipped", 0)

            result.files_created.append(".chronomemory/events.wal")
            result.message = (
                f"Migrated {reqs_m} requirements + {tests_m} test cases to ChronoStore WAL. "
                f"{skipped} already present (skipped)."
            )
        except Exception as exc:  # noqa: BLE001
            result.success = False
            result.error = str(exc)
            result.message = f"ESDB migration failed: {exc}"

        return result
