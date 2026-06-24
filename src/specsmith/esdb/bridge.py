"""specsmith.esdb.bridge — backward-compat bridge shim (chronomemory v0.1.1).

For direct use prefer importing from specsmith.esdb (the package __init__)
which re-exports the full chronomemory v0.1.1 surface and exposes the
backend-dispatch helper ``open_default_store()``.

This module is kept for any code that specifically imports from
specsmith.esdb.bridge.  chronomemory is a **commercial** optional dep —
see 'specsmith esdb status' for the active backend and
'specsmith esdb enable --help' for license activation.

When chronomemory is not installed, all exported names are stubs that raise
``ImportError`` on instantiation — the same pattern used in
``specsmith.esdb.__init__``.
"""

_INSTALL_HINT = (
    "chronomemory (ESDB commercial backend) is not installed.\n"
    "Install: pip install specsmith[esdb]\n"
    "License: contact licensing@layer1labs.ai to obtain a license key."
)

try:
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
except ImportError:  # pragma: no cover

    class _Stub:  # noqa: F811
        """Placeholder that raises a clear error on instantiation or call."""

        def __init__(self, *_: object, **__: object) -> None:
            raise ImportError(_INSTALL_HINT)

        def __call__(self, *_: object, **__: object) -> "_Stub":
            raise ImportError(_INSTALL_HINT)

    class _StubModule:  # noqa: F811
        def __getattr__(self, name: str) -> "_Stub":
            raise AttributeError(  # noqa: TRY301
                f"'{name}' is unavailable: {_INSTALL_HINT}"
            )

    EsdbBridge = EsdbRecord = EsdbStatus = ContextPackCompiler = DepGraph = _Stub  # noqa: F811
    query = _StubModule()  # noqa: F811
    metrics = _StubModule()  # noqa: F811
    RUST_BACKEND = False  # noqa: F811

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
