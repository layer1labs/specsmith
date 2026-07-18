import pytest

from specsmith.esdb.replicated_events import (
    EventConflictError,
    ReplicatedEvent,
    ReplicatedEventSet,
)


def _event(event_id, payload, parents=(), replica="r1"):
    return ReplicatedEvent(event_id, "REQ-1", payload, parents, "actor", "agent", replica, "s")


def test_union_and_materialization_are_order_independent() -> None:
    first = ReplicatedEventSet((_event("a", {"v": 1}),))
    second = ReplicatedEventSet((_event("b", {"v": 2}, ("a",), "r2"),))
    left = first.union(second)
    right = second.union(first)
    assert left.canonical_root == right.canonical_root
    assert left.materialize().records == {"REQ-1": {"v": 2}}


def test_concurrent_edits_are_explicit_and_block_authoritative_reads() -> None:
    merged = ReplicatedEventSet((_event("a", {"v": 1}), _event("b", {"v": 2}, replica="r2")))
    state = merged.materialize()
    assert state.conflicts == {"REQ-1": ("a", "b")}
    with pytest.raises(EventConflictError, match="unresolved"):
        state.get_authoritative("REQ-1")


def test_event_collision_and_legacy_chain_evidence() -> None:
    event = _event("a", {"v": 1})
    events = ReplicatedEventSet((event,))
    with pytest.raises(EventConflictError, match="collision"):
        events.add(_event("a", {"v": 2}))
    legacy = ReplicatedEvent("legacy", "X", {}, (), "a", "g", "r", "s", legacy_chain_hash="abc")
    assert legacy.canonical()["legacy_chain_hash"] == "abc"
