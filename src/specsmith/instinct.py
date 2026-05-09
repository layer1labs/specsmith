# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Instinct persistence system (REQ-221..REQ-227).

Instincts are patterns extracted from successful agent sessions and promoted
by the user via ``specsmith instinct learn``.  They are injected into the
system prompt at session start (REQ-238) and updated based on application
outcome (REQ-225).

Storage: ``.specsmith/instincts.json`` (gitignored — session-local knowledge).

Data contract:
    Each instinct record contains:
    - id            : unique slug (auto-generated or user-supplied)
    - trigger_pattern : natural-language pattern that activates this instinct
    - content         : the advice / learned behaviour
    - confidence      : float 0.0–1.0 (increases on accept, decreases on reject)
    - project_scope   : project root path, or "" for global instincts
    - created         : ISO-8601 creation timestamp
    - last_used       : ISO-8601 last application timestamp
    - use_count       : total number of times applied
"""

from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Data model (REQ-222)
# ---------------------------------------------------------------------------


def _ISO_NOW() -> str:  # noqa: N802
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class InstinctRecord:
    """A single learned instinct (REQ-222)."""

    id: str
    trigger_pattern: str
    content: str
    confidence: float = 0.7
    project_scope: str = ""  # "" = global; absolute path = project-scoped
    created: str = field(default_factory=_ISO_NOW)
    last_used: str = field(default_factory=_ISO_NOW)
    use_count: int = 0

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("InstinctRecord id must be non-empty")
        if not self.trigger_pattern or not self.trigger_pattern.strip():
            raise ValueError("InstinctRecord trigger_pattern must be non-empty")
        if not self.content or not self.content.strip():
            raise ValueError("InstinctRecord content must be non-empty")
        self.confidence = max(0.0, min(1.0, float(self.confidence)))

    # ------------------------------------------------------------------
    # Update helpers (REQ-225)
    # ------------------------------------------------------------------

    def record_accepted(self) -> None:
        """Increase confidence when this instinct is accepted by the user."""
        self.confidence = min(1.0, self.confidence + 0.05)
        self.use_count += 1
        self.last_used = _ISO_NOW()

    def record_rejected(self) -> None:
        """Decrease confidence when this instinct is rejected."""
        self.confidence = max(0.0, self.confidence - 0.10)
        self.use_count += 1
        self.last_used = _ISO_NOW()

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> InstinctRecord:
        return cls(
            id=str(raw.get("id") or "").strip(),
            trigger_pattern=str(raw.get("trigger_pattern") or "").strip(),
            content=str(raw.get("content") or "").strip(),
            confidence=float(raw.get("confidence", 0.7)),
            project_scope=str(raw.get("project_scope") or "").strip(),
            created=str(raw.get("created") or _ISO_NOW()),
            last_used=str(raw.get("last_used") or _ISO_NOW()),
            use_count=int(raw.get("use_count", 0)),
        )


# ---------------------------------------------------------------------------
# Store (REQ-221 / REQ-226)
# ---------------------------------------------------------------------------

_STORE_FILE = Path(".specsmith") / "instincts.json"


class InstinctStore:
    """Loads, persists, and queries instinct records (REQ-221).

    The store lives at ``.specsmith/instincts.json`` relative to the project
    root.  It is gitignored so instincts are session-local by default; the
    export/import commands (REQ-226) allow sharing them.
    """

    def __init__(self, root: Path) -> None:
        self._path = root / _STORE_FILE
        self._records: dict[str, InstinctRecord] = {}
        self._load()

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw_list = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(raw_list, list):
                return
            for raw in raw_list:
                if isinstance(raw, dict):
                    rec = InstinctRecord.from_dict(raw)
                    self._records[rec.id] = rec
        except Exception:  # noqa: BLE001
            pass  # Corrupt store — start fresh

    def save(self) -> None:
        """Write the store to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = [r.to_dict() for r in self._records.values()]
        self._path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add(
        self,
        trigger_pattern: str,
        content: str,
        *,
        project_scope: str = "",
        confidence: float = 0.7,
        instinct_id: str | None = None,
    ) -> InstinctRecord:
        """Create a new instinct record and persist it (REQ-224)."""
        if instinct_id is None:
            slug = re.sub(r"[^a-z0-9]+", "-", trigger_pattern.lower().strip())[:40]
            instinct_id = f"{slug}-{uuid.uuid4().hex[:6]}"

        rec = InstinctRecord(
            id=instinct_id,
            trigger_pattern=trigger_pattern.strip(),
            content=content.strip(),
            confidence=confidence,
            project_scope=project_scope,
        )
        self._records[instinct_id] = rec
        self.save()
        return rec

    def get(self, instinct_id: str) -> InstinctRecord | None:
        return self._records.get(instinct_id)

    def remove(self, instinct_id: str) -> bool:
        if instinct_id in self._records:
            del self._records[instinct_id]
            self.save()
            return True
        return False

    def all(self) -> list[InstinctRecord]:
        """All instincts, sorted by confidence descending (REQ-227)."""
        return sorted(self._records.values(), key=lambda r: r.confidence, reverse=True)

    def for_project(self, project_root: str) -> list[InstinctRecord]:
        """Global instincts plus those scoped to ``project_root``."""
        return [r for r in self.all() if r.project_scope == "" or r.project_scope == project_root]

    # ------------------------------------------------------------------
    # Confidence updates (REQ-225)
    # ------------------------------------------------------------------

    def record_accepted(self, instinct_id: str) -> None:
        if rec := self._records.get(instinct_id):
            rec.record_accepted()
            self.save()

    def record_rejected(self, instinct_id: str) -> None:
        if rec := self._records.get(instinct_id):
            rec.record_rejected()
            self.save()

    # ------------------------------------------------------------------
    # Export / Import (REQ-226)
    # ------------------------------------------------------------------

    def export_markdown(self) -> str:
        """Render instincts as Markdown for sharing."""
        if not self._records:
            return "# Instincts\n\n*(no instincts recorded)*\n"
        lines: list[str] = ["# Instincts\n"]
        for r in self.all():
            scope = f" _(project: {r.project_scope})_" if r.project_scope else ""
            lines.append(
                f"## {r.id}{scope}\n"
                f"**Trigger:** {r.trigger_pattern}  \n"
                f"**Content:** {r.content}  \n"
                f"**Confidence:** {r.confidence:.2f}  "
                f"**Used:** {r.use_count}×  "
                f"**Created:** {r.created}\n"
            )
        return "\n".join(lines)

    def import_from_path(self, path: Path) -> int:
        """Load instincts from a JSON export file.  Returns count imported."""
        try:
            raw_list = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw_list, list):
                return 0
            count = 0
            for raw in raw_list:
                if isinstance(raw, dict):
                    rec = InstinctRecord.from_dict(raw)
                    if rec.id not in self._records:
                        self._records[rec.id] = rec
                        count += 1
            self.save()
            return count
        except Exception:  # noqa: BLE001
            return 0


