"""REQ-419 / TEST-429: `esdb status` human-readable output never aborts.

The human-readable branch must emit its status block even when the Rich console
render raises (for example the spurious ``KeyboardInterrupt`` observed on the
Windows legacy console, which Click converts to ``Abort``/exit 1). In that case
it falls back to a resilient plain-text stdout writer and still exits 0.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from rich.console import Console

from specsmith import cli as cli_mod
from specsmith import esdb as esdb_mod


class _StatusStore:
    """Minimal stand-in for an opened ESDB store used by `esdb status`."""

    def __init__(self, *, chain_valid: bool = True) -> None:
        self._chain_valid = chain_valid

    def __enter__(self) -> _StatusStore:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def record_count(self) -> int:
        return 7

    def chain_valid(self) -> bool:
        return self._chain_valid

    def query(self, kind: str) -> list[object]:  # noqa: ARG002 - signature parity only
        return []


def _patch_common(monkeypatch: pytest.MonkeyPatch, store: _StatusStore) -> None:
    monkeypatch.setattr(esdb_mod, "ESDB_BACKEND", "sqlite")
    monkeypatch.setattr("specsmith.sync.auto_migrate_if_needed", lambda _root: {})
    monkeypatch.setattr("specsmith.esdb.open_default_store", lambda *_a, **_k: store)
    monkeypatch.setattr("specsmith.esdb._license.resolve_license_path", lambda: None)


def test_human_readable_status_prints_via_console(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Healthy console: the status block is rendered through console.print."""
    buf = io.StringIO()
    monkeypatch.setattr(cli_mod, "console", Console(file=buf, force_terminal=False, width=200))
    _patch_common(monkeypatch, _StatusStore(chain_valid=True))

    cli_mod.esdb_status_cmd.callback(str(tmp_path), False)

    out = buf.getvalue()
    assert "ESDB" in out
    assert "Records: 7" in out
    assert "Integrity OK" in out


class _RaisingConsole:
    """Console stand-in whose print() raises the spurious KeyboardInterrupt (#263)."""

    def print(self, *_a: object, **_k: object) -> None:
        raise KeyboardInterrupt


def test_human_readable_status_falls_back_when_console_aborts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When console.print raises, the plain stdout writer emits the block; exit 0."""
    monkeypatch.setattr(cli_mod, "console", _RaisingConsole())
    _patch_common(monkeypatch, _StatusStore(chain_valid=True))

    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)

    # Must NOT raise SystemExit / Abort / KeyboardInterrupt — i.e. it exits 0.
    cli_mod.esdb_status_cmd.callback(str(tmp_path), False)

    captured = out.getvalue()
    assert "ESDB" in captured
    assert "Records: 7" in captured
    assert "Integrity OK" in captured
