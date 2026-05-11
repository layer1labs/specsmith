# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for specsmith.channel — persistent dev/stable channel selection."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from specsmith.channel import (
    VALID_CHANNELS,
    _channel_from_version,
    clear_persisted_channel,
    effective_channel,
    effective_channel_with_source,
    get_persisted_channel,
    set_persisted_channel,
)
from specsmith.cli import main  # noqa: E402

# ---------------------------------------------------------------------------
# Unit tests for channel module
# ---------------------------------------------------------------------------


class TestChannelFromVersion:
    def test_stable_version(self) -> None:
        assert _channel_from_version("0.10.1") == "stable"

    def test_dev_version(self) -> None:
        assert _channel_from_version("0.10.1.dev42") == "dev"

    def test_empty_string_is_stable(self) -> None:
        assert _channel_from_version("") == "stable"

    def test_dev_anywhere_in_string(self) -> None:
        assert _channel_from_version("1.0.0.dev0") == "dev"


class TestPersistedChannel:
    def test_no_file_returns_none(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        assert get_persisted_channel() is None

    def test_set_and_get_stable(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        set_persisted_channel("stable")
        assert get_persisted_channel() == "stable"

    def test_set_and_get_dev(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        set_persisted_channel("dev")
        assert get_persisted_channel() == "dev"

    def test_invalid_channel_raises(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        with pytest.raises(ValueError, match="Unknown channel"):
            set_persisted_channel("nightly")

    def test_clear_removes_file(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        set_persisted_channel("dev")
        assert get_persisted_channel() == "dev"
        clear_persisted_channel()
        assert get_persisted_channel() is None

    def test_clear_no_file_is_noop(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "missing" / "channel")
        clear_persisted_channel()  # should not raise

    def test_corrupted_file_returns_none(self, tmp_path, monkeypatch) -> None:
        channel_file = tmp_path / "channel"
        channel_file.write_text("garbage\n", encoding="utf-8")
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", channel_file)
        assert get_persisted_channel() is None


class TestEffectiveChannel:
    def test_persisted_wins_over_version(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        set_persisted_channel("dev")
        # Even with a stable version string, persisted "dev" should win.
        result = effective_channel(_version="1.0.0")
        assert result == "dev"

    def test_version_fallback_stable(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        result = effective_channel(_version="1.0.0")
        assert result == "stable"

    def test_version_fallback_dev(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        result = effective_channel(_version="1.0.0.dev5")
        assert result == "dev"

    def test_returns_valid_channel(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        result = effective_channel(_version="1.0.0")
        assert result in VALID_CHANNELS


class TestEffectiveChannelWithSource:
    def test_source_user_when_persisted(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        set_persisted_channel("stable")
        channel, source = effective_channel_with_source(_version="1.0.0.dev5")
        assert channel == "stable"
        assert source == "user"

    def test_source_version_when_not_persisted(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        channel, source = effective_channel_with_source(_version="1.0.0")
        assert channel == "stable"
        assert source == "version"

    def test_source_version_dev(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        channel, source = effective_channel_with_source(_version="1.0.0.dev3")
        assert channel == "dev"
        assert source == "version"


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------


class TestChannelCLI:
    def test_channel_get(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        monkeypatch.setenv("SPECSMITH_NO_AUTO_UPDATE", "1")
        runner = CliRunner()
        result = runner.invoke(main, ["channel", "get"])
        assert result.exit_code == 0
        assert "Channel" in result.output or "stable" in result.output or "dev" in result.output

    def test_channel_get_json(self, tmp_path, monkeypatch) -> None:
        import json

        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        monkeypatch.setenv("SPECSMITH_NO_AUTO_UPDATE", "1")
        runner = CliRunner()
        result = runner.invoke(main, ["channel", "get", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["channel"] in VALID_CHANNELS
        assert data["source"] in ("user", "version")

    def test_channel_set_stable(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        monkeypatch.setenv("SPECSMITH_NO_AUTO_UPDATE", "1")
        runner = CliRunner()
        result = runner.invoke(main, ["channel", "set", "stable"])
        assert result.exit_code == 0
        assert "stable" in result.output

    def test_channel_set_dev(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        monkeypatch.setenv("SPECSMITH_NO_AUTO_UPDATE", "1")
        runner = CliRunner()
        result = runner.invoke(main, ["channel", "set", "dev"])
        assert result.exit_code == 0
        assert "dev" in result.output

    def test_channel_set_persists(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        monkeypatch.setenv("SPECSMITH_NO_AUTO_UPDATE", "1")
        runner = CliRunner()
        runner.invoke(main, ["channel", "set", "dev"])
        assert get_persisted_channel() == "dev"

    def test_channel_clear(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        monkeypatch.setenv("SPECSMITH_NO_AUTO_UPDATE", "1")
        set_persisted_channel("dev")
        runner = CliRunner()
        result = runner.invoke(main, ["channel", "clear"])
        assert result.exit_code == 0
        assert get_persisted_channel() is None

    def test_channel_set_invalid(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        monkeypatch.setenv("SPECSMITH_NO_AUTO_UPDATE", "1")
        runner = CliRunner()
        result = runner.invoke(main, ["channel", "set", "nightly"])
        assert result.exit_code != 0

    def test_channel_get_shows_source(self, tmp_path, monkeypatch) -> None:
        """After set, get should show 'user preference'."""
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "channel")
        monkeypatch.setenv("SPECSMITH_NO_AUTO_UPDATE", "1")
        runner = CliRunner()
        runner.invoke(main, ["channel", "set", "stable"])
        result = runner.invoke(main, ["channel", "get"])
        assert result.exit_code == 0
        assert "user preference" in result.output

    def test_channel_get_shows_version_source(self, tmp_path, monkeypatch) -> None:
        """Without a persisted channel, get should show 'version inference'."""
        monkeypatch.setattr("specsmith.channel._CHANNEL_FILE", tmp_path / "no_channel")
        monkeypatch.setenv("SPECSMITH_NO_AUTO_UPDATE", "1")
        runner = CliRunner()
        result = runner.invoke(main, ["channel", "get"])
        assert result.exit_code == 0
        assert "version inference" in result.output
