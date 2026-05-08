# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""PatentsView data source client — disambiguated US patent search.

PatentsView (patentsview.org) provides the richest search API for US
patents including disambiguated inventor/assignee IDs, CPC/IPC
classification, claims text, and detailed descriptions.

All methods use stdlib urllib — no external dependencies.
"""

from __future__ import annotations

import urllib.parse
from typing import Any

from specsmith.datasources.base import DataSourceError, http_get

BASE_URL = "https://search.patentsview.org/api/v1"


# ---------------------------------------------------------------------------
# Field sets for progressive disclosure
# ---------------------------------------------------------------------------

MINIMAL_FIELDS = [
    "patent_id",
    "patent_title",
    "patent_date",
    "patent_num_claims",
]

BALANCED_FIELDS = MINIMAL_FIELDS + [
    "patent_abstract",
    "patent_type",
    "assignees.assignee_organization",
    "inventors.inventor_first_name",
    "inventors.inventor_last_name",
    "cpcs.cpc_group_id",
    "cpcs.cpc_group_title",
]

COMPLETE_FIELDS = BALANCED_FIELDS + [
    "application.app_number",
    "application.app_date",
    "patent_num_cited_by_us_patents",
    "patent_num_us_patent_citations",
    "ipcs.ipc_class",
]


def _field_set(detail: str) -> list[str]:
    if detail == "complete":
        return COMPLETE_FIELDS
    if detail == "balanced":
        return BALANCED_FIELDS
    return MINIMAL_FIELDS


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class PatentsViewClient:
    """First-class PatentsView search client bundled with specsmith."""

    name = "PatentsView"
    source_id = "patentsview"

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {}
        if self._api_key:
            h["X-Api-Key"] = self._api_key
        return h

    def test_connection(self) -> dict[str, Any]:
        """Check PatentsView API availability."""
        try:
            url = f"{BASE_URL}/patent/?q={{\"_gte\":{{\"patent_date\":\"2024-01-01\"}}}}&f=[\"patent_id\"]&o={{\"per_page\":1}}"
            data = http_get(url, headers=self._headers(), timeout=10)
            count = data.get("total_patent_count", 0)
            return {
                "available": True,
                "message": f"PatentsView online ({count:,} total patents)",
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
        search_type: str = "any",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Search patents by text query.

        Args:
            query: Search terms for title and abstract.
            detail: "minimal", "balanced", or "complete".
            limit: Max results (max 1000).
            offset: Pagination offset.
            search_type: "any" (OR), "all" (AND), or "phrase" (exact).
        """
        fields = _field_set(detail)

        # Build the query filter.
        if search_type == "phrase":
            q = {"_text_phrase": {"patent_title": query}}
        elif search_type == "all":
            q = {"_text_all": {"patent_title": query}}
        else:
            q = {"_text_any": {"patent_title": query}}

        params = {
            "q": q,
            "f": fields,
            "o": {"page": (offset // limit) + 1, "per_page": min(limit, 1000)},
        }

        import json

        url = f"{BASE_URL}/patent/?q={urllib.parse.quote(json.dumps(params['q']))}&f={urllib.parse.quote(json.dumps(params['f']))}&o={urllib.parse.quote(json.dumps(params['o']))}"

        try:
            data = http_get(url, headers=self._headers())
        except DataSourceError:
            raise

        patents = data.get("patents", [])
        return {
            "source": self.source_id,
            "detail": detail,
            "total": data.get("total_patent_count", len(patents)),
            "results": patents,
            "count": len(patents),
        }

    def get(self, patent_id: str, **kwargs: Any) -> dict[str, Any]:
        """Get a single patent by ID."""
        import json

        q = {"patent_id": patent_id}
        f = COMPLETE_FIELDS
        url = f"{BASE_URL}/patent/?q={urllib.parse.quote(json.dumps(q))}&f={urllib.parse.quote(json.dumps(f))}&o={urllib.parse.quote(json.dumps({'per_page': 1}))}"

        data = http_get(url, headers=self._headers())
        patents = data.get("patents", [])
        if not patents:
            raise DataSourceError(f"Patent {patent_id} not found")
        return patents[0]

    def get_claims(self, patent_id: str) -> dict[str, Any]:
        """Get all claims text for a patent."""
        import json

        q = {"patent_id": patent_id}
        f = ["patent_id", "claims.claim_text", "claims.claim_sequence"]
        url = f"{BASE_URL}/patent/?q={urllib.parse.quote(json.dumps(q))}&f={urllib.parse.quote(json.dumps(f))}&o={urllib.parse.quote(json.dumps({'per_page': 1}))}"

        data = http_get(url, headers=self._headers())
        patents = data.get("patents", [])
        if not patents:
            raise DataSourceError(f"Patent {patent_id} not found")
        return {
            "patent_id": patent_id,
            "claims": patents[0].get("claims", []),
        }

    def search_inventors(
        self, name: str, *, limit: int = 100,
    ) -> dict[str, Any]:
        """Search for disambiguated inventors by name."""
        import json

        q = {"_text_any": {"inventor_last_name": name}}
        f = [
            "inventor_id",
            "inventor_first_name",
            "inventor_last_name",
            "inventor_total_num_patents",
        ]
        o = {"per_page": min(limit, 1000)}
        url = f"{BASE_URL}/inventor/?q={urllib.parse.quote(json.dumps(q))}&f={urllib.parse.quote(json.dumps(f))}&o={urllib.parse.quote(json.dumps(o))}"

        data = http_get(url, headers=self._headers())
        return {
            "source": self.source_id,
            "total": data.get("total_inventor_count", 0),
            "results": data.get("inventors", []),
        }

    def search_assignees(
        self, name: str, *, limit: int = 100,
    ) -> dict[str, Any]:
        """Search for disambiguated assignees (companies) by name."""
        import json

        q = {"_text_any": {"assignee_organization": name}}
        f = [
            "assignee_id",
            "assignee_organization",
            "assignee_total_num_patents",
        ]
        o = {"per_page": min(limit, 1000)}
        url = f"{BASE_URL}/assignee/?q={urllib.parse.quote(json.dumps(q))}&f={urllib.parse.quote(json.dumps(f))}&o={urllib.parse.quote(json.dumps(o))}"

        data = http_get(url, headers=self._headers())
        return {
            "source": self.source_id,
            "total": data.get("total_assignee_count", 0),
            "results": data.get("assignees", []),
        }

    def search_by_cpc(
        self, cpc_code: str, *, limit: int = 100,
    ) -> dict[str, Any]:
        """Search patents by CPC classification code."""
        import json

        q = {"_begins": {"cpc_group_id": cpc_code}}
        f = BALANCED_FIELDS
        o = {"per_page": min(limit, 1000)}
        url = f"{BASE_URL}/patent/?q={urllib.parse.quote(json.dumps(q))}&f={urllib.parse.quote(json.dumps(f))}&o={urllib.parse.quote(json.dumps(o))}"

        data = http_get(url, headers=self._headers())
        return {
            "source": self.source_id,
            "total": data.get("total_patent_count", 0),
            "results": data.get("patents", []),
        }
