# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""specsmith — Forge governed project scaffolds."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

try:
    __version__: str = _pkg_version("specsmith")
except PackageNotFoundError:  # running from source without install
    __version__ = "0.10.1"  # fallback: keep in sync with pyproject.toml
