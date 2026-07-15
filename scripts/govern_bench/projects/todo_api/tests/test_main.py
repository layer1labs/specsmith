"""Tests for the Todo API.

These are the STARTING tests — present before any benchmark task runs.
Some tests intentionally fail due to the deliberate bugs baked into the project:

  test_create_todo_isolation — FAILS because of the T2 mutable default argument bug.
    Run `pytest` to see: AssertionError: Expected 1 todo, got N

All other tests pass on the clean starting state.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_store():
    """Reset the module-level store before each test.

    NOTE: This fixture resets _TODO_STORE, but does NOT reset the mutable
    default argument in create_todo(). The T2 bug persists across tests
    because the inner `db=[]` list is a different object from _TODO_STORE.
    """
    import app.main as m

    m._TODO_STORE.clear()
    m._NEXT_ID = 1
    yield
    m._TODO_STORE.clear()
    m._NEXT_ID = 1


# ---------------------------------------------------------------------------
# Basic CRUD tests (all pass on clean state)
# ---------------------------------------------------------------------------


def test_list_todos_empty():
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == []


def test_create_todo():
    response = client.post("/todos", json={"title": "Buy milk"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Buy milk"
    assert data["id"] is not None
    assert data["completed"] is False


def test_get_todo():
    create_resp = client.post("/todos", json={"title": "Read book"})
    todo_id = create_resp.json()["id"]

    get_resp = client.get(f"/todos/{todo_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Read book"


def test_get_todo_not_found():
    response = client.get("/todos/99999")
    assert response.status_code == 404


def test_update_todo():
    create_resp = client.post("/todos", json={"title": "Walk dog"})
    todo_id = create_resp.json()["id"]

    update_resp = client.patch(f"/todos/{todo_id}", json={"completed": True})
    assert update_resp.status_code == 200
    assert update_resp.json()["completed"] is True


def test_delete_todo():
    create_resp = client.post("/todos", json={"title": "Delete me"})
    todo_id = create_resp.json()["id"]

    del_resp = client.delete(f"/todos/{todo_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/todos/{todo_id}")
    assert get_resp.status_code == 404


def test_list_todos_returns_all():
    client.post("/todos", json={"title": "First"})
    client.post("/todos", json={"title": "Second"})
    client.post("/todos", json={"title": "Third"})

    response = client.get("/todos")
    assert response.status_code == 200
    assert len(response.json()) == 3


# ---------------------------------------------------------------------------
# T2 FAILING TEST — mutable default argument bug
# This test will FAIL until T2 is implemented correctly.
# ---------------------------------------------------------------------------


def test_create_todo_isolation():
    """Verify that creating one todo results in exactly one todo in the store.

    This test FAILS on the starting codebase because create_todo() uses a
    mutable default argument `db: list = []` that persists across test runs.
    The fix is to use the module-level _TODO_STORE directly (not a default arg).
    """
    response = client.post("/todos", json={"title": "Isolation test"})
    assert response.status_code == 201

    list_resp = client.get("/todos")
    todos = list_resp.json()
    assert len(todos) == 1, f"Expected 1 todo, got {len(todos)}"
