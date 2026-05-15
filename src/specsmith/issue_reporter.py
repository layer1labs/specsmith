# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Issue reporter — duplicate-guarded GitHub issue filing (REQ-303, REQ-304).

All filing goes through this module.  The caller always gets a structured
result object; exceptions are never propagated to CLI callers.

Duplicate detection
-------------------
Title-word Jaccard similarity against the 5 most-relevant open issues
returned by GitHub Search.  Two thresholds:

    SIMILAR_THRESHOLD   ≥ 0.30 → listed as "similar" (informational)
    DUPLICATE_THRESHOLD ≥ 0.60 → listed as "likely duplicate" (blocks filing)

GitHub API strategy
-------------------
1. ``gh api <path>``  — uses the user's ``gh auth`` token (preferred).
2. Unauthenticated ``urllib.request``  — public repos only, rate-limited
   to ~10 req/min.  Used as fallback when ``gh`` is absent or unauthenticated.

Public surface
--------------
- ``search_issues(repo, query, *, max_results=5)`` → list[dict]
- ``check_duplicate(repo, title)`` → DuplicateCheckResult
- ``file_issue(repo, title, body, labels=(), *, force=False)`` → FiledIssueResult
- ``ai_enhance_report(title, body)`` → tuple[str, str]
- ``DuplicateBlockedError`` — raised by file_issue when duplicates exist
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

# ── Repo mapping ────────────────────────────────────────────────────────────

ORGS: dict[str, str] = {
    "kairos": "BitConcepts/kairos",
    "specsmith": "BitConcepts/specsmith",
}

_GITHUB_API = "https://api.github.com"
_TIMEOUT = 10  # seconds

# ── Similarity thresholds ────────────────────────────────────────────────────

SIMILAR_THRESHOLD: float = 0.30
DUPLICATE_THRESHOLD: float = 0.60


# ── Similarity helpers ───────────────────────────────────────────────────────


def _words(text: str) -> set[str]:
    """Normalised word set for Jaccard.  Strips punctuation; ignores stop words."""
    _STOP = {"the", "a", "an", "is", "in", "on", "at", "to", "of", "for", "not", "with", "can"}
    return {
        w.lower()
        for w in re.findall(r"[a-z0-9_]+", text.lower())
        if len(w) > 2 and w.lower() not in _STOP
    }


def _jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 0.0


# ── GitHub API helpers ───────────────────────────────────────────────────────


def _gh_available() -> bool:
    """Return True if ``gh`` is on PATH and authenticated."""
    try:
        r = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            timeout=5,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _gh_api_get(path: str) -> Any:
    """GET via ``gh api`` (auth-backed) or unauthenticated urllib fallback."""
    if _gh_available():
        try:
            result = subprocess.run(
                ["gh", "api", path],
                capture_output=True,
                text=True,
                timeout=_TIMEOUT,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            pass
    # Unauthenticated fallback
    url = f"{_GITHUB_API}/{path.lstrip('/')}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "specsmith-issue-reporter/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except Exception:  # noqa: BLE001
        return {}


def _gh_api_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """POST via ``gh api``.  Returns {\"error\": ...} dict on failure."""
    encoded = json.dumps(payload).encode()
    try:
        # Write payload to a temp file to avoid Windows quoting issues (H12)
        import tempfile  # noqa: PLC0415

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".json", delete=False) as tmp:
            tmp.write(encoded)
            tmp_path = tmp.name

        result = subprocess.run(
            [
                "gh",
                "api",
                "--method",
                "POST",
                "-H",
                "Accept: application/vnd.github+json",
                "--input",
                tmp_path,
                path,
            ],
            capture_output=True,
            timeout=30,
        )
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)

        if result.returncode == 0:
            return json.loads(result.stdout.decode()) if result.stdout else {}
        err = result.stderr.decode(errors="replace")
        return {"error": err or f"gh exited {result.returncode}"}
    except FileNotFoundError:
        return {"error": "gh CLI not found — install GitHub CLI to file issues"}
    except subprocess.TimeoutExpired:
        return {"error": "gh API call timed out after 30s"}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


# ── Public data classes ──────────────────────────────────────────────────────


@dataclass
class DuplicateCheckResult:
    """Result of a duplicate check.

    ``similar``    — issues with Jaccard ≥ SIMILAR_THRESHOLD  (informational)
    ``duplicates`` — issues with Jaccard ≥ DUPLICATE_THRESHOLD (blocks filing)
    ``error``      — non-empty on network or API failures
    """

    similar: list[dict[str, Any]] = field(default_factory=list)
    duplicates: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""

    @property
    def has_likely_duplicates(self) -> bool:
        return bool(self.duplicates)

    @property
    def blocked(self) -> bool:
        """True when filing should be blocked without ``--force``."""
        return self.has_likely_duplicates

    def to_dict(self) -> dict[str, Any]:
        return {
            "duplicates": self.duplicates,
            "similar": self.similar,
            "blocked": self.blocked,
            "error": self.error,
        }


