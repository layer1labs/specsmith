# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Generate and maintain a safe Zoo Code Local-LLM import asset.

Zoo Code stores live provider profiles in VS Code Secret Storage.  Specsmith
therefore does *not* write extension storage files directly.  Instead it
generates the documented Zoo settings-import document used by Zoo Code's manual
and ``roo-cline.autoImportSettingsPath`` import flows.  The schema implemented
here is verified against Zoo Code's ``ProviderSettingsManager``,
``importExport`` and ``provider-settings`` sources.

The generated asset intentionally contains no ``litellmApiKey``.  Zoo Code uses
its documented dummy key when the proxy does not require authentication; users
who protect a proxy configure the real key in Zoo Code Secret Storage.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import click

PROFILE_NAME = "Local-LLM"
PROFILE_ID = "specsmith-local-llm-v1"
LITELLM_BASE_URL = "http://127.0.0.1:4000"
IMPORT_SCHEMA = "zoo-code-import-v1"
ASSET_NAME = "specsmith-zoo-local-llm.json"
MANIFEST_NAME = ".specsmith-zoo-local-llm.manifest.json"
AUTO_IMPORT_SETTING = "roo-cline.autoImportSettingsPath"

# Zoo's built-in mode slugs plus the Specsmith reviewer mode.  Additional
# Specsmith modes are discovered from project assets or passed explicitly.
SPEC_SMITH_MODES = ("orchestrator", "architect", "code", "debug", "ask", "reviewer")

# This content stays byte-identical across generated assets.  Zoo's current
# import schema supports both of the global switches below, so volatile time
# and cost values are excluded from the cacheable governance prefix.
PROMPT_CACHE_PREFIX = (
    "# Specsmith Governance Context\n"
    "<!-- specsmith-zoo-assets:v3 -->\n"
    "## Rules\n"
    "You are operating under Specsmith governance. All non-trivial work must "
    "be anchored to requirements, constraints, acceptance criteria, evidence, "
    "and verification.\n"
)
DEFAULT_ALLOWED_COMMANDS = ["*"]

Platform = Literal["windows", "linux", "macos"]


@dataclass
class Result:
    """Structured result for setup, validation, repair, and removal."""

    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    repaired: list[str] = field(default_factory=list)
    preserved: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(self, other: Result) -> None:
        for name in ("created", "updated", "repaired", "preserved", "errors", "warnings"):
            getattr(self, name).extend(getattr(other, name))


@dataclass
class CacheCapability:
    """LiteLLM's explicitly reported prompt-cache capability."""

    supported: bool = False
    model: str = ""
    cache_type: str = ""
    discovered: bool = False
    discovery_error: str = ""


def zoo_import_asset_path(project_dir: Path) -> Path:
    """Return Specsmith's project-local, portable Zoo settings import asset."""
    return project_dir / ".zoo-code" / ASSET_NAME


def _manifest_path(asset_path: Path) -> Path:
    return asset_path.with_name(MANIFEST_NAME)


def _asset_hash(data: dict[str, Any]) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, None
    if not path.is_file():
        return None, f"Expected a file at {path}"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"Invalid JSON at {path}: {exc}"
    if not isinstance(value, dict):
        return None, f"Expected a JSON object at {path}"
    return value, None


def _write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _next_backup_path(path: Path) -> Path:
    base = path.with_name(f"{path.name}.broken")
    if not base.exists():
        return base
    index = 1
    while True:
        candidate = path.with_name(f"{path.name}.broken.{index}")
        if not candidate.exists():
            return candidate
        index += 1


def _is_managed_document(data: dict[str, Any]) -> bool:
    metadata = data.get("specsmith")
    return isinstance(metadata, dict) and metadata.get("schema") == IMPORT_SCHEMA


def _read_manifest(asset_path: Path) -> dict[str, Any] | None:
    manifest, error = _read_json(_manifest_path(asset_path))
    if error or not manifest:
        return None
    if manifest.get("schema") != IMPORT_SCHEMA or manifest.get("asset") != asset_path.name:
        return None
    return manifest


