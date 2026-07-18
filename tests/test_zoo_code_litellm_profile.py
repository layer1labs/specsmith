# SPDX-License-Identifier: MIT
"""Regression tests for the current Zoo Code Local-LLM import lifecycle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from click.testing import CliRunner

from specsmith.commands.zoo_code import zoo_code_group
from specsmith.commands.zoo_code_litellm_profile import (
    ASSET_NAME,
    AUTO_IMPORT_SETTING,
    DEFAULT_ALLOWED_COMMANDS,
    IMPORT_SCHEMA,
    LITELLM_BASE_URL,
    PROFILE_ID,
    PROFILE_NAME,
    PROMPT_CACHE_PREFIX,
    SPEC_SMITH_MODES,
    CacheCapability,
    build_import_document,
    detect_cache_capability,
    enable_auto_import,
    generate_profile,
    uninstall_profile,
    validate_profile,
    vscode_user_settings_path,
    zoo_import_asset_path,
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_generated_document_uses_current_zoo_import_schema() -> None:
    document = build_import_document()
    profile = document["providerProfiles"]["apiConfigs"][PROFILE_NAME]

    assert document["specsmith"]["schema"] == IMPORT_SCHEMA
    assert document["providerProfiles"]["currentApiConfigName"] == PROFILE_NAME
    assert profile == {
        "id": PROFILE_ID,
        "apiProvider": "litellm",
        "litellmBaseUrl": LITELLM_BASE_URL,
    }
    assert "litellmApiKey" not in json.dumps(document)
    assert document["globalSettings"] == {
        "customInstructions": PROMPT_CACHE_PREFIX,
        "includeCurrentTime": False,
        "includeCurrentCost": False,
        "allowedCommands": ["*"],
    }


def test_wildcard_command_default_is_literal_for_cross_platform_commands() -> None:
    document = build_import_document()
    serialized = json.dumps(document)
    representative_commands = [
        'powershell.exe -NoProfile -Command "Get-ChildItem C:\\Program Files"',
        'cmd.exe /c "echo hello world"',
        """bash -lc 'printf %s "hello world"'""",
        "/usr/local/bin/tool --path '/tmp/with spaces'",
    ]

    assert document["globalSettings"]["allowedCommands"] == DEFAULT_ALLOWED_COMMANDS == ["*"]
    assert json.loads(serialized)["globalSettings"]["allowedCommands"] == ["*"]
    assert all(command not in serialized for command in representative_commands)


def test_cache_control_is_only_emitted_for_explicitly_supported_models() -> None:
    unknown = build_import_document(cache_capability=CacheCapability())
    unsupported = build_import_document(cache_capability=CacheCapability(discovered=True))
    supported = build_import_document(
        cache_capability=CacheCapability(discovered=True, supported=True, model="local-coder")
    )

    assert "litellmUsePromptCache" not in unknown["providerProfiles"]["apiConfigs"][PROFILE_NAME]
    assert (
        "litellmUsePromptCache" not in unsupported["providerProfiles"]["apiConfigs"][PROFILE_NAME]
    )
    assert (
        supported["providerProfiles"]["apiConfigs"][PROFILE_NAME]["litellmUsePromptCache"] is True
    )


def test_model_is_omitted_until_zoo_discovers_it() -> None:
    auto = build_import_document(model="auto-discover")
    explicit = build_import_document(model="local-coder")

    assert "litellmModelId" not in auto["providerProfiles"]["apiConfigs"][PROFILE_NAME]
    assert (
        explicit["providerProfiles"]["apiConfigs"][PROFILE_NAME]["litellmModelId"] == "local-coder"
    )


def test_mode_mappings_include_builtins_and_additional_specsmith_modes() -> None:
    document = build_import_document(modes=[*SPEC_SMITH_MODES, "specsmith-release"])
    mappings = document["providerProfiles"]["modeApiConfigs"]

    assert set(SPEC_SMITH_MODES).issubset(mappings)
    assert mappings["specsmith-release"] == PROFILE_ID
    assert set(mappings.values()) == {PROFILE_ID}


def test_cache_discovery_reads_documented_model_info(monkeypatch: Any) -> None:
    def urlopen(_: object, timeout: float) -> FakeResponse:
        assert timeout == 0.1
        return FakeResponse(
            {
                "data": [
                    {"model_name": "local-coder", "model_info": {"supports_prompt_caching": True}}
                ]
            }
        )

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    result = detect_cache_capability(timeout=0.1)

    assert result.discovered is True
    assert result.supported is True
    assert result.model == "local-coder"


def test_cache_discovery_does_not_infer_support_from_model_listing(monkeypatch: Any) -> None:
    def urlopen(_: object, timeout: float) -> FakeResponse:
        return FakeResponse({"data": [{"id": "local-coder"}]})

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    result = detect_cache_capability(timeout=0.1)

    assert result.discovered is True
    assert result.supported is False


def test_generate_creates_managed_asset_and_manifest(tmp_path: Path) -> None:
    asset = zoo_import_asset_path(tmp_path)
    result = generate_profile(project_dir=tmp_path)

    assert result.created == [str(asset)]
    assert validate_profile(project_dir=tmp_path).ok
    assert asset.exists()
    assert asset.with_name(".specsmith-zoo-local-llm.manifest.json").exists()


def test_generate_is_idempotent(tmp_path: Path) -> None:
    generate_profile(project_dir=tmp_path)
    result = generate_profile(project_dir=tmp_path)

    assert not result.created
    assert result.preserved
    assert not result.repaired


def test_customized_command_policy_is_preserved_on_regeneration(tmp_path: Path) -> None:
    asset = zoo_import_asset_path(tmp_path)
    generate_profile(project_dir=tmp_path)
    data = read_json(asset)
    data["globalSettings"]["allowedCommands"] = ["git status", "python -m pytest"]
    asset.write_text(json.dumps(data), encoding="utf-8")

    result = generate_profile(project_dir=tmp_path)

    assert result.preserved
    assert read_json(asset)["globalSettings"]["allowedCommands"] == [
        "git status",
        "python -m pytest",
    ]
    assert validate_profile(project_dir=tmp_path).warnings


def test_untouched_pre_wildcard_managed_asset_migrates(tmp_path: Path) -> None:
    asset = zoo_import_asset_path(tmp_path)
    old_document = build_import_document()
    old_document["globalSettings"].pop("allowedCommands")
    asset.parent.mkdir()
    asset.write_text(json.dumps(old_document), encoding="utf-8")
    manifest = asset.with_name(".specsmith-zoo-local-llm.manifest.json")
    manifest.write_text(
        json.dumps(
            {
                "schema": IMPORT_SCHEMA,
                "asset": asset.name,
                "sha256": hashlib.sha256(
                    json.dumps(old_document, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
            }
        ),
        encoding="utf-8",
    )

    result = generate_profile(project_dir=tmp_path)

    assert result.repaired
    assert read_json(asset)["globalSettings"]["allowedCommands"] == ["*"]


def test_unverified_pre_wildcard_policy_is_not_migrated(tmp_path: Path) -> None:
    asset = zoo_import_asset_path(tmp_path)
    old_document = build_import_document()
    old_document["globalSettings"].pop("allowedCommands")
    asset.parent.mkdir()
    asset.write_text(json.dumps(old_document), encoding="utf-8")

    result = generate_profile(project_dir=tmp_path)

    assert result.preserved
    assert result.warnings
    assert "allowedCommands" not in read_json(asset)["globalSettings"]


def test_generation_discovers_specsmith_generated_project_modes(tmp_path: Path) -> None:
    modes_path = tmp_path / ".zoo-code" / "specsmith-modes.json"
    modes_path.parent.mkdir()
    modes_path.write_text(json.dumps({"modes": [{"mode": "specsmith-planner"}]}), encoding="utf-8")

    generate_profile(project_dir=tmp_path)

    data = read_json(zoo_import_asset_path(tmp_path))
    assert data["providerProfiles"]["modeApiConfigs"]["specsmith-planner"] == PROFILE_ID


def test_malformed_owned_asset_is_backed_up_and_repaired(tmp_path: Path) -> None:
    asset = zoo_import_asset_path(tmp_path)
    generate_profile(project_dir=tmp_path)
    asset.write_text("{ broken", encoding="utf-8")

    result = generate_profile(project_dir=tmp_path)

    assert result.repaired
    assert asset.with_name(f"{ASSET_NAME}.broken").read_text(encoding="utf-8") == "{ broken"
    assert validate_profile(project_dir=tmp_path).ok


def test_tampered_managed_asset_is_backed_up_and_repaired(tmp_path: Path) -> None:
    asset = zoo_import_asset_path(tmp_path)
    generate_profile(project_dir=tmp_path)
    data = read_json(asset)
    data["providerProfiles"]["apiConfigs"][PROFILE_NAME]["apiProvider"] = "openai"
    asset.write_text(json.dumps(data), encoding="utf-8")

    result = generate_profile(project_dir=tmp_path)

    assert result.repaired
    assert asset.with_name(f"{ASSET_NAME}.broken").exists()
    assert validate_profile(project_dir=tmp_path).ok


def test_malformed_unowned_asset_is_not_overwritten(tmp_path: Path) -> None:
    asset = zoo_import_asset_path(tmp_path)
    asset.parent.mkdir()
    asset.write_text("{ broken", encoding="utf-8")

    result = generate_profile(project_dir=tmp_path)

    assert result.errors
    assert asset.read_text(encoding="utf-8") == "{ broken"


def test_unowned_valid_asset_is_preserved(tmp_path: Path) -> None:
    asset = zoo_import_asset_path(tmp_path)
    asset.parent.mkdir()
    asset.write_text(json.dumps({"user": "configuration"}), encoding="utf-8")

    result = generate_profile(project_dir=tmp_path)

    assert result.preserved
    assert read_json(asset) == {"user": "configuration"}


def test_legacy_wip_asset_is_migrated_only_when_identified_as_specsmith_owned(
    tmp_path: Path,
) -> None:
    asset = zoo_import_asset_path(tmp_path)
    asset.parent.mkdir()
    asset.write_text(
        json.dumps(
            {
                "apiConfigProfiles": {
                    PROFILE_NAME: {
                        "description": "Specsmith default: local LiteLLM proxy with prompt caching"
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    result = generate_profile(project_dir=tmp_path)

    assert result.repaired
    assert validate_profile(project_dir=tmp_path).ok


def test_validate_reports_secret_and_mapping_errors(tmp_path: Path) -> None:
    generate_profile(project_dir=tmp_path)
    asset = zoo_import_asset_path(tmp_path)
    data = read_json(asset)
    profile = data["providerProfiles"]["apiConfigs"][PROFILE_NAME]
    profile["litellmApiKey"] = "do-not-write-this"
    data["providerProfiles"]["modeApiConfigs"].pop("debug")
    asset.write_text(json.dumps(data), encoding="utf-8")

    result = validate_profile(project_dir=tmp_path)

    assert any("must not serialize" in message for message in result.errors)
    assert any("'debug'" in message for message in result.errors)


def test_cross_platform_vscode_paths() -> None:
    home = Path("/home/specsmith")
    assert vscode_user_settings_path(
        "windows", home=home, appdata=Path("C:/Users/spec/AppData/Roaming")
    ) == Path("C:/Users/spec/AppData/Roaming/Code/User/settings.json")
    assert vscode_user_settings_path("linux", home=home) == Path(
        "/home/specsmith/.config/Code/User/settings.json"
    )
    assert vscode_user_settings_path("macos", home=home) == Path(
        "/home/specsmith/Library/Application Support/Code/User/settings.json"
    )


def test_enable_auto_import_preserves_other_strict_json_settings(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"editor.fontSize": 14}), encoding="utf-8")
    asset = zoo_import_asset_path(tmp_path)
    asset.parent.mkdir()
    asset.write_text("{}", encoding="utf-8")

    result = enable_auto_import(asset, settings_path=settings)
    data = read_json(settings)

    assert result.ok
    assert data["editor.fontSize"] == 14
    assert data[AUTO_IMPORT_SETTING] == str(asset.resolve())


def test_enable_auto_import_refuses_to_destroy_jsonc_or_malformed_settings(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text("{ // comment\n}", encoding="utf-8")

    result = enable_auto_import(tmp_path / "asset.json", settings_path=settings)

    assert result.errors
    assert settings.read_text(encoding="utf-8") == "{ // comment\n}"


def test_uninstall_removes_only_manifest_owned_asset(tmp_path: Path) -> None:
    generate_profile(project_dir=tmp_path)
    asset = zoo_import_asset_path(tmp_path)

    result = uninstall_profile(asset)

    assert result.ok
    assert not asset.exists()
    assert not asset.with_name(".specsmith-zoo-local-llm.manifest.json").exists()


def test_uninstall_preserves_unowned_asset(tmp_path: Path) -> None:
    asset = zoo_import_asset_path(tmp_path)
    asset.parent.mkdir()
    asset.write_text("{}", encoding="utf-8")

    result = uninstall_profile(asset)

    assert result.warnings
    assert asset.exists()


def test_cli_exposes_litellm_subgroup_and_generates_asset(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        zoo_code_group,
        ["litellm", "setup", "--project-dir", str(tmp_path), "--no-proxy-check"],
    )

    assert result.exit_code == 0, result.output
    assert zoo_import_asset_path(tmp_path).exists()
