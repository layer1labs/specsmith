# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Unified Provider Registry (REQ-220).

A single flat list of all configured AI backends. Each entry is one of 5
types: cloud, ollama, vllm, byoe, huggingface.  The registry replaces the
scattered EndpointStore + hardcoded provider list + .keys.json pattern
with a single source of truth for "where can I send LLM requests?".

Storage: ``~/.specsmith/providers.json``

The registry is orthogonal to *roles* and *profiles* — it answers
"what providers exist?" while profiles answer "which are allowed?" and
role assignments answer "which should I use for this task?".
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

SCHEMA_VERSION = 1

# Known cloud provider base URLs (auto-filled on add).
CLOUD_PROVIDERS: dict[str, dict[str, str]] = {
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models_url": "https://api.openai.com/v1/models",
    },
    "anthropic": {
        "label": "Anthropic",
        "base_url": "https://api.anthropic.com/v1",
        "models_url": "https://api.anthropic.com/v1/models",
    },
    "gemini": {
        "label": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "models_url": "",
    },
    "mistral": {
        "label": "Mistral",
        "base_url": "https://api.mistral.ai/v1",
        "models_url": "https://api.mistral.ai/v1/models",
    },
    "groq": {
        "label": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "models_url": "https://api.groq.com/openai/v1/models",
    },
    "together": {
        "label": "Together",
        "base_url": "https://api.together.xyz/v1",
        "models_url": "https://api.together.xyz/v1/models",
    },
    "fireworks": {
        "label": "Fireworks",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "models_url": "https://api.fireworks.ai/inference/v1/models",
    },
    "deepinfra": {
        "label": "DeepInfra",
        "base_url": "https://api.deepinfra.com/v1/openai",
        "models_url": "https://api.deepinfra.com/v1/openai/models",
    },
    "openrouter": {
        "label": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "models_url": "https://openrouter.ai/api/v1/models",
    },
    "perplexity": {
        "label": "Perplexity",
        "base_url": "https://api.perplexity.ai",
        "models_url": "",
    },
}

VALID_PROVIDER_TYPES = ("cloud", "ollama", "vllm", "byoe", "huggingface")


