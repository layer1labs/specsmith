"""agentic-cli-tool — benchmark demo project.

A Click-based file-processing CLI.

Current commands:
  process   — read files, apply transforms, write JSON output
  validate  — check a file against a schema

MISSING(T5): an `export` command that converts process output to CSV.
"""

from __future__ import annotations

import click

from cli.commands.process import process
from cli.commands.validate import validate

# T5: register `from cli.commands.export import export` here


@click.group()
@click.version_option("0.1.0")
def cli() -> None:
    """File processing CLI for benchmark testing."""


cli.add_command(process)
cli.add_command(validate)
# T5: cli.add_command(export)


if __name__ == "__main__":
    cli()
