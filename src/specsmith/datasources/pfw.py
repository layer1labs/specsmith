# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Patent File Wrapper (PFW) data source client.

PFW provides prosecution document metadata and download URLs for patent
applications. Requires a MyUSPTO API key for full access.
"""

from __future__ import annotations

import urllib.parse
from typing import Any

from specsmith.datasources.base import DataSourceError, http_get

BASE_URL = "https://developer.uspto.gov/pfw-api/v1"


class PFWClient:
    """Patent File Wrapper client bundled with specsmith."""

    name = "Patent File Wrapper"
    source_id = "pfw"

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {}
        if self._api_key:
            h["X-Api-Key"] = self._api_key
        return h

    def test_connection(self) -> dict[str, Any]:
        try:
            data = http_get(f"{BASE_URL}/applications?rows=1", headers=self._headers(), timeout=10)
            return {"available": True, "message": "PFW online", "latency_ms": data.get("_latency_ms", 0)}
        except DataSourceError as exc:
            return {"available": False, "message": str(exc), "latency_ms": 0}

    def search(
        self, query: str, *, detail: str = "minimal", limit: int = 25, offset: int = 0, **kwargs: Any,
    ) -> dict[str, Any]:
        """Search patent applications."""
        params = urllib.parse.urlencode({"searchText": query, "start": offset, "rows": min(limit, 100)})
        data = http_get(f"{BASE_URL}/applications?{params}", headers=self._headers())
        results = data.get("patentFileWrapperDataBag", data.get("results", []))
        if not isinstance(results, list):
            results = [results] if results else []
        return {"source": self.source_id, "detail": detail, "total": data.get("recordTotalQuantity", len(results)), "results": results, "count": len(results)}

    def get(self, app_number: str, **kwargs: Any) -> dict[str, Any]:
        """Get application data."""
        return http_get(f"{BASE_URL}/applications/{app_number}", headers=self._headers())

    def get_documents(self, app_number: str, *, document_code: str = "", limit: int = 50) -> dict[str, Any]:
        """Get prosecution document metadata for an application."""
        url = f"{BASE_URL}/applications/{app_number}/documents"
        if document_code:
            url += f"?documentCode={document_code}"
        return http_get(url, headers=self._headers())
