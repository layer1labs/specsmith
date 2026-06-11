"""Tests for ESDB license gate and MCP yaml_mode req_list fix (REQ-364, REQ-366, REQ-367).

TEST-365: MCP governance_req_list reads YAML in yaml_mode  (see test_mcp_server.py)
TEST-367: License gate — valid/invalid/expired/wrong-key/override scenarios
TEST-368: chronomemory LICENSE is proprietary (not MIT)
"""

from __future__ import annotations

import base64
import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from specsmith.esdb._license import (
    LicenseStatus,
    _ESDB_PUBLIC_KEY_B64,
    _PRODUCT_NAME,
    _canonical_payload,
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
    from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption

    priv_bytes = base64.b64decode(_PRIVATE_KEY_B64)
    priv_key = Ed25519PrivateKey.from_private_bytes(priv_bytes)

    payload = f"{customer}|{product}|{issued_at}|{expires_at}".encode("utf-8")
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
    key = _make_license_file(tmp_path, filename="esdb.key")
    default = Path.home() / ".specsmith" / "esdb.key"
    # Temporarily patch home to tmp_path
    with patch("specsmith.esdb._license.Path") as MockPath:
        # Only mock Path.home(); let other Path calls through
        import specsmith.esdb._license as lic_mod

        original_home = Path.home

        def fake_home():
            return tmp_path

        with patch.object(Path, "home", staticmethod(fake_home)):
            found = lic_mod.resolve_license_path()
        assert found is not None


def test_check_license_no_key_returns_invalid() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with patch("specsmith.esdb._license.resolve_license_path", return_value=None):
            status = check_license(warn=False)
    assert status.valid is False


def test_check_license_valid_key(tmp_path: Path) -> None:
    key = _make_license_file(tmp_path)
    with patch("specsmith.esdb._license.resolve_license_path", return_value=key):
        status = check_license(warn=False)
    assert status.valid is True


def test_check_license_issues_warning_on_failure() -> None:
    with patch("specsmith.esdb._license.resolve_license_path", return_value=None):
        with pytest.warns(UserWarning, match="ESDB"):
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
