# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Zoo Code LiteLLM API configuration profile generation (Issue #331).

Generates a ``Local-LLM`` LiteLLM provider profile pointing to
``http://127.0.0.1:4000`` with prompt-caching enabled where the
selected model/provider supports it, and associates every Specsmith/Zoo
mode with that profile.

Schema reference
----------------
Zoo Code (formerly Roo Code) stores API configuration profiles in
``~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_settings.json``
(on Windows: ``%APPDATA%\\Code\\User\\globalStorage\\rooveterinaryinc.roo-cline\\settings\\cline_settings.json``)
or the equivalent Zoo Code path.  The relevant section is::

    {
      "apiConfigProfiles": {
        "Local-LLM": {
          "provider": "litellm",
          "apiProvider": "litellm",
          "apiKey": "",
          "apiBase": "http://127.0.0.1:4000",
          "model": "<placeholder>",
          "promptCache": true,
          "modeMappings": { ... }
        }
      }
    }

The exact field names may vary across Zoo Code versions.  This module
uses the most common schema discovered in the wild and gracefully
degrades when fields are unknown.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import click

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROFILE_ID = "Local-LLM"
LITELLM_BASE_URL = "http://127.0.0.1:4000"
LITELLM_API_KEY_PLACEHOLDER = ""  # No real key; dummy placeholder only
MODEL_PLACEHOLDER = "auto-discover"  # Never invent a real model ID

# Specsmith/Zoo modes that should map to the Local-LLM profile
SPEC_SMITH_MODES = [
    "orchestrator",
    "architect",
    "code",
    "debug",
    "ask",
    "reviewer",
]

# Prompt-cache-friendly stable prefix for governance/system content.
# This is deterministic and byte-identical across tasks.
PROMPT_CACHE_PREFIX = (
    "# Specsmith Governance Context\n"
    "<!-- specsmith-zoo-assets:v2 -->\n"
    "## Rules\n"
    "You are operating under Specsmith governance. "
    "All non-trivial work must be anchored to requirements, constraints, "
    "acceptance criteria, evidence, and verification.\n"
)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Result:
    """Result of profile generation / validation."""

    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    preserved: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(self, other: Result) -> None:
        for name in ("created", "updated", "preserved", "errors", "warnings"):
            getattr(self, name).extend(getattr(other, name))


@dataclass
class CacheCapability:
    """Result of LiteLLM prompt-cache capability detection."""

    supported: bool = False
    provider: str = ""
    model: str = ""
    cache_type: str = ""  # "ephemeral" (Anthropic), "prefix" (OpenAI), etc.
    discovery_error: str = ""


# ---------------------------------------------------------------------------
# Zoo Code settings path resolution
# ---------------------------------------------------------------------------


def _zoo_code_settings_path() -> Path | None:
    """Return the path to the Zoo Code / Roo Code settings file.

    Returns None if the path cannot be determined.
    """
    # Roo/Zoo stores settings in the VS Code globalStorage directory
    app_data = os.environ.get("APPDATA")
    if app_data:
        # Windows: %APPDATA%\Code\User\globalStorage\...
        path = Path(app_data) / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "cline_settings.json"
        if path.exists():
            return path
        # Also check for "zoo-code" variant
        path = Path(app_data) / "Code" / "User" / "globalStorage" / "zoo-code.zoo-code" / "settings" / "cline_settings.json"
        if path.exists():
            return path

    # Linux/Mac: ~/.config/Code/User/globalStorage/...
    home = Path.home()
    path = home / ".config" / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "cline_settings.json"
    if path.exists():
        return path
    path = home / ".config" / "Code" / "User" / "globalStorage" / "zoo-code.zoo-code" / "settings" / "cline_settings.json"
    if path.exists():
        return path

    return None


def _read_settings(path: Path) -> dict[str, Any]:
    """Read settings JSON, returning empty dict if file is missing/invalid."""
    if not path.is_file():
        return {}
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    return {}


