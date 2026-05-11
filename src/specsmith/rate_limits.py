# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Runtime model rate-limit profiles, pacing, and retry helpers."""

from __future__ import annotations

import json
import math
import random
import re
import time
from collections import deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

_STATE_DIR = ".specsmith"
_PROFILE_FILE = "model-rate-limits.json"
_RUNTIME_STATE_FILE = "model-rate-limit-state.json"
_ROLLING_WINDOW_SECONDS = 60.0
_CONCURRENCY_POLL_SECONDS = 0.1
_MOVING_AVERAGE_ALPHA = 0.25
_RETRY_JITTER_RATIO = 0.2

_WAIT_PATTERNS = (
    re.compile(
        r"please\s+try\s+again\s+in\s+(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>ms|s|sec|secs|seconds)",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"retry\s+(?:after|in)\s+(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>ms|s|sec|secs|seconds)",
        flags=re.IGNORECASE,
    ),
)


@dataclass(slots=True)
class ModelRateLimitProfile:
    """Rate-limit profile for a single provider/model path."""

    provider: str
    model: str
    rpm_limit: int
    tpm_limit: int
    utilization_target: float = 0.7
    concurrency_cap: int = 1
    source: str = "local"

    def __post_init__(self) -> None:
        self.provider = _normalize_key_part(self.provider)
        self.model = _normalize_key_part(self.model)
        if self.rpm_limit <= 0:
            raise ValueError("rpm_limit must be greater than zero")
        if self.tpm_limit <= 0:
            raise ValueError("tpm_limit must be greater than zero")
        if not 0 < self.utilization_target <= 1:
            raise ValueError("utilization_target must be greater than 0 and at most 1")
        if self.concurrency_cap <= 0:
            raise ValueError("concurrency_cap must be greater than zero")

    @property
    def key(self) -> str:
        """Stable provider/model key."""
        return _profile_key(self.provider, self.model)

    @property
    def effective_rpm_limit(self) -> int:
        """Budgeted request ceiling after utilization target is applied."""
        return max(1, int(math.floor(self.rpm_limit * self.utilization_target)))

    @property
    def effective_tpm_limit(self) -> int:
        """Budgeted token ceiling after utilization target is applied."""
        return max(1, int(math.floor(self.tpm_limit * self.utilization_target)))

    def matches(self, provider: str, model: str) -> bool:
        """Check if this profile applies to the given provider/model."""
        provider = _normalize_key_part(provider)
        model = _normalize_key_part(model)
        provider_match = self.provider == "*" or self.provider == provider
        model_match = self.model == "*" or self.model == model
        return provider_match and model_match


@dataclass(slots=True)
class RateLimitReservation:
    """A pre-dispatch budget reservation for a single request."""

    reservation_id: str
    provider: str
    model: str
    estimated_input_tokens: int
    max_output_tokens: int
    estimated_total_tokens: int
    acquired_at: float
    waited_seconds: float = 0.0


_DEFAULT_IMAGE_TOKEN_ESTIMATE = 4096


@dataclass(slots=True)
class RateLimitSnapshot:
    """Current rolling-window and moving-average state for a model."""

    provider: str
    model: str
    rpm_limit: int
    tpm_limit: int
    effective_rpm_limit: int
    effective_tpm_limit: int
    rolling_request_count: int
    rolling_token_count: int
    moving_average_requests: float
    moving_average_tokens: float
    request_utilization: float
    token_utilization: float
    base_concurrency_cap: int
    current_concurrency_cap: int
    in_flight: int
    # EMA utilisation fields (REQ-272): normalised 0.0–1.0
    rpm_ema: float = 0.0
    tpm_ema: float = 0.0
    # Adaptive concurrency state
    dynamic_concurrency: int = 0


@dataclass(slots=True)
class RateLimitErrorDetails:
    """Normalized provider rate-limit classification."""

    is_rate_limit: bool
    message: str
    status_code: int | None = None
    retry_after_seconds: float | None = None


