#!/usr/bin/env python3
"""sign_license.py — Issue a signed specsmith-esdb license file.

PRIVATE TOOL — not shipped in the specsmith wheel.  Run locally to issue
licenses to customers.  The matching private key must NEVER be committed to
any repository.

Usage
-----
    # Interactive (prompts for all fields)
    python scripts/sign_license.py --private-key /path/to/esdb_private.key

    # Non-interactive
    python scripts/sign_license.py \\
        --private-key /path/to/esdb_private.key \\
        --customer acme-corp \\
        --expires 2027-06-11 \\
        --output /tmp/acme-corp.esdb.key

Private key format
------------------
The private key file must contain a single line: the raw Ed25519 private key
as base64.  Generate one with:

    python -c "
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
    import base64
    priv = Ed25519PrivateKey.generate()
    raw = priv.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    print(base64.b64encode(raw).decode())
    "

IMPORTANT: Store the private key in a secure secrets manager (1Password,
AWS Secrets Manager, etc.) and NEVER commit it to version control.  The
corresponding public key is embedded in src/specsmith/esdb/_license.py.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from datetime import date, timedelta
from pathlib import Path

_PRODUCT = "specsmith-esdb"


def sign_license(
    private_key_b64: str,
    customer: str,
    expires_at: str,
    issued_at: str | None = None,
) -> dict[str, str]:
    """Create a signed license dict.

    Args:
        private_key_b64: Raw Ed25519 private key, base64-encoded.
        customer:        Customer identifier (e.g. 'acme-corp').
        expires_at:      Expiry date string 'YYYY-MM-DD'.
        issued_at:       Issue date string 'YYYY-MM-DD' (defaults to today).

    Returns:
        License dict ready to be written as JSON.
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    issued = issued_at or date.today().isoformat()

    # Validate dates
    date.fromisoformat(issued)
    date.fromisoformat(expires_at)

    priv_bytes = base64.b64decode(private_key_b64.strip())
    priv_key = Ed25519PrivateKey.from_private_bytes(priv_bytes)

    payload = f"{customer}|{_PRODUCT}|{issued}|{expires_at}".encode()
    sig_bytes = priv_key.sign(payload)
    sig_b64 = base64.b64encode(sig_bytes).decode("ascii")

    return {
        "customer": customer,
        "product": _PRODUCT,
        "issued_at": issued,
        "expires_at": expires_at,
        "signature": sig_b64,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Issue a signed specsmith-esdb license file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--private-key",
        required=True,
        help="Path to file containing raw Ed25519 private key (base64, one line).",
    )
    parser.add_argument("--customer", help="Customer identifier (e.g. 'acme-corp').")
    parser.add_argument(
        "--expires",
        help="Expiry date YYYY-MM-DD (default: 1 year from today).",
    )
    parser.add_argument(
        "--output",
        help="Output file path (default: <customer>.esdb.key in current dir).",
    )
    parser.add_argument(
        "--issued-at",
        help="Issue date YYYY-MM-DD (default: today).",
    )
    args = parser.parse_args()

    # Load private key
    key_path = Path(args.private_key)
    if not key_path.exists():
        print(f"Error: private key file not found: {key_path}", file=sys.stderr)
        sys.exit(1)
    priv_key_b64 = key_path.read_text(encoding="utf-8").strip()

    # Prompt for missing fields
    customer = args.customer or input("Customer identifier (e.g. acme-corp): ").strip()
    if not customer:
        print("Error: customer is required.", file=sys.stderr)
        sys.exit(1)

    default_expires = (date.today() + timedelta(days=365)).isoformat()
    expires_at = (
        args.expires or input(f"Expiry date [YYYY-MM-DD, default {default_expires}]: ").strip()
    )
    if not expires_at:
        expires_at = default_expires

    try:
        license_data = sign_license(
            priv_key_b64,
            customer=customer,
            expires_at=expires_at,
            issued_at=args.issued_at,
        )
    except Exception as exc:
        print(f"Error signing license: {exc}", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.output) if args.output else Path(f"{customer}.esdb.key")
    out_path.write_text(json.dumps(license_data, indent=2) + "\n", encoding="utf-8")

    print(f"✓ License written to: {out_path}")
    print(f"  Customer : {customer}")
    print(f"  Product  : {_PRODUCT}")
    print(f"  Issued   : {license_data['issued_at']}")
    print(f"  Expires  : {expires_at}")
    print()
    print("Send the .esdb.key file to the customer.")
    print("They activate it with: specsmith esdb enable --key-file <path>")


if __name__ == "__main__":
    main()
