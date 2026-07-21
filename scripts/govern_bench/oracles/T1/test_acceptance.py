from __future__ import annotations

import app.main as main
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_store() -> None:
    main._TODO_STORE.clear()
    main._NEXT_ID = 1


def test_pagination_contract() -> None:
    client = TestClient(main.app)
    for index in range(25):
        response = client.post("/todos", json={"title": f"todo-{index}"})
        assert response.status_code == 201

    first_page = client.get("/todos")
    second_page = client.get("/todos", params={"skip": 20, "limit": 20})

    assert first_page.status_code == 200
    assert len(first_page.json()) == 20
    assert [item["title"] for item in second_page.json()] == [
        f"todo-{index}" for index in range(20, 25)
    ]


def test_pagination_bounds_and_response_shape() -> None:
    client = TestClient(main.app)
    created = client.post("/todos", json={"title": "shape"}).json()
    response = client.get("/todos", params={"skip": 0, "limit": 1})

    assert client.get("/todos", params={"limit": 101}).status_code == 422
    assert client.get("/todos", params={"skip": -1}).status_code == 422
    assert response.status_code == 200
    assert set(response.json()[0]) == set(created)
