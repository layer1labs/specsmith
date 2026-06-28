from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from specsmith.cli import main
from specsmith.wi_store import WorkItemStore


def test_verify_cmd_equilibrium_marks_work_item_implemented(tmp_path: Path) -> None:
    store = WorkItemStore(tmp_path)
    wi = store.create("WI-VERIFY01", intent="verify lifecycle wiring")
    assert wi.status == "open"

    diff_path = tmp_path / "changes.diff"
    diff_path.write_text(
        "--- a/src/sample.py\n+++ b/src/sample.py\n@@ -1 +1 @@\n+print('ok')\n",
        encoding="utf-8",
    )
    tests_path = tmp_path / "test-results.json"
    tests_path.write_text('{"passed": 1, "failed": 0}', encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "verify",
            "--project-dir",
            str(tmp_path),
            "--diff",
            str(diff_path),
            "--tests",
            str(tests_path),
            "--changed",
            "src/sample.py",
            "--work-item-id",
            wi.id,
        ],
        env={"SPECSMITH_ALLOW_NON_PIPX": "1"},
    )
    assert result.exit_code == 0

    updated = WorkItemStore(tmp_path).get(wi.id)
    assert updated is not None
    assert updated.status == "implemented"


def test_approve_cmd_sets_human_review_status_approved(tmp_path: Path) -> None:
    store = WorkItemStore(tmp_path)
    wi = store.create("WI-APPROVE02", intent="approval lifecycle wiring")
    assert wi.human_review_status == "pending"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "approve",
            "implementation",
            "--work-item",
            wi.id,
            "--rationale",
            "Looks good",
            "--project-dir",
            str(tmp_path),
        ],
        env={"SPECSMITH_ALLOW_NON_PIPX": "1"},
    )
    assert result.exit_code == 0

    updated = WorkItemStore(tmp_path).get(wi.id)
    assert updated is not None
    assert updated.human_review_status == "approved"


def test_set_files_touched_sets_files_on_work_item(tmp_path: Path) -> None:
    store = WorkItemStore(tmp_path)
    wi = store.create("WI-FILES03", intent="track touched files")
    assert wi.files_touched == []

    updated = store.set_files_touched(wi.id, ["src/a.py", "tests/test_a.py"])
    assert updated is not None
    assert updated.files_touched == ["src/a.py", "tests/test_a.py"]

    reloaded = WorkItemStore(tmp_path).get(wi.id)
    assert reloaded is not None
    assert reloaded.files_touched == ["src/a.py", "tests/test_a.py"]
