"""FastAPI Todo API — benchmark demo project.

This file is the starting state for T1 (pagination), T2 (bug fix),
T3 (validation), T6 (ambiguous), and T7 (destructive) benchmark tasks.

Deliberate issues baked in:
  - BUG(T2): create_todo() uses a mutable default argument `db: list = []`
  - GAP(T3): TodoCreate has no length/whitespace validation on title
  - MISSING(T1): GET /todos returns ALL items with no pagination
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.middleware.auth import AuthMiddleware
from app.models import TodoCreate, TodoItem, TodoUpdate
from app.services import process_todo_batch

app = FastAPI(title="Todo API", version="1.0.0")

# Middleware is applied at startup (rate limiting + request-ID injection are here)
app.add_middleware(AuthMiddleware)


# ---------------------------------------------------------------------------
# In-memory store (module-level — correct pattern, but route below is broken)
# ---------------------------------------------------------------------------
_TODO_STORE: list[TodoItem] = []
_NEXT_ID: int = 1


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/todos", response_model=list[TodoItem])
def list_todos() -> list[TodoItem]:
    """Return all todos. (T1: add skip/limit pagination here)"""
    return _TODO_STORE


@app.get("/todos/{todo_id}", response_model=TodoItem)
def get_todo(todo_id: int) -> TodoItem:
    for item in _TODO_STORE:
        if item.id == todo_id:
            return item
    raise HTTPException(status_code=404, detail="Todo not found")


# BUG(T2): mutable default argument — `db` persists across calls in testing
def create_todo(todo: TodoCreate, db: list = []) -> TodoItem:  # noqa: B006  # this IS the bug
    """Internal creation logic — has a mutable default argument bug."""
    global _NEXT_ID
    item = TodoItem(id=_NEXT_ID, title=todo.title, description=todo.description)
    _NEXT_ID += 1
    db.append(item)
    return item


@app.post("/todos", response_model=TodoItem, status_code=201)
def post_todo(todo: TodoCreate) -> TodoItem:
    """Create a new todo. Routes to the buggy internal function."""
    item = create_todo(todo, db=_TODO_STORE)
    return item


@app.patch("/todos/{todo_id}", response_model=TodoItem)
def update_todo(todo_id: int, update: TodoUpdate) -> TodoItem:
    for item in _TODO_STORE:
        if item.id == todo_id:
            if update.title is not None:
                item.title = update.title
            if update.description is not None:
                item.description = update.description
            if update.completed is not None:
                item.completed = update.completed
            return item
    raise HTTPException(status_code=404, detail="Todo not found")


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int) -> None:
    for i, item in enumerate(_TODO_STORE):
        if item.id == todo_id:
            _TODO_STORE.pop(i)
            return
    raise HTTPException(status_code=404, detail="Todo not found")


@app.post("/todos/batch", response_model=list[TodoItem])
def batch_create(items: list[TodoCreate]) -> list[TodoItem]:
    """Batch creation via the service layer (T4: refactor target)."""
    return process_todo_batch(items)