def _manifest_matches_document(manifest: dict[str, Any] | None, data: dict[str, Any]) -> bool:
    """Return whether the manifest proves that ``data`` is untouched.

    The manifest is both a provenance marker and a content hash. A previous
    Specsmith asset without the command policy can migrate to the new default
    only when we can prove it has not been edited after generation.
    """
    return bool(manifest and manifest.get("sha256") == _asset_hash(data))


def _custom_allowed_commands(data: dict[str, Any]) -> list[str] | None:
    """Return a user-selected command policy, never treating malformed data as one."""
    settings = data.get("globalSettings")
    commands = settings.get("allowedCommands") if isinstance(settings, dict) else None
    if (
        isinstance(commands, list)
        and all(isinstance(command, str) and command for command in commands)
        and commands != DEFAULT_ALLOWED_COMMANDS
    ):
        return commands
    return None


def _normalise_modes(modes: Iterable[str]) -> list[str]:
    return sorted({mode.strip() for mode in modes if isinstance(mode, str) and mode.strip()})


def discover_specsmith_modes(project_dir: Path) -> list[str]:
    """Discover mode slugs from Specsmith's generated JSON mode asset.

    Zoo supports several project-mode formats.  Specsmith's own generated asset
    is JSON, so reading only that known shape avoids guessing at user files.
    """
    discovered: list[str] = []
    path = project_dir / ".zoo-code" / "specsmith-modes.json"
    data, error = _read_json(path)
    if error or not data:
        return discovered
    raw_modes = data.get("modes")
    if not isinstance(raw_modes, list):
        return discovered
    for mode in raw_modes:
        if not isinstance(mode, dict):
            continue
        slug = mode.get("slug") or mode.get("mode")
        if isinstance(slug, str) and slug.strip():
            discovered.append(slug.strip())
    return discovered


def _build_mode_api_configs(modes: Iterable[str]) -> dict[str, str]:
    return {mode: PROFILE_ID for mode in _normalise_modes(modes)}


def build_import_document(
    *,
    base_url: str = LITELLM_BASE_URL,
    model: str | None = None,
    cache_capability: CacheCapability | None = None,
    modes: Iterable[str] = SPEC_SMITH_MODES,
) -> dict[str, Any]:
    """Build the current Zoo settings-import schema.

    Zoo validates LiteLLM profiles using ``apiProvider``, ``litellmBaseUrl``,
    ``litellmModelId``, and ``litellmUsePromptCache``.  Never add the secret
    ``litellmApiKey`` field: the extension owns secret storage.
    """
    profile: dict[str, Any] = {
        "id": PROFILE_ID,
        "apiProvider": "litellm",
        "litellmBaseUrl": base_url,
    }
    if model and model != "auto-discover":
        profile["litellmModelId"] = model
    if cache_capability and cache_capability.discovered and cache_capability.supported:
        profile["litellmUsePromptCache"] = True

    return {
        "specsmith": {
            "schema": IMPORT_SCHEMA,
            "managedProfile": PROFILE_NAME,
            "purpose": "Zoo Code LiteLLM Local-LLM provisioning asset",
        },
        "providerProfiles": {
            "currentApiConfigName": PROFILE_NAME,
            "apiConfigs": {PROFILE_NAME: profile},
            "modeApiConfigs": _build_mode_api_configs(modes),
        },
        "globalSettings": {
            "customInstructions": PROMPT_CACHE_PREFIX,
            "includeCurrentTime": False,
            "includeCurrentCost": False,
            # Zoo Code's current global-settings schema names this
            # ``allowedCommands``. It is intentionally a literal wildcard, not
            # a shell pattern expanded by Specsmith.
            "allowedCommands": DEFAULT_ALLOWED_COMMANDS,
        },
    }


