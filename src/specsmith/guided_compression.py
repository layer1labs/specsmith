# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Guided Compression — epistemic-value-aware context compression.

Unlike the naive tiered compression in ``context_orchestrator.py``, guided
compression evaluates the *epistemic value* of each context element and
preserves what matters for governance continuity while discarding or
summarizing low-value content.

Epistemic value tiers:
  TIER_CRITICAL  — Never evict. Accepted requirements, sealed decisions,
                   active work items, phase state, confidence thresholds.
  TIER_HIGH      — Keep full text. Accepted preflights, verification results,
                   audit reports, recent ESDB records (last 7 days).
  TIER_MEDIUM    — Summarize to metadata. Conversation turns older than 24 h,
                   intermediate notes, tool output summaries.
  TIER_LOW       — Compress to one-liner. Debug traces, verbose tool output,
                   repeated status checks, raw JSON dumps.
  TIER_DISCARD   — Drop entirely. Temporary files, lock files, stale PID files,
                   duplicate status reports.

Usage::

    from specsmith.guided_compression import GuidedCompressor

    compressor = GuidedCompressor(project_root)
    result = compressor.compress(context, target_fill_pct=50.0)
    # result.compressed_context fits within target fill percentage
    # result.summary shows what was preserved vs compressed

REQ-308: Context orchestrator — automatic tiered optimization (extends)
REQ-312: specsmith context optimize CLI command (extends)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Epistemic value classification
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EpistemicProfile:
    """Defines the epistemic value profile for a context element.

    Args:
        element_type: Type identifier (e.g. "requirement", "conversation_turn").
        base_tier: Default epistemic tier.
        min_tier: Lowest tier this element can be downgraded to.
        max_tier: Highest tier (never above TIER_CRITICAL).
        retention_hours: Hours to keep full text before summarization (-1 = forever).
        summary_template: Format string for summarization.
    """

    element_type: str
    base_tier: str = "TIER_MEDIUM"
    min_tier: str = "TIER_DISCARD"
    max_tier: str = "TIER_HIGH"
    retention_hours: float = -1  # -1 = forever
    summary_template: str = "[Summarized {count} {type} entries]"


