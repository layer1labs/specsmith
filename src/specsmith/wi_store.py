# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""specsmith.wi_store — Work Item lifecycle storage and state management.

Work Items (WIs) are the atomic governance units created by ``specsmith preflight``
when a change is accepted.  Every WI has a full lifecycle:

    open → implemented → promoted   (WI elevated to a formal REQ-NNN)
         ↘ closed                  (done; matched existing REQ; no new REQ needed)
         ↘ archived                (abandoned / deferred)
         ↘ rejected                (explicitly refused)

State machine invariants:
- Only ``open`` WIs may transition to ``implemented``.
- Only ``implemented`` WIs may be ``promoted`` or ``closed``.
- ``archived`` and ``rejected`` are terminal; ``promoted``/``closed`` are also terminal.
- ``promoted`` WIs carry a ``promoted_to_req`` field linking to the new REQ-NNN.

Storage: ``.specsmith/workitems.json``  — a JSON array of WorkItem dicts.
This file is the machine-readable source of truth; LEDGER.md holds the
human-readable audit trail via ``work_proposal`` entries.

DEPRECATED(REQ-421): the ``workitems.json`` flat file is slated for teardown.
Every mutation is already mirrored into the ESDB ``work_item`` kind via
``WorkItemStore._sync_to_esdb`` (REQ-398); REQ-423 will make ESDB the source of
truth and drop this file. See docs/DEPRECATIONS.md.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# DEPRECATED(REQ-421): legacy flat-file cache; superseded by the ESDB ``work_item``
# kind (REQ-398 dual-write today, REQ-423 ESDB-first teardown). See docs/DEPRECATIONS.md.
_WORKITEMS_FILE = "workitems.json"

#: Valid WI lifecycle states (ordered from youngest to oldest).
WI_STATES: tuple[str, ...] = (
    "open",
    "implemented",
    "promoted",
    "closed",
    "archived",
    "rejected",
)

#: Valid WI kind / classification labels.
WI_KINDS: tuple[str, ...] = (
    "feature",
    "bug",
    "chore",
    "spike",
    "refactor",
    "docs",
)

#: Terminal states — no further transitions allowed.
WI_TERMINAL_STATES: frozenset[str] = frozenset({"promoted", "closed", "archived", "rejected"})

#: Allowed transitions: {from_state: {to_state, ...}}
WI_TRANSITIONS: dict[str, frozenset[str]] = {
    "open": frozenset({"implemented", "archived", "rejected"}),
    "implemented": frozenset({"promoted", "closed", "archived"}),
    "promoted": frozenset(),
    "closed": frozenset(),
    "archived": frozenset({"open"}),  # un-defer is allowed
    "rejected": frozenset(),
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class WorkItem:
    """A single Work Item record.

    Fields mirror the JSON schema stored in ``.specsmith/workitems.json``.
    """

    #: ``WI-XXXXXXXX`` — 8-hex-digit identifier minted by ``specsmith preflight``.
    id: str

    #: Current lifecycle state.  One of :data:`WI_STATES`.
    status: str = "open"

    #: Classification label.  One of :data:`WI_KINDS`.
    kind: str = "feature"

    #: Natural-language intent string from the accepted preflight utterance.
    intent: str = ""

    #: ISO-8601 UTC creation timestamp.
    created_at: str = ""

    #: ISO-8601 UTC last-update timestamp.
    updated_at: str = ""

    #: Requirement IDs matched at preflight time.
    requirement_ids: list[str] = field(default_factory=list)

    #: Test case IDs matched at preflight time.
    test_case_ids: list[str] = field(default_factory=list)

    #: REQ-NNN set when this WI is promoted to a formal requirement.
    promoted_to_req: str = ""

    #: ISO-8601 UTC timestamp when the WI moved to a terminal state.
    closed_at: str = ""

    #: Human-readable reason for closing/archiving/rejecting.
    closed_reason: str = ""

    #: Confidence target from the accepted preflight payload.
    confidence_target: float = 0.85

    #: True once ``specsmith verify`` has reached equilibrium for this WI.
    verified: bool = False

    #: Optional list of files touched by the implementation.
    files_touched: list[str] = field(default_factory=list)

    #: Optional blast-radius hint: local | service | subsystem | global.
    blast_radius_estimate: str = ""

    #: Optional agent confidence signal (0.0 - 1.0).
    agent_confidence: float = 0.0

    #: Human review status marker.
    human_review_status: str = "pending"

    #: Optional manual risk override.
    risk_override_level: str = ""
    risk_override_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkItem:
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})

    def can_transition_to(self, new_status: str) -> bool:
        """Return True if the transition ``self.status → new_status`` is allowed."""
        return new_status in WI_TRANSITIONS.get(self.status, frozenset())

    def is_terminal(self) -> bool:
        return self.status in WI_TERMINAL_STATES


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------


