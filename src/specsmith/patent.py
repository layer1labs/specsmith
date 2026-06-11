# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Patent — USPTO ODP API integration for patent prior art analysis.

Uses the USPTO Open Data Portal API (https://data.uspto.gov/apis/).
Requires a USPTO API key: set USPTO_API_KEY or use `specsmith auth set uspto`.

Resolves GitHub issue #10.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

_ODP_BASE = "https://data.uspto.gov/api/v1"
_TIMEOUT = 30


@dataclass
class PatentResult:
    """A single patent search result."""

    patent_number: str
    title: str
    abstract: str = ""
    filing_date: str = ""
    grant_date: str = ""
    inventors: list[str] = field(default_factory=list)
    assignee: str = ""
    classification: str = ""
    url: str = ""

    @property
    def short_summary(self) -> str:
        return f"{self.patent_number}: {self.title[:80]}"


@dataclass
class PriorArtReport:
    """Prior art analysis report for a claim."""

    claim_text: str
    query_used: str
    results: list[PatentResult] = field(default_factory=list)
    generated_at: str = ""
    api_key_used: bool = False
    error: str = ""

    @property
    def has_results(self) -> bool:
        return len(self.results) > 0

    def to_markdown(self) -> str:
        lines = [
            "# Prior Art Analysis",
            "",
            f"**Claim text:** {self.claim_text[:500]}",
            f"**Query used:** `{self.query_used}`",
            f"**Results found:** {len(self.results)}",
            f"**Generated:** {self.generated_at}",
            "",
        ]
        if self.error:
            lines.append(f"> ⚠ Error: {self.error}")
            lines.append("")

        if not self.results:
            lines.append("No prior art found for this query.")
            return "\n".join(lines)

        lines.append("## Prior Art Results")
        lines.append("")
        for i, result in enumerate(self.results, 1):
            lines.append(f"### {i}. {result.patent_number} — {result.title}")
            lines.append("")
            if result.filing_date:
                lines.append(f"- **Filed:** {result.filing_date}")
            if result.grant_date:
                lines.append(f"- **Granted:** {result.grant_date}")
            if result.assignee:
                lines.append(f"- **Assignee:** {result.assignee}")
            if result.inventors:
                lines.append(f"- **Inventors:** {', '.join(result.inventors[:3])}")
            if result.url:
                lines.append(f"- **URL:** {result.url}")
            if result.abstract:
                lines.append("")
                lines.append(f"**Abstract:** {result.abstract[:400]}...")
            lines.append("")

        return "\n".join(lines)


def _get_api_key() -> str | None:
    """Get USPTO API key from env or auth module."""
    import os

    key = os.environ.get("USPTO_API_KEY", "").strip()
    if key:
        return key
    try:
        from specsmith.auth import get_token

        return get_token("uspto")
    except ImportError:
        return None


def search_patents(
    query: str,
    *,
    max_results: int = 10,
    api_key: str | None = None,
) -> list[PatentResult]:
    """Search USPTO patent database via ODP API.

    Args:
        query: Full-text search query
        max_results: Maximum results to return (default 10)
        api_key: USPTO API key (auto-detected if not provided)

    Returns:
        List of PatentResult objects.
    """
    key = api_key or _get_api_key()

    params = {
        "q": query,
        "rows": min(max_results, 50),
        "offset": 0,
        "fields": (
            "patentNumber,patentTitle,inventionTitle,abstract,"
            "filingDate,grantDate,assigneeEntityName,inventorName"
        ),
    }
    url = f"{_ODP_BASE}/patents/applications/search?{urllib.parse.urlencode(params)}"

    headers: dict[str, str] = {"Accept": "application/json"}
    if key:
        headers["X-Api-Key"] = key

    try:
        req = urllib.request.Request(url, headers=headers)  # noqa: S310
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:  # noqa: S310
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            raise RuntimeError(
                "USPTO API key required. Set USPTO_API_KEY or run: specsmith auth set uspto"
            ) from e
        raise RuntimeError(f"USPTO API error: HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"USPTO API unreachable: {e}") from e

    results = []
    docs = data.get("results", data.get("patents", []))
    for doc in docs[:max_results]:
        pn = doc.get("patentNumber", doc.get("applicationNumber", ""))
        title = doc.get("inventionTitle", doc.get("patentTitle", "")) or doc.get("title", "")
        abstract = doc.get("abstract", "")
        if isinstance(abstract, list):
            abstract = " ".join(abstract)

        inventors_raw = doc.get("inventorName", [])
        if isinstance(inventors_raw, str):
            inventors_raw = [inventors_raw]
        inventors = [str(i) for i in inventors_raw]

        results.append(
            PatentResult(
                patent_number=str(pn),
                title=str(title),
                abstract=str(abstract)[:1000],
                filing_date=str(doc.get("filingDate", "")),
                grant_date=str(doc.get("grantDate", "")),
                inventors=inventors[:5],
                assignee=str(doc.get("assigneeEntityName", "")),
                url=f"https://patents.google.com/patent/US{pn}" if pn else "",
            )
        )

    return results


def analyze_prior_art(
    claim_text: str,
    *,
    max_results: int = 10,
    api_key: str | None = None,
) -> PriorArtReport:
    """Analyze prior art for a patent claim.

    Extracts key terms from the claim, constructs an optimized query,
    and searches USPTO. Returns a PriorArtReport with structured results.
    """
    # Build search query from claim text
    query = _extract_search_terms(claim_text)
    key = api_key or _get_api_key()

    report = PriorArtReport(
        claim_text=claim_text,
        query_used=query,
        generated_at=datetime.now().isoformat(),
        api_key_used=bool(key),
    )

    try:
        report.results = search_patents(query, max_results=max_results, api_key=key)
    except Exception as e:  # noqa: BLE001
        report.error = str(e)

    return report


def save_prior_art_report(report: PriorArtReport, output_dir: Path) -> Path:
    """Save a prior art report to the prior-art/ directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = report.generated_at[:10].replace("-", "")
    query_slug = "".join(c for c in report.query_used[:30] if c.isalnum() or c == "-")
    filename = f"prior-art-{slug}-{query_slug}.md"
    out_path = output_dir / filename
    out_path.write_text(report.to_markdown(), encoding="utf-8")
    return out_path


def _extract_search_terms(claim_text: str) -> str:
    """Extract key technical terms from claim text for USPTO search.

    Simple heuristic: extract noun phrases and technical terms,
    strip legal boilerplate.
    """
    import re

    # Remove common patent boilerplate
    boilerplate = [
        r"\bcomprising\b",
        r"\bconsisting of\b",
        r"\bwherein\b",
        r"\bclaim \d+\b",
        r"\bthe method of\b",
        r"\ba method for\b",
        r"\ban apparatus\b",
        r"\ba system\b",
        r"\bcharacterized by\b",
    ]
    text = claim_text
    for pattern in boilerplate:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    # Extract meaningful words (>3 chars, not common words)
    _STOP = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "into",
        "each",
        "when",
        "where",
        "said",
        "have",
        "been",
        "which",
    }
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text)
    significant = [w for w in words if w.lower() not in _STOP]

    # Take most significant terms (deduplicated, preserve order)
    seen: set[str] = set()
    unique: list[str] = []
    for w in significant:
        wl = w.lower()
        if wl not in seen:
            seen.add(wl)
            unique.append(w)

    # Build query from top terms
    terms = unique[:8]
    return " AND ".join(terms) if terms else claim_text[:200]
