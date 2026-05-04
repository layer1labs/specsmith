# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Bring-Your-Own-Endpoint (BYOE) data model and persistence (REQ-142).

Specsmith historically hard-coded a closed provider list (``ollama`` /
``anthropic`` / ``openai`` / ``gemini`` / ``mistral``). This module
introduces a generic OpenAI-v1-compatible endpoint store so users can
register self-hosted vLLM, llama.cpp ``server``, LM Studio, TGI, or any
other ``/v1/chat/completions``-shaped backend and pick between several
side-by-side.

Storage layout (``~/.specsmith/endpoints.json``):

.. code-block:: json

    {
      "schema_version": 1,
      "default_endpoint_id": "home-vllm",
      "endpoints": [
        {
          "id": "home-vllm",
          "name": "Home vLLM",
          "base_url": "http://10.0.0.4:8000/v1",
          "auth": {"kind": "bearer-keyring",
                   "keyring_service": "specsmith",
                   "keyring_user": "endpoint:home-vllm"},
          "default_model": "Qwen/Qwen2.5-Coder-32B",
          "verify_tls": true,
          "tags": ["local", "coder"],
          "created_at": "2026-05-01T11:30:17Z"
        }
      ]
    }

Tokens are NEVER printed verbatim by anything in this module; ``list_all``
serialisation routes through :func:`Endpoint.to_public_dict` which
redacts inline tokens to ``"***"``.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
DEFAULT_KEYRING_SERVICE = "specsmith"

VALID_AUTH_KINDS = ("none", "bearer-inline", "bearer-env", "bearer-keyring")


