"""process command — reads a JSON/text file and writes processed output."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", default=None, help="Output file path (default: stdout)")
@click.option("--uppercase", is_flag=True, help="Uppercase all string values")
def process(input_file: str, output: str | None, uppercase: bool) -> None:
    """Process INPUT_FILE and write JSON output.

    Reads the input file, applies optional transforms, and outputs JSON.
    """
    path = Path(input_file)
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        click.echo(f"Error: Invalid JSON in {input_file}: {exc}", err=True)
        sys.exit(1)

    if uppercase:
        data = _apply_uppercase(data)

    result = json.dumps(data, indent=2)

    if output:
        Path(output).write_text(result, encoding="utf-8")
        click.echo(f"Written to {output}")
    else:
        click.echo(result)


def _apply_uppercase(obj: object) -> object:
    """Recursively uppercase all string values in a JSON-like structure."""
    if isinstance(obj, str):
        return obj.upper()
    if isinstance(obj, list):
        return [_apply_uppercase(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _apply_uppercase(v) for k, v in obj.items()}
    return obj
