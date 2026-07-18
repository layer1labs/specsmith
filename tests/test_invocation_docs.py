from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_invocation_strategy_is_canonical_and_in_rtd_navigation() -> None:
    page = (ROOT / "docs/site/invocation-strategy.md").read_text(encoding="utf-8")
    nav = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for value in ("MCP", "Slash command", "Skill", "Direct CLI", "Windows", "Headless"):
        assert value in page
    assert "invocation-strategy.md" in nav
    assert "zoo-code-roo.md" in nav
    assert "zoo-code-roo" in readme
