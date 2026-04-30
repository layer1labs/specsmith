# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Voice transcription wrapper (REQ-141).

Wraps the optional ``whisper_cpp_python`` library so the rest of specsmith
can call ``transcribe(path)`` without caring whether the extra is
installed. When the library is missing, ``transcribe`` raises
``VoiceUnavailableError`` with a friendly install hint so the caller can
surface it to the user.

The wrapper supports three modes:

* **real** -- ``whisper_cpp_python`` is installed and a model file is
  available (auto-located under ``~/.specsmith/voice/`` or pointed to via
  ``SPECSMITH_VOICE_MODEL``). Real audio decoding.
* **stub** -- ``SPECSMITH_VOICE_STUB=<text>`` is set. Returns the literal
  text without touching the audio file. Used by tests and CI so we don't
  need to ship a 500MB model file.
* **unavailable** -- neither of the above. ``transcribe`` raises.

The CLI exposes this as ``specsmith voice transcribe <wav>``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class VoiceUnavailableError(RuntimeError):
    """Raised when whisper-cpp is not installed and no stub is set."""


@dataclass
class TranscribeResult:
    text: str
    backend: str  # 'whisper-cpp', 'stub', 'unavailable'
    model: str = ""
    duration_s: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "text": self.text,
            "backend": self.backend,
            "model": self.model,
            "duration_s": round(self.duration_s, 3),
        }


def default_model_dir() -> Path:
    return Path.home() / ".specsmith" / "voice"


def _resolve_model_path() -> Path | None:
    """Return the on-disk model path, or None if no model is configured."""
    env = os.environ.get("SPECSMITH_VOICE_MODEL", "").strip()
    if env:
        p = Path(env)
        if p.is_file():
            return p
    # Auto-locate the smallest .bin under ~/.specsmith/voice/
    voice_dir = default_model_dir()
    if voice_dir.is_dir():
        candidates = sorted(voice_dir.glob("*.bin"), key=lambda x: x.stat().st_size)
        if candidates:
            return candidates[0]
    return None


def is_available() -> bool:
    """Cheap probe: True iff transcription would succeed without raising."""
    if os.environ.get("SPECSMITH_VOICE_STUB", "").strip():
        return True
    try:
        import whisper_cpp_python  # noqa: F401  (presence-only check)
    except Exception:  # noqa: BLE001
        return False
    return _resolve_model_path() is not None


def transcribe(path: Path) -> TranscribeResult:
    """Transcribe a wav/flac/mp3 file to text.

    Order of resolution:
    1. If ``SPECSMITH_VOICE_STUB`` is set, return its value verbatim. This
       lets tests run without a model file.
    2. Otherwise import ``whisper_cpp_python`` and run a real transcription.
    3. If neither is available, raise :class:`VoiceUnavailableError` with
       an actionable message.
    """
    import time as _time

    if not path.exists():
        raise FileNotFoundError(f"audio file not found: {path}")

    stub = os.environ.get("SPECSMITH_VOICE_STUB", "").strip()
    if stub:
        return TranscribeResult(text=stub, backend="stub")

    try:
        import whisper_cpp_python  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        raise VoiceUnavailableError(
            "whisper-cpp-python is not installed. Run "
            "`pipx inject specsmith whisper-cpp-python` "
            "(or `pip install specsmith[voice]`)."
        ) from exc

    model_path = _resolve_model_path()
    if model_path is None:
        raise VoiceUnavailableError(
            "No whisper model found. Set SPECSMITH_VOICE_MODEL or place a "
            f".bin model under {default_model_dir()}."
        )

    start = _time.perf_counter()
    whisper = whisper_cpp_python.Whisper(model_path=str(model_path))
    out = whisper.transcribe(str(path))
    text = out.get("text") if isinstance(out, dict) else str(out)
    return TranscribeResult(
        text=str(text or "").strip(),
        backend="whisper-cpp",
        model=model_path.name,
        duration_s=_time.perf_counter() - start,
    )


__all__ = [
    "TranscribeResult",
    "VoiceUnavailableError",
    "default_model_dir",
    "is_available",
    "transcribe",
]
