"""Sync .specsmith/requirements.json and .specsmith/testcases.json from
human-readable governance markdown.

Implements REQ-003 (Machine State Must Reflect Governance State).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse_requirements(text: str) -> list[dict]:
    blocks = re.split(r"\n## \d+\. ", "\n" + text)
    out: list[dict] = []
    for block in blocks[1:]:
        m_id = re.search(r"-\s*\*\*ID:\*\*\s*(\S+)", block)
        m_title = re.search(r"-\s*\*\*Title:\*\*\s*([^\n]+)", block)
        m_desc = re.search(r"-\s*\*\*Description:\*\*\s*([^\n]+)", block)
        m_source = re.search(r"-\s*\*\*Source:\*\*\s*([^\n]+)", block)
        m_status = re.search(r"-\s*\*\*Status:\*\*\s*([^\n]+)", block)
        if not (m_id and m_title and m_desc):
            continue
        out.append(
            {
                "id": m_id.group(1).strip(),
                "title": m_title.group(1).strip(),
                "description": m_desc.group(1).strip(),
                "source": (m_source.group(1).strip() if m_source else "ARCHITECTURE.md"),
                "status": (m_status.group(1).strip() if m_status else "defined"),
            }
        )
    return out


def parse_tests(text: str) -> list[dict]:
    blocks = re.split(r"\n## TEST-", "\n" + text)
    out: list[dict] = []
    for block in blocks[1:]:
        block = "TEST-" + block
        m_id = re.search(r"-\s*\*\*ID:\*\*\s*(\S+)", block)
        m_title = re.search(r"-\s*\*\*Title:\*\*\s*([^\n]+)", block)
        m_desc = re.search(r"-\s*\*\*Description:\*\*\s*([^\n]+)", block)
        m_req = re.search(r"-\s*\*\*Requirement ID:\*\*\s*(\S+)", block)
        m_type = re.search(r"-\s*\*\*Type:\*\*\s*(\S+)", block)
        m_method = re.search(r"-\s*\*\*Verification Method:\*\*\s*([^\n]+)", block)
        if not (m_id and m_title and m_desc and m_req):
            continue
        out.append(
            {
                "id": m_id.group(1).strip(),
                "title": m_title.group(1).strip(),
                "description": m_desc.group(1).strip(),
                "requirement_id": m_req.group(1).strip(),
                "type": (m_type.group(1).strip() if m_type else "unit"),
                "verification_method": (m_method.group(1).strip() if m_method else "evaluator"),
                "input": {},
                "expected_behavior": {},
                "confidence": 1.0,
            }
        )
    return out


def main() -> None:
    reqs_md = (ROOT / "REQUIREMENTS.md").read_text(encoding="utf-8")
    tests_md = (ROOT / "TESTS.md").read_text(encoding="utf-8")

    reqs = parse_requirements(reqs_md)
    tests = parse_tests(tests_md)

    state_dir = ROOT / ".specsmith"
    state_dir.mkdir(exist_ok=True)

    (state_dir / "requirements.json").write_text(
        json.dumps(reqs, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (state_dir / "testcases.json").write_text(
        json.dumps(tests, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Synced {len(reqs)} requirements and {len(tests)} test cases.")


if __name__ == "__main__":
    main()
