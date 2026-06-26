"""REQ-417 / TEST-427: honest ESDB integrity reporting in `esdb status` and `resume`.

`esdb status` must render "Integrity OK" only when the hash chain verifies and
"Integrity FAILED" when it does not (previously the label was hardcoded). `resume`
must drive its leading ESDB indicator from the real chain state instead of always
printing a green check.
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

    def __init__(self, *, chain_valid: bool) -> None:
        self._chain_valid = chain_valid

    def __enter__(self) -> _StatusStore:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def record_count(self) -> int:
        return 3

    def chain_valid(self) -> bool:
        return self._chain_valid

    def query(self, kind: str) -> list[object]:  # noqa: ARG002 - signature parity only
        return []


def _run_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, chain_valid: bool) -> str:
    """Invoke `esdb status` (human-readable) with a fake SQLite store; return output."""
    buf = io.StringIO()
    store = _StatusStore(chain_valid=chain_valid)
    monkeypatch.setattr(cli_mod, "console", Console(file=buf, force_terminal=False, width=200))
    monkeypatch.setattr(esdb_mod, "ESDB_BACKEND", "sqlite")
    monkeypatch.setattr("specsmith.sync.auto_migrate_if_needed", lambda _root: {})
    monkeypatch.setattr("specsmith.esdb.open_default_store", lambda *_a, **_k: store)
    monkeypatch.setattr("specsmith.esdb._license.resolve_license_path", lambda: None)
    cli_mod.esdb_status_cmd.callback(str(tmp_path), False)
    return buf.getvalue()


def test_esdb_status_reports_failed_when_chain_invalid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = _run_status(tmp_path, monkeypatch, chain_valid=False)
    assert "Integrity FAILED" in out
    assert "Integrity OK" not in out


def test_esdb_status_reports_ok_when_chain_valid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = _run_status(tmp_path, monkeypatch, chain_valid=True)
    assert "Integrity OK" in out
    assert "Integrity FAILED" not in out


class _ResumeStatus:
    """Stand-in for EsdbBridge.status() used by `resume`."""

    def __init__(self, chain_valid: bool) -> None:
        self.available = True
        self.backend = "sqlite"
        self.record_count = 5
        self.chain_valid = chain_valid


def _make_bridge(chain_valid: bool) -> type:
    class _Bridge:
        def __init__(self, *_a: object, **_k: object) -> None:
            pass

        def status(self) -> _ResumeStatus:
            return _ResumeStatus(chain_valid)

    return _Bridge


class _Sync:
    success = True
    message = "synced"


class _Runner:
    def __init__(self, **_k: object) -> None:
        pass

    def run_interactive(self) -> None:
        return None


def _resume_esdb_line(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, chain_valid: bool) -> str:
    """Run `resume` with stubbed pull/bridge/agent; return the rendered ESDB line."""
    buf = io.StringIO()
    monkeypatch.setattr(cli_mod, "console", Console(file=buf, force_terminal=False, width=200))
    monkeypatch.setattr("specsmith.vcs_commands.run_sync", lambda _root: _Sync())
    monkeypatch.setattr("specsmith.esdb.bridge.EsdbBridge", _make_bridge(chain_valid))
    monkeypatch.setattr("specsmith.agent.runner.AgentRunner", _Runner)
    cli_mod.resume_cmd.callback(str(tmp_path), None, None, None, "balanced")
    return next(line for line in buf.getvalue().splitlines() if "ESDB:" in line)


def test_resume_indicator_red_when_chain_invalid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    line = _resume_esdb_line(tmp_path, monkeypatch, chain_valid=False)
    assert "\u2717" in line  # ✗ cross
    assert "\u2713" not in line  # no green check anywhere on the line


def test_resume_indicator_green_when_chain_valid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    line = _resume_esdb_line(tmp_path, monkeypatch, chain_valid=True)
    assert "\u2713" in line  # ✓ check
    assert "\u2717" not in line  # no cross
