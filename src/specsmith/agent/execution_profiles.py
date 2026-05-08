# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Execution Profiles — provider-constraint layer (REQ-221).

A profile defines **which providers are allowed** for a session.  The model
selector operates within the profile's constraints — it will never use a
provider that isn't in the profile's ``allowed_providers`` list.

Built-in profiles:
  unrestricted — all enabled providers (default)
  local-only   — Ollama + vLLM only, zero cloud calls
  budget       — cheapest per role (local first, then cheap cloud)
  performance  — best benchmark score regardless of cost
  air-gapped   — vLLM only (sensitive IP / classified work)

Custom profiles: user defines allowed provider IDs + per-role overrides.

Storage: ``~/.specsmith/execution_profiles.json``
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

SCHEMA_VERSION = 1


@dataclass
class RoleOverride:
    """Per-role provider+model override within a profile."""

    provider_id: str = ""
    model: str = ""
    temperature: float | None = None
    max_tokens: int | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"provider_id": self.provider_id, "model": self.model}
        if self.temperature is not None:
            d["temperature"] = self.temperature
        if self.max_tokens is not None:
            d["max_tokens"] = self.max_tokens
        return d

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> RoleOverride:
        return cls(
            provider_id=str(raw.get("provider_id") or ""),
            model=str(raw.get("model") or ""),
            temperature=raw.get("temperature"),
            max_tokens=raw.get("max_tokens"),
        )


@dataclass
class ExecutionProfile:
    """A named set of provider constraints."""

    id: str
    name: str
    description: str = ""
    allowed_providers: list[str] = field(default_factory=list)  # empty = all
    allowed_provider_types: list[str] = field(default_factory=list)  # empty = all
    role_overrides: dict[str, RoleOverride] = field(default_factory=dict)
    is_default: bool = False
    is_builtin: bool = False

    def allows_provider(self, provider_id: str, provider_type: str) -> bool:
        """Check if this profile allows using a given provider."""
        if self.allowed_providers and provider_id not in self.allowed_providers:
            return False
        return not (
            self.allowed_provider_types and provider_type not in self.allowed_provider_types
        )

    def get_role_override(self, role: str) -> RoleOverride | None:
        return self.role_overrides.get(role)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "allowed_providers": self.allowed_providers,
            "allowed_provider_types": self.allowed_provider_types,
            "role_overrides": {k: v.to_dict() for k, v in self.role_overrides.items()},
            "is_default": self.is_default,
            "is_builtin": self.is_builtin,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ExecutionProfile:
        overrides = {}
        for k, v in (raw.get("role_overrides") or {}).items():
            if isinstance(v, dict):
                overrides[k] = RoleOverride.from_dict(v)
        return cls(
            id=str(raw.get("id") or ""),
            name=str(raw.get("name") or ""),
            description=str(raw.get("description") or ""),
            allowed_providers=raw.get("allowed_providers") or [],
            allowed_provider_types=raw.get("allowed_provider_types") or [],
            role_overrides=overrides,
            is_default=bool(raw.get("is_default", False)),
            is_builtin=bool(raw.get("is_builtin", False)),
        )


# ---------------------------------------------------------------------------
# Built-in profiles
# ---------------------------------------------------------------------------

BUILTIN_PROFILES: list[ExecutionProfile] = [
    ExecutionProfile(
        id="unrestricted",
        name="Unrestricted",
        description="All enabled providers. Best model wins.",
        is_default=True,
        is_builtin=True,
    ),
    ExecutionProfile(
        id="local-only",
        name="Local Only",
        description="Ollama + vLLM only. Zero cloud calls, zero cost.",
        allowed_provider_types=["ollama", "vllm"],
        is_builtin=True,
    ),
    ExecutionProfile(
        id="budget",
        name="Budget",
        description="Cheapest provider per role. Prefers local, then cheap cloud.",
        is_builtin=True,
        # No provider constraints — cost sorting happens at assignment resolution.
    ),
    ExecutionProfile(
        id="performance",
        name="Performance",
        description="Best benchmark score per role regardless of cost.",
        is_builtin=True,
    ),
    ExecutionProfile(
        id="air-gapped",
        name="Air-Gapped",
        description="vLLM only. For sensitive IP or classified work.",
        allowed_provider_types=["vllm"],
        is_builtin=True,
    ),
]


# ---------------------------------------------------------------------------
# Profile store
# ---------------------------------------------------------------------------


class ExecutionProfileStore:
    """Load/save/query execution profiles."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path.home() / ".specsmith" / "execution_profiles.json"
        self._profiles: list[ExecutionProfile] = []
        self._load()

    def _load(self) -> None:
        # Always start with built-in profiles.
        self._profiles = [
            ExecutionProfile(
                id=p.id,
                name=p.name,
                description=p.description,
                allowed_providers=list(p.allowed_providers),
                allowed_provider_types=list(p.allowed_provider_types),
                role_overrides=dict(p.role_overrides),
                is_default=p.is_default,
                is_builtin=True,
            )
            for p in BUILTIN_PROFILES
        ]
        if not self._path.is_file():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            for entry in raw.get("profiles", []):
                profile = ExecutionProfile.from_dict(entry)
                # Don't duplicate built-ins; user overrides of built-in IDs
                # replace the built-in version.
                existing = self._find(profile.id)
                if existing is not None:
                    self._profiles[existing] = profile
                else:
                    self._profiles.append(profile)
            # Apply saved default.
            default_id = raw.get("default_profile_id", "")
            if default_id:
                for p in self._profiles:
                    p.is_default = p.id == default_id
        except Exception:  # noqa: BLE001
            _log.warning("Failed to load execution profiles from %s", self._path)

    def _find(self, profile_id: str) -> int | None:
        for i, p in enumerate(self._profiles):
            if p.id == profile_id:
                return i
        return None

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        default_id = ""
        for p in self._profiles:
            if p.is_default:
                default_id = p.id
                break
        data = {
            "schema_version": SCHEMA_VERSION,
            "default_profile_id": default_id,
            "profiles": [
                p.to_dict() for p in self._profiles if not p.is_builtin or p.role_overrides
            ],
        }
        self._path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # ── Queries ────────────────────────────────────────────────────────

    @property
    def profiles(self) -> list[ExecutionProfile]:
        return list(self._profiles)

    def get(self, profile_id: str) -> ExecutionProfile | None:
        idx = self._find(profile_id)
        return self._profiles[idx] if idx is not None else None

    def default(self) -> ExecutionProfile:
        for p in self._profiles:
            if p.is_default:
                return p
        # Fallback to unrestricted if nothing is default.
        return self._profiles[0] if self._profiles else BUILTIN_PROFILES[0]

    # ── Mutations ──────────────────────────────────────────────────────

    def add(self, profile: ExecutionProfile) -> None:
        if self._find(profile.id) is not None:
            raise ValueError(f"profile {profile.id!r} already exists")
        self._profiles.append(profile)
        self._save()

    def set_default(self, profile_id: str) -> None:
        if self._find(profile_id) is None:
            raise ValueError(f"profile {profile_id!r} not found")
        for p in self._profiles:
            p.is_default = p.id == profile_id
        self._save()

    def remove(self, profile_id: str) -> None:
        idx = self._find(profile_id)
        if idx is None:
            raise ValueError(f"profile {profile_id!r} not found")
        if self._profiles[idx].is_builtin:
            raise ValueError(f"cannot remove built-in profile {profile_id!r}")
        self._profiles.pop(idx)
        self._save()

    @classmethod
    def load(cls, path: Path | None = None) -> ExecutionProfileStore:
        return cls(path=path)
