# SPDX-License-Identifier: MIT
"""Unit tests for the agent profile store + routing table (REQ-146)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specsmith.agent.profiles import (
    DEFAULT_PRESETS,
    Profile,
    ProfileError,
    ProfileStore,
    apply_preset,
)


def test_default_preset_round_trip(tmp_path: Path) -> None:
    store_path = tmp_path / "agents.json"
    store = apply_preset("default", path=store_path)
    assert store_path.is_file()
    raw = json.loads(store_path.read_text(encoding="utf-8"))
    assert raw["default_profile_id"] == "coder"
    assert any(p["id"] == "architect" for p in raw["profiles"])
    assert raw["routes"]["/plan"] == "architect"
    assert raw["routes"]["/why"] == "reviewer"


def test_resolve_for_activity_routes_to_correct_profile(tmp_path: Path) -> None:
    store_path = tmp_path / "agents.json"
    apply_preset("default", path=store_path)
    store = ProfileStore.load(store_path)
    assert store.resolve_for_activity("/plan").id == "architect"
    assert store.resolve_for_activity("/fix").id == "coder"
    assert store.resolve_for_activity("/why").id == "reviewer"
    # Unknown activity falls through to the default profile.
    assert store.resolve_for_activity("/unknown").id == "coder"


def test_add_remove_round_trip(tmp_path: Path) -> None:
    store = ProfileStore(path=tmp_path / "agents.json")
    profile = Profile(
        id="custom",
        role="coder",
        provider="anthropic",
        model="claude-sonnet-4-5",
        fallback_chain=["ollama/qwen2.5-coder:7b"],
    )
    store.add(profile)
    store.save()
    loaded = ProfileStore.load(store.path)
    assert loaded.get("custom").model == "claude-sonnet-4-5"
    assert loaded.default_profile_id == "custom"
    assert loaded.remove("custom") is True
    assert loaded.profiles == []


def test_set_route_rejects_unknown_profile(tmp_path: Path) -> None:
    store = ProfileStore(path=tmp_path / "agents.json")
    with pytest.raises(ProfileError):
        store.set_route("/plan", "ghost")


def test_known_presets_have_required_keys() -> None:
    for name, blob in DEFAULT_PRESETS.items():
        assert "default_profile_id" in blob, f"{name} missing default_profile_id"
        assert isinstance(blob.get("profiles"), list)
        assert isinstance(blob.get("routes", {}), dict)
