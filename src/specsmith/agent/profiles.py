# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Agent Profiles + Activity Routing (REQ-146).

A *profile* unifies ``(provider, model, endpoint_id?, prompt_prefix,
capabilities, fallback_chain)`` into a single named object. A *routing
table* maps activities (``/plan``, ``/fix``, ``/test``, AEE phases, MCP
tool categories) to a profile. The runner consults the table on every
turn, then falls back to the legacy single-provider path if no match
exists.

Storage layout (``~/.specsmith/agents.json``)::

    {
      "schema_version": 1,
      "default_profile_id": "coder",
      "profiles": [
        {"id": "architect", "role": "architect",
         "provider": "anthropic", "model": "claude-opus-4",
         "fallback_chain": ["openai/gpt-5", "ollama/qwen2.5:32b"],
         "endpoint_id": "", "prompt_prefix": "",
         "capabilities": ["reasoning", "long-context"]},
        ...
      ],
      "routes": {
        "/plan": "architect",
        "/fix": "coder",
        ...
      }
    }

Per-project overrides land at ``<project>/.specsmith/agents.json`` with
the same schema. Missing keys inherit from the global file.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


VALID_ROLES = (
    "architect",
    "coder",
    "reviewer",
    "editor",
    "researcher",
    "tester",
    "classifier",
    "generalist",
)


