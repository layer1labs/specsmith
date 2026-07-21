"""Verify selected models through the endpoints used by GovernanceBench.

Hugging Face selections are checked against the Inference Providers metadata
router. OpenAI selections are checked against the model endpoint. With
``--live-call``, every supported provider also receives one tiny tool-enabled
chat request, catching exhausted credits and runtime incompatibilities before
an expensive matrix starts.

    GET https://router.huggingface.co/v1/models/<repo_id>   (Bearer HF_TOKEN)

The command exits non-zero if any selected model cannot be verified. Secrets
are read from environment variables and are never printed.

Model selection (first match wins):
    positional MODEL ids ...        explicit repo ids to probe
    --matrix PATH | -               read select_models.py JSON ({"include": [...]})
    --groups/--providers/--tiers    filter models.yml directly (see select_models)

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
import urllib.parse
import urllib.request
from pathlib import Path

# Same-package helpers (script dir is added to sys.path below).
sys.path.insert(0, str(Path(__file__).parent))

from select_models import _csv_set, load_registry, select  # noqa: E402

_ROUTER_MODEL_URL = "https://router.huggingface.co/v1/models/"
_HF_CHAT_URL = "https://router.huggingface.co/v1/chat/completions"
_OPENAI_MODEL_URL = "https://api.openai.com/v1/models/"
_OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
_HF_PROVIDER = "huggingface"


def _http_error_message(exc: urllib.error.HTTPError) -> str:
    """Return a bounded provider error message without request headers or secrets."""
    detail = ""
    try:
        payload = json.loads(exc.read().decode("utf-8"))
        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            detail = error["message"].strip()[:500]
    except (UnicodeDecodeError, ValueError):
        pass
    suffix = f": {detail}" if detail else ""
    return f"HTTP {exc.code} {exc.reason}{suffix}"


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
        return {"model": model_id, "ok": False, "error": _http_error_message(exc)}
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


def _probe_openai_model(model_id: str, token: str | None, timeout: float) -> dict:
    """Confirm that an OpenAI credential can access an exact model id."""
    if not token:
        return {"model": model_id, "ok": False, "error": "OPENAI_API_KEY is not set"}
    quoted = urllib.parse.quote(model_id, safe="")
    req = urllib.request.Request(
        _OPENAI_MODEL_URL + quoted,
        headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"model": model_id, "ok": False, "error": _http_error_message(exc)}
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return {"model": model_id, "ok": False, "error": str(exc)}
    returned_id = payload.get("id") if isinstance(payload, dict) else None
    return {
        "model": model_id,
        "ok": returned_id == model_id,
        "error": None if returned_id == model_id else "model lookup returned an unexpected id",
    }


def _chat_probe_payload(model_id: str) -> dict:
    """Build a minimal tool-enabled request matching the benchmark API surface."""
    payload: dict = {
        "model": model_id,
        "messages": [{"role": "user", "content": "Reply with OK."}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "ping",
                    "description": "Return a health-check value.",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ],
        "tool_choice": "auto",
        "temperature": 0,
    }
    lowered = model_id.lower()
    if lowered.startswith(("gpt-5", "o1", "o3", "o4")):
        payload["max_completion_tokens"] = 32
        payload.pop("temperature", None)
        if lowered.startswith("gpt-5.6"):
            payload["reasoning_effort"] = "none"
    else:
        payload["max_tokens"] = 32
    return payload


def _probe_chat_endpoint(
    model_id: str,
    token: str | None,
    endpoint: str,
    timeout: float,
) -> dict:
    """Make one tiny paid call to detect auth, billing, and tool failures."""
    if not token:
        return {"model": model_id, "ok": False, "error": "API credential is not set"}
    body = json.dumps(_chat_probe_payload(model_id)).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"model": model_id, "ok": False, "error": _http_error_message(exc)}
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return {"model": model_id, "ok": False, "error": str(exc)}
    choices = payload.get("choices") if isinstance(payload, dict) else None
    usage = payload.get("usage", {}) if isinstance(payload, dict) else {}
    return {
        "model": model_id,
        "ok": isinstance(choices, list) and bool(choices),
        "usage": usage if isinstance(usage, dict) else {},
        "error": None if isinstance(choices, list) and choices else "response had no choices",
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
    parser.add_argument(
        "--live-call",
        action="store_true",
        help=(
            "make one tiny tool-enabled request per model to verify auth, "
            "credits, and runtime support"
        ),
    )
    args = parser.parse_args()
    if args.registry is None:
        args.registry = str(Path(__file__).with_name("models.yml"))
    return args


def main() -> int:
    args = _parse_args()
    try:
        rows = _resolve_models(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error resolving models: {exc}", file=sys.stderr)
        return 1

    failures: list[str] = []
    print(f"Probing {len(rows)} selected model(s):\n")
    for row in rows:
        model_id = str(row["model"])
        provider = str(row.get("provider") or _HF_PROVIDER)
        result: dict
        if provider == _HF_PROVIDER:
            token = os.environ.get("HF_TOKEN")
            result = _probe_one(model_id, token, args.timeout)
            if result["ok"]:
                print(f"OK {provider}/{model_id} ({result['n_providers']} provider(s))")
                for live_provider in result["live"]:
                    print(f"    {_fmt_provider(live_provider)}")
                if args.live_call:
                    result = _probe_chat_endpoint(
                        model_id,
                        token,
                        _HF_CHAT_URL,
                        args.timeout,
                    )
            if result["ok"] and args.live_call:
                print("    live tool call: OK")
        elif provider == "openai":
            token = os.environ.get("OPENAI_API_KEY")
            result = _probe_openai_model(model_id, token, args.timeout)
            if result["ok"]:
                print(f"OK {provider}/{model_id} (model access)")
                if args.live_call:
                    result = _probe_chat_endpoint(
                        model_id,
                        token,
                        _OPENAI_CHAT_URL,
                        args.timeout,
                    )
            if result["ok"] and args.live_call:
                print("    live tool call: OK")
        elif provider == "openai-compat" and args.live_call:
            base_url = os.environ.get(
                "BENCH_OPENAI_BASE_URL",
                "https://openrouter.ai/api/v1",
            ).rstrip("/")
            result = _probe_chat_endpoint(
                model_id,
                os.environ.get("BENCH_OPENAI_COMPAT_API_KEY"),
                f"{base_url}/chat/completions",
                args.timeout,
            )
            if result["ok"]:
                print(f"OK {provider}/{model_id} (live tool call)")
        else:
            result = {
                "model": model_id,
                "ok": False,
                "error": f"no fail-closed endpoint probe is implemented for provider '{provider}'",
            }

        if not result["ok"]:
            print(f"FAIL {provider}/{model_id}: {result['error']}", file=sys.stderr)
            failures.append(f"{provider}/{model_id}")

    print()
    if failures:
        print(
            f"[FATAL] {len(failures)} model probe(s) failed: {failures}. "
            "Refusing to start a full run against unavailable endpoints.",
            file=sys.stderr,
        )
        return 1
    print(f"All {len(rows)} selected model(s) passed their available probes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