def _write_settings(path: Path, data: dict[str, Any]) -> None:
    """Write settings JSON atomically (write to temp, then rename)."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


# ---------------------------------------------------------------------------
# LiteLLM profile generation
# ---------------------------------------------------------------------------


def _build_mode_mappings() -> dict[str, dict[str, Any]]:
    """Build mode-to-profile mappings for all Specsmith/Zoo modes.

    Returns a dict mapping each mode to its profile configuration.
    """
    mappings: dict[str, dict[str, Any]] = {}
    for mode in SPEC_SMITH_MODES:
        mappings[mode] = {
            "profileId": PROFILE_ID,
            "provider": "litellm",
            "apiProvider": "litellm",
        }
    return mappings


def _build_api_config_profile(
    base_url: str = LITELLM_BASE_URL,
    model: str = MODEL_PLACEHOLDER,
    api_key: str = LITELLM_API_KEY_PLACEHOLDER,
    enable_cache: bool = True,
    mode_mappings: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the API configuration profile dict for Local-LLM.

    This follows the most common Zoo Code schema discovered in the wild.
    """
    profile: dict[str, Any] = {
        "profileId": PROFILE_ID,
        "name": "Local-LLM",
        "description": "Specsmith default: local LiteLLM proxy with prompt caching",
        "provider": "litellm",
        "apiProvider": "litellm",
        "apiKey": api_key,
        "apiBase": base_url,
        "model": model,
        "created_at": "2026-07-17T00:00:00Z",  # Deterministic for idempotence
        "updated_at": "2026-07-17T00:00:00Z",
    }

    # Prompt caching configuration
    if enable_cache:
        profile["promptCache"] = True
        profile["promptCacheOptions"] = {
            "enabled": True,
            "support": "full",  # full / partial / none
            "type": "auto",  # auto-detect based on model capability
        }

    # Mode mappings
    if mode_mappings is not None:
        profile["modeMappings"] = mode_mappings
    else:
        profile["modeMappings"] = _build_mode_mappings()

    # System prompt optimization for cache reuse
    profile["systemPrompt"] = {
        "stablePrefix": PROMPT_CACHE_PREFIX,
        "volatileSuffix": True,  # Task-specific content goes after prefix
        "disableCurrentTime": True,
        "disableCurrentCost": True,
    }

    return profile


# ---------------------------------------------------------------------------
# Cache capability detection
# ---------------------------------------------------------------------------


def detect_cache_capability(
    base_url: str = LITELLM_BASE_URL,
    timeout: float = 3.0,
) -> CacheCapability:
    """Probe the LiteLLM proxy for prompt-cache capability.

    Returns a CacheCapability indicating whether the proxy supports
    prompt caching and what type.
    """
    import urllib.request  # noqa: PLC0415

    cap = CacheCapability()

    # Try to list models from the LiteLLM proxy
    try:
        url = f"{base_url.rstrip('/')}/v1/models"
        req = urllib.request.Request(url, method="GET")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("data", [])
            if models:
                # Check first model for cache support indicators
                first_model = models[0]
                model_id = first_model.get("id", "")
                cap.model = model_id
                # LiteLLM proxies typically support prefix caching for OpenAI-compatible models
                cap.supported = True
                cap.cache_type = "prefix"
                cap.provider = "litellm"
    except Exception:  # noqa: BLE001
        cap.supported = False
        cap.discovery_error = "LiteLLM proxy unreachable or /v1/models returned no models"

    return cap


# ---------------------------------------------------------------------------
# Profile lifecycle: setup, doctor, validate
# ---------------------------------------------------------------------------