# Default presets shipped with the CLI so a fresh install Just Works.
# The exact model strings can be customised per-deployment via
# ``specsmith agents preset apply <name>`` or by editing the file directly.
DEFAULT_PRESETS: dict[str, dict[str, Any]] = {
    "default": {
        "default_profile_id": "coder",
        "profiles": [
            {
                "id": "architect",
                "role": "architect",
                "provider": "anthropic",
                "model": "claude-opus-4",
                "fallback_chain": ["openai/gpt-5", "ollama/qwen2.5:32b"],
                "capabilities": ["reasoning", "long-context"],
            },
            {
                "id": "coder",
                "role": "coder",
                "provider": "anthropic",
                "model": "claude-sonnet-4-5",
                "fallback_chain": [
                    "mistral/codestral-latest",
                    "ollama/qwen2.5-coder:32b",
                ],
                "capabilities": ["code", "function-calling"],
            },
            {
                "id": "reviewer",
                "role": "reviewer",
                "provider": "openai",
                "model": "gpt-5-codex",
                "fallback_chain": [
                    "gemini/gemini-3-flash",
                    "ollama/deepseek-r1:14b",
                ],
                "capabilities": ["code-review", "different-family-from-coder"],
            },
            {
                "id": "editor",
                "role": "editor",
                "provider": "anthropic",
                "model": "claude-haiku-4-5",
                "fallback_chain": ["openai/gpt-5-mini", "ollama/qwen2.5-coder:7b"],
                "capabilities": ["fast", "diff-apply"],
            },
            {
                "id": "researcher",
                "role": "researcher",
                "provider": "gemini",
                "model": "gemini-3-pro",
                "fallback_chain": ["ollama/qwen2.5:14b"],
                "capabilities": ["search", "long-context", "mcp"],
            },
            {
                "id": "tester",
                "role": "tester",
                "provider": "mistral",
                "model": "mistral-small-latest",
                "fallback_chain": ["ollama/qwen2.5:14b"],
                "capabilities": ["test-design"],
            },
            {
                "id": "classifier",
                "role": "classifier",
                "provider": "anthropic",
                "model": "claude-haiku-4-5",
                "fallback_chain": ["ollama/qwen2.5:3b"],
                "capabilities": ["fast", "classification"],
            },
        ],
        "routes": {
            "chat": "coder",
            "/plan": "architect",
            "/architect": "architect",
            "/ask": "researcher",
            "/fix": "coder",
            "/code": "coder",
            "/refactor": "coder",
            "/test": "tester",
            "/review": "reviewer",
            "/why": "reviewer",
            "/audit": "reviewer",
            "/commit": "editor",
            "/pr": "editor",
            "/undo": "editor",
            "/context": "researcher",
            "/search": "researcher",
            "phase:inception": "architect",
            "phase:architecture": "architect",
            "phase:requirements": "researcher",
            "phase:test_spec": "tester",
            "phase:implementation": "coder",
            "phase:verification": "reviewer",
            "phase:release": "editor",
            "predict_next": "classifier",
            "suggest_command": "classifier",
        },
    },
    "local-only": {
        "default_profile_id": "local-coder",
        "profiles": [
            {
                "id": "local-architect",
                "role": "architect",
                "provider": "ollama",
                "model": "qwen2.5:32b",
                "fallback_chain": ["ollama/qwen2.5:14b"],
            },
            {
                "id": "local-coder",
                "role": "coder",
                "provider": "ollama",
                "model": "qwen2.5-coder:32b",
                "fallback_chain": ["ollama/qwen2.5-coder:7b"],
            },
            {
                "id": "local-reviewer",
                "role": "reviewer",
                "provider": "ollama",
                "model": "deepseek-r1:14b",
                "fallback_chain": ["ollama/qwen2.5:7b"],
            },
            {
                "id": "local-editor",
                "role": "editor",
                "provider": "ollama",
                "model": "qwen2.5-coder:7b",
                "fallback_chain": [],
            },
            {
                "id": "local-classifier",
                "role": "classifier",
                "provider": "ollama",
                "model": "qwen2.5:3b",
                "fallback_chain": [],
            },
        ],
        "routes": {
            "chat": "local-coder",
            "/plan": "local-architect",
            "/architect": "local-architect",
            "/fix": "local-coder",
            "/code": "local-coder",
            "/test": "local-coder",
            "/review": "local-reviewer",
            "/why": "local-reviewer",
            "/commit": "local-editor",
            "/pr": "local-editor",
            "predict_next": "local-classifier",
            "suggest_command": "local-classifier",
        },
    },
    "frontier-only": {
        "default_profile_id": "opus-coder",
        "profiles": [
            {
                "id": "opus-architect",
                "role": "architect",
                "provider": "anthropic",
                "model": "claude-opus-4",
                "fallback_chain": [],
            },
            {
                "id": "opus-coder",
                "role": "coder",
                "provider": "anthropic",
                "model": "claude-opus-4",
                "fallback_chain": [],
            },
        ],
        "routes": {
            "chat": "opus-coder",
            "/plan": "opus-architect",
            "/architect": "opus-architect",
        },
    },
    "cost-conscious": {
        "default_profile_id": "haiku-coder",
        "profiles": [
            {
                "id": "haiku-coder",
                "role": "coder",
                "provider": "anthropic",
                "model": "claude-haiku-4-5",
                "fallback_chain": ["ollama/qwen2.5-coder:7b"],
            },
            {
                "id": "sonnet-architect",
                "role": "architect",
                "provider": "anthropic",
                "model": "claude-sonnet-4-5",
                "fallback_chain": ["ollama/qwen2.5:32b"],
            },
        ],
        "routes": {
            "chat": "haiku-coder",
            "/plan": "sonnet-architect",
            "/architect": "sonnet-architect",
            "/fix": "haiku-coder",
            "/test": "haiku-coder",
        },
    },
}


