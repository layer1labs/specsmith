"""Versioned, provenance-aware global/project/local configuration resolution."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml

SCHEMA_VERSION = 1
KNOWN_TOP_LEVEL = {
    "schema_version",
    "project",
    "name",
    "description",
    "author",
    "license",
    "url",
    "aee_phase",
    "version",
    "spec_version",
    "platform",
    "type",
    "governance",
    "execution",
    "identity",
    "context",
    "zoo_code",
    "providers",
    "extensions",
}
_SECRET_KEY = re.compile(r"(?:token|secret|password|api_key|credential)", re.IGNORECASE)
_SECRET_REFERENCE = re.compile(r"^\$\{(?:ENV|KEYRING):[^}]+\}$")


class ConfigError(ValueError):
    """Configuration is invalid, conflicting, or unsafe."""


@dataclass(frozen=True)
class ResolvedConfig:
    values: dict[str, Any]
    provenance: dict[str, str]
    source_paths: tuple[str, ...]

    def redacted(self) -> dict[str, Any]:
        def visit(value: Any, key: str = "") -> Any:
            if _SECRET_KEY.search(key):
                return "<redacted>"
            if isinstance(value, dict):
                return {k: visit(v, k) for k, v in value.items()}
            if isinstance(value, list):
                return [visit(item, key) for item in value]
            return value

        return cast(dict[str, Any], visit(self.values))


def global_config_path(
    *, platform: str | None = None, environ: Mapping[str, str] | None = None
) -> Path:
    platform = platform or os.name
    environ = environ or os.environ
    if platform == "nt":
        base = Path(environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    else:
        base = Path(environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "specsmith" / "config.yml"


def _load(path: Path, source: str) -> tuple[dict[str, Any], str] | None:
    if not path.is_file():
        return None
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as error:
        raise ConfigError(f"invalid {source} config at {path}: {error}") from error
    if not isinstance(value, dict):
        raise ConfigError(f"{source} config must be a mapping: {path}")
    version = value.get("schema_version", SCHEMA_VERSION)
    if version != SCHEMA_VERSION:
        raise ConfigError(f"unsupported {source} schema_version={version}: {path}")
    unknown = sorted(set(value) - KNOWN_TOP_LEVEL)
    if unknown:
        raise ConfigError(f"unknown {source} config keys at {path}: {', '.join(unknown)}")
    _validate_secrets(value, source)
    return value, str(path)


def _validate_secrets(value: Any, source: str, prefix: str = "") -> None:
    if not isinstance(value, dict):
        return
    for key, child in value.items():
        path = f"{prefix}.{key}" if prefix else key
        if (
            _SECRET_KEY.search(key)
            and isinstance(child, str)
            and not _SECRET_REFERENCE.match(child)
        ):
            raise ConfigError(f"plaintext secret rejected at {path} in {source} config")
        _validate_secrets(child, source, path)


def _merge(
    target: dict[str, Any],
    incoming: Mapping[str, Any],
    provenance: dict[str, str],
    source: str,
    prefix: str = "",
) -> None:
    for key, value in incoming.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, Mapping) and isinstance(target.get(key), dict):
            _merge(target[key], value, provenance, source, path)
        else:
            target[key] = dict(value) if isinstance(value, Mapping) else value
            provenance[path] = source


def _env_overrides(environ: Mapping[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    mapping = {
        "SPECSMITH_SHELL": ("execution", "shell"),
        "SPECSMITH_ACTOR_ID": ("identity", "actor_id"),
        "SPECSMITH_AGENT_ID": ("identity", "agent_id"),
        "SPECSMITH_REPLICA_ID": ("identity", "replica_id"),
    }
    for env_key, path in mapping.items():
        value = environ.get(env_key)
        if value:
            result.setdefault(path[0], {})[path[1]] = value
    return result


def resolve_config(
    project_root: Path,
    *,
    explicit: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
    global_path: Path | None = None,
) -> ResolvedConfig:
    """Resolve global < tracked project < ignored local < env < explicit."""
    root = project_root.resolve()
    environ = environ or os.environ
    sources = [
        (global_path or global_config_path(environ=environ), "global"),
        (root / "docs" / "SPECSMITH.yml", "project"),
        (root / ".specsmith" / "local.yml", "local"),
    ]
    values: dict[str, Any] = {"schema_version": SCHEMA_VERSION}
    provenance = {"schema_version": "default"}
    source_paths: list[str] = []
    for path, source in sources:
        loaded = _load(path, source)
        if loaded:
            data, source_path = loaded
            _merge(values, data, provenance, source)
            source_paths.append(source_path)
    _merge(values, _env_overrides(environ), provenance, "environment")
    if explicit:
        _validate_secrets(dict(explicit), "explicit")
        _merge(values, explicit, provenance, "explicit")
    return ResolvedConfig(values, provenance, tuple(source_paths))
