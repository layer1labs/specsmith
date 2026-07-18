"""Deterministic context control, residency, health, and Zoo directives.

The module deliberately contains no model calls.  Zoo owns token telemetry and
applies directives; Specsmith owns the decision, packet, digest, and evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ContextState(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"


class ContextAction(str, Enum):
    CONTINUE = "continue"
    SEMANTIC_CHECKPOINT = "semantic_checkpoint"
    CHECKPOINT_AND_CONDENSE = "checkpoint_and_condense"
    SPAWN_FRESH_TASK = "spawn_fresh_task"
    BLOCKED_DEGRADED = "blocked_degraded"


@dataclass(frozen=True)
class ContextPolicy:
    yellow: float = 0.50
    orange: float = 0.65
    red: float = 0.78
    uncertainty: float = 0.25
    minimum_post_task_headroom: float = 0.20
    semantic_cooldown_turns: int = 4
    starvation_turns: int = 10
    material_event_limit: int = 5
    failed_attempt_limit: int = 3


@dataclass(frozen=True)
class ContextTelemetry:
    context_limit: int
    current_input: int
    output_reserve: int
    safety_reserve: int
    checkpoint_reserve: int = 0
    meaningful_turns_since_checkpoint: int = 0
    material_events_since_checkpoint: int = 0
    failed_attempts: int = 0
    turns_since_semantic_checkpoint: int = 99
    last_condensation_before: int | None = None
    last_condensation_after: int | None = None

    @property
    def usable_capacity(self) -> int:
        return max(1, self.context_limit - self.output_reserve - self.safety_reserve)

    @property
    def pressure(self) -> float:
        return self.current_input / self.usable_capacity

    @property
    def remaining_work_capacity(self) -> int:
        return max(
            0,
            self.context_limit
            - self.current_input
            - self.output_reserve
            - self.safety_reserve
            - self.checkpoint_reserve,
        )


@dataclass(frozen=True)
class TaskEnvelope:
    task_class: str
    expected_reasoning: int
    expected_reads: int
    expected_tool_output: int
    expected_verification: int
    uncertainty: float | None = None

    def tokens(self, default_uncertainty: float) -> int:
        base = (
            self.expected_reasoning
            + self.expected_reads
            + self.expected_tool_output
            + self.expected_verification
        )
        margin = default_uncertainty if self.uncertainty is None else self.uncertainty
        return int(base * (1 + margin))


@dataclass(frozen=True)
class ContextDecision:
    state: ContextState
    action: ContextAction
    task_tokens: int
    remaining_work_capacity: int
    post_task_headroom: int
    fits: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "action": self.action.value,
            "task_tokens": self.task_tokens,
            "remaining_work_capacity": self.remaining_work_capacity,
            "post_task_headroom": self.post_task_headroom,
            "fits": self.fits,
            "reasons": list(self.reasons),
        }


def decide_context_action(
    telemetry: ContextTelemetry,
    task: TaskEnvelope,
    *,
    policy: ContextPolicy | None = None,
    hard_boundary: bool = False,
    after_condensation: bool = False,
    checkpoint_integrity: bool = True,
) -> ContextDecision:
    """Return a deterministic, explainable task-fit and transition decision."""
    policy = policy or ContextPolicy()
    pressure = telemetry.pressure
    if pressure >= policy.red:
        state = ContextState.RED
    elif pressure >= policy.orange:
        state = ContextState.ORANGE
    elif pressure >= policy.yellow:
        state = ContextState.YELLOW
    else:
        state = ContextState.GREEN

    task_tokens = task.tokens(policy.uncertainty)
    required_headroom = int(telemetry.context_limit * policy.minimum_post_task_headroom)
    post_task = telemetry.remaining_work_capacity - task_tokens
    fits = post_task >= required_headroom
    reasons = [f"pressure={pressure:.3f}", f"task_class={task.task_class}"]

    if after_condensation and (not checkpoint_integrity or not fits):
        reasons.append("post-condensation capacity or checkpoint integrity is insufficient")
        action = ContextAction.SPAWN_FRESH_TASK
    elif state is ContextState.RED or not fits:
        reasons.append("task does not retain configured post-task headroom")
        action = ContextAction.CHECKPOINT_AND_CONDENSE
    elif hard_boundary:
        reasons.append("hard semantic boundary overrides cooldown")
        action = ContextAction.SEMANTIC_CHECKPOINT
    elif (
        telemetry.failed_attempts >= policy.failed_attempt_limit
        or telemetry.material_events_since_checkpoint >= policy.material_event_limit
        or telemetry.meaningful_turns_since_checkpoint >= policy.starvation_turns
    ) and telemetry.turns_since_semantic_checkpoint >= policy.semantic_cooldown_turns:
        reasons.append("semantic starvation or material-event threshold reached")
        action = ContextAction.SEMANTIC_CHECKPOINT
    elif state is ContextState.ORANGE:
        reasons.append("orange pressure requires a semantic checkpoint before non-trivial work")
        action = ContextAction.SEMANTIC_CHECKPOINT
    else:
        reasons.append("task fits; continue with deterministic micro-checkpoints")
        action = ContextAction.CONTINUE

    return ContextDecision(
        state=state,
        action=action,
        task_tokens=task_tokens,
        remaining_work_capacity=telemetry.remaining_work_capacity,
        post_task_headroom=post_task,
        fits=fits,
        reasons=tuple(reasons),
    )


@dataclass(frozen=True)
class SemanticCheckpoint:
    checkpoint_id: str
    work_item_id: str
    invariants: Mapping[str, Any]
    digest: str

    @classmethod
    def create(cls, work_item_id: str, invariants: Mapping[str, Any]) -> SemanticCheckpoint:
        required = {"objective", "user_constraints", "decisions", "risks", "next_action"}
        missing = sorted(required - invariants.keys())
        if missing:
            raise ValueError(f"semantic checkpoint missing invariants: {', '.join(missing)}")
        content = {"work_item_id": work_item_id, "invariants": dict(invariants)}
        digest = _digest(content)
        return cls(f"CTX-{digest[:16].upper()}", work_item_id, dict(invariants), digest)


@dataclass(frozen=True)
class ContextRecord:
    record_id: str
    claim: str
    token_cost: int
    relevance: float
    confidence: float = 1.0
    source_authority: float = 1.0
    recency: float = 0.0
    pinned: bool = False
    unresolved: bool = False
    provenance: str = ""
    source_digest: str = ""
    identity_key: str = ""
    residency: str = "cold"

    @property
    def score(self) -> float:
        return (
            self.relevance * 4
            + self.confidence * 2
            + self.source_authority * 2
            + self.recency
            + (100 if self.pinned else 0)
            + (2 if self.unresolved else 0)
            - self.token_cost / 10_000
        )


class ResidencyIndex:
    """Ephemeral residency view; durable records are never changed or tombstoned."""

    def __init__(self, records: Iterable[ContextRecord] = ()) -> None:
        self._records = {record.record_id: record for record in records}

    def offload(self, record_ids: Iterable[str]) -> None:
        for record_id in record_ids:
            record = self._records.get(record_id)
            if record and not record.pinned:
                self._records[record_id] = replace(record, residency="cold")

    def retrieve(self, token_budget: int) -> tuple[list[ContextRecord], dict[str, str]]:
        selected: list[ContextRecord] = []
        reasons: dict[str, str] = {}
        used = 0
        seen_claims: set[str] = set()
        ranked = sorted(self._records.values(), key=lambda item: (-item.score, item.record_id))
        for record in ranked:
            claim_key = " ".join(record.claim.lower().split())
            if claim_key in seen_claims:
                reasons[record.record_id] = "omitted duplicate claim"
                continue
            if used + record.token_cost > token_budget:
                reasons[record.record_id] = "omitted by token budget"
                continue
            resident = replace(record, residency="resident")
            selected.append(resident)
            seen_claims.add(claim_key)
            used += record.token_cost
            reasons[record.record_id] = "selected by deterministic rank"
        return selected, reasons

    def get(self, record_id: str) -> ContextRecord | None:
        return self._records.get(record_id)


@dataclass(frozen=True)
class ContextHealthReport:
    status: str
    missing_invariants: tuple[str, ...] = ()
    duplicate_groups: tuple[tuple[str, ...], ...] = ()
    stale_records: tuple[str, ...] = ()
    contradictions: tuple[tuple[str, ...], ...] = ()
    provenance_gaps: tuple[str, ...] = ()
    quarantined: tuple[str, ...] = ()
    recommended_actions: tuple[str, ...] = ()

    @property
    def resume_allowed(self) -> bool:
        return self.status in {"healthy", "warning"}


_SUSPICIOUS = re.compile(
    r"(?:ignore (?:all |the )?(?:previous|prior) instructions|system prompt|developer message)",
    re.IGNORECASE,
)


def check_context_health(
    records: Iterable[ContextRecord],
    *,
    required_invariants: Iterable[str],
    present_invariants: Mapping[str, Any],
    authoritative_digests: Mapping[str, str] | None = None,
) -> ContextHealthReport:
    items = list(records)
    missing = tuple(sorted(key for key in required_invariants if not present_invariants.get(key)))
    by_claim: dict[str, list[str]] = {}
    by_identity: dict[str, dict[str, list[str]]] = {}
    stale: list[str] = []
    provenance_gaps: list[str] = []
    quarantined: list[str] = []
    authoritative_digests = authoritative_digests or {}
    for record in items:
        by_claim.setdefault(" ".join(record.claim.lower().split()), []).append(record.record_id)
        if record.identity_key:
            by_identity.setdefault(record.identity_key, {}).setdefault(record.claim, []).append(
                record.record_id
            )
        if not record.provenance:
            provenance_gaps.append(record.record_id)
        if (
            record.provenance in authoritative_digests
            and record.source_digest != authoritative_digests[record.provenance]
        ):
            stale.append(record.record_id)
        if _SUSPICIOUS.search(record.claim):
            quarantined.append(record.record_id)

    duplicates = tuple(tuple(sorted(ids)) for ids in by_claim.values() if len(ids) > 1)
    contradictions = tuple(
        tuple(sorted(record_id for ids in claims.values() for record_id in ids))
        for claims in by_identity.values()
        if len(claims) > 1
    )
    findings = bool(
        missing or duplicates or stale or contradictions or provenance_gaps or quarantined
    )
    unsafe = bool(missing or contradictions or quarantined)
    status = "unsafe" if unsafe else "warning" if findings else "healthy"
    actions: list[str] = []
    if missing:
        actions.append("reload missing authoritative invariants")
    if duplicates:
        actions.append("deduplicate resident context")
    if stale:
        actions.append("refresh stale records from authoritative sources")
    if contradictions:
        actions.append("resolve or explicitly approve contradictions")
    if quarantined:
        actions.append("quarantine suspicious embedded instructions")
    return ContextHealthReport(
        status=status,
        missing_invariants=missing,
        duplicate_groups=duplicates,
        stale_records=tuple(sorted(stale)),
        contradictions=contradictions,
        provenance_gaps=tuple(sorted(provenance_gaps)),
        quarantined=tuple(sorted(quarantined)),
        recommended_actions=tuple(actions),
    )


@dataclass(frozen=True)
class ContextPacket:
    checkpoint_id: str
    work_item_id: str
    invariants: Mapping[str, Any]
    records: tuple[dict[str, Any], ...]
    digest: str

    @classmethod
    def build(
        cls,
        checkpoint: SemanticCheckpoint,
        records: Iterable[ContextRecord],
    ) -> ContextPacket:
        pointers = tuple(
            {
                "record_id": record.record_id,
                "claim": record.claim,
                "provenance": record.provenance,
                "confidence": record.confidence,
            }
            for record in records
        )
        content = {
            "checkpoint_id": checkpoint.checkpoint_id,
            "work_item_id": checkpoint.work_item_id,
            "invariants": dict(checkpoint.invariants),
            "records": pointers,
        }
        return cls(
            checkpoint.checkpoint_id,
            checkpoint.work_item_id,
            dict(checkpoint.invariants),
            pointers,
            _digest(content),
        )


def cleanup_context(
    checkpoint: SemanticCheckpoint | None,
    records: Iterable[ContextRecord],
    *,
    token_budget: int,
    authoritative_digests: Mapping[str, str] | None = None,
) -> tuple[ContextPacket, ContextHealthReport]:
    """Checkpoint-first cleanup that rebuilds residency without deleting evidence."""
    if checkpoint is None:
        raise ValueError("cleanup requires a semantic checkpoint")
    items = list(records)
    report = check_context_health(
        items,
        required_invariants=checkpoint.invariants.keys(),
        present_invariants=checkpoint.invariants,
        authoritative_digests=authoritative_digests,
    )
    excluded = set(report.quarantined) | set(report.stale_records)
    index = ResidencyIndex(record for record in items if record.record_id not in excluded)
    selected, _ = index.retrieve(token_budget)
    packet = ContextPacket.build(checkpoint, selected)
    return packet, report


@dataclass(frozen=True)
class ZooContextDirective:
    action: str
    packet_digest: str = ""
    resume_allowed: bool = False
    native_summary_allowed: bool = False
    degraded: bool = False
    reason: str = ""


class ZooContextController:
    """Pure contract adapter for Specsmith-authoritative Zoo transitions."""

    def directive(
        self,
        decision: ContextDecision,
        *,
        governed: bool,
        packet: ContextPacket | None = None,
        specsmith_available: bool = True,
        health: ContextHealthReport | None = None,
    ) -> ZooContextDirective:
        if not governed:
            return ZooContextDirective(
                action="unmanaged",
                resume_allowed=True,
                native_summary_allowed=True,
                reason="user explicitly disabled governed context",
            )
        if not specsmith_available:
            return ZooContextDirective(
                action=ContextAction.BLOCKED_DEGRADED.value,
                degraded=True,
                reason="Specsmith unavailable; preserve raw history and reconcile before resume",
            )
        if health is not None and not health.resume_allowed:
            return ZooContextDirective(
                action=ContextAction.BLOCKED_DEGRADED.value,
                packet_digest=packet.digest if packet else "",
                degraded=True,
                reason="context health gate rejected the packet",
            )
        requires_packet = decision.action in {
            ContextAction.SEMANTIC_CHECKPOINT,
            ContextAction.CHECKPOINT_AND_CONDENSE,
            ContextAction.SPAWN_FRESH_TASK,
        }
        if requires_packet and packet is None:
            return ZooContextDirective(
                action=ContextAction.BLOCKED_DEGRADED.value,
                degraded=True,
                reason="governed transition requires an exact Specsmith packet",
            )
        return ZooContextDirective(
            action=decision.action.value,
            packet_digest=packet.digest if packet else "",
            resume_allowed=decision.action is ContextAction.CONTINUE,
            native_summary_allowed=False,
        )

    @staticmethod
    def verify_applied(directive: ZooContextDirective, applied_digest: str) -> bool:
        return bool(
            directive.packet_digest
            and directive.packet_digest == applied_digest
            and not directive.degraded
        )
