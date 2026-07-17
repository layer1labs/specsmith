"""Immutable replicated ESDB event sets with deterministic materialization."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


class EventConflictError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReplicatedEvent:
    event_id: str
    entity_id: str
    payload: dict[str, Any]
    parent_ids: tuple[str, ...]
    actor_id: str
    agent_id: str
    replica_id: str
    session_id: str
    operation: str = "upsert"
    legacy_chain_hash: str = ""

    def canonical(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "entity_id": self.entity_id,
            "payload": self.payload,
            "parent_ids": sorted(self.parent_ids),
            "actor_id": self.actor_id,
            "agent_id": self.agent_id,
            "replica_id": self.replica_id,
            "session_id": self.session_id,
            "operation": self.operation,
            "legacy_chain_hash": self.legacy_chain_hash,
        }

    @property
    def digest(self) -> str:
        raw = json.dumps(self.canonical(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()


@dataclass(frozen=True)
class MaterializedState:
    records: dict[str, dict[str, Any]]
    tombstones: frozenset[str]
    conflicts: dict[str, tuple[str, ...]]
    canonical_root: str

    def get_authoritative(self, entity_id: str) -> dict[str, Any] | None:
        if entity_id in self.conflicts:
            raise EventConflictError(f"unresolved ESDB conflict for {entity_id}")
        return self.records.get(entity_id)


class ReplicatedEventSet:
    def __init__(self, events: tuple[ReplicatedEvent, ...] = ()) -> None:
        self._events: dict[str, ReplicatedEvent] = {}
        for event in events:
            self.add(event)

    def add(self, event: ReplicatedEvent) -> None:
        existing = self._events.get(event.event_id)
        if existing and existing.digest != event.digest:
            raise EventConflictError(f"event ID collision for {event.event_id}")
        self._events[event.event_id] = event

    def union(self, other: ReplicatedEventSet) -> ReplicatedEventSet:
        merged = ReplicatedEventSet(tuple(self._events.values()))
        for event in other._events.values():
            merged.add(event)
        return merged

    @property
    def canonical_root(self) -> str:
        digests = "\n".join(sorted(event.digest for event in self._events.values()))
        return hashlib.sha256(digests.encode()).hexdigest()

    def materialize(self) -> MaterializedState:
        by_entity: dict[str, list[ReplicatedEvent]] = {}
        parent_ids = {parent for event in self._events.values() for parent in event.parent_ids}
        for event in self._events.values():
            by_entity.setdefault(event.entity_id, []).append(event)
        records: dict[str, dict[str, Any]] = {}
        tombstones: set[str] = set()
        conflicts: dict[str, tuple[str, ...]] = {}
        for entity_id, events in by_entity.items():
            frontier = sorted(
                (event for event in events if event.event_id not in parent_ids),
                key=lambda event: event.event_id,
            )
            unique = {(event.operation, event.digest) for event in frontier}
            if len(unique) > 1:
                conflicts[entity_id] = tuple(event.event_id for event in frontier)
                continue
            event = frontier[0]
            if event.operation == "delete":
                tombstones.add(entity_id)
            else:
                records[entity_id] = dict(event.payload)
        return MaterializedState(records, frozenset(tombstones), conflicts, self.canonical_root)

    def events(self) -> tuple[ReplicatedEvent, ...]:
        return tuple(sorted(self._events.values(), key=lambda event: event.event_id))
