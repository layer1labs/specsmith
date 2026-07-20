from __future__ import annotations

from specsmith.sync import parse_requirements_md, parse_tests_md


def test_parsers_emit_version_field() -> None:
    reqs = parse_requirements_md("## REQ-001: hello\n- **Status**: defined\n")
    tests = parse_tests_md("## TEST-001\n- **Requirement ID**: REQ-001\n")
    assert reqs and reqs[0]["version"] == 1
    assert tests and tests[0]["version"] == 1
