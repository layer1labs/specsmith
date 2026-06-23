from __future__ import annotations

from typing import Any


def verify(context: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "plugin": "example-verifier", "context_keys": sorted(context.keys())}
