# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Persistent update-channel selection for specsmith.

Users can pin specsmith to a release channel so that ``self-update`` always
upgrades to the right track regardless of what is currently installed::

    specsmith channel set dev     # always track pre-releases
    specsmith channel set stable  # always track stable releases
    specsmith channel get         # show effective channel + resolution source

Storage:  ``~/.specsmith/channel``  (plain text, first line is "stable" or "dev").
Fallback: if no preference is persisted, the channel is inferred from the
          installed version (``X.Y.Z.devN`` → dev, otherwise stable).
"""

from __future__ import annotations

import contextlib
from pathlib import Path

VALID_CHANNELS: tuple[str, ...] = ("stable", "dev")

_CHANNEL_FILE = Path.home() / ".specsmith" / "channel"


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------


def get_persisted_channel() -> str | None:
    """Return the user's saved channel preference, or *None* if unset.

    Returns ``None`` rather than raising so callers can fall back gracefully.
    """
    try:
        text = _CHANNEL_FILE.read_text(encoding="utf-8").strip()
        if text in VALID_CHANNELS:
            return text
    except (OSError, ValueError):
        pass
    return None


def set_persisted_channel(channel: str) -> None:
    """Persist *channel* to ``~/.specsmith/channel``.

    Raises :exc:`ValueError` for unknown channel names.  Creates parent
    directories as needed.
    """
    channel = channel.strip().lower()
    if channel not in VALID_CHANNELS:
        raise ValueError(f"Unknown channel {channel!r}. Valid choices: {', '.join(VALID_CHANNELS)}")
    _CHANNEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CHANNEL_FILE.write_text(channel + "\n", encoding="utf-8")


def clear_persisted_channel() -> None:
    """Remove a saved channel preference (reset to auto-detect)."""
    with contextlib.suppress(OSError):
        _CHANNEL_FILE.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


def _channel_from_version(version: str) -> str:
    """Infer channel from an installed version string."""
    return "dev" if ".dev" in version else "stable"


def effective_channel(*, _version: str | None = None) -> str:
    """Return the effective update channel.

    Resolution order:
    1. User's persisted preference (``~/.specsmith/channel``).
    2. Installed version suffix — ``.devN`` → ``dev``, otherwise ``stable``.

    *_version* is an override used only in unit tests.
    """
    persisted = get_persisted_channel()
    if persisted is not None:
        return persisted

    if _version is None:
        from specsmith import __version__

        _version = __version__

    return _channel_from_version(_version)


def effective_channel_with_source(*, _version: str | None = None) -> tuple[str, str]:
    """Like :func:`effective_channel` but also returns how it was determined.

    Returns ``(channel, source)`` where *source* is one of:
    - ``"user"``     — read from ``~/.specsmith/channel``
    - ``"version"``  — inferred from installed version string
    """
    persisted = get_persisted_channel()
    if persisted is not None:
        return persisted, "user"

    if _version is None:
        from specsmith import __version__

        _version = __version__

    return _channel_from_version(_version), "version"
