# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Targeted CLI regressions for #249, #254, and #212."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from click.testing import CliRunner

from specsmith.cli import main


def _invoke(args: list[str]):
    runner = CliRunner()
    return runner.invoke(
        main,
        args,
        env={
            "SPECSMITH_NO_AUTO_UPDATE": "1",
            "SPECSMITH_PYPI_CHECKED": "1",
            "SPECSMITH_ALLOW_NON_PIPX": "1",
        },
    )


def test_esdb_enable_same_path_skips_copy2(monkeypatch, tmp_path: Path) -> None:
    """#249: esdb enable must not call copy2 when src and dst resolve equal."""

    class _Status:
        valid = True
        customer = "Test Customer"
        expires_at = "2099-12-31T00:00:00Z"
        reason = ""

    home = tmp_path / "home"
    key_dest = home / ".specsmith" / "esdb.key"
    key_dest.parent.mkdir(parents=True)
    key_dest.write_text("{}", encoding="utf-8")

    monkeypatch.setattr("specsmith.esdb._license.verify_license_file", lambda _: _Status())
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr(
        "shutil.copy2", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("copy2"))
    )

    result = _invoke(["esdb", "enable", "--key-file", str(key_dest), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True


def test_phase_next_skips_suppressed_phases(tmp_path: Path) -> None:
    """#254: phase next should skip phases listed in suppressed_phases."""
    scaffold = {
        "name": "phase-regression",
        "type": "cli-python",
        "language": "python",
        "aee_phase": "requirements",
        "suppressed_phases": ["test_spec"],
    }
    (tmp_path / "scaffold.yml").write_text(yaml.safe_dump(scaffold), encoding="utf-8")

    result = _invoke(["phase", "next", "--force", "--project-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output

    updated = yaml.safe_load((tmp_path / "scaffold.yml").read_text(encoding="utf-8"))
    assert updated["aee_phase"] == "implementation"
    assert "Skipped suppressed phase" in result.output


def test_doctor_json_outputs_overall_key(tmp_path: Path) -> None:
    """#212: doctor --json should return valid JSON with an overall status key."""
    result = _invoke(["doctor", "--project-dir", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert "checks" in payload
    assert "overall" in payload
    assert payload["overall"] in ("pass", "fail")


def test_doctor_human_exits_zero(tmp_path: Path) -> None:
    """#212: doctor human output should exit 0 in normal environments."""
    result = _invoke(["doctor", "--project-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "specsmith doctor" in result.output
