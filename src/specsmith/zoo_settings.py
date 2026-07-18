"""Versioned ownership and drift-repair contract for Zoo settings."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any


def settings_digest(settings: dict[str, Any]) -> str:
    raw = json.dumps(settings, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass(frozen=True)
class ZooSettingSpec:
    key: str
    desired: Any
    ownership: str
    min_version: str = "0"
    ui_path: str = ""
    reload_required: bool = False


@dataclass(frozen=True)
class ZooSettingsResult:
    status: str
    settings: dict[str, Any]
    repaired: tuple[str, ...]
    manual_actions: tuple[str, ...]
    manifest: dict[str, Any]


def reconcile_zoo_settings(
    current: dict[str, Any],
    registry: tuple[ZooSettingSpec, ...],
    *,
    version: str,
    previous_manifest: dict[str, Any] | None = None,
    expected_digest: str | None = None,
    fix: bool = True,
) -> ZooSettingsResult:
    try:
        major = int(version.split(".", 1)[0])
    except ValueError:
        major = -1
    if major != 3:
        return ZooSettingsResult(
            "unsupported_version",
            copy.deepcopy(current),
            (),
            (f"Zoo version {version!r} is unsupported; no settings were changed",),
            {"schema_version": 1, "zoo_version": version, "managed": {}},
        )
    if expected_digest and settings_digest(current) != expected_digest:
        raise ValueError("Zoo settings changed concurrently; retry from a fresh read")
    updated = copy.deepcopy(current)
    repaired: list[str] = []
    managed_drift: list[str] = []
    manual: list[str] = []
    managed: dict[str, Any] = {}
    prior_values = dict((previous_manifest or {}).get("prior_values") or {})
    for spec in registry:
        if spec.ownership == "manual":
            if current.get(spec.key) != spec.desired:
                instruction = (
                    f"{spec.ui_path}: set {spec.key}={spec.desired!r}; "
                    f"verify with `specsmith zoo-code doctor`; "
                    f"reload={'yes' if spec.reload_required else 'no'}"
                )
                manual.append(instruction)
            continue
        managed[spec.key] = spec.desired
        if current.get(spec.key) != spec.desired:
            managed_drift.append(spec.key)
            prior_values.setdefault(spec.key, current.get(spec.key))
            if fix:
                updated[spec.key] = spec.desired
                repaired.append(spec.key)
    if manual:
        status = "partial_manual_required"
    elif managed_drift and not fix:
        status = "repair_required"
    else:
        status = "healthy"
    manifest = {
        "schema_version": 1,
        "zoo_version": version,
        "managed": managed,
        "prior_values": prior_values,
        "settings_digest": settings_digest(updated),
    }
    return ZooSettingsResult(status, updated, tuple(repaired), tuple(manual), manifest)


def uninstall_zoo_settings(
    current: dict[str, Any], previous_manifest: dict[str, Any]
) -> dict[str, Any]:
    updated = copy.deepcopy(current)
    for key, managed_value in (previous_manifest.get("managed") or {}).items():
        if updated.get(key) != managed_value:
            continue
        prior = (previous_manifest.get("prior_values") or {}).get(key)
        if prior is None:
            updated.pop(key, None)
        else:
            updated[key] = prior
    return updated
