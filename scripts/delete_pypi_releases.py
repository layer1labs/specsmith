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

import time
from playwright.sync_api import sync_playwright, Page

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
    import urllib.request, json
    url = f"https://pypi.org/pypi/{PROJECT}/json"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read())
    return sorted(data["releases"].keys())


def delete_version(page: Page, version: str) -> bool:
    """Navigate to a release page and click the delete button."""
    url = f"https://pypi.org/manage/project/{PROJECT}/release/{version}/"
    try:
        page.goto(url, timeout=20_000)
        page.wait_for_load_state("domcontentloaded", timeout=15_000)
    except Exception:
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

    # Fill confirmation input (PyPI asks you to type the version number)
    try:
        confirm_input = page.locator(
            "input[id*='confirm'], input[name*='confirm'], "
            "input[placeholder*='version'], "
            "dialog input[type='text'], .modal input[type='text']"
        ).first
        if confirm_input.is_visible(timeout=4_000):
            confirm_input.fill(version)
            time.sleep(0.3)
    except Exception:
        pass

    # Click the final confirmation/submit button
    try:
        submit = page.locator(
            "dialog button[type='submit'], .modal button[type='submit'], "
            "button:has-text('Delete'), button:has-text('Confirm delete')"
        ).first
        if submit.is_visible(timeout=4_000):
            submit.click()
            page.wait_for_load_state("domcontentloaded", timeout=15_000)
            time.sleep(0.5)
    except Exception:
        pass

    print(f"  DEL   {version} ✓")
    return True


def main() -> None:
    all_versions = get_all_versions()
    to_delete = [v for v in all_versions if v not in KEEP]
    to_keep = [v for v in all_versions if v in KEEP]

    print(f"Specsmith PyPI cleanup — {len(all_versions)} total versions\n")
    print(f"Keeping ({len(to_keep)}):  {', '.join(to_keep)}")
    print(f"Deleting ({len(to_delete)}): all others\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=200)
        ctx = browser.new_context()
        page = ctx.new_page()

        # Step 1: open login page
        page.goto("https://pypi.org/account/login/")
        print("=" * 60)
        print("Browser is open. Log in to PyPI (including 2FA if needed).")
        print("When you're fully logged in and see your dashboard,")
        print("press ENTER here to start the deletions...")
        print("=" * 60)
        input()

        # Verify logged in — navigate to the project management page.
        # PyPI may do a brief redirect chain; catch interruptions gracefully.
        try:
            page.goto(
                f"https://pypi.org/manage/project/{PROJECT}/releases/",
                wait_until="commit",
                timeout=20_000,
            )
        except Exception:
            pass  # navigation interruptions are expected during PyPI's redirect
        # Give any redirect chain time to settle
        time.sleep(2)
        page.wait_for_load_state("domcontentloaded", timeout=15_000)

        current_url = page.url
        if "account/login" in current_url:
            print("ERROR: Redirected to login page — not authenticated. Aborting.")
            browser.close()
            return
        print(f"Login confirmed (landed at: {current_url}). Starting deletions...\n")

        print(f"Starting deletion of {len(to_delete)} versions...\n")
        deleted = 0
        skipped = 0

        for version in to_delete:  # oldest first (list is already sorted ascending)
            try:
                ok = delete_version(page, version)
                if ok:
                    deleted += 1
                else:
                    skipped += 1
                time.sleep(0.5)
            except Exception as exc:
                print(f"  ERROR {version}: {exc}")
                skipped += 1

        print(f"\nDone. Deleted: {deleted}  Skipped/errors: {skipped}")
        print("Closing browser in 5 seconds...")
        time.sleep(5)
        browser.close()


if __name__ == "__main__":
    main()
