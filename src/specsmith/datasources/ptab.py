# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""USPTO PTAB data source client.

Search IPR/PGR/CBM trial proceedings, ex parte appeals, and interference
proceedings at the Patent Trial and Appeal Board.
"""

from __future__ import annotations

import urllib.parse
from typing import Any

from specsmith.datasources.base import DataSourceError, http_get

BASE_URL = "https://developer.uspto.gov/ptab-api/v2"


class PTABClient:
    """PTAB proceedings client bundled with specsmith."""

    name = "USPTO PTAB"
    source_id = "ptab"

    def test_connection(self) -> dict[str, Any]:
        try:
            data = http_get(f"{BASE_URL}/trials?limit=1", timeout=10)
            total = data.get("metadata", {}).get("count", 0)
            return {"available": True, "message": f"PTAB online ({total:,} trials)", "latency_ms": data.get("_latency_ms", 0)}
        except DataSourceError as exc:
            return {"available": False, "message": str(exc), "latency_ms": 0}

    def search(
        self, query: str, *, detail: str = "minimal", limit: int = 25, offset: int = 0, **kwargs: Any,
    ) -> dict[str, Any]:
        """Search PTAB trial proceedings."""
        return self.search_trials(patent_number=query, limit=limit, offset=offset)

    def get(self, trial_number: str, **kwargs: Any) -> dict[str, Any]:
        """Get a specific trial by number."""
        data = http_get(f"{BASE_URL}/trials?trialNumber={trial_number}&limit=1")
        results = data.get("results", [])
        if not results:
            raise DataSourceError(f"Trial {trial_number} not found")
        return results[0]

    def search_trials(
        self,
        *,
        patent_number: str = "",
        petitioner_name: str = "",
        patent_owner_name: str = "",
        trial_type: str = "",
        trial_status: str = "",
        limit: int = 25,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search IPR/PGR/CBM trials with filters."""
        params: dict[str, str | int] = {"limit": min(limit, 100), "offset": offset}
        if patent_number:
            params["patentNumber"] = patent_number
        if petitioner_name:
            params["petitionerPartyName"] = petitioner_name
        if patent_owner_name:
            params["patentOwnerPartyName"] = patent_owner_name
        if trial_type:
            params["trialType"] = trial_type
        if trial_status:
            params["trialStatus"] = trial_status

        url = f"{BASE_URL}/trials?{urllib.parse.urlencode(params)}"
        data = http_get(url)
        results = data.get("results", [])
        return {"source": self.source_id, "total": data.get("metadata", {}).get("count", 0), "results": results, "count": len(results)}

    def search_appeals(
        self,
        *,
        application_number: str = "",
        patent_number: str = "",
        examiner_name: str = "",
        limit: int = 25,
    ) -> dict[str, Any]:
        """Search ex parte appeals."""
        params: dict[str, str | int] = {"limit": min(limit, 100)}
        if application_number:
            params["applicationNumber"] = application_number
        if patent_number:
            params["patentNumber"] = patent_number
        if examiner_name:
            params["examinerName"] = examiner_name

        url = f"{BASE_URL}/appeals?{urllib.parse.urlencode(params)}"
        data = http_get(url)
        results = data.get("results", [])
        return {"source": self.source_id, "total": data.get("metadata", {}).get("count", 0), "results": results, "count": len(results)}

    def get_documents(self, trial_number: str, *, limit: int = 50) -> dict[str, Any]:
        """Get document list for a trial."""
        url = f"{BASE_URL}/trials/{trial_number}/documents?limit={limit}"
        data = http_get(url)
        return {"trial_number": trial_number, "documents": data.get("results", []), "count": len(data.get("results", []))}
