# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for the Zoo Code LiteLLM profile generation module (Issue #331)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from specsmith.commands.zoo_code_litellm_profile import (
    LITELLM_API_KEY_PLACEHOLDER,
    LITELLM_BASE_URL,
    MODEL_PLACEHOLDER,
    PROFILE_ID,
    PROMPT_CACHE_PREFIX,
    SPEC_SMITH_MODES,
    CacheCapability,
    Result,
    _build_api_config_profile,
    _build_mode_mappings,
    _emit_result,
    _read_settings,
    _write_settings,
    _zoo_code_settings_path,
    detect_cache_capability,
    doctor,
    generate_profile,
    litellm_doctor,
    litellm_setup,
    litellm_validate,
    validate_profile,
)


# ---------------------------------------------------------------------------
# Result tests
# ---------------------------------------------------------------------------


class TestResult:
    def test_ok_true_when_no_errors(self) -> None:
        r = Result()
        assert r.ok is True

    def test_ok_false_when_errors(self) -> None:
        r = Result(errors=["bad"])
        assert r.ok is False

    def test_add_merges_lists(self) -> None:
        a = Result(created=["x"], warnings=["w1"])
        b = Result(updated=["y"], errors=["e1"])
        a.add(b)
        assert a.created == ["x"]
        assert a.updated == ["y"]
        assert a.warnings == ["w1"]
        assert a.errors == ["e1"]

    def test_add_errors_preserved(self) -> None:
        a = Result(warnings=["w1"])
        b = Result(errors=["e1"])
        a.add(b)
        assert a.warnings == ["w1"]
        assert a.errors == ["e1"]


# ---------------------------------------------------------------------------
# CacheCapability tests
# ---------------------------------------------------------------------------


class TestCacheCapability:
    def test_defaults(self) -> None:
        c = CacheCapability()
        assert c.supported is False
        assert c.provider == ""
        assert c.model == ""
        assert c.cache_type == ""
        assert c.discovery_error == ""


# ---------------------------------------------------------------------------
# Settings I/O tests
# ---------------------------------------------------------------------------


