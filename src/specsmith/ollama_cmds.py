"""ollama_cmds — Ollama local model management helpers for specsmith.

Provides:
    - CATALOG: curated list of recommended models with VRAM/size/task metadata
    - get_installed_models(): query running Ollama for installed model IDs
    - get_vram_gb(): detect available GPU VRAM (nvidia-smi + Windows WMI fallback)
    - recommend_models(vram_gb): return CATALOG entries that fit within a VRAM budget
    - pull_model(model_id): stream progress from ``ollama pull``
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Iterator

OLLAMA_API = "http://localhost:11434"


# ---------------------------------------------------------------------------
# Curated model catalog
# ---------------------------------------------------------------------------


@dataclass
class CatalogEntry:
    id: str
    name: str
    vram_gb: float
    size_gb: float
    ctx_k: int
    tier: str
    best_for: list[str] = field(default_factory=list)
    notes: str = ""


CATALOG: list[CatalogEntry] = [
    CatalogEntry(
        id="llama3.2:latest",
        name="Llama 3.2 3B",
        vram_gb=2.0,
        size_gb=2.0,
        ctx_k=128,
        tier="Tiny",
        best_for=["chat", "quick tasks"],
        notes="Tiny & fast, minimal VRAM",
    ),
    CatalogEntry(
        id="mistral:latest",
        name="Mistral 7B",
        vram_gb=4.5,
        size_gb=4.1,
        ctx_k=32,
        tier="Balanced",
        best_for=["chat", "writing"],
        notes="Fast general-purpose",
    ),
    CatalogEntry(
        id="qwen2.5:7b",
        name="Qwen 2.5 7B",
        vram_gb=5.0,
        size_gb=4.7,
        ctx_k=32,
        tier="Balanced",
        best_for=["coding", "analysis", "requirements"],
        notes="Best 7B for technical work",
    ),
    CatalogEntry(
        id="qwen2.5-coder:7b-instruct",
        name="Qwen 2.5 Coder 7B",
        vram_gb=4.8,
        size_gb=4.7,
        ctx_k=32,
        tier="Balanced",
        best_for=["code generation", "debugging"],
        notes="Specialized coder model",
    ),
    CatalogEntry(
        id="gemma3:12b",
        name="Gemma 3 12B",
        vram_gb=8.0,
        size_gb=7.8,
        ctx_k=128,
        tier="Capable",
        best_for=["general", "analysis"],
        notes="Google open model, 128K ctx",
    ),
    CatalogEntry(
        id="phi4:latest",
        name="Phi-4 14B",
        vram_gb=9.0,
        size_gb=8.5,
        ctx_k=16,
        tier="Capable",
        best_for=["reasoning", "analysis", "requirements"],
        notes="Outstanding reasoning (Microsoft)",
    ),
    CatalogEntry(
        id="qwen2.5:14b",
        name="Qwen 2.5 14B",
        vram_gb=9.0,
        size_gb=8.9,
        ctx_k=32,
        tier="Capable",
        best_for=["coding", "requirements engineering"],
        notes="Best for AEE workflows",
    ),
    CatalogEntry(
        id="deepseek-coder-v2:latest",
        name="DeepSeek Coder v2 16B",
        vram_gb=11.0,
        size_gb=9.1,
        ctx_k=128,
        tier="Capable",
        best_for=["code generation", "code review"],
        notes="Top local coding model",
    ),
    CatalogEntry(
        id="qwen2.5:32b",
        name="Qwen 2.5 32B",
        vram_gb=20.0,
        size_gb=19.0,
        ctx_k=32,
        tier="Powerful",
        best_for=["complex reasoning", "architecture"],
        notes="Best quality (high VRAM)",
    ),
]

# Task keyword → catalog best_for tags
TASK_TAGS: dict[str, list[str]] = {
    "code":          ["code generation", "debugging", "coding"],
    "requirements":  ["requirements", "requirements engineering", "analysis"],
    "architecture":  ["complex reasoning", "architecture", "requirements engineering"],
    "chat":          ["chat", "writing", "general"],
    "analysis":      ["analysis", "reasoning", "requirements"],
    "reasoning":     ["complex reasoning", "reasoning"],
}


# ---------------------------------------------------------------------------
# Ollama API helpers
# ---------------------------------------------------------------------------


def is_running() -> bool:
    """Return True if an Ollama server is reachable at localhost:11434."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_API}/api/version", timeout=3) as r:
            return r.status == 200
    except Exception:  # noqa: BLE001
        return False


def get_installed_models() -> list[str]:
    """Return list of installed model IDs from the running Ollama server."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_API}/api/tags", timeout=5) as r:
            data: dict = json.loads(r.read().decode())
            return [m["name"] for m in data.get("models", [])]
    except Exception:  # noqa: BLE001
        return []


# ---------------------------------------------------------------------------
# GPU / VRAM detection
# ---------------------------------------------------------------------------


def get_vram_gb() -> float:
    """Return available GPU VRAM in GB, or 0.0 if no GPU detected.

    Detection order:
    1. ``nvidia-smi`` (works cross-platform for NVIDIA)
    2. Windows WMI via PowerShell (AMD/Intel/any WDDM GPU)
    """
    # ── NVIDIA nvidia-smi ──────────────────────────────────────────────────
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            mb = int(r.stdout.strip().split("\n")[0])
            if mb > 0:
                return mb / 1024
    except Exception:  # noqa: BLE001
        pass

    # ── Windows WMI (AMD / Intel / any WDDM GPU) ───────────────────────────
    if sys.platform == "win32":
        try:
            r = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-WmiObject Win32_VideoController "
                    "| Sort-Object AdapterRAM -Descending "
                    "| Select-Object -First 1 -ExpandProperty AdapterRAM",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip():
                return int(r.stdout.strip()) / (1024**3)
        except Exception:  # noqa: BLE001
            pass

    return 0.0


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


def recommend_models(vram_gb: float = 0.0, task: str = "") -> list[CatalogEntry]:
    """Return CATALOG entries ordered by fit for the given VRAM budget and task.

    Args:
        vram_gb: Available GPU VRAM in GB. 0 = unlimited (CPU mode).
        task:    Task keyword matching TASK_TAGS keys (e.g. ``'code'``).
                 Empty string returns all fitting models sorted by tier.
    """
    budget = vram_gb * 0.90 if vram_gb > 0 else 999.0
    tags = TASK_TAGS.get(task.lower(), [])

    def _score(e: CatalogEntry) -> tuple[int, float]:
        tag_score = sum(1 for t in tags if t in e.best_for)
        return (-tag_score, e.vram_gb)  # more matching tags first, then smallest VRAM

    return sorted(
        [e for e in CATALOG if e.vram_gb <= budget],
        key=_score,
    )


# ---------------------------------------------------------------------------
# Pull (stream)
# ---------------------------------------------------------------------------


def pull_model(model_id: str) -> Iterator[dict]:
    """Stream progress dicts from ``ollama pull <model_id>``.

    Each yielded dict has at least a ``"status"`` key.
    Yields ``{"status": "error", "message": ...}`` on failure.
    """
    try:
        proc = subprocess.Popen(
            ["ollama", "pull", model_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"status": line}
        proc.wait()
        if proc.returncode != 0:
            yield {"status": "error", "message": f"ollama pull exited {proc.returncode}"}
    except FileNotFoundError:
        yield {"status": "error", "message": "ollama not found — install from https://ollama.ai"}
    except Exception as exc:  # noqa: BLE001
        yield {"status": "error", "message": str(exc)}
