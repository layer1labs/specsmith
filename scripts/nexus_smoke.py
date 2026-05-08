#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Nexus smoke test — verify l1-nexus connectivity (REQ-089, REQ-095).

Run manually when you have a local vLLM/Ollama instance:
    python scripts/nexus_smoke.py

Returns a structured JSON result with pass/fail and timing.
"""

from __future__ import annotations

import json
import sys
import time


def smoke_test(
    base_url: str = "",
    *,
    timeout: float = 10.0,
) -> dict:
    """Run a minimal smoke test against local LLM endpoints.

    Returns ``{"ok": bool, "content": str, "latency_ms": int, "error": str}``.
    """
    import urllib.error
    import urllib.request

    if base_url:
        endpoints = [(base_url.rstrip("/") + "/api/tags", "custom")]
    else:
        endpoints = [
            ("http://localhost:11434/api/tags", "ollama"),
            ("http://localhost:8000/v1/models", "vllm"),
        ]

    last_error = ""
    for url, name in endpoints:
        try:
            t0 = time.monotonic()
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
                body = resp.read().decode()
            latency = int((time.monotonic() - t0) * 1000)
            return {
                "ok": True,
                "content": body[:500],
                "latency_ms": latency,
                "error": "",
            }
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
            continue

    return {
        "ok": False,
        "content": "",
        "latency_ms": 0,
        "error": last_error or "No local LLM endpoint reachable",
    }


if __name__ == "__main__":
    result = smoke_test()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["ok"] else 1)