@dataclass(slots=True)
class _TokenEvent:
    timestamp: float
    tokens: int
    reservation_id: str


@dataclass(slots=True)
class _ModelRuntimeState:
    request_timestamps: deque[float] = field(default_factory=deque)
    token_events: deque[_TokenEvent] = field(default_factory=deque)
    active_reservations: set[str] = field(default_factory=set)
    in_flight: int = 0
    current_concurrency_cap: int = 0
    success_streak: int = 0
    moving_average_requests: float = 0.0
    moving_average_tokens: float = 0.0
    # EMA utilisation (normalised 0.0–1.0) — REQ-272
    rpm_ema: float = 0.0
    tpm_ema: float = 0.0
    # Adaptive concurrency: timestamp until which concurrency is reduced — REQ-273
    reduced_until: float = 0.0


def _normalize_key_part(value: str) -> str:
    return value.strip().lower()


def _profile_key(provider: str, model: str) -> str:
    return f"{_normalize_key_part(provider)}::{_normalize_key_part(model)}"


def _get_profile_path(root: Path) -> Path:
    path = root / _STATE_DIR / _PROFILE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _get_runtime_state_path(root: Path) -> Path:
    path = root / _STATE_DIR / _RUNTIME_STATE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Built-in provider/model defaults
# ---------------------------------------------------------------------------
# These are conservative starting points.  Account and tier limits vary.
# Local overrides (saved in .specsmith/model-rate-limits.json) always take
# precedence over these defaults — see load_rate_limit_profiles().


def _default(  # noqa: PLR0913
    provider: str,
    model: str,
    rpm: int,
    tpm: int,
    utilization_target: float = 0.7,
    concurrency_cap: int = 1,
) -> ModelRateLimitProfile:
    return ModelRateLimitProfile(
        provider=provider,
        model=model,
        rpm_limit=rpm,
        tpm_limit=tpm,
        utilization_target=utilization_target,
        concurrency_cap=concurrency_cap,
        source="default",
    )


BUILTIN_PROFILES: list[ModelRateLimitProfile] = [
    # --- OpenAI ---
    _default("openai", "gpt-4o", rpm=500, tpm=30_000_000),
    _default("openai", "gpt-4o-mini", rpm=500, tpm=200_000_000),
    _default("openai", "gpt-4-turbo", rpm=500, tpm=800_000),
    _default("openai", "gpt-3.5-turbo", rpm=3500, tpm=90_000),
    _default("openai", "o1", rpm=500, tpm=30_000_000),
    _default("openai", "o1-mini", rpm=1000, tpm=200_000_000),
    _default("openai", "o3-mini", rpm=1000, tpm=200_000_000),
    # gpt-5.4 — org quota from issue #59 example: 500K TPM
    _default("openai", "gpt-5.4", rpm=60, tpm=500_000),
    # Wildcard fallback for unknown OpenAI models
    _default("openai", "*", rpm=500, tpm=500_000),
    # --- Anthropic ---
    _default("anthropic", "claude-opus-4", rpm=2000, tpm=40_000_000),
    _default("anthropic", "claude-sonnet-4", rpm=2000, tpm=40_000_000),
    _default("anthropic", "claude-haiku-3-5", rpm=2000, tpm=200_000_000),
    _default("anthropic", "claude-3-5-sonnet", rpm=2000, tpm=40_000_000),
    _default("anthropic", "claude-3-5-haiku", rpm=2000, tpm=200_000_000),
    _default("anthropic", "claude-3-opus", rpm=2000, tpm=40_000_000),
    # Wildcard fallback for unknown Anthropic models
    _default("anthropic", "*", rpm=2000, tpm=40_000_000),
    # --- Google ---
    _default("google", "gemini-1.5-pro", rpm=360, tpm=4_000_000),
    _default("google", "gemini-1.5-flash", rpm=1000, tpm=4_000_000),
    _default("google", "gemini-2.0-flash", rpm=1000, tpm=4_000_000),
    _default("google", "gemini-2.5-pro", rpm=360, tpm=4_000_000),
    # Wildcard fallback for unknown Google models
    _default("google", "*", rpm=360, tpm=4_000_000),
]
"""Conservative built-in RPM/TPM profiles for common provider/model paths.

Use ``specsmith credits limits defaults`` to inspect these values or install
them into a project's local override file.
"""


