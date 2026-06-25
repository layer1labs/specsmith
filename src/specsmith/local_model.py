# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Hardware-aware local model selector for the fallback REPL AI (REQ-385, REQ-386).

Detects the host GPU/unified-memory tier and returns the best Ollama model tag
to use as a local fallback when no cloud API key is configured.

Model selection rationale
--------------------------
*Qwen2.5-Coder* (Alibaba, Apache-2.0) tops every major coding benchmark at its
size tier and ships with first-class Ollama GGUF quants.  It outperforms
Llama-3.3 and DeepSeek-Coder on HumanEval, MBPP, and LiveCodeBench at 7B, 14B,
and 32B.  The 32B Q4_K_M fits in 20 GB VRAM; the 7B Q8_0 fits in 8 GB.

Hardware detection
------------------
* Apple Silicon: ``platform.processor() == "arm"`` on macOS; unified memory via
  ``sysctl hw.memsize``.
* NVIDIA: ``nvidia-smi --query-gpu=memory.total`` (MiB).
* CPU-only / < 8 GB: returns ``None`` — do not load a model that would be
  unusably slow.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Tier thresholds (GB)
# ---------------------------------------------------------------------------
_TIER_32B_GB = 20.0  # ≥ 20 GB VRAM → 32B Q4
_TIER_14B_GB = 10.0  # ≥ 10 GB VRAM → 14B Q4
_TIER_7B_GB = 7.0  # ≥  7 GB VRAM →  7B Q8
# Below _TIER_7B_GB → None (skip)

# Apple Silicon thresholds are higher because the model shares unified memory
# with the OS.  Leave ~4 GB headroom.
_AS_TIER_32B_GB = 32.0
_AS_TIER_14B_GB = 16.0
_AS_TIER_7B_GB = 8.0

#: Ollama model tags in descending capability order
_MODEL_32B = "qwen2.5-coder:32b"
_MODEL_14B = "qwen2.5-coder:14b"
_MODEL_7B = "qwen2.5-coder:7b"


@dataclass
class LocalModelInfo:
    """Recommended local model for the current machine (REQ-385)."""

    model: str
    """Ollama model tag, e.g. ``qwen2.5-coder:14b``."""

    runtime: str
    """Always ``"ollama"`` in this version."""

    hardware: str
    """Human-readable hardware description, e.g. ``"apple-silicon-24gb"``."""

    vram_gb: float
    """Detected VRAM / unified memory in GB."""

    pull_cmd: str
    """Shell command to pull the model: ``"ollama pull <model>"``."""

    @property
    def hf_repo(self) -> str:
        """Canonical HuggingFace repo for the selected model."""
        _hf = {
            _MODEL_7B: "Qwen/Qwen2.5-Coder-7B-Instruct",
            _MODEL_14B: "Qwen/Qwen2.5-Coder-14B-Instruct",
            _MODEL_32B: "Qwen/Qwen2.5-Coder-32B-Instruct",
        }
        return _hf.get(self.model, "")


# ---------------------------------------------------------------------------
# Hardware detection helpers
# ---------------------------------------------------------------------------


def _detect_apple_silicon_gb() -> float | None:
    """Return unified memory in GB for Apple Silicon, or None if not AS."""
    if platform.system() != "Darwin" or platform.processor() != "arm":
        return None
    try:
        out = subprocess.check_output(  # noqa: S603
            ["sysctl", "-n", "hw.memsize"],  # noqa: S607
            text=True,
            timeout=5,
        )
        return int(out.strip()) / (1024**3)
    except Exception:  # noqa: BLE001
        return None


def _detect_nvidia_vram_gb() -> float | None:
    """Return total VRAM in GB for the first NVIDIA GPU, or None if absent."""
    if not shutil.which("nvidia-smi"):
        return None
    try:
        out = subprocess.check_output(  # noqa: S603
            [  # noqa: S607
                "nvidia-smi",
                "--query-gpu=memory.total",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=10,
        )
        # First GPU only; value is in MiB
        first = out.strip().splitlines()[0].strip()
        return int(first) / 1024.0
    except Exception:  # noqa: BLE001
        return None


def _pick_model(gb: float, *, tier_32b: float, tier_14b: float, tier_7b: float) -> str | None:
    """Pick a model tag based on memory, or None when below the minimum tier."""
    if gb >= tier_32b:
        return _MODEL_32B
    if gb >= tier_14b:
        return _MODEL_14B
    if gb >= tier_7b:
        return _MODEL_7B
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_local_model() -> LocalModelInfo | None:
    """Detect hardware and return the best Ollama model, or ``None`` to skip.

    Returns ``None`` when the machine is CPU-only or has < 7 GB VRAM, since
    running a large language model in that environment would be unusably slow
    (REQ-385).
    """
    # 1. Apple Silicon (Metal backend in Ollama)
    as_gb = _detect_apple_silicon_gb()
    if as_gb is not None:
        model = _pick_model(
            as_gb, tier_32b=_AS_TIER_32B_GB, tier_14b=_AS_TIER_14B_GB, tier_7b=_AS_TIER_7B_GB
        )
        if model is None:
            return None
        hw = f"apple-silicon-{int(as_gb)}gb"
        return LocalModelInfo(
            model=model,
            runtime="ollama",
            hardware=hw,
            vram_gb=as_gb,
            pull_cmd=f"ollama pull {model}",
        )

    # 2. NVIDIA (CUDA backend in Ollama)
    nv_gb = _detect_nvidia_vram_gb()
    if nv_gb is not None:
        model = _pick_model(
            nv_gb, tier_32b=_TIER_32B_GB, tier_14b=_TIER_14B_GB, tier_7b=_TIER_7B_GB
        )
        if model is None:
            return None
        hw = f"nvidia-{int(nv_gb)}gb"
        return LocalModelInfo(
            model=model,
            runtime="ollama",
            hardware=hw,
            vram_gb=nv_gb,
            pull_cmd=f"ollama pull {model}",
        )

    # 3. CPU-only or unrecognised → skip
    return None


def ensure_local_model(model_tag: str) -> bool:
    """Pull *model_tag* via Ollama if it is not already present.

    Returns ``True`` when the model is available (already present or
    successfully pulled), ``False`` on failure (Ollama not running, pull
    error, etc.).
    """
    if not shutil.which("ollama"):
        return False
    try:
        # Check if model is already local (non-zero output = present)
        result = subprocess.run(  # noqa: S603
            ["ollama", "show", model_tag],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True
        # Model not present — pull it
        pull = subprocess.run(  # noqa: S603
            ["ollama", "pull", model_tag],  # noqa: S607
            timeout=600,
            check=False,
        )
        return pull.returncode == 0
    except Exception:  # noqa: BLE001
        return False


__all__ = [
    "LocalModelInfo",
    "detect_local_model",
    "ensure_local_model",
]
