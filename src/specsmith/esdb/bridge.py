"""specsmith.esdb.bridge — backward-compat bridge shim (chronomemory v0.1.1).

For direct use prefer importing from specsmith.esdb (the package __init__)
which re-exports the full chronomemory v0.1.1 surface.  This module is kept
for any code that specifically imports from specsmith.esdb.bridge.
"""

from chronomemory import (
    RUST_BACKEND,
    ContextPackCompiler,
    DepGraph,
    EsdbBridge,
    EsdbRecord,
    EsdbStatus,
    metrics,
    query,
)

__all__ = [
    "EsdbBridge",
    "EsdbRecord",
    "EsdbStatus",
    "ContextPackCompiler",
    "DepGraph",
    "RUST_BACKEND",
    "query",
    "metrics",
]