def save_rate_limit_profiles(root: Path, profiles: list[ModelRateLimitProfile]) -> None:
    """Persist local rate-limit profiles."""
    path = _get_profile_path(root)
    path.write_text(
        json.dumps([asdict(profile) for profile in profiles], indent=2),
        encoding="utf-8",
    )


def load_rate_limit_profiles(
    root: Path,
    *,
    defaults: list[ModelRateLimitProfile] | None = None,
) -> list[ModelRateLimitProfile]:
    """Load local profiles, overriding any provided defaults by provider/model key."""
    merged = {profile.key: profile for profile in defaults or []}
    path = _get_profile_path(root)
    if not path.exists():
        return list(merged.values())

    try:
        raw_profiles = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return list(merged.values())

    for item in raw_profiles:
        profile = ModelRateLimitProfile(**item)
        merged[profile.key] = profile
    return list(merged.values())


def classify_rate_limit_error(error: object) -> RateLimitErrorDetails:
    """Normalize provider-specific 429/rate-limit failures."""
    status_code = _extract_status_code(error)
    message = _extract_message(error)
    headers = _extract_headers(error)

    retry_after = _parse_retry_after_headers(headers)
    if retry_after is None:
        retry_after = _parse_retry_after_message(message)

    message_lower = message.lower()
    code = _extract_error_code(error)
    is_rate_limit = bool(
        status_code == 429
        or code in {"rate_limit_exceeded", "rate_limited"}
        or "rate limit" in message_lower
        or "too many requests" in message_lower
    )

    return RateLimitErrorDetails(
        is_rate_limit=is_rate_limit,
        message=message,
        status_code=status_code,
        retry_after_seconds=retry_after,
    )


def compute_retry_delay(
    error: object,
    attempt: int,
    *,
    base_delay_seconds: float = 1.0,
    max_delay_seconds: float = 60.0,
    random_fn: Callable[[], float] | None = None,
) -> float:
    """Return provider-prescribed wait or exponential backoff plus jitter."""
    details = classify_rate_limit_error(error)
    if details.retry_after_seconds is not None:
        return details.retry_after_seconds

    jitter_source = random_fn or random.random
    backoff = min(max_delay_seconds, base_delay_seconds * (2 ** max(attempt - 1, 0)))
    return float(backoff + (backoff * _RETRY_JITTER_RATIO * jitter_source()))


