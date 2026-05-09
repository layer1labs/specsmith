# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Context Window Management (REQ-228..REQ-231).

Provides:
- GPU VRAM detection (NVIDIA via nvidia-smi, AMD via rocm-smi) — REQ-228
- Context window size recommendation for Ollama based on VRAM — REQ-228
- ContextFillTracker: per-turn token accounting + JSONL event emission — REQ-229
- ContextFullError: hard-ceiling enforcement — REQ-231

The hard reservation ensures at least 15 % of the context window (or 2048 tokens
minimum) is always free, so auto-compression always has room to run — REQ-231.

JSONL event schema (emitted by ContextFillTracker.record):
  {"type": "context_fill", "used": <int>, "limit": <int>, "pct": <float>}

When pct >= hard_ceiling_pct, attempting to record more tokens raises
ContextFullError and the caller MUST trigger emergency compression before
accepting any further user input.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Hard ceiling as a percentage of the context window.  The caller must trigger
#: emergency compression when fill reaches or exceeds this value (REQ-231).
HARD_CEILING_PCT: float = 85.0

#: Minimum number of tokens that must remain free regardless of HARD_CEILING_PCT.
MIN_FREE_TOKENS: int = 2048

#: VRAM → num_ctx recommendation tiers (Ollama / llama.cpp).
_VRAM_TIERS: list[tuple[float, int]] = [
    (20.0, 32768),
    (12.0, 16384),
    (6.0,   8192),
    (0.0,   4096),   # CPU-only or very low VRAM
]


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class ContextFullError(RuntimeError):
    """Raised when the context window has reached the hard ceiling.

    Callers must trigger emergency compression before accepting any further
    user input (REQ-231).
    """

    def __init__(self, used: int, limit: int, pct: float) -> None:
        self.used = used
        self.limit = limit
        self.pct = pct
        super().__init__(
            f"Context window hard ceiling reached: {pct:.1f}% full "
            f"({used}/{limit} tokens). Emergency compression required (REQ-231)."
        )


# ---------------------------------------------------------------------------
# GPU VRAM detection
# ---------------------------------------------------------------------------


