"""select_models.py — turn models.yml into a filtered GitHub Actions matrix.

Reads the model registry (models.yml) and prints a JSON object suitable for a
GitHub Actions matrix:

    {"include": [{"label": ..., "provider": ..., "model": ..., "group": ...,
                  "tier": ...}, ...]}

Filters (each a comma-separated allowlist; omit to keep everything):
    --groups      e.g. open  |  open,openai
    --providers   e.g. huggingface
    --tiers       e.g. open-small,open-xl
    --models      match by label OR exact model id

Usage:
    # Open models only (default group used by bench.yml):
    python scripts/govern_bench/select_models.py --groups open

    # Smallest vs largest open models:
    python scripts/govern_bench/select_models.py --tiers open-small,open-xl

Exits non-zero when no model matches the filters, so a misconfigured run fails
loudly instead of dispatching an empty matrix.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import yaml

_DEFAULT_REGISTRY = Path(__file__).with_name("models.yml")
_REQUIRED_FIELDS = ("label", "provider", "model", "group", "tier")


def _csv_set(value: str | None) -> set[str] | None:
    """Parse a comma-separated allowlist into a set, or None when unset."""
    if not value:
        return None
    return {item.strip() for item in value.split(",") if item.strip()}


def load_registry(path: str | os.PathLike[str]) -> list[dict]:
    """Load and validate the model registry YAML."""
    # os.path.realpath is the CodeQL-recognised path sanitizer.
    safe_path = os.path.realpath(str(path))
    raw = yaml.safe_load(Path(safe_path).read_text(encoding="utf-8")) or {}
    models = raw.get("models", [])
    if not isinstance(models, list) or not models:
        raise ValueError(f"No 'models' list found in registry: {safe_path}")
    for entry in models:
        missing = [f for f in _REQUIRED_FIELDS if not entry.get(f)]
        if missing:
            raise ValueError(f"Registry entry {entry!r} missing fields: {missing}")
    return models


def select(
    models: list[dict],
    groups: set[str] | None = None,
    providers: set[str] | None = None,
    tiers: set[str] | None = None,
    model_ids: set[str] | None = None,
) -> list[dict]:
    """Filter registry entries down to those matching every supplied allowlist."""
    selected = []
    for entry in models:
        if groups is not None and entry["group"] not in groups:
            continue
        if providers is not None and entry["provider"] not in providers:
            continue
        if tiers is not None and entry["tier"] not in tiers:
            continue
        if model_ids is not None and not (
            entry["label"] in model_ids or entry["model"] in model_ids
        ):
            continue
        selected.append({f: entry[f] for f in _REQUIRED_FIELDS})
    return selected


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--registry", default=str(_DEFAULT_REGISTRY))
    parser.add_argument("--groups", help="Comma-separated group allowlist")
    parser.add_argument("--providers", help="Comma-separated provider allowlist")
    parser.add_argument("--tiers", help="Comma-separated tier allowlist")
    parser.add_argument("--models", help="Comma-separated label/model-id allowlist")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Indent the JSON output (human-readable; not for GITHUB_OUTPUT)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        models = load_registry(args.registry)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"Error loading registry: {exc}", file=sys.stderr)
        return 1

    selected = select(
        models,
        groups=_csv_set(args.groups),
        providers=_csv_set(args.providers),
        tiers=_csv_set(args.tiers),
        model_ids=_csv_set(args.models),
    )

    if not selected:
        print(
            "Error: no models matched the given filters "
            f"(groups={args.groups!r} providers={args.providers!r} "
            f"tiers={args.tiers!r} models={args.models!r})",
            file=sys.stderr,
        )
        return 1

    matrix = {"include": selected}
    if args.pretty:
        print(json.dumps(matrix, indent=2))
    else:
        print(json.dumps(matrix, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
