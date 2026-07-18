"""Layered actor, agent, replica, and session identity resolution."""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from specsmith.config_resolver import ResolvedConfig


@dataclass(frozen=True)
class ResolvedIdentity:
    actor_id: str
    agent_id: str
    replica_id: str
    session_id: str
    provenance: Mapping[str, str]
    display_name: str = ""

    def event_attribution(self) -> dict[str, str]:
        return {
            "actor_id": self.actor_id,
            "agent_id": self.agent_id,
            "replica_id": self.replica_id,
            "session_id": self.session_id,
        }


IdentityDetector = Callable[[], Mapping[str, str] | None]


def resolve_identity(
    config: ResolvedConfig,
    project_root: Path,
    *,
    session_id: str | None = None,
    detectors: tuple[IdentityDetector, ...] = (),
) -> ResolvedIdentity:
    raw = dict(config.values.get("identity") or {})
    provenance: dict[str, str] = {}
    detected: Mapping[str, str] = {}
    if not raw.get("actor_id"):
        for detector in detectors:
            candidate = detector() or {}
            if candidate.get("actor_id"):
                detected = candidate
                break

    root_hash = hashlib.sha256(str(project_root.resolve()).encode()).hexdigest()[:16]
    defaults = {
        "actor_id": detected.get("actor_id") or f"anonymous-{root_hash}",
        "agent_id": "specsmith-agent",
        "replica_id": f"worktree-{root_hash}",
        "session_id": session_id or f"session-{uuid.uuid4().hex}",
    }
    values: dict[str, str] = {}
    for key, default in defaults.items():
        values[key] = str(raw.get(key) or default)
        provenance[key] = config.provenance.get(
            f"identity.{key}", "provider-detection" if detected.get(key) else "generated"
        )
    return ResolvedIdentity(
        **values,
        provenance=provenance,
        display_name=str(raw.get("display_name") or detected.get("display_name") or ""),
    )
