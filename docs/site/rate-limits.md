# Provider rate-limit pacing

Specsmith's provider adapters can pace requests before a `429`, using rolling
request-per-minute and token-per-minute windows. This is supporting runtime
behavior for Grace and benchmarks, not a separate credit-management product.

The public CLI does not expose rate-limit administration. Prefer the coding
agent or provider dashboard for account limits. Grace reads configured endpoint
and provider settings automatically and reports actionable retry guidance.

Project-specific overrides may be stored in
`.specsmith/model-rate-limits.json`; runtime counters stay in
`.specsmith/model-rate-limit-state.json` and should remain untracked.

## Python API

```python
from pathlib import Path

from specsmith.rate_limits import BUILTIN_PROFILES, load_rate_limit_scheduler

scheduler = load_rate_limit_scheduler(Path("."), BUILTIN_PROFILES)
reservation = scheduler.acquire(
    "openai",
    "configured-model",
    estimated_input_tokens=5_000,
    max_output_tokens=2_000,
)

# After the provider call:
scheduler.record_success(
    reservation,
    actual_input_tokens=4_800,
    actual_output_tokens=1_900,
)
```

On a provider error, call `record_rate_limit`; it parses a provider wait hint,
reduces concurrency, and returns a bounded retry delay. Limits remain estimates:
the provider account is authoritative.
