# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""specsmith — Forge governed project scaffolds."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

try:
    __version__: str = _pkg_version("specsmith")
except PackageNotFoundError:  # running from source without install
    __version__ = "0.22.5"  # fallback: keep in sync with pyproject.toml

# Governance/schema version — independent from the package version.
# Bump this when the scaffold config schema or governance rules change.
GOVERNANCE_VERSION: str = "0.22.5"
