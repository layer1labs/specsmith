from specsmith.mcp_server import _HANDLERS, _TOOLS


def _args() -> dict:
    return {
        "telemetry": {
            "context_limit": 10_000,
            "current_input": 7000,
            "output_reserve": 500,
            "safety_reserve": 500,
        },
        "task": {
            "task_class": "high",
            "expected_reasoning": 1000,
            "expected_reads": 1000,
            "expected_tool_output": 1000,
            "expected_verification": 1000,
        },
        "work_item_id": "WI-ZOO",
        "invariants": {
            "objective": "finish",
            "user_constraints": ["exact"],
            "decisions": ["governed"],
            "risks": ["overflow"],
            "next_action": "handoff",
        },
        "records": [
            {
                "record_id": "R1",
                "claim": "exact constraint",
                "token_cost": 20,
                "relevance": 1.0,
                "pinned": True,
                "provenance": "user",
            }
        ],
    }


def test_mcp_exposes_exact_specsmith_context_transition() -> None:
    names = {tool["name"] for tool in _TOOLS}
    assert {"governance_context_transition", "governance_context_verify"} <= names
    result = _HANDLERS["governance_context_transition"](_args())
    assert result["directive"]["native_summary_allowed"] is False
    assert result["packet"]["digest"] == result["directive"]["packet_digest"]
    assert result["packet"]["invariants"]["user_constraints"] == ["exact"]


def test_mcp_packet_verification_blocks_tampering() -> None:
    result = _HANDLERS["governance_context_transition"](_args())
    expected = result["packet"]["digest"]
    valid = _HANDLERS["governance_context_verify"](
        {"expected_digest": expected, "applied_digest": expected}
    )
    tampered = _HANDLERS["governance_context_verify"](
        {"expected_digest": expected, "applied_digest": "bad"}
    )
    assert valid == {"verified": True, "resume_allowed": True, "status": "healthy"}
    assert tampered["status"] == "blocked_degraded"
    assert tampered["resume_allowed"] is False


def test_unmanaged_opt_out_is_explicit() -> None:
    args = _args()
    args["governed"] = False
    result = _HANDLERS["governance_context_transition"](args)
    assert result["directive"]["action"] == "unmanaged"
    assert result["directive"]["native_summary_allowed"] is True
