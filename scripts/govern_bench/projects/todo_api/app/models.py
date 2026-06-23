"""Pydantic models for the Todo API.

GAP(T3): TodoCreate has no title validation. A blank title or a 10,000-char
title will both be accepted. T3 adds Pydantic field validators to fix this.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class TodoCreate(BaseModel):
    """Input model for creating a todo.

    GAP: title accepts any string — no length limit, no empty-string check.
    T3 task: add Pydantic validators here.
    """

    title: str
    description: Optional[str] = None
    priority: int = 1  # 1=low, 2=medium, 3=high


class TodoUpdate(BaseModel):
    """Partial update model — all fields optional."""

    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[int] = None


class TodoItem(BaseModel):
    """Full todo item returned by the API."""

    id: int
    title: str
    description: Optional[str] = None
    completed: bool = False
    priority: int = 1
