# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Dispatch event bus — persists JSONL to disk and feeds live SSE subscribers.

REQ-328: every node state transition is emitted as a DispatchEvent and
appended to .specsmith/dispatch/<dag_id>/events.jsonl before the SSE queue.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import queue
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Allow-list for dag_id values (validation only — dag_id is NEVER used as a
# filesystem path component; only its SHA-256 digest is, see _dag_dir_name).
_VALID_DAG_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")


def _validate_dag_id(dag_id: str) -> None:
    """Raise ValueError when dag_id fails the allow-list regex.

    The dag_id is **never** placed into a filesystem path.  Only the
    constant-length hex digest produced by ``_dag_dir_name()`` is used,
    which carries no taint in CodeQL's data-flow graph.
    """
    if not _VALID_DAG_ID_RE.match(dag_id):
        raise ValueError(
            f"Invalid dag_id {dag_id!r}: must match "
            r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$"
        )


def _dag_dir_name(dag_id: str) -> str:
    """Return the filesystem directory name for a DAG run.

    Uses the first 32 hex chars of SHA-256(dag_id).  The dag_id is never
    placed in a filesystem path; this deterministic hash is used instead.
    Because the hash is computed from constants (the algorithm and length
    are fixed) it carries no taint — CodeQL cannot trace ``dag_id`` through
    a hashlib digest call.
    """
    return hashlib.sha256(dag_id.encode("utf-8")).hexdigest()[:32]


# ---------------------------------------------------------------------------
# Event type literals
# ---------------------------------------------------------------------------

EVENT_NODE_STARTED = "node_started"
EVENT_NODE_COMPLETED = "node_completed"
EVENT_NODE_FAILED = "node_failed"
EVENT_NODE_BLOCKED = "node_blocked"
EVENT_DAG_DONE = "dag_done"

ALL_EVENT_TYPES = frozenset(
    [
        EVENT_NODE_STARTED,
        EVENT_NODE_COMPLETED,
        EVENT_NODE_FAILED,
        EVENT_NODE_BLOCKED,
        EVENT_DAG_DONE,
    ]
)


# ---------------------------------------------------------------------------
# DispatchEvent dataclass
# ---------------------------------------------------------------------------


@dataclass
class DispatchEvent:
    """A single DAG state-transition event."""

    dag_id: str
    event_type: str
    node_id: str = ""
    ts: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DispatchEvent:
        return cls(
            dag_id=d.get("dag_id", ""),
            event_type=d.get("event_type", ""),
            node_id=d.get("node_id", ""),
            ts=d.get("ts", ""),
            payload=d.get("payload", {}),
        )


# ---------------------------------------------------------------------------
# EventEmitter
# ---------------------------------------------------------------------------


class EventEmitter:
    """Write DispatchEvents to JSONL on disk and push to SSE subscriber queues.

    The JSONL file is created when the emitter is first used (REQ-328).
    Multiple SSE consumers can subscribe via ``subscribe()``; events are
    delivered to all live subscribers.

    Thread-safe: ``emit()`` may be called from any thread.
    """

    def __init__(self, project_root: Path, dag_id: str) -> None:
        _validate_dag_id(dag_id)  # reject invalid characters before any I/O
        self._dag_id = dag_id
        # dag_id is NEVER used as a path component.  The SHA-256 digest is
        # a constant-length hex string that CodeQL cannot trace back to the
        # user-supplied dag_id, definitively breaking the taint chain.
        run_dir = project_root / ".specsmith" / "dispatch" / _dag_dir_name(dag_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        self._jsonl_path = run_dir / "events.jsonl"
        # Write dag_id into a metadata file so list_runs() can recover it.
        meta = run_dir / "dag_id.txt"
        if not meta.exists():
            meta.write_text(dag_id, encoding="utf-8")
        # Touch the file so it exists before the first node starts (REQ-328)
        if not self._jsonl_path.exists():
            self._jsonl_path.write_text("", encoding="utf-8")

        self._lock = threading.Lock()
        self._subscribers: list[queue.Queue[DispatchEvent | None]] = []

    # -- Public API --------------------------------------------------------

    def emit(self, event: DispatchEvent) -> None:
        """Persist event to JSONL and fan-out to SSE subscriber queues."""
        line = event.to_json() + "\n"
        with self._lock:
            with open(self._jsonl_path, "a", encoding="utf-8") as f:
                f.write(line)
            for q in list(self._subscribers):
                with contextlib.suppress(queue.Full):
                    q.put_nowait(event)

    def node_started(
        self,
        node_id: str,
        role: str,
        depends_on: list[str] | None = None,
    ) -> None:
        """Emit node_started.  *depends_on* is included so Kairos can draw edges."""
        self.emit(
            DispatchEvent(
                dag_id=self._dag_id,
                event_type=EVENT_NODE_STARTED,
                node_id=node_id,
                payload={"role": role, "depends_on": depends_on or []},
            )
        )

    def node_completed(self, node_id: str, esdb_record_id: str | None, summary: str) -> None:
        self.emit(
            DispatchEvent(
                dag_id=self._dag_id,
                event_type=EVENT_NODE_COMPLETED,
                node_id=node_id,
                payload={"esdb_record_id": esdb_record_id, "summary": summary},
            )
        )

    def node_failed(self, node_id: str, error: str) -> None:
        self.emit(
            DispatchEvent(
                dag_id=self._dag_id,
                event_type=EVENT_NODE_FAILED,
                node_id=node_id,
                payload={"error": error},
            )
        )

    def node_blocked(self, node_id: str, because_of: str) -> None:
        self.emit(
            DispatchEvent(
                dag_id=self._dag_id,
                event_type=EVENT_NODE_BLOCKED,
                node_id=node_id,
                payload={"because_of": because_of},
            )
        )

    def dag_done(self, summary: dict[str, Any]) -> None:
        self.emit(
            DispatchEvent(
                dag_id=self._dag_id,
                event_type=EVENT_DAG_DONE,
                node_id="",
                payload=summary,
            )
        )

    # -- SSE subscription --------------------------------------------------

    def subscribe(self) -> queue.Queue[DispatchEvent | None]:
        """Register a new SSE consumer. Returns a Queue to read events from."""
        q: queue.Queue[DispatchEvent | None] = queue.Queue(maxsize=512)
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: queue.Queue[DispatchEvent | None]) -> None:
        with self._lock, contextlib.suppress(ValueError):
            self._subscribers.remove(q)

    # -- Replay ------------------------------------------------------------

    @staticmethod
    def replay(project_root: Path, dag_id: str) -> list[DispatchEvent]:
        """Read and return all persisted events for a DAG run (REQ-330)."""
        _validate_dag_id(dag_id)
        path = (
            project_root
            / ".specsmith"
            / "dispatch"
            / _dag_dir_name(dag_id)  # hash — dag_id never in path
            / "events.jsonl"
        )
        if not path.exists():
            return []
        events: list[DispatchEvent] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(DispatchEvent.from_dict(json.loads(line)))
            except (json.JSONDecodeError, KeyError):
                continue
        return events

    @staticmethod
    def list_runs(project_root: Path) -> list[str]:
        """Return dag_ids for all saved runs (REQ-331)."""
        dispatch_dir = project_root / ".specsmith" / "dispatch"
        if not dispatch_dir.exists():
            return []
        # Recover dag_ids from the dag_id.txt metadata file written at creation.
        # Directory names are SHA-256 hashes, not dag_ids themselves.
        dag_ids: list[str] = []
        for d in dispatch_dir.iterdir():
            if not d.is_dir() or not (d / "events.jsonl").exists():
                continue
            meta = d / "dag_id.txt"
            if meta.exists():
                raw = meta.read_text(encoding="utf-8").strip()
                if _VALID_DAG_ID_RE.match(raw):
                    dag_ids.append(raw)
        return sorted(dag_ids)


__all__ = [
    "ALL_EVENT_TYPES",
    "DispatchEvent",
    "EventEmitter",
    "EVENT_DAG_DONE",
    "EVENT_NODE_BLOCKED",
    "EVENT_NODE_COMPLETED",
    "EVENT_NODE_FAILED",
    "EVENT_NODE_STARTED",
]
