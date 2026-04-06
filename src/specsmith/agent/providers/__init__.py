# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""LLM provider factory for the specsmith agentic client.

Provider priority (auto-detection order):
  1. SPECSMITH_PROVIDER env var (explicit override)
  2. ANTHROPIC_API_KEY present → Anthropic
  3. OPENAI_API_KEY present → OpenAI (also covers any OpenAI-compatible API)
  4. GOOGLE_API_KEY present → Gemini
  5. Ollama running on localhost:11434 → Ollama (local, no API key needed)
  6. Raise ProviderNotAvailable

All providers are optional. Install extras as needed:
    pip install specsmith[anthropic]   # Claude models
    pip install specsmith[openai]      # GPT / O-series + any OpenAI-compat
    pip install specsmith[agent]       # Both Anthropic + OpenAI
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from specsmith.agent.core import MODEL_DEFAULTS, ModelTier, ProviderNotAvailable

if TYPE_CHECKING:
    from specsmith.agent.core import BaseProvider


def get_provider(
    provider_name: str | None = None,
    model: str | None = None,
    tier: ModelTier = ModelTier.BALANCED,
    base_url: str | None = None,
    api_key: str | None = None,
) -> BaseProvider:
    """Get a configured LLM provider.

    Args:
        provider_name: "anthropic", "openai", "gemini", "mistral", "ollama", or None (auto-detect)
        model: specific model name, or None (use tier default)
        tier: ModelTier.FAST / BALANCED / POWERFUL
        base_url: override API base URL (for OpenAI-compatible proxies)
        api_key: override API key (otherwise reads from environment)

    Returns:
        A configured provider instance.

    Raises:
        ProviderNotAvailable: if the required SDK is not installed
    """
    if provider_name is None:
        provider_name = _auto_detect_provider()

    resolved_model = model or MODEL_DEFAULTS.get(provider_name, {}).get(tier, "")

    if provider_name == "anthropic":
        from specsmith.agent.providers.anthropic import AnthropicProvider

        return AnthropicProvider(
            model=resolved_model or "claude-sonnet-4-5",
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
        )
    elif provider_name == "openai":
        from specsmith.agent.providers.openai import OpenAIProvider

        return OpenAIProvider(
            model=resolved_model or "gpt-4o",
            api_key=api_key or os.environ.get("OPENAI_API_KEY", ""),
            base_url=base_url or os.environ.get("OPENAI_BASE_URL", ""),
        )
    elif provider_name == "gemini":
        from specsmith.agent.providers.gemini import GeminiProvider

        return GeminiProvider(
            model=resolved_model or "gemini-2.5-pro",
            api_key=api_key or os.environ.get("GOOGLE_API_KEY", ""),
        )
    elif provider_name == "mistral":
        from specsmith.agent.providers.mistral import MistralProvider

        return MistralProvider(
            model=resolved_model or "mistral-large-latest",
            api_key=api_key or os.environ.get("MISTRAL_API_KEY", ""),
        )
    elif provider_name == "ollama":
        from specsmith.agent.providers.ollama import OllamaProvider

        return OllamaProvider(
            model=resolved_model or "qwen2.5:14b",
            base_url=base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
    else:
        raise ValueError(
            f"Unknown provider '{provider_name}'. Valid: anthropic, openai, gemini, mistral, ollama"
        )


def _auto_detect_provider() -> str:
    """Detect available provider from environment variables."""
    explicit = os.environ.get("SPECSMITH_PROVIDER", "").strip().lower()
    if explicit:
        return explicit

    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    if os.environ.get("MISTRAL_API_KEY"):
        return "mistral"

    # Try Ollama (no API key needed)
    import urllib.request

    try:
        urllib.request.urlopen(  # noqa: S310
            "http://localhost:11434/api/version", timeout=1
        )
        return "ollama"
    except Exception:  # noqa: BLE001
        pass

    raise ProviderNotAvailable(
        "auto",
        "anthropic` or `specsmith[openai]` or `specsmith[gemini]",
    )


def list_providers() -> list[dict[str, str]]:
    """Return a list of providers with their availability status."""
    providers = []
    for name, key_env in [
        ("anthropic", "ANTHROPIC_API_KEY"),
        ("openai", "OPENAI_API_KEY"),
        ("gemini", "GOOGLE_API_KEY"),
        ("mistral", "MISTRAL_API_KEY"),
        ("ollama", ""),
    ]:
        if name == "ollama":
            import urllib.request

            try:
                urllib.request.urlopen(  # noqa: S310
                    "http://localhost:11434/api/version", timeout=1
                )
                status = "available (local)"
            except Exception:  # noqa: BLE001
                status = "not running"
        else:
            key_val = os.environ.get(key_env, "")
            status = "configured" if key_val else "no API key"
        providers.append({"name": name, "status": status})
    return providers
