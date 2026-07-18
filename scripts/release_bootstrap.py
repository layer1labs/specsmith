"""Private CI candidate bootstrap and closure checker (GitHub issue #323)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

from release_evidence import create_seal


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args: list[str], *, cwd: Path) -> None:
    environment = os.environ | {
        "SPECSMITH_ALLOW_NON_PIPX": "1",
        "SPECSMITH_DISABLE_UPDATE_CHECK": "1",
        "PIP_NO_CACHE_DIR": "1",
    }
    subprocess.run(args, cwd=cwd, check=True, env=environment)


def git_status(root: Path) -> str:
    return subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def python_in(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def version_from_pyproject(root: Path) -> str:
    match = re.search(r'^version\s*=\s*"([^"]+)"$', (root / "pyproject.toml").read_text(), re.M)
    if not match:
        raise ValueError("pyproject.toml has no package version")
    return match.group(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "check"))
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--version")
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_dir.resolve()
    version = version_from_pyproject(root)
    requested_version = args.version.removeprefix("v") if args.version else version
    if requested_version != version:
        raise SystemExit(f"requested version {args.version} does not match package {version}")
    metadata = __import__("yaml").safe_load((root / "docs/SPECSMITH.yml").read_text()) or {}
    if metadata.get("version") != version or metadata.get("spec_version") != version:
        raise SystemExit("package, project version, and spec_version must match before closure")
    before_status = git_status(root)
    with tempfile.TemporaryDirectory(prefix="specsmith-release-") as temp:
        temp_dir = Path(temp)
        dist = temp_dir / "dist"
        run([sys.executable, "-m", "build", "--sdist", "--outdir", str(dist)], cwd=root)
        sdist = next(dist.glob("specsmith-*.tar.gz"))
        run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--no-deps",
                "--wheel-dir",
                str(dist),
                str(sdist),
            ],
            cwd=root,
        )  # noqa: E501
        wheel = next(dist.glob("specsmith-*.whl"))
        candidate = temp_dir / "candidate-venv"
        venv.EnvBuilder(with_pip=True).create(candidate)
        candidate_python = python_in(candidate)
        run(
            [
                str(candidate_python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                str(wheel),
            ],
            cwd=root,
        )  # noqa: E501
        run([str(candidate_python), "-m", "specsmith", "--version"], cwd=root)
        if args.mode == "prepare":
            run(
                [str(candidate_python), "-m", "specsmith", "sync", "--project-dir", str(root)],
                cwd=root,
            )  # noqa: E501
        else:
            run(
                [str(candidate_python), "-m", "specsmith", "audit", "--project-dir", str(root)],
                cwd=root,
            )  # noqa: E501
            run(
                [
                    str(candidate_python),
                    "-m",
                    "specsmith",
                    "validate",
                    "--strict",
                    "--project-dir",
                    str(root),
                ],
                cwd=root,
            )  # noqa: E501
        after_status = git_status(root)
        if args.mode == "check" and after_status != before_status:
            raise SystemExit("candidate closure check changed the worktree")
        source_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        manifest = {
            "schema": 1,
            "mode": args.mode,
            "candidate_version": version,
            "expected_tag": f"v{version}",
            "sdist_sha256": sha256(sdist),
            "wheel_sha256": sha256(wheel),
            "project_version": metadata["version"],
            "spec_version": metadata["spec_version"],
            "check_result": "passed",
            "source_commit": source_commit,
            "governed_files": sorted(line[3:] for line in after_status.splitlines()),
        }
        manifest_path = args.manifest.resolve()
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(create_seal(manifest), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
