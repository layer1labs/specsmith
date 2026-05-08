# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Patent Public Search (PPUBS) data source client.

PPUBS (ppubs.uspto.gov) provides daily-updated full-text search of US
patents and published applications. Prefer over PatentsView when you
need the most current data.

All methods use stdlib urllib — no external dependencies.
"""

from __future__ import annotations

from typing import Any, cast

from specsmith.datasources.base import DataSourceError, http_post

# PPUBS uses a POST-based search API.
SEARCH_URL = "https://ppubs.uspto.gov/dirsearch-public/searches/searchWithBeFamily"
DOCUMENT_URL = "https://ppubs.uspto.gov/dirsearch-public/patents"


class PPUBSClient:
    """Patent Public Search client bundled with specsmith."""

    name = "Patent Public Search (PPUBS)"
    source_id = "ppubs"

    def test_connection(self) -> dict[str, Any]:
        try:
            result = self.search("test", limit=1)
            return {
                "available": True,
                "message": f"PPUBS online ({result.get('total', 0)} results for probe)",
                "latency_ms": result.get("_latency_ms", 0),
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
        source_type: str = "USPAT",
        sort: str = "date_publ desc",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Search patents or applications via PPUBS.

        Args:
            query: USPTO search syntax (e.g., TTL/"neural network").
            source_type: "USPAT" for grants, "US-PGPUB" for applications.
            sort: Sort order (default: "date_publ desc").
        """
        payload = {
            "searchText": query,
            "fpiOnly": False,
            "start": offset,
            "pageCount": min(limit, 500),
            "sort": sort,
            "docTypes": [source_type],
        }

        data = http_post(SEARCH_URL, payload, timeout=20)
        results = data.get("patents", [])

        # Normalize to common format.
        normalized = []
        for r in results:
            entry: dict[str, Any] = {
                "guid": r.get("guid", ""),
                "title": r.get("inventionTitle", ""),
                "abstract": r.get("abstract", "") if detail != "minimal" else "",
                "publication_date": r.get("datePublished", ""),
                "patent_number": r.get("patentNumber", ""),
                "application_number": r.get("applicationNumber", ""),
            }
            if detail in ("balanced", "complete"):
                entry["inventors"] = r.get("inventorName", "")
                entry["assignee"] = r.get("assigneeName", "")
                entry["cpc_codes"] = r.get("cpcCodes", [])
            normalized.append(entry)

        return {
            "source": self.source_id,
            "detail": detail,
            "total": data.get("numFound", len(results)),
            "results": normalized,
            "count": len(normalized),
        }

    def get(self, patent_number: str, **kwargs: Any) -> dict[str, Any]:
        """Get a patent by number from PPUBS."""
        result = self.search(patent_number, limit=1, detail="complete")
        if not result["results"]:
            raise DataSourceError(f"Patent {patent_number} not found in PPUBS")
        return cast(dict[str, Any], result["results"][0])

    def search_applications(
        self,
        query: str,
        *,
        limit: int = 25,
        offset: int = 0,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Search published patent applications."""
        return self.search(query, limit=limit, offset=offset, source_type="US-PGPUB", **kwargs)
