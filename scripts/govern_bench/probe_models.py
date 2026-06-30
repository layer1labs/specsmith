"""probe_models.py — verify selected models have a live inference provider.

For every HuggingFace model in the selection, this queries the Inference
Providers router:

    GET https://router.huggingface.co/v1/models/<repo_id>   (Bearer HF_TOKEN)

and reports the live provider(s), context length, tool support, and per-token
pricing. It exits non-zero if any HuggingFace model has no live provider, so a
full benchmark run can be gated behind a fast, free availability check instead
of discovering dead models mid-run.

Model selection (first match wins):
    positional MODEL ids ...        explicit repo ids to probe
    --matrix PATH | -               read select_models.py JSON ({"include": [...]})
    --groups/--providers/--tiers    filter models.yml directly (see select_models)

Non-HuggingFace entries are listed but not probed (the router only covers HF).

Usage:
    python scripts/govern_bench/select_models.py --groups open \\
        | python scripts/govern_bench/probe_models.py --matrix -
    python scripts/govern_bench/probe_models.py --groups open
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Same-package helpers (script dir is added to sys.path below).
sys.path.insert(0, str(Path(__file__).parent))

from select_models import _csv_set, load_registry, select  # noqa: E402

_ROUTER_MODEL_URL = "https://router.huggingface.co/v1/models/"
_HF_PROVIDER = "huggingface"


def _split_route(model_id: str) -> tuple[str, str | None]:
    """Split an ``org/repo:provider`` id into (repo_id, pinned_provider|None).

    The HF router accepts a ``:<provider>`` suffix to pin one inference
    provider. The model-metadata endpoint is keyed by the bare repo id, so we
    strip the suffix for the lookup and validate the pin separately. Repo ids
    contain ``/`` and never ``:``; a provider slug never contains ``/``.
    """
    base, sep, route = model_id.rpartition(":")
    if sep and route and "/" not in route:
        return base, route
    return model_id, None


def _pinned_result(model_id: str, pinned: str, providers: list[dict]) -> dict:
    """Validate a pinned provider is offered, live, and tool-capable.

    A pinned provider that is missing, not live, or lacks tool support is a hard
    failure: the run-time tools/tool_choice params 422 with
    UNSUPPORTED_OPENAI_PARAMS, which is exactly what pinning is meant to avoid.
    """
    match = next(
        (p for p in providers if str(p.get("provider", "")).lower() == pinned.lower()),
        None,
    )
    if match is None:
        error: str | None = f"pinned provider '{pinned}' not offered"
    elif str(match.get("status", "")).lower() != "live":
        error = f"pinned provider '{pinned}' is not live"
    elif match.get("supports_tools") is not True:
        error = f"pinned provider '{pinned}' does not support tools"
    else:
        error = None
    return {
        "model": model_id,
        "ok": error is None,
        "n_providers": len(providers),
        "live": [match] if (error is None and match is not None) else [],
        "error": error,
    }


def _probe_one(model_id: str, token: str | None, timeout: float) -> dict:
    """Query the router for a single model id; return a structured result.

    When ``model_id`` pins a provider (``org/repo:provider``), that provider
    must exist, be live, AND advertise tool support. Unpinned ids pass as long
    as any provider is live.
    """
    repo_id, pinned = _split_route(model_id)
    url = _ROUTER_MODEL_URL + repo_id  # repo ids contain '/', kept as a path
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)  # fixed HTTPS router host
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"model": model_id, "ok": False, "error": f"HTTP {exc.code} {exc.reason}"}
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return {"model": model_id, "ok": False, "error": str(exc)}

    # The router wraps the model under a top-level "data" envelope:
    #   {"data": {"id": ..., "providers": [{"provider", "status", "pricing", ...}]}}
    # Fall back to a flat shape in case the API changes.
    body = payload.get("data", payload) if isinstance(payload, dict) else {}
    providers = body.get("providers") or []
    live = [p for p in providers if str(p.get("status", "")).lower() == "live"]

    if pinned is not None:
        return _pinned_result(model_id, pinned, providers)

    return {
        "model": model_id,
        "ok": bool(live),
        "n_providers": len(providers),
        "live": live,
        "error": None if live else "no live provider",
    }


def _money(value: object) -> str:
    """Render a per-1M price, rounding floats and passing through unknowns."""
    if isinstance(value, (int, float)):
        return f"${value:.4f}/1M"
    return "$?/1M"


def _fmt_provider(p: dict) -> str:
    name = p.get("provider") or p.get("name") or "?"
    ctx = p.get("context_length") or p.get("context_length_tokens") or "?"
    pricing = p.get("pricing") or {}
    tools = p.get("supports_tools")
    return (
        f"{name}: ctx={ctx} in={_money(pricing.get('input'))} "
        f"out={_money(pricing.get('output'))} tools={tools}"
    )


def _models_from_matrix(text: str) -> list[dict]:
    """Extract registry-shaped rows from a select_models.py matrix JSON blob."""
    data = json.loads(text)
    include = data.get("include", []) if isinstance(data, dict) else []
    return [row for row in include if isinstance(row, dict) and row.get("model")]


def _resolve_models(args: argparse.Namespace) -> list[dict]:
    """Resolve the model rows to probe from the first selection source given."""
    if args.models_positional:
        return [{"model": m, "provider": _HF_PROVIDER, "label": m} for m in args.models_positional]
    if args.matrix:
        text = sys.stdin.read() if args.matrix == "-" else _read_file(args.matrix)
        return _models_from_matrix(text)
    registry = load_registry(args.registry)
    return select(
        registry,
        groups=_csv_set(args.groups),
        providers=_csv_set(args.providers),
        tiers=_csv_set(args.tiers),
    )


def _read_file(path: str) -> str:
    safe_path = os.path.realpath(path)  # CodeQL-recognised path sanitizer
    return Path(safe_path).read_text(encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("models_positional", nargs="*", metavar="MODEL")
    parser.add_argument("--matrix", help="select_models JSON file, or '-' for stdin")
    parser.add_argument("--registry", default=None)
    parser.add_argument("--groups")
    parser.add_argument("--providers")
    parser.add_argument("--tiers")
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()
    if args.registry is None:
        args.registry = str(Path(__file__).with_name("models.yml"))
    return args


def main() -> int:
    args = _parse_args()
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("Warning: HF_TOKEN not set; probing unauthenticated may fail.", file=sys.stderr)

    try:
        rows = _resolve_models(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error resolving models: {exc}", file=sys.stderr)
        return 1

    hf_rows = [r for r in rows if r.get("provider", _HF_PROVIDER) == _HF_PROVIDER]
    other = [r for r in rows if r.get("provider") not in (None, _HF_PROVIDER)]
    for r in other:
        print(f"  skip (not huggingface): {r['provider']}/{r['model']}")

    if not hf_rows:
        print("No HuggingFace models to probe.", file=sys.stderr)
        return 0

    failures: list[str] = []
    print(f"Probing {len(hf_rows)} HuggingFace model(s) via the Inference Providers router:\n")
    for r in hf_rows:
        model_id = r["model"]
        result = _probe_one(model_id, token, args.timeout)
        if result["ok"]:
            print(f"✓ {model_id}  ({result['n_providers']} provider(s))")
            for p in result["live"]:
                print(f"    {_fmt_provider(p)}")
        else:
            print(f"✗ {model_id}  — {result['error']}", file=sys.stderr)
            failures.append(model_id)

    print()
    if failures:
        print(
            f"[FATAL] {len(failures)} model(s) have no live provider: {failures}. "
            "Refusing to start a full run against dead endpoints.",
            file=sys.stderr,
        )
        return 1
    print(f"All {len(hf_rows)} HuggingFace model(s) have a live provider.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
