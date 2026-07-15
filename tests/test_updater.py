"""Regression coverage for reachable version-mismatch remediation."""

from __future__ import annotations

import pytest

from specsmith.updater import version_mismatch_remediation


@pytest.mark.parametrize("version", ["0.22.0.dev1", "0.22.0rc1", "0.22.0+local"])
def test_version_mismatch_reports_exact_pipx_install_for_nonstable_project(version: str) -> None:
    assert version_mismatch_remediation(version) == f"pipx install --force specsmith=={version}"


def test_version_mismatch_keeps_normal_upgrade_for_stable_project() -> None:
    assert version_mismatch_remediation("0.22.0") == "pipx upgrade specsmith"
