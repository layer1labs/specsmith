"""specsmith.esdb.bridge — backward-compat bridge shim (chronomemory v0.1.1).

For direct use prefer importing from specsmith.esdb (the package __init__)
which re-exports the full chronomemory v0.1.1 surface and exposes the
backend-dispatch helper ``open_default_store()``.

This module is kept for any code that specifically imports from
specsmith.esdb.bridge.  chronomemory is a **commercial** optional dep —
see 'specsmith esdb status' for the active backend and
'specsmith esdb enable --help' for license activation.
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
