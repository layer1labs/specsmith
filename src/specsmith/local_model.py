# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Hardware-aware local model selector for the fallback REPL AI (REQ-385–391).

Detects the host GPU/unified-memory tier and returns the best Ollama model tag
to use as a local fallback when no cloud API key is configured.

Model roles (REQ-387)
---------------------
* ``general``  — *Qwen2.5* (versatile; project management, Q&A, conversation).
* ``coding``   — *Qwen2.5-Coder* (top coding benchmarks at every size tier).
* ``reasoning``— *DeepSeek-R1* (deep analysis, architecture, debugging chains).

Hardware detection
------------------
* Apple Silicon: ``platform.processor() == "arm"`` on macOS; unified memory via
  ``sysctl hw.memsize``.
* NVIDIA: ``nvidia-smi --query-gpu=memory.total`` (MiB).
* CPU-only / < 8 GB: returns empty dict — do not load a model that would be
  unusably slow.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Model roles (REQ-387)
# ---------------------------------------------------------------------------


class ModelRole(str, Enum):
    """Semantic role that determines which local model is invoked."""

    general = "general"    # project management, Q&A, chat
    coding = "coding"      # code generation, editing, debugging
    reasoning = "reasoning"  # deep analysis, architecture, multi-step reasoning


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

# ── Coding models (qwen2.5-coder) ──────────────────────────────────────────
_MODEL_32B = "qwen2.5-coder:32b"
_MODEL_14B = "qwen2.5-coder:14b"
_MODEL_7B = "qwen2.5-coder:7b"

# ── General-purpose models (qwen2.5) ───────────────────────────────────────
_GEN_32B = "qwen2.5:32b"
_GEN_14B = "qwen2.5:14b"
_GEN_7B = "qwen2.5:7b"

# ── Reasoning models (deepseek-r1) ─────────────────────────────────────────
_REASON_14B = "deepseek-r1:14b"
_REASON_8B = "deepseek-r1:8b"
_REASON_7B = "deepseek-r1:7b"


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


def detect_local_models() -> dict[ModelRole, LocalModelInfo]:
    """Detect hardware and return recommended models for all three roles (REQ-387).

    Returns an empty dict on CPU-only hardware or when no GPU is detected.
    The three roles are ``general``, ``coding``, and ``reasoning``, each
    selecting the best-fitting model for the detected VRAM tier.
    """
    # 1. Apple Silicon
    as_gb = _detect_apple_silicon_gb()
    if as_gb is not None:
        coding_model = _pick_model(
            as_gb, tier_32b=_AS_TIER_32B_GB, tier_14b=_AS_TIER_14B_GB, tier_7b=_AS_TIER_7B_GB
        )
        if coding_model is None:
            return {}
        hw = f"apple-silicon-{int(as_gb)}gb"
        gen_model = _pick_from(
            as_gb,
            tier_32b=_AS_TIER_32B_GB,
            tier_14b=_AS_TIER_14B_GB,
            tier_7b=_AS_TIER_7B_GB,
            tag_32b=_GEN_32B,
            tag_14b=_GEN_14B,
            tag_7b=_GEN_7B,
        )
        reason_model = _pick_reasoning(as_gb, apple=True)
        return _build_role_dict(hw, as_gb, coding_model, gen_model, reason_model)

    # 2. NVIDIA
    nv_gb = _detect_nvidia_vram_gb()
    if nv_gb is not None:
        coding_model = _pick_model(
            nv_gb, tier_32b=_TIER_32B_GB, tier_14b=_TIER_14B_GB, tier_7b=_TIER_7B_GB
        )
        if coding_model is None:
            return {}
        hw = f"nvidia-{int(nv_gb)}gb"
        gen_model = _pick_from(
            nv_gb,
            tier_32b=_TIER_32B_GB,
            tier_14b=_TIER_14B_GB,
            tier_7b=_TIER_7B_GB,
            tag_32b=_GEN_32B,
            tag_14b=_GEN_14B,
            tag_7b=_GEN_7B,
        )
        reason_model = _pick_reasoning(nv_gb, apple=False)
        return _build_role_dict(hw, nv_gb, coding_model, gen_model, reason_model)

    return {}


