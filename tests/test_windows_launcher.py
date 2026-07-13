from __future__ import annotations

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