class WorkItemError(RuntimeError):
    """Raised for invalid WI operations."""


class WorkItemStore:
    """CRUD + lifecycle store for Work Items.

    Usage::

        store = WorkItemStore(project_root)
        store.create("WI-3A9F1C02", intent="add retry logic", requirement_ids=["REQ-042"])
        store.mark_implemented("WI-3A9F1C02")
        store.promote_to_req("WI-3A9F1C02", "REQ-367")
        items = store.list_by_status("open")
    """

    def __init__(self, project_root: str | Path) -> None:
        # os.path.realpath is the CodeQL-recognised sanitiser for py/path-injection.
        # Path.resolve() is NOT tracked by CodeQL's taint model — always use
        # os.path.realpath for paths originating from caller/user input.
        root = os.path.realpath(str(project_root))
        state_dir = os.path.realpath(os.path.join(root, ".specsmith"))
        path = os.path.realpath(os.path.join(state_dir, _WORKITEMS_FILE))
        if state_dir != root and not state_dir.startswith(root + os.sep):
            raise WorkItemError(f"Work-item state escapes project root: {state_dir!r}")
        if not path.startswith(state_dir + os.sep):
            raise WorkItemError(f"Work-item file escapes state directory: {path!r}")
        self._root = Path(root)
        self._path = Path(path)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self) -> list[WorkItem]:
        """Load all WIs from disk.  Returns [] when the file does not exist."""
        if not self._path.is_file():
            return []
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                return []
            return [WorkItem.from_dict(r) for r in raw if isinstance(r, dict) and r.get("id")]
        except (OSError, ValueError, TypeError):
            return []

    def save(self, items: list[WorkItem]) -> None:
        """Write *items* to disk atomically (write-to-tmp-then-rename)."""
        # DEPRECATED(REQ-421): writes the legacy ``.specsmith/workitems.json``.
        # ESDB ``work_item`` records are the forward store (see _sync_to_esdb);
        # this writer is retained until REQ-423 flips ESDB to source of truth.
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps([it.to_dict() for it in items], indent=2, ensure_ascii=False)
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(self._path)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get(self, wi_id: str) -> WorkItem | None:
        """Return the WI with *wi_id*, or None."""
        for item in self.load():
            if item.id == wi_id:
                return item
        return None

    def list_by_status(self, status: str | None = None) -> list[WorkItem]:
        """Return all WIs, optionally filtered by *status*."""
        items = self.load()
        if status is None:
            return items
        return [i for i in items if i.status == status]

    def all_open(self) -> list[WorkItem]:
        return self.list_by_status("open")

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def upsert(self, item: WorkItem) -> None:
        """Insert or update a WI by ID."""
        items = self.load()
        for idx, existing in enumerate(items):
            if existing.id == item.id:
                items[idx] = item
                self.save(items)
                return
        items.append(item)
        self.save(items)

    def _sync_to_esdb(self, item: WorkItem) -> None:
        """Best-effort ESDB sync after any WI mutation (REQ-398).

        Never raises — ESDB is not on the critical path for WI operations.
        """
        try:
            from specsmith.esdb_writer import write_work_item_record

            write_work_item_record(self._root, item)
        except Exception:  # noqa: BLE001
            pass

    def create(
        self,
        wi_id: str,
        *,
        intent: str = "",
        requirement_ids: list[str] | None = None,
        test_case_ids: list[str] | None = None,
        confidence_target: float = 0.85,
        kind: str = "feature",
    ) -> WorkItem:
        """Create a new ``open`` WI.  Idempotent: returns existing record if found."""
        existing = self.get(wi_id)
        if existing is not None:
            return existing
        ts = _now_iso()
        item = WorkItem(
            id=wi_id,
            status="open",
            kind=kind,
            intent=intent,
            created_at=ts,
            updated_at=ts,
            requirement_ids=list(requirement_ids or []),
            test_case_ids=list(test_case_ids or []),
            confidence_target=confidence_target,
        )
        self.upsert(item)
        self._sync_to_esdb(item)
        return item

    def set_status(
        self,
        wi_id: str,
        new_status: str,
        *,
        reason: str = "",
        force: bool = False,
    ) -> WorkItem:
        """Transition *wi_id* to *new_status*.

        Raises :class:`WorkItemError` if the transition is not allowed unless
        ``force=True``.
        """
        if new_status not in WI_STATES:
            raise WorkItemError(f"Unknown status {new_status!r}. Valid: {WI_STATES}")
        item = self.get(wi_id)
        if item is None:
            raise WorkItemError(f"Work item {wi_id!r} not found.")
        if not force and not item.can_transition_to(new_status):
            raise WorkItemError(
                f"Cannot transition {wi_id} from {item.status!r} to {new_status!r}. "
                f"Allowed: {sorted(WI_TRANSITIONS.get(item.status, frozenset()))}",
            )
        ts = _now_iso()
        item.status = new_status
        item.updated_at = ts
        if new_status in WI_TERMINAL_STATES:
            item.closed_at = ts
            if reason:
                item.closed_reason = reason
        self.upsert(item)
        self._sync_to_esdb(item)
        return item

    def mark_implemented(self, wi_id: str) -> WorkItem | None:
        """Transition *wi_id* to ``implemented``.  No-op and returns None when WI is not found."""
        item = self.get(wi_id)
        if item is None:
            return None
        if item.status != "open":
            return item  # already progressed; silently skip
        item.status = "implemented"
        item.verified = True
        item.updated_at = _now_iso()
        self.upsert(item)
        self._sync_to_esdb(item)
        return item

    def set_files_touched(self, wi_id: str, files: list[str]) -> WorkItem | None:
        item = self.get(wi_id)
        if item is None:
            return None
        item.files_touched = list(files)
        item.updated_at = _now_iso()
        self.upsert(item)
        self._sync_to_esdb(item)
        return item

    def add_test_case_ids(self, wi_id: str, test_ids: list[str]) -> WorkItem | None:
        """Append *test_ids* to the WI's test_case_ids list (deduplicating)."""
        item = self.get(wi_id)
        if item is None:
            return None
        existing = set(item.test_case_ids)
        for tid in test_ids:
            if tid not in existing:
                item.test_case_ids.append(tid)
                existing.add(tid)
        item.updated_at = _now_iso()
        self.upsert(item)
        self._sync_to_esdb(item)
        return item

    def promote_to_req(self, wi_id: str, req_id: str) -> WorkItem:
        """Record that *wi_id* has been promoted to *req_id*.

        Transitions the WI to ``promoted`` and writes the REQ link.
        """
        item = self.get(wi_id)
        if item is None:
            raise WorkItemError(f"Work item {wi_id!r} not found.")
        if item.status not in ("open", "implemented"):
            if item.status == "promoted":
                return item  # idempotent
            raise WorkItemError(
                f"Cannot promote {wi_id}: currently in terminal state {item.status!r}.",
            )
        ts = _now_iso()
        item.status = "promoted"
        item.promoted_to_req = req_id
        item.closed_at = ts
        item.updated_at = ts
        self.upsert(item)
        self._sync_to_esdb(item)
        return item

    def tag(self, wi_id: str, kind: str) -> WorkItem:
        """Set the *kind* label on *wi_id*."""
        if kind not in WI_KINDS:
            raise WorkItemError(f"Unknown kind {kind!r}. Valid: {WI_KINDS}")
        item = self.get(wi_id)
        if item is None:
            raise WorkItemError(f"Work item {wi_id!r} not found.")
        item.kind = kind
        item.updated_at = _now_iso()
        self.upsert(item)
        return item

    def import_from_ledger(self, ledger_path: Path) -> int:
        """Parse LEDGER.md for ``work_proposal`` entries and import missing WIs.

        Returns the count of newly imported WIs.
        """
        import re

        if not ledger_path.is_file():
            return 0
        text = ledger_path.read_text(encoding="utf-8", errors="ignore")
        # Match lines like: work_proposal WI-3A9F1C02: <intent>
        pattern = re.compile(r"work_proposal\s+(WI-[A-F0-9]{8})[:\s]+(.{0,200})", re.IGNORECASE)
        imported = 0
        for match in pattern.finditer(text):
            wi_id = match.group(1).upper()
            intent = match.group(2).strip()
            existing = self.get(wi_id)
            if existing is None:
                self.create(wi_id, intent=intent)
                imported += 1
        return imported


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
