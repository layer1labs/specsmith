# specsmith.esdb — ESDB integration package
#
# Two-tier backend architecture (REQ-365, REQ-366):
#
#   SQLite backend  (default, free, MIT — no external deps, no license required)
#       specsmith.esdb.sqlite_store.SqliteStore
#       DB at: <project_root>/.specsmith/esdb.sqlite3
#
#   ChronoStore backend  (commercial — requires chronomemory[esdb] + valid license)
#       chronomemory.ChronoStore via specsmith.esdb namespace
#       Requires: pip install specsmith[esdb]  AND  a valid Ed25519 license file
#       Contact: licensing@layer1labs.com
#
# Backend selection (open_default_store / ESDB_BACKEND):
#   1. SPECSMITH_ESDB_BACKEND=sqlite env var  → force SQLite
#   2. chronomemory installed + valid license  → ChronoStore
#   3. chronomemory installed, no valid license → warn + SQLite
#   4. chronomemory not installed              → SQLite silently
#
# Install chronomemory (commercial, requires license):
#   pip install specsmith[esdb]
#   specsmith esdb enable --key-file /path/to/your.esdb.key

import os as _os

_INSTALL_HINT = (
    "chronomemory (ESDB commercial backend) is not installed.\n"
    "Install: pip install specsmith[esdb]\n"
    "License: contact licensing@layer1labs.com to obtain a license key.\n"
    "specsmith[esdb] requires a valid Ed25519 license — see 'specsmith esdb enable --help'.\n"
    "The free SQLite backend is used by default without any license."
)

# ---------------------------------------------------------------------------
# SQLite backend — always available, free, MIT (REQ-365)
# ---------------------------------------------------------------------------
from specsmith.esdb.sqlite_store import SqliteRecord, SqliteStore  # noqa: E402

# ---------------------------------------------------------------------------
# chronomemory (ChronoStore) — commercial backend (REQ-366)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Backend dispatch helpers (REQ-365, REQ-366)
# ---------------------------------------------------------------------------

#: Active backend name — ``"sqlite"`` or ``"chronomemory"``.  Resolved lazily
#: on first call to ``open_default_store()``.
ESDB_BACKEND: str = "sqlite"  # updated by open_default_store at runtime


def open_default_store(
    project_root: "str | object",
    *,
    warn: bool = True,
) -> "SqliteStore | object":  # returns SqliteStore or ChronoStore
    """Return the appropriate ESDB store for *project_root*.

    Backend selection priority:

    1. ``SPECSMITH_ESDB_BACKEND=sqlite`` env var → :class:`SqliteStore`
    2. chronomemory installed + valid Ed25519 license → ``ChronoStore``
    3. chronomemory installed but no/invalid license → :class:`SqliteStore` + warning
    4. chronomemory not installed → :class:`SqliteStore` silently

    The store is **not** opened — call ``.open()`` or use as a context manager.
    """
    global ESDB_BACKEND  # noqa: PLW0603

    from pathlib import Path

    root = Path(str(project_root)).resolve()

    # Priority 1: explicit override
    if _os.environ.get("SPECSMITH_ESDB_BACKEND", "").strip().lower() == "sqlite":
        ESDB_BACKEND = "sqlite"
        return SqliteStore(root)

    # Priority 2/3: chronomemory + license check
    if CHRONO_AVAILABLE:
        from specsmith.esdb._license import check_license

        lic = check_license(warn=warn)
        if lic.valid:
            ESDB_BACKEND = "chronomemory"
            return ChronoStore(root)  # type: ignore[return-value]
        # Invalid/absent license — fall through to SQLite

    # Priority 4: SQLite default
    ESDB_BACKEND = "sqlite"
    return SqliteStore(root)


__all__ = [
    # SQLite backend (free, MIT)
    "SqliteStore",
    "SqliteRecord",
    # Backend dispatch
    "ESDB_BACKEND",
    "open_default_store",
    # Core chronomemory (commercial)
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
    # Availability flag
    "CHRONO_AVAILABLE",
]
