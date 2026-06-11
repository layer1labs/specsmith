# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""specsmith.esdb._license — offline Ed25519 license verification (REQ-366).

The chronomemory ESDB backend (ChronoStore) is a commercial add-on that requires
a valid signed license file.  This module verifies license files without any
network access using an Ed25519 public key embedded below.

License file format (JSON):
    {
        "customer":   "acme-corp",
        "product":    "specsmith-esdb",
        "issued_at":  "2026-06-11",
        "expires_at": "2027-06-11",
        "signature":  "<base64url Ed25519 sig over canonical payload>"
    }

Canonical payload that is signed:
    "<customer>|<product>|<issued_at>|<expires_at>"  (UTF-8, no trailing newline)

To obtain a license contact: licensing@layer1labs.com
"""

from __future__ import annotations

import base64
import json
import sys
import warnings
from datetime import date, datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Embedded public key (Ed25519, raw 32-byte, base64-encoded)
# IMPORTANT: The matching private key must NEVER be committed to any repository.
#            Keep it in a secure secrets manager (1Password, AWS Secrets Manager,
#            etc.).  If the private key is compromised, rotate by generating a
#            new keypair, embedding the new public key here, and re-issuing
#            all existing licenses.
# ---------------------------------------------------------------------------

_ESDB_PUBLIC_KEY_B64 = "aLEC0o3tip2b4Xj0mdGsw7lVDIEISuyGmkL4lYxgloE="
_PRODUCT_NAME = "specsmith-esdb"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _canonical_payload(data: dict[str, str]) -> bytes:
    """Return the canonical UTF-8 byte string that was signed."""
    return "|".join(
        [
            data.get("customer", ""),
            data.get("product", ""),
            data.get("issued_at", ""),
            data.get("expires_at", ""),
        ]
    ).encode("utf-8")


def _load_pub_key() -> "object":
    """Load the embedded Ed25519 public key via the *cryptography* library."""
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PublicKey,
        )
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat  # noqa: F401

        raw = base64.b64decode(_ESDB_PUBLIC_KEY_B64)
        return Ed25519PublicKey.from_public_bytes(raw)
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class LicenseStatus:
    """Result of a license verification attempt."""

    def __init__(
        self,
        valid: bool,
        reason: str = "",
        customer: str = "",
        expires_at: str = "",
    ) -> None:
        self.valid = valid
        self.reason = reason
        self.customer = customer
        self.expires_at = expires_at

    def __bool__(self) -> bool:
        return self.valid

    def __repr__(self) -> str:
        if self.valid:
            return f"LicenseStatus(valid=True, customer={self.customer!r}, expires={self.expires_at})"
        return f"LicenseStatus(valid=False, reason={self.reason!r})"


def verify_license_file(path: str | Path) -> LicenseStatus:
    """Verify an Ed25519-signed ESDB license file.

    Args:
        path: Path to the JSON license file (``~/.specsmith/esdb.key`` or
              the value of ``SPECSMITH_ESDB_KEY``).

    Returns:
        :class:`LicenseStatus` — ``.valid`` is True only when the file exists,
        is well-formed, has a valid signature, is for the correct product, and
        has not expired.
    """
    p = Path(path).expanduser()

    if not p.exists():
        return LicenseStatus(False, f"license file not found: {p}")

    # Parse JSON
    try:
        data: dict[str, str] = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return LicenseStatus(False, f"license file unreadable: {exc}")

    required = {"customer", "product", "issued_at", "expires_at", "signature"}
    missing = required - data.keys()
    if missing:
        return LicenseStatus(False, f"license missing fields: {sorted(missing)}")

    # Product check
    if data.get("product") != _PRODUCT_NAME:
        return LicenseStatus(
            False,
            f"license is for product '{data.get('product')}', expected '{_PRODUCT_NAME}'",
        )

    # Expiry check (compare against UTC date)
    try:
        exp = datetime.strptime(data["expires_at"], "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        today = datetime.now(tz=timezone.utc)
        if today > exp:
            return LicenseStatus(
                False,
                f"license expired on {data['expires_at']}",
                customer=data.get("customer", ""),
                expires_at=data["expires_at"],
            )
    except ValueError:
        return LicenseStatus(False, "license has invalid expires_at date format (expected YYYY-MM-DD)")

    # Cryptography import check
    pub_key = _load_pub_key()
    if pub_key is None:
        # cryptography not installed — treat as unlicensed (not an error)
        return LicenseStatus(
            False,
            "cryptography library not installed; cannot verify ESDB license "
            "(install specsmith[esdb] to enable ChronoStore)",
        )

    # Signature verification
    try:
        from cryptography.exceptions import InvalidSignature

        sig_bytes = base64.b64decode(data["signature"])
        payload = _canonical_payload(data)
        pub_key.verify(sig_bytes, payload)  # raises InvalidSignature on failure
    except Exception as exc:  # noqa: BLE001
        return LicenseStatus(False, f"license signature invalid: {exc}")

    return LicenseStatus(
        True,
        customer=data.get("customer", ""),
        expires_at=data.get("expires_at", ""),
    )


def resolve_license_path() -> Path | None:
    """Return the license file path from env var or default location, or None."""
    import os

    env_key = os.environ.get("SPECSMITH_ESDB_KEY", "").strip()
    if env_key:
        return Path(env_key).expanduser()
    default = Path.home() / ".specsmith" / "esdb.key"
    if default.exists():
        return default
    return None


def check_license(*, warn: bool = True) -> LicenseStatus:
    """Check the ESDB license from the standard locations.

    Returns a :class:`LicenseStatus`.  When *warn* is True and the license is
    invalid or absent a one-time :class:`UserWarning` is emitted to stderr (not
    raised, so it never crashes the CLI).
    """
    path = resolve_license_path()
    if path is None:
        status = LicenseStatus(
            False,
            "no ESDB license found — set SPECSMITH_ESDB_KEY or place license at "
            "~/.specsmith/esdb.key.  Using SQLite backend.",
        )
    else:
        status = verify_license_file(path)

    if not status.valid and warn:
        warnings.warn(
            f"specsmith ESDB: {status.reason}  Falling back to SQLite backend.",
            UserWarning,
            stacklevel=3,
        )
    return status
