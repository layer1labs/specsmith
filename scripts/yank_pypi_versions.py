#!/usr/bin/env python3
"""Yank all non-strategic specsmith versions from PyPI.

Usage:
    python scripts/yank_pypi_versions.py --token pypi-<your-token>

Versions kept (not yanked):
    0.11.7, 0.12.0, 0.13.0, 0.13.1, 0.14.0, 0.14.1

Everything else (dev builds, alphas, pre-0.11.7 stable) is yanked.
"""

import argparse
import sys
import time
import urllib.request
import json

KEEP = {
    "0.11.7",
    "0.12.0",
    "0.13.0",
    "0.13.1",
    "0.14.0",
    "0.14.1",
}

YANK_REASON = (
    "Superseded; only stable milestone releases are supported. "
    "Please upgrade to the latest version."
)

PROJECT = "specsmith"


def get_all_versions() -> list[str]:
    url = f"https://pypi.org/pypi/{PROJECT}/json"
    with urllib.request.urlopen(url) as resp:  # noqa: S310
        data = json.loads(resp.read())
    return list(data["releases"].keys())


def yank_version(version: str, token: str, dry_run: bool) -> None:
    url = f"https://pypi.org/pypi/{PROJECT}/{version}/json"
    # Check it exists first
    try:
        urllib.request.urlopen(url)  # noqa: S310
    except Exception:
        print(f"  SKIP  {version} (not found or already deleted)")
        return

    # Yank via PyPI API
    # PyPI's yank endpoint (warehouse API)
    yank_url = (
        f"https://pypi.org/manage/project/{PROJECT}/release/{version}/yank/"
    )
    data = f"reason={urllib.parse.quote(YANK_REASON)}".encode()

    if dry_run:
        print(f"  DRY   would yank {version}")
        return

    req = urllib.request.Request(
        yank_url,
        data=data,
        headers={
            "Authorization": f"Token {token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "specsmith-yank-script/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:  # noqa: S310
            status = resp.status
        print(f"  YANK  {version} → HTTP {status}")
    except urllib.error.HTTPError as e:
        print(f"  ERROR {version} → HTTP {e.code}: {e.reason}")
    except Exception as exc:
        print(f"  ERROR {version} → {exc}")

    time.sleep(0.5)  # be polite to the API


def main() -> None:
    import urllib.parse

    parser = argparse.ArgumentParser(description="Yank old specsmith PyPI versions")
    parser.add_argument("--token", required=True, help="PyPI API token (pypi-...)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be yanked")
    args = parser.parse_args()

    print(f"Fetching all {PROJECT} versions from PyPI...")
    all_versions = get_all_versions()
    print(f"Found {len(all_versions)} versions total.\n")

    to_yank = sorted(v for v in all_versions if v not in KEEP)
    to_keep = sorted(v for v in all_versions if v in KEEP)

    print(f"Keeping ({len(to_keep)}):")
    for v in to_keep:
        print(f"  KEEP  {v}")

    print(f"\nYanking ({len(to_yank)}):")
    for version in to_yank:
        yank_version(version, args.token, args.dry_run)

    print(f"\nDone. {'(dry run)' if args.dry_run else ''}")
    print("Note: yanked versions remain on PyPI but pip will not install")
    print("them unless explicitly pinned. Use the PyPI web UI to delete")
    print("individual files if you want permanent removal.")


if __name__ == "__main__":
    main()
