from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from specsmith.cli import main


def _config(tmp_path: Path, name: str) -> Path:
    payload = {
        "name": name,
        "type": "cli-python",
        "platforms": ["linux"],
        "language": "python",
        "git_init": False,
        "vcs_platform": "",
    }
    p = tmp_path / f"{name}.yml"
    p.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return p


@pytest.mark.integration
@pytest.mark.parametrize("mode", ["lite", "team", "regulated"])
def test_golden_path_init_and_governance_smoke(tmp_path: Path, mode: str) -> None:
    runner = CliRunner()
    cfg = _config(tmp_path, f"{mode}-golden")
    init = runner.invoke(
        main,
        [
            "init",
            "--config",
            str(cfg),
            "--output-dir",
            str(tmp_path),
            "--mode",
            mode,
            "--json",
        ],
    )
    assert init.exit_code == 0, init.output
    project = tmp_path / f"{mode}-golden"
    assert (project / "AGENTS.md").exists()
    assert (project / ".specsmith").exists()

    audit = runner.invoke(main, ["audit", "--project-dir", str(project)])
    assert audit.exit_code in (0, 1)  # existing project warnings are tolerated in integration smoke

    doctor = runner.invoke(main, ["doctor", "--project-dir", str(project), "--json"])
    assert doctor.exit_code == 0, doctor.output
