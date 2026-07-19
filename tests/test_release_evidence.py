import json
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError

import pytest

from scripts.release_evidence import create_receipt, create_seal, digest
from scripts.verify_publication import (
    PYPI_PROPAGATION_ATTEMPTS,
    PYPI_PROPAGATION_DELAY_SECONDS,
    fetch_pypi_payload,
    verify_pypi_files,
)


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


def test_pypi_fetch_retries_release_propagation(monkeypatch: pytest.MonkeyPatch) -> None:
    responses: list[Exception | BytesIO] = [
        HTTPError("https://example.invalid", 404, "Not Found", {}, None),
        BytesIO(json.dumps({"info": {"version": "1.2.3"}}).encode()),
    ]

    def fake_urlopen(url: str, timeout: int) -> BytesIO:
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    sleeps: list[float] = []
    monkeypatch.setattr("scripts.verify_publication.urllib.request.urlopen", fake_urlopen)
    monkeypatch.setattr("scripts.verify_publication.time.sleep", sleeps.append)

    payload = fetch_pypi_payload("1.2.3", attempts=2, delay_seconds=0)

    assert payload["info"]["version"] == "1.2.3"
    assert sleeps == [0]


def test_pypi_default_propagation_window_is_at_least_three_minutes() -> None:
    assert (PYPI_PROPAGATION_ATTEMPTS - 1) * PYPI_PROPAGATION_DELAY_SECONDS >= 180
