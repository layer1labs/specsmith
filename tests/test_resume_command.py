# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for specsmith inspect and specsmith ledger export CLI commands (REQ-409)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    (tmp_path / ".specsmith").mkdir(parents=True)
    os.environ["SPECSMITH_ESDB_BACKEND"] = "sqlite"
    yield tmp_path
    os.environ.pop("SPECSMITH_ESDB_BACKEND", None)


# ---------------------------------------------------------------------------
# specsmith inspect
# ---------------------------------------------------------------------------


def test_resume_cmd_exits_zero(tmp_project: Path) -> None:
    """specsmith inspect exits 0 on a governed project."""
    from specsmith.cli import main

    runner = CliRunner()
    result = runner.invoke(main, ["inspect", "--project-dir", str(tmp_project)])
    assert result.exit_code == 0


def test_resume_cmd_json_contains_expected_keys(tmp_project: Path) -> None:
    """specsmith inspect --json contains audit_healthy, active_work_items, timestamp."""
    from specsmith.cli import main

    runner = CliRunner()
    result = runner.invoke(main, ["inspect", "--json", "--project-dir", str(tmp_project)])
    assert result.exit_code == 0

    payload = json.loads(result.output)
    assert "audit_healthy" in payload
    assert "active_work_items" in payload
    assert "timestamp" in payload


def test_resume_cmd_json_has_efficiency_when_eff_current_present(
    tmp_project: Path,
) -> None:
    """inspect --json includes efficiency key when EFF-CURRENT is in ESDB."""
    from specsmith.cli import main
    from specsmith.esdb import SqliteRecord, SqliteStore

    # Insert EFF-CURRENT manually
    with SqliteStore(tmp_project) as store:
        store.upsert(
            SqliteRecord(
                id="EFF-CURRENT",
                kind="efficiency_metric",
                status="active",
                label="test efficiency snapshot",
                confidence=1.0,
                data={
                    "tokens_per_correct_answer": 1500.0,
                    "degraded": False,
                    "sessions_analyzed": 5,
                    "epistemic_quality": {
                        "score": 0.72,
                        "confidence_density": 0.8,
                        "recency_score": 0.9,
                        "coherence_score": 0.7,
                        "closure_score": 0.5,
                        "non_contradiction_score": 0.6,
                    },
                    "computed_at": "2026-06-25T12:00:00Z",
                },
            )
        )

    runner = CliRunner()
    result = runner.invoke(main, ["inspect", "--json", "--project-dir", str(tmp_project)])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert "efficiency" in payload
    eff = payload["efficiency"]
    assert eff.get("tokens_per_correct_answer") == pytest.approx(1500.0)


# ---------------------------------------------------------------------------
# specsmith ledger export
# ---------------------------------------------------------------------------


def test_ledger_export_esdb_source(tmp_project: Path) -> None:
    """ledger export --source esdb --json returns ledger_event records from ESDB."""
    from specsmith.cli import main
    from specsmith.esdb_writer import write_ledger_event

    write_ledger_event(tmp_project, description="ledger entry A", author="test")
    write_ledger_event(tmp_project, description="ledger entry B", author="test")
    write_ledger_event(tmp_project, description="ledger entry C", author="test")

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["ledger", "export", "--json", "--source", "esdb", "--project-dir", str(tmp_project)],
    )
    assert result.exit_code == 0
    entries = json.loads(result.output)
    assert len(entries) == 3
    descs = {e["description"] for e in entries}
    assert "ledger entry A" in descs
    assert "ledger entry C" in descs


def test_ledger_export_file_source(tmp_project: Path) -> None:
    """ledger export --source file reads from LEDGER.md."""
    from specsmith.cli import main

    ledger_path = tmp_project / "LEDGER.md"
    ledger_path.write_text(
        "# Change Ledger\n"
        "\n## 2026-06-01T10:00 — entry one\n- **Author**: test\n"
        "\n## 2026-06-02T11:00 — entry two\n- **Author**: test\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["ledger", "export", "--json", "--source", "file", "--project-dir", str(tmp_project)],
    )
    assert result.exit_code == 0
    entries = json.loads(result.output)
    assert len(entries) >= 2


def test_ledger_export_no_entries_exits_ok(tmp_project: Path) -> None:
    """ledger export exits 0 with a message when no entries are found."""
    from specsmith.cli import main

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["ledger", "export", "--project-dir", str(tmp_project)],
    )
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# specsmith esdb sweep
# ---------------------------------------------------------------------------


def test_esdb_sweep_cmd_exits_zero(tmp_project: Path) -> None:
    """specsmith esdb sweep exits 0."""
    from specsmith.cli import main
    from specsmith.esdb import SqliteStore

    with SqliteStore(tmp_project):
        pass  # create schema

    runner = CliRunner()
    result = runner.invoke(main, ["esdb", "sweep", "--project-dir", str(tmp_project)])
    assert result.exit_code == 0


def test_esdb_sweep_cmd_dry_run_json(tmp_project: Path) -> None:
    """specsmith esdb sweep --dry-run --json emits JSON without tombstoning."""
    from specsmith.cli import main
    from specsmith.esdb import SqliteStore

    with SqliteStore(tmp_project):
        pass

    runner = CliRunner()
    result = runner.invoke(
        main, ["esdb", "sweep", "--dry-run", "--json", "--project-dir", str(tmp_project)]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert "tombstoned" in payload
    assert "orphans_flagged" in payload
    assert payload["dry_run"] is True
