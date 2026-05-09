# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Base DataSource protocol for all built-in data source clients.

Every data source (PatentsView, PPUBS, ODP, PFW, Citations, FPD, PTAB)
implements this protocol so the tool-calling layer can discover and
invoke them uniformly.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any, Protocol, cast, runtime_checkable

_log = logging.getLogger(__name__)


class DataSourceError(RuntimeError):
    """Raised for data source client errors (network, auth, parse)."""


@runtime_checkable
class DataSource(Protocol):
    """Protocol all specsmith data source clients implement."""

    @property
    def name(self) -> str:
        """Human-readable name (e.g. 'PatentsView')."""
        ...

    @property
    def source_id(self) -> str:
        """Machine identifier (e.g. 'patentsview')."""
        ...

    def test_connection(self) -> dict[str, Any]:
        """Check if the data source is reachable.

        Returns ``{"available": True/False, "message": "...", "latency_ms": N}``.
        """
        ...

    def search(
        self,
        query: str,
        *,
        detail: str = "minimal",
        limit: int = 25,
        offset: int = 0,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Search the data source.

        Args:
            query: Search terms or structured query.
            detail: Field set — "minimal", "balanced", or "complete".
            limit: Max results to return.
            offset: Pagination offset.

        Returns:
            ``{"results": [...], "total": N, "detail": "minimal", ...}``
        """
        ...

    def get(self, record_id: str, **kwargs: Any) -> dict[str, Any]:
        """Get a single record by ID.

        Returns the full record as a dict.
        """
        ...


# ---------------------------------------------------------------------------
# HTTP helpers shared by all clients
# ---------------------------------------------------------------------------


def http_get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """GET a JSON endpoint. Raises DataSourceError on failure."""
    req_headers = {"Accept": "application/json", "User-Agent": "specsmith/0.10"}
    if headers:
        req_headers.update(headers)
    try:
        req = urllib.request.Request(url, headers=req_headers, method="GET")
        t0 = time.monotonic()
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            body = resp.read().decode("utf-8")
        latency_ms = int((time.monotonic() - t0) * 1000)
        data = json.loads(body)
        if isinstance(data, dict):
            data["_latency_ms"] = latency_ms
        return cast(dict[str, Any], data)
    except urllib.error.HTTPError as exc:
        raise DataSourceError(f"HTTP {exc.code}: {exc.reason} — {url}") from exc
    except urllib.error.URLError as exc:
        raise DataSourceError(f"Connection error: {exc.reason} — {url}") from exc
    except json.JSONDecodeError as exc:
        raise DataSourceError(f"Invalid JSON from {url}: {exc}") from exc


def http_post(
    url: str,
    payload: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """POST JSON to an endpoint. Raises DataSourceError on failure."""
    req_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "specsmith/0.10",
    }
    if headers:
        req_headers.update(headers)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
        t0 = time.monotonic()
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            resp_body = resp.read().decode("utf-8")
        latency_ms = int((time.monotonic() - t0) * 1000)
        data = json.loads(resp_body)
        if isinstance(data, dict):
            data["_latency_ms"] = latency_ms
        return cast(dict[str, Any], data)
    except urllib.error.HTTPError as exc:
        raise DataSourceError(f"HTTP {exc.code}: {exc.reason} — {url}") from exc
    except urllib.error.URLError as exc:
        raise DataSourceError(f"Connection error: {exc.reason} — {url}") from exc
    except json.JSONDecodeError as exc:
        raise DataSourceError(f"Invalid JSON from {url}: {exc}") from exc