# ---------------------------------------------------------------------------
# Session-end extraction (REQ-223)
# ---------------------------------------------------------------------------


def extract_candidate_instincts(
    session_text: str,
    min_length: int = 30,
) -> list[dict[str, str]]:
    """Scan ``session_text`` for patterns worth promoting to instincts.

    Returns a list of ``{trigger_pattern, content}`` dicts that the user can
    review and optionally promote via ``specsmith instinct learn``.

    Heuristic (Round 1): extract any non-trivial repeated commands or
    explicit patterns the agent marked with ``PATTERN:`` or ``INSTINCT:``.
    More sophisticated ML-based extraction is planned for Phase 2.

    REQ-223: SESSION_END hook must call this.
    """
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()

    # Look for explicit PATTERN: / INSTINCT: annotations in session text.
    for m in re.finditer(r"(?:PATTERN|INSTINCT):\s*(.+?)(?:\n|$)", session_text, re.IGNORECASE):
        text = m.group(1).strip()
        if len(text) >= min_length and text not in seen:
            seen.add(text)
            candidates.append({"trigger_pattern": text, "content": text})

    # Extract repeated shell commands (3+ chars, appears 2+ times).
    commands = re.findall(r"`([^`]{3,80})`", session_text)
    from collections import Counter

    for cmd, count in Counter(commands).items():
        if count >= 2 and cmd not in seen:
            seen.add(cmd)
            candidates.append(
                {
                    "trigger_pattern": f"run {cmd}",
                    "content": f"Run `{cmd}` when this situation arises.",
                }
            )

    return candidates[:10]  # Cap at 10 candidates per session


# ---------------------------------------------------------------------------
# System-prompt injection (REQ-238)
# ---------------------------------------------------------------------------


def build_instinct_prompt_section(
    store: InstinctStore,
    project_root: str,
    *,
    token_budget: int = 2000,
) -> str:
    """Return a Markdown section injecting relevant instincts into the prompt.

    Respects the ``token_budget`` (approximate character limit) so the
    context window is not overwhelmed.  High-confidence instincts appear first.
    """
    instincts = store.for_project(project_root)
    if not instincts:
        return ""

    lines: list[str] = ["## Active Instincts (learned patterns)\n"]
    chars = 0
    for r in instincts:
        entry = f"- **{r.trigger_pattern}** ({r.confidence:.0%} confidence):  \n  {r.content}\n"
        chars += len(entry)
        if chars > token_budget:
            break
        lines.append(entry)

    return "\n".join(lines)
