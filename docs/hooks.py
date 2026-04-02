# SPDX-License-Identifier: MIT
"""MkDocs hook — inject package version into documentation pages.

Replaces ``{{ version }}`` placeholders with the installed specsmith version.
This eliminates hardcoded version strings from documentation source files.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("mkdocs.hooks.version")


def _get_version() -> str:
    """Read specsmith version from installed package metadata."""
    try:
        from specsmith import __version__

        return __version__
    except Exception:  # noqa: BLE001
        return "dev"


def on_page_markdown(markdown: str, **_kwargs: Any) -> str:
    """Replace {{ version }} placeholders in every page."""
    ver = _get_version()
    return markdown.replace("{{ version }}", ver)
