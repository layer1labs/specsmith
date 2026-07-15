from __future__ import annotations

import pytest

from specsmith.release_guard import (
    is_development_version,
    is_stable_version,
    require_development_version,
    require_stable_version,
)


@pytest.mark.parametrize("version", ["0.21.0.dev1", "0.21.0a1", "0.21.0rc1", "0.21.0+local"])
def test_non_final_versions_are_rejected(version: str) -> None:
    assert not is_stable_version(version)
    with pytest.raises(ValueError, match="non-final"):
        require_stable_version(version)


def test_final_version_is_accepted() -> None:
    assert is_stable_version("0.21.0")
    require_stable_version("0.21.0")


def test_stable_version_must_match_release_tag() -> None:
    require_stable_version("0.21.0", "v0.21.0")
    with pytest.raises(ValueError, match="does not match tag"):
        require_stable_version("0.21.0", "v0.21.1")


@pytest.mark.parametrize("version", ["0.21.1.dev0", "0.21.1.dev42"])
def test_explicit_development_versions_are_accepted(version: str) -> None:
    assert is_development_version(version)
    require_development_version(version, version)


@pytest.mark.parametrize("version", ["0.21.1", "0.21.1rc1", "0.21.1+local"])
def test_non_development_versions_are_rejected_from_dev_channel(version: str) -> None:
    assert not is_development_version(version)
    with pytest.raises(ValueError, match="requires an X.Y.Z.devN"):
        require_development_version(version)
