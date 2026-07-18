import os
import subprocess
import sys
import time
from pathlib import Path


def _import_cli(
    cwd: Path, environ: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update(environ or {})
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import specsmith.cli; "
            + "print('specsmith.commands.reporting' in sys.modules)",
        ],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
    )


def test_basic_cli_import_is_bounded_and_does_not_load_reporting(tmp_path: Path) -> None:
    workdir = tmp_path / "path with spaces ünicode"
    workdir.mkdir()
    started = time.monotonic()
    result = _import_cli(workdir)
    assert time.monotonic() - started < 8
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "False"


def test_cli_import_is_bounded_across_locale_values(tmp_path: Path) -> None:
    for value in ("", "C", "invalid_LOCALE", "en_US.UTF-8:fr_FR.UTF-8"):
        result = _import_cli(
            tmp_path,
            {"LANG": value, "LC_ALL": value, "LANGUAGE": value},
        )
        assert result.returncode == 0, (value, result.stderr)
        assert result.stdout.strip() == "False"
