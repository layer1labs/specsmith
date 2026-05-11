# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Natural-Language Governance Broker (REQ-084).

The broker translates plain-language user utterances into Specsmith-governed
work without the user having to reason about REQ IDs, TEST IDs, or work
items.

Boundary
--------
Per ARCHITECTURE.md "Nexus Broker Boundary":

* Specsmith is the only source of governance truth. The broker calls
  ``specsmith preflight`` and ``specsmith verify`` and renders their JSON
  output verbatim. It does **not** decide preflight outcomes itself.
* REQ/TEST/work-item IDs are hidden by default in user-facing narration.
  They are only revealed when ``verbose=True`` (mapped to ``/why`` or
  ``/show-governance`` in the REPL).
* Retries are bounded (REQ-014). The broker never retries forever.
* On stop-and-align (REQ-063), the broker surfaces a single clarifying
  question rather than guessing.
* The broker never drafts new REQs or TESTs without explicit user
  confirmation.

Design split
------------
The broker is intentionally **rule-based** for the steps where determinism
matters (intent classification, retry budgeting, JSON parsing) and only
defers to LLM-assisted narration for plain-language summaries. This keeps
governance behavior reproducible and testable without an LLM.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


def _safe_file_read(path: Path, encoding: str = "utf-8") -> str:
    """Read a file after validating it contains no path-traversal components.

    CodeQL ``py/path-injection``: reject any path whose components include
    ``..`` or null bytes before performing the read.
    """
    raw = str(path)
    if "\x00" in raw:
        raise ValueError(f"Path contains null byte: {raw!r}")
    for part in path.parts:
        if part in ("..", "..."):
            raise ValueError(f"Path traversal rejected: {raw!r}")
    return path.read_text(encoding=encoding)


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------


class Intent(str, Enum):
    """Coarse-grained user intent."""

    READ_ONLY_ASK = "read_only_ask"
    CHANGE = "change"
    RELEASE = "release"
    DESTRUCTIVE = "destructive"


# Patterns are intentionally simple and deterministic. They are checked in
# order; the first match wins. Destructive patterns must always win over
# change patterns to be conservative.
_DESTRUCTIVE_PATTERNS = (
    re.compile(r"\bdelete\b", re.IGNORECASE),
    re.compile(r"\bdrop\s+(database|table)\b", re.IGNORECASE),
    re.compile(r"\brm\s+-rf?\b", re.IGNORECASE),
    re.compile(r"\bforce[- ]push\b", re.IGNORECASE),
    re.compile(r"\bwipe\b", re.IGNORECASE),
    re.compile(r"\brevert\s+everything\b", re.IGNORECASE),
)

_RELEASE_PATTERNS = (
    re.compile(r"\brelease\b", re.IGNORECASE),
    re.compile(r"\bship\b", re.IGNORECASE),
    re.compile(r"\bpublish\s+(to\s+)?pypi\b", re.IGNORECASE),
    re.compile(r"\btag\s+v?\d", re.IGNORECASE),
    re.compile(r"\bbump\s+(the\s+)?version\b", re.IGNORECASE),
)

_CHANGE_PATTERNS = (
    re.compile(r"\b(fix|repair|patch)\b", re.IGNORECASE),
    re.compile(r"\b(add|implement|create|introduce|build)\b", re.IGNORECASE),
    re.compile(r"\b(refactor|rewrite|rename|extract)\b", re.IGNORECASE),
    re.compile(r"\b(update|migrate|upgrade)\b", re.IGNORECASE),
    re.compile(r"\b(remove|delete)\s+(the\s+)?(unused|stale|legacy)\b", re.IGNORECASE),
)

_READ_ONLY_PATTERNS = (
    re.compile(r"^\s*(what|how|where|why|when|who)\b", re.IGNORECASE),
    re.compile(r"\b(explain|describe|show|tell\s+me|list)\b", re.IGNORECASE),
    re.compile(r"\?\s*$"),
)


