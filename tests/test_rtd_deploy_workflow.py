"""Regression coverage for the checked Read the Docs deployment workflow."""

from pathlib import Path


def test_rtd_deploy_uses_canonical_project_and_main() -> None:
    """TEST-473: latest must be synchronized from this repository's main branch."""
    workflow = (
        Path(__file__).resolve().parents[1] / ".github" / "workflows" / "rtd-deploy.yml"
    ).read_text(encoding="utf-8")

    assert "https://github.com/layer1labs/specsmith" in workflow
    assert '"default_branch":"main"' in workflow
    assert "rtd-project-state.json" in workflow
    assert "PROJECT_REPOSITORY" in workflow
    assert "PROJECT_BRANCH" in workflow
    assert "projects/specsmith/sync-versions/" in workflow
    assert '[ "$PROJECT_STATUS" = "204" ]' in workflow
    assert '[ "$SYNC_STATUS" = "202" ]' in workflow
    assert "RTD latest now tracks main." in workflow
    assert "RTD latest did not switch to main after version sync." in workflow
    assert '[ "$STATUS" = "202" ]' in workflow
