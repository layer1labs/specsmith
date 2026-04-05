# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Auth — secure API key management for platform integrations.

Priority order for credential resolution:
  1. Environment variables (CI-friendly, always checked first)
  2. OS keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service)
  3. Encrypted config file fallback (~/.specsmith/credentials)

Security rules (never violated):
  - Tokens NEVER written to logs, ledger, or governance files
  - Tokens NEVER passed as CLI arguments (prompted or read from env/keyring)
  - Token values NEVER printed; only masked versions shown

Resolves GitHub issue #37.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Platform definitions
# ---------------------------------------------------------------------------

PLATFORMS = {
    "readthedocs": {
        "env_var": "SPECSMITH_RTD_TOKEN",
        "description": "ReadTheDocs API v3 token",
        "url": "https://readthedocs.org/accounts/tokens/",
    },
    "pypi": {
        "env_var": "SPECSMITH_PYPI_TOKEN",
        "description": "PyPI API token",
        "url": "https://pypi.org/manage/account/token/",
    },
    "testpypi": {
        "env_var": "SPECSMITH_TESTPYPI_TOKEN",
        "description": "TestPyPI API token",
        "url": "https://test.pypi.org/manage/account/token/",
    },
    "github": {
        "env_var": "SPECSMITH_GITHUB_TOKEN",
        "description": "GitHub personal access token",
        "url": "https://github.com/settings/tokens",
    },
    "gitlab": {
        "env_var": "SPECSMITH_GITLAB_TOKEN",
        "description": "GitLab personal access token",
        "url": "https://gitlab.com/-/profile/personal_access_tokens",
    },
    "uspto": {
        "env_var": "USPTO_API_KEY",
        "description": "USPTO Open Data Portal API key",
        "url": "https://developer.uspto.gov/",
    },
}

_KEYRING_SERVICE = "specsmith"
_CREDS_FILE = Path.home() / ".specsmith" / "credentials.json"


# ---------------------------------------------------------------------------
# Credential resolution
# ---------------------------------------------------------------------------


def get_token(platform: str) -> str | None:
    """Resolve a token for a platform.

    Priority: env var → OS keyring → encrypted file.
    Returns None if no token is found.
    """
    platform = platform.lower()
    info = PLATFORMS.get(platform)

    # 1. Environment variable (CI-friendly)
    env_var = info["env_var"] if info else f"SPECSMITH_{platform.upper()}_TOKEN"
    token = os.environ.get(env_var, "").strip()
    if token:
        return token

    # 2. OS keyring
    keyring_token = _keyring_get(platform)
    if keyring_token:
        return keyring_token

    # 3. File fallback
    return _file_get(platform)


def set_token(platform: str, token: str) -> str:
    """Store a token for a platform. Returns the storage method used."""
    platform = platform.lower()

    # Try OS keyring first
    if _keyring_set(platform, token):
        return "keyring"

    # Fall back to encrypted file
    _file_set(platform, token)
    return "file"


def remove_token(platform: str) -> bool:
    """Remove a stored token. Returns True if something was removed."""
    platform = platform.lower()
    removed = False
    if _keyring_delete(platform):
        removed = True
    if _file_delete(platform):
        removed = True
    return removed


def list_configured() -> list[dict[str, str]]:
    """List all platforms with their configuration status."""
    result = []
    for name, info in PLATFORMS.items():
        token = get_token(name)
        if token:
            source = _detect_source(name, token)
            masked = _mask_token(token)
            result.append(
                {
                    "platform": name,
                    "status": "configured",
                    "source": source,
                    "masked": masked,
                    "description": info["description"],
                }
            )
        else:
            result.append(
                {
                    "platform": name,
                    "status": "not set",
                    "source": "",
                    "masked": "",
                    "description": info["description"],
                }
            )
    return result


def check_required(platforms: list[str]) -> dict[str, bool]:
    """Check which of the given platforms have tokens configured."""
    return {p: get_token(p) is not None for p in platforms}


# ---------------------------------------------------------------------------
# OS keyring helpers
# ---------------------------------------------------------------------------


def _keyring_get(platform: str) -> str | None:
    try:
        import keyring  # type: ignore[import]

        value = keyring.get_password(_KEYRING_SERVICE, platform)  # type: ignore[no-any-return]
        return str(value) if value else None
    except Exception:  # noqa: BLE001
        return None


def _keyring_set(platform: str, token: str) -> bool:
    try:
        import keyring  # type: ignore[import]

        keyring.set_password(_KEYRING_SERVICE, platform, token)  # type: ignore[no-untyped-call]
        return True
    except Exception:  # noqa: BLE001
        return False


def _keyring_delete(platform: str) -> bool:
    try:
        import keyring  # type: ignore[import]

        keyring.delete_password(_KEYRING_SERVICE, platform)  # type: ignore[no-untyped-call]
        return True
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------------------
# File fallback helpers (simple obfuscation, not true encryption)
# ---------------------------------------------------------------------------


def _file_get(platform: str) -> str | None:
    if not _CREDS_FILE.exists():
        return None
    try:
        data = json.loads(_CREDS_FILE.read_text(encoding="utf-8"))
        entry = data.get(platform, "")
        if entry:
            return _deobfuscate(entry)
    except Exception:  # noqa: BLE001
        pass
    return None


def _file_set(platform: str, token: str) -> None:
    _CREDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    import contextlib

    data: dict[str, str] = {}
    if _CREDS_FILE.exists():
        with contextlib.suppress(Exception):
            data = json.loads(_CREDS_FILE.read_text(encoding="utf-8"))
    data[platform] = _obfuscate(token)
    _CREDS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # Restrict permissions on non-Windows
    with contextlib.suppress(Exception):
        _CREDS_FILE.chmod(0o600)


def _file_delete(platform: str) -> bool:
    if not _CREDS_FILE.exists():
        return False
    try:
        data = json.loads(_CREDS_FILE.read_text(encoding="utf-8"))
        if platform in data:
            del data[platform]
            _CREDS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return True
    except Exception:  # noqa: BLE001
        pass
    return False


def _obfuscate(token: str) -> str:
    """Simple XOR obfuscation with machine-derived key. Not true encryption."""
    key = _machine_key()
    xored = bytes(c ^ key[i % len(key)] for i, c in enumerate(token.encode()))
    return xored.hex()


def _deobfuscate(hex_str: str) -> str:
    try:
        key = _machine_key()
        xored = bytes.fromhex(hex_str)
        return bytes(c ^ key[i % len(key)] for i, c in enumerate(xored)).decode()
    except Exception:  # noqa: BLE001
        return ""


def _machine_key() -> bytes:
    """Derive a machine-specific key from system info."""
    import platform

    node = platform.node() or "specsmith-default"
    return hashlib.sha256(node.encode()).digest()


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _mask_token(token: str) -> str:
    if len(token) <= 8:
        return "***"
    return token[:4] + "..." + token[-4:]


def _detect_source(platform: str, token: str) -> str:
    info = PLATFORMS.get(platform, {})
    env_var = info.get("env_var", f"SPECSMITH_{platform.upper()}_TOKEN")
    if os.environ.get(env_var, "").strip() == token:
        return f"env:{env_var}"
    if _keyring_get(platform) == token:
        return "keyring"
    return "file"