def classify_intent(utterance: str) -> Intent:
    """Classify the user's natural-language utterance.

    Order: DESTRUCTIVE > RELEASE > CHANGE > READ_ONLY_ASK > READ_ONLY_ASK
    (default).
    """
    if not utterance or not utterance.strip():
        return Intent.READ_ONLY_ASK
    text = utterance.strip()
    for p in _DESTRUCTIVE_PATTERNS:
        if p.search(text):
            return Intent.DESTRUCTIVE
    for p in _RELEASE_PATTERNS:
        if p.search(text):
            return Intent.RELEASE
    for p in _CHANGE_PATTERNS:
        if p.search(text):
            return Intent.CHANGE
    for p in _READ_ONLY_PATTERNS:
        if p.search(text):
            return Intent.READ_ONLY_ASK
    # Fallback: treat ambiguous utterances as read-only so we don't write
    # without explicit user intent.
    return Intent.READ_ONLY_ASK


# ---------------------------------------------------------------------------
# Scope inference
# ---------------------------------------------------------------------------


_REQ_HEADING = re.compile(r"^##\s+\d+\.\s+(?P<title>.+)\s*$", re.MULTILINE)
_REQ_ID = re.compile(r"-\s*\*\*ID:\*\*\s*(REQ-\d+)")
_REQ_DESC = re.compile(r"-\s*\*\*Description:\*\*\s*(.+)")

# A small stopword list to keep keyword matches meaningful.
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "have",
        "in",
        "is",
        "it",
        "its",
        "must",
        "of",
        "on",
        "or",
        "so",
        "that",
        "the",
        "this",
        "to",
        "was",
        "with",
        "you",
        "your",
    }
)


def _tokenize(text: str) -> set[str]:
    return {
        t.lower()
        for t in re.findall(r"[A-Za-z][A-Za-z_-]+", text)
        if len(t) > 2 and t.lower() not in _STOPWORDS
    }


@dataclass
class RequirementSummary:
    """Lightweight in-memory view of one REQ block."""

    req_id: str
    title: str
    description: str

    @property
    def text_blob(self) -> str:
        return f"{self.title}\n{self.description}"


def parse_requirements(req_md_path: Path) -> list[RequirementSummary]:
    """Parse REQUIREMENTS.md into ``RequirementSummary`` records.

    Best-effort: missing files yield an empty list.
    """
    if not req_md_path.is_file():
        return []
    try:
        text = _safe_file_read(req_md_path)
    except ValueError:
        return []
    out: list[RequirementSummary] = []
    blocks = re.split(r"^##\s+\d+\.\s+", text, flags=re.MULTILINE)[1:]
    for block in blocks:
        lines = block.splitlines()
        title = lines[0].strip() if lines else ""
        m_id = _REQ_ID.search(block)
        m_desc = _REQ_DESC.search(block)
        if not m_id:
            continue
        out.append(
            RequirementSummary(
                req_id=m_id.group(1),
                title=title,
                description=m_desc.group(1).strip() if m_desc else "",
            )
        )
    return out


@dataclass
class ScopeProposal:
    """Result of scope inference. Internal — REQ IDs hidden in narration."""

    matched_requirements: list[RequirementSummary] = field(default_factory=list)
    suggested_files: list[str] = field(default_factory=list)
    confidence: float = 0.0

    @property
    def is_known(self) -> bool:
        return bool(self.matched_requirements)


