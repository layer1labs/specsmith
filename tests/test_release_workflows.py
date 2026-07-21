from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ci_uses_module_pytest_for_repository_private_release_tests() -> None:
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "python -m pytest --cov=specsmith" in text
    assert "\n          pytest --cov=specsmith" not in text


def test_ci_dependency_audit_has_no_vulnerability_suppressions() -> None:
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "- run: pip-audit" in text
    assert "--ignore-vuln" not in text


def test_prepare_workflow_defaults_to_check_and_protects_refs() -> None:
    text = (ROOT / ".github/workflows/prepare-release.yml").read_text(encoding="utf-8")
    assert "options: [check, prepare]" in text
    assert "release/" in text
    assert "release_status_guard.py" in text
    assert "Clean second pass" in text
    assert "git add -A" not in text
    assert "force" not in text.lower()
    assert "permissions: {}" in text
    assert "contents: read" in text
    assert "contents: write" in text
    assert "contents: ${{" not in text
    assert "if: inputs.mode == 'check'" in text
    assert "if: inputs.mode == 'prepare'" in text
    assert text.count("python -m pip install build pyyaml") == 2


def test_tag_workflow_is_non_mutating_and_rejects_duplicates() -> None:
    text = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "python -m pip install build pyyaml" in text
    assert "python -m pytest tests/ -x -q" in text
    assert "- run: pytest tests/ -x -q" not in text
    assert "release_bootstrap.py check" in text
    assert "merge-base --is-ancestor" in text
    assert "build --sdist" in text
    assert "already exists on PyPI" in text
    assert "skip-existing" not in text
    assert "sed -i" not in text
    assert "verify-publication:" in text
    assert "verify_publication.py" in text
    assert "publication-receipt.json" in text
    assert "name: release-evidence" in text
    assert "--seal release-evidence/release-seal.json" in text
    verify_block = text.split("verify-publication:", 1)[1].split("cleanup-dev-releases:", 1)[0]
    assert "name: release-evidence" in verify_block


def test_canonical_runbook_has_fixed_point_and_immutable_recovery() -> None:
    text = (ROOT / "docs/site/releasing.md").read_text(encoding="utf-8")
    assert "second pass must be" in text
    assert "Published tags and package versions are immutable" in text
    assert "new commit and a new version" in text
    assert "post-publication receipt" in text