# Predefined profiles for known element types.
EPIDEMIC_PROFILES: dict[str, EpistemicProfile] = {
    "requirement": EpistemicProfile(
        element_type="requirement",
        base_tier="TIER_CRITICAL",
        min_tier="TIER_CRITICAL",
        max_tier="TIER_CRITICAL",
        retention_hours=-1,
        summary_template="[REQ {id}: {title} ({status})]",
    ),
    "work_item": EpistemicProfile(
        element_type="work_item",
        base_tier="TIER_HIGH",
        min_tier="TIER_MEDIUM",
        max_tier="TIER_HIGH",
        retention_hours=-1,
        summary_template="[WI {id}: {title} ({status})]",
    ),
    "seal": EpistemicProfile(
        element_type="seal",
        base_tier="TIER_CRITICAL",
        min_tier="TIER_CRITICAL",
        max_tier="TIER_CRITICAL",
        retention_hours=-1,
        summary_template="[Seal {seal_type}: {description}]",
    ),
    "preflight": EpistemicProfile(
        element_type="preflight",
        base_tier="TIER_HIGH",
        min_tier="TIER_MEDIUM",
        max_tier="TIER_HIGH",
        retention_hours=720,  # 30 days
        summary_template="[Preflight {decision}: {instruction}]",
    ),
    "verification": EpistemicProfile(
        element_type="verification",
        base_tier="TIER_HIGH",
        min_tier="TIER_MEDIUM",
        max_tier="TIER_HIGH",
        retention_hours=720,  # 30 days
        summary_template="[Verify {decision}: {instruction}]",
    ),
    "audit": EpistemicProfile(
        element_type="audit",
        base_tier="TIER_HIGH",
        min_tier="TIER_MEDIUM",
        max_tier="TIER_HIGH",
        retention_hours=720,  # 30 days
        summary_template="[Audit: {passed}/{total} checks passed]",
    ),
    "phase_state": EpistemicProfile(
        element_type="phase_state",
        base_tier="TIER_CRITICAL",
        min_tier="TIER_CRITICAL",
        max_tier="TIER_CRITICAL",
        retention_hours=-1,
        summary_template="[Phase: {phase} ({pct}%)]",
    ),
    "conversation_turn": EpistemicProfile(
        element_type="conversation_turn",
        base_tier="TIER_MEDIUM",
        min_tier="TIER_LOW",
        max_tier="TIER_HIGH",
        retention_hours=24,
        summary_template="[Conversation: {role} — {word_count} words]",
    ),
    "tool_output": EpistemicProfile(
        element_type="tool_output",
        base_tier="TIER_LOW",
        min_tier="TIER_DISCARD",
        max_tier="TIER_MEDIUM",
        retention_hours=48,
        summary_template="[Tool {name}: {exit_code}]",
    ),
    "ledger_entry": EpistemicProfile(
        element_type="ledger_entry",
        base_tier="TIER_MEDIUM",
        min_tier="TIER_LOW",
        max_tier="TIER_HIGH",
        retention_hours=720,  # 30 days
        summary_template="[Ledger: {entry_type} — {description}]",
    ),
    "esdb_record": EpistemicProfile(
        element_type="esdb_record",
        base_tier="TIER_MEDIUM",
        min_tier="TIER_LOW",
        max_tier="TIER_HIGH",
        retention_hours=168,  # 7 days
        summary_template="[ESDB {key}: {data_type}]",
    ),
    "debug_trace": EpistemicProfile(
        element_type="debug_trace",
        base_tier="TIER_LOW",
        min_tier="TIER_DISCARD",
        max_tier="TIER_MEDIUM",
        retention_hours=24,
        summary_template="[Debug trace: {message}]",
    ),
    "status_check": EpistemicProfile(
        element_type="status_check",
        base_tier="TIER_LOW",
        min_tier="TIER_DISCARD",
        max_tier="TIER_MEDIUM",
        retention_hours=1,
        summary_template="[Status: {result}]",
    ),
}


# ---------------------------------------------------------------------------
# Compression result
# ---------------------------------------------------------------------------


@dataclass
class GuidedCompressionResult:
    """Result of a guided compression operation.

    Args:
        original_size: Original context size in characters.
        compressed_size: Compressed context size in characters.
        compression_ratio: Ratio of compressed/original (0–1).
        elements_preserved: Count of elements kept at full fidelity.
        elements_summarized: Count of elements summarized.
        elements_discarded: Count of elements dropped entirely.
        actions: List of human-readable action descriptions.
        summary: High-level summary of what was done.
    """

    original_size: int = 0
    compressed_size: int = 0
    compression_ratio: float = 1.0
    elements_preserved: int = 0
    elements_summarized: int = 0
    elements_discarded: int = 0
    actions: list[str] = field(default_factory=list)
    summary: str = ""

    @property
    def space_saved(self) -> int:
        """Bytes saved by compression."""
        return self.original_size - self.compressed_size

    @property
    def space_saved_pct(self) -> float:
        """Percentage of space saved."""
        if self.original_size == 0:
            return 0.0
        return (self.space_saved / self.original_size) * 100


# ---------------------------------------------------------------------------
# Context element classification
# ---------------------------------------------------------------------------


@dataclass
class ContextElement:
    """A single element within the context to be compressed.

    Args:
        element_id: Unique identifier.
        element_type: Type from EPIDEMIC_PROFILES keys.
        content: The full content.
        metadata: Additional metadata for classification.
        created_at: Timestamp (ISO 8601).
    """

    element_id: str
    element_type: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    @property
    def profile(self) -> EpistemicProfile:
        """Return the epistemic profile for this element type."""
        return EPIDEMIC_PROFILES.get(
            self.element_type,
            EpistemicProfile(
                element_type=self.element_type,
                base_tier="TIER_MEDIUM",
                retention_hours=24,
            ),
        )

    @property
    def age_hours(self) -> float:
        """Return age in hours from created_at."""
        if not self.created_at:
            return 0.0
        try:
            ts = datetime.fromisoformat(self.created_at)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - ts).total_seconds() / 3600
        except (ValueError, TypeError):
            return 0.0

    @property
    def size(self) -> int:
        """Size in characters."""
        return len(self.content)