class RateLimitScheduler:
    """Rolling-window model scheduler with pacing and adaptive concurrency."""

    def __init__(
        self,
        profiles: list[ModelRateLimitProfile],
        *,
        clock: Callable[[], float] | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        random_fn: Callable[[], float] | None = None,
        window_seconds: float = _ROLLING_WINDOW_SECONDS,
        restore_after_successes: int = 3,
        concurrency_poll_seconds: float = _CONCURRENCY_POLL_SECONDS,
    ) -> None:
        self._profiles = {profile.key: profile for profile in profiles}
        self._states: dict[str, _ModelRuntimeState] = {}
        self._reservations: dict[str, RateLimitReservation] = {}
        self._clock = clock or time.monotonic
        self._sleep_fn = sleep_fn or time.sleep
        self._random_fn = random_fn or random.random
        self._window_seconds = window_seconds
        self._restore_after_successes = restore_after_successes
        self._concurrency_poll_seconds = concurrency_poll_seconds
        self._reservation_counter = 0

    def upsert_profiles(self, profiles: list[ModelRateLimitProfile]) -> None:
        """Add or replace profiles by provider/model key."""
        for profile in profiles:
            self._profiles[profile.key] = profile

    def acquire(
        self,
        provider: str,
        model: str,
        *,
        estimated_input_tokens: int,
        max_output_tokens: int,
    ) -> RateLimitReservation:
        """Block until RPM/TPM budget and concurrency are available."""
        profile = self._resolve_profile(provider, model)
        state = self._get_state(profile)
        waited_seconds = 0.0
        estimated_total_tokens = max(0, estimated_input_tokens) + max(0, max_output_tokens)

        while True:
            now = self._clock()
            self._purge_expired(state, now)
            wait_seconds = self._compute_wait_seconds(state, profile, estimated_total_tokens, now)
            if wait_seconds <= 0:
                break
            self._sleep_fn(wait_seconds)
            waited_seconds += wait_seconds

        now = self._clock()
        reservation = RateLimitReservation(
            reservation_id=self._next_reservation_id(),
            provider=profile.provider,
            model=profile.model,
            estimated_input_tokens=max(0, estimated_input_tokens),
            max_output_tokens=max(0, max_output_tokens),
            estimated_total_tokens=estimated_total_tokens,
            acquired_at=now,
            waited_seconds=waited_seconds,
        )
        state.request_timestamps.append(now)
        state.token_events.append(
            _TokenEvent(
                timestamp=now,
                tokens=estimated_total_tokens,
                reservation_id=reservation.reservation_id,
            )
        )
        state.active_reservations.add(reservation.reservation_id)
        state.in_flight += 1
        self._reservations[reservation.reservation_id] = reservation
        self._update_moving_averages(state)
        return reservation

    def record_success(
        self,
        reservation: RateLimitReservation | str,
        *,
        actual_input_tokens: int | None = None,
        actual_output_tokens: int | None = None,
    ) -> RateLimitSnapshot:
        """Finalize a successful request and optionally reconcile token estimate."""
        reservation = self._coerce_reservation(reservation)
        profile = self._resolve_profile(reservation.provider, reservation.model)
        state = self._get_state(profile)
        actual_total_tokens = reservation.estimated_total_tokens
        if actual_input_tokens is not None or actual_output_tokens is not None:
            actual_total_tokens = max(0, actual_input_tokens or 0) + max(
                0, actual_output_tokens or 0
            )
            self._update_token_event(state, reservation.reservation_id, actual_total_tokens)

        self._release_reservation(state, reservation.reservation_id)
        if state.current_concurrency_cap < profile.concurrency_cap:
            state.success_streak += 1
            if state.success_streak >= self._restore_after_successes:
                state.current_concurrency_cap += 1
                state.success_streak = 0
        self._update_moving_averages(state)
        _ = actual_total_tokens
        return self.snapshot(profile.provider, profile.model)

    def record_rate_limit(
        self,
        reservation: RateLimitReservation | str,
        error: object,
        *,
        attempt: int,
    ) -> float:
        """Apply concurrency reduction and return the delay before retry."""
        reservation = self._coerce_reservation(reservation)
        profile = self._resolve_profile(reservation.provider, reservation.model)
        state = self._get_state(profile)
        self._release_reservation(state, reservation.reservation_id)
        state.success_streak = 0
        state.current_concurrency_cap = max(1, math.ceil(state.current_concurrency_cap / 2))
        self._update_moving_averages(state)
        return compute_retry_delay(error, attempt, random_fn=self._random_fn)

    def get_reservation(self, reservation_id: str) -> RateLimitReservation:
        """Get an active reservation by identifier."""
        if reservation_id not in self._reservations:
            raise KeyError(f"Unknown reservation id: {reservation_id}")
        return self._reservations[reservation_id]

    def snapshot(self, provider: str, model: str) -> RateLimitSnapshot:
        """Get rolling-window and concurrency state for a provider/model."""
        profile = self._resolve_profile(provider, model)
        state = self._get_state(profile)
        self._purge_expired(state, self._clock())
        rolling_requests = len(state.request_timestamps)
        rolling_tokens = sum(event.tokens for event in state.token_events)
        self._update_moving_averages(state)
        return RateLimitSnapshot(
            provider=profile.provider,
            model=profile.model,
            rpm_limit=profile.rpm_limit,
            tpm_limit=profile.tpm_limit,
            effective_rpm_limit=profile.effective_rpm_limit,
            effective_tpm_limit=profile.effective_tpm_limit,
            rolling_request_count=rolling_requests,
            rolling_token_count=rolling_tokens,
            moving_average_requests=state.moving_average_requests,
            moving_average_tokens=state.moving_average_tokens,
            request_utilization=rolling_requests / profile.effective_rpm_limit,
            token_utilization=rolling_tokens / profile.effective_tpm_limit,
            base_concurrency_cap=profile.concurrency_cap,
            current_concurrency_cap=state.current_concurrency_cap,
            in_flight=state.in_flight,
            rpm_ema=state.rpm_ema,
            tpm_ema=state.tpm_ema,
            dynamic_concurrency=state.current_concurrency_cap,
        )

    # ── Glossa-Lab-style convenience API (REQ-272..REQ-274) ──────────────

    def on_rate_limit(self, model: str, error: object, attempt: int) -> float:
        """Decrease dynamic concurrency by 1 and return suggested retry delay.

        Conforms to the glossa-lab AIModelPacer.on_rate_limit() contract:
        - Decreases dynamic_concurrency by 1 (minimum 1)
        - Sets ``reduced_until`` to now + 120 s so concurrency can be
          restored by ``_maybe_restore_concurrency``
        - Returns a float delay (seconds) for the caller to sleep
        """
        try:
            profile = self._resolve_profile("*", model)
        except KeyError:
            profile = next(iter(self._profiles.values())) if self._profiles else None
            if profile is None:
                return min(30.0, 2**attempt)
        state = self._get_state(profile)
        now = self._clock()
        state.current_concurrency_cap = max(1, state.current_concurrency_cap - 1)
        state.reduced_until = now + 120.0
        retry_after = parse_retry_after_seconds(str(error))
        base = retry_after if retry_after is not None else min(30.0, 2**attempt)
        import random as _random  # noqa: PLC0415

        jitter = _random.uniform(0.0, max(0.25, base * 0.25))
        return base + jitter

    def estimate_request_tokens(
        self,
        *,
        provider: str = "*",
        model: str = "*",
        prompt: str | None = None,
        messages: list[dict[str, object]] | None = None,
        max_output_tokens: int = 0,
        image_count: int = 0,
        image_token_estimate: int = _DEFAULT_IMAGE_TOKEN_ESTIMATE,
    ) -> int:
        """Estimate total token reservation for a request (REQ-274).

        Includes text tokens (approx. 4 chars/token), image tokens
        (``image_count × image_token_estimate``), and ``max_output_tokens``.
        """
        estimate = 0
        if prompt:
            estimate += max(1, math.ceil(len(prompt) / 4))
        if messages:
            for msg in messages:
                content = msg.get("content", "")
                if isinstance(content, str):
                    estimate += max(1, math.ceil(len(content) / 4)) + 8
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") in ("image_url", "input_image"):
                                estimate += image_token_estimate
                            else:
                                estimate += max(1, math.ceil(len(str(item.get("text", item))) / 4))
        estimate += image_count * image_token_estimate
        return estimate + max_output_tokens

    def _resolve_profile(self, provider: str, model: str) -> ModelRateLimitProfile:
        provider = _normalize_key_part(provider)
        model = _normalize_key_part(model)
        exact_key = _profile_key(provider, model)
        if exact_key in self._profiles:
            return self._profiles[exact_key]

        for wildcard_key in (
            _profile_key(provider, "*"),
            _profile_key("*", model),
            _profile_key("*", "*"),
        ):
            if wildcard_key in self._profiles:
                return self._profiles[wildcard_key]

        raise KeyError(f"No rate-limit profile configured for {provider}/{model}")

    def _get_state(self, profile: ModelRateLimitProfile) -> _ModelRuntimeState:
        if profile.key not in self._states:
            self._states[profile.key] = _ModelRuntimeState(
                current_concurrency_cap=profile.concurrency_cap
            )
        return self._states[profile.key]

    def _compute_wait_seconds(
        self,
        state: _ModelRuntimeState,
        profile: ModelRateLimitProfile,
        estimated_total_tokens: int,
        now: float,
    ) -> float:
        request_wait = 0.0
        if len(state.request_timestamps) + 1 > profile.effective_rpm_limit:
            oldest_request = state.request_timestamps[0]
            request_wait = max(0.0, oldest_request + self._window_seconds - now)

        token_wait = self._compute_token_wait_seconds(
            state=state,
            token_limit=profile.effective_tpm_limit,
            estimated_total_tokens=estimated_total_tokens,
            now=now,
        )

        concurrency_wait = (
            self._concurrency_poll_seconds
            if state.in_flight >= state.current_concurrency_cap
            else 0.0
        )
        return max(request_wait, token_wait, concurrency_wait)

    def _compute_token_wait_seconds(
        self,
        *,
        state: _ModelRuntimeState,
        token_limit: int,
        estimated_total_tokens: int,
        now: float,
    ) -> float:
        current_tokens = sum(event.tokens for event in state.token_events)
        if current_tokens + estimated_total_tokens <= token_limit:
            return 0.0

        tokens_to_free = current_tokens + estimated_total_tokens - token_limit
        freed_tokens = 0
        wait_seconds = 0.0
        for event in state.token_events:
            freed_tokens += event.tokens
            wait_seconds = max(0.0, event.timestamp + self._window_seconds - now)
            if freed_tokens >= tokens_to_free:
                return wait_seconds
        return self._window_seconds

    def _purge_expired(self, state: _ModelRuntimeState, now: float) -> None:
        cutoff = now - self._window_seconds
        while state.request_timestamps and state.request_timestamps[0] <= cutoff:
            state.request_timestamps.popleft()
        while state.token_events and state.token_events[0].timestamp <= cutoff:
            state.token_events.popleft()

    def _release_reservation(self, state: _ModelRuntimeState, reservation_id: str) -> None:
        if reservation_id in state.active_reservations:
            state.active_reservations.remove(reservation_id)
            state.in_flight = max(0, state.in_flight - 1)
        self._reservations.pop(reservation_id, None)

    def _update_token_event(
        self,
        state: _ModelRuntimeState,
        reservation_id: str,
        actual_total_tokens: int,
    ) -> None:
        for event in state.token_events:
            if event.reservation_id == reservation_id:
                event.tokens = actual_total_tokens
                break

    def _update_moving_averages(self, state: _ModelRuntimeState) -> None:
        current_requests = float(len(state.request_timestamps))
        current_tokens = float(sum(event.tokens for event in state.token_events))
        state.moving_average_requests = (_MOVING_AVERAGE_ALPHA * current_requests) + (
            (1 - _MOVING_AVERAGE_ALPHA) * state.moving_average_requests
        )
        state.moving_average_tokens = (_MOVING_AVERAGE_ALPHA * current_tokens) + (
            (1 - _MOVING_AVERAGE_ALPHA) * state.moving_average_tokens
        )
        # Normalised EMA utilisation (REQ-272)
        for profile in self._profiles.values():
            if self._get_state(profile) is state:
                if profile.rpm_limit > 0:
                    rpm_util = current_requests / profile.rpm_limit
                    state.rpm_ema = (
                        rpm_util
                        if state.rpm_ema == 0
                        else _MOVING_AVERAGE_ALPHA * rpm_util
                        + (1 - _MOVING_AVERAGE_ALPHA) * state.rpm_ema
                    )
                if profile.tpm_limit > 0:
                    tpm_util = current_tokens / profile.tpm_limit
                    state.tpm_ema = (
                        tpm_util
                        if state.tpm_ema == 0
                        else _MOVING_AVERAGE_ALPHA * tpm_util
                        + (1 - _MOVING_AVERAGE_ALPHA) * state.tpm_ema
                    )
                break

    def _next_reservation_id(self) -> str:
        self._reservation_counter += 1
        return f"reservation-{self._reservation_counter}"

    def export_state(self) -> dict[str, object]:
        """Serialize the scheduler state for persistence."""
        now = self._clock()
        states: dict[str, object] = {}
        for key, state in self._states.items():
            self._purge_expired(state, now)
            self._update_moving_averages(state)
            states[key] = {
                "request_timestamps": list(state.request_timestamps),
                "token_events": [
                    {
                        "timestamp": event.timestamp,
                        "tokens": event.tokens,
                        "reservation_id": event.reservation_id,
                    }
                    for event in state.token_events
                ],
                "active_reservations": sorted(state.active_reservations),
                "in_flight": state.in_flight,
                "current_concurrency_cap": state.current_concurrency_cap,
                "success_streak": state.success_streak,
                "moving_average_requests": state.moving_average_requests,
                "moving_average_tokens": state.moving_average_tokens,
            }

        return {
            "states": states,
            "reservations": {
                reservation_id: asdict(reservation)
                for reservation_id, reservation in self._reservations.items()
            },
            "reservation_counter": self._reservation_counter,
        }

    def import_state(self, data: dict[str, object]) -> None:
        """Restore scheduler state from persistence."""
        self._states = {}
        raw_states = data.get("states", {})
        if isinstance(raw_states, dict):
            for key, raw_state in raw_states.items():
                if not isinstance(raw_state, dict):
                    continue
                token_events: deque[_TokenEvent] = deque()
                for raw_event in raw_state.get("token_events", []):
                    if not isinstance(raw_event, dict):
                        continue
                    token_events.append(
                        _TokenEvent(
                            timestamp=float(raw_event["timestamp"]),
                            tokens=int(raw_event["tokens"]),
                            reservation_id=str(raw_event["reservation_id"]),
                        )
                    )
                self._states[str(key)] = _ModelRuntimeState(
                    request_timestamps=deque(
                        float(timestamp) for timestamp in raw_state.get("request_timestamps", [])
                    ),
                    token_events=token_events,
                    active_reservations=set(
                        str(reservation_id)
                        for reservation_id in raw_state.get("active_reservations", [])
                    ),
                    in_flight=int(raw_state.get("in_flight", 0)),
                    current_concurrency_cap=int(raw_state.get("current_concurrency_cap", 0)),
                    success_streak=int(raw_state.get("success_streak", 0)),
                    moving_average_requests=float(raw_state.get("moving_average_requests", 0.0)),
                    moving_average_tokens=float(raw_state.get("moving_average_tokens", 0.0)),
                )

        self._reservations = {}
        raw_reservations = data.get("reservations", {})
        if isinstance(raw_reservations, dict):
            for reservation_id, raw_reservation in raw_reservations.items():
                if not isinstance(raw_reservation, dict):
                    continue
                reservation = RateLimitReservation(**raw_reservation)
                self._reservations[str(reservation_id)] = reservation

        reservation_counter = data.get("reservation_counter", 0)
        if isinstance(reservation_counter, int):
            self._reservation_counter = reservation_counter

    def _coerce_reservation(self, reservation: RateLimitReservation | str) -> RateLimitReservation:
        if isinstance(reservation, RateLimitReservation):
            return reservation
        return self.get_reservation(reservation)


