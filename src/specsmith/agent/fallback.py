# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Resilient fallback-chain executor for agent profiles (REQ-146).

Profiles in :mod:`specsmith.agent.profiles` carry a ``fallback_chain``
list of ``"<provider>/<model>"`` or ``"endpoint:<id>"`` strings. When the
primary call raises a transient error (timeout / connection refused /
HTTP 429 / HTTP 5xx), this module walks the chain in order until one
returns successfully or the chain is exhausted.

The chain is **resilience**, not **routing** — picking the right primary
is the routing table's job. The chain only kicks in when the chosen
primary fails.
"""

from __future__ import annotations

import contextlib
import socket
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError

# (ruff I001 sentinel: imports above are intentionally grouped stdlib + typing)


# Errors we treat as worth falling through. Anything else is a programmer
# bug and should bubble up so we don't paper over correctness issues.
TRANSIENT_EXCEPTIONS: tuple[type[BaseException], ...] = (
    TimeoutError,
    socket.timeout,
    URLError,
    ConnectionError,
    OSError,
)


@dataclass
class FallbackAttempt:
    """One step of an executed chain."""

    target: str
    ok: bool
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"target": self.target, "ok": self.ok, "error": self.error}


@dataclass
class FallbackResult:
    """Outcome of :func:`run_with_fallback`."""

    value: Any
    used: str = ""
    attempts: list[FallbackAttempt] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.attempts is None:
            self.attempts = []


def _is_transient(exc: BaseException) -> bool:
    if isinstance(exc, HTTPError):
        return 500 <= int(getattr(exc, "code", 0) or 0) < 600 or exc.code in {408, 429}
    return isinstance(exc, TRANSIENT_EXCEPTIONS)


def parse_target(target: str) -> tuple[str, str, str]:
    """Decompose a chain entry into ``(kind, provider_or_id, model)``.

    Examples::

        parse_target("anthropic/claude-haiku-4-5")
            # -> ("provider", "anthropic", "claude-haiku-4-5")
        parse_target("ollama/qwen2.5:7b")
            # -> ("provider", "ollama", "qwen2.5:7b")
        parse_target("endpoint:home-vllm")
            # -> ("endpoint", "home-vllm", "")
    """
    cleaned = (target or "").strip()
    if not cleaned:
        return ("provider", "", "")
    if cleaned.startswith("endpoint:"):
        return ("endpoint", cleaned[len("endpoint:") :], "")
    if "/" not in cleaned:
        return ("provider", cleaned, "")
    provider, _, model = cleaned.partition("/")
    return ("provider", provider.strip(), model.strip())


def run_with_fallback(
    primary_target: str,
    fallback_chain: Iterable[str],
    invoke: Callable[[str, str, str], Any],
    *,
    on_attempt: Callable[[FallbackAttempt], None] | None = None,
) -> FallbackResult:
    """Try the primary target; on transient failure walk the chain.

    ``invoke`` is called as ``invoke(kind, provider_or_id, model)`` and
    must raise on failure. Any non-transient exception aborts the chain
    immediately (we don't want to mask a programmer bug as an outage).
    """
    targets = [primary_target] + [t for t in fallback_chain if t]
    result = FallbackResult(value=None, attempts=[])
    for target in targets:
        kind, ident, model = parse_target(target)
        if not ident:
            continue
        try:
            value = invoke(kind, ident, model)
        except Exception as exc:  # noqa: BLE001
            attempt = FallbackAttempt(target=target, ok=False, error=str(exc))
            result.attempts.append(attempt)
            if on_attempt:
                with contextlib.suppress(Exception):
                    on_attempt(attempt)
            if not _is_transient(exc):
                # Programmer error / auth failure — bubble up immediately
                # so the caller sees the real cause.
                raise
            continue
        attempt = FallbackAttempt(target=target, ok=True)
        result.attempts.append(attempt)
        if on_attempt:
            with contextlib.suppress(Exception):
                on_attempt(attempt)
        result.value = value
        result.used = target
        return result
    return result  # exhausted, value=None


__all__ = [
    "FallbackAttempt",
    "FallbackResult",
    "TRANSIENT_EXCEPTIONS",
    "parse_target",
    "run_with_fallback",
]
