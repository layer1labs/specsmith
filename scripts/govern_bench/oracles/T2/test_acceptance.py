from __future__ import annotations

import inspect

import app.main as main
from fastapi.testclient import TestClient


def test_create_todo_has_no_mutable_default() -> None:
    parameter = inspect.signature(main.create_todo).parameters.get("db")
    assert parameter is None or not isinstance(parameter.default, list)
    assert ".clear(" not in inspect.getsource(main.create_todo)


def test_public_api_remains_isolated_and_compatible() -> None:
    main._TODO_STORE.clear()
    main._NEXT_ID = 1
    client = TestClient(main.app)

    first = client.post("/todos", json={"title": "first"})
    assert first.status_code == 201
    assert client.get("/todos").json() == [first.json()]

    main._TODO_STORE.clear()
    main._NEXT_ID = 1
    second = client.post("/todos", json={"title": "second"})
    assert second.status_code == 201
    assert client.get("/todos").json() == [second.json()]