def infer_scope(
    utterance: str,
    req_md_path: Path,
    repo_index_path: Path | None = None,
    *,
    top_k: int = 3,
) -> ScopeProposal:
    """Infer the project scope affected by a natural-language utterance.

    Combines two deterministic signals:

    * Token overlap with each REQ block in ``REQUIREMENTS.md``.
    * Filename overlap from ``.repo-index/files.json`` (when present).
    """
    tokens = _tokenize(utterance)
    if not tokens:
        return ScopeProposal()

    # Score requirements by token overlap with title + description.
    scored: list[tuple[float, RequirementSummary]] = []
    for req in parse_requirements(req_md_path):
        req_tokens = _tokenize(req.text_blob)
        overlap = len(tokens & req_tokens)
        if overlap == 0:
            continue
        # Normalize by the smaller side so very short titles don't dominate.
        denom = max(1, min(len(tokens), len(req_tokens)))
        scored.append((overlap / denom, req))
    scored.sort(key=lambda x: -x[0])
    top_reqs = [r for _, r in scored[:top_k]]

    # File matches from .repo-index/files.json (best-effort, optional).
    suggested_files: list[str] = []
    if repo_index_path and repo_index_path.is_file():
        try:
            files = json.loads(_safe_file_read(repo_index_path))
        except (OSError, json.JSONDecodeError, ValueError):
            files = []
        for f in files:
            if not isinstance(f, str):
                continue
            stem = Path(f).stem.lower()
            if any(tok in stem or stem in tok for tok in tokens):
                suggested_files.append(f)
        suggested_files = suggested_files[:top_k]

    confidence = scored[0][0] if scored else 0.0
    return ScopeProposal(
        matched_requirements=top_reqs,
        suggested_files=suggested_files,
        confidence=round(confidence, 3),
    )


# ---------------------------------------------------------------------------
# Specsmith CLI wrappers (preflight / verify)
# ---------------------------------------------------------------------------


@dataclass
class PreflightDecision:
    """Wrapped Specsmith preflight outcome."""

    raw: dict[str, Any]
    decision: str = "unknown"
    work_item_id: str = ""
    requirement_ids: list[str] = field(default_factory=list)
    test_case_ids: list[str] = field(default_factory=list)
    confidence_target: float = 0.0
    instruction: str = ""

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> PreflightDecision:
        return cls(
            raw=payload,
            decision=str(payload.get("decision", "unknown")),
            work_item_id=str(payload.get("work_item_id", "")),
            requirement_ids=list(payload.get("requirement_ids", [])),
            test_case_ids=list(payload.get("test_case_ids", [])),
            confidence_target=float(payload.get("confidence_target", 0.0) or 0.0),
            instruction=str(payload.get("instruction", "")),
        )

    @property
    def accepted(self) -> bool:
        return self.decision.lower() == "accepted"


def _resolve_specsmith_executable() -> str:
    """Pick the best `specsmith` invocation on this machine."""
    found = shutil.which("specsmith")
    if found:
        return found
    return "specsmith"


def run_preflight(
    utterance: str,
    project_dir: Path,
    *,
    runner: Callable[[list[str]], subprocess.CompletedProcess[str]] | None = None,
) -> PreflightDecision:
    """Invoke ``specsmith preflight <utterance> --json`` and parse the result.

    A ``runner`` callable can be injected for tests; production calls
    ``subprocess.run`` against the installed CLI.
    """
    cmd = [
        _resolve_specsmith_executable(),
        "preflight",
        utterance,
        "--project-dir",
        str(project_dir),
        "--json",
    ]
    if runner is None:
        proc = subprocess.run(  # noqa: S603 - argv is a list, never shell
            cmd, capture_output=True, text=True, timeout=60, check=False
        )
    else:
        proc = runner(cmd)
    out = (proc.stdout or "").strip()
    if not out:
        # Specsmith doesn't yet ship a `preflight` subcommand by default; the
        # broker treats missing CLI support as "needs_clarification" rather
        # than fabricating a decision (REQ-084).
        return PreflightDecision(
            raw={"decision": "needs_clarification", "reason": "preflight unavailable"},
            decision="needs_clarification",
            instruction="Specsmith preflight is not available on this machine.",
        )
    try:
        payload = json.loads(out)
    except json.JSONDecodeError:
        return PreflightDecision(
            raw={"decision": "needs_clarification", "stdout": out},
            decision="needs_clarification",
            instruction="Could not parse preflight output as JSON.",
        )
    return PreflightDecision.from_json(payload)


# ---------------------------------------------------------------------------
# Plain-language narration
# ---------------------------------------------------------------------------


_GOVERNANCE_ID = re.compile(r"\b(REQ-\d+|TEST-\d+|WI-[A-Z0-9-]+)\b")


def _strip_governance_ids(text: str) -> str:
    """Remove REQ-/TEST-/WI- tokens from text for hidden-by-default mode."""
    return _GOVERNANCE_ID.sub("the relevant area", text)