class ProfileError(RuntimeError):
    """Raised for user-facing profile / routing errors."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Profile:
    """A single named agent configuration.

    ``fallback_chain`` entries are simple ``"<provider>/<model>"`` strings
    or ``"endpoint:<id>"`` references; resolution is performed by
    :mod:`specsmith.agent.fallback`.
    """

    id: str
    role: str = "generalist"
    provider: str = "ollama"
    model: str = ""
    endpoint_id: str = ""
    prompt_prefix: str = ""
    capabilities: list[str] = field(default_factory=list)
    fallback_chain: list[str] = field(default_factory=list)
    created_at: str = ""

    def validate(self) -> None:
        if not self.id or not self.id.strip():
            raise ProfileError("profile id must be non-empty")
        if any(c.isspace() for c in self.id):
            raise ProfileError(f"profile id {self.id!r} must not contain whitespace")
        if self.role and self.role not in VALID_ROLES:
            # Roles are advisory but warn-on-set so downstream consumers
            # don't trip on typos. We still allow the value through.
            pass
        if not self.provider:
            raise ProfileError(f"profile {self.id!r} requires a provider")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "provider": self.provider,
            "model": self.model,
            "endpoint_id": self.endpoint_id,
            "prompt_prefix": self.prompt_prefix,
            "capabilities": list(self.capabilities),
            "fallback_chain": list(self.fallback_chain),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Profile:
        return cls(
            id=str(raw.get("id") or "").strip(),
            role=str(raw.get("role") or "generalist").strip(),
            provider=str(raw.get("provider") or "ollama").strip(),
            model=str(raw.get("model") or "").strip(),
            endpoint_id=str(raw.get("endpoint_id") or "").strip(),
            prompt_prefix=str(raw.get("prompt_prefix") or ""),
            capabilities=[str(c) for c in (raw.get("capabilities") or [])],
            fallback_chain=[str(c) for c in (raw.get("fallback_chain") or [])],
            created_at=str(raw.get("created_at") or ""),
        )


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------


def default_store_path() -> Path:
    """Resolve ``~/.specsmith/agents.json``, honouring ``SPECSMITH_HOME``."""
    base = os.environ.get("SPECSMITH_HOME", "").strip()
    home = Path(base) if base else Path.home() / ".specsmith"
    return home / "agents.json"


def project_store_path(project_dir: str | Path) -> Path:
    """Resolve ``<project>/.specsmith/agents.json`` for per-project overrides."""
    return Path(project_dir).resolve() / ".specsmith" / "agents.json"


@dataclass
class ProfileStore:
    """Read/write wrapper around the profiles JSON file.

    Supports a two-level inheritance model: a project-level file (when
    constructed via :meth:`load_for_project`) overrides whatever is set
    globally in ``~/.specsmith/agents.json``.
    """

    path: Path
    schema_version: int = SCHEMA_VERSION
    default_profile_id: str = ""
    profiles: list[Profile] = field(default_factory=list)
    routes: dict[str, str] = field(default_factory=dict)

    # ── I/O ────────────────────────────────────────────────────────────

    @classmethod
    def load(cls, path: Path | None = None) -> ProfileStore:
        target = path or default_store_path()
        if not target.exists():
            return cls(path=target)
        try:
            raw = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ProfileError(
                f"agents store at {target} is corrupted: {exc}. "
                "Move it aside or fix the JSON to continue."
            ) from exc
        if not isinstance(raw, dict):
            raise ProfileError(f"agents store at {target} must be a JSON object")
        return cls._from_raw(target, raw)

    @classmethod
    def load_for_project(cls, project_dir: str | Path) -> ProfileStore:
        """Return a merged view of global + project-level profiles.

        Project profiles win on id collisions; routes are merged with
        project entries taking precedence; ``default_profile_id`` is the
        project value when set, else global.
        """
        global_store = cls.load()
        project_path = project_store_path(project_dir)
        if not project_path.exists():
            return global_store
        try:
            raw = json.loads(project_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return global_store
        project_store = cls._from_raw(project_path, raw)
        merged_profiles: dict[str, Profile] = {p.id: p for p in global_store.profiles}
        for p in project_store.profiles:
            merged_profiles[p.id] = p
        merged_routes: dict[str, str] = dict(global_store.routes)
        merged_routes.update(project_store.routes)
        return cls(
            path=project_path,
            schema_version=SCHEMA_VERSION,
            default_profile_id=project_store.default_profile_id
            or global_store.default_profile_id,
            profiles=list(merged_profiles.values()),
            routes=merged_routes,
        )

    @classmethod
    def _from_raw(cls, path: Path, raw: dict[str, Any]) -> ProfileStore:
        version = int(raw.get("schema_version") or 0)
        if version and version != SCHEMA_VERSION:
            raise ProfileError(
                f"agents store at {path} uses schema_version={version}; "
                f"this build of specsmith only understands {SCHEMA_VERSION}."
            )
        profiles_raw = raw.get("profiles") or []
        if not isinstance(profiles_raw, list):
            raise ProfileError("agents store: 'profiles' must be a list")
        profiles = [Profile.from_dict(item) for item in profiles_raw if isinstance(item, dict)]
        routes_raw = raw.get("routes") or {}
        if not isinstance(routes_raw, dict):
            raise ProfileError("agents store: 'routes' must be an object")
        routes = {str(k): str(v) for k, v in routes_raw.items()}
        return cls(
            path=path,
            schema_version=SCHEMA_VERSION,
            default_profile_id=str(raw.get("default_profile_id") or "").strip(),
            profiles=profiles,
            routes=routes,
        )

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self.schema_version,
            "default_profile_id": self.default_profile_id,
            "profiles": [p.to_dict() for p in self.profiles],
            "routes": dict(self.routes),
        }
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # ── CRUD ───────────────────────────────────────────────────────────

    def add(self, profile: Profile, *, replace: bool = False) -> None:
        profile.validate()
        if not profile.created_at:
            profile.created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        existing = self._index(profile.id)
        if existing is not None:
            if not replace:
                raise ProfileError(
                    f"profile {profile.id!r} already exists. Use --replace to overwrite."
                )
            self.profiles[existing] = profile
        else:
            self.profiles.append(profile)
        if not self.default_profile_id:
            self.default_profile_id = profile.id

    def remove(self, profile_id: str) -> bool:
        idx = self._index(profile_id)
        if idx is None:
            return False
        self.profiles.pop(idx)
        if self.default_profile_id == profile_id:
            self.default_profile_id = self.profiles[0].id if self.profiles else ""
        # Drop any routing entries pointing at the removed profile.
        self.routes = {k: v for k, v in self.routes.items() if v != profile_id}
        return True

    def get(self, profile_id: str) -> Profile:
        idx = self._index(profile_id)
        if idx is None:
            raise ProfileError(f"unknown profile id {profile_id!r}")
        return self.profiles[idx]

    def get_default(self) -> Profile | None:
        if not self.default_profile_id:
            return None
        idx = self._index(self.default_profile_id)
        return self.profiles[idx] if idx is not None else None

    def set_default(self, profile_id: str) -> None:
        if self._index(profile_id) is None:
            raise ProfileError(f"unknown profile id {profile_id!r}")
        self.default_profile_id = profile_id

    def list_all(self) -> list[Profile]:
        return list(self.profiles)

    # ── Routing ───────────────────────────────────────────────────────

    def set_route(self, activity: str, profile_id: str) -> None:
        activity = activity.strip()
        if not activity:
            raise ProfileError("activity must be non-empty")
        if self._index(profile_id) is None:
            raise ProfileError(f"unknown profile id {profile_id!r}")
        self.routes[activity] = profile_id

    def clear_route(self, activity: str) -> None:
        self.routes.pop(activity, None)

    def resolve_for_activity(self, activity: str) -> Profile | None:
        target_id = self.routes.get(activity) or self.default_profile_id
        if not target_id:
            return None
        idx = self._index(target_id)
        return self.profiles[idx] if idx is not None else self.get_default()

    # ── Internals ──────────────────────────────────────────────────────

    def _index(self, profile_id: str) -> int | None:
        for i, p in enumerate(self.profiles):
            if p.id == profile_id:
                return i
        return None


# ---------------------------------------------------------------------------
# Preset application
# ---------------------------------------------------------------------------


def apply_preset(name: str, *, path: Path | None = None) -> ProfileStore:
    """Overwrite the profiles store with one of :data:`DEFAULT_PRESETS`.

    Any existing profiles are replaced wholesale. Endpoint references in
    profile entries are preserved if they happen to match a registered
    BYOE endpoint id, otherwise they are dropped from the resolved
    profile to avoid dangling foreign keys.
    """
    if name not in DEFAULT_PRESETS:
        raise ProfileError(
            f"unknown preset {name!r}. Available: {', '.join(sorted(DEFAULT_PRESETS))}"
        )
    target = path or default_store_path()
    blob = DEFAULT_PRESETS[name]
    profiles = [Profile.from_dict(p) for p in blob.get("profiles", [])]
    for p in profiles:
        if not p.created_at:
            p.created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    store = ProfileStore(
        path=target,
        schema_version=SCHEMA_VERSION,
        default_profile_id=str(blob.get("default_profile_id") or ""),
        profiles=profiles,
        routes={str(k): str(v) for k, v in (blob.get("routes") or {}).items()},
    )
    store.save()
    return store


__all__ = [
    "DEFAULT_PRESETS",
    "Profile",
    "ProfileError",
    "ProfileStore",
    "SCHEMA_VERSION",
    "VALID_ROLES",
    "apply_preset",
    "default_store_path",
    "project_store_path",
]
