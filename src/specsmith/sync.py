# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Machine state sync — keeps .specsmith/ JSON in sync with governance sources.

Implements REQ-003 (Machine State Must Reflect Governance State).

Canonical sources (YAML-first, Markdown fallback):
  docs/requirements/*.yml  ->  .specsmith/requirements.json  ->  docs/REQUIREMENTS.md
  docs/tests/*.yml         ->  .specsmith/testcases.json     ->  docs/TESTS.md

Design contract:
  - When .specsmith/governance-mode == "yaml" (YAML-first mode):
    YAML files are the source of truth.  JSON is a derived cache, MD is generated.
  - When governance-mode is absent/"markdown" (legacy mode):
    Markdown is the source of truth.  JSON is a derived cache.
  - Existing ``input`` / ``expected_behavior`` fields in testcases.json are preserved
    so hand-crafted test specs are not clobbered.
  - workitems.json is NOT managed here — it is runtime state only and should
    be gitignored.  Preflight allocates WI IDs dynamically at runtime.
"""

from __future__ import annotations

import contextlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

# ---------------------------------------------------------------------------
# Markdown parsers
# ---------------------------------------------------------------------------

# Matches either:
#   Style A: ## REQ-001  or  ## REQ-CLI-001: Title
#     The optional ": Title" suffix is captured in group(2).
#   Style B: ## N. Title  (ID comes from inline - **ID:** REQ-NNN field)
_FLEX_REQ_ID = r"REQ-(?:[A-Z][A-Z0-9_]*-)?\d+"
_NUMBERED_HEADING = re.compile(r"^#{1,3}\s+\d+\.\s+(.+?)\s*$")
# Group 1: REQ-ID,  Group 2 (optional): title text after the colon.
_DIRECT_HEADING = re.compile(r"^#{1,3}\s+(" + _FLEX_REQ_ID + r")(?::\s*(.+))?\s*$")
_ID_FIELD = re.compile(r"^-\s+\*\*ID:\*\*\s+(" + _FLEX_REQ_ID + r")")
_FIELD_LINE = re.compile(r"^-\s+\*\*(.+?):\*\*\s+(.+)")

# Letter suffixes (e.g. TEST-NN-002a) are supported via [a-z]* — fixes #183.
_FLEX_TEST_ID = r"TEST-(?:[A-Z][A-Z0-9_]*-)?\d+[a-z]*"
_TEST_NUMBERED_HEADING = re.compile(r"^#{1,3}\s+(?:TEST-[A-Z0-9_-]+\s+)?(.+?)\s*$")
_TEST_ID_FIELD = re.compile(r"^-\s+\*\*ID:\*\*\s+(" + _FLEX_TEST_ID + r")")


def parse_requirements_md(text: str) -> list[dict[str, Any]]:
    """Parse REQUIREMENTS.md and return a list of requirement records."""
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    pending_title: str = ""

    def _flush() -> None:
        if current.get("id"):
            records.append(dict(current))

    for line in text.splitlines():
        m_direct = _DIRECT_HEADING.match(line)
        if m_direct:
            _flush()
            # Group 2 carries the title when the heading is '## REQ-NNN: Title'
            inline_title = (m_direct.group(2) or "").strip()
            current = {"id": m_direct.group(1)}
            if inline_title:
                current["title"] = inline_title
            pending_title = ""
            continue

        m_num = _NUMBERED_HEADING.match(line)
        if m_num:
            _flush()
            current = {}
            pending_title = m_num.group(1).strip()
            continue

        m_id = _ID_FIELD.match(line)
        if m_id and pending_title and not current.get("id"):
            current["id"] = m_id.group(1)
            current.setdefault("title", pending_title)
            pending_title = ""
            continue

        if current.get("id"):
            m_field = _FIELD_LINE.match(line)
            if m_field:
                key = m_field.group(1).strip().lower()
                val = m_field.group(2).strip()
                if key not in ("id",):
                    current.setdefault(key, val)
            elif line.strip() and not line.startswith("#"):
                # Plain paragraph text after the heading — capture as description
                # (e.g. '## REQ-001: Title\nThe system SHALL...')
                current.setdefault("description", line.strip())

    _flush()
    return [
        {
            "id": r["id"],
            "version": 1,
            "title": r.get("title", r["id"]),
            "description": r.get("description", ""),
            "source": r.get("source", "docs/REQUIREMENTS.md"),
            "status": r.get("status", "defined"),
        }
        for r in records
    ]


def parse_tests_md(text: str) -> list[dict[str, Any]]:
    """Parse TESTS.md and return a list of test case records."""
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    pending_title: str = ""

    def _flush() -> None:
        if current.get("id"):
            records.append(dict(current))

    for line in text.splitlines():
        # TEST-NNN heading or numbered-style
        m_test_heading = re.match(r"^#{1,3}\s+(" + _FLEX_TEST_ID + r")(?:\.\s+(.+?))?\s*$", line)
        if m_test_heading:
            _flush()
            current = {
                "id": m_test_heading.group(1),
                "title": (m_test_heading.group(2) or "").strip(),
            }
            pending_title = ""
            continue

        # Numbered-style heading without TEST- prefix
        m_num = _NUMBERED_HEADING.match(line)
        if m_num and not re.match(r"#{1,3}\s+TEST-", line):
            _flush()
            current = {}
            pending_title = m_num.group(1).strip()
            continue

        # Inline ID field (resolves numbered heading)
        m_id = _TEST_ID_FIELD.match(line)
        if m_id and pending_title and not current.get("id"):
            current["id"] = m_id.group(1)
            current.setdefault("title", pending_title)
            pending_title = ""
            continue

        if current.get("id"):
            m_field = _FIELD_LINE.match(line)
            if m_field:
                key = m_field.group(1).strip().lower()
                val = m_field.group(2).strip()
                if key not in ("id",):
                    current.setdefault(key, val)

    _flush()
    return [
        {
            "id": r["id"],
            "version": 1,
            "title": r.get("title", r["id"]),
            "description": r.get("description", ""),
            "requirement_id": r.get("requirement id", r.get("requirement_id", "")),
            "type": r.get("type", "unit"),
            "verification_method": r.get(
                "verification method", r.get("verification_method", "evaluator")
            ),
            "input": {},
            "expected_behavior": {},
            "confidence": 1.0,
        }
        for r in records
    ]


# ---------------------------------------------------------------------------
# Sync result
# ---------------------------------------------------------------------------


@dataclass
class SyncResult:
    reqs_before: int
    reqs_after: int
    tests_before: int
    tests_after: int
    reqs_changed: bool
    tests_changed: bool
    dry_run: bool

    @property
    def changed(self) -> bool:
        return self.reqs_changed or self.tests_changed

    @property
    def message(self) -> str:
        status = "would update" if self.dry_run else "synced"
        parts: list[str] = []
        if self.reqs_changed:
            parts.append(f"requirements.json: {self.reqs_before} → {self.reqs_after} entries")
        if self.tests_changed:
            parts.append(f"testcases.json: {self.tests_before} → {self.tests_after} entries")
        if parts:
            return f"Machine state {status}: " + "; ".join(parts)
        return "Machine state already in sync."


# ---------------------------------------------------------------------------
# ESDB legacy policy normalization (.gitignore)
# ---------------------------------------------------------------------------

_ESDB_GITIGNORE_FORBIDDEN = frozenset(
    {
        ".specsmith/",
        ".chronomemory/",
    }
)

# DEPRECATED(REQ-421): several entries below (workitems.json, ledger.jsonl,
# trace.jsonl, esdb_migration_manifest.json, sessions/) are legacy flat files kept
# ignored until their teardown REQs land. The policy keeps canonical ESDB state
# (esdb.sqlite3, .chronomemory/*) tracked. See docs/DEPRECATIONS.md.
_ESDB_GITIGNORE_REQUIRED = (
    "!.specsmith/config.yml",
    "!.specsmith/requirements.json",
    "!.specsmith/testcases.json",
    "!.specsmith/esdb.sqlite3",
    "!.chronomemory/events.wal",
    "!.chronomemory/snapshot.json",
    ".chronomemory/backup/",
    ".specsmith/workitems.json",
    ".specsmith/runs/",
    ".specsmith/chat/",
    ".specsmith/perf/",
    ".specsmith/recovery/",
    ".specsmith/ledger.jsonl",
    ".specsmith/ledger-chain.txt",
    ".specsmith/trace.jsonl",
    ".specsmith/credit-budget.json",
    ".specsmith/credits.json",
    ".specsmith/model-rate-limits.json",
    ".specsmith/pids/",
    ".specsmith/logs/",
    ".specsmith/sessions/",
    ".specsmith/agent-reports/",
    ".specsmith/dispatch/",
    ".specsmith/esdb_migration_manifest.json",
)


def normalize_esdb_gitignore_policy(root: Path, *, dry_run: bool = False) -> bool:
    """Normalize ESDB gitignore policy for legacy projects.

    Ensures broad ignores that hide canonical ESDB state are removed and that
    explicit policy lines are present so SQLite/Chrono canonical artifacts are
    always tracked while runtime files stay ignored.
    """
    gitignore_path = root / ".gitignore"
    if gitignore_path.exists():
        original_lines = gitignore_path.read_text(encoding="utf-8").splitlines()
    else:
        original_lines = []

    normalized_lines: list[str] = []
    removed_forbidden = False
    for line in original_lines:
        if line.strip() in _ESDB_GITIGNORE_FORBIDDEN:
            removed_forbidden = True
            continue
        normalized_lines.append(line)

    existing = {line.strip() for line in normalized_lines if line.strip()}
    missing = [entry for entry in _ESDB_GITIGNORE_REQUIRED if entry not in existing]
    changed = removed_forbidden or bool(missing)

    if not changed:
        return False

    if normalized_lines and normalized_lines[-1].strip():
        normalized_lines.append("")
    if missing:
        normalized_lines.append("# specsmith ESDB policy (auto-normalized)")
        normalized_lines.extend(missing)

    if not dry_run:
        rendered = "\n".join(normalized_lines)
        if rendered and not rendered.endswith("\n"):
            rendered += "\n"
        gitignore_path.write_text(rendered, encoding="utf-8")

    return True


# ---------------------------------------------------------------------------
# Core sync
# ---------------------------------------------------------------------------


def run_sync(root: Path, *, dry_run: bool = False) -> SyncResult:
    """Regenerate .specsmith/requirements.json and testcases.json from governance sources.

    In YAML-first mode (governance-mode == "yaml"):
      1. Reads docs/requirements/*.yml and docs/tests/*.yml
      2. Writes .specsmith/requirements.json and testcases.json
      3. Regenerates docs/REQUIREMENTS.md and docs/TESTS.md as artifacts

    In legacy Markdown mode:
      1. Reads docs/REQUIREMENTS.md and docs/TESTS.md
      2. Writes .specsmith/requirements.json and testcases.json

    Args:
        root:    Project root directory.
        dry_run: If True, compute the diff but do not write anything.

    Returns:
        A :class:`SyncResult` describing what changed.
    """
    from specsmith.governance_yaml import (
        is_yaml_mode,
        load_yaml_requirements,
        load_yaml_tests,
    )

    state_dir = root / ".specsmith"
    reqs_md_path = root / "docs" / "REQUIREMENTS.md"
    tests_md_path = root / "docs" / "TESTS.md"
    reqs_json_path = state_dir / "requirements.json"
    tests_json_path = state_dir / "testcases.json"
    if not dry_run:
        normalize_esdb_gitignore_policy(root)

    if is_yaml_mode(root):
        # ── YAML-first mode ─────────────────────────────────────────────────
        new_reqs = load_yaml_requirements(root)
        new_tests = load_yaml_tests(root)

        # REQ-358: If YAML mode has no YAML files but REQUIREMENTS.md has content,
        # fall back to Markdown parsing rather than silently producing an empty state.
        if not new_reqs and reqs_md_path.exists():
            _md_text = reqs_md_path.read_text(encoding="utf-8")
            import re as _re

            if len(_re.findall(r"REQ-[A-Z0-9-]+", _md_text)) >= 5:
                new_reqs = parse_requirements_md(_md_text)

        if not new_tests and tests_md_path.exists():
            new_tests = parse_tests_md(tests_md_path.read_text(encoding="utf-8"))

        # Normalise to the same schema that the Markdown path produces
        # Build req_id → [test_ids] map from the loaded tests so requirements.json
        # includes test_ids for audit coverage checks (#147).
        _req_to_tests: dict[str, list[str]] = {}
        for _t in new_tests:
            _rid = str(_t.get("requirement_id", ""))
            _tid = str(_t.get("id", ""))
            if _rid and _tid:
                _req_to_tests.setdefault(_rid, []).append(_tid)

        new_reqs = [
            {
                "id": r["id"],
                "version": int(r.get("version", 1) or 1),
                "title": r.get("title", r["id"]),
                "description": str(r.get("description", "")),
                "source": r.get("source", "docs/requirements/"),
                "status": str(r.get("status", "defined")),
                "test_ids": _req_to_tests.get(r["id"], []),
                # Epistemic metadata — passed through from YAML so that
                # generate_requirements_md renders them into REQUIREMENTS.md
                # and belief.py can parse Platform/Boundary/Confidence fields.
                **({"platform": str(r["platform"])} if r.get("platform") else {}),
                **({"boundary": str(r["boundary"])} if r.get("boundary") else {}),
                **({"confidence": str(r["confidence"])} if r.get("confidence") else {}),
            }
            for r in new_reqs
        ]
        new_tests = [
            {
                "id": t["id"],
                "version": int(t.get("version", 1) or 1),
                "title": t.get("title", t["id"]),
                "description": str(t.get("description", "")),
                "requirement_id": str(t.get("requirement_id", "")),
                "type": str(t.get("type", "unit")),
                "verification_method": str(t.get("verification_method", "evaluator")),
                "input": t.get("input") or {},
                "expected_behavior": t.get("expected_behavior") or {},
                "confidence": float(t.get("confidence", 1.0)),
            }
            for t in new_tests
        ]
    else:
        # ── Legacy Markdown mode (DEPRECATED — REQ-373) ──────────────────────
        # Markdown mode will be removed in a future release.
        # Run 'specsmith migrate run' to upgrade to YAML-first mode.
        import warnings as _warnings

        _warnings.warn(
            "specsmith: markdown governance mode is deprecated. "
            "Run 'specsmith migrate run' to migrate to YAML-first mode. "
            "Markdown mode will be removed in a future release.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Auto-trigger m007 migration (idempotent, non-destructive)
        import contextlib as _cl

        with _cl.suppress(Exception):
            from specsmith.migrations.m007_yaml_first import YamlFirstMigration as _M007
            from specsmith.migrations.runner import MigrationRunner as _MR

            _applied = _MR(root).applied_versions()
            if 7 not in _applied and not dry_run:
                _m007_result = _M007().run(root)
                if _m007_result.success and is_yaml_mode(root):
                    # Successfully migrated — restart sync in YAML mode
                    return run_sync(root, dry_run=dry_run)

        new_reqs = []
        if reqs_md_path.exists():
            # DEPRECATED: reads REQUIREMENTS.md — migrate to YAML-first mode
            new_reqs = parse_requirements_md(reqs_md_path.read_text(encoding="utf-8"))

        new_tests = []
        if tests_md_path.exists():
            # DEPRECATED: reads TESTS.md — migrate to YAML-first mode
            new_tests = parse_tests_md(tests_md_path.read_text(encoding="utf-8"))

        # Inject test_ids into requirements even in Markdown mode (#147)
        _req_to_tests_md: dict[str, list[str]] = {}
        for _t in new_tests:
            _rid = str(_t.get("requirement_id", ""))
            _tid = str(_t.get("id", ""))
            if _rid and _tid:
                _req_to_tests_md.setdefault(_rid, []).append(_tid)
        for _r in new_reqs:
            if "test_ids" not in _r:
                _r["test_ids"] = _req_to_tests_md.get(_r["id"], [])

    # Placeholder so the variable is always defined for the merge step below
    new_reqs_obj: list[dict[str, Any]] = new_reqs
    new_tests_obj: list[dict[str, Any]] = new_tests

    # Load existing JSON for comparison (and to preserve hand-crafted fields)
    old_reqs: list[dict[str, Any]] = []
    if reqs_json_path.exists():
        with contextlib.suppress(OSError, ValueError):
            old_reqs = json.loads(reqs_json_path.read_text(encoding="utf-8"))

    old_tests: list[dict[str, Any]] = []
    existing_test_map: dict[str, dict[str, Any]] = {}
    if tests_json_path.exists():
        with contextlib.suppress(OSError, ValueError):
            old_tests = json.loads(tests_json_path.read_text(encoding="utf-8"))
            existing_test_map = {t["id"]: t for t in old_tests if isinstance(t, dict)}

    # Merge: preserve existing input/expected_behavior for tests that already
    # have hand-crafted content so we don't clobber kairos-style detailed specs.
    for tc in new_tests_obj:
        existing = existing_test_map.get(tc["id"], {})
        if existing.get("input"):
            tc["input"] = existing["input"]
        if existing.get("expected_behavior"):
            tc["expected_behavior"] = existing["expected_behavior"]

    # Detect drift (compare by serialising to canonical JSON)
    reqs_before = len(old_reqs)
    tests_before = len(old_tests)
    reqs_changed = json.dumps(new_reqs_obj, sort_keys=True) != json.dumps(old_reqs, sort_keys=True)
    tests_changed = json.dumps(new_tests_obj, sort_keys=True) != json.dumps(
        old_tests, sort_keys=True
    )

    if not dry_run:
        state_dir.mkdir(parents=True, exist_ok=True)
        # DEPRECATED(REQ-421): ``.specsmith/requirements.json`` and ``testcases.json``
        # are a regeneratable cache of docs/requirements/*.yml + docs/tests/*.yml,
        # mirrored into ESDB by _sync_esdb below. REQ-424 will stop writing this JSON
        # cache once all projects read governance from ESDB. See docs/DEPRECATIONS.md.
        if reqs_changed:
            reqs_json_path.write_text(
                json.dumps(new_reqs_obj, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        if tests_changed:
            tests_json_path.write_text(
                json.dumps(new_tests_obj, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        # docs/REQUIREMENTS.md and docs/TESTS.md are deprecated in YAML-first mode.
        # They are no longer regenerated; edit docs/requirements/*.yml instead.

        # ── ESDB sync (best-effort — never blocks sync on ESDB failure) ────────
        # Keep ChronoStore in sync with JSON so ESDB is never stale.
        # Only runs when .chronomemory/events.wal exists (i.e. migrate was run).
        if reqs_changed or tests_changed:
            _sync_esdb(root, state_dir)

    return SyncResult(
        reqs_before=reqs_before,
        reqs_after=len(new_reqs_obj),
        tests_before=tests_before,
        tests_after=len(new_tests_obj),
        reqs_changed=reqs_changed,
        tests_changed=tests_changed,
        dry_run=dry_run,
    )


def _sync_esdb(root: Path, state_dir: Path) -> None:
    """Upsert all current requirements and testcases into ChronoStore.

    This is called automatically by :func:`run_sync` after the JSON cache is
    updated, keeping the audit trail in sync without requiring a separate
    ``specsmith migrate`` invocation.

    Design invariants:
    - Idempotent: re-running upserts the same data with no side effects.
    - Non-blocking: any exception is swallowed so sync never fails on ESDB.
    - Status mapping: governance status (defined/implemented) → ESDB status
      (active/deprecated) via ChronoStore._governance_to_esdb_status.
    - ESDB is an audit trail, not a source of truth.  The JSON files remain
      the authoritative machine state.
    """
    wal_path = root / ".chronomemory" / "events.wal"
    if not wal_path.exists():
        return  # ESDB not initialised for this project yet

    try:
        from chronomemory import ChronoRecord, ChronoStore

        store = ChronoStore(root).open()
        _map = ChronoStore._governance_to_esdb_status

        for filename, kind in [
            (state_dir / "requirements.json", "requirement"),
            (state_dir / "testcases.json", "testcase"),
        ]:
            if not filename.is_file():
                continue
            try:
                items = json.loads(filename.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue

            for item in items:
                if not isinstance(item, dict) or not item.get("id"):
                    continue
                rec_id = item["id"]
                esdb_status = _map(item.get("status", "active"))
                label = item.get("title", "")
                confidence = float(item.get("confidence", 0.7 if kind == "requirement" else 1.0))

                # Skip if nothing changed
                existing = store.get(rec_id)
                if (
                    existing is not None
                    and existing.label == label
                    and existing.status == esdb_status
                    and existing.confidence == confidence
                ):
                    continue

                store.upsert(
                    ChronoRecord(
                        id=rec_id,
                        kind=kind,
                        label=label,
                        status=esdb_status,
                        confidence=confidence,
                        source_type="observed",
                        evidence=[f"synced from {filename.name}"],
                        data=item,
                    )
                )
        store.close()
    except Exception:  # noqa: BLE001 — ESDB sync is always best-effort
        pass


def _json_file_has_content(path: Path) -> bool:
    """Return True when *path* exists and contains a non-empty JSON list.

    Falls back to a small size heuristic for malformed JSON so we still treat
    legacy state files with obvious content as migratable.
    """
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return isinstance(payload, list) and len(payload) > 0
    except (OSError, ValueError):
        with contextlib.suppress(OSError):
            return path.stat().st_size > 2
        return False


def _should_auto_migrate(store: Any, specsmith_dir: Path) -> bool:
    """Return True when ESDB is empty and legacy JSON sources have content.

    This is used by CLI surfaces (`sync`, `audit`, `esdb status`) to
    opportunistically bootstrap ESDB from `.specsmith/*.json` exactly once.
    """
    if store.record_count() > 0:
        return False
    candidates = (
        specsmith_dir / "requirements.json",
        specsmith_dir / "testcases.json",
    )
    return any(_json_file_has_content(path) for path in candidates)


def auto_migrate_if_needed(root: Path) -> dict[str, int]:
    """Best-effort ESDB bootstrap from legacy JSON when the store is empty.

    Returns migration counts on success, or an empty dict when no migration was
    needed or if any backend error occurred.
    """
    from specsmith.esdb import open_default_store

    specsmith_dir = root / ".specsmith"
    if not specsmith_dir.exists():
        return {}

    class _MigratableStore(Protocol):
        def record_count(self) -> int:
            pass  # noqa: E704

        def migrate_from_json(self, specsmith_dir: Path) -> dict[str, int] | Any:
            pass  # noqa: E704

    try:
        with open_default_store(root, warn=False) as store:
            typed_store = cast(_MigratableStore, store)
            if not _should_auto_migrate(typed_store, specsmith_dir):
                return {}
            counts = typed_store.migrate_from_json(specsmith_dir)
            if isinstance(counts, dict):
                return {
                    "requirements": int(counts.get("requirements", 0)),
                    "testcases": int(counts.get("testcases", 0)),
                    "skipped": int(counts.get("skipped", 0)),
                }
            return {}
    except Exception:  # noqa: BLE001 - never block caller commands
        return {}


def check_sync(root: Path) -> SyncResult:
    """Check whether machine state is in sync without writing anything.

    Convenience wrapper around :func:`run_sync` with ``dry_run=True``.
    Used by :func:`specsmith.auditor.run_audit` to surface sync drift warnings.
    """
    return run_sync(root, dry_run=True)
