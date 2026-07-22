"""Starter incident API with deliberate long-horizon gaps."""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="Incident Command Console")


@app.get("/health")
def health() -> dict[str, str]:
    """Return a stable process health contract."""
    return {"status": "ok"}


# T28 intentionally starts without the incident model, store, or product routes.
