# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Nexus live l1-nexus smoke test (REQ-089).

POSTs a minimal chat-completions request to a running vLLM ``l1-nexus``
container and reports whether the model responded with a well-formed
``choices[0].message.content``.

The pytest integration test (TEST-089) skips unless ``NEXUS_LIVE=1`` is set,
so the suite stays green offline. When the container is up, the script
verifies that the docker-compose entrypoint, the Hermes tool-call parser,
and the ``--served-model-name l1-nexus`` flag (REQ-074, REQ-075) all
cooperate to produce an OpenAI-compatible response.

Usage (from a shell, not pytest)::

    docker compose up -d l1-nexus
    py scripts/nexus_smoke.py
    docker compose down

Or from Python::

    from scripts.nexus_smoke import smoke_test
    result = smoke_test()
    assert result["ok"], result
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_MODEL = "l1-nexus"
DEFAULT_PROMPT = "Reply with the single word 'ready'."


def smoke_test(
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    prompt: str = DEFAULT_PROMPT,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Send a chat-completions request and return a structured result.

    Always returns a dict (never raises) so callers can inspect ``ok`` and
    ``error`` without try/except. The function is deliberately small so it
    can be exercised by both ``pytest`` and a human at the shell.

    Returns
    -------
    dict
        ``{"ok": bool, "content": str, "latency_ms": int, "error": str}``
    """
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 16,
        "temperature": 0.0,
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(  # noqa: S310 - localhost is the contract
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            raw = response.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        return {
            "ok": False,
            "content": "",
            "latency_ms": int((time.monotonic() - started) * 1000),
            "error": f"transport: {exc}",
        }
    elapsed_ms = int((time.monotonic() - started) * 1000)

    try:
        data = json.loads(raw)
    except ValueError as exc:
        return {
            "ok": False,
            "content": "",
            "latency_ms": elapsed_ms,
            "error": f"non-json response: {exc}",
        }

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        return {
            "ok": False,
            "content": "",
            "latency_ms": elapsed_ms,
            "error": f"missing choices[0].message.content: {exc}",
        }

    if not isinstance(content, str) or not content.strip():
        return {
            "ok": False,
            "content": str(content),
            "latency_ms": elapsed_ms,
            "error": "empty content",
        }

    return {
        "ok": True,
        "content": content.strip(),
        "latency_ms": elapsed_ms,
        "error": "",
    }


def _main() -> int:
    result = smoke_test()
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(_main())
