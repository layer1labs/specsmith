"""Visible structural checks for the T28 React product boundary."""

from __future__ import annotations

from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    app = (root / "ui" / "src" / "App.tsx").read_text(encoding="utf-8")
    api = (root / "ui" / "src" / "api.ts").read_text(encoding="utf-8")
    browser_test = (root / "ui" / "tests" / "incident-console.spec.ts").read_text(encoding="utf-8")
    required_app_terms = ("loading", "error", "severity", "status", "acknowledge")
    missing = [term for term in required_app_terms if term not in app.casefold()]
    if missing:
        print(f"App.tsx missing UI states/actions: {', '.join(missing)}")
        return 1
    if "/api/incidents" not in api:
        print("api.ts does not call /api/incidents")
        return 1
    if "test.skip" in browser_test or "getbyrole" not in browser_test.casefold():
        print("Playwright flow is skipped or lacks accessible role selectors")
        return 1
    print("UI structure and browser-flow checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
