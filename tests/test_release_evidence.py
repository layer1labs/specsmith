from copy import deepcopy
from pathlib import Path

import pytest

from scripts.release_evidence import create_receipt, create_seal, digest
from scripts.verify_publication import verify_pypi_files


def test_receipt_links_immutable_seal() -> None:
    seal = create_seal({"candidate_version": "1.2.3", "wheel_sha256": "a" * 64})
    receipt = create_receipt(seal, {"pypi_version": "1.2.3"}, status="verified")
    assert receipt["seal_sha256"] == seal["seal_sha256"]
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    assert receipt["receipt_sha256"] == digest(unsigned)


def test_tampered_seal_is_rejected() -> None:
    seal = create_seal({"candidate_version": "1.2.3"})
    tampered = deepcopy(seal)
    tampered["closure"]["candidate_version"] = "9.9.9"
    with pytest.raises(ValueError, match="digest mismatch"):
        create_receipt(tampered, {}, status="failed")


def test_pypi_verification_requires_matching_artifact_digest(tmp_path: Path) -> None:
    wheel = tmp_path / "specsmith-1.2.3-py3-none-any.whl"
    wheel.write_bytes(b"candidate")
    expected = "9e78b74e18d9b38b8e6b6b6779b7fd4d83e92f5cc98d0e5f48a7f5f52c9af1d8"
    payload = {
        "urls": [
            {
                "filename": wheel.name,
                "url": "https://example.invalid/wheel",
                "digests": {"sha256": expected},
            }
        ]
    }
    with pytest.raises(ValueError, match="digest mismatch"):
        verify_pypi_files(tmp_path, payload)
