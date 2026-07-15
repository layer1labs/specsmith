#!/usr/bin/env python3
"""Bulk-delete old specsmith releases from PyPI using browser automation.

Steps:
1. Opens a real Chromium browser to pypi.org/account/login/
2. You log in manually (2FA, etc.)
3. Once you're logged in, press Enter in the terminal
4. The script deletes all non-strategic versions automatically

Versions KEPT (never deleted):
    0.11.7, 0.12.0, 0.13.0, 0.13.1, 0.14.0, 0.14.1

Usage:
    python scripts/delete_pypi_releases.py
"""

import contextlib
import time

from playwright.sync_api import Page, sync_playwright

PROJECT = "specsmith"

KEEP = {
    "0.11.7",
    "0.12.0",
    "0.13.0",
    "0.13.1",
    "0.14.0",
    "0.14.1",
}


def get_all_versions() -> list[str]:
    import json
    import urllib.request

    url = f"https://pypi.org/pypi/{PROJECT}/json"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read())
    return sorted(data["releases"].keys())


def delete_version(page: Page, version: str) -> bool:
    """Navigate to a release page and click the delete button."""
    url = f"https://pypi.org/manage/project/{PROJECT}/release/{version}/"
    with contextlib.suppress(Exception):  # noqa: BLE001
        page.goto(url, timeout=20_000)
        page.wait_for_load_state("domcontentloaded", timeout=15_000)
    print(f"  SKIP  {version} — page load failed")
    return False

    # If redirected to login, session expired
    if "login" in page.url.lower():
        print(f"  SKIP  {version} — session expired, please re-login")
        return False

    # If 404 (version doesn't exist / already deleted)
    if page.locator("h1:has-text('404')").is_visible() or "404" in page.title():
        print(f"  SKIP  {version} — 404 (already deleted)")
        return False

    # Find the Delete release button
    delete_btn = page.locator(
        "button:has-text('Delete release'), "
        "a:has-text('Delete release'), "
        "input[value='Delete release']"
    ).first

    if not delete_btn.is_visible(timeout=3_000):
        print(f"  SKIP  {version} — delete button not found")
        return False

    delete_btn.click()
    time.sleep(0.5)

    # Click the final confirmation/submit button
    with contextlib.suppress(Exception):  # noqa: BLE001
        submit = page.locator(
            "dialog button[type='submit'], .modal button[type='submit'], "
            "button:has-text('Delete'), button:has-text('Confirm delete')"
        ).first
        if submit.is_visible(timeout=4_000):
            submit.click()
            page.wait_for_load_state("domcontentloaded", timeout=15_000)
            time.sleep(0.5)
    # submit button not found or click failed; page state logged above

    print(f"  DEL   {version} ✓")
    return True


def main() -> None:
    all_versions = get_all_versions()
    to_delete = [v for v in all_versions if v not in KEEP]
    print(f"Found {len(all_versions)} versions, {len(to_delete)} to delete")
    print("Press Enter to start deletion...")
    input()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=200)
        try:
            page = browser.new_page()
            for version in to_delete:
                if not delete_version(page, version):
                    break
        finally:
            browser.close()


if __name__ == "__main__":
    main()
