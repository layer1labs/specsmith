# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for proactive model rate-limit pacing and retry handling."""

from __future__ import annotations

from pathlib import Path

from specsmith.rate_limits import (
    BUILTIN_PROFILES,
    ModelRateLimitProfile,
    RateLimitScheduler,
    classify_rate_limit_error,
    compute_retry_delay,
    load_rate_limit_profiles,
    save_rate_limit_profiles,
)


class FakeClock:
    def __init__(self) -> None:
        self.current = 0.0

    def __call__(self) -> float:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.current += seconds


def test_profile_overrides_round_trip(tmp_path: Path) -> None:
    defaults = [
        ModelRateLimitProfile(
            provider="openai",
            model="gpt-5.4",
            rpm_limit=60,
            tpm_limit=500000,
            utilization_target=0.7,
            concurrency_cap=4,
            source="default",
        )
    ]
    save_rate_limit_profiles(
        tmp_path,
        [
            ModelRateLimitProfile(
                provider="openai",
                model="gpt-5.4",
                rpm_limit=45,
                tpm_limit=400000,
                utilization_target=0.6,
                concurrency_cap=2,
                source="override",
            )
        ],
    )

    profiles = load_rate_limit_profiles(tmp_path, defaults=defaults)

    assert len(profiles) == 1
    assert profiles[0].rpm_limit == 45
    assert profiles[0].tpm_limit == 400000
    assert profiles[0].concurrency_cap == 2


def test_acquire_waits_for_token_budget_refill() -> None:
    clock = FakeClock()
    scheduler = RateLimitScheduler(
        [
            ModelRateLimitProfile(
                provider="openai",
                model="gpt-5.4",
                rpm_limit=20,
                tpm_limit=1000,
                utilization_target=0.7,
                concurrency_cap=4,
            )
        ],
        clock=clock,
        sleep_fn=clock.sleep,
    )

    first = scheduler.acquire(
        "openai",
        "gpt-5.4",
        estimated_input_tokens=200,
        max_output_tokens=300,
    )
    second = scheduler.acquire(
        "openai",
        "gpt-5.4",
        estimated_input_tokens=200,
        max_output_tokens=100,
    )
    snapshot = scheduler.snapshot("openai", "gpt-5.4")

    assert first.waited_seconds == 0.0
    assert second.waited_seconds == 60.0
    assert clock.current == 60.0
    assert snapshot.rolling_token_count == 300
    assert snapshot.token_utilization < 1.0
    assert snapshot.moving_average_tokens > 0.0


def test_acquire_waits_for_request_budget_refill() -> None:
    clock = FakeClock()
    scheduler = RateLimitScheduler(
        [
            ModelRateLimitProfile(
                provider="anthropic",
                model="claude-sonnet",
                rpm_limit=2,
                tpm_limit=100000,
                utilization_target=0.5,
                concurrency_cap=2,
            )
        ],
        clock=clock,
        sleep_fn=clock.sleep,
    )

    scheduler.acquire(
        "anthropic",
        "claude-sonnet",
        estimated_input_tokens=100,
        max_output_tokens=100,
    )
    second = scheduler.acquire(
        "anthropic",
        "claude-sonnet",
        estimated_input_tokens=100,
        max_output_tokens=100,
    )

    assert second.waited_seconds == 60.0
    assert clock.current == 60.0


def test_openai_retry_after_text_is_parsed() -> None:
    error = (
        "OpenAI API error: received error while streaming: "
        '{"type":"tokens","code":"rate_limit_exceeded","message":"Rate limit reached '
        "for gpt-5.4 in organization org-123 on tokens per min (TPM): Limit 500000, "
        'Used 341693, Requested 248254. Please try again in 10.793s."}'
    )

    details = classify_rate_limit_error(error)

    assert details.is_rate_limit is True
    assert details.retry_after_seconds == 10.793


def test_fallback_backoff_uses_exponential_delay_with_jitter() -> None:
    delay = compute_retry_delay(
        "429 too many requests",
        attempt=3,
        base_delay_seconds=2.0,
        max_delay_seconds=60.0,
        random_fn=lambda: 0.5,
    )

    assert delay == 8.8