class EndpointError(RuntimeError):
    """Raised for user-facing endpoint errors (validation, missing token, ...)."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class EndpointAuth:
    """Discriminated-union auth metadata.

    ``kind`` is one of:

    * ``none`` — no Authorization header (e.g. open vLLM on a trusted LAN).
    * ``bearer-inline`` — token stored verbatim in ``endpoints.json``.
      Only used when the user explicitly opts in; the on-disk plaintext
      is documented as insecure.
    * ``bearer-env`` — token resolved from ``token_env`` at call time.
    * ``bearer-keyring`` — token stored in the OS keyring under
      ``(keyring_service, keyring_user)``.
    """

    kind: str = "none"
    token: str = ""  # only set when kind == "bearer-inline"
    token_env: str = ""  # only set when kind == "bearer-env"
    keyring_service: str = DEFAULT_KEYRING_SERVICE
    keyring_user: str = ""

    def to_dict(self) -> dict[str, Any]:
        """On-disk shape (token included for ``bearer-inline``)."""
        out: dict[str, Any] = {"kind": self.kind}
        if self.kind == "bearer-inline":
            out["token"] = self.token
        elif self.kind == "bearer-env":
            out["token_env"] = self.token_env
        elif self.kind == "bearer-keyring":
            out["keyring_service"] = self.keyring_service
            out["keyring_user"] = self.keyring_user
        return out

    def to_public_dict(self) -> dict[str, Any]:
        """Redacted shape — never returns inline token bytes."""
        out: dict[str, Any] = {"kind": self.kind}
        if self.kind == "bearer-inline":
            out["token"] = "***"
        elif self.kind == "bearer-env":
            out["token_env"] = self.token_env
        elif self.kind == "bearer-keyring":
            out["keyring_service"] = self.keyring_service
            out["keyring_user"] = self.keyring_user
        return out

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> EndpointAuth:
        kind = str(raw.get("kind") or "none").strip()
        if kind not in VALID_AUTH_KINDS:
            raise EndpointError(f"invalid auth kind {kind!r}; expected one of {VALID_AUTH_KINDS}")
        return cls(
            kind=kind,
            token=str(raw.get("token") or ""),
            token_env=str(raw.get("token_env") or ""),
            keyring_service=str(raw.get("keyring_service") or DEFAULT_KEYRING_SERVICE),
            keyring_user=str(raw.get("keyring_user") or ""),
        )


@dataclass
class Endpoint:
    """A single OpenAI-v1-compatible endpoint registered for use with specsmith."""

    id: str
    name: str
    base_url: str
    auth: EndpointAuth = field(default_factory=EndpointAuth)
    default_model: str = ""
    verify_tls: bool = True
    tags: list[str] = field(default_factory=list)
    created_at: str = ""

    # ── Validation ─────────────────────────────────────────────────────────

    def validate(self) -> None:
        """Raise :class:`EndpointError` on structural problems."""
        if not self.id or not self.id.strip():
            raise EndpointError("endpoint id must be non-empty")
        if any(c.isspace() for c in self.id):
            raise EndpointError(f"endpoint id {self.id!r} must not contain whitespace")
        if not self.base_url.startswith(("http://", "https://")):
            raise EndpointError(
                f"endpoint base_url {self.base_url!r} must start with http:// or https://"
            )
        if self.auth.kind == "bearer-env" and not self.auth.token_env:
            raise EndpointError("auth.kind == 'bearer-env' requires a non-empty token_env")
        if self.auth.kind == "bearer-keyring" and not self.auth.keyring_user:
            raise EndpointError(
                "auth.kind == 'bearer-keyring' requires a keyring_user (defaults to endpoint:<id>)"
            )

    # ── Token resolution ───────────────────────────────────────────────────

    def resolve_token(self) -> str | None:
        """Return the bearer token for this endpoint, or ``None`` for unauthenticated.

        Order of resolution mirrors :data:`EndpointAuth.kind`. Errors are
        converted to :class:`EndpointError` so callers can surface a clean
        message instead of a stack trace.
        """
        kind = self.auth.kind
        if kind == "none":
            return None
        if kind == "bearer-inline":
            return self.auth.token or None
        if kind == "bearer-env":
            value = os.environ.get(self.auth.token_env, "").strip()
            if not value:
                raise EndpointError(
                    f"endpoint {self.id!r} expects token in env var "
                    f"{self.auth.token_env!r}, but it is unset"
                )
            return value
        if kind == "bearer-keyring":
            try:
                import keyring
            except Exception as exc:  # noqa: BLE001
                raise EndpointError(
                    "keyring is not available — install python-keyring or "
                    "switch the endpoint to --auth bearer-env"
                ) from exc
            try:
                value = keyring.get_password(self.auth.keyring_service, self.auth.keyring_user)
            except Exception as exc:  # noqa: BLE001
                raise EndpointError(f"keyring lookup failed: {exc}") from exc
            if not value:
                raise EndpointError(
                    f"endpoint {self.id!r} has no token stored in keyring "
                    f"({self.auth.keyring_service}/{self.auth.keyring_user})"
                )
            return str(value)
        raise EndpointError(f"unknown auth kind {kind!r}")

    # ── Health / discovery ─────────────────────────────────────────────────

    def health(self, *, timeout: float = 5.0) -> EndpointHealth:
        """Probe ``<base_url>/models`` and return a structured result.

        Network and HTTP errors are caught — the returned record always has
        ``ok`` populated. ``models`` is empty when the endpoint does not
        expose ``/models``; that is not an error in itself.
        """
        import urllib.error
        import urllib.request

        url = self.base_url.rstrip("/") + "/models"
        req = urllib.request.Request(url)  # noqa: S310 - user-supplied
        try:
            token = self.resolve_token()
        except EndpointError as exc:
            return EndpointHealth(
                ok=False, latency_ms=0.0, models=[], error=str(exc), status_code=None
            )
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        start = time.perf_counter()
        try:
            ctx = None
            if not self.verify_tls and url.startswith("https://"):
                import ssl

                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(  # noqa: S310 - user-supplied
                req, timeout=timeout, context=ctx
            ) as resp:
                latency_ms = (time.perf_counter() - start) * 1000.0
                payload = json.loads(resp.read().decode("utf-8"))
                models = _extract_model_ids(payload)
                return EndpointHealth(
                    ok=True,
                    latency_ms=latency_ms,
                    models=models,
                    error="",
                    status_code=int(resp.status),
                )
        except urllib.error.HTTPError as exc:
            return EndpointHealth(
                ok=False,
                latency_ms=(time.perf_counter() - start) * 1000.0,
                models=[],
                error=f"HTTP {exc.code}",
                status_code=int(exc.code),
            )
        except Exception as exc:  # noqa: BLE001
            return EndpointHealth(
                ok=False,
                latency_ms=(time.perf_counter() - start) * 1000.0,
                models=[],
                error=str(exc),
                status_code=None,
            )

    # ── Serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "base_url": self.base_url,
            "auth": self.auth.to_dict(),
            "default_model": self.default_model,
            "verify_tls": bool(self.verify_tls),
            "tags": list(self.tags),
            "created_at": self.created_at,
        }

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "base_url": self.base_url,
            "auth": self.auth.to_public_dict(),
            "default_model": self.default_model,
            "verify_tls": bool(self.verify_tls),
            "tags": list(self.tags),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Endpoint:
        return cls(
            id=str(raw.get("id") or "").strip(),
            name=str(raw.get("name") or "").strip(),
            base_url=str(raw.get("base_url") or "").strip(),
            auth=EndpointAuth.from_dict(raw.get("auth") or {}),
            default_model=str(raw.get("default_model") or "").strip(),
            verify_tls=bool(raw.get("verify_tls", True)),
            tags=[str(t) for t in (raw.get("tags") or [])],
            created_at=str(raw.get("created_at") or ""),
        )


@dataclass
class EndpointHealth:
    """Structured result of :meth:`Endpoint.health`."""

    ok: bool
    latency_ms: float
    models: list[str]
    error: str = ""
    status_code: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "latency_ms": round(self.latency_ms, 2),
            "models": list(self.models),
            "error": self.error,
            "status_code": self.status_code,
        }


def _extract_model_ids(payload: Any) -> list[str]:
    """Pull a list of model id strings out of an OpenAI ``/v1/models`` body.

    Tolerates the two common shapes (``{"data": [{"id": ...}]}`` from real
    OpenAI / vLLM and ``{"models": [...]}`` used by some proxies).
    """
    out: list[str] = []
    if isinstance(payload, dict):
        candidates = payload.get("data") or payload.get("models") or []
        if isinstance(candidates, list):
            for item in candidates:
                if isinstance(item, dict) and "id" in item:
                    out.append(str(item["id"]))
                elif isinstance(item, str):
                    out.append(item)
    return out


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------


def default_store_path() -> Path:
    """Resolve ``~/.specsmith/endpoints.json``, honouring ``SPECSMITH_HOME``."""
    base = os.environ.get("SPECSMITH_HOME", "").strip()
    home = Path(base) if base else Path.home() / ".specsmith"
    return home / "endpoints.json"


@dataclass
class EndpointStore:
    """Read/write wrapper around ``~/.specsmith/endpoints.json``.

    Tokens are never logged. Inline tokens (``auth.kind == "bearer-inline"``)
    land in the JSON unchanged, but :meth:`list_public` redacts them. The
    keyring-backed and env-backed paths never store secrets in the JSON at
    all.
    """

    path: Path
    schema_version: int = SCHEMA_VERSION
    default_endpoint_id: str = ""
    endpoints: list[Endpoint] = field(default_factory=list)

    # ── I/O ────────────────────────────────────────────────────────────────

    @classmethod
    def load(cls, path: Path | None = None) -> EndpointStore:
        target = path or default_store_path()
        if not target.exists():
            return cls(path=target)
        try:
            raw = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise EndpointError(
                f"endpoints store at {target} is corrupted: {exc}. "
                "Move it aside or fix the JSON to continue."
            ) from exc
        if not isinstance(raw, dict):
            raise EndpointError(f"endpoints store at {target} must be a JSON object")
        version = int(raw.get("schema_version") or 0)
        if version != SCHEMA_VERSION:
            raise EndpointError(
                f"endpoints store at {target} uses schema_version={version}; "
                f"this build of specsmith only understands {SCHEMA_VERSION}."
            )
        endpoints_raw = raw.get("endpoints") or []
        if not isinstance(endpoints_raw, list):
            raise EndpointError("endpoints store: 'endpoints' must be a list")
        endpoints = [Endpoint.from_dict(item) for item in endpoints_raw]
        return cls(
            path=target,
            schema_version=version,
            default_endpoint_id=str(raw.get("default_endpoint_id") or ""),
            endpoints=endpoints,
        )

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self.schema_version,
            "default_endpoint_id": self.default_endpoint_id,
            "endpoints": [e.to_dict() for e in self.endpoints],
        }
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        # Best-effort lock-down on POSIX
        import contextlib

        with contextlib.suppress(Exception):
            self.path.chmod(0o600)

    # ── CRUD ───────────────────────────────────────────────────────────────

    def add(self, endpoint: Endpoint, *, replace: bool = False) -> None:
        endpoint.validate()
        if not endpoint.created_at:
            endpoint.created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        existing = self._index(endpoint.id)
        if existing is not None:
            if not replace:
                raise EndpointError(
                    f"endpoint {endpoint.id!r} already exists. Use --replace to overwrite."
                )
            self.endpoints[existing] = endpoint
        else:
            self.endpoints.append(endpoint)
        if not self.default_endpoint_id:
            self.default_endpoint_id = endpoint.id

    def remove(self, endpoint_id: str) -> bool:
        idx = self._index(endpoint_id)
        if idx is None:
            return False
        self.endpoints.pop(idx)
        if self.default_endpoint_id == endpoint_id:
            self.default_endpoint_id = self.endpoints[0].id if self.endpoints else ""
        return True

    def get(self, endpoint_id: str) -> Endpoint:
        idx = self._index(endpoint_id)
        if idx is None:
            raise EndpointError(f"unknown endpoint id {endpoint_id!r}")
        return self.endpoints[idx]

    def get_default(self) -> Endpoint | None:
        if not self.default_endpoint_id:
            return None
        idx = self._index(self.default_endpoint_id)
        if idx is None:
            return None
        return self.endpoints[idx]

    def set_default(self, endpoint_id: str) -> None:
        if self._index(endpoint_id) is None:
            raise EndpointError(f"unknown endpoint id {endpoint_id!r}")
        self.default_endpoint_id = endpoint_id

    def list_all(self) -> list[Endpoint]:
        return list(self.endpoints)

    def list_public(self) -> list[dict[str, Any]]:
        return [e.to_public_dict() for e in self.endpoints]

    def resolve(self, endpoint_id: str | None) -> Endpoint:
        """Return the named endpoint, or the default if ``endpoint_id`` is empty."""
        if endpoint_id:
            return self.get(endpoint_id)
        default = self.get_default()
        if default is None:
            raise EndpointError(
                "no endpoint specified and no default is set. "
                "Run `specsmith endpoints add ...` to register one."
            )
        return default

    # ── Internals ──────────────────────────────────────────────────────────

    def _index(self, endpoint_id: str) -> int | None:
        for i, e in enumerate(self.endpoints):
            if e.id == endpoint_id:
                return i
        return None


__all__ = [
    "DEFAULT_KEYRING_SERVICE",
    "Endpoint",
    "EndpointAuth",
    "EndpointError",
    "EndpointHealth",
    "EndpointStore",
    "SCHEMA_VERSION",
    "VALID_AUTH_KINDS",
    "default_store_path",
]