def _extract_status_code(error: object) -> int | None:
    status_code = getattr(error, "status_code", None)
    if isinstance(status_code, int):
        return status_code

    response = getattr(error, "response", None)
    response_status = getattr(response, "status_code", None)
    if isinstance(response_status, int):
        return response_status
    return None


def _extract_headers(error: object) -> dict[str, str]:
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    if isinstance(headers, dict):
        return {str(k).lower(): str(v) for k, v in headers.items()}
    if isinstance(error, dict):
        raw_headers = error.get("headers")
        if isinstance(raw_headers, dict):
            return {str(k).lower(): str(v) for k, v in raw_headers.items()}
    return {}


def _extract_message(error: object) -> str:
    if isinstance(error, str):
        return error
    if isinstance(error, dict):
        parts: list[str] = []
        for key in ("message", "detail", "error"):
            value = error.get(key)
            if isinstance(value, str):
                parts.append(value)
        if parts:
            return " ".join(parts)
        return json.dumps(error)
    message = getattr(error, "message", None)
    if isinstance(message, str) and message:
        return message
    args = getattr(error, "args", ())
    if args:
        return " ".join(str(arg) for arg in args if arg)
    return str(error)


def _extract_error_code(error: object) -> str | None:
    if isinstance(error, dict):
        code = error.get("code")
        if isinstance(code, str):
            return code.lower()
    code = getattr(error, "code", None)
    if isinstance(code, str):
        return code.lower()
    return None


