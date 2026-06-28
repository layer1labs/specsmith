"""Structural validator for patent-draft benchmark tasks."""

from __future__ import annotations

import re
import sys
from pathlib import Path

CLAIM_PATTERN = re.compile(r"^\s*(\d+)\.\s+(.+)$")
DEPENDENCY_PATTERN = re.compile(r"\bclaim\s+(\d+)\b", re.IGNORECASE)
PLACEHOLDER_PATTERN = re.compile(r"\{[^}]+\}")


def parse_claims(claims_text: str) -> dict[int, str]:
    claims: dict[int, str] = {}
    current_number: int | None = None
    for raw_line in claims_text.splitlines():
        match = CLAIM_PATTERN.match(raw_line)
        if match:
            current_number = int(match.group(1))
            claims[current_number] = match.group(2).strip()
            continue
        if current_number is not None and raw_line.strip():
            claims[current_number] = f"{claims[current_number]} {raw_line.strip()}"
    return claims


def validate(claims_path: Path, spec_path: Path) -> list[str]:
    errors: list[str] = []
    claims_text = claims_path.read_text(encoding="utf-8")
    spec_text = spec_path.read_text(encoding="utf-8")

    if "# Claims" not in claims_text:
        errors.append("claims section heading '# Claims' is missing")

    claims = parse_claims(claims_text)
    if 1 not in claims:
        errors.append("independent claim 1 is missing")

    if PLACEHOLDER_PATTERN.search(claims_text) or PLACEHOLDER_PATTERN.search(spec_text):
        errors.append("placeholder token found; remove all '{...}' placeholders")

    claim_numbers = set(claims)
    for number, body in claims.items():
        refs = {int(ref) for ref in DEPENDENCY_PATTERN.findall(body)}
        for ref in refs:
            if ref not in claim_numbers:
                errors.append(f"claim {number} references missing claim {ref}")
            elif ref >= number:
                errors.append(f"claim {number} must depend on a lower-numbered claim")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_patent.py <claims.md> <specification.md>")
        return 2

    claims_path = Path(argv[0])
    spec_path = Path(argv[1])

    if not claims_path.exists():
        print(f"missing file: {claims_path}")
        return 2
    if not spec_path.exists():
        print(f"missing file: {spec_path}")
        return 2

    errors = validate(claims_path, spec_path)
    if errors:
        for item in errors:
            print(f"ERROR: {item}")
        return 1

    print("PASS: patent draft structural checks succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
