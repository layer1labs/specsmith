# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Context compression helpers for agent runner integration.

Provides guided compression integration for the agent runner and serve.py
REPL. Auto-compresses conversation history when it exceeds a configurable
threshold while preserving epistemic-critical elements.

Usage in agent runner::

    from specsmith.agent.context_compressor import compress_history_elements

    history = [...]  # list of {role, text} dicts
    compressed, stats = compress_history_elements(
        history,
        project_dir="/path/to/project",
        target_pct=70.0,
    )

REQ-308: Context orchestrator — automatic tiered optimization (extends)
"""

from __future__ import annotations

import json
from typing import Any


def compress_history_elements(
    history: list[dict[str, Any]],
    *,
    project_dir: str,
    target_pct: float = 70.0,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Compress conversation history using guided compression.

    Args:
        history: List of {role, text, ...} conversation turns.
        project_dir: Project root directory.
        target_pct: Target fill percentage (0-100).

    Returns:
        Tuple of (compressed_history, stats_dict).
        stats_dict contains: ok, original_size, compressed_size,
        space_saved_pct, elements_preserved, elements_summarized,
        elements_discarded, error (if not ok).
    """
    try:
        from specsmith.guided_compression import (
            ContextElement,
            GuidedCompressionResult,
            GuidedCompressor,
        )

        elements: list[ContextElement] = [
            ContextElement(
                element_id=f"turn-{i}",
                element_type="conversation_turn",
                content=json.dumps(h, ensure_ascii=False),
                metadata={"role": h.get("role", "unknown")},
            )
            for i, h in enumerate(history)
        ]

        compressor = GuidedCompressor(project_dir)
        result: GuidedCompressionResult = compressor.compress(elements, target_fill_pct=target_pct)

        if result.space_saved_pct <= 10:
            # Not worth compressing
            return history, {
                "ok": True,
                "skipped": True,
                "reason": "compression savings below 10%",
            }

        # Rebuild compressed history
        classified = compressor._classify_elements(elements)
        compressed_parts: list[str] = []
        for elem in classified:
            action = compressor._decide_action(elem, target_pct)
            if action == "preserve":
                compressed_parts.append(elem.content)
            elif action == "summarize":
                compressed_parts.append(compressor._summarize_element(elem))

        # Parse back into history format
        new_history: list[dict[str, Any]] = []
        for p in compressed_parts:
            if '"role"' in p and '"text"' in p:
                try:
                    new_history.append(json.loads(p))
                except json.JSONDecodeError:
                    new_history.append({"role": "system", "text": p})
            else:
                new_history.append({"role": "system", "text": p})

        stats = {
            "ok": True,
            "original_size": result.original_size,
            "compressed_size": result.compressed_size,
            "space_saved_pct": round(result.space_saved_pct, 1),
            "elements_preserved": result.elements_preserved,
            "elements_summarized": result.elements_summarized,
            "elements_discarded": result.elements_discarded,
        }
        return new_history, stats

    except Exception as exc:  # noqa: BLE001
        return history, {"ok": False, "error": str(exc)}


def should_compress(history: list[dict[str, Any]], threshold_chars: int = 10000) -> bool:
    """Check if history should be compressed based on total character count.

    Args:
        history: List of conversation turns.
        threshold_chars: Character count threshold for triggering compression.

    Returns:
        True if history exceeds threshold.
    """
    total = sum(len(h.get("text", "") or "") for h in history)
    return total > threshold_chars
