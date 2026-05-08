# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""USPTO Enriched Citations data source client.

Provides office action citation search via Solr/Lucene queries. Data
available from October 2017 forward.
"""

from __future__ import annotations

import urllib.parse
from typing import Any

from specsmith.datasources.base import DataSourceError, http_get

BASE_URL = "https://developer.uspto.gov/ds-api/oa_citations/v2/records"


MINIMAL_FIELDS = "patentApplicationNumber,citedDocumentIdentifier,groupArtUnitNumber,citationCategoryCode,officeActionDate,examinerIndicator"
BALANCED_FIELDS = MINIMAL_FIELDS + ",passageLocationText,firstApplicantNameText,decisionTypeCode,techCenter"


class CitationsClient:
    """USPTO Enriched Citations client bundled with specsmith."""

    name = "USPTO Enriched Citations"
    source_id = "citations"

    def test_connection(self) -> dict[str, Any]:
        try:
            data = http_get(f"{BASE_URL}?criteria=*:*&rows=1", timeout=10)
            total = data.get("response", {}).get("numFound", 0)
            return {"available": True, "message": f"Citations online ({total:,} records)", "latency_ms": data.get("_latency_ms", 0)}
        except DataSourceError as exc:
            return {"available": False, "message": str(exc), "latency_ms": 0}

    def search(
        self, query: str, *, detail: str = "minimal", limit: int = 25, offset: int = 0, **kwargs: Any,
    ) -> dict[str, Any]:
        """Search citations via Solr/Lucene query syntax."""
        fl = BALANCED_FIELDS if detail in ("balanced", "complete") else MINIMAL_FIELDS
        params = urllib.parse.urlencode({"criteria": query or "*:*", "start": offset, "rows": min(limit, 200), "fl": fl})
        data = http_get(f"{BASE_URL}?{params}")
        resp = data.get("response", {})
        results = resp.get("docs", [])
        return {"source": self.source_id, "detail": detail, "total": resp.get("numFound", 0), "results": results, "count": len(results)}

    def get(self, citation_id: str, **kwargs: Any) -> dict[str, Any]:
        """Get a specific citation by ID."""
        data = http_get(f"{BASE_URL}?criteria=id:{citation_id}&rows=1")
        docs = data.get("response", {}).get("docs", [])
        if not docs:
            raise DataSourceError(f"Citation {citation_id} not found")
        return docs[0]

    def search_by_application(self, app_number: str, **kwargs: Any) -> dict[str, Any]:
        """Get all citations for an application."""
        return self.search(f"patentApplicationNumber:{app_number}", detail="balanced", limit=100, **kwargs)