# ---------------------------------------------------------------------------
# Guided compressor
# ---------------------------------------------------------------------------


class GuidedCompressor:
    """Epistemic-value-aware context compressor.

    Usage::

        compressor = GuidedCompressor(project_root)
        elements = [
            ContextElement("req-1", "requirement", "REQ-001: ..."),
            ContextElement("turn-1", "conversation_turn", "User: ..."),
        ]
        result = compressor.compress(elements, target_fill_pct=50.0)
    """

    def __init__(self, project_root: str | Path) -> None:
        self.root = Path(project_root).resolve()

    def compress(
        self,
        elements: list[ContextElement],
        *,
        target_fill_pct: float = 50.0,
        max_output_chars: int | None = None,
    ) -> GuidedCompressionResult:
        """Compress context elements based on epistemic value.

        Args:
            elements: List of context elements to compress.
            target_fill_pct: Target fill percentage (0–100). Lower = more aggressive.
            max_output_chars: Hard cap on output size in characters.

        Returns:
            GuidedCompressionResult with compressed elements and summary.
        """
        original_size = sum(e.size for e in elements)
        result = GuidedCompressionResult(original_size=original_size)

        if not elements:
            result.summary = "No elements to compress."
            return result

        # Classify each element
        classified = self._classify_elements(elements)

        # Apply compression tiers
        preserved: list[ContextElement] = []
        summarized: list[tuple[ContextElement, str]] = []
        discarded: list[ContextElement] = []

        for elem in classified:
            action = self._decide_action(elem, target_fill_pct)
            if action == "preserve":
                preserved.append(elem)
                result.elements_preserved += 1
            elif action == "summarize":
                summary = self._summarize_element(elem)
                summarized.append((elem, summary))
                result.elements_summarized += 1
            else:
                discarded.append(elem)
                result.elements_discarded += 1

        # Build compressed context
        compressed_parts: list[str] = []
        for elem in preserved:
            compressed_parts.append(elem.content)
        for _elem, summary in summarized:
            compressed_parts.append(summary)

        compressed_text = "\n\n".join(compressed_parts)
        result.compressed_size = len(compressed_text)
        result.compression_ratio = (
            result.compressed_size / original_size if original_size > 0 else 1.0
        )

        # Build actions list
        for elem in preserved:
            result.actions.append(f"Preserved {elem.element_type} ({elem.element_id})")
        for elem, _summary in summarized:
            result.actions.append(f"Summarized {elem.element_type} ({elem.element_id})")
        for elem in discarded:
            result.actions.append(f"Discarded {elem.element_type} ({elem.element_id})")

        result.summary = (
            f"Compressed {len(elements)} elements: "
            f"{result.elements_preserved} preserved, "
            f"{result.elements_summarized} summarized, "
            f"{result.elements_discarded} discarded. "
            f"Space saved: {result.space_saved_pct:.1f}%."
        )

        return result

    # ------------------------------------------------------------------
    # Internal classification & decision logic
    # ------------------------------------------------------------------

    def _classify_elements(self, elements: list[ContextElement]) -> list[ContextElement]:
        """Classify elements, adjusting tier based on age and metadata."""
        classified: list[ContextElement] = []
        for elem in elements:
            profile = elem.profile
            # Downgrade based on age
            if profile.retention_hours > 0 and elem.age_hours > profile.retention_hours:
                # Element has aged out of full retention
                current_tier = profile.base_tier
                tiers = ["TIER_CRITICAL", "TIER_HIGH", "TIER_MEDIUM", "TIER_LOW", "TIER_DISCARD"]
                current_idx = tiers.index(current_tier) if current_tier in tiers else 2
                # Downgrade by one tier, but not below min_tier
                new_idx = min(current_idx + 1, tiers.index(profile.min_tier))
                adjusted_tier = tiers[new_idx]
            else:
                adjusted_tier = profile.base_tier

            elem.metadata["adjusted_tier"] = adjusted_tier
            classified.append(elem)
        return classified

    def _decide_action(self, elem: ContextElement, target_fill_pct: float) -> str:
        """Decide whether to preserve, summarize, or discard an element.

        Args:
            elem: The classified context element.
            target_fill_pct: Target fill percentage.

        Returns:
            One of "preserve", "summarize", "discard".
        """
        adjusted_tier = elem.metadata.get("adjusted_tier", elem.profile.base_tier)

        # Critical elements are always preserved
        if adjusted_tier == "TIER_CRITICAL":
            return "preserve"

        # High elements preserved unless very aggressive compression needed
        if adjusted_tier == "TIER_HIGH":
            if target_fill_pct <= 30:
                return "summarize"
            return "preserve"

        # Medium elements summarized if target is aggressive
        if adjusted_tier == "TIER_MEDIUM":
            if target_fill_pct <= 40:
                return "summarize"
            if target_fill_pct <= 20:
                return "discard"
            return "preserve"

        # Low elements summarized or discarded
        if adjusted_tier == "TIER_LOW":
            if target_fill_pct <= 30:
                return "discard"
            return "summarize"

        # Discard tier is always discarded
        return "discard"

    def _summarize_element(self, elem: ContextElement) -> str:
        """Create a summary for an element being compressed.

        Args:
            elem: The element to summarize.

        Returns:
            Summary string.
        """
        profile = elem.profile
        template = profile.summary_template

        # Extract metadata for template substitution
        meta = elem.metadata.copy()
        meta["type"] = elem.element_type
        meta["id"] = elem.element_id
        meta["word_count"] = len(elem.content.split())

        # Try to extract common fields from content
        content = elem.content
        for field_name in ("title", "status", "description", "message", "result"):
            match = re.search(rf'"{field_name}"\s*:\s*"([^"]*)"', content)
            if match:
                meta[field_name] = match.group(1)[:100]
                break

        # Also check metadata for common fields
        for field_name in ("title", "status", "description", "message", "result"):
            if field_name in elem.metadata:
                meta[field_name] = str(elem.metadata[field_name])[:100]

        try:
            return template.format(**meta)
        except (KeyError, IndexError):
            return (
                f"[Summarized {elem.element_type} ({elem.element_id}): {len(elem.content)} chars]"
            )

    def _classify_esdb_key(self, key: str) -> str:
        """Classify an ESDB key into an element type."""
        if key.startswith("REQ-"):
            return "requirement"
        if key.startswith("WI-"):
            return "work_item"
        if key.startswith("SEAL-"):
            return "seal"
        if key.startswith("PHASE-"):
            return "phase_state"
        if key.startswith("EFF-"):
            return "esdb_record"
        return "esdb_record"

    def compress_from_conversation(
        self,
        history: list[dict[str, Any]],
        *,
        target_fill_pct: float = 50.0,
    ) -> GuidedCompressionResult:
        """Compress conversation history based on epistemic value.

        Args:
            history: List of {role, content, ...} conversation turns.
            target_fill_pct: Target fill percentage.

        Returns:
            GuidedCompressionResult.
        """
        elements: list[ContextElement] = []

        for i, turn in enumerate(history):
            role = turn.get("role", "unknown")
            elements.append(
                ContextElement(
                    element_id=f"turn-{i}",
                    element_type="conversation_turn",
                    content=json.dumps(turn, ensure_ascii=False),
                    metadata={"role": role, "index": i},
                )
            )

        return self.compress(elements, target_fill_pct=target_fill_pct)

    def compress_from_esdb(
        self,
        *,
        target_fill_pct: float = 50.0,
        max_records: int = 100,
    ) -> GuidedCompressionResult:
        """Compress active SQLite ESDB records based on epistemic value."""
        try:
            from specsmith.esdb import SqliteStore
        except ImportError:
            return GuidedCompressionResult(summary="ESDB module not available.")

        with SqliteStore(self.root) as store:
            records = store.query(status="active")[:max_records]

        elements: list[ContextElement] = []
        for record in records:
            record_id = str(record.id)
            element_type = self._classify_esdb_key(record_id)
            content = json.dumps(
                {
                    "id": record_id,
                    "kind": record.kind,
                    "label": record.label,
                    "data": record.data,
                },
                ensure_ascii=False,
                indent=2,
            )
            elements.append(
                ContextElement(
                    element_id=record_id,
                    element_type=element_type,
                    content=content,
                    metadata={
                        "source": "esdb",
                        "kind": record.kind,
                        "branch": record.branch,
                    },
                )
            )

        return self.compress(elements, target_fill_pct=target_fill_pct)

    def compress_from_ledger(
        self,
        *,
        keep_recent_entries: int = 10,
        target_fill_pct: float = 50.0,
    ) -> GuidedCompressionResult:
        """Compress LEDGER.md entries based on epistemic value.

        Args:
            keep_recent_entries: Number of recent entries to keep full.
            target_fill_pct: Target fill percentage.

        Returns:
            GuidedCompressionResult.
        """
        from specsmith.paths import find_ledger

        ledger_path = find_ledger(self.root)
        if not ledger_path or not ledger_path.exists():
            return GuidedCompressionResult(
                summary="LEDGER.md not found.",
            )

        text = ledger_path.read_text(encoding="utf-8")
        from specsmith.compressor import _split_ledger

        preamble, entries = _split_ledger(text)

        elements: list[ContextElement] = []
        for i, entry in enumerate(entries):
            # Extract entry metadata
            first_line = entry.split("\n", 1)[0].strip()
            status_match = re.search(r"Status:\s*(.+)", entry)
            status = status_match.group(1).strip() if status_match else "unknown"

            # Determine entry type from header
            if "Session" in first_line:
                entry_type = "session"
            elif "Entry" in first_line:
                entry_type = "entry"
            else:
                entry_type = "other"

            elements.append(
                ContextElement(
                    element_id=f"ledger-{i}",
                    element_type="ledger_entry",
                    content=entry,
                    metadata={
                        "first_line": first_line,
                        "status": status,
                        "entry_type": entry_type,
                    },
                )
            )

        # Mark recent entries as higher value
        for i, elem in enumerate(elements):
            reverse_idx = len(elements) - 1 - i
            if reverse_idx < keep_recent_entries:
                elem.metadata["is_recent"] = True
                elem.metadata["adjusted_tier"] = "TIER_HIGH"
            else:
                elem.metadata["is_recent"] = False

        return self.compress(elements, target_fill_pct=target_fill_pct)


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------


def guided_compress(
    project_root: str | Path,
    elements: list[ContextElement] | None = None,
    history: list[dict[str, Any]] | None = None,
    *,
    target_fill_pct: float = 50.0,
) -> GuidedCompressionResult:
    """Convenience function for guided compression.

    Args:
        project_root: Project root directory.
        elements: Optional list of ContextElement objects.
        history: Optional conversation history (list of {role, content}).
        target_fill_pct: Target fill percentage.

    Returns:
        GuidedCompressionResult.

    Example::

        result = guided_compress(
            "/path/to/project",
            history=[{"role": "user", "content": "..."}],
            target_fill_pct=40.0,
        )
    """
    compressor = GuidedCompressor(project_root)

    if history is not None:
        return compressor.compress_from_conversation(history, target_fill_pct=target_fill_pct)

    if elements is not None:
        return compressor.compress(elements, target_fill_pct=target_fill_pct)

    return GuidedCompressionResult(
        summary="No elements or history provided.",
    )
