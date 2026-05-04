# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Fallback-chain executor tests (REQ-146, F5).

Exercises ``specsmith.agent.fallback.run_with_fallback`` end-to-end with
synthetic ``invoke`` callables that raise the same shapes the real
provider drivers raise: ``urllib.error.HTTPError`` for HTTP responses,
``TimeoutError`` / ``socket.timeout`` / ``ConnectionError`` for network
failures, and arbitrary ``RuntimeError`` for programmer bugs.

These tests are pure-Python and hermetic — no real HTTP, no providers.
"""

from __future__ import annotations

import io
from urllib.error import HTTPError, URLError

import pytest

from specsmith.agent.fallback import (
    FallbackAttempt,
    FallbackResult,
    parse_target,
    run_with_fallback,
)

# ---------------------------------------------------------------------------
# parse_target
# ---------------------------------------------------------------------------


def test_parse_target_provider_with_model() -> None:
    assert parse_target("anthropic/claude-haiku-4-5") == (
        "provider",
        "anthropic",
        "claude-haiku-4-5",
    )


def test_parse_target_ollama_model_with_colon() -> None:
    # Ollama model tags contain a colon; the partition on '/' must keep the
    # whole right-hand side as the model name.
    assert parse_target("ollama/qwen2.5:7b") == ("provider", "ollama", "qwen2.5:7b")


def test_parse_target_endpoint_prefix() -> None:
    assert parse_target("endpoint:home-vllm") == ("endpoint", "home-vllm", "")


def test_parse_target_provider_only() -> None:
    # No '/' — no model component.
    assert parse_target("anthropic") == ("provider", "anthropic", "")


def test_parse_target_empty_or_blank() -> None:
    assert parse_target("") == ("provider", "", "")
    assert parse_target("   ") == ("provider", "", "")


def test_parse_target_strips_whitespace() -> None:
    assert parse_target("  anthropic / claude-haiku-4-5  ") == (
        "provider",
        "anthropic",
        "claude-haiku-4-5",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _http_error(code: int) -> HTTPError:
    """Construct an HTTPError matching what urllib raises in production."""
    return HTTPError(
        url="http://example/v1/chat",
        code=code,
        msg=f"HTTP {code}",
        hdrs=None,  # type: ignore[arg-type]
        fp=io.BytesIO(b""),
    )


def _make_invoke(behaviors: dict[str, object]):
    """Return an ``invoke`` callable whose behavior keys on the ident.

    Each value is either an exception instance to raise or a sentinel
    string to return.
    """

    def invoke(kind: str, ident: str, model: str) -> object:  # noqa: ARG001
        b = behaviors.get(ident)
        if isinstance(b, BaseException):
            raise b
        return b

    return invoke


# ---------------------------------------------------------------------------
# run_with_fallback — primary success path
# ---------------------------------------------------------------------------


def test_primary_success_short_circuits_chain() -> None:
    invoke = _make_invoke({"anthropic": "primary-result", "ollama": "fallback-result"})
    out = run_with_fallback(
        primary_target="anthropic/claude-haiku-4-5",
        fallback_chain=["ollama/qwen2.5:7b"],
        invoke=invoke,
    )
    assert isinstance(out, FallbackResult)
    assert out.value == "primary-result"
    assert out.used == "anthropic/claude-haiku-4-5"
    assert len(out.attempts) == 1
    assert out.attempts[0].ok is True


# ---------------------------------------------------------------------------
# Transient failures — chain walks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code",
    [408, 429, 500, 502, 503, 504, 599],
)
def test_http_5xx_and_throttling_falls_through(code: int) -> None:
    """5xx + 408 + 429 are treated as transient; chain advances."""
    invoke = _make_invoke({"anthropic": _http_error(code), "ollama": "fallback-result"})
    out = run_with_fallback(
        primary_target="anthropic/claude-haiku-4-5",
        fallback_chain=["ollama/qwen2.5:7b"],
        invoke=invoke,
    )
    assert out.value == "fallback-result"
    assert out.used == "ollama/qwen2.5:7b"
    assert len(out.attempts) == 2
    assert out.attempts[0].ok is False
    assert str(code) in out.attempts[0].error
    assert out.attempts[1].ok is True


@pytest.mark.parametrize(
    "exc",
    [
        TimeoutError("timed out"),
        URLError("connection refused"),
        ConnectionError("connection reset"),
        OSError("network is unreachable"),
    ],
)
def test_network_errors_fall_through(exc: BaseException) -> None:
    invoke = _make_invoke({"anthropic": exc, "ollama": "fallback-result"})
    out = run_with_fallback(
        primary_target="anthropic/claude-haiku-4-5",
        fallback_chain=["ollama/qwen2.5:7b"],
        invoke=invoke,
    )
    assert out.value == "fallback-result"
    assert out.used == "ollama/qwen2.5:7b"
    assert out.attempts[0].ok is False
    assert out.attempts[1].ok is True


def test_chain_walks_all_targets_in_order() -> None:
    """All targets failing transiently exhausts the chain (value=None)."""
    invoke = _make_invoke(
        {
            "anthropic": _http_error(503),
            "ollama": _http_error(429),
            "home-vllm": _http_error(500),
        },
    )
    out = run_with_fallback(
        primary_target="anthropic/claude-haiku-4-5",
        fallback_chain=["ollama/qwen2.5:7b", "endpoint:home-vllm"],
        invoke=invoke,
    )
    assert out.value is None
    assert out.used == ""
    assert [a.target for a in out.attempts] == [
        "anthropic/claude-haiku-4-5",
        "ollama/qwen2.5:7b",
        "endpoint:home-vllm",
    ]
    assert all(a.ok is False for a in out.attempts)


# ---------------------------------------------------------------------------
# Non-transient failures must surface immediately
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("code", [400, 401, 403, 404, 422])
def test_http_4xx_non_throttle_is_not_retried(code: int) -> None:
    """4xx (except 408/429) must bubble up.

    Masking auth errors as outages is the failure mode this guards against.
    """
    invoke = _make_invoke({"anthropic": _http_error(code), "ollama": "fallback"})
    with pytest.raises(HTTPError) as exc_info:
        run_with_fallback(
            primary_target="anthropic/claude-haiku-4-5",
            fallback_chain=["ollama/qwen2.5:7b"],
            invoke=invoke,
        )
    assert exc_info.value.code == code


def test_runtime_error_is_not_retried() -> None:
    invoke = _make_invoke({"anthropic": RuntimeError("invariant violated")})
    with pytest.raises(RuntimeError, match="invariant violated"):
        run_with_fallback(
            primary_target="anthropic/claude-haiku-4-5",
            fallback_chain=["ollama/qwen2.5:7b"],
            invoke=invoke,
        )


def test_value_error_is_not_retried() -> None:
    invoke = _make_invoke({"anthropic": ValueError("bad input")})
    with pytest.raises(ValueError, match="bad input"):
        run_with_fallback(
            primary_target="anthropic/claude-haiku-4-5",
            fallback_chain=["ollama/qwen2.5:7b"],
            invoke=invoke,
        )


# ---------------------------------------------------------------------------
# Chain edge cases
# ---------------------------------------------------------------------------


def test_blank_targets_are_skipped() -> None:
    """Empty-string entries in the chain are filtered out, not retried as ''.

    Otherwise an empty entry would consume an attempt slot.
    """
    invoke = _make_invoke(
        {"anthropic": _http_error(503), "ollama": "fallback-result"},
    )
    out = run_with_fallback(
        primary_target="anthropic/claude-haiku-4-5",
        fallback_chain=["", "   ", "ollama/qwen2.5:7b"],
        invoke=invoke,
    )
    assert out.used == "ollama/qwen2.5:7b"
    # Only the primary + the real ollama target should be in attempts.
    assert [a.target for a in out.attempts] == [
        "anthropic/claude-haiku-4-5",
        "ollama/qwen2.5:7b",
    ]


def test_empty_primary_target_is_skipped_and_chain_runs() -> None:
    invoke = _make_invoke({"ollama": "fallback-result"})
    out = run_with_fallback(
        primary_target="",
        fallback_chain=["ollama/qwen2.5:7b"],
        invoke=invoke,
    )
    assert out.used == "ollama/qwen2.5:7b"
    assert out.value == "fallback-result"


def test_endpoint_target_invokes_with_endpoint_kind() -> None:
    seen: list[tuple[str, str, str]] = []

    def invoke(kind: str, ident: str, model: str) -> object:
        seen.append((kind, ident, model))
        return "ok"

    out = run_with_fallback(
        primary_target="endpoint:home-vllm",
        fallback_chain=[],
        invoke=invoke,
    )
    assert out.value == "ok"
    assert seen == [("endpoint", "home-vllm", "")]


# ---------------------------------------------------------------------------
# on_attempt callback
# ---------------------------------------------------------------------------


def test_on_attempt_called_per_attempt() -> None:
    invoke = _make_invoke({"anthropic": _http_error(503), "ollama": "fallback"})
    seen: list[FallbackAttempt] = []
    out = run_with_fallback(
        primary_target="anthropic/claude-haiku-4-5",
        fallback_chain=["ollama/qwen2.5:7b"],
        invoke=invoke,
        on_attempt=seen.append,
    )
    assert out.value == "fallback"
    assert len(seen) == 2
    assert seen[0].ok is False
    assert seen[1].ok is True
    assert seen[1].target == "ollama/qwen2.5:7b"


def test_on_attempt_callback_errors_are_swallowed() -> None:
    """A buggy on_attempt callback must not break the fallback chain."""

    def boom(_: FallbackAttempt) -> None:
        raise RuntimeError("callback exploded")

    invoke = _make_invoke({"anthropic": _http_error(503), "ollama": "fallback"})
    out = run_with_fallback(
        primary_target="anthropic/claude-haiku-4-5",
        fallback_chain=["ollama/qwen2.5:7b"],
        invoke=invoke,
        on_attempt=boom,
    )
    assert out.value == "fallback"
    assert out.used == "ollama/qwen2.5:7b"


# ---------------------------------------------------------------------------
# FallbackAttempt / FallbackResult dataclasses
# ---------------------------------------------------------------------------


def test_fallback_attempt_to_dict_round_trip() -> None:
    attempt = FallbackAttempt(target="anthropic/claude", ok=False, error="boom")
    assert attempt.to_dict() == {
        "target": "anthropic/claude",
        "ok": False,
        "error": "boom",
    }


def test_fallback_result_default_attempts_is_empty_list() -> None:
    """FallbackResult.__post_init__ must replace None with [] so callers can
    safely append without checking for None first."""
    result = FallbackResult(value="x")
    assert result.attempts == []
    result.attempts.append(FallbackAttempt(target="a", ok=True))
    assert len(result.attempts) == 1
