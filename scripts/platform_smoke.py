#!/usr/bin/env python3
"""Exercise the exact candidate wheel through a portable public-CLI workflow.

Designed for GitHub-hosted Windows, Linux, and macOS runners.  This script
does not activate a virtual environment, rely on a console-script location, or
use a shell.  The temporary workspace deliberately contains spaces and Unicode
characters to catch path/quoting regressions in package installations.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
import venv
from collections.abc import Sequence
from pathlib import Path


def venv_python(venv_dir: Path) -> Path:
    """Return the interpreter path for a venv on the active platform."""
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def run(command: Sequence[str], *, cwd: Path, env: dict[str, str]) -> None:
    """Run an argv command with useful, platform-neutral failure context."""
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd, env=env, check=True)


def find_wheel(wheel_dir: Path) -> Path:
    """Return the single candidate universal wheel from *wheel_dir*."""
    wheels = sorted(wheel_dir.glob("specsmith-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"Expected exactly one Specsmith wheel in {wheel_dir}; found {wheels}")
    return wheels[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel-dir", type=Path, default=Path("dist"))
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help="Optional writable parent for temporary smoke directories.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    wheel = find_wheel(args.wheel_dir.resolve())
    if args.work_dir is not None:
        args.work_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="specsmith wheel smoke ", dir=str(args.work_dir) if args.work_dir else None
    ) as temporary:
        root = Path(temporary) / "workspace with spaces ünicode"
        root.mkdir(parents=True)
        environment = os.environ.copy()
        environment.update(
            {
                # CI validates an isolated wheel rather than a pipx install.
                "SPECSMITH_ALLOW_NON_PIPX": "1",
                "SPECSMITH_NO_AUTO_UPDATE": "1",
                "SPECSMITH_PYPI_CHECKED": "1",
            }
        )

        environment_dir = root / "wheel-venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(environment_dir)
        python = venv_python(environment_dir)
        install_command = [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            str(wheel),
        ]
        run(
            install_command,
            cwd=root,
            env=environment,
        )
        run([str(python), "-m", "specsmith", "--version"], cwd=root, env=environment)

        config = root / "smoke-config.yml"
        config.write_text(
            "\n".join(
                (
                    "name: wheel-smoke",
                    "type: cli-python",
                    "platforms:",
                    "  - linux",
                    "language: python",
                    "git_init: false",
                    'vcs_platform: ""',
                    "",
                )
            ),
            encoding="utf-8",
            newline="\n",
        )
        run(
            [
                str(python),
                "-m",
                "specsmith",
                "init",
                "--config",
                str(config),
                "--output-dir",
                str(root),
                "--no-git",
                "--quiet",
            ],
            cwd=root,
            env=environment,
        )
        project = root / "wheel-smoke"
        common = ["--project-dir", str(project)]
        run([str(python), "-m", "specsmith", "audit", *common], cwd=root, env=environment)
        run(
            [str(python), "-m", "specsmith", "validate", "--strict", *common],
            cwd=root,
            env=environment,
        )
        run([str(python), "-m", "specsmith", "sync", *common], cwd=root, env=environment)
        run([str(python), "-m", "specsmith", "sync", "--check", *common], cwd=root, env=environment)
        run(
            [
                str(python),
                "-m",
                "specsmith",
                "zoo-code",
                "litellm",
                "setup",
                "--project-dir",
                str(project),
                "--no-proxy-check",
            ],
            cwd=root,
            env=environment,
        )
        run(
            [
                str(python),
                "-m",
                "specsmith",
                "zoo-code",
                "litellm",
                "validate",
                "--project-dir",
                str(project),
            ],
            cwd=root,
            env=environment,
        )

    print("Candidate wheel smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
