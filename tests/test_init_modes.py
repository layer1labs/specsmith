from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from specsmith.cli import main


def _write_config(tmp_path: Path, name: str) -> Path:
    cfg = {
        "name": name,
        "type": "cli-python",
        "platforms": ["linux"],
        "language": "python",
        "git_init": False,
        "vcs_platform": "",
    }
    p = tmp_path / f"{name}.yml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return p


def test_init_mode_lite_creates_minimal_set(tmp_path: Path) -> None:
    cfg = _write_config(tmp_path, "lite-project")
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "init",
            "--config",
            str(cfg),
            "--output-dir",
            str(tmp_path),
            "--mode",
            "lite",
            "--quiet",
        ],
    )
    assert result.exit_code == 0
    root = tmp_path / "lite-project"
    assert (root / "AGENTS.md").exists()
    assert (root / "docs" / "REQUIREMENTS.md").exists()
    assert (root / "docs" / "TESTS.md").exists()
    assert (root / ".specsmith").exists()


def test_init_mode_regulated_adds_compliance_files(tmp_path: Path) -> None:
    cfg = _write_config(tmp_path, "regulated-project")
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "init",
            "--config",
            str(cfg),
            "--output-dir",
            str(tmp_path),
            "--mode",
            "regulated",
            "--quiet",
        ],
    )
    assert result.exit_code == 0
    root = tmp_path / "regulated-project"
    assert (root / "docs" / "compliance" / "COMPLIANCE.md").exists()
    assert (root / "docs" / "compliance" / "EVIDENCE-PACK.md").exists()
    assert (root / ".specsmith" / "gate-config.yml").exists()


def test_init_dry_run_json_lists_files(tmp_path: Path) -> None:
    cfg = _write_config(tmp_path, "dryrun-project")
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "init",
            "--config",
            str(cfg),
            "--output-dir",
            str(tmp_path),
            "--mode",
            "team",
            "--dry-run",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert '"dry_run": true' in result.output
    assert '"planned_files"' in result.output


def test_init_output_shows_exactly_three_next_commands(tmp_path: Path) -> None:
    cfg = _write_config(tmp_path, "output-project")
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "init",
            "--config",
            str(cfg),
            "--output-dir",
            str(tmp_path),
            "--mode",
            "team",
        ],
    )
    assert result.exit_code == 0
    marker = "Next (run these 3 commands):"
    assert marker in result.output
    block = result.output.split(marker, 1)[1]
    lines = [line for line in block.splitlines() if "specsmith " in line]
    assert len(lines) == 3
