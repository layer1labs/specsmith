"""Stable-release version validation (REQ-450)."""

from __future__ import annotations

import re

_DEVELOPMENT_VERSION = re.compile(r"\d+\.\d+\.\d+\.dev\d+")
_STABLE_VERSION = re.compile(r"\d+\.\d+\.\d+")


def is_stable_version(version: str) -> bool:
    """Return whether *version* is a plain PEP 440 release without a suffix."""
    return _STABLE_VERSION.fullmatch(version) is not None


def is_development_version(version: str) -> bool:
    """Return whether *version* belongs to the explicit development channel."""
    return _DEVELOPMENT_VERSION.fullmatch(version) is not None


def require_stable_version(version: str, expected_version: str | None = None) -> None:
    """Raise a clear error before any stable-channel publication."""
    if not is_stable_version(version):
        raise ValueError(f"Stable release rejects non-final version: {version}")
    if expected_version is not None and version != expected_version.lstrip("v"):
        raise ValueError(f"Stable release version {version} does not match tag {expected_version}")


def require_development_version(version: str, expected_version: str | None = None) -> None:
    """Raise a clear error before an artifact enters the development channel."""
    if not is_development_version(version):
        raise ValueError(f"Development release requires an X.Y.Z.devN version: {version}")
    if expected_version is not None and version != expected_version:
        raise ValueError(
            f"Development release version {version} does not match expected {expected_version}"
        )
