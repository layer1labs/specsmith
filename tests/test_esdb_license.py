"""Tests for ESDB license gate and MCP yaml_mode req_list fix (REQ-364, REQ-366, REQ-367).

TEST-365: MCP governance_req_list reads YAML in yaml_mode  (see test_mcp_server.py)
TEST-367: License gate — valid/invalid/expired/wrong-key/override scenarios
TEST-368: chronomemory LICENSE is proprietary (not MIT)
"""

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from specsmith.esdb._license import (
    _PRODUCT_NAME,
    check_license,
    resolve_license_path,
    verify_license_file,
)

# ---------------------------------------------------------------------------
# Helpers — generate a valid license using the test private key
# ---------------------------------------------------------------------------

_PRIVATE_KEY_B64 = "BLbppnF+/ThDo2G25Vc6P7smfvr1Kup9qd9vtDJpybA="  # test key only


def _make_license_file(
    tmp_path: Path,
    *,
    customer: str = "test-corp",
    product: str = _PRODUCT_NAME,
    issued_at: str = "2026-01-01",
    expires_at: str = "2099-12-31",
    tamper: bool = False,
    filename: str = "test.esdb.key",
) -> Path:
    """Create a signed license file in tmp_path and return its path."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv_bytes = base64.b64decode(_PRIVATE_KEY_B64)
    priv_key = Ed25519PrivateKey.from_private_bytes(priv_bytes)

    payload = f"{customer}|{product}|{issued_at}|{expires_at}".encode()
    sig_bytes = priv_key.sign(payload)
    sig_b64 = base64.b64encode(sig_bytes).decode("ascii")

    data = {
        "customer": customer,
        "product": product,
        "issued_at": issued_at,
        "expires_at": expires_at,
        "signature": sig_b64 if not tamper else "AAAA" + sig_b64[4:],
    }
    key_path = tmp_path / filename
    key_path.write_text(json.dumps(data), encoding="utf-8")
    return key_path


# ---------------------------------------------------------------------------
# TEST-367: verify_license_file — valid license
# ---------------------------------------------------------------------------


def test_base_install_includes_cryptography_for_license_verification() -> None:
    """TEST-472: pipx base installs need the verifier used by esdb enable."""
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    base_dependencies = pyproject.read_text(encoding="utf-8").split(
        "[project.optional-dependencies]", maxsplit=1
    )[0]

    assert any(
        line.strip().startswith('"cryptography>=42.0"')
        for line in base_dependencies.splitlines()
    )


def test_valid_license(tmp_path: Path) -> None:
    key = _make_license_file(tmp_path)
    status = verify_license_file(key)
    assert status.valid is True
    assert status.customer == "test-corp"
    assert status.expires_at == "2099-12-31"


def test_valid_license_bool_truthy(tmp_path: Path) -> None:
    key = _make_license_file(tmp_path)
    assert bool(verify_license_file(key)) is True


# ---------------------------------------------------------------------------
# Invalid / missing
# ---------------------------------------------------------------------------


def test_missing_file_returns_invalid(tmp_path: Path) -> None:
    status = verify_license_file(tmp_path / "nonexistent.key")
    assert status.valid is False
    assert "not found" in status.reason


def test_malformed_json(tmp_path: Path) -> None:
    key = tmp_path / "bad.key"
    key.write_text("not json", encoding="utf-8")
    status = verify_license_file(key)
    assert status.valid is False
    assert "unreadable" in status.reason


def test_missing_fields(tmp_path: Path) -> None:
    key = tmp_path / "missing.key"
    key.write_text(json.dumps({"customer": "x"}), encoding="utf-8")
    status = verify_license_file(key)
    assert status.valid is False
    assert "missing fields" in status.reason


def test_wrong_product(tmp_path: Path) -> None:
    key = _make_license_file(tmp_path, product="other-product")
    status = verify_license_file(key)
    assert status.valid is False
    assert "product" in status.reason


def test_expired_license(tmp_path: Path) -> None:
    key = _make_license_file(tmp_path, expires_at="2020-01-01")
    status = verify_license_file(key)
    assert status.valid is False
    assert "expired" in status.reason


def test_invalid_expires_format(tmp_path: Path) -> None:
    data = {
        "customer": "x",
        "product": _PRODUCT_NAME,
        "issued_at": "2026-01-01",
        "expires_at": "not-a-date",
        "signature": "AAAA",
    }
    key = tmp_path / "bad_date.key"
    key.write_text(json.dumps(data), encoding="utf-8")
    status = verify_license_file(key)
    assert status.valid is False
    assert "invalid" in status.reason.lower()


def test_tampered_signature(tmp_path: Path) -> None:
    key = _make_license_file(tmp_path, tamper=True)
    status = verify_license_file(key)
    assert status.valid is False
    assert "invalid" in status.reason


# ---------------------------------------------------------------------------
# resolve_license_path + check_license
# ---------------------------------------------------------------------------


def test_resolve_license_path_from_env(tmp_path: Path) -> None:
    key = _make_license_file(tmp_path)
    with patch.dict(os.environ, {"SPECSMITH_ESDB_KEY": str(key)}):
        found = resolve_license_path()
    assert found == key


def test_resolve_license_path_default(tmp_path: Path) -> None:
    # resolve_license_path looks for Path.home() / ".specsmith" / "esdb.key"
    specsmith_dir = tmp_path / ".specsmith"
    specsmith_dir.mkdir()
    _make_license_file(specsmith_dir, filename="esdb.key")
    from specsmith.esdb import _license as lic_mod  # noqa: PLC0415

    def fake_home() -> Path:
        return tmp_path

    with patch.object(Path, "home", staticmethod(fake_home)):
        found = lic_mod.resolve_license_path()
    assert found is not None


def test_check_license_no_key_returns_invalid() -> None:
    with (
        patch.dict(os.environ, {}, clear=True),
        patch("specsmith.esdb._license.resolve_license_path", return_value=None),
    ):
        status = check_license(warn=False)
    assert status.valid is False


def test_check_license_valid_key(tmp_path: Path) -> None:
    key = _make_license_file(tmp_path)
    with patch("specsmith.esdb._license.resolve_license_path", return_value=key):
        status = check_license(warn=False)
    assert status.valid is True


def test_check_license_issues_warning_on_failure() -> None:
    with (
        patch("specsmith.esdb._license.resolve_license_path", return_value=None),
        pytest.warns(UserWarning, match="ESDB"),
    ):
        check_license(warn=True)


# ---------------------------------------------------------------------------
# open_default_store backend selection
# ---------------------------------------------------------------------------


def test_sqlite_backend_forced_via_env(tmp_path: Path) -> None:
    from specsmith.esdb import open_default_store
    from specsmith.esdb.sqlite_store import SqliteStore

    with patch.dict(os.environ, {"SPECSMITH_ESDB_BACKEND": "sqlite"}):
        store = open_default_store(tmp_path, warn=False)
    assert isinstance(store, SqliteStore)


def test_sqlite_backend_when_no_license(tmp_path: Path) -> None:
    from specsmith.esdb import open_default_store
    from specsmith.esdb.sqlite_store import SqliteStore

    with patch("specsmith.esdb._license.resolve_license_path", return_value=None):
        store = open_default_store(tmp_path, warn=False)
    assert isinstance(store, SqliteStore)


# ---------------------------------------------------------------------------
# TEST-368: chronomemory LICENSE is proprietary
# ---------------------------------------------------------------------------

_CHRONO_LICENSE_PATH = (
    Path(__file__).parent.parent.parent.parent  # up from tests/ to Development/
    / "chronomemory"
    / "LICENSE"
)
_CHRONO_PYPROJECT_PATH = (
    Path(__file__).parent.parent.parent.parent / "chronomemory" / "pyproject.toml"
)


@pytest.mark.skipif(
    not _CHRONO_LICENSE_PATH.exists(),
    reason="chronomemory repo not found at expected path",
)
def test_chronomemory_license_is_proprietary() -> None:
    """REQ-367: chronomemory LICENSE must not be MIT and must declare Proprietary."""
    text = _CHRONO_LICENSE_PATH.read_text(encoding="utf-8")
    # Must NOT open with the MIT boilerplate heading
    assert not text.strip().startswith("MIT License"), (
        "chronomemory LICENSE must not be MIT (file opens with MIT License header)"
    )
    # Must declare PROPRIETARY in the header area (first 300 chars)
    assert "PROPRIETARY" in text[:300].upper(), (
        "chronomemory LICENSE must declare PROPRIETARY near the top"
    )
    assert "Layer1Labs" in text


@pytest.mark.skipif(
    not _CHRONO_PYPROJECT_PATH.exists(),
    reason="chronomemory repo not found at expected path",
)
def test_chronomemory_pyproject_proprietary_classifier() -> None:
    """REQ-367: chronomemory pyproject.toml must declare Proprietary license."""
    text = _CHRONO_PYPROJECT_PATH.read_text(encoding="utf-8")
    assert "MIT" not in text.split("[project]")[1].split("[project.")[0], (
        "chronomemory [project] section must not declare MIT license"
    )
    assert "Proprietary" in text


# ---------------------------------------------------------------------------
# TEST-372 / issue #263: esdb status JSON output diagnostics
# ---------------------------------------------------------------------------


class _FakeStore:
    def __enter__(self) -> _FakeStore:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def record_count(self) -> int:
        return 7

    def chain_valid(self) -> bool:
        return True


def test_esdb_status_json_uses_active_backend(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """REQ-366/#263: status JSON must report the backend after open_default_store."""
    from specsmith import esdb as esdb_mod
    from specsmith.cli import esdb_status_cmd

    old_backend = esdb_mod.ESDB_BACKEND
    # Inject a fake chronomemory module so the test runs without the package installed.
    mock_chrono = MagicMock()
    mock_chrono.EsdbBridge.return_value.record_counts.return_value = {"requirement": 3}
    try:
        with (
            patch.dict(sys.modules, {"chronomemory": mock_chrono}),
            patch("specsmith.sync.auto_migrate_if_needed", return_value={}),
            patch("specsmith.esdb.open_default_store", return_value=_FakeStore()),
            patch("specsmith.esdb._license.resolve_license_path", return_value=None),
        ):
            esdb_mod.ESDB_BACKEND = "chronomemory"
            esdb_status_cmd.callback(str(tmp_path), True)
    finally:
        esdb_mod.ESDB_BACKEND = old_backend

    payload = json.loads(capsys.readouterr().out)
    assert payload["backend"] == "chronomemory"
    assert payload["backend_label"] == "ChronoStore WAL (chronomemory commercial)"
    assert payload["record_count"] == 7