def _pick_from(
    gb: float,
    *,
    tier_32b: float,
    tier_14b: float,
    tier_7b: float,
    tag_32b: str,
    tag_14b: str,
    tag_7b: str,
) -> str | None:
    """Generic 3-tier model picker using caller-supplied tags."""
    if gb >= tier_32b:
        return tag_32b
    if gb >= tier_14b:
        return tag_14b
    if gb >= tier_7b:
        return tag_7b
    return None


def _pick_reasoning(gb: float, *, apple: bool) -> str | None:
    """Pick a deepseek-r1 reasoning model for the available memory."""
    tier_14b = _AS_TIER_14B_GB if apple else _TIER_14B_GB
    tier_7b = _AS_TIER_7B_GB if apple else _TIER_7B_GB
    if gb >= tier_14b:
        return _REASON_14B
    if gb >= tier_7b:
        return _REASON_8B if apple else _REASON_7B
    return None


def _build_role_dict(
    hardware: str,
    vram_gb: float,
    coding_model: str,
    gen_model: str | None,
    reason_model: str | None,
) -> dict[ModelRole, LocalModelInfo]:
    roles: dict[ModelRole, LocalModelInfo] = {}
    roles[ModelRole.coding] = LocalModelInfo(
        model=coding_model,
        runtime="ollama",
        hardware=hardware,
        vram_gb=vram_gb,
        pull_cmd=f"ollama pull {coding_model}",
    )
    if gen_model:
        roles[ModelRole.general] = LocalModelInfo(
            model=gen_model,
            runtime="ollama",
            hardware=hardware,
            vram_gb=vram_gb,
            pull_cmd=f"ollama pull {gen_model}",
        )
    if reason_model:
        roles[ModelRole.reasoning] = LocalModelInfo(
            model=reason_model,
            runtime="ollama",
            hardware=hardware,
            vram_gb=vram_gb,
            pull_cmd=f"ollama pull {reason_model}",
        )
    return roles


# ---------------------------------------------------------------------------
# Config persistence (REQ-391)
# ---------------------------------------------------------------------------

_CONFIG_FILENAME = "local-models.yml"


def load_local_models_config(project_dir: str | Path) -> dict[str, str]:
    """Load persisted role→model mapping from ``.specsmith/local-models.yml``.

    Returns an empty dict when the file does not exist or cannot be parsed.
    Keys are role names (``"general"``, ``"coding"``, ``"reasoning"``);
    values are Ollama model tags.
    """
    cfg_path = Path(project_dir) / ".specsmith" / _CONFIG_FILENAME
    if not cfg_path.exists():
        return {}
    try:
        text = cfg_path.read_text(encoding="utf-8")
        # Minimal YAML parser — we only need the ``models:`` sub-dict.
        # Using a hand-rolled parser keeps the stdlib-only guarantee.
        import re as _re

        models_block: dict[str, str] = {}
        in_models = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped == "models:":
                in_models = True
                continue
            if in_models:
                if stripped.startswith("  ") or line.startswith(" "):
                    m = _re.match(r'^\s+(\w+):\s+(.+)$', line)
                    if m:
                        models_block[m.group(1)] = m.group(2).strip()
                elif stripped and not stripped.startswith(" "):
                    in_models = False  # new top-level key
        return models_block
    except Exception:  # noqa: BLE001
        return {}


def save_local_models_config(
    project_dir: str | Path,
    roles: dict[ModelRole, LocalModelInfo],
    *,
    hardware: str = "",
) -> None:
    """Persist role→model mapping to ``.specsmith/local-models.yml`` (REQ-391)."""
    import datetime

    spec_dir = Path(project_dir) / ".specsmith"
    spec_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = spec_dir / _CONFIG_FILENAME
    _now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# specsmith local model routing config — auto-generated, do not edit manually",
        f"# detected_at: {_now}",
        f"hardware: {hardware or (next(iter(roles.values())).hardware if roles else 'unknown')}",
        "provider: ollama",
        "models:",
    ]
    for role in (ModelRole.general, ModelRole.coding, ModelRole.reasoning):
        if role in roles:
            lines.append(f"  {role.value}: {roles[role].model}")
    cfg_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    "ModelRole",
    "detect_local_model",
    "detect_local_models",
    "ensure_local_model",
    "load_local_models_config",
    "save_local_models_config",
]
