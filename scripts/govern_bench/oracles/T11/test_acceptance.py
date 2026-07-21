from __future__ import annotations

import app.main as main
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_store() -> None:
    main._TODO_STORE.clear()
    main._NEXT_ID = 1


def test_tags_create_patch_and_preserve() -> None:
    client = TestClient(main.app)
    plain = client.post("/todos", json={"title": "plain"})
    tagged = client.post(
        "/todos",
        json={"title": "tagged", "tags": ["work", "urgent"]},
    )

    assert plain.status_code == 201
    assert plain.json()["tags"] == []
    assert tagged.json()["tags"] == ["work", "urgent"]

    todo_id = tagged.json()["id"]
    replaced = client.patch(f"/todos/{todo_id}", json={"tags": ["done"]})
    preserved = client.patch(f"/todos/{todo_id}", json={"title": "renamed"})
    assert replaced.json()["tags"] == ["done"]
    assert preserved.json()["tags"] == ["done"]


def test_exact_tag_filter_and_empty_filter() -> None:
    client = TestClient(main.app)
    client.post("/todos", json={"title": "a", "tags": ["work"]})
    client.post("/todos", json={"title": "b", "tags": ["home"]})

    assert [item["title"] for item in client.get("/todos?tag=work").json()] == ["a"]
    assert len(client.get("/todos?tag=").json()) == 2
    assert len(client.get("/todos").json()) == 2
