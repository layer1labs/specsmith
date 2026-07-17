import pytest

from specsmith.zoo_settings import (
    ZooSettingSpec,
    reconcile_zoo_settings,
    settings_digest,
    uninstall_zoo_settings,
)

REGISTRY = (
    ZooSettingSpec("allowedCommands", ["*"], "managed"),
    ZooSettingSpec("nativeCondense", False, "manual", ui_path="Settings > Context"),
)


def test_setup_repairs_managed_drift_and_reports_exact_manual_gap() -> None:
    current = {"allowedCommands": ["git"], "customProfile": {"name": "mine"}}
    result = reconcile_zoo_settings(current, REGISTRY, version="3.68.0")
    assert result.settings["allowedCommands"] == ["*"]
    assert result.settings["customProfile"] == {"name": "mine"}
    assert result.status == "partial_manual_required"
    assert "Settings > Context" in result.manual_actions[0]
    second = reconcile_zoo_settings(result.settings, REGISTRY, version="3.68.0")
    assert not second.repaired


def test_concurrent_write_fails_and_uninstall_preserves_later_user_edit() -> None:
    current = {"allowedCommands": ["git"]}
    with pytest.raises(ValueError, match="concurrently"):
        reconcile_zoo_settings(current, REGISTRY, version="3", expected_digest="bad")
    setup = reconcile_zoo_settings(
        current, REGISTRY, version="3", expected_digest=settings_digest(current)
    )
    user_changed = dict(setup.settings, allowedCommands=["make"])
    assert uninstall_zoo_settings(user_changed, setup.manifest)["allowedCommands"] == ["make"]


def test_unknown_version_and_read_only_doctor_fail_closed() -> None:
    current = {"allowedCommands": ["git"]}
    unsupported = reconcile_zoo_settings(current, REGISTRY, version="99.0")
    assert unsupported.status == "unsupported_version"
    assert unsupported.settings == current
    doctor = reconcile_zoo_settings(
        {"allowedCommands": ["git"], "nativeCondense": False},
        REGISTRY,
        version="3.68.0",
        fix=False,
    )
    assert doctor.status == "repair_required"
    assert doctor.settings["allowedCommands"] == ["git"]
