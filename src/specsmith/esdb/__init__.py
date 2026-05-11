# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs / BitConcepts, LLC.
"""ChronoMemory ESDB Python bridge.

Provides a pure-Python adapter for the Rust ESDB engine.
Until PyO3 bindings are compiled, this module exposes the ESDB
data model as Python dataclasses that mirror the Rust types.
"""

from __future__ import annotations

__all__ = ["EsdbBridge", "is_esdb_available"]


def is_esdb_available(project_dir: str = ".") -> bool:
    """Check if an ESDB exists for the given project."""
    from pathlib import Path

    esdb_dir = Path(project_dir).resolve() / ".chronomemory"
    return (esdb_dir / "events.wal").is_file()