def detect_cache_capability(
    base_url: str = LITELLM_BASE_URL,
    timeout: float = 3.0,
) -> CacheCapability:
    """Read LiteLLM's documented model metadata without inferring support.

    Zoo queries ``/v1/model/info`` and reads
    ``model_info.supports_prompt_caching``.  ``/v1/models`` is an intentional
    compatibility fallback only; a model listing alone never proves caching.
    """
    capability = CacheCapability()
    endpoints = ("/v1/model/info", "/v1/models")
    errors: list[str] = []
    for endpoint in endpoints:
        url = f"{base_url.rstrip('/')}{endpoint}"
        try:
            request = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (
            OSError,
            urllib.error.URLError,
            urllib.error.HTTPError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            errors.append(f"{endpoint}: {exc}")
            continue

        models = payload.get("data", payload.get("models", [])) if isinstance(payload, dict) else []
        if not isinstance(models, list):
            errors.append(f"{endpoint}: response did not contain a model list")
            continue
        capability.discovered = True
        for item in models:
            if not isinstance(item, dict):
                continue
            model_info = item.get("model_info")
            details = model_info if isinstance(model_info, dict) else item
            model = item.get("model_name") or item.get("id") or details.get("model_name", "")
            supports = details.get("supports_prompt_caching")
            if supports is True:
                capability.supported = True
                capability.model = str(model)
                capability.cache_type = "provider-reported"
                return capability
        capability.discovery_error = "LiteLLM returned model metadata with no cache-capable model"
        return capability

    capability.discovery_error = "; ".join(errors) or "LiteLLM proxy unavailable"
    return capability


def generate_profile(
    settings_path: Path | None = None,
    *,
    project_dir: Path | None = None,
    base_url: str = LITELLM_BASE_URL,
    model: str | None = None,
    cache_capability: CacheCapability | None = None,
    additional_modes: Iterable[str] = (),
    dry_run: bool = False,
) -> Result:
    """Generate or safely repair the managed Zoo import asset.

    ``settings_path`` remains as a compatibility alias for callers of the old
    command.  It now denotes the generated import asset, not Zoo Secret Storage.
    """
    result = Result()
    root = project_dir or Path.cwd()
    asset_path = settings_path or zoo_import_asset_path(root)
    modes = [*SPEC_SMITH_MODES, *discover_specsmith_modes(root), *additional_modes]
    document = build_import_document(
        base_url=base_url,
        model=model,
        cache_capability=cache_capability,
        modes=modes,
    )
    existing, error = _read_json(asset_path)
    manifest = _read_manifest(asset_path)

    if error:
        if manifest is None:
            result.errors.append(
                f"Refusing to replace malformed unowned asset {asset_path}. "
                "Restore it manually or remove it before setup."
            )
            return result
        backup = _next_backup_path(asset_path)
        if not dry_run:
            asset_path.replace(backup)
            _write_json_atomic(asset_path, document)
            _write_json_atomic(
                _manifest_path(asset_path),
                {
                    "schema": IMPORT_SCHEMA,
                    "asset": asset_path.name,
                    "sha256": _asset_hash(document),
                },
            )
        result.repaired.append(f"{asset_path} (backup: {backup})")
        return result

    if existing is None:
        if not dry_run:
            _write_json_atomic(asset_path, document)
            _write_json_atomic(
                _manifest_path(asset_path),
                {
                    "schema": IMPORT_SCHEMA,
                    "asset": asset_path.name,
                    "sha256": _asset_hash(document),
                },
            )
        result.created.append(str(asset_path))
        return result

    if _is_managed_document(existing):
        custom_commands = _custom_allowed_commands(existing)
        if custom_commands is not None:
            # An explicit non-default allowlist is user policy. Keep it even
            # if we later need to repair another managed field.
            document["globalSettings"]["allowedCommands"] = custom_commands
        elif "allowedCommands" not in existing.get(
            "globalSettings", {}
        ) and not _manifest_matches_document(manifest, existing):
            result.preserved.append(f"{asset_path} (unverified pre-wildcard policy)")
            result.warnings.append(
                "The existing managed import asset has no allowedCommands policy and its "
                "manifest does not prove it is untouched; it was preserved as user policy."
            )
            return result
        if existing == document:
            result.preserved.append(f"{asset_path} (already current)")
            return result
        backup = _next_backup_path(asset_path)
        if not dry_run:
            asset_path.replace(backup)
            _write_json_atomic(asset_path, document)
            _write_json_atomic(
                _manifest_path(asset_path),
                {
                    "schema": IMPORT_SCHEMA,
                    "asset": asset_path.name,
                    "sha256": _asset_hash(document),
                },
            )
        result.repaired.append(f"{asset_path} (backup: {backup})")
        return result

    # The obsolete WIP writer identified itself with these deterministic fields.
    # Only that explicit legacy shape is migrated; arbitrary Local-LLM files are
    # user-owned and remain untouched.
    legacy_profile = existing.get("apiConfigProfiles", {}).get(PROFILE_NAME)
    if isinstance(legacy_profile, dict) and legacy_profile.get("description") == (
        "Specsmith default: local LiteLLM proxy with prompt caching"
    ):
        backup = _next_backup_path(asset_path)
        if not dry_run:
            asset_path.replace(backup)
            _write_json_atomic(asset_path, document)
            _write_json_atomic(
                _manifest_path(asset_path),
                {
                    "schema": IMPORT_SCHEMA,
                    "asset": asset_path.name,
                    "sha256": _asset_hash(document),
                },
            )
        result.repaired.append(f"{asset_path} (migrated legacy asset; backup: {backup})")
        return result

    result.preserved.append(f"{asset_path} (unowned existing file)")
    result.warnings.append(
        "Existing Zoo import asset is not Specsmith-managed; it was preserved. "
        "Choose another --asset-path or review it manually."
    )
    return result


def validate_profile(
    settings_path: Path | None = None,
    *,
    project_dir: Path | None = None,
    expected_url: str = LITELLM_BASE_URL,
) -> Result:
    """Validate a generated asset or a Zoo settings export against current schema."""
    result = Result()
    asset_path = settings_path or zoo_import_asset_path(project_dir or Path.cwd())
    data, error = _read_json(asset_path)
    if error:
        result.errors.append(error)
        return result
    if data is None:
        result.errors.append(f"Zoo import asset does not exist: {asset_path}")
        return result

    profiles = data.get("providerProfiles")
    if not isinstance(profiles, dict):
        result.errors.append("Missing providerProfiles object required by Zoo Code import schema")
        return result
    configs = profiles.get("apiConfigs")
    if not isinstance(configs, dict) or not isinstance(configs.get(PROFILE_NAME), dict):
        result.errors.append(f"Missing {PROFILE_NAME!r} API configuration")
        return result
    profile = configs[PROFILE_NAME]
    if profile.get("id") != PROFILE_ID:
        result.errors.append(f"{PROFILE_NAME!r} id must be {PROFILE_ID!r}")
    if profile.get("apiProvider") != "litellm":
        result.errors.append("Local-LLM must use Zoo Code's dedicated 'litellm' provider")
    if profile.get("litellmBaseUrl") != expected_url:
        actual_url = profile.get("litellmBaseUrl")
        result.errors.append(
            f"Local-LLM litellmBaseUrl is {actual_url!r}, expected {expected_url!r}"
        )
    if "litellmApiKey" in profile:
        result.errors.append("Generated Zoo import asset must not serialize litellmApiKey")
    cache = profile.get("litellmUsePromptCache")
    if cache is not None and cache is not True:
        result.errors.append("litellmUsePromptCache must be omitted or true")

    mappings = profiles.get("modeApiConfigs")
    if not isinstance(mappings, dict):
        result.errors.append("Missing modeApiConfigs object")
    else:
        for mode in SPEC_SMITH_MODES:
            if mappings.get(mode) != PROFILE_ID:
                result.errors.append(f"Mode {mode!r} is not mapped to Local-LLM")

    global_settings = data.get("globalSettings")
    if not isinstance(global_settings, dict):
        result.errors.append("Missing globalSettings object")
    else:
        if global_settings.get("customInstructions") != PROMPT_CACHE_PREFIX:
            result.errors.append(
                "The deterministic Specsmith governance prefix is missing or changed"
            )
        if global_settings.get("includeCurrentTime") is not False:
            result.errors.append("includeCurrentTime must be false for cache-safe defaults")
        if global_settings.get("includeCurrentCost") is not False:
            result.errors.append("includeCurrentCost must be false for cache-safe defaults")
        allowed_commands = global_settings.get("allowedCommands")
        if not (
            isinstance(allowed_commands, list)
            and allowed_commands
            and all(isinstance(command, str) and command for command in allowed_commands)
        ):
            result.errors.append(
                "allowedCommands must be a non-empty array of Zoo Code command prefixes"
            )
        elif allowed_commands != DEFAULT_ALLOWED_COMMANDS:
            result.warnings.append(
                "allowedCommands is user-customized; Specsmith preserved this execution policy"
            )
    return result


def doctor(
    settings_path: Path | None = None,
    *,
    project_dir: Path | None = None,
    check_proxy: bool = True,
) -> Result:
    """Validate the asset and report LiteLLM reachability/caching diagnostics."""
    result = validate_profile(settings_path, project_dir=project_dir)
    if check_proxy:
        capability = detect_cache_capability()
        if capability.supported:
            model_label = capability.model or "a discovered model"
            result.preserved.append(f"LiteLLM reports prompt-cache support for {model_label}")
        elif capability.discovered:
            result.warnings.append(
                "LiteLLM is reachable but no model reports supports_prompt_caching=true; "
                "the generated asset does not force cache controls."
            )
        else:
            result.warnings.append(f"LiteLLM is unreachable: {capability.discovery_error}")
    return result


def vscode_user_settings_path(
    platform: Platform | None = None,
    *,
    home: Path | None = None,
    appdata: Path | None = None,
) -> Path:
    """Return VS Code's user settings path for Windows, Linux, or macOS."""
    selected = platform or _runtime_platform()
    user_home = home or Path.home()
    if selected == "windows":
        base = appdata or Path(os.environ.get("APPDATA", user_home / "AppData" / "Roaming"))
        return base / "Code" / "User" / "settings.json"
    if selected == "macos":
        return user_home / "Library" / "Application Support" / "Code" / "User" / "settings.json"
    return user_home / ".config" / "Code" / "User" / "settings.json"


def _runtime_platform() -> Platform:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def enable_auto_import(
    asset_path: Path,
    *,
    settings_path: Path | None = None,
    platform: Platform | None = None,
) -> Result:
    """Opt in to Zoo's documented auto-import setting without replacing JSONC.

    VS Code settings commonly use comments and trailing commas.  The standard
    library cannot safely edit JSONC, so this function refuses such files rather
    than stripping user comments or overwriting unrelated settings.
    """
    result = Result()
    target = settings_path or vscode_user_settings_path(platform)
    settings, error = _read_json(target)
    if error:
        result.errors.append(
            f"Cannot safely update VS Code settings: {error}. Add {AUTO_IMPORT_SETTING!r} manually."
        )
        return result
    if settings is None:
        settings = {}
    existing = settings.get(AUTO_IMPORT_SETTING)
    desired = str(asset_path.resolve())
    if existing == desired:
        result.preserved.append(f"{target} (auto-import already configured)")
        return result
    settings[AUTO_IMPORT_SETTING] = desired
    try:
        _write_json_atomic(target, settings)
    except OSError as exc:
        result.errors.append(f"Failed to write VS Code settings {target}: {exc}")
        return result
    result.updated.append(f"{target} ({AUTO_IMPORT_SETTING})")
    result.warnings.append(
        "Zoo auto-import re-applies this asset at every extension startup. "
        "Disable it after provisioning if Local-LLM profile or mode mappings are user-customized."
    )
    return result


def uninstall_profile(settings_path: Path, *, dry_run: bool = False) -> Result:
    """Remove only a provenance-marked Specsmith import asset and manifest."""
    result = Result()
    manifest = _read_manifest(settings_path)
    if manifest is None:
        result.warnings.append(f"{settings_path} is not proven Specsmith-managed; preserved")
        return result
    if not dry_run:
        try:
            settings_path.unlink(missing_ok=True)
            _manifest_path(settings_path).unlink(missing_ok=True)
        except OSError as exc:
            result.errors.append(f"Failed to remove managed Zoo asset: {exc}")
            return result
    result.updated.append(f"removed {settings_path}")
    return result


_litellm_group = click.Group("litellm")


@_litellm_group.command("setup")
@click.option(
    "--project-dir", type=click.Path(path_type=Path), default=Path("."), show_default=True
)
@click.option("--asset-path", type=click.Path(path_type=Path), default=None)
@click.option("--base-url", default=LITELLM_BASE_URL, show_default=True)
@click.option("--model", default=None, help="Optional LiteLLM model ID; omit for Zoo discovery.")
@click.option("--mode", "additional_modes", multiple=True, help="Additional Specsmith mode slug.")
@click.option("--no-proxy-check", is_flag=True, help="Do not query LiteLLM capability metadata.")
@click.option(
    "--enable-auto-import",
    "enable_auto_import_setting",
    is_flag=True,
    help="Opt in to Zoo's repeated VS Code auto-import setting.",
)
@click.option("--vscode-settings-path", type=click.Path(path_type=Path), default=None)
@click.option("--dry-run", is_flag=True)
def litellm_setup(
    project_dir: Path,
    asset_path: Path | None,
    base_url: str,
    model: str | None,
    additional_modes: tuple[str, ...],
    no_proxy_check: bool,
    enable_auto_import_setting: bool,
    vscode_settings_path: Path | None,
    dry_run: bool,
) -> None:
    """Generate a safe, current Zoo Code Local-LLM import asset."""
    capability = None if no_proxy_check else detect_cache_capability(base_url)
    asset = asset_path or zoo_import_asset_path(project_dir)
    result = generate_profile(
        asset,
        project_dir=project_dir,
        base_url=base_url,
        model=model,
        cache_capability=capability,
        additional_modes=additional_modes,
        dry_run=dry_run,
    )
    if enable_auto_import_setting and result.ok and not dry_run:
        result.add(enable_auto_import(asset, settings_path=vscode_settings_path))
    _emit_result(result, dry_run)


@_litellm_group.command("validate")
@click.option(
    "--project-dir", type=click.Path(path_type=Path), default=Path("."), show_default=True
)
@click.option("--asset-path", type=click.Path(path_type=Path), default=None)
@click.option("--expected-url", default=LITELLM_BASE_URL, show_default=True)
def litellm_validate(project_dir: Path, asset_path: Path | None, expected_url: str) -> None:
    """Validate a Zoo import asset or an exported Zoo settings document."""
    _emit_result(validate_profile(asset_path, project_dir=project_dir, expected_url=expected_url))


@_litellm_group.command("doctor")
@click.option(
    "--project-dir", type=click.Path(path_type=Path), default=Path("."), show_default=True
)
@click.option("--asset-path", type=click.Path(path_type=Path), default=None)
@click.option("--no-proxy-check", is_flag=True)
def litellm_doctor(project_dir: Path, asset_path: Path | None, no_proxy_check: bool) -> None:
    """Diagnose the generated asset and LiteLLM cache metadata."""
    _emit_result(doctor(asset_path, project_dir=project_dir, check_proxy=not no_proxy_check))


@_litellm_group.command("uninstall")
@click.option(
    "--project-dir", type=click.Path(path_type=Path), default=Path("."), show_default=True
)
@click.option("--asset-path", type=click.Path(path_type=Path), default=None)
@click.option("--dry-run", is_flag=True)
def litellm_uninstall(project_dir: Path, asset_path: Path | None, dry_run: bool) -> None:
    """Remove only the provenance-marked Local-LLM import asset."""
    _emit_result(
        uninstall_profile(asset_path or zoo_import_asset_path(project_dir), dry_run=dry_run),
        dry_run,
    )


def _emit_result(result: Result, dry_run: bool = False) -> None:
    prefix = "[DRY RUN] " if dry_run else ""
    for kind in ("created", "updated", "repaired", "preserved"):
        for item in getattr(result, kind):
            click.echo(f"{prefix}{kind.capitalize()}: {item}")
    for item in result.warnings:
        click.echo(f"{prefix}Warning: {item}", err=True)
    for item in result.errors:
        click.echo(f"{prefix}Error: {item}", err=True)
    if not result.ok:
        raise SystemExit(2)