@dataclass
class FiledIssueResult:
    """Result of a file_issue() call."""

    number: int = 0
    html_url: str = ""
    title: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return bool(self.html_url) and not self.error

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "number": self.number,
            "html_url": self.html_url,
            "title": self.title,
            "error": self.error,
        }


class DuplicateBlockedError(Exception):
    """Raised by file_issue() when likely duplicates exist and force=False."""

    def __init__(self, result: DuplicateCheckResult) -> None:
        self.result = result
        titles = [d["title"] for d in result.duplicates[:3]]
        super().__init__(f"Likely duplicate(s) found: {titles!r}. Use --force to file anyway.")


# ── Core functions ───────────────────────────────────────────────────────────


def search_issues(
    repo: str,
    query: str,
    *,
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """Search open issues in *repo* matching *query*.

    ``repo`` is a short name: ``"kairos"`` or ``"specsmith"``.
    Returns a list of issue dicts with keys: number, title, html_url, state.
    """
    full_repo = ORGS.get(repo, f"BitConcepts/{repo}")
    keywords = "+".join(list(_words(query))[:8])
    q = f"repo:{full_repo}+is:issue+is:open+{urllib.parse.quote(keywords, safe='+:')}"
    path = f"search/issues?q={q}&per_page={max_results}"
    data = _gh_api_get(path)
    items: list[dict[str, Any]] = data.get("items", []) if isinstance(data, dict) else []
    return [
        {
            "number": item.get("number"),
            "title": item.get("title", ""),
            "html_url": item.get("html_url", ""),
            "state": item.get("state", ""),
        }
        for item in items
        if isinstance(item, dict)
    ]


def check_duplicate(repo: str, title: str) -> DuplicateCheckResult:
    """Return a DuplicateCheckResult for the given *title* in *repo*.

    Never raises; errors are captured in ``.error``.
    """
    try:
        candidates = search_issues(repo, title, max_results=5)
    except Exception as exc:  # noqa: BLE001
        return DuplicateCheckResult(error=str(exc))

    title_words = _words(title)
    similar: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    for c in candidates:
        score = _jaccard(title_words, _words(c.get("title", "")))
        entry = {**c, "similarity": round(score, 3)}
        if score >= DUPLICATE_THRESHOLD:
            duplicates.append(entry)
        elif score >= SIMILAR_THRESHOLD:
            similar.append(entry)

    return DuplicateCheckResult(similar=similar, duplicates=duplicates)


def file_issue(
    repo: str,
    title: str,
    body: str,
    labels: tuple[str, ...] = (),
    *,
    force: bool = False,
) -> FiledIssueResult:
    """File a GitHub issue, blocking if likely duplicates exist.

    When ``force=False`` (the default) and ``check_duplicate()`` finds issues
    with Jaccard similarity ≥ DUPLICATE_THRESHOLD, raises ``DuplicateBlockedError``.
    Set ``force=True`` to bypass the check.

    Requires ``gh`` CLI to be installed and authenticated.
    """
    if not force:
        check = check_duplicate(repo, title)
        if check.blocked:
            raise DuplicateBlockedError(check)

    full_repo = ORGS.get(repo, f"BitConcepts/{repo}")
    payload: dict[str, Any] = {"title": title, "body": body}
    if labels:
        payload["labels"] = list(labels)

    data = _gh_api_post(f"repos/{full_repo}/issues", payload)
    if "error" in data:
        return FiledIssueResult(error=data["error"])
    return FiledIssueResult(
        number=data.get("number", 0),
        html_url=data.get("html_url", ""),
        title=data.get("title", title),
    )


def ai_enhance_report(title: str, body: str) -> tuple[str, str]:
    """Attempt to improve a bug report using the configured specsmith LLM.

    Returns ``(title, improved_body)``.  Falls back to originals on any
    error (LLM not configured, provider unavailable, timeout, etc.).

    The improvement prompt asks the model to add structured sections:
    Description, Steps to Reproduce, Expected Behavior, Actual Behavior.
    """
    prompt = (
        "You are a concise GitHub bug report formatter. "
        "Reformat the raw description below into a clean issue body with "
        "these markdown sections: **Description**, **Steps to Reproduce**, "
        "**Expected Behavior**, **Actual Behavior**, **Environment** (leave "
        "environment blank for user to fill in). "
        "Do NOT add commentary outside the sections.\n\n"
        f"Title: {title}\n\n"
        f"Raw description:\n{body}"
    )
    try:
        from specsmith.agent.chat_runner import run_single_prompt  # noqa: PLC0415

        improved = run_single_prompt(prompt, max_tokens=600)
        if improved and len(improved) > 80:
            return title, improved
    except (ImportError, Exception):  # noqa: BLE001
        pass
    # Second attempt: direct Ollama (zero-dep stdlib call)
    try:
        import json as _json  # noqa: PLC0415

        payload_bytes = _json.dumps(
            {
                "model": "qwen2.5:3b",
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 500},
            }
        ).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=payload_bytes,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = _json.loads(resp.read().decode())
            improved = data.get("response", "").strip()
            if improved and len(improved) > 80:
                return title, improved
    except Exception:  # noqa: BLE001
        pass
    return title, body
