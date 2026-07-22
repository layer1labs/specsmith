from __future__ import annotations

import importlib
import json
import shutil
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent


def _allows_null(schema: dict) -> bool:
    value_type = schema.get("type")
    if value_type == "null" or (isinstance(value_type, list) and "null" in value_type):
        return True
    if schema.get("const", object()) is None or None in schema.get("enum", []):
        return True
    return any(
        _allows_null(option)
        for keyword in ("anyOf", "oneOf")
        for option in schema.get(keyword, [])
        if isinstance(option, dict)
    )


def _has_empty_state(app: str) -> bool:
    app = app.casefold()
    return "empty" in app or (
        "incidents.length" in app
        and "=== 0" in app
        and ("no incident" in app or "no matching incident" in app)
    )


def test_shared_schema_is_complete_and_strict() -> None:
    schema = json.loads((ROOT / "contracts" / "incident.schema.json").read_text(encoding="utf-8"))
    fields = {
        "id",
        "title",
        "service",
        "severity",
        "status",
        "created_at",
        "acknowledged_at",
    }
    assert fields <= set(schema["properties"])
    assert fields <= set(schema["required"])
    assert schema.get("additionalProperties") is False
    assert set(schema["properties"]["severity"]["enum"]) == {
        "low",
        "medium",
        "high",
        "critical",
    }
    assert set(schema["properties"]["status"]["enum"]) == {"open", "acknowledged"}
    acknowledged = schema["properties"]["acknowledged_at"]
    assert _allows_null(acknowledged)


def test_python_api_create_filter_and_acknowledge_flow() -> None:
    import backend.main as backend

    backend = importlib.reload(backend)
    client = TestClient(backend.app)
    critical = client.post(
        "/api/incidents",
        json={"title": "Database unavailable", "service": "billing", "severity": "critical"},
    )
    assert critical.status_code == 201, critical.text
    created = critical.json()
    assert created["status"] == "open"
    assert created["service"] == "billing"
    assert created["severity"] == "critical"
    assert created["acknowledged_at"] is None
    assert created["id"] and created["created_at"]

    second = client.post(
        "/api/incidents",
        json={"title": "Slow queue", "service": "worker", "severity": "medium"},
    )
    assert second.status_code == 201

    filtered = client.get("/api/incidents?severity=critical&status=open")
    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()] == [created["id"]]

    acknowledged = client.patch(f"/api/incidents/{created['id']}/ack")
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "acknowledged"
    assert acknowledged.json()["acknowledged_at"]
    assert client.get("/api/incidents?status=open").json()[0]["service"] == "worker"
    assert client.patch("/api/incidents/not-found/ack").status_code == 404
    assert (
        client.post(
            "/api/incidents",
            json={"title": "bad", "service": "billing", "severity": "urgent"},
        ).status_code
        == 422
    )


def test_go_normalizer_matches_contract_and_rejects_bad_alerts() -> None:
    worker = ROOT / "worker"
    source = (worker / "main.go").read_text(encoding="utf-8")
    for json_name in (
        "id",
        "title",
        "service",
        "severity",
        "status",
        "created_at",
        "acknowledged_at",
    ):
        assert f'json:"{json_name}"' in source
    assert "func NormalizeAlert(raw []byte) (Incident, error)" in source

    go = shutil.which("go")
    if go is None:
        return
    oracle_test = worker / "t28_oracle_test.go"
    oracle_test.write_text(
        """package main

import "testing"

func TestT28NormalizeAlert(t *testing.T) {
    got, err := NormalizeAlert([]byte(`{"title":"CPU hot","service":"edge","severity":"high"}`))
    if err != nil { t.Fatalf("valid alert rejected: %v", err) }
    if got.Title != "CPU hot" || got.Service != "edge" || got.Severity != "high" {
        t.Fatalf("wrong mapping: %#v", got)
    }
    if got.Status != "open" || got.ID == "" || got.CreatedAt == "" {
        t.Fatalf("missing defaults: %#v", got)
    }
    badSeverity := []byte(`{"title":"bad","service":"edge","severity":"urgent"}`)
    if _, err := NormalizeAlert(badSeverity); err == nil {
        t.Fatal("invalid severity accepted")
    }
    missingTitle := []byte(`{"title":"","service":"edge","severity":"low"}`)
    if _, err := NormalizeAlert(missingTitle); err == nil {
        t.Fatal("missing title accepted")
    }
}
""",
        encoding="utf-8",
    )
    try:
        result = subprocess.run(
            [go, "test", "./..."],
            cwd=worker,
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    finally:
        oracle_test.unlink(missing_ok=True)


def test_ui_has_real_accessible_flow_and_playwright_journey() -> None:
    app = (ROOT / "ui" / "src" / "App.tsx").read_text(encoding="utf-8").casefold()
    api = (ROOT / "ui" / "src" / "api.ts").read_text(encoding="utf-8").casefold()
    browser = (
        (ROOT / "ui" / "tests" / "incident-console.spec.ts").read_text(encoding="utf-8").casefold()
    )

    for term in ("loading", "error", "severity", "status", "acknowledge"):
        assert term in app
    assert _has_empty_state(app)
    assert "usestate" in app and "useeffect" in app
    assert "<label" in app or "aria-label" in app
    assert 'role="alert"' in app or "role={'alert'}" in app or 'role="status"' in app
    assert "/api/incidents" in api
    assert "severity" in api and "status" in api
    assert "encodeuricomponent" in api or "urlsearchparams" in api
    assert "patch" in api and "/ack" in api

    assert "test.skip" not in browser
    assert "getbyrole" in browser
    for journey_step in ("incident", "filter", "acknowledge", "expect"):
        assert journey_step in browser


def test_architecture_and_public_tests_cover_boundaries() -> None:
    architecture = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8").casefold()
    public_tests = (ROOT / "tests" / "test_backend.py").read_text(encoding="utf-8").casefold()
    for term in ("python", "go", "react", "schema", "data flow"):
        assert term in architecture
    assert "in-memory" in architecture or "in memory" in architecture
    assert len(architecture.split()) >= 100
    assert "post(" in public_tests
    assert "/api/incidents" in public_tests
    assert "/ack" in public_tests
