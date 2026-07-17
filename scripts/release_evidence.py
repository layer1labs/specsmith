"""Canonical pre-release seal and post-publication receipt helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def create_seal(closure: dict[str, Any]) -> dict[str, Any]:
    seal = {"schema": "specsmith-release-seal-v1", "closure": closure}
    return seal | {"seal_sha256": digest(seal)}


def create_receipt(
    seal: dict[str, Any], publication: dict[str, Any], *, status: str
) -> dict[str, Any]:
    if status not in {"verified", "incomplete", "failed"}:
        raise ValueError("invalid receipt status")
    expected = seal.get("seal_sha256")
    unsigned = {k: v for k, v in seal.items() if k != "seal_sha256"}
    if expected != digest(unsigned):
        raise ValueError("pre-release seal digest mismatch")
    receipt = {
        "schema": "specsmith-publication-receipt-v1",
        "seal_sha256": expected,
        "publication": publication,
        "status": status,
    }
    return receipt | {"receipt_sha256": digest(receipt)}