class TestSettingsIO:
    def test_read_settings_missing_file(self, tmp_path: Path) -> None:
        p = tmp_path / "missing.json"
        assert _read_settings(p) == {}

    def test_read_settings_invalid_json(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("not json", encoding="utf-8")
        assert _read_settings(p) == {}

    def test_read_settings_valid(self, tmp_path: Path) -> None:
        p = tmp_path / "valid.json"
        p.write_text('{"apiConfigProfiles": {}}', encoding="utf-8")
        result = _read_settings(p)
        assert isinstance(result, dict)
        assert result["apiConfigProfiles"] == {}

    def test_write_and_read_roundtrip(self, tmp_path: Path) -> None:
        p = tmp_path / "settings.json"
        data = {"apiConfigProfiles": {"Local-LLM": {"provider": "litellm"}}}
        _write_settings(p, data)
        assert p.exists()
        loaded = _read_settings(p)
        assert loaded == data

    def test_write_creates_tmp_then_renames(self, tmp_path: Path) -> None:
        p = tmp_path / "settings.json"
        data = {"key": "val"}
        _write_settings(p, data)
        assert not p.with_suffix(".tmp").exists()
        assert p.exists()


# ---------------------------------------------------------------------------
# Path resolution tests
# ---------------------------------------------------------------------------


class TestZooCodeSettingsPath:
    def test_returns_none_when_nothing_exists(self) -> None:
        with patch("pathlib.Path.exists", return_value=False):
            assert _zoo_code_settings_path() is None


# ---------------------------------------------------------------------------
# Mode mappings tests
# ---------------------------------------------------------------------------


class TestModeMappings:
    def test_build_mode_mappings_contains_all_modes(self) -> None:
        mappings = _build_mode_mappings()
        for mode in SPEC_SMITH_MODES:
            assert mode in mappings
            assert mappings[mode]["provider"] == "litellm"
            assert mappings[mode]["apiProvider"] == "litellm"
            assert mappings[mode]["profileId"] == PROFILE_ID

    def test_mode_mappings_count(self) -> None:
        mappings = _build_mode_mappings()
        assert len(mappings) == len(SPEC_SMITH_MODES)


# ---------------------------------------------------------------------------
# Profile building tests
# ---------------------------------------------------------------------------


class TestBuildApiConfigProfile:
    def test_default_profile(self) -> None:
        profile = _build_api_config_profile()
        assert profile["profileId"] == PROFILE_ID
        assert profile["name"] == "Local-LLM"
        assert profile["provider"] == "litellm"
        assert profile["apiProvider"] == "litellm"
        assert profile["apiBase"] == LITELLM_BASE_URL
        assert profile["model"] == MODEL_PLACEHOLDER
        assert profile["apiKey"] == LITELLM_API_KEY_PLACEHOLDER
        assert profile["promptCache"] is True
        assert "modeMappings" in profile
        assert "systemPrompt" in profile

    def test_custom_base_url(self) -> None:
        profile = _build_api_config_profile(base_url="http://localhost:8080")
        assert profile["apiBase"] == "http://localhost:8080"

    def test_no_cache(self) -> None:
        profile = _build_api_config_profile(enable_cache=False)
        assert "promptCache" not in profile
        assert "promptCacheOptions" not in profile

    def test_custom_mode_mappings(self) -> None:
        custom = {"code": {"profileId": "custom"}}
        profile = _build_api_config_profile(mode_mappings=custom)
        assert profile["modeMappings"] == custom

    def test_deterministic_timestamps(self) -> None:
        profile = _build_api_config_profile()
        assert profile["created_at"] == "2026-07-17T00:00:00Z"
        assert profile["updated_at"] == "2026-07-17T00:00:00Z"


# ---------------------------------------------------------------------------
# generate_profile tests
# ---------------------------------------------------------------------------


class TestGenerateProfile:
    def test_creates_profile_in_settings(self, tmp_path: Path) -> None:
        settings = tmp_path / "settings.json"
        result = generate_profile(settings_path=settings)
        assert result.ok
        assert PROFILE_ID in result.created
        data = _read_settings(settings)
        assert PROFILE_ID in data.get("apiConfigProfiles", {})

    def test_dry_run_no_file_written(self, tmp_path: Path) -> None:
        settings = tmp_path / "settings.json"
        result = generate_profile(settings_path=settings, dry_run=True)
        assert result.ok
        assert not settings.exists()

    def test_preserves_existing_user_modified(self, tmp_path: Path) -> None:
        settings = tmp_path / "settings.json"
        generate_profile(settings_path=settings)
        data = _read_settings(settings)
        data["apiConfigProfiles"][PROFILE_ID]["apiBase"] = "http://different:4000"
        _write_settings(settings, data)
        result = generate_profile(settings_path=settings, preserve_existing=True)
        assert result.ok
        assert any("differs from defaults" in w for w in result.warnings)

    def test_overwrite_existing(self, tmp_path: Path) -> None:
        settings = tmp_path / "settings.json"
        generate_profile(settings_path=settings)
        data = _read_settings(settings)
        data["apiConfigProfiles"][PROFILE_ID]["apiBase"] = "http://different:4000"
        _write_settings(settings, data)
        result = generate_profile(settings_path=settings, preserve_existing=False)
        assert result.ok
        updated_data = _read_settings(settings)
        assert updated_data["apiConfigProfiles"][PROFILE_ID]["apiBase"] == LITELLM_BASE_URL

    def test_nonexistent_path_creates_profile(self, tmp_path: Path) -> None:
        # When settings_path points to a non-existent file, the code
        # creates it anyway (with a warning about the missing file).
        settings = tmp_path / "settings.json"
        result = generate_profile(settings_path=settings)
        assert result.ok
        assert PROFILE_ID in result.created
        assert settings.exists()


# ---------------------------------------------------------------------------
# validate_profile tests
# ---------------------------------------------------------------------------


class TestValidateProfile:
    def test_valid_profile(self, tmp_path: Path) -> None:
        settings = tmp_path / "settings.json"
        generate_profile(settings_path=settings)
        result = validate_profile(settings_path=settings)
        assert result.ok

    def test_missing_profile(self, tmp_path: Path) -> None:
        settings = tmp_path / "settings.json"
        settings.write_text("{}", encoding="utf-8")
        result = validate_profile(settings_path=settings)
        assert not result.ok
        assert any("not found" in e for e in result.errors)

    def test_wrong_provider(self, tmp_path: Path) -> None:
        settings = tmp_path / "settings.json"
        data = {
            "apiConfigProfiles": {
                PROFILE_ID: {"provider": "openai", "apiBase": LITELLM_BASE_URL}
            }
        }
        _write_settings(settings, data)
        result = validate_profile(settings_path=settings)
        assert not result.ok
        assert any("provider" in e for e in result.errors)

    def test_wrong_base_url(self, tmp_path: Path) -> None:
        settings = tmp_path / "settings.json"
        data = {
            "apiConfigProfiles": {
                PROFILE_ID: {"provider": "litellm", "apiBase": "http://wrong:4000"}
            }
        }
        _write_settings(settings, data)
        result = validate_profile(settings_path=settings, expected_url="http://127.0.0.1:4000")
        assert not result.ok
        assert any("apiBase" in e for e in result.errors)

    def test_missing_mode_mapping_warning(self, tmp_path: Path) -> None:
        settings = tmp_path / "settings.json"
        data = {
            "apiConfigProfiles": {
                PROFILE_ID: {
                    "provider": "litellm",
                    "apiBase": LITELLM_BASE_URL,
                    "modeMappings": {},
                }
            }
        }
        _write_settings(settings, data)
        result = validate_profile(settings_path=settings)
        assert any("mode mapping" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# doctor tests
# ---------------------------------------------------------------------------


class TestDoctor:
    def test_doctor_with_valid_profile(self, tmp_path: Path) -> None:
        settings = tmp_path / "settings.json"
        generate_profile(settings_path=settings)
        result = doctor(settings_path=settings, check_proxy=False)
        assert result.ok

    def test_doctor_with_missing_settings(self) -> None:
        result = doctor(settings_path=Path("/nonexistent/path.json"), check_proxy=False)
        assert not result.ok
        assert any("does not exist" in e for e in result.errors)

    def test_doctor_skips_proxy_check(self, tmp_path: Path) -> None:
        settings = tmp_path / "settings.json"
        generate_profile(settings_path=settings)
        result = doctor(settings_path=settings, check_proxy=False)
        assert not any("proxy" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# detect_cache_capability tests
# ---------------------------------------------------------------------------


class TestDetectCacheCapability:
    def test_unreachable_proxy(self) -> None:
        cap = detect_cache_capability(base_url="http://127.0.0.1:1", timeout=0.1)
        assert cap.supported is False
        assert "unreachable" in cap.discovery_error.lower() or "error" in cap.discovery_error.lower()

    def test_reachable_mock(self) -> None:
        cap = CacheCapability(supported=True, provider="litellm", model="test", cache_type="prefix")
        assert cap.supported is True
        assert cap.provider == "litellm"
        assert cap.cache_type == "prefix"


# ---------------------------------------------------------------------------
# _emit_result tests
# ---------------------------------------------------------------------------


class TestEmitResult:
    def test_emit_ok_result(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = Result(created=["x"], updated=["y"])
        _emit_result(r)
        out = capsys.readouterr().out
        assert "Created: x" in out
        assert "Updated: y" in out

    def test_emit_errors_exits(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = Result(errors=["bad"])
        with pytest.raises(SystemExit, match="2"):
            _emit_result(r)
        err = capsys.readouterr().err
        assert "Error: bad" in err

    def test_emit_dry_run_prefix(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = Result(created=["x"])
        _emit_result(r, dry_run=True)
        out = capsys.readouterr().out
        assert "[DRY RUN] Created: x" in out


# ---------------------------------------------------------------------------
# CLI command tests
# ---------------------------------------------------------------------------


class TestCLICommands:
    def test_litellm_setup_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(litellm_setup, ["--help"])
        assert result.exit_code == 0
        assert "--base-url" in result.output

    def test_litellm_validate_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(litellm_validate, ["--help"])
        assert result.exit_code == 0
        assert "--expected-url" in result.output

    def test_litellm_doctor_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(litellm_doctor, ["--help"])
        assert result.exit_code == 0
        assert "--no-proxy-check" in result.output

    def test_litellm_setup_dry_run(self, tmp_path: Path) -> None:
        runner = CliRunner()
        settings = tmp_path / "settings.json"
        result = runner.invoke(litellm_setup, ["--dry-run", "--settings-path", str(settings)])
        assert result.exit_code == 0
        assert not settings.exists()

    def test_litellm_setup_writes_file(self, tmp_path: Path) -> None:
        runner = CliRunner()
        settings = tmp_path / "settings.json"
        result = runner.invoke(litellm_setup, ["--settings-path", str(settings)])
        assert result.exit_code == 0
        assert settings.exists()
        data = json.loads(settings.read_text())
        assert PROFILE_ID in data.get("apiConfigProfiles", {})

    def test_litellm_validate_missing(self, tmp_path: Path) -> None:
        runner = CliRunner()
        settings = tmp_path / "settings.json"
        settings.write_text("{}", encoding="utf-8")
        result = runner.invoke(litellm_validate, ["--settings-path", str(settings)])
        assert result.exit_code == 2
        assert "not found" in result.output.lower() or "Error" in result.output

    def test_litellm_doctor_no_proxy(self, tmp_path: Path) -> None:
        runner = CliRunner()
        settings = tmp_path / "settings.json"
        generate_profile(settings_path=settings)
        result = runner.invoke(
            litellm_doctor,
            ["--settings-path", str(settings), "--no-proxy-check"],
        )
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    def test_profile_id(self) -> None:
        assert PROFILE_ID == "Local-LLM"

    def test_base_url(self) -> None:
        assert LITELLM_BASE_URL == "http://127.0.0.1:4000"

    def test_api_key_placeholder_empty(self) -> None:
        assert LITELLM_API_KEY_PLACEHOLDER == ""

    def test_model_placeholder(self) -> None:
        assert MODEL_PLACEHOLDER == "auto-discover"

    def test_prompt_cache_prefix_is_deterministic(self) -> None:
        assert "# Specsmith Governance Context" in PROMPT_CACHE_PREFIX
        assert "<!-- specsmith-zoo-assets:v2 -->" in PROMPT_CACHE_PREFIX

    def test_spec_smith_modes_list(self) -> None:
        assert "orchestrator" in SPEC_SMITH_MODES
        assert "architect" in SPEC_SMITH_MODES
        assert "code" in SPEC_SMITH_MODES
        assert "debug" in SPEC_SMITH_MODES
        assert "ask" in SPEC_SMITH_MODES
        assert "reviewer" in SPEC_SMITH_MODES