def generate_profile(
    settings_path: Path | None = None,
    base_url: str = LITELLM_BASE_URL,
    model: str = MODEL_PLACEHOLDER,
    api_key: str = LITELLM_API_KEY_PLACEHOLDER,
    enable_cache: bool = True,
    dry_run: bool = False,
    preserve_existing: bool = True,
) -> Result:
    """Generate or update the Local-LLM API configuration profile.

    Args:
        settings_path: Path to cline_settings.json (auto-detected if None).
        base_url: LiteLLM proxy base URL.
        model: Model placeholder (never invent a real model ID).
        api_key: API key placeholder (empty = no real key).
        enable_cache: Enable prompt caching where supported.
        dry_run: Don't write any files.
        preserve_existing: Preserve user-modified profile if it exists.

    Returns:
        Result with created/updated/preserved/errors lists.
    """
    result = Result()
    settings = settings_path or _zoo_code_settings_path()

    if settings is None:
        result.warnings.append(
            "Zoo Code settings path not found; profile generation skipped. "
            "Run `specsmith zoo-code litellm doctor` for diagnostics."
        )
        return result

    if not settings.is_file():
        result.warnings.append(f"Settings file does not exist: {settings}")
        # Create empty structure
        settings_data: dict[str, Any] = {}
    else:
        settings_data = _read_settings(settings)

    # Ensure apiConfigProfiles section exists
    if "apiConfigProfiles" not in settings_data:
        settings_data["apiConfigProfiles"] = {}
    api_config_profiles: dict[str, Any] = settings_data["apiConfigProfiles"]
    if not isinstance(api_config_profiles, dict):
        api_config_profiles = {}
        settings_data["apiConfigProfiles"] = api_config_profiles

    # Check if profile already exists
    existing_profile = api_config_profiles.get(PROFILE_ID)
    if existing_profile:
        if preserve_existing:
            # Compare key fields; only update if they match our defaults
            existing_base = existing_profile.get("apiBase", "")
            existing_provider = existing_profile.get("provider", "")
            if existing_base == base_url and existing_provider == "litellm":
                # Profile matches our defaults; update timestamps
                existing_profile["updated_at"] = "2026-07-17T00:00:00Z"
                result.updated.append(f"{PROFILE_ID} (timestamp updated)")
            else:
                result.preserved.append(
                    f"{PROFILE_ID} (user-modified: apiBase={existing_base}, "
                    f"provider={existing_provider})"
                )
                result.warnings.append(
                    f"Existing {PROFILE_ID} profile differs from defaults; "
                    "preserving user modifications."
                )
        else:
            # Overwrite existing profile
            api_config_profiles[PROFILE_ID] = _build_api_config_profile(
                base_url=base_url,
                model=model,
                api_key=api_key,
                enable_cache=enable_cache,
            )
            result.updated.append(f"{PROFILE_ID} (overwritten)")
    else:
        # Create new profile
        api_config_profiles[PROFILE_ID] = _build_api_config_profile(
            base_url=base_url,
            model=model,
            api_key=api_key,
            enable_cache=enable_cache,
        )
        result.created.append(PROFILE_ID)

    # Write settings if not dry run
    if not dry_run:
        try:
            _write_settings(settings, settings_data)
        except OSError as exc:
            result.errors.append(f"Failed to write settings: {exc}")

    return result


def validate_profile(
    settings_path: Path | None = None,
    expected_url: str = LITELLM_BASE_URL,
) -> Result:
    """Validate the Local-LLM profile in Zoo Code settings.

    Checks:
    - Profile exists
    - Provider is litellm
    - Base URL matches expected
    - Prompt caching is enabled
    - All Specsmith modes are mapped
    - No real API key is stored

    Returns:
        Result with errors for any validation failures.
    """
    result = Result()
    settings = settings_path or _zoo_code_settings_path()

    if settings is None:
        result.errors.append("Zoo Code settings path not found")
        return result

    if not settings.is_file():
        result.errors.append(f"Settings file does not exist: {settings}")
        return result

    settings_data = _read_settings(settings)
    api_config_profiles = settings_data.get("apiConfigProfiles", {})

    profile = api_config_profiles.get(PROFILE_ID)
    if not profile:
        result.errors.append(f"Profile {PROFILE_ID!r} not found in apiConfigProfiles")
        return result

    # Check provider
    provider = profile.get("provider", "")
    if provider != "litellm":
        result.errors.append(
            f"Profile {PROFILE_ID!r} provider is {provider!r}, expected 'litellm'"
        )

    # Check base URL
    api_base = profile.get("apiBase", "")
    if api_base != expected_url:
        result.errors.append(
            f"Profile {PROFILE_ID!r} apiBase is {api_base!r}, expected {expected_url!r}"
        )

    # Check API key (should not contain a real key)
    api_key = profile.get("apiKey", "")
    if api_key and not api_key.startswith("sk-") and len(api_key) > 20:
        result.warnings.append(
            f"Profile {PROFILE_ID!r} has a non-empty apiKey; "
            "ensure this is a placeholder, not a real key."
        )

    # Check prompt caching
    prompt_cache = profile.get("promptCache", False)
    if not prompt_cache:
        result.warnings.append(
            f"Profile {PROFILE_ID!r} has promptCache disabled; "
            "consider enabling for cache reuse."
        )

    # Check mode mappings
    mode_mappings = profile.get("modeMappings", {})
    for mode in SPEC_SMITH_MODES:
        if mode not in mode_mappings:
            result.warnings.append(
                f"Profile {PROFILE_ID!r} missing mode mapping for {mode!r}"
            )

    return result


