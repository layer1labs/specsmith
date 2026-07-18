from specsmith.agent.todo_renderer import TodoItem, render_todo_list
from specsmith.agent.tools import build_tool_registry, update_todo_list


def test_todo_renderer_formats_status_nesting_titles_and_pause() -> None:
    output = render_todo_list(
        (
            TodoItem(
                "A very long top-level title " * 5,
                "in_progress",
                (TodoItem("done", "completed"), TodoItem("pending", children=(TodoItem("deep"),))),
            ),
        ),
        paused=True,
        pause_reason="Waiting for verification.",
    )
    assert "### 🔄" in output and "…" in output
    assert "- ✅ done" in output
    assert "  - ⏳ deep" in output
    assert "<details>" in output and "Waiting for verification." in output


def test_agent_tool_uses_renderer_in_every_mode() -> None:
    output = update_todo_list(
        [{"title": "parent", "status": "completed", "children": [{"title": "child"}]}]
    )
    assert "### ✅ parent" in output and "- ⏳ child" in output
    assert "update_todo_list" in {tool.name for tool in build_tool_registry()}