class ProviderError(RuntimeError):
    """Raised for user-facing provider registry errors."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ProviderEntry:
    """A single registered AI provider/endpoint."""

    id: str
    name: str
    provider_type: str  # cloud | ollama | vllm | byoe | huggingface
    provider_id: str = ""  # e.g. "openai", "anthropic", "ollama"
    base_url: str = ""
    api_key: str = ""  # encrypted at rest in future; plain for now
    headers: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    status: str = "untested"  # reachable | unreachable | untested
    available_models: list[str] = field(default_factory=list)
    last_probed_at: str = ""
    max_context_tokens: int = 0
    cost_per_1k_tokens: float = 0.0
    tags: list[str] = field(default_factory=list)
    notes: str = ""

    def validate(self) -> None:
        if not self.id or not self.id.strip():
            raise ProviderError("provider id must be non-empty")
        if any(c.isspace() for c in self.id):
            raise ProviderError(f"provider id {self.id!r} must not contain whitespace")
        if self.provider_type not in VALID_PROVIDER_TYPES:
            raise ProviderError(
                f"provider_type {self.provider_type!r} invalid; "
                f"expected one of {VALID_PROVIDER_TYPES}"
            )
        if self.provider_type != "ollama" and not self.base_url:
            # Ollama can auto-detect
            if self.provider_type == "cloud" and self.provider_id in CLOUD_PROVIDERS:
                self.base_url = CLOUD_PROVIDERS[self.provider_id]["base_url"]
            elif not self.base_url:
                raise ProviderError("base_url is required for non-Ollama providers")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider_type": self.provider_type,
            "provider_id": self.provider_id,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "headers": self.headers,
            "enabled": self.enabled,
            "status": self.status,
            "available_models": self.available_models,
            "last_probed_at": self.last_probed_at,
            "max_context_tokens": self.max_context_tokens,
            "cost_per_1k_tokens": self.cost_per_1k_tokens,
            "tags": self.tags,
            "notes": self.notes,
        }

    def to_public_dict(self) -> dict[str, Any]:
        """Redacted shape — never returns API key."""
        d = self.to_dict()
        d["api_key"] = "***" if self.api_key else ""
        d["api_key_set"] = bool(self.api_key)
        return d

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ProviderEntry:
        return cls(
            id=str(raw.get("id") or ""),
            name=str(raw.get("name") or ""),
            provider_type=str(raw.get("provider_type") or "byoe"),
            provider_id=str(raw.get("provider_id") or ""),
            base_url=str(raw.get("base_url") or ""),
            api_key=str(raw.get("api_key") or ""),
            headers=raw.get("headers") or {},
            enabled=bool(raw.get("enabled", True)),
            status=str(raw.get("status") or "untested"),
            available_models=raw.get("available_models") or [],
            last_probed_at=str(raw.get("last_probed_at") or ""),
            max_context_tokens=int(raw.get("max_context_tokens") or 0),
            cost_per_1k_tokens=float(raw.get("cost_per_1k_tokens") or 0),
            tags=raw.get("tags") or [],
            notes=str(raw.get("notes") or ""),
        )


# ---------------------------------------------------------------------------
# Probe functions
# ---------------------------------------------------------------------------


def probe_openai_compatible(
    base_url: str,
    api_key: str = "",
    headers: dict[str, str] | None = None,
    *,
    timeout: float = 8.0,
) -> dict[str, Any]:
    """Probe an OpenAI-compatible endpoint for available models."""
    base = (base_url or "").strip().rstrip("/")
    url = f"{base}/models" if base.endswith("/v1") else f"{base}/v1/models"
    req_headers: dict[str, str] = {"Accept": "application/json"}
    if api_key:
        req_headers["Authorization"] = f"Bearer {api_key}"
    if headers:
        req_headers.update(headers)
    try:
        req = urllib.request.Request(url, headers=req_headers, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            data = json.loads(resp.read().decode())
        models: list[str] = []
        for entry in data.get("data") or data.get("models") or []:
            mid = (
                entry.get("id") or entry.get("name") or ""
                if isinstance(entry, dict)
                else str(entry)
            )
            if mid:
                models.append(str(mid))
        return {"valid": True, "message": f"OK — {len(models)} model(s)", "models": models[:200]}
    except urllib.error.HTTPError as exc:
        msg = f"HTTP {exc.code}: {exc.reason}"
        if exc.code in (401, 403):
            msg = f"Unauthorized (HTTP {exc.code}). Check API key."
        return {"valid": False, "message": msg, "models": []}
    except Exception as exc:  # noqa: BLE001
        return {"valid": False, "message": f"Connection error: {exc}", "models": []}


def probe_ollama(base_url: str = "", *, timeout: float = 5.0) -> dict[str, Any]:
    """Probe an Ollama instance for installed models."""
    base = (base_url or "http://localhost:11434").strip().rstrip("/")
    try:
        req = urllib.request.Request(f"{base}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            data = json.loads(resp.read().decode())
        models = [m["name"] for m in data.get("models", []) if m.get("name")]
        return {"valid": True, "message": f"OK — {len(models)} model(s)", "models": models}
    except Exception as exc:  # noqa: BLE001
        return {"valid": False, "message": f"Not reachable: {exc}", "models": []}


def probe_anthropic(api_key: str, *, timeout: float = 8.0) -> dict[str, Any]:
    """Probe the Anthropic API (uses x-api-key header)."""
    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/models",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Accept": "application/json",
            },
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            data = json.loads(resp.read().decode())
        models = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
        return {"valid": True, "message": f"OK — {len(models)} model(s)", "models": models[:100]}
    except urllib.error.HTTPError as exc:
        return {"valid": False, "message": f"HTTP {exc.code}: {exc.reason}", "models": []}
    except Exception as exc:  # noqa: BLE001
        return {"valid": False, "message": str(exc), "models": []}


def probe_provider(entry: ProviderEntry) -> dict[str, Any]:
    """Probe any provider and return {valid, message, models}."""
    if entry.provider_type == "ollama":
        return probe_ollama(entry.base_url or "http://localhost:11434")
    if entry.provider_type == "cloud" and entry.provider_id == "anthropic":
        return probe_anthropic(entry.api_key)
    # Everything else is OpenAI-compatible (cloud, vllm, byoe, huggingface)
    return probe_openai_compatible(entry.base_url, entry.api_key, entry.headers)


# ---------------------------------------------------------------------------
# Registry persistence
# ---------------------------------------------------------------------------


class ProviderRegistry:
    """Load/save/query the provider registry from ``~/.specsmith/providers.json``."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path.home() / ".specsmith" / "providers.json"
        self._providers: list[ProviderEntry] = []
        self._load()

    def _load(self) -> None:
        if not self._path.is_file():
            self._providers = []
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            self._providers = [ProviderEntry.from_dict(e) for e in raw.get("providers", [])]
        except Exception:  # noqa: BLE001
            _log.warning("Failed to load provider registry from %s", self._path)
            self._providers = []

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "schema_version": SCHEMA_VERSION,
            "providers": [p.to_dict() for p in self._providers],
        }
        self._path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # ── Queries ────────────────────────────────────────────────────────

    @property
    def providers(self) -> list[ProviderEntry]:
        return list(self._providers)

    def enabled(self) -> list[ProviderEntry]:
        return [p for p in self._providers if p.enabled]

    def get(self, provider_id: str) -> ProviderEntry | None:
        for p in self._providers:
            if p.id == provider_id:
                return p
        return None

    def by_type(self, provider_type: str) -> list[ProviderEntry]:
        return [p for p in self._providers if p.provider_type == provider_type and p.enabled]

    def by_tags(self, *tags: str) -> list[ProviderEntry]:
        tag_set = set(tags)
        return [p for p in self._providers if p.enabled and tag_set.issubset(set(p.tags))]

    # ── Mutations ──────────────────────────────────────────────────────

    def add(self, entry: ProviderEntry) -> None:
        entry.validate()
        if self.get(entry.id):
            raise ProviderError(f"provider {entry.id!r} already exists")
        self._providers.append(entry)
        self._save()

    def update(self, entry: ProviderEntry) -> None:
        entry.validate()
        for i, p in enumerate(self._providers):
            if p.id == entry.id:
                self._providers[i] = entry
                self._save()
                return
        raise ProviderError(f"provider {entry.id!r} not found")

    def remove(self, provider_id: str) -> None:
        before = len(self._providers)
        self._providers = [p for p in self._providers if p.id != provider_id]
        if len(self._providers) == before:
            raise ProviderError(f"provider {provider_id!r} not found")
        self._save()

    def test(self, provider_id: str) -> dict[str, Any]:
        """Probe a provider and update its status + models list."""
        entry = self.get(provider_id)
        if not entry:
            raise ProviderError(f"provider {provider_id!r} not found")
        result = probe_provider(entry)
        entry.status = "reachable" if result["valid"] else "unreachable"
        entry.available_models = result.get("models", [])
        entry.last_probed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._save()
        return result

    @classmethod
    def load(cls, path: Path | None = None) -> ProviderRegistry:
        return cls(path=path)
