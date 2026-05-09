# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""USPTO Final Petition Decisions (FPD) data source client.

Search and retrieve petition decisions from the USPTO Director's office.
"""

from __future__ import annotations

import urllib.parse
from typing import Any, cast

from specsmith.datasources.base import DataSourceError, http_get

BASE_URL = "https://developer.uspto.gov/ds-api/fpd/v1/records"


class FPDClient:
    """Final Petition Decisions client bundled with specsmith."""

    name = "USPTO Final Petition Decisions"
    source_id = "fpd"

    def test_connection(self) -> dict[str, Any]:
        try:
            data = http_get(f"{BASE_URL}?criteria=*:*&rows=1", timeout=10)
            total = data.get("response", {}).get("numFound", 0)
            return {
                "available": True,
                "message": f"FPD online ({total:,} decisions)",
                "latency_ms": data.get("_latency_ms", 0),
            }
        except DataSourceError as exc:
            return {"available": False, "message": str(exc), "latency_ms": 0}

    def search(
        self,
        query: str,
        *,
        detail: str = "minimal",
        limit: int = 25,
        offset: int = 0,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Search petition decisions."""
        params = urllib.parse.urlencode(
            {"criteria": query or "*:*", "start": offset, "rows": min(limit, 200)}
        )
        data = http_get(f"{BASE_URL}?{params}")
        resp = data.get("response", {})
        results = resp.get("docs", [])
        return {
            "source": self.source_id,
            "detail": detail,
            "total": resp.get("numFound", 0),
            "results": results,
            "count": len(results),
        }

    def get(self, petition_id: str, **kwargs: Any) -> dict[str, Any]:
        """Get a specific petition decision."""
        data = http_get(f"{BASE_URL}?criteria=id:{petition_id}&rows=1")
        docs = data.get("response", {}).get("docs", [])
        if not docs:
            raise DataSourceError(f"Petition {petition_id} not found")
        return cast(dict[str, Any], docs[0])

    def search_by_application(self, app_number: str, **kwargs: Any) -> dict[str, Any]:
        """Get all petitions for an application."""
        return self.search(
            f"applicationNumberText:{app_number}", detail="balanced", limit=50, **kwargs
        )