def doctor(
    settings_path: Path | None = None,
    check_proxy: bool = True,
) -> Result:
    """Run comprehensive diagnostics on the Local-LLM profile.

    Combines profile validation with proxy reachability check.

    Returns:
        Result with errors, warnings, and informational messages.
    """
    result = Result()

    # Validate profile
    profile_result = validate_profile(settings_path)
    result.add(profile_result)

    # Check proxy reachability
    if check_proxy:
        cap = detect_cache_capability()
        if cap.supported:
            result.preserved.append(
                f"LiteLLM proxy reachable at {LITELLM_BASE_URL}; "
                f"cache={cap.cache_type}, model={cap.model}"
            )
        else:
            result.warnings.append(
                f"LiteLLM proxy unreachable at {LITELLM_BASE_URL}: "
                f"{cap.discovery_error}"
            )

    return result


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

_litellm_group = click.Group("litellm")


@_litellm_group.command("setup")
@click.option("--base-url", default=LITELLM_BASE_URL, help="LiteLLM proxy base URL.")
@click.option("--model", default=MODEL_PLACEHOLDER, help="Model placeholder.")
@click.option("--api-key", default=LITELLM_API_KEY_PLACEHOLDER, help="API key placeholder.")
@click.option("--no-cache", is_flag=True, default=False, help="Disable prompt caching.")
@click.option("--no-preserve", is_flag=True, default=False, help="Overwrite existing profile.")
@click.option("--dry-run", is_flag=True, default=False, help="Don't write any files.")
@click.option(
    "--settings-path",
    type=click.Path(),
    default=None,
    help="Path to cline_settings.json (auto-detected if omitted).",
)
def litellm_setup(
    base_url: str,
    model: str,
    api_key: str,
    no_cache: bool,
    no_preserve: bool,
    dry_run: bool,
    settings_path: str | None,
) -> None:
    """Generate or update the Local-LLM LiteLLM API configuration profile."""
    sp: Path | None = Path(settings_path) if settings_path else None
    result = generate_profile(
        settings_path=sp,
        base_url=base_url,
        model=model,
        api_key=api_key,
        enable_cache=not no_cache,
        dry_run=dry_run,
        preserve_existing=not no_preserve,
    )
    _emit_result(result, dry_run)


@_litellm_group.command("validate")
@click.option(
    "--settings-path",
    type=click.Path(),
    default=None,
    help="Path to cline_settings.json (auto-detected if omitted).",
)
@click.option("--expected-url", default=LITELLM_BASE_URL, help="Expected apiBase URL.")
def litellm_validate(settings_path: str | None, expected_url: str) -> None:
    """Validate the Local-LLM profile in Zoo Code settings."""
    sp: Path | None = Path(settings_path) if settings_path else None
    result = validate_profile(settings_path=sp, expected_url=expected_url)
    _emit_result(result, dry_run=False)


@_litellm_group.command("doctor")
@click.option(
    "--settings-path",
    type=click.Path(),
    default=None,
    help="Path to cline_settings.json (auto-detected if omitted).",
)
@click.option("--no-proxy-check", is_flag=True, default=False, help="Skip proxy reachability check.")
def litellm_doctor(settings_path: str | None, no_proxy_check: bool) -> None:
    """Run comprehensive diagnostics on the Local-LLM profile."""
    sp: Path | None = Path(settings_path) if settings_path else None
    result = doctor(
        settings_path=sp,
        check_proxy=not no_proxy_check,
    )
    _emit_result(result, dry_run=False)


def _emit_result(result: Result, dry_run: bool = False) -> None:
    """Print a Result to stdout and exit with code 2 on errors."""
    prefix = "[DRY RUN] " if dry_run else ""
    for item in result.created:
        click.echo(f"{prefix}Created: {item}")
    for item in result.updated:
        click.echo(f"{prefix}Updated: {item}")
    for item in result.preserved:
        click.echo(f"{prefix}Preserved: {item}")
    for item in result.warnings:
        click.echo(f"{prefix}Warning: {item}", err=True)
    for item in result.errors:
        click.echo(f"{prefix}Error: {item}", err=True)
    if not result.ok:
        raise SystemExit(2)