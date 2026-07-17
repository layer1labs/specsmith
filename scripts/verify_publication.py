"""Verify published PyPI artifacts and create a linked release receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

try:
    from scripts.release_evidence import create_receipt
except ModuleNotFoundError:  # Direct execution adds scripts/, not the repository root.
    from release_evidence import create_receipt


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_pypi_files(dist_dir: Path, payload: dict[str, Any]) -> list[dict[str, str]]:
    local = sorted((*dist_dir.glob("*.whl"), *dist_dir.glob("*.tar.gz")))
    if not local:
        raise ValueError("no wheel or source archive found")
    published = {entry["filename"]: entry for entry in payload.get("urls", [])}
    verified: list[dict[str, str]] = []
    for path in local:
        digest = sha256_file(path)
        remote = published.get(path.name)
        if remote is None:
            raise ValueError(f"PyPI is missing {path.name}")
        remote_digest = remote.get("digests", {}).get("sha256")
        if remote_digest != digest:
            raise ValueError(f"PyPI digest mismatch for {path.name}")
        verified.append({"filename": path.name, "sha256": digest, "url": remote["url"]})
    return verified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seal", type=Path, required=True)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--github-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    version = args.version.removeprefix("v")
    with urllib.request.urlopen(
        f"https://pypi.org/pypi/specsmith/{version}/json", timeout=30
    ) as response:
        payload = json.load(response)
    if payload.get("info", {}).get("version") != version:
        raise ValueError("PyPI version response does not match the release")

    seal = json.loads(args.seal.read_text(encoding="utf-8"))
    publication = {
        "version": version,
        "tag": args.tag,
        "repository": args.repository,
        "github_release_url": args.github_url,
        "pypi_url": f"https://pypi.org/project/specsmith/{version}/",
        "artifacts": verify_pypi_files(args.dist, payload),
    }
    receipt = create_receipt(seal, publication, status="verified")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
