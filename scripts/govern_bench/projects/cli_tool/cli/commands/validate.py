"""validate command — checks a JSON file against a basic schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

REQUIRED_FIELDS = ["id", "title"]


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--strict", is_flag=True, help="Fail on any extra fields")
def validate(input_file: str, strict: bool) -> None:
    """Validate INPUT_FILE against the expected schema.

    Checks that each record has the required fields: id, title.
    """
    path = Path(input_file)
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        click.echo(f"Error: Invalid JSON — {exc}", err=True)
        sys.exit(1)

    if not isinstance(data, list):
        click.echo("Error: Expected a JSON array at the top level.", err=True)
        sys.exit(1)

    errors = []
    for i, record in enumerate(data):
        for field in REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"Record {i}: missing required field '{field}'")
        if strict:
            extra = set(record) - set(REQUIRED_FIELDS)
            if extra:
                errors.append(f"Record {i}: unexpected fields {sorted(extra)}")

    if errors:
        for err in errors:
            click.echo(f"FAIL: {err}", err=True)
        sys.exit(1)

    click.echo(f"OK: {len(data)} records validated successfully.")
