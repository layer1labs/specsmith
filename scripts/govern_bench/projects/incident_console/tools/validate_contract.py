"""Visible deterministic checks for the T28 shared incident contract."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

INCIDENT_FIELDS = {
    "id",
    "title",
    "service",
    "severity",
    "status",
    "created_at",
    "acknowledged_at",
}


def _allows_null(node: dict[str, Any]) -> bool:
    type_value = node.get("type")
    if type_value == "null":
        return True
    if isinstance(type_value, list) and "null" in type_value:
        return True
    return any(
        isinstance(option, dict) and _allows_null(option)
        for key in ("anyOf", "oneOf")
        for option in (node.get(key) or [])
    )


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    schema = json.loads((root / "contracts" / "incident.schema.json").read_text(encoding="utf-8"))
    properties = set(schema.get("properties") or {})
    required = set(schema.get("required") or [])
    missing_properties = sorted(INCIDENT_FIELDS - properties)
    missing_required = sorted(INCIDENT_FIELDS - required)
    if missing_properties or missing_required:
        if missing_properties:
            print("Schema properties missing: " + ", ".join(missing_properties))
        if missing_required:
            print("Schema required list missing: " + ", ".join(missing_required))
        return 1
    if schema.get("additionalProperties") is not False:
        print("Schema must set additionalProperties to false")
        return 1
    severity = set(schema["properties"]["severity"].get("enum") or [])
    if severity != {"low", "medium", "high", "critical"}:
        print("Schema severity enum must be low, medium, high, critical")
        return 1
    status = set(schema["properties"]["status"].get("enum") or [])
    if status != {"open", "acknowledged"}:
        print("Schema status enum must be open, acknowledged")
        return 1
    if not _allows_null(schema["properties"]["acknowledged_at"]):
        print("Schema acknowledged_at must allow null")
        return 1
    worker = (root / "worker" / "main.go").read_text(encoding="utf-8")
    if re.search(r"(?m)^\s*package\s+main\s*$", worker) is None:
        print("worker/main.go must preserve the starter package main boundary")
        return 1
    print("Shared incident contract checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