def narrate_plan(
    intent: Intent,
    scope: ScopeProposal,
    decision: PreflightDecision,
    *,
    verbose: bool = False,
) -> str:
    """Render a plain-language plan for the user.

    By default IDs are hidden. With ``verbose=True`` (e.g. user typed `/why`),
    governance IDs are revealed.
    """
    lines: list[str] = []
    if intent == Intent.READ_ONLY_ASK:
        lines.append("Read-only request \u2014 no changes will be made.")
    elif intent == Intent.RELEASE:
        lines.append("Release request \u2014 will require explicit confirmation before publishing.")
    elif intent == Intent.DESTRUCTIVE:
        lines.append(
            "Destructive request \u2014 will require explicit confirmation before running."
        )
    else:
        lines.append("Change request \u2014 will run under Specsmith governance.")

    if scope.is_known:
        titles = ", ".join(r.title for r in scope.matched_requirements[:3])
        lines.append(f"Touches: {titles}.")
    else:
        lines.append("No matching governance scope found; will ask before drafting anything new.")

    if decision.accepted:
        lines.append("Specsmith approved this work.")
    elif decision.decision == "needs_clarification":
        # Surface only one clarifying question (REQ-063 stop-and-align).
        question = decision.instruction or "Specsmith needs more detail to approve this."
        lines.append(f"Need clarification: {question}")
    elif decision.decision in {"blocked", "rejected"}:
        lines.append(f"Specsmith {decision.decision} this work: {decision.instruction}")
    else:
        lines.append("Specsmith decision pending.")

    rendered = "\n".join(lines)
    if verbose:
        # In verbose mode, append the underlying governance IDs.
        ids = []
        if decision.work_item_id:
            ids.append(f"work-item={decision.work_item_id}")
        if decision.requirement_ids:
            ids.append("reqs=" + ",".join(decision.requirement_ids))
        if decision.test_case_ids:
            ids.append("tests=" + ",".join(decision.test_case_ids))
        if ids:
            rendered += "\n[governance: " + " ".join(ids) + "]"
        return rendered
    return _strip_governance_ids(rendered)


# ---------------------------------------------------------------------------
# Bounded execution wrapper
# ---------------------------------------------------------------------------


@dataclass
class RunResult:
    """Outcome of execute_with_governance.

    REQ-096 adds the ``strategy`` field, which is one of the canonical
    retry-strategy labels from REQ-028 when ``success`` is False:

      - ``narrow_scope``: too much was attempted; cut scope and retry.
      - ``expand_scope``: not enough context; broaden scope and retry.
      - ``fix_tests``: tests are wrong or missing; repair tests first.
      - ``rollback``: the change is destructive or contradictory; revert.
      - ``stop``: confidence cannot improve; stop and ask the user.

    On success the field is left as the empty string.
    """

    success: bool
    attempts: int
    confidence: float = 0.0
    summary: str = ""
    clarifying_question: str = ""
    strategy: str = ""


# REQ-014: retries are bounded. The default is intentionally small.
DEFAULT_RETRY_BUDGET = 3

# REQ-028 / REQ-096: canonical retry strategies.
RETRY_STRATEGIES = (
    "narrow_scope",
    "expand_scope",
    "fix_tests",
    "rollback",
    "stop",
)


