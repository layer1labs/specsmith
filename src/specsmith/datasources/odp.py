# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""USPTO Open Data Portal (ODP) data source client.

ODP provides application metadata, prosecution transactions, assignments,
continuity data, and patent term adjustment. No API key required.
"""

from __future__ import annotations

from typing import Any

from specsmith.datasources.base import DataSourceError, http_get

BASE_URL = "https://developer.uspto.gov/ibd-api/v1"


class ODPClient:
    """USPTO Open Data Portal client bundled with specsmith."""

    name = "USPTO Open Data Portal"
    source_id = "odp"

    def test_connection(self) -> dict[str, Any]:
        try:
            data = http_get(f"{BASE_URL}/application/grants?rows=1", timeout=10)
            return {
                "available": True,
                "message": "ODP online",
                "latency_ms": data.get("_latency_ms", 0),
            }
        except DataSourceError as exc:
            return {"available": False, "message": str(exc), "latency_ms": 0}

    def search(
        self, query: str, *, detail: str = "minimal", limit: int = 25, offset: int = 0, **kwargs: Any,
    ) -> dict[str, Any]:
        """Search patent applications via ODP."""
        params = f"searchText={query}&start={offset}&rows={min(limit, 100)}"
        data = http_get(f"{BASE_URL}/application/grants?{params}")
        results = data.get("response", {}).get("docs", data.get("results", []))
        return {"source": self.source_id, "detail": detail, "total": len(results), "results": results, "count": len(results)}

    def get(self, app_number: str, **kwargs: Any) -> dict[str, Any]:
        """Get application data by number."""
        data = http_get(f"{BASE_URL}/application/{app_number}")
        return data

    def get_continuity(self, app_number: str) -> dict[str, Any]:
        """Get patent family/continuity data."""
        return http_get(f"{BASE_URL}/application/{app_number}/continuity")

    def get_transactions(self, app_number: str) -> dict[str, Any]:
        """Get prosecution transaction history."""
        return http_get(f"{BASE_URL}/application/{app_number}/transactions")

    def get_assignment(self, app_number: str) -> dict[str, Any]:
        """Get assignment/ownership records."""
        return http_get(f"{BASE_URL}/application/{app_number}/assignment")

    def get_adjustment(self, app_number: str) -> dict[str, Any]:
        """Get patent term adjustment (PTA) data."""
        return http_get(f"{BASE_URL}/application/{app_number}/adjustment")