def _run_silent(cmd: list[str]) -> str:
    """Run *cmd* and return stdout; return '' on any error."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout if result.returncode == 0 else ""
    except Exception:  # noqa: BLE001
        return ""


def _detect_nvidia_vram() -> float:
    """Return total NVIDIA VRAM in GB, or 0.0 if nvidia-smi is unavailable."""
    output = _run_silent(
        ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"]
    )
    total_mib = 0
    for line in output.splitlines():
        line = line.strip()
        if line.isdigit():
            total_mib += int(line)
    return total_mib / 1024.0 if total_mib else 0.0


def _detect_amd_vram() -> float:
    """Return total AMD VRAM in GB via rocm-smi, or 0.0 if unavailable."""
    output = _run_silent(["rocm-smi", "--showmeminfo", "vram"])
    total_bytes = 0
    for line in output.splitlines():
        # rocm-smi outputs lines like: "GPU[0] : VRAM Total Memory (B): 17163091968"
        if "Total Memory (B)" in line and ":" in line:
            try:
                value = int(line.split(":")[-1].strip())
                total_bytes += value
            except ValueError:
                continue
    return total_bytes / (1024 ** 3) if total_bytes else 0.0


def detect_gpu_vram() -> float:
    """Detect total GPU VRAM in GB across NVIDIA and AMD devices.

    Returns 0.0 when no GPU is detected or when the relevant CLI tools
    (``nvidia-smi`` / ``rocm-smi``) are not installed.  This function
    never raises — safe to call on any platform.

    Satisfies REQ-228.
    """
    try:
        vram = _detect_nvidia_vram()
        if vram > 0.0:
            return vram
        return _detect_amd_vram()
    except Exception:  # noqa: BLE001
        return 0.0


# ---------------------------------------------------------------------------
# Context window sizing
# ---------------------------------------------------------------------------


def suggest_context_window(vram_gb: float) -> int:
    """Recommend an Ollama ``num_ctx`` value based on available VRAM.

    Uses a simple tier table so that users with less VRAM don't
    accidentally OOM their machine.  Cloud providers use their own
    published context limits and are not affected by this function.

    Tiers:
      - ≥ 20 GB  → 32 768 tokens
      - ≥ 12 GB  → 16 384 tokens
      - ≥  6 GB  →  8 192 tokens
      - < 6 GB / CPU-only →  4 096 tokens

    Satisfies REQ-228.
    """
    for threshold, num_ctx in _VRAM_TIERS:
        if vram_gb >= threshold:
            return num_ctx
    return 4096  # unreachable but safe fallback


# ---------------------------------------------------------------------------
# Context fill tracker
# ---------------------------------------------------------------------------


@dataclass
class ContextFillEvent:
    """Structured context fill event (emitted as JSONL by ContextFillTracker)."""

    type: str = "context_fill"
    used: int = 0
    limit: int = 0
    pct: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "used": self.used, "limit": self.limit, "pct": self.pct}


@dataclass
class ContextFillTracker:
    """Track token usage across turns and emit fill events.

    Parameters
    ----------
    limit:
        Total context window size in tokens.
    hard_ceiling_pct:
        When fill reaches this percentage, :exc:`ContextFullError` is raised
        regardless of the auto-compress toggle.  Defaults to
        :data:`HARD_CEILING_PCT` (85 %).
    min_free_tokens:
        Minimum tokens that must remain free.  If ``hard_ceiling_pct`` would
        allow fewer free tokens than this value, the effective ceiling is
        tightened.  Defaults to :data:`MIN_FREE_TOKENS` (2048).

    Satisfies REQ-229 (fill tracking + JSONL events) and REQ-231 (hard ceiling).
    """

    limit: int
    hard_ceiling_pct: float = HARD_CEILING_PCT
    min_free_tokens: int = MIN_FREE_TOKENS
    _used: int = field(default=0, init=False, repr=False)
    _events: list[ContextFillEvent] = field(default_factory=list, init=False, repr=False)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def used(self) -> int:
        """Current token usage."""
        return self._used

    @property
    def fill_pct(self) -> float:
        """Current fill as a percentage of *limit*."""
        if self.limit <= 0:
            return 0.0
        return min(self._used / self.limit * 100.0, 100.0)

    @property
    def effective_ceiling_pct(self) -> float:
        """Effective ceiling accounting for :attr:`min_free_tokens`."""
        min_free_ceiling = max(0.0, (1.0 - self.min_free_tokens / max(self.limit, 1)) * 100.0)
        return min(self.hard_ceiling_pct, min_free_ceiling)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(self, used: int, limit: int | None = None) -> ContextFillEvent:
        """Record the current token usage and return a fill event.

        Parameters
        ----------
        used:
            Total tokens used so far (prompt + completion).
        limit:
            Override the tracker's limit for this specific turn.  Pass
            ``None`` (default) to use the tracker's configured limit.

        Returns
        -------
        ContextFillEvent
            The fill event for this turn.

        Raises
        ------
        ContextFullError
            When :attr:`fill_pct` reaches or exceeds
            :attr:`effective_ceiling_pct`.
        """
        effective_limit = limit if limit is not None else self.limit
        self._used = used
        if effective_limit != self.limit and effective_limit > 0:
            self.limit = effective_limit

        pct = min(used / max(self.limit, 1) * 100.0, 100.0)
        event = ContextFillEvent(used=used, limit=self.limit, pct=round(pct, 2))
        self._events.append(event)

        if pct >= self.effective_ceiling_pct:
            raise ContextFullError(used=used, limit=self.limit, pct=pct)

        return event

    def reset(self) -> None:
        """Reset usage to zero (e.g. after successful compression)."""
        self._used = 0
        self._events.clear()

    def all_events(self) -> list[ContextFillEvent]:
        """Return all recorded fill events in order."""
        return list(self._events)