def classify_retry_strategy(report: dict[str, Any], decision: PreflightDecision) -> str:
    """Map an executor failure report to one of the canonical retry strategies.

    The classification is deterministic and inspects:
      - ``test_results`` for non-zero failure counts (-> fix_tests),
      - ``summary`` text for rollback / contradiction / scope hints,
      - ``confidence`` distance from the target (>0.5 below -> narrow_scope,
        otherwise expand_scope when scope was unknown),
      - falls through to ``stop`` when nothing else matches.
    """
    summary_text = str(report.get("summary", report.get("message", "")) or "").lower()
    test_results = report.get("test_results") or {}
    confidence = float(report.get("confidence", 0.0) or 0.0)

    # Rollback signal: explicit destructive / contradiction language.
    rollback_tokens = ("rollback", "contradiction", "revert", "corrupt", "data loss")
    if any(tok in summary_text for tok in rollback_tokens):
        return "rollback"

    # Test failures dominate everything else.
    failed_count = 0
    if isinstance(test_results, dict):
        for key in ("failed", "failures", "errors"):
            try:
                failed_count += int(test_results.get(key, 0) or 0)
            except (TypeError, ValueError):
                continue
        raw_text = str(test_results.get("raw", "") or "")
        if "failed" in raw_text.lower():
            failed_count = max(failed_count, 1)
    if failed_count > 0:
        return "fix_tests"

    # Scope hints.
    if "too broad" in summary_text or "narrow" in summary_text:
        return "narrow_scope"
    if "out of scope" in summary_text or "expand" in summary_text:
        return "expand_scope"

    # Confidence-distance heuristic.
    if decision.confidence_target > 0:
        gap = decision.confidence_target - confidence
        if gap >= 0.5:
            return "narrow_scope"
        if gap >= 0.2 and not getattr(decision, "requirement_ids", []):
            return "expand_scope"

    return "stop"


def execute_with_governance(
    decision: PreflightDecision,
    *,
    executor: Callable[[PreflightDecision, int], dict[str, Any]],
    retry_budget: int = DEFAULT_RETRY_BUDGET,
) -> RunResult:
    """Run the work with Specsmith governance and a hard retry budget.

    ``executor(decision, attempt)`` is the side-effecting callable that
    performs the work and returns a Specsmith verify-shaped JSON dict. The
    broker checks ``equilibrium`` and ``confidence``; if the run is below
    threshold after the budget is exhausted, the broker returns a single
    clarifying question instead of looping. The ``RunResult`` carries a
    canonical ``strategy`` label (REQ-096) when retries are exhausted.
    """
    if retry_budget < 1:
        retry_budget = 1

    last_summary = ""
    last_confidence = 0.0
    last_report: dict[str, Any] = {}
    for attempt in range(1, retry_budget + 1):
        report = executor(decision, attempt) or {}
        last_report = report
        equilibrium = bool(report.get("equilibrium", False))
        confidence = float(report.get("confidence", 0.0) or 0.0)
        last_confidence = confidence
        last_summary = str(report.get("summary", report.get("message", "")))

        if equilibrium and confidence >= decision.confidence_target:
            return RunResult(
                success=True,
                attempts=attempt,
                confidence=confidence,
                summary=last_summary or "Verified by Specsmith.",
            )

    # Bounded retries exhausted \u2014 stop-and-align (REQ-063) plus a
    # canonical retry-strategy label (REQ-096).
    strategy = classify_retry_strategy(last_report, decision)
    question = (
        "I tried this a few times and Specsmith isn't yet satisfied. "
        f"Suggested next step: {strategy}. "
        "Could you tell me which behavior you expected, in one sentence?"
    )
    return RunResult(
        success=False,
        attempts=retry_budget,
        confidence=last_confidence,
        summary=last_summary or "Verification did not reach equilibrium.",
        clarifying_question=question,
        strategy=strategy,
    )


# ---------------------------------------------------------------------------
# Convenience top-level entry point used by the REPL.
# ---------------------------------------------------------------------------


def broker_step(
    utterance: str,
    project_dir: Path,
    *,
    verbose: bool = False,
    runner: Callable[[list[str]], subprocess.CompletedProcess[str]] | None = None,
) -> str:
    """Single-shot, side-effect-free broker pipeline used by the REPL.

    This intentionally stops *before* execute_with_governance because actually
    performing the work requires a wired-up Nexus orchestrator, which the REPL
    constructs separately. ``broker_step`` is the deterministic preflight +
    narrate pipeline.
    """
    intent = classify_intent(utterance)
    req_md = project_dir / "REQUIREMENTS.md"
    repo_index = project_dir / ".repo-index" / "files.json"
    scope = infer_scope(utterance, req_md, repo_index_path=repo_index)
    decision = run_preflight(utterance, project_dir, runner=runner)
    return narrate_plan(intent, scope, decision, verbose=verbose)
