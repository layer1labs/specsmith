# specsmith.esdb — ESDB integration package
#
# Re-exports the full chronomemory v0.1.1 public surface under the
# specsmith.esdb namespace so internal modules can use a single import
# path and never import chronomemory directly in more than one place.

# Re-export query and metrics as module references so callers can do:
#   from specsmith.esdb import query, metrics
from chronomemory import (
    RUST_BACKEND,
    # Core store
    ChronoRecord,
    ChronoStore,
    # Phase 2: context pack compiler
    ContextPack,
    ContextPackCompiler,
    ContextPackEntry,
    DependencyEdge,
    # Phase 2: dependency graph
    DepGraph,
    # Bridge (backward-compat with .specsmith/*.json)
    EsdbBridge,
    EsdbRecord,
    EsdbStatus,
    # Phase 2: epistemic rollback
    RollbackReport,
    # Phase 3: optional Rust acceleration (None / False when not compiled)
    RustChronoStore,
    RustRecord,
    WalEvent,
    invalidate,
    metrics,  # noqa: F401 — module re-export
    open_store,
    query,  # noqa: F401 — module re-export
)

__all__ = [
    # Core
    "ChronoStore",
    "ChronoRecord",
    "WalEvent",
    "open_store",
    # Bridge
    "EsdbBridge",
    "EsdbRecord",
    "EsdbStatus",
    # Phase 2
    "DepGraph",
    "DependencyEdge",
    "RollbackReport",
    "invalidate",
    "ContextPack",
    "ContextPackCompiler",
    "ContextPackEntry",
    # Phase 3
    "RustChronoStore",
    "RustRecord",
    "RUST_BACKEND",
    # Modules
    "query",
    "metrics",
]
