"""Mode-independent Markdown renderer for readable agent todo trees."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TodoItem:
    title: str
    status: str = "pending"
    children: tuple[TodoItem, ...] = field(default_factory=tuple)


_STATUS = {"completed": "✅", "in_progress": "🔄", "pending": "⏳"}


def _bounded(title: str, limit: int = 60) -> str:
    clean = " ".join(title.split())
    return clean if len(clean) <= limit else clean[: limit - 1].rstrip() + "…"


def render_todo_list(
    items: tuple[TodoItem, ...], *, paused: bool = False, pause_reason: str = ""
) -> str:
    lines = ["## Updated the to-do list", ""]

    def child_lines(item: TodoItem, depth: int) -> None:
        symbol = _STATUS.get(item.status, "⏳")
        lines.append(f"{'  ' * depth}- {symbol} {_bounded(item.title)}")
        for child in item.children:
            child_lines(child, depth + 1)

    for item in items:
        symbol = _STATUS.get(item.status, "⏳")
        lines.extend([f"### {symbol} {_bounded(item.title)}", ""])
        for child in item.children:
            child_lines(child, 0)
        if item.children:
            lines.append("")
    if paused:
        lines.extend(
            [
                "<details>",
                "<summary>⏸ Paused</summary>",
                "",
                pause_reason or "Waiting for a governed resume condition.",
                "",
                "</details>",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"
