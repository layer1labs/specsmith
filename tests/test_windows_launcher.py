from __future__ import annotations

import json

from click.testing import CliRunner

from specsmith.cli import main
from specsmith.updater import find_windows_launchers


def test_find_windows_launchers_detects_path_shadowing(tmp_path) -> None:
    pipx = tmp_path / "pipx"
    scripts = tmp_path / "scripts"
    pipx.mkdir()
    scripts.mkdir()
    (pipx / "specsmith.exe").touch()
    (scripts / "specsmith.exe").touch()

    launchers = find_windows_launchers(f"{pipx};{scripts}")

    assert launchers == [pipx / "specsmith.exe", scripts / "specsmith.exe"]


def test_doctor_warns_about_windows_launcher_shadowing(tmp_path, monkeypatch) -> None:
    launchers = [tmp_path / "pipx" / "specsmith.exe", tmp_path / "scripts" / "specsmith.exe"]
    monkeypatch.setattr("specsmith.cli._is_windows_platform", lambda: True)
    monkeypatch.setattr("specsmith.updater.find_windows_launchers", lambda _: launchers)

    result = CliRunner().invoke(main, ["doctor", "--project-dir", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    launcher_check = next(
        check for check in payload["checks"] if check["name"] == "specsmith launchers"
    )
    assert launcher_check == {
        "name": "specsmith launchers",
        "status": "warn",
        "detail": "2 found; use pipx only",
    }
