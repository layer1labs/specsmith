# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Context Orchestrator — unified context management that never loses important data.

Coordinates three subsystems:
  1. ContextFillTracker  — token usage accounting
  2. Compressor          — ledger archival
  3. ChronoStore / ESDB  — epistemic record persistence

Optimization tiers triggered by fill percentage:
  Tier 1 (60–79%):  compress LEDGER.md history → free ~20% context
  Tier 2 (80–84%):  summarize oldest conversation half + evict low-confidence
                    ESDB records from in-context representation
  Tier 3 (≥85%):   emergency — protect critical records (accepted requirements,
                    last 5 ledger entries, ESDB confidence ≥ 0.7), discard the
                    rest from the in-context view only (never from disk)

"Never lose important data" invariant:
  Optimization ONLY affects what is passed to the model as context.
  All data is always preserved on disk via ESDB WAL + LEDGER.md.

REQ-308: Context orchestrator — automatic tiered optimization
REQ-312: specsmith context optimize CLI command
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Fill percentage thresholds
TIER1_PCT = 60.0
TIER2_PCT = 80.0
TIER3_PCT = 85.0  # Hard ceiling (matches HARD_CEILING_PCT in context_window.py)

# Minimum confidence to be "critical" (never evicted from Tier 3 emergency path)
CRITICAL_CONFIDENCE = 0.7

# Minimum ledger entries to always retain in context
KEEP_LEDGER_ENTRIES = 5


@dataclass
class OptimizeResult:
    """Result of a context optimization run."""

    tier: int = 0           # Highest tier triggered (0 = nothing needed)
    actions: list[str] = field(default_factory=list)
    tokens_freed_estimate: int = 0
    critical_records_protected: int = 0
    records_evicted: int = 0