def test_rate_limit_reduces_concurrency_and_success_restores_it() -> None:
    clock = FakeClock()
    scheduler = RateLimitScheduler(
        [
            ModelRateLimitProfile(
                provider="google",
                model="gemini-flash",
                rpm_limit=100,
                tpm_limit=100000,
                utilization_target=0.7,
                concurrency_cap=4,
            )
        ],
        clock=clock,
        sleep_fn=clock.sleep,
        restore_after_successes=2,
    )

    reservation = scheduler.acquire(
        "google",
        "gemini-flash",
        estimated_input_tokens=50,
        max_output_tokens=50,
    )
    scheduler.record_rate_limit(reservation, "Rate limit exceeded", attempt=1)
    degraded = scheduler.snapshot("google", "gemini-flash")

    for _ in range(2):
        success = scheduler.acquire(
            "google",
            "gemini-flash",
            estimated_input_tokens=50,
            max_output_tokens=50,
        )
        scheduler.record_success(success)
    partially_restored = scheduler.snapshot("google", "gemini-flash")

    for _ in range(2):
        success = scheduler.acquire(
            "google",
            "gemini-flash",
            estimated_input_tokens=50,
            max_output_tokens=50,
        )
        scheduler.record_success(success)
    fully_restored = scheduler.snapshot("google", "gemini-flash")

    assert degraded.current_concurrency_cap == 2
    assert partially_restored.current_concurrency_cap == 3
    assert fully_restored.current_concurrency_cap == 4


def test_builtin_profiles_cover_common_providers() -> None:
    """BUILTIN_PROFILES must include wildcard fallbacks for the three main providers."""
    providers = {p.provider for p in BUILTIN_PROFILES}
    assert "openai" in providers
    assert "anthropic" in providers
    assert "google" in providers

    # Every entry must have a positive RPM and TPM
    for profile in BUILTIN_PROFILES:
        assert profile.rpm_limit > 0, f"{profile.key}: rpm_limit must be > 0"
        assert profile.tpm_limit > 0, f"{profile.key}: tpm_limit must be > 0"
        assert 0 < profile.utilization_target <= 1, (
            f"{profile.key}: utilization_target out of range"
        )


def test_builtin_profiles_gpt54_matches_issue_example() -> None:
    """gpt-5.4 entry should have the 500K TPM limit from the issue #59 example."""
    gpt54 = next(
        (p for p in BUILTIN_PROFILES if p.provider == "openai" and p.model == "gpt-5.4"), None
    )
    assert gpt54 is not None, "gpt-5.4 profile must be present in BUILTIN_PROFILES"
    assert gpt54.tpm_limit == 500_000


def test_builtin_profiles_used_as_defaults_and_overridden(tmp_path: Path) -> None:
    """Local override for a built-in model replaces the built-in entry."""
    override = ModelRateLimitProfile(
        provider="openai",
        model="gpt-4o",
        rpm_limit=100,
        tpm_limit=5_000_000,
        source="override",
    )
    save_rate_limit_profiles(tmp_path, [override])

    profiles = load_rate_limit_profiles(tmp_path, defaults=BUILTIN_PROFILES)

    gpt4o = next((p for p in profiles if p.provider == "openai" and p.model == "gpt-4o"), None)
    assert gpt4o is not None
    assert gpt4o.rpm_limit == 100, "local override should take precedence over built-in"
    assert gpt4o.tpm_limit == 5_000_000


def test_scheduler_resolves_builtin_profile_via_wildcard() -> None:
    """Scheduler must fall back to the openai/* wildcard for an unknown model."""
    clock = FakeClock()
    scheduler = RateLimitScheduler(
        BUILTIN_PROFILES,
        clock=clock,
        sleep_fn=clock.sleep,
    )
    # "gpt-future" is not an explicit profile but openai/* catches it
    reservation = scheduler.acquire(
        "openai",
        "gpt-future",
        estimated_input_tokens=100,
        max_output_tokens=100,
    )
    assert reservation.waited_seconds == 0.0  # no wait on first request
