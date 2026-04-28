# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""UTF-8 safe ``rich.console.Console`` factory.

Implements REQ-082: Specsmith CLI console output must not raise
``UnicodeEncodeError`` on Windows code pages such as ``cp1252`` when emitting
common UI glyphs (``\u26a0``, ``\u2192``, ``\u2713``, ``\u2717`` ...).

Strategy
--------
1. On Python 3.7+ ``sys.stdout``/``sys.stderr`` expose a ``reconfigure`` method
   that lets us switch the encoding to UTF-8 *in place*. We do this once,
   idempotently, with ``errors="backslashreplace"`` so a stray non-encodable
   byte degrades gracefully instead of crashing.
2. We construct a ``rich.console.Console`` with ``legacy_windows=False`` so
   rich does not fall back to the legacy Win32 renderer (which is the call
   site that raised ``UnicodeEncodeError``).

Calling :func:`make_console` is idempotent and safe on non-Windows platforms.
"""

from __future__ import annotations

import os
import sys

from rich.console import Console


def _ensure_utf8_stream(stream) -> None:
    """Best-effort upgrade of ``stream`` to UTF-8 with safe error handling."""
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is None:
        return
    try:
        reconfigure(encoding="utf-8", errors="backslashreplace")
    except (OSError, ValueError):
        # Some streams (notably captured/redirected streams in tests) refuse
        # reconfigure. That's fine \u2014 they are usually already UTF-8.
        return


def make_console(**kwargs) -> Console:
    """Return a UTF-8 safe ``rich.console.Console``.

    Any keyword arguments are forwarded to ``Console`` and override the
    safe defaults set by this helper.
    """
    _ensure_utf8_stream(sys.stdout)
    _ensure_utf8_stream(sys.stderr)

    # Belt-and-suspenders: Python honors PYTHONIOENCODING for child processes
    # we may spawn (e.g. tests, CI runners).
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    defaults = {
        "legacy_windows": False,
        "soft_wrap": False,
        "force_terminal": None,
    }
    defaults.update(kwargs)
    return Console(**defaults)