def test_esdb_status_json_stdout_failure_has_structured_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """REQ-366/REQ-392/#263: stdout write failures exit 1 with structured stderr error."""
    from specsmith import esdb as esdb_mod
    from specsmith.cli import esdb_status_cmd

    class BadStdout:
        def write(self, _: str) -> int:
            raise OSError("simulated stdout failure")

        def flush(self) -> None:
            raise OSError("simulated stdout flush failure")

    old_backend = esdb_mod.ESDB_BACKEND
    # Inject a fake chronomemory module so the test runs without the package installed.
    mock_chrono = MagicMock()
    mock_chrono.EsdbBridge.return_value.record_counts.return_value = {}
    try:
        with (
            patch.dict(sys.modules, {"chronomemory": mock_chrono}),
            patch("specsmith.sync.auto_migrate_if_needed", return_value={}),
            patch("specsmith.esdb.open_default_store", return_value=_FakeStore()),
            patch("specsmith.esdb._license.resolve_license_path", return_value=None),
        ):
            esdb_mod.ESDB_BACKEND = "chronomemory"
            monkeypatch.setattr(sys, "stdout", BadStdout())
            with pytest.raises(SystemExit) as exc_info:
                esdb_status_cmd.callback(str(tmp_path), True)
    finally:
        esdb_mod.ESDB_BACKEND = old_backend

    # Must exit 1 — not 0, not an Abort (REQ-392)
    assert exc_info.value.code == 1

    err = capsys.readouterr().err
    payload = json.loads(err)
    assert payload["ok"] is False
    assert payload["error"] == "esdb status: stdout write failed"
    assert "simulated stdout failure" in payload["reason"]
