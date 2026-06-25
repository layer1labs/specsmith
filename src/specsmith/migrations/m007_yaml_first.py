# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""M007 — YAML-first governance migration (REQ-373).

Converts a markdown-mode project to YAML-first governance:
  1. Parses docs/REQUIREMENTS.md  →  docs/requirements/migrated.yml
  2. Parses docs/TESTS.md         →  docs/tests/migrated.yml
  3. Writes 'yaml' to .specsmith/governance-mode
  4. Adds a deprecation header to the MD files (does NOT delete them)

Idempotent: if governance-mode is already 'yaml', this is a no-op.
Non-destructive: REQUIREMENTS.md and TESTS.md are kept with a deprecation notice.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from specsmith.migrations import Migration, MigrationResult

_DEPRECATED_HEADER = (
    "<!-- DEPRECATED: This file is no longer the source of truth.\n"
    "     Edit docs/requirements/*.yml (or docs/tests/*.yml) instead.\n"
    "     This file will be removed after all projects have migrated.\n"
    "     Run: specsmith migrate run  to update your project. -->\n"
)


class YamlFirstMigration(Migration):
    version = 7
    title = "Migrate markdown governance to YAML-first mode"
    description = (
        "Converts docs/REQUIREMENTS.md and docs/TESTS.md to YAML source files "
        "under docs/requirements/ and docs/tests/. Sets .specsmith/governance-mode "
        "to 'yaml'. The markdown files are kept but marked as deprecated — "
        "they will be removed in a future release once all projects have migrated."
    )

    def run(self, root: Path, *, dry_run: bool = False) -> MigrationResult:
        result = MigrationResult(version=self.version, title=self.title, dry_run=dry_run)

        # Idempotent: already in YAML mode → nothing to do
        mode_file = root / ".specsmith" / "governance-mode"
        if mode_file.exists() and mode_file.read_text(encoding="utf-8").strip().lower() == "yaml":
            result.message = "Already in YAML-first mode — nothing to do."
            return result

        req_md = root / "docs" / "REQUIREMENTS.md"
        tests_md = root / "docs" / "TESTS.md"
        req_yaml_dir = root / "docs" / "requirements"
        tests_yaml_dir = root / "docs" / "tests"

        # ── Requirements migration ───────────────────────────────────────────
        if req_md.exists():
            yaml_files_exist = req_yaml_dir.is_dir() and any(req_yaml_dir.glob("*.yml"))
            if not yaml_files_exist:
                from specsmith.sync import parse_requirements_md

                reqs = parse_requirements_md(req_md.read_text(encoding="utf-8"))
                if reqs:
                    if not dry_run:
                        req_yaml_dir.mkdir(parents=True, exist_ok=True)
                        migrated = req_yaml_dir / "migrated.yml"
                        _write_req_yaml(migrated, reqs)
                    result.files_created.append("docs/requirements/migrated.yml")

            # Add deprecation header to REQUIREMENTS.md (idempotent)
            if not dry_run:
                _add_deprecation_header(req_md, _DEPRECATED_HEADER)
            result.files_modified.append("docs/REQUIREMENTS.md")

        # ── Tests migration ──────────────────────────────────────────────────
        if tests_md.exists():
            yaml_files_exist = tests_yaml_dir.is_dir() and any(tests_yaml_dir.glob("*.yml"))
            if not yaml_files_exist:
                from specsmith.sync import parse_tests_md

                tests = parse_tests_md(tests_md.read_text(encoding="utf-8"))
                if tests:
                    if not dry_run:
                        tests_yaml_dir.mkdir(parents=True, exist_ok=True)
                        migrated = tests_yaml_dir / "migrated.yml"
                        _write_test_yaml(migrated, tests)
                    result.files_created.append("docs/tests/migrated.yml")

            if not dry_run:
                _add_deprecation_header(tests_md, _DEPRECATED_HEADER)
            result.files_modified.append("docs/TESTS.md")

        # ── Set governance-mode = yaml ───────────────────────────────────────
        if not dry_run:
            mode_file.parent.mkdir(parents=True, exist_ok=True)
            mode_file.write_text("yaml\n", encoding="utf-8")
        result.files_modified.append(".specsmith/governance-mode")

        n_created = len(result.files_created)
        n_modified = len(result.files_modified)
        if dry_run:
            result.message = (
                f"Would create {n_created} YAML file(s) and mark {n_modified} "
                "file(s) as deprecated."
            )
        else:
            result.message = (
                f"Migrated to YAML-first mode. Created {n_created} YAML file(s). "
                "Markdown files kept with deprecation notices — remove them manually "
                "once all your projects have migrated."
            )
        return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _add_deprecation_header(path: Path, header: str) -> None:
    """Prepend deprecation header to *path* if not already present."""
    text = path.read_text(encoding="utf-8")
    if "DEPRECATED" in text[:300]:
        return  # Already has a deprecation notice
    path.write_text(header + text, encoding="utf-8")


def _write_req_yaml(path: Path, reqs: list[dict]) -> None:
    header = (
        "# specsmith requirements — migrated from REQUIREMENTS.md by m007\n"
        "# CANONICAL SOURCE: edit this file, not docs/REQUIREMENTS.md\n"
        "# docs/REQUIREMENTS.md is now DEPRECATED.\n"
        "#\n"
        "# Schema: id (REQ-NNN), title, description, source, status\n"
    )
    body = yaml.dump(reqs, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(header + body, encoding="utf-8")


def _write_test_yaml(path: Path, tests: list[dict]) -> None:
    header = (
        "# specsmith test cases — migrated from TESTS.md by m007\n"
        "# CANONICAL SOURCE: edit this file, not docs/TESTS.md\n"
        "# docs/TESTS.md is now DEPRECATED.\n"
        "#\n"
        "# Schema: id (TEST-NNN), title, requirement_id, type, verification_method\n"
    )
    body = yaml.dump(tests, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(header + body, encoding="utf-8")
