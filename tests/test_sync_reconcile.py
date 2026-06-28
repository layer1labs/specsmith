from __future__ import annotations

from pathlib import Path

from specsmith.sync import run_sync


def _set_yaml_mode(root: Path) -> None:
    state_dir = root / ".specsmith"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "governance-mode").write_text("yaml", encoding="utf-8")


def _write_yaml_req(root: Path, req_id: str) -> None:
    reqs_dir = root / "docs" / "requirements"
    reqs_dir.mkdir(parents=True, exist_ok=True)
    (reqs_dir / "core.yml").write_text(
        f"- id: {req_id}\n  title: {req_id} title\n  status: defined\n",
        encoding="utf-8",
    )


def _write_yaml_test(root: Path, test_id: str, requirement_id: str = "REQ-001") -> None:
    tests_dir = root / "docs" / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "core.yml").write_text(
        f"- id: {test_id}\n"
        f"  title: {test_id} title\n"
        f"  requirement_id: {requirement_id}\n"
        "  type: unit\n",
        encoding="utf-8",
    )


def test_run_sync_warns_when_requirements_md_has_req_id_missing_from_yaml(tmp_path: Path) -> None:
    _set_yaml_mode(tmp_path)
    _write_yaml_req(tmp_path, "REQ-001")
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "REQUIREMENTS.md").write_text(
        "## REQ-001: Existing\n## REQ-999: Missing from YAML\n",
        encoding="utf-8",
    )

    result = run_sync(tmp_path, dry_run=True)
    expected = (
        "REQ-999 found in docs/REQUIREMENTS.md but missing from docs/requirements/*.yml — "
        "add it to a YAML file and re-run sync."
    )

    assert any(w.message == expected for w in result.warnings)


def test_run_sync_has_no_requirement_warning_when_requirements_ids_match(tmp_path: Path) -> None:
    _set_yaml_mode(tmp_path)
    _write_yaml_req(tmp_path, "REQ-001")
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "REQUIREMENTS.md").write_text("## REQ-001: Existing\n", encoding="utf-8")

    result = run_sync(tmp_path, dry_run=True)

    assert not any("docs/REQUIREMENTS.md" in w.message for w in result.warnings)


def test_run_sync_warns_when_tests_md_has_test_id_missing_from_yaml(tmp_path: Path) -> None:
    _set_yaml_mode(tmp_path)
    _write_yaml_req(tmp_path, "REQ-001")
    _write_yaml_test(tmp_path, "TEST-001")
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "TESTS.md").write_text(
        "## TEST-001. Existing\n## TEST-999. Missing from YAML\n",
        encoding="utf-8",
    )

    result = run_sync(tmp_path, dry_run=True)
    expected = (
        "TEST-999 found in docs/TESTS.md but missing from docs/tests/*.yml — "
        "add it to a YAML file and re-run sync."
    )

    assert any(w.message == expected for w in result.warnings)


def test_run_sync_has_no_test_warning_when_test_ids_match(tmp_path: Path) -> None:
    _set_yaml_mode(tmp_path)
    _write_yaml_req(tmp_path, "REQ-001")
    _write_yaml_test(tmp_path, "TEST-001")
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "TESTS.md").write_text("## TEST-001. Existing\n", encoding="utf-8")

    result = run_sync(tmp_path, dry_run=True)

    assert not any("docs/TESTS.md" in w.message for w in result.warnings)
