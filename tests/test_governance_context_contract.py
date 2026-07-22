from __future__ import annotations

import json
from pathlib import Path

from specsmith.agent.context_seed import build_context_seed
from specsmith.esdb import SqliteRecord, SqliteStore
from specsmith.governance_logic import run_preflight
from specsmith.session_store import save_session


def _write_governance_state(root: Path, count: int = 1) -> None:
    state = root / ".specsmith"
    state.mkdir(parents=True)
    requirements = [
        {
            "id": f"REQ-{index:03d}",
            "title": f"Requirement {index}",
            "description": "Long prose is intentionally excluded. " * 100,
            "test_ids": [f"TEST-{index:03d}"],
        }
        for index in range(1, count + 1)
    ]
    tests = [
        {
            "id": f"TEST-{index:03d}",
            "title": f"Independent boundary test {index}",
            "requirement_id": f"REQ-{index:03d}",
            "verification_method": f"pytest tests/test_boundary_{index}.py",
            "expected_behavior": "Exercise the public write and read paths. " * 20,
        }
        for index in range(1, count + 1)
    ]
    (state / "requirements.json").write_text(json.dumps(requirements), encoding="utf-8")
    (state / "testcases.json").write_text(json.dumps(tests), encoding="utf-8")


def test_preflight_emits_bounded_independent_test_contract(tmp_path: Path) -> None:
    _write_governance_state(tmp_path)

    result = run_preflight("Implement REQ-001", tmp_path, predict_only=True)

    contract = result["context_contract"]
    assert contract["requirements"] == [{"id": "REQ-001", "title": "Requirement 1"}]
    assert contract["independent_tests"][0]["verification"] == ("pytest tests/test_boundary_1.py")
    assert "without editing them" in contract["instruction"]
    assert len(json.dumps(contract, ensure_ascii=False)) <= 1_200
    assert "Long prose" not in json.dumps(contract)


def test_context_contract_keeps_trace_ids_under_many_matches(tmp_path: Path) -> None:
    _write_governance_state(tmp_path, count=12)
    utterance = "Implement " + " ".join(f"REQ-{index:03d}" for index in range(1, 13))

    contract = run_preflight(utterance, tmp_path, predict_only=True)["context_contract"]

    assert contract["requirements"][0]["id"] == "REQ-001"
    assert contract["independent_tests"][0]["id"] == "TEST-001"
    assert len(json.dumps(contract, ensure_ascii=False)) <= 1_200


def test_context_seed_prioritizes_active_evidence_and_caps_chat(tmp_path: Path) -> None:
    _write_governance_state(tmp_path)
    history = [{"role": "user", "content": f"turn-{index}-" + "x" * 100} for index in range(10)]
    save_session(tmp_path, {"session_id": "seed-test", "project_name": "demo"}, history)
    with SqliteStore(tmp_path) as store:
        store.upsert(
            SqliteRecord(
                id="WI-ACTIVE",
                kind="preflight_decision",
                status="active",
                label="repair the public write boundary",
                confidence=0.9,
                data={"decision": "accepted"},
                source_ids=["REQ-001", "TEST-001"],
            )
        )

    seed = build_context_seed(tmp_path, char_budget=1_200, max_history_turns=4)
    rendered = json.dumps(seed)

    assert "WI-ACTIVE" in rendered
    assert "turn-9" in rendered
    assert "turn-6" in rendered
    assert "turn-5" not in rendered
    assert sum(len(json.dumps(turn, ensure_ascii=False)) for turn in seed) <= 1_400
