# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Terminal-environment detection for specsmith (REQ-444).

Lets the interactive REPL (``specsmith run``) detect when it is running
inside Warp so it can adapt its banner / ``ready`` frame.  Detection is
based on the standard ``TERM_PROGRAM`` signal Warp sets, plus any
``WARP_*`` environment variables, and is purely read-only.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TerminalInfo:
    """Information about the host terminal."""

    is_warp: bool
    program: str
    version: str

    def as_dict(self) -> dict[str, object]:
        """Return a flat dict suitable for the ``ready`` event frame."""
        return asdict(self)


def detect_terminal(env: dict[str, str] | None = None) -> TerminalInfo:
    """Detect the host terminal from environment variables.

    Warp sets ``TERM_PROGRAM=WarpTerminal`` (and ``TERM_PROGRAM_VERSION``).
    As a fallback we also treat the presence of any ``WARP_*`` variable as a
    Warp signal.  Pass *env* to override ``os.environ`` (used by tests).
    """
    source = os.environ if env is None else env
    program = (source.get("TERM_PROGRAM") or "").strip()
    version = (source.get("TERM_PROGRAM_VERSION") or "").strip()
    is_warp = program == "WarpTerminal" or any(k.startswith("WARP_") for k in source)
    if is_warp and not program:
        program = "WarpTerminal"
    return TerminalInfo(is_warp=is_warp, program=program, version=version)
