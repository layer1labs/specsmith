from __future__ import annotations

import app.main as main
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_store() -> None:
    main._TODO_STORE.clear()
    main._NEXT_ID = 1


def test_empty_stats_route_is_reachable() -> None:
    response = TestClient(main.app).get("/todos/stats")
    assert response.status_code == 200
    assert response.json() == {
        "total": 0,
        "completed": 0,
        "pending": 0,
        "by_priority": {"1": 0, "2": 0, "3": 0},
    }


def test_stats_counts_mixed_todos() -> None:
    client = TestClient(main.app)
    created = [
        client.post("/todos", json={"title": "low", "priority": 1}).json(),
        client.post("/todos", json={"title": "high-a", "priority": 3}).json(),
        client.post("/todos", json={"title": "high-b", "priority": 3}).json(),
    ]
    client.patch(f"/todos/{created[1]['id']}", json={"completed": True})

    response = client.get("/todos/stats")
    assert response.status_code == 200
    assert response.json() == {
        "total": 3,
        "completed": 1,
        "pending": 2,
        "by_priority": {"1": 1, "2": 0, "3": 2},
    }
