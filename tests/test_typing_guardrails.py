from __future__ import annotations

from pathlib import Path

TYPE_IGNORE_BASELINE = 69


def test_type_ignore_count_does_not_increase() -> None:
    root = Path(__file__).resolve().parents[1] / "src" / "specsmith"
    count = 0
    for py in root.rglob("*.py"):
        count += py.read_text(encoding="utf-8").count("# type: ignore")
    assert count <= TYPE_IGNORE_BASELINE, (
        f"Found {count} '# type: ignore' comments; baseline is {TYPE_IGNORE_BASELINE}. "
        "Reduce new ignores or update roadmap before raising the baseline."
    )