def _parse_retry_after_headers(headers: dict[str, str]) -> float | None:
    for key in ("retry-after", "retry-after-ms", "x-ratelimit-reset-after"):
        value = headers.get(key)
        if value is None:
            continue
        try:
            numeric = float(value)
        except ValueError:
            continue
        if key == "retry-after-ms":
            return numeric / 1000.0
        return numeric
    return None


def _parse_retry_after_message(message: str) -> float | None:
    for pattern in _WAIT_PATTERNS:
        match = pattern.search(message)
        if not match:
            continue
        value = float(match.group("value"))
        unit = match.group("unit").lower()
        if unit == "ms":
            return value / 1000.0
        return value
    return None


def load_rate_limit_scheduler(
    root: Path,
    profiles: list[ModelRateLimitProfile],
    *,
    clock: Callable[[], float] | None = None,
    sleep_fn: Callable[[float], None] | None = None,
    random_fn: Callable[[], float] | None = None,
    window_seconds: float = _ROLLING_WINDOW_SECONDS,
    restore_after_successes: int = 3,
    concurrency_poll_seconds: float = _CONCURRENCY_POLL_SECONDS,
) -> RateLimitScheduler:
    """Build a scheduler and hydrate any saved runtime state."""
    scheduler = RateLimitScheduler(
        profiles,
        clock=clock,
        sleep_fn=sleep_fn,
        random_fn=random_fn,
        window_seconds=window_seconds,
        restore_after_successes=restore_after_successes,
        concurrency_poll_seconds=concurrency_poll_seconds,
    )
    path = _get_runtime_state_path(root)
    if not path.exists():
        return scheduler

    try:
        raw_state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return scheduler

    if isinstance(raw_state, dict):
        scheduler.import_state(raw_state)
    return scheduler


def save_rate_limit_scheduler(root: Path, scheduler: RateLimitScheduler) -> None:
    """Persist current runtime scheduler state."""
    path = _get_runtime_state_path(root)
    path.write_text(json.dumps(scheduler.export_state(), indent=2), encoding="utf-8")


def parse_retry_after_seconds(message: str) -> float | None:
    """Extract retry delay from a provider error string.

    Matches patterns like ``"try again in 5s"`` or ``"retry in 30 seconds"``.
    Returns ``None`` when no match is found.
    """
    return _parse_retry_after_message(message)


# Alias for glossa-lab-style API compatibility (REQ-272..REQ-274)
ModelRateLimitScheduler = RateLimitScheduler
