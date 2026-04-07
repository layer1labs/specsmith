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
from collections.abc import Iterator
from dataclasses import dataclass, field

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
    # ── Tiny (< 3 GB VRAM) ────────────────────────────────────────────────────
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
        id="gemma3:4b",
        name="Gemma 3 4B",
        vram_gb=3.0,
        size_gb=3.3,
        ctx_k=128,
        tier="Tiny",
        best_for=["chat", "analysis"],
        notes="Google Gemma 3, 128K ctx, vision capable",
    ),
    # ── Balanced (4–8 GB VRAM) ──────────────────────────────────────────────
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
        id="qwen3:7b",
        name="Qwen 3 7B",
        vram_gb=5.0,
        size_gb=4.9,
        ctx_k=128,
        tier="Balanced",
        best_for=["coding", "analysis", "requirements"],
        notes="Qwen 3 — latest generation, 128K ctx, tool calling",
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
    # ── Capable (8–12 GB VRAM) ───────────────────────────────────────────────
    CatalogEntry(
        id="gemma3:12b",
        name="Gemma 3 12B",
        vram_gb=8.0,
        size_gb=7.8,
        ctx_k=128,
        tier="Capable",
        best_for=["general", "analysis"],
        notes="Google Gemma 3, 128K ctx, vision capable",
    ),
    CatalogEntry(
        id="qwen3:14b",
        name="Qwen 3 14B",
        vram_gb=9.0,
        size_gb=9.3,
        ctx_k=128,
        tier="Capable",
        best_for=["coding", "requirements engineering", "analysis"],
        notes="Qwen 3 — best 14B, 128K ctx, tool calling, AEE workflows",
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
        notes="Qwen 2.5 — previous generation, 32K ctx",
    ),
    CatalogEntry(
        id="deepseek-coder-v2:latest",
        name="DeepSeek Coder v2 16B",
        vram_gb=11.0,
        size_gb=9.1,
        ctx_k=128,
        tier="Capable",
        best_for=["code generation", "code review"],
        notes="Top local coding model, 128K ctx",
    ),
    # ── Powerful (16+ GB VRAM) ────────────────────────────────────────────────
    CatalogEntry(
        id="qwen3:32b",
        name="Qwen 3 32B",
        vram_gb=20.0,
        size_gb=19.8,
        ctx_k=128,
        tier="Powerful",
        best_for=["complex reasoning", "architecture", "requirements"],
        notes="Qwen 3 32B — top local quality, 128K ctx",
    ),
    CatalogEntry(
        id="gemma3:27b",
        name="Gemma 3 27B",
        vram_gb=18.0,
        size_gb=16.9,
        ctx_k=128,
        tier="Powerful",
        best_for=["general", "analysis", "complex reasoning"],
        notes="Google Gemma 3 27B, vision capable, 128K ctx",
    ),
    CatalogEntry(
        id="llama3.3:70b",
        name="Llama 3.3 70B",
        vram_gb=42.0,
        size_gb=39.0,
        ctx_k=128,
        tier="Powerful",
        best_for=["complex reasoning", "architecture", "chat"],
        notes="Llama 3.3 70B — requires high-end GPU (40+ GB VRAM)",
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
# Model detail + management
# ---------------------------------------------------------------------------


def get_installed_models_detail() -> list[dict]:
    """Return installed models with size, digest, and modified_at metadata."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_API}/api/tags", timeout=5) as r:  # noqa: S310
            data: dict = json.loads(r.read().decode())
            return data.get("models", [])
    except Exception:  # noqa: BLE001
        return []


def delete_model(model_id: str) -> bool:
    """Delete an installed model via the Ollama API. Returns True on success.

    API: DELETE /api/delete   body: {"model": "<name>"}
    Note: Ollama API uses the field ``model`` (not ``name``) in the request body.
    """
    import urllib.error
    # Ollama API uses 'model' (not 'name') in the delete request body
    payload = json.dumps({"model": model_id}).encode()
    req = urllib.request.Request(  # noqa: S310
        f"{OLLAMA_API}/api/delete",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="DELETE",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:  # noqa: S310
            return r.status == 200
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False  # already deleted
        raise
    except Exception:  # noqa: BLE001
        return False


def get_ollama_version() -> str | None:
    """Return the running Ollama server version string, or None if unavailable."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_API}/api/version", timeout=3) as r:  # noqa: S310
            data: dict = json.loads(r.read().decode())
            return data.get("version")
    except Exception:  # noqa: BLE001
        return None


def check_ollama_update() -> tuple[str | None, str | None]:
    """Check for a newer Ollama release on GitHub.

    Returns (installed_version, latest_version). Either may be None if
    not available. latest_version has the 'v' prefix stripped.
    """
    installed = get_ollama_version()
    latest: str | None = None
    try:
        req = urllib.request.Request(  # noqa: S310
            "https://api.github.com/repos/ollama/ollama/releases/latest",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "specsmith"},
        )
        with urllib.request.urlopen(req, timeout=8) as r:  # noqa: S310
            data: dict = json.loads(r.read().decode())
            tag = data.get("tag_name", "")
            latest = tag.lstrip("v")
    except Exception:  # noqa: BLE001
        pass
    return installed, latest


def upgrade_ollama_cmd() -> str:
    """Return the platform-appropriate command to upgrade Ollama."""
    if sys.platform == "win32":
        return "winget upgrade --id Ollama.Ollama"
    if sys.platform == "darwin":
        return "brew upgrade ollama"
    # Linux: re-run the install script
    return "curl -fsSL https://ollama.ai/install.sh | sh"


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
