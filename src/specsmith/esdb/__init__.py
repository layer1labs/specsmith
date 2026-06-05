# specsmith.esdb — ESDB integration package
#
# Re-exports the full chronomemory v0.1.1 public surface under the
# specsmith.esdb namespace so internal modules can use a single import
# path and never import chronomemory directly in more than one place.
#
# chronomemory is a git-URL dependency stripped from the PyPI wheel.
# If it is not installed, all symbols are stubbed with a class that
# raises a clear ImportError with install instructions rather than
# crashing silently at module import time.
#
# Install the missing dep:
#   pipx inject specsmith "chronomemory @ git+https://github.com/layer1labs/chronomemory.git@v0.1.1"

_INSTALL_HINT = (
    "chronomemory is not installed.\n"
    "Run: pipx inject specsmith "
    '"chronomemory @ git+https://github.com/layer1labs/chronomemory.git@v0.1.1"'
)

try:
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

    CHRONO_AVAILABLE: bool = True

except ImportError:
    CHRONO_AVAILABLE = False

    class _Stub:  # type: ignore[no-redef]
        """Placeholder that raises a clear error on instantiation or call."""

        def __init__(self, *_: object, **__: object) -> None:
            raise ImportError(_INSTALL_HINT)

        def __call__(self, *_: object, **__: object) -> "_Stub":
            raise ImportError(_INSTALL_HINT)

        def __class_getitem__(cls, _: object) -> "type[_Stub]":
            return cls

    # Stub every exported name so `from specsmith.esdb import X` doesn't fail.
    ChronoRecord = ChronoStore = EsdbBridge = EsdbRecord = EsdbStatus = _Stub  # type: ignore[misc]
    ContextPack = ContextPackCompiler = ContextPackEntry = _Stub  # type: ignore[misc]
    DepGraph = DependencyEdge = RollbackReport = _Stub  # type: ignore[misc]
    RustChronoStore = RustRecord = WalEvent = invalidate = open_store = _Stub  # type: ignore[misc]
    RUST_BACKEND: bool = False  # type: ignore[misc]

    class _StubModule:
        """Stub module reference so 'from specsmith.esdb import query, metrics' works."""

        def __getattr__(self, name: str) -> "_Stub":
            raise ImportError(_INSTALL_HINT)

    query = _StubModule()  # type: ignore[assignment]
    metrics = _StubModule()  # type: ignore[assignment]

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