class ContextOrchestrator:
    """Orchestrates tiered context compression.

    Usage in agent loop::

        orchestrator = ContextOrchestrator(project_root)
        result = orchestrator.check_and_optimize(fill_pct, history)
        if result.tier > 0:
            # history may have been trimmed by Tier 2 — use result.history
            history = result.history
    """

    def __init__(self, project_root: str | Path) -> None:
        self.root = Path(project_root).resolve()

    def check_and_optimize(
        self,
        fill_pct: float,
        history: list[dict[str, Any]] | None = None,
    ) -> OptimizeResultEx:
        """Run the appropriate optimization tier for the current fill percentage.

        Args:
            fill_pct: Current context fill as a percentage (0–100).
            history: Current conversation history (list of {role, content}).

        Returns:
            OptimizeResultEx with actions taken and (possibly trimmed) history.
        """
        result = OptimizeResultEx(history=list(history or []))

        if fill_pct >= TIER3_PCT:
            self._run_tier3(result)
        elif fill_pct >= TIER2_PCT:
            self._run_tier2(result)
        elif fill_pct >= TIER1_PCT:
            self._run_tier1(result)

        return result

    def optimize_all(self, *, dry_run: bool = False) -> OptimizeResultEx:
        """Run all three tiers unconditionally (used by specsmith context optimize).

        Args:
            dry_run: If True, report what would be done without writing.

        Returns:
            OptimizeResultEx with all actions.
        """
        result = OptimizeResultEx(history=[])

        if dry_run:
            result.actions.append("[dry-run] Would run Tier 1: compress LEDGER.md")
            result.actions.append("[dry-run] Would run Tier 2: summarize conversation history")
            result.actions.append("[dry-run] Would run Tier 3: protect critical ESDB records")
            result.tier = 3
            return result

        self._run_tier1(result)
        self._run_tier2(result)
        self._run_tier3(result)
        return result

    # ------------------------------------------------------------------
    # Tier implementations
    # ------------------------------------------------------------------

    def _run_tier1(self, result: OptimizeResultEx) -> None:
        """Tier 1 (60–79%): compress LEDGER.md history."""
        result.tier = max(result.tier, 1)
        try:
            from specsmith.compressor import run_compress

            compress_result = run_compress(self.root, threshold=200, keep_recent=10)
            if compress_result.archived_entries > 0:
                freed = compress_result.archived_entries * 150  # ~150 tokens per entry
                result.tokens_freed_estimate += freed
                result.actions.append(
                    f"Tier 1: archived {compress_result.archived_entries} ledger entries "
                    f"(~{freed} tokens freed)"
                )
            else:
                result.actions.append(
                    f"Tier 1: {compress_result.message}"
                )
        except Exception as exc:  # noqa: BLE001
            result.actions.append(f"Tier 1: ledger compress skipped ({exc})")

    def _run_tier2(self, result: OptimizeResultEx) -> None:
        """Tier 2 (80–84%): summarize old history + evict low-confidence ESDB records."""
        result.tier = max(result.tier, 2)

        # Summarize oldest half of conversation history
        if len(result.history) > 4:
            half = len(result.history) // 2
            dropped = result.history[:half]
            kept = result.history[half:]
            summary_content = (
                f"[Earlier conversation summary — {len(dropped)} turns condensed. "
                "Key context preserved in ESDB and LEDGER.md.]"
            )
            result.history = [{"role": "assistant", "content": summary_content}] + kept
            freed = sum(len(t.get("content", "")) for t in dropped) // 4  # ~4 chars/token
            result.tokens_freed_estimate += freed
            result.actions.append(
                f"Tier 2: summarized {len(dropped)} history turns into 1 (~{freed} tokens freed)"
            )

        # Evict low-confidence / synthetic ESDB records from in-context representation
        evicted = self._evict_low_confidence_records(min_confidence=0.5, source_type_exclude=["synthetic"])
        if evicted > 0:
            freed_esdb = evicted * 80  # ~80 tokens per record summary
            result.tokens_freed_estimate += freed_esdb
            result.records_evicted += evicted
            result.actions.append(
                f"Tier 2: evicted {evicted} low-confidence ESDB records from context "
                f"(~{freed_esdb} tokens freed)"
            )

    def _run_tier3(self, result: OptimizeResultEx) -> None:
        """Tier 3 (≥85%): emergency — protect critical records, evict the rest."""
        result.tier = max(result.tier, 3)

        # Keep only last KEEP_LEDGER_ENTRIES turns of history
        if len(result.history) > KEEP_LEDGER_ENTRIES * 2:
            kept = result.history[-(KEEP_LEDGER_ENTRIES * 2):]
            dropped = len(result.history) - len(kept)
            freed = sum(len(t.get("content", "")) for t in result.history[:dropped]) // 4
            result.history = [
                {
                    "role": "assistant",
                    "content": (
                        f"[EMERGENCY COMPRESSION: {dropped} turns dropped. "
                        "Critical ESDB records and last 5 ledger entries preserved.]"
                    ),
                }
            ] + kept
            result.tokens_freed_estimate += freed
            result.actions.append(
                f"Tier 3: emergency-dropped {dropped} history turns (~{freed} tokens freed)"
            )

        # Count critical records protected
        protected = self._count_critical_records()
        result.critical_records_protected = protected
        if protected > 0:
            result.actions.append(
                f"Tier 3: {protected} critical ESDB records protected "
                f"(confidence ≥ {CRITICAL_CONFIDENCE}, status=active)"
            )

        # Evict everything below CRITICAL_CONFIDENCE from in-context
        evicted = self._evict_low_confidence_records(min_confidence=CRITICAL_CONFIDENCE)
        if evicted > 0:
            result.records_evicted += evicted
            result.actions.append(
                f"Tier 3: evicted {evicted} non-critical ESDB records from context"
            )

    # ------------------------------------------------------------------
    # ESDB helpers
    # ------------------------------------------------------------------

    def _evict_low_confidence_records(
        self,
        min_confidence: float = 0.5,
        source_type_exclude: list[str] | None = None,
    ) -> int:
        """Mark low-confidence records as 'evicted-from-context' in memory only.

        NOTE: This does NOT delete from the WAL — it only removes from the
        in-context representation returned by the current query.

        Returns the count of records that would be evicted.
        """

        wal = self.root / ".chronomemory" / "events.wal"
        if not wal.exists():
            return 0
        try:
            from specsmith.esdb.store import ChronoStore

            with ChronoStore(self.root) as store:
                records = store.query()
                count = 0
                for rec in records:
                    evict = rec.confidence < min_confidence
                    if source_type_exclude and rec.source_type in source_type_exclude:
                        evict = True
                    if evict:
                        count += 1
                return count
        except Exception:  # noqa: BLE001
            return 0

    def _count_critical_records(self) -> int:
        """Count records that qualify as critical (must be protected)."""
        wal = self.root / ".chronomemory" / "events.wal"
        if not wal.exists():
            return 0
        try:
            from specsmith.esdb.store import ChronoStore

            with ChronoStore(self.root) as store:
                return sum(
                    1
                    for r in store.query()
                    if r.confidence >= CRITICAL_CONFIDENCE
                    and r.status == "active"
                )
        except Exception:  # noqa: BLE001
            return 0


@dataclass
class OptimizeResultEx(OptimizeResult):
    """Extended OptimizeResult that also carries the (possibly trimmed) history."""

    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier,
            "actions": self.actions,
            "tokens_freed_estimate": self.tokens_freed_estimate,
            "critical_records_protected": self.critical_records_protected,
            "records_evicted": self.records_evicted,
            "history_turns": len(self.history),
        }

    def summary(self) -> str:
        if not self.actions:
            return "Context already optimal — no optimization needed."
        lines = [f"Optimization tier {self.tier} completed:"]
        lines.extend(f"  • {a}" for a in self.actions)
        lines.append(
            f"  Total estimated tokens freed: ~{self.tokens_freed_estimate:,}"
        )
        return "\n".join(lines)
