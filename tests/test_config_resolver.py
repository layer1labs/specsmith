from pathlib import Path

import pytest

from specsmith.config_resolver import ConfigError, global_config_path, resolve_config


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_layered_precedence_and_provenance(tmp_path: Path) -> None:
    global_path = tmp_path / "global.yml"
    _write(
        global_path, "schema_version: 1\nexecution:\n  shell: sh\nidentity:\n  agent_id: global\n"
    )
    _write(tmp_path / "docs/SPECSMITH.yml", "schema_version: 1\nexecution:\n  shell: bash\n")
    _write(tmp_path / ".specsmith/local.yml", "schema_version: 1\nidentity:\n  agent_id: local\n")
    resolved = resolve_config(
        tmp_path,
        global_path=global_path,
        environ={"SPECSMITH_SHELL": "pwsh"},
        explicit={"execution": {"shell": "cmd"}},
    )
    assert resolved.values["execution"]["shell"] == "cmd"
    assert resolved.provenance["execution.shell"] == "explicit"
    assert resolved.values["identity"]["agent_id"] == "local"


def test_unknown_keys_and_plaintext_secrets_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "docs/SPECSMITH.yml"
    _write(path, "schema_version: 1\nunknown: true\n")
    with pytest.raises(ConfigError, match="unknown"):
        resolve_config(tmp_path, environ={}, global_path=tmp_path / "none")
    _write(path, "schema_version: 1\nproviders:\n  api_token: plaintext\n")
    with pytest.raises(ConfigError, match="plaintext secret"):
        resolve_config(tmp_path, environ={}, global_path=tmp_path / "none")


def test_platform_native_global_paths() -> None:
    assert (
        global_config_path(platform="nt", environ={"APPDATA": "C:/Config"})
        .as_posix()
        .endswith("Config/specsmith/config.yml")
    )
    assert global_config_path(platform="posix", environ={"XDG_CONFIG_HOME": "/cfg"}) == Path(
        "/cfg/specsmith/config.yml"
    )
